#!/usr/bin/env python3
"""
Coinone WebSocket 클라이언트
코인원 WebSocket API를 통한 실시간 데이터 수집

Coinone WebSocket API 사양:
- URL: wss://ws.coinone.co.kr
- 프로토콜: JSON 메시지
- 인증: API 키 필요 (Private 데이터) 또는 불필요 (Public 데이터)
- 채널: ticker, orderbook, trade, candles
"""

import asyncio
import json
import logging
import websockets
import hmac
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class CoinoneWebSocketClient:
    """코인원 WebSocket 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 data_handler: Optional[Callable] = None):
        """
        초기화
        
        Args:
            api_key: API 키 (Private 데이터 접근 시 필요)
            secret_key: Secret 키 (Private 데이터 접근 시 필요)
            data_handler: 데이터 처리 콜백 함수
        """
        self.ws_url = "wss://stream.coinone.co.kr"
        self.api_key = api_key
        self.secret_key = secret_key
        self.data_handler = data_handler
        self.websocket = None
        self.running = False
        
        # 연결 관리
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5
        
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
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """API 인증 시그니처 생성"""
        if not self.secret_key:
            return ""
        
        message = f"{timestamp}{method.upper()}{path}{body}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def connect(self) -> bool:
        """WebSocket 연결"""
        try:
            logger.info(f"Connecting to Coinone WebSocket: {self.ws_url}")
            
            # 기본 연결 (인증 헤더는 WebSocket 연결 후 메시지로 처리)
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.running = True
            self.stats['connection_time'] = datetime.now()
            self.reconnect_attempts = 0
            
            logger.info("Coinone WebSocket connected successfully")
            
            # 인증이 필요한 경우 로그인 메시지 전송
            if self.api_key and self.secret_key:
                await self._send_auth_message()
            
            return True
            
        except Exception as e:
            logger.error(f"Coinone WebSocket 연결 실패: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _send_auth_message(self):
        """인증 메시지 전송"""
        try:
            if not self.websocket:
                logger.error("WebSocket 연결이 없습니다")
                return
                
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(timestamp, "GET", "/")
            
            auth_message = {
                "request_type": "AUTH",
                "api_key": self.api_key,
                "signature": signature,
                "timestamp": timestamp
            }
            
            await self.websocket.send(json.dumps(auth_message))
            logger.info("인증 메시지 전송 완료")
            
        except Exception as e:
            logger.error(f"인증 메시지 전송 실패: {e}")
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        self.running = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        logger.info("Coinone WebSocket disconnected")
    
    async def subscribe_ticker(self, symbols: List[str]):
        """
        티커 데이터 구독
        
        Args:
            symbols: 심볼 리스트 (예: ['BTC', 'ETH', 'ADA'])
        """
        # Coinone은 한 번에 하나씩 구독해야 할 수 있음
        for symbol in symbols:
            subscription_msg = {
                "request_type": "SUBSCRIBE",
                "channel": "TICKER",
                "topic": {
                    "quote_currency": "KRW",
                    "target_currency": symbol
                }
            }
            
            await self._send_subscription(subscription_msg, 'ticker', [symbol])
    
    async def subscribe_orderbook(self, symbols: List[str]):
        """
        호가 데이터 구독
        
        Args:
            symbols: 심볼 리스트
        """
        for symbol in symbols:
            subscription_msg = {
                "request_type": "SUBSCRIBE",
                "channel": "ORDERBOOK",
                "topic": {
                    "quote_currency": "KRW",
                    "target_currency": symbol
                }
            }
            
            await self._send_subscription(subscription_msg, 'orderbook', [symbol])
    
    async def subscribe_trade(self, symbols: List[str]):
        """
        체결 데이터 구독
        
        Args:
            symbols: 심볼 리스트
        """
        for symbol in symbols:
            subscription_msg = {
                "request_type": "SUBSCRIBE",
                "channel": "TRADE",
                "topic": {
                    "quote_currency": "KRW",
                    "target_currency": symbol
                }
            }
            
            await self._send_subscription(subscription_msg, 'trade', [symbol])
    
    async def subscribe_candles(self, symbols: List[str], interval: str = "1m"):
        """
        캔들 데이터 구독
        
        Args:
            symbols: 심볼 리스트
            interval: 간격 (1m, 5m, 15m, 30m, 1h, 6h, 12h, 1d)
        """
        subscription_msg = {
            "request_type": "SUBSCRIBE",
            "channel": "CANDLES",
            "topic": {
                "quote_currency": "KRW",
                "target_currency": symbols,
                "interval": interval
            }
        }
        
        await self._send_subscription(subscription_msg, f'candles_{interval}', symbols)
    
    async def _send_subscription(self, message: Dict, channel: str, symbols: List[str]):
        """구독 메시지 전송"""
        try:
            if not self.websocket:
                logger.error("WebSocket 연결이 없습니다")
                return
            
            await self.websocket.send(json.dumps(message))
            
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
                message = await self.websocket.recv()
                data = json.loads(message)
                
                await self._handle_message(data)
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Coinone WebSocket 연결이 닫혔습니다")
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
            
            # 메시지 타입별 처리
            response_type = data.get('response_type', 'unknown')
            channel = data.get('channel', 'unknown')
            
            if response_type == "DATA":
                if channel == "TICKER":
                    await self._handle_ticker_data(data)
                elif channel == "ORDERBOOK":
                    await self._handle_orderbook_data(data)
                elif channel == "TRADE":
                    await self._handle_trade_data(data)
                elif channel.startswith("CANDLES"):
                    await self._handle_candle_data(data)
            elif response_type == "SUBSCRIBE":
                logger.info(f"구독 확인: {data}")
            elif response_type == "ERROR":
                logger.error(f"서버 오류: {data}")
                self.stats['errors'] += 1
            
            # 외부 핸들러 호출
            if self.data_handler:
                await self.data_handler(data)
                
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            self.stats['errors'] += 1
    
    async def _handle_ticker_data(self, data: Dict):
        """티커 데이터 처리"""
        try:
            ticker_data = data.get('data', {})
            symbol = ticker_data.get('target_currency', 'unknown')
            price = float(ticker_data.get('last', 0))
            volume = float(ticker_data.get('volume', 0))
            
            # 주요 심볼만 로깅
            if symbol in ['BTC', 'ETH', 'ADA']:
                change_24h = float(ticker_data.get('yesterday_last', 0))
                change_pct = 0.0
                if change_24h > 0:
                    change_pct = ((price - change_24h) / change_24h) * 100
                
                logger.info(
                    f"📊 [Coinone] {symbol}: ₩{price:,.0f} "
                    f"({change_pct:+.2f}%, Vol: {volume:,.2f})"
                )
                
        except Exception as e:
            logger.error(f"티커 데이터 처리 오류: {e}")
    
    async def _handle_orderbook_data(self, data: Dict):
        """호가 데이터 처리"""
        try:
            orderbook_data = data.get('data', {})
            symbol = orderbook_data.get('target_currency', 'unknown')
            
            asks = orderbook_data.get('ask', [])
            bids = orderbook_data.get('bid', [])
            
            if asks and bids:
                best_ask = float(asks[0].get('price', 0))
                best_bid = float(bids[0].get('price', 0))
                
                if best_ask > 0 and best_bid > 0:
                    spread = ((best_ask - best_bid) / best_bid) * 100
                    
                    # 스프레드가 큰 경우만 로깅
                    if spread > 0.2:  # 0.2% 이상
                        logger.info(
                            f"📋 [Coinone] {symbol}: Bid ₩{best_bid:,.0f} / "
                            f"Ask ₩{best_ask:,.0f} (Spread: {spread:.2f}%)"
                        )
                        
        except Exception as e:
            logger.error(f"호가 데이터 처리 오류: {e}")
    
    async def _handle_trade_data(self, data: Dict):
        """체결 데이터 처리"""
        try:
            trade_data = data.get('data', {})
            symbol = trade_data.get('target_currency', 'unknown')
            price = float(trade_data.get('price', 0))
            volume = float(trade_data.get('qty', 0))
            
            # 큰 거래량만 로깅
            if volume > 0.1:  # 0.1개 이상
                logger.info(
                    f"🔄 [Coinone] {symbol}: ₩{price:,.0f} "
                    f"(Vol: {volume:,.4f})"
                )
                
        except Exception as e:
            logger.error(f"체결 데이터 처리 오류: {e}")
    
    async def _handle_candle_data(self, data: Dict):
        """캔들 데이터 처리"""
        try:
            candle_data = data.get('data', {})
            symbol = candle_data.get('target_currency', 'unknown')
            
            # 캔들 정보 추출
            open_price = float(candle_data.get('open', 0))
            high_price = float(candle_data.get('high', 0))
            low_price = float(candle_data.get('low', 0))
            close_price = float(candle_data.get('close', 0))
            volume = float(candle_data.get('volume', 0))
            
            # 주요 심볼의 큰 변화만 로깅
            if symbol in ['BTC', 'ETH'] and volume > 10:
                logger.info(
                    f"🕯️ [Coinone] {symbol}: OHLC ₩{open_price:,.0f}/₩{high_price:,.0f}/"
                    f"₩{low_price:,.0f}/₩{close_price:,.0f} (Vol: {volume:,.0f})"
                )
                
        except Exception as e:
            logger.error(f"캔들 데이터 처리 오류: {e}")
    
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
                elif channel.startswith('candles_'):
                    interval = channel.split('_')[1]
                    await self.subscribe_candles(symbols, interval)
    
    def get_stats(self) -> Dict:
        """통계 정보 반환"""
        return {
            'connected': self.running and self.websocket is not None,
            'active_symbols': len(self.active_symbols),
            'subscriptions': list(self.subscriptions.keys()),
            **self.stats
        }


async def test_coinone_websocket():
    """Coinone WebSocket 테스트"""
    async def data_handler(data):
        response_type = data.get('response_type', 'unknown')
        channel = data.get('channel', 'unknown')
        print(f"Received: {response_type} from {channel}")
    
    client = CoinoneWebSocketClient(data_handler=data_handler)
    
    try:
        # 연결
        if await client.connect():
            # 구독
            await client.subscribe_ticker(['BTC', 'ETH'])
            
            # 10초간 수신
            listen_task = asyncio.create_task(client.listen())
            await asyncio.sleep(10)
            
            # 정리
            await client.disconnect()
            listen_task.cancel()
            
            print(f"Stats: {client.get_stats()}")
    
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_coinone_websocket())
