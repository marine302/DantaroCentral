#!/usr/bin/env python3
"""
프로덕션 실시간 데이터 수집 서비스
WebSocket + REST API 통합 실시간 시장 데이터 수집
"""
import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from typing import Dict, List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.market_data_collector import market_data_collector
from app.services.okx_websocket import OKXWebSocketClient
from app.core.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/realtime_data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RealtimeDataService:
    """실시간 데이터 수집 서비스"""
    
    def __init__(self):
        self.running = False
        self.websocket_client = None
        self.data_received_count = 0
        self.last_data_time = None
        
    def setup_signal_handlers(self):
        """시그널 핸들러 설정"""
        def signal_handler(signum, frame):
            logger.info(f"시그널 {signum} 수신. 안전한 종료를 진행합니다...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def websocket_data_handler(self, data: Dict):
        """WebSocket 데이터 처리 핸들러"""
        try:
            self.data_received_count += 1
            self.last_data_time = datetime.now()
            
            # 데이터 유형별 처리
            if 'arg' in data:
                channel = data['arg'].get('channel', 'unknown')
                symbol = data['arg'].get('instId', 'unknown')
                
                if channel == 'tickers' and 'data' in data:
                    for ticker_data in data['data']:
                        price = float(ticker_data.get('last', 0))
                        bid = float(ticker_data.get('bidPx', 0))
                        ask = float(ticker_data.get('askPx', 0))
                        volume = float(ticker_data.get('vol24h', 0))
                        
                        logger.info(
                            f"📊 {symbol} - Price: ${price:,.2f}, "
                            f"Bid: ${bid:,.2f}, Ask: ${ask:,.2f}, "
                            f"Vol: {volume:,.0f}"
                        )
                
                elif channel.startswith('candle') and 'data' in data:
                    for candle_data in data['data']:
                        open_price = float(candle_data[1])
                        high_price = float(candle_data[2])
                        low_price = float(candle_data[3])
                        close_price = float(candle_data[4])
                        volume = float(candle_data[5])
                        
                        logger.info(
                            f"🕯️ {symbol} - OHLC: {open_price:.2f}/{high_price:.2f}/"
                            f"{low_price:.2f}/{close_price:.2f}, Vol: {volume:.0f}"
                        )
        
        except Exception as e:
            logger.error(f"WebSocket 데이터 처리 오류: {e}")
    
    async def initialize_exchanges(self):
        """거래소 초기화"""
        logger.info("거래소 연결 초기화...")
        
        try:
            exchange_configs = {}
            
            # OKX 설정
            if settings.okx_api_key:
                exchange_configs['okx'] = {
                    'api_key': settings.okx_api_key,
                    'secret_key': settings.okx_secret_key,
                    'passphrase': settings.okx_passphrase
                }
                logger.info("✅ OKX 거래소 설정 완료")
            
            # 추가 거래소들 (향후 확장)
            # if settings.binance_api_key:
            #     exchange_configs['binance'] = {...}
            
            if not exchange_configs:
                raise ValueError("설정된 거래소가 없습니다. .env 파일을 확인하세요.")
            
            market_data_collector.configure_exchanges(exchange_configs)
            logger.info(f"✅ {len(exchange_configs)}개 거래소 연결 완료")
            
        except Exception as e:
            logger.error(f"❌ 거래소 초기화 실패: {e}")
            raise
    
    async def setup_websocket_connection(self, symbols: List[str]):
        """WebSocket 연결 설정"""
        logger.info("WebSocket 연결 설정...")
        
        try:
            self.websocket_client = OKXWebSocketClient(
                data_handler=self.websocket_data_handler
            )
            
            await self.websocket_client.connect()
            logger.info("✅ WebSocket 연결 성공")
            
            # 티커 구독
            await self.websocket_client.subscribe_ticker(symbols)
            logger.info(f"✅ 티커 구독 완료: {symbols}")
            
            # 1분 캔들 구독
            await self.websocket_client.subscribe_candles(symbols, '1m')
            logger.info(f"✅ 1분 캔들 구독 완료: {symbols}")
            
        except Exception as e:
            logger.error(f"❌ WebSocket 설정 실패: {e}")
            raise
    
    async def start_rest_data_collection(self, symbols: List[str]):
        """REST API 데이터 수집 시작"""
        logger.info("REST API 데이터 수집 시작...")
        
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
    
    async def monitor_data_flow(self):
        """데이터 흐름 모니터링"""
        last_count = 0
        
        while self.running:
            await asyncio.sleep(30)  # 30초마다 모니터링
            
            current_count = self.data_received_count
            data_rate = current_count - last_count
            last_count = current_count
            
            logger.info(
                f"📈 데이터 수집 현황 - "
                f"총 수신: {current_count}개, "
                f"최근 30초: {data_rate}개, "
                f"마지막 수신: {self.last_data_time.strftime('%H:%M:%S') if self.last_data_time else 'N/A'}"
            )
            
            # 데이터 수신이 멈춘 경우 경고
            if self.last_data_time:
                time_since_last = (datetime.now() - self.last_data_time).total_seconds()
                if time_since_last > 120:  # 2분 이상 데이터 없음
                    logger.warning(f"⚠️ 데이터 수신이 {time_since_last:.0f}초간 중단됨")
    
    async def run(self, symbols: List[str]):
        """서비스 실행"""
        logger.info("🚀 실시간 데이터 수집 서비스 시작")
        logger.info(f"대상 심볼: {symbols}")
        logger.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.running = True
        self.setup_signal_handlers()
        
        try:
            # 거래소 초기화
            await self.initialize_exchanges()
            
            # WebSocket 연결 설정
            await self.setup_websocket_connection(symbols)
            
            # REST API 데이터 수집 시작
            collection_task = await self.start_rest_data_collection(symbols)
            
            # 모니터링 시작
            monitor_task = asyncio.create_task(self.monitor_data_flow())
            
            logger.info("✅ 모든 서비스가 시작되었습니다. 데이터 수집 중...")
            
            # 메인 루프
            while self.running:
                await asyncio.sleep(1)
            
            logger.info("서비스 종료 신호 수신. 정리 작업 시작...")
            
            # 정리 작업
            if self.websocket_client:
                await self.websocket_client.disconnect()
                logger.info("✅ WebSocket 연결 해제 완료")
            
            market_data_collector.stop_collection()
            
            # 작업 정리
            for task in [collection_task, monitor_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            logger.info("✅ 서비스 정상 종료 완료")
            
        except Exception as e:
            logger.error(f"❌ 서비스 실행 중 오류: {e}")
            raise
        
        finally:
            logger.info(f"📊 최종 통계 - 총 {self.data_received_count}개 데이터 수신")


async def main():
    """메인 함수"""
    # 주요 암호화폐 심볼
    target_symbols = [
        'BTC-USDT',
        'ETH-USDT',
        'SOL-USDT',
        'ADA-USDT',
        'DOT-USDT'
    ]
    
    # 로그 디렉토리 생성
    os.makedirs('logs', exist_ok=True)
    
    # API 키 확인
    if not settings.okx_api_key:
        logger.error("❌ OKX API 키가 설정되지 않았습니다.")
        logger.error("setup_production_keys.py를 실행하여 API 키를 설정하세요.")
        return
    
    # 서비스 실행
    service = RealtimeDataService()
    
    try:
        await service.run(target_symbols)
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
