"""
Multi-exchange WebSocket manager for real-time market data.

This module manages WebSocket connections to multiple cryptocurrency exchanges
and handles real-time data streaming, buffering, and processing.
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Callable, Any

from app.services.market_data_collector import MarketDataCollector, MarketDataPoint
from app.database.manager import db_manager
from app.database.redis_cache import redis_manager
from app.core.config import settings
from .data_buffer import RealTimeDataBuffer


class MultiExchangeWebSocketManager:
    """다중 거래소 WebSocket 관리자 (향상된 버전)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # WebSocket 클라이언트들 (거래소별)
        self.websocket_clients: Dict[str, Any] = {}
        
        # 데이터 버퍼 (거래소별 심볼별)
        self.data_buffers: Dict[str, Dict[str, RealTimeDataBuffer]] = {}  # exchange -> symbol -> buffer
        
        # 구독 관리 (거래소별)
        self.subscribed_symbols: Dict[str, Set[str]] = {}  # exchange -> symbols
        
        # 배치 처리 설정
        self.batch_interval = getattr(settings, "websocket_batch_interval", 10)  # seconds
        self.batch_size = getattr(settings, "websocket_batch_size", 100)
        
        # 상태 관리
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # 콜백 함수들
        self.ticker_callback: Optional[Callable] = None
        self.orderbook_callback: Optional[Callable] = None
        self.trade_callback: Optional[Callable] = None
        
        # 통계 (거래소별)
        self.stats = {
            'total_messages': 0,
            'messages_per_exchange': {},
            'active_connections': 0,
            'buffer_sizes': {},
            'last_batch_time': None
        }

    async def initialize_websockets(self, exchange_configs: Dict[str, Dict]):
        """WebSocket 클라이언트 초기화 (다중 거래소)"""
        
        # OKX WebSocket 초기화
        if 'okx' in exchange_configs:
            config = exchange_configs['okx']
            okx_client = OKXWebSocketClient(
                api_key=config.get('api_key') or "",
                secret_key=config.get('secret_key') or "",
                passphrase=config.get('passphrase') or ""
            )
            
            self.websocket_clients['okx'] = okx_client
            self.data_buffers['okx'] = {}
            self.subscribed_symbols['okx'] = set()
            self.stats['messages_per_exchange']['okx'] = 0
            self.logger.info("✅ OKX WebSocket client initialized")
        
        # Upbit WebSocket 초기화 (API 키 불필요 - 공개 데이터)
        if 'upbit' in exchange_configs or True:  # Upbit은 항상 사용 가능
            upbit_client = UpbitWebSocketClient(
                data_handler=self._handle_upbit_message
            )
            
            self.websocket_clients['upbit'] = upbit_client
            self.data_buffers['upbit'] = {}
            self.subscribed_symbols['upbit'] = set()
            self.stats['messages_per_exchange']['upbit'] = 0
            self.logger.info("✅ Upbit WebSocket client initialized")
        
        # Coinone WebSocket 초기화
        if 'coinone' in exchange_configs:
            config = exchange_configs['coinone']
            coinone_client = CoinoneWebSocketClient(
                api_key=config.get('api_key'),
                secret_key=config.get('secret_key'),
                data_handler=self._handle_coinone_message
            )
            
            self.websocket_clients['coinone'] = coinone_client
            self.data_buffers['coinone'] = {}
            self.subscribed_symbols['coinone'] = set()
            self.stats['messages_per_exchange']['coinone'] = 0
            self.logger.info("✅ Coinone WebSocket client initialized")
        
        # Gate.io WebSocket 초기화
        if 'gate' in exchange_configs or True:  # Gate.io는 공개 데이터로 항상 사용 가능
            config = exchange_configs.get('gate', {})
            gate_client = GateWebSocketClient(
                api_key=config.get('api_key'),
                secret_key=config.get('secret_key')
            )
            
            # Gate.io 콜백 설정
            gate_client.set_callbacks(
                on_ticker=self._handle_gate_ticker,
                on_orderbook=self._handle_gate_orderbook,
                on_trade=self._handle_gate_trade,
                on_error=self._handle_gate_error
            )
            
            self.websocket_clients['gate'] = gate_client
            self.data_buffers['gate'] = {}
            self.subscribed_symbols['gate'] = set()
            self.stats['messages_per_exchange']['gate'] = 0
            self.logger.info("✅ Gate.io WebSocket client initialized")

    # ...existing code... (connection, subscription, message handling methods)

    async def start_listening(self):
        """모든 WebSocket 리스닝 시작"""
        self.running = True
        listen_tasks = []
        
        for exchange_name, client in self.websocket_clients.items():
            if hasattr(client, 'listen'):
                task = asyncio.create_task(client.listen())
                listen_tasks.append(task)
                self.logger.info(f"🎧 {exchange_name} WebSocket 리스닝 시작")
        
        self.tasks.extend(listen_tasks)
        
        # 배치 처리 태스크 시작
        batch_task = asyncio.create_task(self._batch_processing_loop())
        self.tasks.append(batch_task)

    async def stop(self):
        """모든 WebSocket 연결 종료"""
        self.running = False
        
        # 모든 태스크 취소
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # WebSocket 연결 종료
        for exchange_name, client in self.websocket_clients.items():
            try:
                if hasattr(client, 'disconnect'):
                    await client.disconnect()
                    self.logger.info(f"🔌 {exchange_name} WebSocket 연결 종료")
            except Exception as e:
                self.logger.error(f"{exchange_name} WebSocket 종료 오류: {e}")
        
        self.logger.info("🛑 모든 WebSocket 연결이 종료되었습니다")

    def get_latest_data(self, exchange: str, symbol: str) -> Optional[RealTimeDataBuffer]:
        """최신 데이터 조회"""
        if exchange in self.data_buffers and symbol in self.data_buffers[exchange]:
            return self.data_buffers[exchange][symbol]
        return None

    def get_all_latest_data(self) -> Dict[str, Dict[str, RealTimeDataBuffer]]:
        """모든 최신 데이터 조회"""
        return self.data_buffers.copy()

    def set_data_callbacks(self, 
                          ticker_callback: Optional[Callable] = None,
                          orderbook_callback: Optional[Callable] = None,
                          trade_callback: Optional[Callable] = None):
        """데이터 처리 콜백 함수 설정"""
        self.ticker_callback = ticker_callback
        self.orderbook_callback = orderbook_callback
        self.trade_callback = trade_callback
        self.logger.info("데이터 처리 콜백 함수 설정 완료")

    # ...existing code... (additional helper methods would be here)
    
    # Simplified implementations of key methods
    async def _batch_processing_loop(self):
        """배치 처리 루프 (간소화 버전)"""
        while self.running:
            try:
                await asyncio.sleep(self.batch_interval)
                # Simplified batch processing
                self.logger.debug("배치 처리 실행")
            except Exception as e:
                self.logger.error(f"배치 처리 오류: {e}")

    async def _handle_upbit_message(self, data: Dict):
        """Upbit 메시지 처리 (간소화 버전)"""
        try:
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['upbit'] += 1
            # Simplified message handling
        except Exception as e:
            self.logger.error(f"Upbit 메시지 처리 오류: {e}")

    async def _handle_coinone_message(self, data: Dict):
        """Coinone 메시지 처리 (간소화 버전)"""
        try:
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['coinone'] += 1
            # Simplified message handling
        except Exception as e:
            self.logger.error(f"Coinone 메시지 처리 오류: {e}")

    async def _handle_gate_ticker(self, exchange: str, symbol: str, data: dict):
        """Gate.io 티커 데이터 처리 (간소화 버전)"""
        try:
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['gate'] += 1
            # Simplified ticker handling
        except Exception as e:
            self.logger.error(f"Gate.io 티커 처리 오류: {e}")

    async def _handle_gate_orderbook(self, exchange: str, symbol: str, data: dict):
        """Gate.io 오더북 데이터 처리"""
        pass

    async def _handle_gate_trade(self, exchange: str, symbol: str, data: dict):
        """Gate.io 거래 데이터 처리"""
        pass

    async def _handle_gate_error(self, error_type: str, message: str):
        """Gate.io 오류 처리"""
        self.logger.error(f"Gate.io WebSocket 오류 ({error_type}): {message}")
