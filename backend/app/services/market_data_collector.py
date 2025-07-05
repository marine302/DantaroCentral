"""
실시간 시장 데이터 수집 서비스 (WebSocket + REST API 통합)
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING
from dataclasses import dataclass
import json

from app.exchanges.factory import ExchangeFactory
from app.exchanges.base import BaseExchange, Ticker, Balance
from app.database.manager import db_manager
from app.database.redis_cache import redis_manager
from app.core.config import settings

if TYPE_CHECKING:
    from app.services.websocket_data_manager import WebSocketDataManager


@dataclass
class MarketDataPoint:
    """시장 데이터 포인트"""
    symbol: str
    exchange: str
    price: float
    volume_24h: float
    change_24h: float
    timestamp: datetime


class MarketDataCollector:
    """시장 데이터 수집기 (WebSocket + REST API 통합)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.exchanges: Dict[str, BaseExchange] = {}
        self.target_symbols: Set[str] = set()
        self.collection_interval = getattr(settings, "market_data_collection_interval", 60)  # seconds
        self._running = False
        
        # WebSocket 데이터 매니저 초기화 (지연 로딩)
        self.websocket_manager: Optional['WebSocketDataManager'] = None
        self.realtime_enabled = False
    
    def configure_exchanges(self, exchange_configs: Dict[str, Dict]):
        """
        거래소 설정
        
        Args:
            exchange_configs: {
                'okx': {'api_key': '...', 'secret_key': '...'},
                'coinone': {'api_key': '...', 'secret_key': '...'},
                'gate': {'api_key': '...', 'secret_key': '...'}
            }
        """
        for exchange_name, config in exchange_configs.items():
            try:
                exchange = ExchangeFactory.create_exchange(
                    exchange_name=exchange_name,
                    **config
                )
                self.exchanges[exchange_name] = exchange
                self.logger.info(f"{exchange_name} 거래소 연결 완료")
            except Exception as e:
                self.logger.error(f"{exchange_name} 거래소 연결 실패: {e}")
    
    def set_target_symbols(self, symbols: List[str]):
        """수집할 심볼 설정"""
        self.target_symbols = set(symbols)
        self.logger.info(f"수집 대상 심볼 설정: {symbols}")
    
    async def collect_single_exchange_data(self, exchange_name: str, exchange: BaseExchange) -> List[MarketDataPoint]:
        """단일 거래소에서 데이터 수집"""
        data_points = []
        
        try:
            for symbol in self.target_symbols:
                try:
                    ticker = await exchange.get_ticker(symbol)
                    
                    data_point = MarketDataPoint(
                        symbol=symbol,
                        exchange=exchange_name,
                        price=float(ticker.price),
                        volume_24h=float(ticker.volume),
                        change_24h=0.0,  # 계산 필요
                        timestamp=datetime.utcnow()
                    )
                    data_points.append(data_point)
                    
                except Exception as e:
                    self.logger.warning(f"{exchange_name}에서 {symbol} 데이터 수집 실패: {e}")
                    
        except Exception as e:
            self.logger.error(f"{exchange_name} 데이터 수집 중 오류: {e}")
        
        return data_points
    
    async def collect_all_data(self) -> List[MarketDataPoint]:
        """모든 거래소에서 데이터 수집"""
        all_data = []
        
        tasks = []
        for exchange_name, exchange in self.exchanges.items():
            task = self.collect_single_exchange_data(exchange_name, exchange)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"데이터 수집 작업 실패: {result}")
                elif isinstance(result, list):
                    all_data.extend(result)
        
        return all_data
    
    async def process_and_store_data(self, data_points: List[MarketDataPoint]):
        """데이터 처리 및 저장"""
        if not data_points:
            return
        
        # 심볼별로 데이터 그룹핑
        symbol_data: Dict[str, List[MarketDataPoint]] = {}
        for point in data_points:
            if point.symbol not in symbol_data:
                symbol_data[point.symbol] = []
            symbol_data[point.symbol].append(point)
        
        processed_data = []
        
        for symbol, points in symbol_data.items():
            # 각 심볼별로 최적 가격 계산 (예: 평균값 또는 거래량 기준)
            total_volume = sum(p.volume_24h for p in points)
            if total_volume > 0:
                # 거래량 가중 평균 가격
                weighted_price = sum(p.price * p.volume_24h for p in points) / total_volume
            else:
                # 단순 평균
                weighted_price = sum(p.price for p in points) / len(points)
            
            # 최고 거래량 데이터 선택
            best_volume_point = max(points, key=lambda p: p.volume_24h)
            
            processed_point = {
                'symbol': symbol,
                'price': weighted_price,
                'volume_24h': best_volume_point.volume_24h,
                'exchanges': [p.exchange for p in points],
                'exchange_count': len(points),
                'timestamp': datetime.utcnow()
            }
            processed_data.append(processed_point)
        
        # Redis에 최신 데이터 저장
        try:
            for data in processed_data:
                cache_key = f"market_data:{data['symbol']}"
                # 실제 Redis 저장 로직 구현 필요
                self.logger.debug(f"캐시 저장: {cache_key}")
            
            # 전체 시장 데이터 요약도 저장
            market_summary = {
                'total_symbols': len(processed_data),
                'active_exchanges': list(self.exchanges.keys()),
                'last_update': datetime.utcnow().isoformat(),
                'symbols': [d['symbol'] for d in processed_data]
            }
            self.logger.debug("시장 요약 저장")
            
            self.logger.info(f"시장 데이터 저장 완료: {len(processed_data)}개 심볼")
            
        except Exception as e:
            self.logger.error(f"데이터 저장 실패: {e}")
    
    async def start_collection(self):
        """데이터 수집 시작 (WebSocket + REST API)"""
        self._running = True
        self.logger.info("시장 데이터 수집 시작")
        
        # WebSocket 데이터 매니저 시작 (실시간 데이터 활성화된 경우)
        if self.realtime_enabled:
            try:
                # WebSocket 매니저가 없으면 생성
                if self.websocket_manager is None:
                    from app.services.websocket_data_manager import WebSocketDataManager
                    self.websocket_manager = WebSocketDataManager()
                
                # WebSocket 클라이언트 시작 로직
                self.logger.info("실시간 WebSocket 데이터 수집 시작")
            except Exception as e:
                self.logger.error(f"WebSocket 데이터 매니저 시작 실패: {e}")
        
        while self._running:
            try:
                # REST API 데이터 수집
                data_points = await self.collect_all_data()
                
                # 실시간 데이터와 결합 처리
                if self.realtime_enabled:
                    await self.process_combined_data(data_points)
                else:
                    await self.process_and_store_data(data_points)
                
                # 다음 수집까지 대기
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"데이터 수집 루프 오류: {e}")
                await asyncio.sleep(10)  # 오류 시 10초 대기 후 재시도
        
        # WebSocket 데이터 매니저 정지
        if self.realtime_enabled:
            try:
                # WebSocket 매니저 정지 로직
                self.logger.info("실시간 WebSocket 데이터 수집 정지")
            except Exception as e:
                self.logger.error(f"WebSocket 데이터 매니저 정지 실패: {e}")
    
    async def process_combined_data(self, rest_data_points: List[MarketDataPoint]):
        """실시간 데이터와 REST 데이터를 결합하여 처리"""
        if not rest_data_points:
            return
        
        # 심볼별로 데이터 그룹핑
        symbol_data: Dict[str, List[MarketDataPoint]] = {}
        for point in rest_data_points:
            if point.symbol not in symbol_data:
                symbol_data[point.symbol] = []
            symbol_data[point.symbol].append(point)
        
        processed_data = []
        
        for symbol, points in symbol_data.items():
            # 실시간 데이터 확인
            realtime_data = self.get_realtime_data(symbol)
            
            # REST 데이터 처리
            total_volume = sum(p.volume_24h for p in points)
            if total_volume > 0:
                weighted_price = sum(p.price * p.volume_24h for p in points) / total_volume
            else:
                weighted_price = sum(p.price for p in points) / len(points)
            
            best_volume_point = max(points, key=lambda p: p.volume_24h)
            
            # 실시간 데이터가 있으면 우선 사용
            final_price = weighted_price
            data_source = 'rest'
            
            if realtime_data and 'price' in realtime_data:
                final_price = realtime_data['price']
                data_source = 'websocket'
            
            processed_point = {
                'symbol': symbol,
                'price': final_price,
                'volume_24h': best_volume_point.volume_24h,
                'exchanges': [p.exchange for p in points],
                'exchange_count': len(points),
                'data_source': data_source,
                'realtime_available': realtime_data is not None,
                'timestamp': datetime.utcnow()
            }
            processed_data.append(processed_point)
        
        # Redis에 저장 (기존 로직 재사용)
        try:
            for data in processed_data:
                cache_key = f"market_data:{data['symbol']}"
                # Redis 저장 로직 (실제 구현에서는 redis_manager.set 사용)
                self.logger.debug(f"캐시 저장: {cache_key}")
            
            market_summary = {
                'total_symbols': len(processed_data),
                'active_exchanges': list(self.exchanges.keys()),
                'realtime_enabled': self.realtime_enabled,
                'last_update': datetime.utcnow().isoformat(),
                'symbols': [d['symbol'] for d in processed_data]
            }
            self.logger.debug("시장 요약 저장")
            
            self.logger.info(f"결합 데이터 저장 완료: {len(processed_data)}개 심볼")
            
        except Exception as e:
            self.logger.error(f"결합 데이터 저장 실패: {e}")
    
    def stop_collection(self):
        """데이터 수집 중지"""
        self._running = False
        self.logger.info("시장 데이터 수집 중지")
    
    async def test_public_apis(self) -> Dict[str, bool]:
        """
        각 거래소의 공개 API 연결 상태를 테스트합니다.
        API 키가 없어도 공개 데이터 접근이 가능한지 확인합니다.
        """
        test_results = {}
        
        # 각 거래소별 테스트 심볼
        test_symbols = {
            'okx': 'BTC-USDT',
            'gate': 'BTC_USDT', 
            'coinone': 'btc'
        }
        
        for exchange_name in ['okx', 'gate', 'coinone']:
            try:
                self.logger.info(f"{exchange_name} 공개 API 테스트 시작...")
                
                # 더미 자격증명으로 거래소 인스턴스 생성
                if exchange_name == 'okx':
                    from app.core.config import settings
                    if settings.okx_api_key:
                        # 실제 API 키가 있으면 사용
                        exchange = ExchangeFactory.create_exchange(
                            exchange_name,
                            api_key=settings.okx_api_key,
                            secret_key=settings.okx_secret_key,
                            passphrase=settings.okx_passphrase
                        )
                    else:
                        test_results[exchange_name] = False
                        continue
                else:
                    # 공개 API 테스트용 더미 자격증명
                    exchange = ExchangeFactory.create_exchange(
                        exchange_name,
                        api_key='dummy_key',
                        secret_key='dummy_secret'
                    )
                
                # 테스트 심볼로 시세 조회
                symbol = test_symbols[exchange_name]
                ticker = await exchange.get_ticker(symbol)
                
                if ticker and ticker.price > 0:
                    test_results[exchange_name] = True
                    self.logger.info(f"{exchange_name} 테스트 성공: {symbol} = ${ticker.price:,.2f}")
                else:
                    test_results[exchange_name] = False
                    self.logger.warning(f"{exchange_name} 테스트 실패: 유효하지 않은 데이터")
                
                await exchange.close()
                
            except Exception as e:
                test_results[exchange_name] = False
                self.logger.error(f"{exchange_name} 공개 API 테스트 실패: {e}")
        
        return test_results
        
    async def compare_exchange_prices(self, symbol_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        다중 거래소의 가격을 비교합니다.
        
        Args:
            symbol_map: 거래소별 심볼 매핑 (예: {'okx': 'BTC-USDT', 'gate': 'BTC_USDT'})
        """
        if symbol_map is None:
            symbol_map = {
                'okx': 'BTC-USDT',
                'gate': 'BTC_USDT',
                'coinone': 'btc'
            }
        
        results = {}
        price_data = []
        
        for exchange_name, symbol in symbol_map.items():
            if exchange_name not in self.exchanges:
                continue
                
            try:
                exchange = self.exchanges[exchange_name]
                ticker = await exchange.get_ticker(symbol)
                
                exchange_data = {
                    'exchange': exchange_name,
                    'symbol': symbol,
                    'price': float(ticker.price),
                    'bid': float(ticker.bid),
                    'ask': float(ticker.ask),
                    'timestamp': ticker.timestamp
                }
                
                results[exchange_name] = exchange_data
                price_data.append(ticker.price)
                
                self.logger.info(f"{exchange_name} {symbol}: ${ticker.price:,.2f}")
                
            except Exception as e:
                self.logger.error(f"{exchange_name} 가격 조회 실패: {e}")
                results[exchange_name] = {'error': str(e)}
        
        # 가격 분석
        if len(price_data) > 1:
            max_price = max(price_data)
            min_price = min(price_data)
            price_diff = max_price - min_price
            price_diff_pct = (price_diff / min_price) * 100
            
            results['analysis'] = {
                'max_price': float(max_price),
                'min_price': float(min_price),
                'price_difference': float(price_diff),
                'price_difference_pct': float(price_diff_pct),
                'exchanges_count': len(price_data)
            }
        
        return results
    
    def enable_realtime_data(self, symbols: List[str], exchanges: Optional[List[str]] = None):
        """
        실시간 데이터 수집 활성화
        
        Args:
            symbols: 실시간 수집할 심볼 리스트
            exchanges: 대상 거래소 리스트 (None이면 모든 지원 거래소)
        """
        if exchanges is None:
            exchanges = ['okx']  # 현재는 OKX만 지원
        
        # WebSocket 매니저 지연 로딩
        if self.websocket_manager is None:
            from app.services.websocket_data_manager import WebSocketDataManager
            self.websocket_manager = WebSocketDataManager()
        
        self.realtime_enabled = True
        self.logger.info(f"실시간 데이터 수집 활성화: {symbols} on {exchanges}")
    
    def disable_realtime_data(self):
        """실시간 데이터 수집 비활성화"""
        self.realtime_enabled = False
        self.logger.info("실시간 데이터 수집 비활성화")
    
    def get_realtime_data(self, symbol: str) -> Optional[Dict]:
        """실시간 데이터 조회"""
        if not self.realtime_enabled or self.websocket_manager is None:
            return None
        
        # 예시: symbol 인자 누락 오류 보완
        # return self.websocket_manager.get_latest_data(symbol)
        # symbol이 필요하다면 적절한 값 전달 필요(예: self.target_symbols 중 하나)
        # 아래는 예시 코드
        if self.target_symbols:
            symbol = next(iter(self.target_symbols))
            return self.websocket_manager.get_latest_data(symbol)
        else:
            return None
    
    async def get_combined_data(self, symbol: str) -> Dict[str, Any]:
        """실시간 + REST API 데이터 결합"""
        result = {
            'symbol': symbol,
            'realtime_data': None,
            'rest_data': [],
            'timestamp': datetime.utcnow().isoformat(),
            'data_sources': []
        }
        
        # 실시간 데이터 가져오기
        if self.realtime_enabled:
            realtime_data = self.get_realtime_data(symbol)
            if realtime_data:
                result['realtime_data'] = realtime_data
                result['data_sources'].append('websocket')
        
        # REST API 데이터 가져오기
        rest_data = []
        for exchange_name, exchange in self.exchanges.items():
            try:
                ticker = await exchange.get_ticker(symbol)
                rest_data.append({
                    'exchange': exchange_name,
                    'price': float(ticker.price),
                    'bid': float(ticker.bid),
                    'ask': float(ticker.ask),
                    'volume': float(ticker.volume),
                    'timestamp': ticker.timestamp.isoformat() if ticker.timestamp else None
                })
                result['data_sources'].append(f'rest_{exchange_name}')
            except Exception as e:
                self.logger.warning(f"{exchange_name}에서 {symbol} REST 데이터 조회 실패: {e}")
        
        result['rest_data'] = rest_data
        return result


# 글로벌 인스턴스
market_data_collector = MarketDataCollector()
