"""
OKX WebSocket 실시간 데이터 클라이언트
"""

import asyncio
import json
import logging
import time
import hmac
import base64
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

@dataclass
class WebSocketMessage:
    """WebSocket 메시지 데이터 클래스"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    exchange: str = "okx"

class OKXWebSocketClient:
    """OKX WebSocket 실시간 데이터 클라이언트"""
    
    # OKX WebSocket 엔드포인트
    WEBSOCKET_URL = "wss://ws.okx.com:8443/ws/v5/public"
    PRIVATE_WEBSOCKET_URL = "wss://ws.okx.com:8443/ws/v5/private"
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 passphrase: Optional[str] = None, data_handler: Optional[Callable] = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        
        # 연결 상태
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.running = False
        
        # 구독 관리
        self.subscriptions: Dict[str, Dict] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # 데이터 핸들러
        self.data_handler = data_handler
        
        # 성능 최적화 설정
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # 초
        self.heartbeat_interval = 30  # 초
        self.message_queue_size = 1000  # 메시지 큐 크기 제한
        
        # 통계 및 모니터링 (최적화)
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'reconnect_count': 0,
            'last_message_time': None,
            'connection_start_time': None,
            'error_count': 0
        }
        
        # 로깅
        self.logger = logging.getLogger(f"{__name__}.OKXWebSocket")
        
        # 재연결 설정
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        
        # 통계
        self.stats = {
            'messages_received': 0,
            'last_message_time': None,
            'connection_start_time': None,
            'reconnect_count': 0
        }
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """OKX API 서명 생성"""
        if not all([self.api_key, self.secret_key, self.passphrase]):
            raise ValueError("API credentials are required for private channels")
        
        message = timestamp + method + request_path + body
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                'sha256'
            ).digest()
        ).decode('utf-8')
        
        return signature
    
    def _create_auth_message(self) -> Dict:
        """인증 메시지 생성"""
        timestamp = str(int(time.time()))
        method = "GET"
        request_path = "/users/self/verify"
        
        signature = self._generate_signature(timestamp, method, request_path)
        
        return {
            "op": "login",
            "args": [{
                "apiKey": self.api_key,
                "passphrase": self.passphrase,
                "timestamp": timestamp,
                "sign": signature
            }]
        }
    
    def _create_subscription_message(self, channel: str, symbols: List[str]) -> Dict:
        """구독 메시지 생성"""
        args = []
        for symbol in symbols:
            args.append({
                "channel": channel,
                "instId": symbol
            })
        
        return {
            "op": "subscribe",
            "args": args
        }
    
    async def connect(self, use_private: bool = False) -> bool:
        """WebSocket 연결"""
        try:
            url = self.PRIVATE_WEBSOCKET_URL if use_private else self.WEBSOCKET_URL
            
            self.logger.info(f"Connecting to OKX WebSocket: {url}")
            self.websocket = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            self.stats['connection_start_time'] = datetime.now()
            self.reconnect_attempts = 0
            
            self.logger.info("OKX WebSocket connected successfully")
            
            # 프라이빗 채널 사용 시 인증
            if use_private and all([self.api_key, self.secret_key, self.passphrase]):
                auth_message = self._create_auth_message()
                await self.websocket.send(json.dumps(auth_message))
                self.logger.info("Authentication message sent")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to OKX WebSocket: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        self.running = False
        if self.websocket:
            try:
                if hasattr(self.websocket, 'closed') and not self.websocket.closed:
                    await self.websocket.close()
                elif hasattr(self.websocket, 'close'):
                    await self.websocket.close()
            except Exception as e:
                self.logger.warning(f"Error during disconnect: {e}")
        self.websocket = None
        self.connected = False
        self.logger.info("OKX WebSocket disconnected")
    
    async def subscribe_ticker(self, symbols: List[str], callback: Optional[Callable] = None):
        """실시간 시세 구독"""
        channel = "tickers"
        
        # 콜백 등록 (있는 경우에만)
        if callback:
            self.message_handlers[channel] = callback
        
        # 구독 메시지 전송
        subscription_message = self._create_subscription_message(channel, symbols)
        await self.websocket.send(json.dumps(subscription_message))
        
        # 구독 정보 저장
        self.subscriptions[channel] = {
            'symbols': symbols,
            'callback': callback,
            'subscribed_at': datetime.now()
        }
        
        self.logger.info(f"Subscribed to ticker data for symbols: {symbols}")
    
    async def subscribe_candle(self, symbols: List[str], timeframe: str = "1m", 
                             callback: Optional[Callable] = None):
        """실시간 캔들 데이터 구독"""
        channel = f"candle{timeframe}"
        
        if callback:
            self.message_handlers[channel] = callback
        
        subscription_message = self._create_subscription_message(channel, symbols)
        await self.websocket.send(json.dumps(subscription_message))
        
        self.subscriptions[channel] = {
            'symbols': symbols,
            'timeframe': timeframe,
            'callback': callback,
            'subscribed_at': datetime.now()
        }
        
        self.logger.info(f"Subscribed to {timeframe} candle data for symbols: {symbols}")
    
    async def subscribe_candles(self, symbols: List[str], timeframe: str = "1m", 
                              callback: Optional[Callable] = None):
        """실시간 캔들 데이터 구독 (복수형 메서드)"""
        return await self.subscribe_candle(symbols, timeframe, callback)
    
    def _parse_ticker_message(self, data: Dict) -> Optional[WebSocketMessage]:
        """시세 메시지 파싱"""
        try:
            if 'data' not in data:
                return None
            
            ticker_data = data['data'][0]  # 첫 번째 데이터
            
            return WebSocketMessage(
                symbol=ticker_data['instId'],
                price=float(ticker_data['last']),
                volume=float(ticker_data['vol24h']),
                timestamp=datetime.fromtimestamp(int(ticker_data['ts']) / 1000),
                exchange="okx"
            )
        except (KeyError, IndexError, ValueError) as e:
            self.logger.error(f"Failed to parse ticker message: {e}")
            return None
    
    async def _handle_message(self, message: str):
        """수신된 메시지 처리"""
        try:
            data = json.loads(message)
            
            # 통계 업데이트
            self.stats['messages_received'] += 1
            self.stats['last_message_time'] = datetime.now()
            
            # 에러 메시지 처리
            if 'error' in data:
                self.logger.error(f"OKX WebSocket error: {data['error']}")
                return
            
            # 이벤트 메시지 처리
            if 'event' in data:
                event = data['event']
                if event == 'subscribe':
                    self.logger.info(f"Subscription confirmed: {data}")
                elif event == 'error':
                    self.logger.error(f"Subscription error: {data}")
                return
            
            # 데이터 메시지 처리
            if 'arg' in data and 'data' in data:
                channel = data['arg']['channel']
                
                # 전역 데이터 핸들러 호출
                if self.data_handler:
                    if asyncio.iscoroutinefunction(self.data_handler):
                        await self.data_handler(data)
                    else:
                        self.data_handler(data)
                
                # 시세 데이터 처리
                if channel == 'tickers' and channel in self.message_handlers:
                    ticker_message = self._parse_ticker_message(data)
                    if ticker_message:
                        callback = self.message_handlers[channel]
                        if asyncio.iscoroutinefunction(callback):
                            await callback(ticker_message)
                        else:
                            callback(ticker_message)
                
                # 캔들 데이터 처리
                elif channel.startswith('candle') and channel in self.message_handlers:
                    callback = self.message_handlers[channel]
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _heartbeat_loop(self):
        """하트비트 루프"""
        while self.running and self.connected:
            try:
                if self.websocket and not self.websocket.closed:
                    ping_message = {"op": "ping"}
                    await self.websocket.send(json.dumps(ping_message))
                await asyncio.sleep(30)  # 30초마다 ping
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                break
    
    async def _reconnect_loop(self):
        """재연결 루프"""
        while self.running:
            if not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
                self.logger.info(f"Attempting to reconnect... (attempt {self.reconnect_attempts + 1})")
                
                success = await self.connect()
                if success:
                    # 기존 구독 복원
                    for channel, sub_info in self.subscriptions.items():
                        try:
                            if channel == 'tickers':
                                await self.subscribe_ticker(sub_info['symbols'], sub_info['callback'])
                            elif channel.startswith('candle'):
                                await self.subscribe_candle(
                                    sub_info['symbols'], 
                                    sub_info['timeframe'], 
                                    sub_info['callback']
                                )
                        except Exception as e:
                            self.logger.error(f"Failed to restore subscription for {channel}: {e}")
                    
                    self.stats['reconnect_count'] += 1
                    self.logger.info("Reconnection successful, subscriptions restored")
                else:
                    self.reconnect_attempts += 1
                    await asyncio.sleep(self.reconnect_interval)
            else:
                await asyncio.sleep(1)
    
    async def start_listening(self):
        """메시지 수신 시작"""
        self.running = True
        
        # 백그라운드 태스크 시작
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        reconnect_task = asyncio.create_task(self._reconnect_loop())
        
        try:
            while self.running:
                if not self.connected:
                    await asyncio.sleep(1)
                    continue
                
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    await self._handle_message(message)
                
                except asyncio.TimeoutError:
                    continue
                except ConnectionClosed:
                    self.logger.warning("WebSocket connection closed")
                    self.connected = False
                except WebSocketException as e:
                    self.logger.error(f"WebSocket error: {e}")
                    self.connected = False
                except Exception as e:
                    self.logger.error(f"Unexpected error in message loop: {e}")
                    await asyncio.sleep(1)
        
        finally:
            # 백그라운드 태스크 정리
            heartbeat_task.cancel()
            reconnect_task.cancel()
            
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            
            try:
                await reconnect_task
            except asyncio.CancelledError:
                pass
    
    def get_stats(self) -> Dict:
        """연결 통계 반환"""
        return {
            **self.stats,
            'connected': self.connected,
            'running': self.running,
            'subscriptions': len(self.subscriptions),
            'reconnect_attempts': self.reconnect_attempts
        }
