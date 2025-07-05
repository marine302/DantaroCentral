"""
WebSocket 기반 실시간 마켓 데이터 수집 관리자 (다중 거래소 지원)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
import json

from app.services.okx_websocket import OKXWebSocketClient, WebSocketMessage
from app.services.upbit_websocket import UpbitWebSocketClient
from app.services.coinone_websocket import CoinoneWebSocketClient
from app.services.gate_websocket import GateWebSocketClient
from app.services.market_data_collector import MarketDataCollector, MarketDataPoint
from app.database.manager import db_manager
from app.database.redis_cache import redis_manager
from app.core.config import settings


@dataclass
class RealTimeDataBuffer:
    """실시간 데이터 버퍼"""
    symbol: str
    exchange: str
    latest_price: float = 0.0
    latest_volume: float = 0.0
    price_updates: List[tuple] = field(default_factory=list)  # (timestamp, price)
    volume_updates: List[tuple] = field(default_factory=list)  # (timestamp, volume)
    last_update: datetime = field(default_factory=datetime.now)
    
    def add_update(self, price: float, volume: float):
        """새로운 업데이트 추가"""
        now = datetime.now()
        
        self.latest_price = price
        self.latest_volume = volume
        self.last_update = now
        
        # 최근 100개 업데이트만 유지
        self.price_updates.append((now, price))
        self.volume_updates.append((now, volume))
        
        if len(self.price_updates) > 100:
            self.price_updates = self.price_updates[-100:]
        if len(self.volume_updates) > 100:
            self.volume_updates = self.volume_updates[-100:]


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
        
        # Coinone WebSocket 초기화 (추가된 부분)
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
        
        # Gate.io WebSocket 초기화 (새로 추가)
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

    async def connect_all_websockets(self):
        """모든 WebSocket 연결"""
        connection_tasks = []
        
        for exchange_name, client in self.websocket_clients.items():
            if hasattr(client, 'connect'):
                task = self._connect_single_websocket(exchange_name, client)
                connection_tasks.append(task)
        
        if connection_tasks:
            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            
            successful_connections = 0
            for i, result in enumerate(results):
                exchange_name = list(self.websocket_clients.keys())[i]
                if isinstance(result, Exception):
                    self.logger.error(f"❌ {exchange_name} WebSocket 연결 실패: {result}")
                elif result:
                    successful_connections += 1
                    self.logger.info(f"✅ {exchange_name} WebSocket 연결 성공")
            
            self.stats['active_connections'] = successful_connections
            self.logger.info(f"🔗 총 {successful_connections}개 WebSocket 연결 완료")

    async def _connect_single_websocket(self, exchange_name: str, client) -> bool:
        """단일 WebSocket 연결"""
        try:
            return await client.connect()
        except Exception as e:
            self.logger.error(f"{exchange_name} WebSocket 연결 중 오류: {e}")
            return False

    async def subscribe_to_symbols(self, symbols_by_exchange: Dict[str, List[str]]):
        """거래소별 심볼 구독"""
        
        for exchange_name, symbols in symbols_by_exchange.items():
            if exchange_name not in self.websocket_clients:
                self.logger.warning(f"거래소 {exchange_name}이 초기화되지 않았습니다")
                continue
                
            try:
                client = self.websocket_clients[exchange_name]
                
                if exchange_name == 'okx' and hasattr(client, 'subscribe_ticker'):
                    # OKX WebSocket 시세 구독
                    await client.subscribe_ticker(symbols, self._handle_okx_ticker_message)
                    self.subscribed_symbols['okx'].update(symbols)
                    self.logger.info(f"📊 OKX에서 {len(symbols)}개 심볼 구독 완료: {symbols}")
                
                elif exchange_name == 'upbit' and hasattr(client, 'subscribe_ticker'):
                    # Upbit WebSocket 시세 구독
                    await client.subscribe_ticker(symbols)
                    self.subscribed_symbols['upbit'].update(symbols)
                    self.logger.info(f"📊 Upbit에서 {len(symbols)}개 심볼 구독 완료: {symbols}")
                
                elif exchange_name == 'coinone' and hasattr(client, 'subscribe_ticker'):
                    # Coinone WebSocket 시세 구독
                    await client.subscribe_ticker(symbols)
                    self.subscribed_symbols['coinone'].update(symbols)
                    self.logger.info(f"📊 Coinone에서 {len(symbols)}개 심볼 구독 완료: {symbols}")
                
                elif exchange_name == 'gate' and hasattr(client, 'subscribe_ticker'):
                    # Gate.io WebSocket 시세 구독
                    await client.subscribe_ticker(symbols)
                    self.subscribed_symbols['gate'].update(symbols)
                    self.logger.info(f"📊 Gate.io에서 {len(symbols)}개 심볼 구독 완료: {symbols}")
                
                # 다른 거래소 구독 로직 추가 가능
                
            except Exception as e:
                self.logger.error(f"❌ {exchange_name}에서 심볼 구독 실패: {e}")

    def _handle_okx_ticker_message(self, message: WebSocketMessage):
        """OKX 시세 메시지 처리"""
        try:
            symbol = message.symbol
            exchange = 'okx'
            
            # 통계 업데이트
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['okx'] += 1
            
            # 데이터 버퍼 업데이트
            if symbol not in self.data_buffers[exchange]:
                self.data_buffers[exchange][symbol] = RealTimeDataBuffer(symbol, exchange)
            
            buffer = self.data_buffers[exchange][symbol]
            buffer.add_update(message.price, message.volume)
            
            # 버퍼 크기 통계 업데이트
            self.stats['buffer_sizes']['okx'] = len(self.data_buffers['okx'])
            
            # 콜백 호출
            if self.ticker_callback:
                ticker_data = {
                    'last_price': message.price,
                    'volume': message.volume,
                    'timestamp': message.timestamp.isoformat() if message.timestamp else None
                }
                self.ticker_callback(exchange, symbol, ticker_data)
            
        except Exception as e:
            self.logger.error(f"OKX 메시지 처리 오류: {e}")

    async def _handle_upbit_message(self, data: Dict):
        """Upbit 메시지 처리"""
        try:
            symbol = data.get('code', 'unknown')
            exchange = 'upbit'
            msg_type = data.get('type', 'unknown')
            
            # 통계 업데이트
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['upbit'] += 1
            
            # 티커 데이터만 처리
            if msg_type == 'ticker':
                price = data.get('trade_price', 0)
                volume = data.get('acc_trade_volume_24h', 0)
                
                # 데이터 버퍼 업데이트
                if symbol not in self.data_buffers[exchange]:
                    self.data_buffers[exchange][symbol] = RealTimeDataBuffer(symbol, exchange)
                
                buffer = self.data_buffers[exchange][symbol]
                buffer.add_update(price, volume)
                
                # 버퍼 크기 통계 업데이트
                self.stats['buffer_sizes']['upbit'] = len(self.data_buffers['upbit'])
                
                # 콜백 호출
                if self.ticker_callback:
                    ticker_data = {
                        'last_price': price,
                        'volume': volume,
                        'timestamp': data.get('trade_timestamp', data.get('timestamp'))
                    }
                    self.ticker_callback(exchange, symbol, ticker_data)
            
        except Exception as e:
            self.logger.error(f"Upbit 메시지 처리 오류: {e}")

    async def _handle_coinone_message(self, data: Dict):
        """Coinone 메시지 처리"""
        try:
            response_type = data.get('response_type', 'unknown')
            channel = data.get('channel', 'unknown')
            exchange = 'coinone'
            
            # 통계 업데이트
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['coinone'] += 1
            
            # 데이터 메시지만 처리
            if response_type == 'DATA' and channel == 'TICKER':
                ticker_data = data.get('data', {})
                symbol = ticker_data.get('target_currency', 'unknown')
                price = float(ticker_data.get('last', 0))
                volume = float(ticker_data.get('volume', 0))
                
                # 데이터 버퍼 업데이트
                if symbol not in self.data_buffers[exchange]:
                    self.data_buffers[exchange][symbol] = RealTimeDataBuffer(symbol, exchange)
                
                buffer = self.data_buffers[exchange][symbol]
                buffer.add_update(price, volume)
                
                # 버퍼 크기 통계 업데이트
                self.stats['buffer_sizes']['coinone'] = len(self.data_buffers['coinone'])
                
                # 콜백 호출
                if self.ticker_callback:
                    callback_ticker_data = {
                        'last_price': price,
                        'volume': volume,
                        'timestamp': ticker_data.get('timestamp')
                    }
                    self.ticker_callback(exchange, symbol, callback_ticker_data)
            
        except Exception as e:
            self.logger.error(f"Coinone 메시지 처리 오류: {e}")

    # Gate.io WebSocket 메시지 핸들러들
    async def _handle_gate_ticker(self, exchange: str, symbol: str, data: dict):
        """Gate.io 티커 데이터 처리"""
        try:
            # 통계 업데이트
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['gate'] += 1
            
            price = data.get('last_price', 0)
            volume = data.get('volume', 0)
            
            # 데이터 버퍼 업데이트
            if 'gate' not in self.data_buffers:
                self.data_buffers['gate'] = {}
            
            if symbol not in self.data_buffers['gate']:
                self.data_buffers['gate'][symbol] = RealTimeDataBuffer(symbol, 'gate')
            
            buffer = self.data_buffers['gate'][symbol]
            buffer.add_update(price, volume)
            
            # 버퍼 크기 통계 업데이트
            self.stats['buffer_sizes']['gate'] = len(self.data_buffers['gate'])
            
            # 콜백 호출
            if self.ticker_callback:
                self.ticker_callback('gate', symbol, data)
                
        except Exception as e:
            self.logger.error(f"Gate.io 티커 처리 오류: {e}")

    async def _handle_gate_orderbook(self, exchange: str, symbol: str, data: dict):
        """Gate.io 오더북 데이터 처리"""
        try:
            # 통계 업데이트
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['gate'] += 1
            
            # 오더북 콜백 호출
            if self.orderbook_callback:
                self.orderbook_callback('gate', symbol, data)
                
        except Exception as e:
            self.logger.error(f"Gate.io 오더북 처리 오류: {e}")

    async def _handle_gate_trade(self, exchange: str, symbol: str, data: dict):
        """Gate.io 거래 데이터 처리"""
        try:
            # 통계 업데이트
            self.stats['total_messages'] += 1
            self.stats['messages_per_exchange']['gate'] += 1
            
            # 거래 콜백 호출
            if self.trade_callback:
                self.trade_callback('gate', symbol, data)
                
        except Exception as e:
            self.logger.error(f"Gate.io 거래 처리 오류: {e}")

    async def _handle_gate_error(self, error_type: str, message: str):
        """Gate.io 오류 처리"""
        self.logger.error(f"Gate.io WebSocket 오류 ({error_type}): {message}")
    
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
        
        # 통계 출력 태스크 시작
        stats_task = asyncio.create_task(self._stats_reporting_loop())
        self.tasks.append(stats_task)

    async def _batch_processing_loop(self):
        """배치 처리 루프"""
        while self.running:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._process_batch_data()
                
            except Exception as e:
                self.logger.error(f"배치 처리 오류: {e}")

    async def _process_batch_data(self):
        """배치 데이터 처리"""
        try:
            current_time = datetime.now()
            processed_count = 0
            
            for exchange_name, symbol_buffers in self.data_buffers.items():
                for symbol, buffer in symbol_buffers.items():
                    if buffer.price_updates:
                        # 최신 데이터를 MarketDataPoint로 변환
                        latest_price = buffer.latest_price
                        latest_volume = buffer.latest_volume
                        
                        data_point = MarketDataPoint(
                            symbol=symbol,
                            exchange=exchange_name,
                            price=latest_price,
                            volume_24h=latest_volume,
                            change_24h=0.0,  # 변화율 계산 로직 필요시 추가
                            timestamp=buffer.last_update
                        )
                        
                        # Redis 캐시에 저장 (간단한 방식)
                        if redis_manager:
                            try:
                                cache_key = f"realtime:{exchange_name}:{symbol}"
                                cache_data = {
                                    'symbol': symbol,
                                    'exchange': exchange_name,
                                    'price': latest_price,
                                    'volume': latest_volume,
                                    'timestamp': buffer.last_update.isoformat()
                                }
                                # Redis에 JSON 문자열로 저장
                                redis_manager.redis_client.setex(
                                    cache_key, 
                                    60,  # 1분 TTL
                                    json.dumps(cache_data, default=str)
                                )
                            except Exception as redis_error:
                                self.logger.warning(f"Redis 캐시 저장 실패: {redis_error}")
                        
                        processed_count += 1
                        
                        # 버퍼 클리어 (메모리 최적화)
                        buffer.price_updates.clear()
                        buffer.volume_updates.clear()
            
            self.stats['last_batch_time'] = current_time
            if processed_count > 0:
                self.logger.info(f"📦 배치 처리 완료: {processed_count}개 데이터 포인트")
                
        except Exception as e:
            self.logger.error(f"배치 데이터 처리 오류: {e}")

    async def _stats_reporting_loop(self):
        """통계 보고 루프"""
        while self.running:
            try:
                await asyncio.sleep(60)  # 1분마다 통계 출력
                await self._report_stats()
                
            except Exception as e:
                self.logger.error(f"통계 보고 오류: {e}")

    async def _report_stats(self):
        """통계 보고"""
        try:
            total_symbols = sum(len(symbols) for symbols in self.subscribed_symbols.values())
            total_buffers = sum(len(buffers) for buffers in self.data_buffers.values())
            
            self.logger.info(
                f"📈 실시간 데이터 통계: "
                f"연결: {self.stats['active_connections']}개, "
                f"구독 심볼: {total_symbols}개, "
                f"버퍼: {total_buffers}개, "
                f"총 메시지: {self.stats['total_messages']:,}개"
            )
            
            # 거래소별 상세 통계
            for exchange, count in self.stats['messages_per_exchange'].items():
                buffer_count = self.stats['buffer_sizes'].get(exchange, 0)
                self.logger.info(f"  📊 {exchange.upper()}: {count:,}개 메시지, {buffer_count}개 버퍼")
                
        except Exception as e:
            self.logger.error(f"통계 보고 처리 오류: {e}")

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


# 기존 WebSocketDataManager를 위한 호환성 유지
class WebSocketDataManager(MultiExchangeWebSocketManager):
    """기존 코드와의 호환성을 위한 래퍼 클래스"""
    pass
