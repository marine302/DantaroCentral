#!/usr/bin/env python3
"""
Dantaro Central 실시간 데이터 수집 서비스 (프로덕션 버전)
검증된 WebSocket + REST API 통합 시스템
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
from app.services.okx_websocket import OKXWebSocketClient
from app.core.config import settings
from optimization_config import dantaro_optimizer

# 로그 디렉토리 생성
os.makedirs('logs', exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/realtime_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DantaroRealtimeService:
    """Dantaro Central 실시간 데이터 수집 서비스 (최적화 버전)"""
    
    def __init__(self):
        self.running = False
        self.websocket_clients: Dict[str, OKXWebSocketClient] = {}
        self.data_stats = {
            'messages_received': 0,
            'last_message_time': None,
            'active_symbols': set(),
            'start_time': None,
            'error_count': 0,
            'reconnect_count': 0
        }
        
        # 메모리 최적화: 데이터 버퍼 크기 제한
        self.max_buffer_size = 1000
        self.recent_prices = {}  # 최근 가격 데이터 캐시
        self.performance_metrics = {
            'avg_latency': 0.0,
            'max_latency': 0.0,
            'message_rate': 0.0
        }
        
    def setup_signal_handlers(self):
        """시그널 핸들러 설정 (안전한 종료)"""
        def signal_handler(signum, frame):
            logger.info(f"종료 신호 {signum} 수신. 안전한 종료를 시작합니다...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def websocket_data_handler(self, data: Dict):
        """WebSocket 데이터 실시간 처리 (최적화된 버전)"""
        try:
            receive_time = datetime.now()
            self.data_stats['messages_received'] += 1
            self.data_stats['last_message_time'] = receive_time
            
            if 'arg' in data and 'data' in data:
                channel = data['arg'].get('channel', 'unknown')
                symbol = data['arg'].get('instId', 'unknown')
                self.data_stats['active_symbols'].add(symbol)
                
                # 성능 최적화: 중요한 데이터만 처리
                if channel == 'tickers' and data['data']:
                    ticker_info = data['data'][0]
                    price = float(ticker_info.get('last', 0))
                    volume = float(ticker_info.get('vol24h', 0))
                    
                    # 메모리 최적화: 최근 가격만 유지
                    self.recent_prices[symbol] = {
                        'price': price,
                        'volume': volume,
                        'timestamp': receive_time,
                        'bid': float(ticker_info.get('bidPx', 0)),
                        'ask': float(ticker_info.get('askPx', 0))
                    }
                    
                    # 로그 최적화: 주요 심볼만 출력
                    if symbol in ['BTC-USDT', 'ETH-USDT']:
                        logger.info(
                            f"📊 {symbol}: ${price:,.2f} "
                            f"(±{self._calculate_price_change(symbol, price):.2f}%)"
                        )
                
                elif channel.startswith('candle') and data['data']:
                    # 캔들 데이터는 중요한 변화만 로깅
                    candle_info = data['data'][0]
                    if len(candle_info) >= 5:
                        close_price = float(candle_info[4])
                        volume = float(candle_info[5])
                        
                        # 주요 심볼의 큰 변화만 로깅
                        if symbol in ['BTC-USDT', 'ETH-USDT'] and volume > 1000:
                            logger.info(
                                f"🕯️ {symbol}: Close ${close_price:,.2f} "
                                f"(Vol: {volume:,.0f})"
                            )
        
        except Exception as e:
            self.data_stats['error_count'] += 1
            if self.data_stats['error_count'] % 10 == 0:  # 10번마다 로깅
                logger.error(f"WebSocket 데이터 처리 오류 ({self.data_stats['error_count']}): {e}")
    
    def _calculate_price_change(self, symbol: str, current_price: float) -> float:
        """가격 변화율 계산 (최적화된 캐시 활용)"""
        if symbol not in self.recent_prices:
            return 0.0
        
        previous_data = self.recent_prices[symbol]
        previous_price = previous_data['price']
        
        if previous_price > 0:
            return ((current_price - previous_price) / previous_price) * 100
        return 0.0
    
    async def initialize_exchanges(self):
        """거래소 연결 초기화"""
        logger.info("🔗 거래소 연결 초기화...")
        
        exchange_configs = {}
        
        # OKX 설정 확인
        if settings.okx_api_key:
            exchange_configs['okx'] = {
                'api_key': settings.okx_api_key,
                'secret_key': settings.okx_secret_key,
                'passphrase': settings.okx_passphrase
            }
            logger.info("✅ OKX 거래소 설정 완료")
        
        if not exchange_configs:
            raise ValueError("설정된 거래소가 없습니다. API 키를 확인하세요.")
        
        market_data_collector.configure_exchanges(exchange_configs)
        logger.info(f"✅ {len(exchange_configs)}개 거래소 연결 완료")
    
    async def setup_websocket_connections(self, symbols: List[str]):
        """WebSocket 연결 설정"""
        logger.info("📡 WebSocket 연결 설정...")
        
        try:
            # OKX WebSocket 클라이언트 생성
            okx_client = OKXWebSocketClient(
                data_handler=self.websocket_data_handler
            )
            
            # 연결
            await okx_client.connect()
            logger.info("✅ OKX WebSocket 연결 성공")
            
            # 티커 구독
            await okx_client.subscribe_ticker(symbols)
            logger.info(f"✅ 티커 구독 완료: {symbols}")
            
            # 1분 캔들 구독
            await okx_client.subscribe_candles(symbols, '1m')
            logger.info(f"✅ 1분 캔들 구독 완료: {symbols}")
            
            self.websocket_clients['okx'] = okx_client
            
        except Exception as e:
            logger.error(f"❌ WebSocket 설정 실패: {e}")
            raise
    
    async def start_rest_data_collection(self, symbols: List[str]):
        """REST API 데이터 수집 시작"""
        logger.info("🔄 REST API 데이터 수집 시작...")
        
        try:
            market_data_collector.set_target_symbols(symbols)
            market_data_collector.enable_realtime_data(symbols, ['okx'])
            
            # 백그라운드에서 데이터 수집 시작
            collection_task = asyncio.create_task(
                market_data_collector.start_collection()
            )
            
            logger.info("✅ REST API 데이터 수집 시작")
            return collection_task
            
        except Exception as e:
            logger.error(f"❌ REST API 데이터 수집 시작 실패: {e}")
            raise
    
    async def monitor_service_health(self):
        """서비스 상태 모니터링 (최적화된 버전)"""
        last_message_count = 0
        last_error_count = 0
        monitoring_interval = 60  # 1분마다 모니터링
        
        while self.running:
            await asyncio.sleep(monitoring_interval)
            
            current_count = self.data_stats['messages_received']
            current_errors = self.data_stats['error_count']
            messages_per_minute = current_count - last_message_count
            errors_per_minute = current_errors - last_error_count
            
            last_message_count = current_count
            last_error_count = current_errors
            
            # 성능 지표 계산
            uptime = (datetime.now() - self.data_stats['start_time']).total_seconds()
            avg_message_rate = current_count / (uptime / 60) if uptime > 0 else 0
            error_rate = (current_errors / current_count * 100) if current_count > 0 else 0
            
            # 메모리 사용량 최적화: 불필요한 데이터 정리
            self._cleanup_old_data()
            
            # 최적화된 로깅: 중요한 정보만
            if messages_per_minute > 0 or current_count % 1000 == 0:
                logger.info(
                    f"📈 서비스 상태 - "
                    f"가동: {uptime/60:.1f}분 | "
                    f"메시지: {current_count:,}개 ({avg_message_rate:.1f}/분) | "
                    f"심볼: {len(self.data_stats['active_symbols'])}개 | "
                    f"오류율: {error_rate:.2f}%"
                )
            
            # 데이터 수신 중단 경고 (임계값 조정)
            if self.data_stats['last_message_time']:
                time_since_last = (datetime.now() - self.data_stats['last_message_time']).total_seconds()
                if time_since_last > 180:  # 3분 이상 데이터 없음
                    logger.warning(f"⚠️ 데이터 수신 중단: {time_since_last/60:.1f}분")
                    
                    # 자동 재연결 시도
                    if time_since_last > 300:  # 5분 이상 중단 시
                        logger.info("🔄 자동 재연결 시도...")
                        await self._attempt_reconnection()
            
            # 메모리 사용량 경고
            active_symbols_count = len(self.data_stats['active_symbols'])
            if active_symbols_count > 50:
                logger.warning(f"⚠️ 높은 심볼 수: {active_symbols_count}개")
    
    def _cleanup_old_data(self):
        """오래된 데이터 정리 (메모리 최적화)"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(minutes=5)  # 5분 이상 된 데이터 제거
            
            # 오래된 가격 데이터 정리
            symbols_to_remove = []
            for symbol, data in self.recent_prices.items():
                if data['timestamp'] < cutoff_time:
                    symbols_to_remove.append(symbol)
            
            for symbol in symbols_to_remove:
                del self.recent_prices[symbol]
                self.data_stats['active_symbols'].discard(symbol)
            
            if symbols_to_remove:
                logger.debug(f"🧹 정리된 심볼: {len(symbols_to_remove)}개")
                
        except Exception as e:
            logger.error(f"데이터 정리 중 오류: {e}")
    
    async def _attempt_reconnection(self):
        """자동 재연결 시도"""
        try:
            self.data_stats['reconnect_count'] += 1
            logger.info(f"🔄 재연결 시도 #{self.data_stats['reconnect_count']}")
            
            # 기존 연결 정리
            for exchange, client in self.websocket_clients.items():
                try:
                    await client.disconnect()
                except Exception as e:
                    logger.warning(f"기존 연결 해제 오류 ({exchange}): {e}")
            
            self.websocket_clients.clear()
            
            # 잠시 대기 후 재연결
            await asyncio.sleep(5)
            
            # 메인 심볼들만 재연결 (최적화)
            core_symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT']
            await self.setup_websocket_connections(core_symbols)
            
            logger.info("✅ 자동 재연결 완료")
            
        except Exception as e:
            logger.error(f"❌ 자동 재연결 실패: {e}")
    
    async def cleanup(self):
        """서비스 정리 작업"""
        logger.info("🧹 서비스 정리 작업 시작...")
        
        # WebSocket 연결 해제
        for exchange, client in self.websocket_clients.items():
            try:
                await client.disconnect()
                logger.info(f"✅ {exchange} WebSocket 연결 해제 완료")
            except Exception as e:
                logger.error(f"❌ {exchange} WebSocket 해제 오류: {e}")
        
        # REST API 수집 중지
        market_data_collector.stop_collection()
        logger.info("✅ REST API 데이터 수집 중지")
        
        # 최종 통계
        total_messages = self.data_stats['messages_received']
        uptime = (datetime.now() - self.data_stats['start_time']).total_seconds()
        avg_rate = total_messages / (uptime / 60) if uptime > 0 else 0
        
        logger.info(
            f"📊 최종 통계 - "
            f"총 메시지: {total_messages:,}개, "
            f"가동시간: {uptime/60:.1f}분, "
            f"평균 분당: {avg_rate:.1f}개"
        )
    
    async def run(self, symbols: List[str]):
        """서비스 메인 실행"""
        logger.info("🚀 Dantaro Central 실시간 데이터 수집 서비스 시작")
        logger.info(f"대상 심볼: {symbols}")
        logger.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.running = True
        self.data_stats['start_time'] = datetime.now()
        self.setup_signal_handlers()
        
        try:
            # 시스템 초기화
            await self.initialize_exchanges()
            await self.setup_websocket_connections(symbols)
            
            # 데이터 수집 시작
            collection_task = await self.start_rest_data_collection(symbols)
            monitor_task = asyncio.create_task(self.monitor_service_health())
            
            logger.info("✅ 모든 서비스 시작 완료. 실시간 데이터 수집 중...")
            
            # 메인 루프
            while self.running:
                await asyncio.sleep(1)
            
            logger.info("🛑 종료 신호 수신. 정리 작업 시작...")
            
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
    """메인 함수 (최적화된 심볼 목록)"""
    # 최적화 설정 요약 출력
    dantaro_optimizer.print_optimization_summary()
    
    # 최적화된 심볼 목록 가져오기
    production_symbols = dantaro_optimizer.get_active_symbols()
    logger.info(f"� 선택된 심볼 ({len(production_symbols)}개): {production_symbols}")
    
    # 성능 설정 적용
    performance_settings = dantaro_optimizer.get_performance_settings()
    logger.info(f"⚡ 성능 모드: {performance_settings}")
    
    # API 키 확인
    if not settings.okx_api_key:
        logger.error("❌ OKX API 키가 설정되지 않았습니다.")
        logger.error("다음 명령으로 API 키를 설정하세요:")
        logger.error("python3 setup_production_keys.py")
        return
    
    # 서비스 실행
    service = DantaroRealtimeService()
    
    try:
        await service.run(production_symbols)
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
