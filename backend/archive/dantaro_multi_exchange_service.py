#!/usr/bin/env python3
"""
Dantaro Central 다중 거래소 실시간 데이터 수집 서비스 (향상된 버전)
OKX + Upbit WebSocket 통합 시스템
"""
import asyncio
import logging
import signal
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.market_data_collector import market_data_collector
from app.services.websocket_data_manager import MultiExchangeWebSocketManager
from app.services.arbitrage_analyzer import ArbitrageAnalyzer
from app.core.config import settings
from optimization_config import dantaro_optimizer

# 로그 디렉토리 생성
os.makedirs('logs', exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multi_exchange_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DantaroMultiExchangeService:
    """Dantaro Central 다중 거래소 실시간 데이터 서비스"""
    
    def __init__(self):
        self.running = False
        self.websocket_manager = MultiExchangeWebSocketManager()
        self.arbitrage_analyzer = ArbitrageAnalyzer()
        
        # 통계 및 모니터링
        self.service_stats = {
            'start_time': None,
            'total_runtime': 0,
            'total_data_points': 0,
            'exchange_status': {},
            'error_count': 0,
            'arbitrage_opportunities': 0,
            'kimchi_premiums_tracked': 0
        }
        
        # 성능 최적화 설정
        self.performance_settings = dantaro_optimizer.get_performance_settings()
        self.active_symbols = dantaro_optimizer.get_active_symbols()
        
        # 차익거래 분석 설정
        self.arbitrage_analysis_interval = 10  # 10초마다 분석
        self.last_arbitrage_analysis = datetime.now()
        
    def setup_signal_handlers(self):
        """시그널 핸들러 설정"""
        def signal_handler(signum, frame):
            logger.info(f"종료 신호 {signum} 수신. 안전한 종료를 시작합니다...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize_exchanges(self):
        """거래소 연결 초기화 (다중 거래소)"""
        logger.info("🔗 다중 거래소 연결 초기화...")
        
        exchange_configs = {}
        
        # OKX 설정 확인
        if settings.okx_api_key:
            exchange_configs['okx'] = {
                'api_key': settings.okx_api_key,
                'secret_key': settings.okx_secret_key,
                'passphrase': settings.okx_passphrase
            }
            logger.info("✅ OKX 거래소 설정 완료")
        else:
            logger.warning("⚠️ OKX API 키가 없습니다. OKX 데이터 수집을 건너뜁니다.")
        
        # Upbit 설정 (공개 API - 항상 사용 가능)
        exchange_configs['upbit'] = {}
        logger.info("✅ Upbit 거래소 설정 완료 (공개 API)")
        
        # Coinone 설정
        if settings.coinone_api_key:
            exchange_configs['coinone'] = {
                'api_key': settings.coinone_api_key,
                'secret_key': settings.coinone_secret_key
            }
            logger.info("✅ Coinone 거래소 설정 완료")
        else:
            logger.info("ℹ️ Coinone API 키가 없습니다. Coinone 데이터 수집을 건너뜁니다.")
        
        if not exchange_configs:
            raise ValueError("설정된 거래소가 없습니다.")
        
        # WebSocket 매니저 초기화
        await self.websocket_manager.initialize_websockets(exchange_configs)
        logger.info(f"✅ {len(exchange_configs)}개 거래소 WebSocket 준비 완료")
        
        # 기존 REST API 수집기도 설정
        market_data_collector.configure_exchanges(exchange_configs)
        logger.info("✅ REST API 수집기 설정 완료")
    
    async def setup_multi_exchange_websockets(self):
        """다중 거래소 WebSocket 연결 및 구독"""
        logger.info("📡 다중 거래소 WebSocket 연결...")
        
        try:
            # 모든 WebSocket 연결
            await self.websocket_manager.connect_all_websockets()
            
            if self.websocket_manager.stats['active_connections'] == 0:
                raise ValueError("WebSocket 연결에 실패했습니다")
            
            # 거래소별 심볼 매핑
            symbols_by_exchange = self._map_symbols_to_exchanges()
            
            # 심볼 구독
            await self.websocket_manager.subscribe_to_symbols(symbols_by_exchange)
            
            # 리스닝 시작
            await self.websocket_manager.start_listening()
            
            logger.info("✅ 다중 거래소 WebSocket 설정 완료")
            
        except Exception as e:
            logger.error(f"❌ WebSocket 설정 실패: {e}")
            raise
    
    def _map_symbols_to_exchanges(self) -> Dict[str, List[str]]:
        """거래소별 심볼 매핑"""
        symbols_by_exchange = {}
        
        # OKX 심볼 (국제 표준)
        if 'okx' in self.websocket_manager.websocket_clients:
            okx_symbols = [symbol for symbol in self.active_symbols if '-USDT' in symbol]
            if not okx_symbols:
                okx_symbols = ['BTC-USDT', 'ETH-USDT']  # 기본값
            symbols_by_exchange['okx'] = okx_symbols
            logger.info(f"📊 OKX 심볼: {okx_symbols}")
        
        # Upbit 심볼 (KRW 기준)
        if 'upbit' in self.websocket_manager.websocket_clients:
            upbit_symbols = [symbol for symbol in self.active_symbols if 'KRW-' in symbol]
            if not upbit_symbols:
                upbit_symbols = ['KRW-BTC', 'KRW-ETH']  # 기본값
            symbols_by_exchange['upbit'] = upbit_symbols
            logger.info(f"📊 Upbit 심볼: {upbit_symbols}")
        
        # Coinone 심볼 (기본 심볼명)
        if 'coinone' in self.websocket_manager.websocket_clients:
            # Coinone은 단순 심볼명 사용 (BTC, ETH 등)
            coinone_symbols = []
            for symbol in self.active_symbols:
                if '-' in symbol:
                    # BTC-USDT -> BTC, KRW-BTC -> BTC 변환
                    base_symbol = symbol.split('-')[0] if symbol.startswith('KRW-') else symbol.split('-')[0]
                    coinone_symbols.append(base_symbol)
                else:
                    coinone_symbols.append(symbol)
            
            if not coinone_symbols:
                coinone_symbols = ['BTC', 'ETH']  # 기본값
            
            # 중복 제거
            coinone_symbols = list(set(coinone_symbols))
            symbols_by_exchange['coinone'] = coinone_symbols
            logger.info(f"📊 Coinone 심볼: {coinone_symbols}")
        
        return symbols_by_exchange
    
    async def start_rest_data_collection(self):
        """REST API 데이터 수집 시작"""
        logger.info("🔄 REST API 데이터 수집 시작...")
        
        try:
            # 모든 심볼을 대상으로 설정
            all_symbols = list(set(self.active_symbols + ['BTC-USDT', 'KRW-BTC']))
            
            market_data_collector.set_target_symbols(all_symbols)
            market_data_collector.enable_realtime_data(all_symbols, ['okx', 'upbit', 'coinone'])
            
            # 백그라운드 수집 시작
            collection_task = asyncio.create_task(
                market_data_collector.start_collection()
            )
            
            logger.info("✅ REST API 데이터 수집 시작")
            return collection_task
            
        except Exception as e:
            logger.error(f"❌ REST API 수집 시작 실패: {e}")
            raise
    
    async def monitor_service_health(self):
        """서비스 상태 모니터링"""
        logger.info("🏥 서비스 상태 모니터링 시작...")
        
        while self.running:
            try:
                await asyncio.sleep(60)  # 1분마다 체크
                
                # WebSocket 상태 확인
                ws_stats = self.websocket_manager.stats
                
                # 연결 상태 체크
                if ws_stats['active_connections'] == 0:
                    logger.error("❌ 모든 WebSocket 연결이 끊어졌습니다!")
                    self.service_stats['error_count'] += 1
                
                # 데이터 수신 상태 체크
                if ws_stats['total_messages'] == 0:
                    logger.warning("⚠️ 데이터 수신이 없습니다")
                
                # 성능 통계 로깅
                self.service_stats['total_data_points'] = ws_stats['total_messages']
                
                logger.info(
                    f"💡 서비스 상태: "
                    f"연결 {ws_stats['active_connections']}개, "
                    f"메시지 {ws_stats['total_messages']:,}개, "
                    f"오류 {self.service_stats['error_count']}개"
                )
                
                # 거래소별 상태
                for exchange, count in ws_stats['messages_per_exchange'].items():
                    logger.info(f"  📊 {exchange.upper()}: {count:,}개 메시지")
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                self.service_stats['error_count'] += 1
    
    async def cleanup(self):
        """리소스 정리"""
        logger.info("🧹 서비스 리소스 정리...")
        
        try:
            # WebSocket 연결 종료
            await self.websocket_manager.stop()
            
            # 수집기 정리
            if hasattr(market_data_collector, 'stop_collection'):
                market_data_collector.stop_collection()  # await 제거
            
            # 통계 출력
            runtime = datetime.now() - self.service_stats['start_time']
            logger.info(f"📈 서비스 실행 시간: {runtime}")
            logger.info(f"📊 총 데이터 포인트: {self.service_stats['total_data_points']:,}개")
            
        except Exception as e:
            logger.error(f"정리 중 오류: {e}")
    
    def setup_websocket_callbacks(self):
        """WebSocket 데이터 처리 콜백 설정"""
        def on_ticker_data(exchange: str, symbol: str, data: dict):
            """티커 데이터 수신 시 차익거래 분석기 업데이트"""
            try:
                price = float(data.get('last_price', 0))
                volume = float(data.get('volume', 0))
                
                if price > 0:
                    self.arbitrage_analyzer.update_price_data(
                        symbol=symbol,
                        exchange=exchange,
                        price=price,
                        volume=volume,
                        timestamp=datetime.now()
                    )
                    
                    # 주기적 차익거래 분석
                    self._check_arbitrage_analysis()
                    
            except Exception as e:
                logger.error(f"티커 데이터 처리 오류 ({exchange}, {symbol}): {e}")
        
        def on_orderbook_data(exchange: str, symbol: str, data: dict):
            """호가 데이터 수신 시 처리"""
            try:
                asks = data.get('asks', [])
                bids = data.get('bids', [])
                
                if asks and bids:
                    best_ask = float(asks[0][0])
                    best_bid = float(bids[0][0])
                    mid_price = (best_ask + best_bid) / 2
                    
                    # 스프레드 기반 거래량 계산
                    spread = best_ask - best_bid
                    volume = 1000 / spread if spread > 0 else 1000  # 임시 거래량
                    
                    self.arbitrage_analyzer.update_price_data(
                        symbol=symbol,
                        exchange=exchange,
                        price=mid_price,
                        volume=volume,
                        timestamp=datetime.now(),
                        bid=best_bid,
                        ask=best_ask
                    )
                    
            except Exception as e:
                logger.error(f"호가 데이터 처리 오류 ({exchange}, {symbol}): {e}")
        
        # 콜백 등록
        self.websocket_manager.set_data_callbacks(
            ticker_callback=on_ticker_data,
            orderbook_callback=on_orderbook_data
        )
    
    def _check_arbitrage_analysis(self):
        """차익거래 분석 체크 및 실행"""
        now = datetime.now()
        
        if (now - self.last_arbitrage_analysis).total_seconds() >= self.arbitrage_analysis_interval:
            asyncio.create_task(self._perform_arbitrage_analysis())
            self.last_arbitrage_analysis = now
    
    async def _perform_arbitrage_analysis(self):
        """차익거래 분석 수행"""
        try:
            # 차익거래 기회 탐지
            opportunities = self.arbitrage_analyzer.find_arbitrage_opportunities()
            
            if opportunities:
                self.service_stats['arbitrage_opportunities'] += len(opportunities)
                
                # 상위 기회들 로깅
                for i, opp in enumerate(opportunities[:3]):  # 상위 3개만
                    logger.info(
                        f"🎯 차익거래 기회 #{i+1}: {opp.symbol} "
                        f"{opp.buy_exchange}({opp.buy_price:.2f}) → "
                        f"{opp.sell_exchange}({opp.sell_price:.2f}) "
                        f"스프레드: {opp.spread_percentage:.2f}%"
                    )
            
            # 김치 프리미엄 계산
            kimchi_premiums = self.arbitrage_analyzer.calculate_kimchi_premium()
            
            if kimchi_premiums:
                self.service_stats['kimchi_premiums_tracked'] += len(kimchi_premiums)
                
                # 높은 프리미엄들 로깅
                significant_premiums = [kp for kp in kimchi_premiums if abs(kp.premium_percentage) > 1.0]
                
                for kp in significant_premiums[:3]:  # 상위 3개만
                    direction = "+" if kp.premium_percentage > 0 else ""
                    logger.info(
                        f"🍡 김치 프리미엄: {kp.symbol} "
                        f"{kp.korean_exchange}({kp.korean_price:.2f}) vs "
                        f"{kp.international_exchange}({kp.international_price:.2f}) "
                        f"{direction}{kp.premium_percentage:.2f}%"
                    )
            
        except Exception as e:
            logger.error(f"차익거래 분석 오류: {e}")
    
    async def start_arbitrage_analyzer(self):
        """차익거래 분석기 시작"""
        logger.info("🧮 차익거래 분석기 시작...")
        
        try:
            # 분석기 초기화
            self.arbitrage_analyzer.min_spread_percentage = 0.3  # 최소 0.3% 스프레드
            self.arbitrage_analyzer.analysis_interval = self.arbitrage_analysis_interval
            
            # WebSocket 콜백 설정
            self.setup_websocket_callbacks()
            
            # 분석기 시작
            await self.arbitrage_analyzer.start()
            
            logger.info("✅ 차익거래 분석기 시작 완료")
            
        except Exception as e:
            logger.error(f"❌ 차익거래 분석기 시작 실패: {e}")
            raise
    
    async def run(self, symbols: Optional[List[str]] = None):
        """메인 서비스 실행"""
        self.setup_signal_handlers()
        self.service_stats['start_time'] = datetime.now()
        
        logger.info("🚀 Dantaro Central 다중 거래소 실시간 서비스 시작")
        logger.info(f"📅 시작 시간: {self.service_stats['start_time']}")
        logger.info(f"⚡ 성능 모드: {self.performance_settings}")
        
        try:
            # 거래소 초기화
            await self.initialize_exchanges()
            
            # WebSocket 설정
            await self.setup_multi_exchange_websockets()
            
            # 차익거래 분석기 시작
            await self.start_arbitrage_analyzer()
            
            # REST API 수집 시작
            collection_task = await self.start_rest_data_collection()
            
            # 모니터링 시작
            monitor_task = asyncio.create_task(self.monitor_service_health())
            
            self.running = True
            logger.info("✅ 모든 서비스 시작 완료. 다중 거래소 실시간 데이터 수집 및 차익거래 분석 중...")
            
            # 메인 루프
            while self.running:
                await asyncio.sleep(1)
            
            logger.info("🛑 종료 신호 수신. 정리 작업 시작...")
            
            # 차익거래 분석기 정리
            await self.arbitrage_analyzer.stop()
            
            # 작업 정리
            for task in [collection_task, monitor_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            await self.cleanup()
            logger.info("✅ 서비스 정상 종료 완료")
            
        except Exception as e:
            logger.error(f"❌ 서비스 실행 중 오류: {e}")
            await self.cleanup()
            raise


async def main():
    """메인 함수"""
    # 최적화 설정 요약
    dantaro_optimizer.print_optimization_summary()
    
    # 활성 심볼 가져오기
    active_symbols = dantaro_optimizer.get_active_symbols()
    logger.info(f"🎯 활성 심볼 ({len(active_symbols)}개): {active_symbols}")
    
    # API 키 상태 확인
    available_exchanges = []
    if settings.okx_api_key:
        available_exchanges.append('OKX')
    available_exchanges.append('Upbit')  # 공개 API
    available_exchanges.append('Coinone')  # 공개 API로도 사용 가능
    
    logger.info(f"🔗 사용 가능한 거래소: {', '.join(available_exchanges)}")
    
    if not available_exchanges:
        logger.error("❌ 사용 가능한 거래소가 없습니다.")
        logger.error("setup_production_keys.py를 실행하여 API 키를 설정하세요.")
        return
    
    # 서비스 실행
    service = DantaroMultiExchangeService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("사용자 중단 요청")
    except Exception as e:
        logger.error(f"서비스 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("프로그램 종료")
    except Exception as e:
        logger.error(f"프로그램 실행 실패: {e}")
        sys.exit(1)
