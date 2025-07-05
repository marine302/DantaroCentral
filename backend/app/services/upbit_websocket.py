#!/usr/bin/env python3
"""
Upbit WebSocket 클라이언트
업비트 WebSocket API를 통한 실시간 데이터 수집

Upbit WebSocket API 사양:
- URL: wss://api.upbit.com/websocket/v1
- 프로토콜: 바이너리 메시지 (JSON)
- 인증: 불필요 (공개 데이터)
- 채널: ticker, orderbook, trade
"""

import asyncio
import json
import logging
import uuid
import websockets
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlencode
from app.core.config import settings

logger = logging.getLogger(__name__)


class UpbitWebSocketClient:
    """업비트 WebSocket 클라이언트"""
    
    def __init__(self, data_handler: Optional[Callable] = None):
        """
        초기화
        
        Args:
            data_handler: 데이터 처리 콜백 함수
        """
        self.ws_url = "wss://api.upbit.com/websocket/v1"
        self.data_handler = data_handler
        self.websocket = None
        self.running = False
        
        # 연결 관리 (settings 기반, 없으면 기본값)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = getattr(settings, "upbit_ws_max_reconnect", 5)
        self.reconnect_delay = getattr(settings, "upbit_ws_reconnect_delay", 5)
        
        # 구독 관리
        self.subscriptions = {}
        self.active_symbols = set()
        
        # 성능 메트릭
        self.stats = {
            'messages_received': 0,
            'last_message_time': None,
            'connection_time': None,
            'errors': 0
        }
    
    async def connect(self) -> bool:
        """WebSocket 연결"""
        try:
            logger.info(f"Connecting to Upbit WebSocket: {self.ws_url}")
            
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.running = True
            self.stats['connection_time'] = datetime.now()
            self.reconnect_attempts = 0
            
            logger.info("Upbit WebSocket connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Upbit WebSocket 연결 실패: {e}")
            self.stats['errors'] += 1
            return False
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        self.running = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        logger.info("Upbit WebSocket disconnected")
    
    async def subscribe_ticker(self, symbols: List[str]):
        """
        티커 데이터 구독
        
        Args:
            symbols: 심볼 리스트 (예: ['KRW-BTC', 'KRW-ETH'])
        """
        subscription_msg = [
            {"ticket": str(uuid.uuid4())},
            {
                "type": "ticker",
                "codes": symbols,
                "isOnlySnapshot": False,
                "isOnlyRealtime": True
            }
        ]
        
        await self._send_subscription(subscription_msg, 'ticker', symbols)
    
    async def subscribe_orderbook(self, symbols: List[str]):
        """
        호가 데이터 구독
        
        Args:
            symbols: 심볼 리스트
        """
        subscription_msg = [
            {"ticket": str(uuid.uuid4())},
            {
                "type": "orderbook",
                "codes": symbols,
                "isOnlySnapshot": False,
                "isOnlyRealtime": True
            }
        ]
        
        await self._send_subscription(subscription_msg, 'orderbook', symbols)
    
    async def subscribe_trade(self, symbols: List[str]):
        """
        체결 데이터 구독
        
        Args:
            symbols: 심볼 리스트
        """
        subscription_msg = [
            {"ticket": str(uuid.uuid4())},
            {
                "type": "trade",
                "codes": symbols,
                "isOnlySnapshot": False,
                "isOnlyRealtime": True
            }
        ]
        
        await self._send_subscription(subscription_msg, 'trade', symbols)
    
    async def _send_subscription(self, message: List[Dict], channel: str, symbols: List[str]):
        """구독 메시지 전송"""
        try:
            if not self.websocket:
                logger.error("WebSocket 연결이 없습니다")
                return
            
            # JSON을 바이너리로 변환하여 전송
            json_str = json.dumps(message)
            await self.websocket.send(json_str.encode('utf-8'))
            
            # 구독 정보 저장
            self.subscriptions[channel] = symbols
            self.active_symbols.update(symbols)
            
            logger.info(f"Subscribed to {channel} data for symbols: {symbols}")
            
        except Exception as e:
            logger.error(f"구독 메시지 전송 실패: {e}")
            self.stats['errors'] += 1
    
    async def listen(self):
        """메시지 수신 루프"""
        while self.running and self.websocket:
            try:
                # 바이너리 메시지 수신
                message = await self.websocket.recv()
                
                # 바이너리를 JSON으로 디코딩
                if isinstance(message, bytes):
                    json_str = message.decode('utf-8')
                    data = json.loads(json_str)
                else:
                    data = json.loads(message)
                
                await self._handle_message(data)
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Upbit WebSocket 연결이 닫혔습니다")
                break
            except Exception as e:
                logger.error(f"메시지 수신 오류: {e}")
                self.stats['errors'] += 1
                
                # 연속 오류 시 재연결
                if self.stats['errors'] % 5 == 0:
                    await self._handle_reconnect()
    
    async def _handle_message(self, data: Dict):
        """메시지 처리"""
        try:
            self.stats['messages_received'] += 1
            self.stats['last_message_time'] = datetime.now()
            
            # 데이터 타입별 처리
            msg_type = data.get('type', 'unknown')
            
            if msg_type == 'ticker':
                await self._handle_ticker_data(data)
            elif msg_type == 'orderbook':
                await self._handle_orderbook_data(data)
            elif msg_type == 'trade':
                await self._handle_trade_data(data)
            
            # 외부 핸들러 호출
            if self.data_handler:
                await self.data_handler(data)
                
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            self.stats['errors'] += 1
    
    async def _handle_ticker_data(self, data: Dict):
        """티커 데이터 처리"""
        try:
            symbol = data.get('code', 'unknown')
            price = data.get('trade_price', 0)
            volume = data.get('acc_trade_volume_24h', 0)
            
            # 주요 심볼만 로깅
            if symbol in ['KRW-BTC', 'KRW-ETH']:
                logger.info(
                    f"📊 [Upbit] {symbol}: ₩{price:,.0f} "
                    f"(Vol: {volume:,.2f})"
                )
                
        except Exception as e:
            logger.error(f"티커 데이터 처리 오류: {e}")
    
    async def _handle_orderbook_data(self, data: Dict):
        """호가 데이터 처리"""
        try:
            symbol = data.get('code', 'unknown')
            orderbook_units = data.get('orderbook_units', [])
            
            if orderbook_units:
                best_bid = orderbook_units[0].get('bid_price', 0)
                best_ask = orderbook_units[0].get('ask_price', 0)
                
                # 스프레드가 큰 경우만 로깅
                if best_bid > 0 and best_ask > 0:
                    spread = ((best_ask - best_bid) / best_bid) * 100
                    if spread > 0.1:  # 0.1% 이상 스프레드
                        logger.info(
                            f"📋 [Upbit] {symbol}: Bid ₩{best_bid:,.0f} / "
                            f"Ask ₩{best_ask:,.0f} (Spread: {spread:.2f}%)"
                        )
                        
        except Exception as e:
            logger.error(f"호가 데이터 처리 오류: {e}")
    
    async def _handle_trade_data(self, data: Dict):
        """체결 데이터 처리"""
        try:
            symbol = data.get('code', 'unknown')
            price = data.get('trade_price', 0)
            volume = data.get('trade_volume', 0)
            side = data.get('ask_bid', 'unknown')
            
            # 큰 거래량만 로깅
            if volume > 1:  # 1개 이상
                logger.info(
                    f"🔄 [Upbit] {symbol}: ₩{price:,.0f} "
                    f"({side.upper()}, Vol: {volume:,.4f})"
                )
                
        except Exception as e:
            logger.error(f"체결 데이터 처리 오류: {e}")
    
    async def _handle_reconnect(self):
        """재연결 처리"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("최대 재연결 시도 횟수 초과")
            self.running = False
            return
        
        self.reconnect_attempts += 1
        logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        await self.disconnect()
        await asyncio.sleep(self.reconnect_delay)
        
        if await self.connect():
            # 기존 구독 복원
            for channel, symbols in self.subscriptions.items():
                if channel == 'ticker':
                    await self.subscribe_ticker(symbols)
                elif channel == 'orderbook':
                    await self.subscribe_orderbook(symbols)
                elif channel == 'trade':
                    await self.subscribe_trade(symbols)
    
    def get_stats(self) -> Dict:
        """통계 정보 반환"""
        return {
            'connected': self.running and self.websocket is not None,
            'active_symbols': len(self.active_symbols),
            'subscriptions': list(self.subscriptions.keys()),
            **self.stats
        }


async def test_upbit_websocket():
    """Upbit WebSocket 테스트 (서비스 코드 분리 권장)"""
    async def data_handler(data):
        # print(f"Received: {data.get('type', 'unknown')} for {data.get('code', 'unknown')}")
        pass
    client = UpbitWebSocketClient(data_handler)
    try:
        if await client.connect():
            await client.subscribe_ticker(['KRW-BTC', 'KRW-ETH'])
            listen_task = asyncio.create_task(client.listen())
            await asyncio.sleep(10)
            await client.disconnect()
            listen_task.cancel()
            # print(f"Stats: {client.get_stats()}")
    except Exception as e:
        # print(f"Test failed: {e}")
        pass


if __name__ == "__main__":
    asyncio.run(test_upbit_websocket())
