#!/usr/bin/env python3
"""
Dantaro Central 메인 오케스트레이터 (클린 버전)
모듈화된 서비스들을 조율하는 메인 컨트롤러
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# 모듈화된 서비스들
from app.services.realtime_data_service import RealTimeDataService, DataServiceConfig
from app.services.arbitrage_analysis_service import ArbitrageAnalysisService, AnalysisServiceConfig
from app.services.notification_service import NotificationService, AlertConfig
from app.core.config import settings
from optimization_config import dantaro_optimizer

# 로그 디렉토리 생성
os.makedirs('logs', exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dantaro_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DantaroCentralOrchestrator:
    """Dantaro Central 메인 오케스트레이터"""
    
    def __init__(self):
        # 서비스 설정
        self.data_config = DataServiceConfig(
            analysis_interval=10,
            reconnect_attempts=5,
            enable_logging=True
        )
        
        self.analysis_config = AnalysisServiceConfig(
            analysis_interval=10,
            min_spread_percentage=0.5,
            min_premium_for_alert=2.0,
            enable_auto_analysis=True
        )
        
        self.alert_config = AlertConfig(
            min_spread_for_alert=1.5,
            min_premium_for_alert=2.0,
            critical_spread_threshold=5.0,
            critical_premium_threshold=8.0,
            max_alerts_per_minute=10
        )
        
        # 서비스 인스턴스들
        self.data_service = RealTimeDataService(self.data_config)
        self.analysis_service = ArbitrageAnalysisService(self.analysis_config)
        self.notification_service = NotificationService(self.alert_config)
        
        # 실행 상태
        self.running = False
        self.start_time = None
        
        # 모니터링 태스크
        self.monitor_task = None
    
    def setup_signal_handlers(self):
        """시그널 핸들러 설정"""
        def signal_handler(signum, frame):
            logger.info(f"종료 신호 {signum} 수신. 안전한 종료를 시작합니다...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _setup_service_connections(self):
        """서비스간 연결 설정"""
        # 데이터 서비스 -> 분석 서비스 연결
        def on_ticker_data(exchange: str, symbol: str, data: dict):
            """티커 데이터를 분석 서비스로 전달"""
            try:
                price = float(data.get('last_price', 0))
                volume = float(data.get('volume', 0))
                
                if price > 0:
                    self.analysis_service.update_price_data(
                        symbol=symbol,
                        exchange=exchange,
                        price=price,
                        volume=volume,
                        timestamp=datetime.now()
                    )
            except Exception as e:
                logger.error(f"티커 데이터 전달 오류: {e}")
        
        self.data_service.set_data_callback('ticker', on_ticker_data)
        
        # 분석 서비스 -> 알림 서비스 연결
        self.analysis_service.add_opportunity_callback(
            self.notification_service.process_arbitrage_opportunities
        )
        self.analysis_service.add_premium_callback(
            self.notification_service.process_kimchi_premiums
        )
        
        logger.info("✅ 서비스간 연결 설정 완료")
    
    def _get_exchange_configs(self) -> Dict[str, Dict]:
        """거래소 설정 구성"""
        exchange_configs = {}
        
        # OKX 설정
        if hasattr(settings, 'okx_api_key') and settings.okx_api_key:
            exchange_configs['okx'] = {
                'api_key': settings.okx_api_key,
                'secret_key': settings.okx_secret_key,
                'passphrase': settings.okx_passphrase
            }
            logger.info("✅ OKX 거래소 설정 완료")
        else:
            logger.warning("⚠️ OKX API 키가 없습니다")
        
        # Upbit 설정 (공개 API)
        exchange_configs['upbit'] = {}
        logger.info("✅ Upbit 거래소 설정 완료")
        
        # Coinone 설정
        if hasattr(settings, 'coinone_api_key') and settings.coinone_api_key:
            exchange_configs['coinone'] = {
                'api_key': settings.coinone_api_key,
                'secret_key': settings.coinone_secret_key
            }
            logger.info("✅ Coinone 거래소 설정 완료")
        else:
            logger.warning("⚠️ Coinone API 키가 없습니다")
        
        # Gate.io 설정 (공개 API로도 사용 가능)
        if hasattr(settings, 'gate_api_key') and settings.gate_api_key:
            exchange_configs['gate'] = {
                'api_key': settings.gate_api_key,
                'secret_key': settings.gate_secret_key
            }
            logger.info("✅ Gate.io 거래소 설정 완료 (인증)")
        else:
            exchange_configs['gate'] = {}  # 공개 API로 사용
            logger.info("✅ Gate.io 거래소 설정 완료 (공개 API)")
        
        return exchange_configs
    
    def _get_symbols_by_exchange(self) -> Dict[str, List[str]]:
        """거래소별 심볼 매핑"""
        active_symbols = dantaro_optimizer.get_active_symbols()
        
        symbols_by_exchange = {}
        
        # OKX 심볼 (국제 표준)
        okx_symbols = [symbol for symbol in active_symbols if '-USDT' in symbol]
        if not okx_symbols:
            okx_symbols = ['DOGE-USDT', 'ADA-USDT', 'MATIC-USDT', 'SOL-USDT', 'AVAX-USDT']
        symbols_by_exchange['okx'] = okx_symbols
        
        # Upbit 심볼 (KRW 기준)
        upbit_symbols = [symbol for symbol in active_symbols if 'KRW-' in symbol]
        if not upbit_symbols:
            upbit_symbols = ['KRW-DOGE', 'KRW-ADA', 'KRW-MATIC', 'KRW-SOL', 'KRW-AVAX']
        symbols_by_exchange['upbit'] = upbit_symbols
        
        # Coinone 심볼 (기본 심볼명)
        coinone_symbols = []
        for symbol in active_symbols:
            if '-' in symbol:
                base_symbol = symbol.split('-')[0] if symbol.startswith('KRW-') else symbol.split('-')[0]
                coinone_symbols.append(base_symbol)
            else:
                coinone_symbols.append(symbol)
        
        if not coinone_symbols:
            coinone_symbols = ['DOGE', 'ADA', 'MATIC', 'SOL', 'AVAX']
        
        symbols_by_exchange['coinone'] = list(set(coinone_symbols))
        
        # Gate.io 심볼 (국제 표준, OKX와 유사)
        gate_symbols = [symbol for symbol in active_symbols if '-USDT' in symbol]
        if not gate_symbols:
            gate_symbols = ['DOGE-USDT', 'ADA-USDT', 'MATIC-USDT', 'SOL-USDT', 'AVAX-USDT']
        symbols_by_exchange['gate'] = gate_symbols
        
        return symbols_by_exchange
    
    async def initialize_services(self):
        """모든 서비스 초기화"""
        logger.info("🔧 서비스 초기화 시작...")
        
        try:
            # 서비스간 연결 설정
            self._setup_service_connections()
            
            # 거래소 설정
            exchange_configs = self._get_exchange_configs()
            symbols_by_exchange = self._get_symbols_by_exchange()
            
            # 데이터 서비스 설정
            self.data_service.configure_exchanges(exchange_configs)
            self.data_service.set_symbols(symbols_by_exchange)
            
            # 서비스 초기화
            await self.data_service.initialize()
            await self.analysis_service.start()
            
            logger.info("✅ 모든 서비스 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ 서비스 초기화 실패: {e}")
            raise
    
    async def start_services(self):
        """모든 서비스 시작"""
        logger.info("🚀 서비스 시작...")
        
        try:
            # 데이터 수집 시작
            await self.data_service.start()
            
            logger.info("✅ 모든 서비스 시작 완료")
            
        except Exception as e:
            logger.error(f"❌ 서비스 시작 실패: {e}")
            raise
    
    async def stop_services(self):
        """모든 서비스 중지"""
        logger.info("🛑 서비스 중지...")
        
        try:
            # 모니터링 태스크 중지
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            
            # 서비스 중지 (역순)
            await self.analysis_service.stop()
            await self.data_service.stop()
            
            logger.info("✅ 모든 서비스 중지 완료")
            
        except Exception as e:
            logger.error(f"❌ 서비스 중지 중 오류: {e}")
    
    async def monitor_system_health(self):
        """시스템 상태 모니터링"""
        logger.info("🏥 시스템 상태 모니터링 시작...")
        
        while self.running:
            try:
                await asyncio.sleep(60)  # 1분마다 체크
                
                # 서비스 상태 체크
                data_stats = self.data_service.get_stats()
                analysis_stats = self.analysis_service.get_stats()
                alert_stats = self.notification_service.get_stats()
                
                # 상태 로깅
                logger.info(
                    f"💡 시스템 상태: "
                    f"데이터 {data_stats['total_messages']:,}개, "
                    f"분석 {analysis_stats['total_analyses']:,}회, "
                    f"알림 {alert_stats['total_alerts']:,}개"
                )
                
                # 거래소별 연결 상태
                connection_status = self.data_service.get_connection_status()
                for exchange, connected in connection_status.items():
                    status = "🟢" if connected else "🔴"
                    logger.info(f"  {status} {exchange.upper()}: {'연결됨' if connected else '연결 끊김'}")
                
                # 추적 심볼 상태
                tracked_symbols = self.analysis_service.get_tracked_symbols()
                logger.info(f"  📊 추적 중인 심볼: {len(tracked_symbols)}개")
                
            except Exception as e:
                logger.error(f"시스템 모니터링 오류: {e}")
    
    async def run(self):
        """메인 실행 함수"""
        self.setup_signal_handlers()
        self.start_time = datetime.now()
        
        logger.info("🚀 Dantaro Central 오케스트레이터 시작")
        logger.info(f"📅 시작 시간: {self.start_time}")
        
        # 성능 설정 출력
        dantaro_optimizer.print_optimization_summary()
        
        try:
            # 서비스 초기화 및 시작
            await self.initialize_services()
            await self.start_services()
            
            # 모니터링 시작
            self.monitor_task = asyncio.create_task(self.monitor_system_health())
            
            self.running = True
            logger.info("✅ 모든 시스템 시작 완료. 실시간 차익거래 모니터링 중...")
            
            # 메인 루프
            while self.running:
                await asyncio.sleep(1)
            
            logger.info("🛑 종료 신호 수신. 시스템 종료 중...")
            
        except Exception as e:
            logger.error(f"❌ 시스템 실행 중 오류: {e}")
            raise
        
        finally:
            # 서비스 정리
            await self.stop_services()
            
            # 실행 통계
            if self.start_time:
                runtime = datetime.now() - self.start_time
                logger.info(f"📈 총 실행 시간: {runtime}")
            
            logger.info("✅ Dantaro Central 오케스트레이터 종료 완료")


async def main():
    """메인 함수"""
    orchestrator = DantaroCentralOrchestrator()
    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
