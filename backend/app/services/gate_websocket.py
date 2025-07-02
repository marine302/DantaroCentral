#!/usr/bin/env python3
"""
Gate.io WebSocket 클라이언트
실시간 마켓 데이터 수신을 위한 WebSocket 연결 관리
"""

import asyncio
import json
import logging
import time
import hashlib
import hmac
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from app.core.config import settings


class GateWebSocketClient:
    """Gate.io WebSocket 클라이언트"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.logger = logging.getLogger(f"{__name__}.GateWebSocketClient")
        
        # Gate.io WebSocket 엔드포인트
        self.ws_url = "wss://api.gateio.ws/ws/v4/"
        
        # 인증 정보 (공개 데이터에는 불필요)
        self.api_key = api_key
        self.secret_key = secret_key
        
        # 연결 상태
        self.websocket = None
        self.connected = False
        self.subscribed_channels = set()
        
        # 콜백 함수들
        self.on_ticker = None
        self.on_orderbook = None
        self.on_trade = None
        self.on_error = None
        
        # 재연결 설정
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5
        self.last_ping = time.time()
        
        # 메시지 통계
        self.message_count = 0
        self.start_time = None
    
    def set_callbacks(self, 
                     on_ticker: Callable = None,
                     on_orderbook: Callable = None,
                     on_trade: Callable = None,
                     on_error: Callable = None):
        """콜백 함수 설정"""
        self.on_ticker = on_ticker
        self.on_orderbook = on_orderbook
        self.on_trade = on_trade
        self.on_error = on_error
    
    async def connect(self):
        """WebSocket 연결 시작"""
        try:
            self.logger.info(f"Gate.io WebSocket 연결 시도: {self.ws_url}")
            
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            self.start_time = datetime.now()
            self.logger.info("✅ Gate.io WebSocket 연결 성공")
            
            # 메시지 수신 루프 시작
            await self._message_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Gate.io WebSocket 연결 실패: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """WebSocket 연결 종료"""
        try:
            self.connected = False
            if self.websocket:
                await self.websocket.close()
                self.logger.info("Gate.io WebSocket 연결 종료")
        except Exception as e:
            self.logger.error(f"연결 종료 중 오류: {e}")
    
    async def _message_loop(self):
        """메시지 수신 루프"""
        try:
            async for message in self.websocket:
                self.message_count += 1
                await self._handle_message(message)
                
        except ConnectionClosed:
            self.logger.warning("Gate.io WebSocket 연결이 종료됨")
            self.connected = False
        except WebSocketException as e:
            self.logger.error(f"Gate.io WebSocket 오류: {e}")
            self.connected = False
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
            if self.on_error:
                await self.on_error("message_error", str(e))
    
    async def _handle_message(self, message: str):
        """메시지 처리"""
        try:
            data = json.loads(message)
            
            # Ping/Pong 처리
            if data.get('method') == 'ping':
                await self._send_pong()
                return
            
            # 에러 메시지 처리
            if 'error' in data:
                self.logger.error(f"Gate.io 서버 오류: {data['error']}")
                if self.on_error:
                    await self.on_error("server_error", data['error'])
                return
            
            # 채널별 데이터 처리
            method = data.get('method')
            channel = data.get('params', {}).get('channel') if 'params' in data else None
            
            if method == 'ticker.update' and channel:
                await self._handle_ticker_update(data)
            elif method == 'depth.update' and channel:
                await self._handle_orderbook_update(data)
            elif method == 'trades.update' and channel:
                await self._handle_trade_update(data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 파싱 오류: {e}")
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
    
    async def _send_pong(self):
        """Pong 응답 전송"""
        try:
            pong_message = {"method": "pong", "id": int(time.time())}
            await self.websocket.send(json.dumps(pong_message))
            self.last_ping = time.time()
        except Exception as e:
            self.logger.error(f"Pong 전송 오류: {e}")
    
    async def _handle_ticker_update(self, data: Dict[str, Any]):
        """티커 업데이트 처리"""
        try:
            params = data.get('params', {})
            result = params.get('result')
            
            if not result:
                return
            
            # Gate.io 티커 데이터 정규화
            symbol = result.get('currency_pair', '').replace('_', '-').upper()
            
            ticker_data = {
                'symbol': symbol,
                'last_price': float(result.get('last', 0)),
                'bid_price': float(result.get('highest_bid', 0)),
                'ask_price': float(result.get('lowest_ask', 0)),
                'volume': float(result.get('base_volume', 0)),
                'quote_volume': float(result.get('quote_volume', 0)),
                'high_24h': float(result.get('high_24h', 0)),
                'low_24h': float(result.get('low_24h', 0)),
                'change_24h': float(result.get('change_percentage', 0)),
                'timestamp': datetime.now(),
                'exchange': 'gate'
            }
            
            if self.on_ticker:
                await self.on_ticker('gate', symbol, ticker_data)
                
        except Exception as e:
            self.logger.error(f"티커 데이터 처리 오류: {e}")
    
    async def _handle_orderbook_update(self, data: Dict[str, Any]):
        """오더북 업데이트 처리"""
        try:
            params = data.get('params', {})
            result = params.get('result')
            
            if not result:
                return
            
            symbol = result.get('s', '').replace('_', '-').upper()
            
            orderbook_data = {
                'symbol': symbol,
                'bids': [[float(bid[0]), float(bid[1])] for bid in result.get('bids', [])],
                'asks': [[float(ask[0]), float(ask[1])] for ask in result.get('asks', [])],
                'timestamp': datetime.now(),
                'exchange': 'gate'
            }
            
            if self.on_orderbook:
                await self.on_orderbook('gate', symbol, orderbook_data)
                
        except Exception as e:
            self.logger.error(f"오더북 데이터 처리 오류: {e}")
    
    async def _handle_trade_update(self, data: Dict[str, Any]):
        """거래 업데이트 처리"""
        try:
            params = data.get('params', {})
            result = params.get('result')
            
            if not result:
                return
            
            for trade in result:
                symbol = trade.get('currency_pair', '').replace('_', '-').upper()
                
                trade_data = {
                    'symbol': symbol,
                    'price': float(trade.get('price', 0)),
                    'amount': float(trade.get('amount', 0)),
                    'side': trade.get('side', ''),
                    'timestamp': datetime.fromtimestamp(float(trade.get('create_time', 0))),
                    'exchange': 'gate'
                }
                
                if self.on_trade:
                    await self.on_trade('gate', symbol, trade_data)
                    
        except Exception as e:
            self.logger.error(f"거래 데이터 처리 오류: {e}")
    
    async def subscribe_ticker(self, symbols: List[str]):
        """티커 구독"""
        for symbol in symbols:
            # Gate.io 심볼 형식으로 변환 (BTC-USDT -> BTC_USDT)
            gate_symbol = symbol.replace('-', '_').lower()
            
            subscribe_message = {
                "method": "ticker.subscribe",
                "params": [gate_symbol],
                "id": int(time.time())
            }
            
            await self._send_message(subscribe_message)
            self.subscribed_channels.add(f"ticker.{gate_symbol}")
            self.logger.info(f"✅ Gate.io 티커 구독: {symbol}")
    
    async def subscribe_orderbook(self, symbols: List[str], depth: int = 20):
        """오더북 구독"""
        for symbol in symbols:
            gate_symbol = symbol.replace('-', '_').lower()
            
            subscribe_message = {
                "method": "depth.subscribe",
                "params": [gate_symbol, depth, "0"],
                "id": int(time.time())
            }
            
            await self._send_message(subscribe_message)
            self.subscribed_channels.add(f"depth.{gate_symbol}")
            self.logger.info(f"✅ Gate.io 오더북 구독: {symbol}")
    
    async def subscribe_trades(self, symbols: List[str]):
        """거래 구독"""
        for symbol in symbols:
            gate_symbol = symbol.replace('-', '_').lower()
            
            subscribe_message = {
                "method": "trades.subscribe",
                "params": [gate_symbol],
                "id": int(time.time())
            }
            
            await self._send_message(subscribe_message)
            self.subscribed_channels.add(f"trades.{gate_symbol}")
            self.logger.info(f"✅ Gate.io 거래 구독: {symbol}")
    
    async def _send_message(self, message: Dict[str, Any]):
        """메시지 전송"""
        try:
            if not self.connected or not self.websocket:
                raise Exception("WebSocket이 연결되지 않음")
            
            await self.websocket.send(json.dumps(message))
            
        except Exception as e:
            self.logger.error(f"메시지 전송 오류: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 통계 조회"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'connected': self.connected,
            'subscribed_channels': len(self.subscribed_channels),
            'message_count': self.message_count,
            'uptime_seconds': uptime,
            'messages_per_second': self.message_count / uptime if uptime > 0 else 0,
            'last_ping': self.last_ping
        }


async def test_gate_websocket():
    """Gate.io WebSocket 테스트"""
    logging.basicConfig(level=logging.INFO)
    
    client = GateWebSocketClient()
    
    # 콜백 함수 설정
    async def on_ticker(exchange, symbol, data):
        print(f"🔔 {exchange} 티커 - {symbol}: ${data['last_price']:.6f}")
    
    async def on_error(error_type, message):
        print(f"❌ 오류 ({error_type}): {message}")
    
    client.set_callbacks(on_ticker=on_ticker, on_error=on_error)
    
    try:
        # 연결 및 구독
        await client.connect()
        await client.subscribe_ticker(['BTC-USDT', 'ETH-USDT', 'DOGE-USDT'])
        
        # 30초 동안 실행
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("🛑 사용자에 의해 중단됨")
    finally:
        await client.disconnect()
        print(f"📊 최종 통계: {client.get_stats()}")


if __name__ == "__main__":
    asyncio.run(test_gate_websocket())
