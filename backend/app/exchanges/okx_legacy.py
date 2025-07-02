"""
OKX 거래소 API 구현
단일 책임: OKX 공식 API를 통합 인터페이스로 변환

참고: https://www.okx.com/docs-v5/
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

import aiohttp

from .base import (
    BaseExchange, Balance, Ticker, OrderBook, Order, Trade,
    OrderSide, OrderType, OrderStatus
)


class OKXExchange(BaseExchange):
    """OKX 거래소 구현"""
    
    BASE_URL = "https://www.okx.com"
    SANDBOX_URL = "https://www.okx.com"  # OKX는 동일한 URL 사용, 계정으로 구분
    
    def __init__(self, api_key: str, secret_key: str, passphrase: str, environment: str = "production", **kwargs):
        super().__init__(api_key, secret_key, **kwargs)
        self.passphrase = passphrase
        self.environment = environment
        self.base_url = self.SANDBOX_URL if environment == "sandbox" else self.BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 관리"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _generate_auth_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        """OKX 인증 헤더 생성"""
        # OKX 공식 문서에 따른 ISO 8601 형식 (밀리초 포함)
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        message = timestamp + method.upper() + request_path + body
        
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                      auth: bool = False) -> Any:
        """HTTP 요청 처리"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        headers = {'Content-Type': 'application/json'}
        body = ""
        
        if method.upper() == 'GET' and params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
        elif method.upper() == 'POST' and params:
            body = json.dumps(params)
        
        if auth:
            headers.update(self._generate_auth_headers(method, endpoint.split('?')[0], body))
        
        try:
            if method.upper() == 'GET':
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, data=body, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
            else:
                raise Exception(f"지원되지 않는 HTTP 메서드: {method}")
            
            if data.get('code') != '0':
                # 자세한 오류 정보 출력
                print(f"OKX API 응답: {data}")
                raise Exception(f"OKX API 오류: {data.get('msg', 'Unknown error')}")
            
            return data.get('data', [])
        
        except aiohttp.ClientError as e:
            raise Exception(f"OKX API 오류: {str(e)}")
    
    # === 인터페이스 구현 ===
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        """잔고 조회"""
        data = await self._request('GET', '/api/v5/account/balance', auth=True)
        balances = {}
        
        if isinstance(data, list) and len(data) > 0:
            details = data[0].get('details', []) if isinstance(data[0], dict) else []
            for detail in details:
                if not isinstance(detail, dict):
                    continue
                curr = detail.get('ccy')
                if not curr or not isinstance(curr, str):
                    continue
                if currency and curr != currency:
                    continue
                balances[curr] = Balance(
                    currency=curr,
                    available=Decimal(detail.get('availBal', '0')),
                    locked=Decimal(detail.get('frozenBal', '0')),
                    total=Decimal(detail.get('bal', '0'))
                )
        
        return balances
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """현재가 조회"""
        params = {'instId': symbol}
        data = await self._request('GET', '/api/v5/market/ticker', params)
        
        if not data:
            raise Exception(f"심볼 {symbol}의 시세 정보를 찾을 수 없습니다")
        
        ticker_data = data[0]
        return Ticker(
            symbol=symbol,
            price=Decimal(ticker_data.get('last', '0')),
            bid=Decimal(ticker_data.get('bidPx', '0')),
            ask=Decimal(ticker_data.get('askPx', '0')),
            volume=Decimal(ticker_data.get('vol24h', '0')),
            timestamp=datetime.fromtimestamp(int(ticker_data.get('ts', '0')) / 1000)
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        """호가 조회"""
        params = {'instId': symbol, 'sz': str(limit)}
        data = await self._request('GET', '/api/v5/market/books', params)
        
        if not data:
            raise Exception(f"심볼 {symbol}의 호가 정보를 찾을 수 없습니다")
        
        orderbook_data = data[0]
        bids = [[Decimal(bid[0]), Decimal(bid[1])] for bid in orderbook_data.get('bids', [])]
        asks = [[Decimal(ask[0]), Decimal(ask[1])] for ask in orderbook_data.get('asks', [])]
        
        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.fromtimestamp(int(orderbook_data.get('ts', '0')) / 1000)
        )
    
    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        """시장가 주문"""
        params = {
            'instId': symbol,
            'tdMode': 'cash',
            'side': side.value,
            'ordType': 'market',
            'sz': str(amount)
        }
        
        data = await self._request('POST', '/api/v5/trade/order', params, auth=True)
        
        if not data:
            raise Exception("주문 생성 실패")
        
        order_data = data[0]
        return Order(
            id=order_data['ordId'],
            symbol=symbol,
            side=side,
            type=OrderType.MARKET,
            amount=amount,
            price=None,
            filled=Decimal('0'),
            remaining=amount,
            status=OrderStatus.PENDING,
            timestamp=datetime.now()
        )
    
    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        """지정가 주문"""
        params = {
            'instId': symbol,
            'tdMode': 'cash',
            'side': side.value,
            'ordType': 'limit',
            'sz': str(amount),
            'px': str(price)
        }
        
        data = await self._request('POST', '/api/v5/trade/order', params, auth=True)
        
        if not data:
            raise Exception("주문 생성 실패")
        
        order_data = data[0]
        return Order(
            id=order_data['ordId'],
            symbol=symbol,
            side=side,
            type=OrderType.LIMIT,
            amount=amount,
            price=price,
            filled=Decimal('0'),
            remaining=amount,
            status=OrderStatus.OPEN,
            timestamp=datetime.now()
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """주문 취소"""
        params = {
            'instId': symbol,
            'ordId': order_id
        }
        
        try:
            await self._request('POST', '/api/v5/trade/cancel-order', params, auth=True)
            return True
        except Exception:
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """주문 조회"""
        params = {
            'instId': symbol,
            'ordId': order_id
        }
        
        data = await self._request('GET', '/api/v5/trade/order', params, auth=True)
        
        if not data:
            raise Exception(f"주문 {order_id}를 찾을 수 없습니다")
        
        return self._parse_order(data[0])
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """미체결 주문 조회"""
        params = {}
        if symbol:
            params['instId'] = symbol
        
        data = await self._request('GET', '/api/v5/trade/orders-pending', params, auth=True)
        return [self._parse_order(order_data) for order_data in data]
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """주문 내역 조회"""
        params = {'limit': str(limit)}
        if symbol:
            params['instId'] = symbol
        
        data = await self._request('GET', '/api/v5/trade/orders-history', params, auth=True)
        return [self._parse_order(order_data) for order_data in data]
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        """체결 내역 조회"""
        params = {'limit': str(limit)}
        if symbol:
            params['instId'] = symbol
        
        data = await self._request('GET', '/api/v5/trade/fills', params, auth=True)
        trades = []
        
        for trade_data in data:
            trades.append(Trade(
                id=trade_data.get('tradeId', ''),
                order_id=trade_data.get('ordId', ''),
                symbol=trade_data.get('instId', ''),
                side=OrderSide(trade_data.get('side', 'buy')),
                amount=Decimal(trade_data.get('fillSz', '0')),
                price=Decimal(trade_data.get('fillPx', '0')),
                fee=Decimal(trade_data.get('fee', '0')),
                timestamp=datetime.fromtimestamp(int(trade_data.get('ts', '0')) / 1000)
            ))
        
        return trades
    
    async def get_symbols(self) -> List[str]:
        """거래 가능한 심볼 목록"""
        data = await self._request('GET', '/api/v5/public/instruments', {'instType': 'SPOT'})
        return [instrument.get('instId', '') for instrument in data]
    
    async def get_trading_rules(self, symbol: str) -> Dict[str, Any]:
        """거래 규칙 조회 (최소 주문 금액, 수량 단위 등)"""
        try:
            data = await self._request('GET', f'/api/v5/public/instruments?instType=SPOT&instId={symbol}')
            
            if data and len(data) > 0:
                instrument = data[0]
                return {
                    'symbol': symbol,
                    'min_order_value': float(instrument.get('minSz', '0')),  # 최소 주문 수량
                    'tick_size': float(instrument.get('tickSz', '0.000001')),  # 가격 단위
                    'lot_size': float(instrument.get('lotSz', '0.1')),  # 수량 단위
                    'base_currency': instrument.get('baseCcy', ''),
                    'quote_currency': instrument.get('quoteCcy', ''),
                    'status': instrument.get('state', ''),
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"거래 규칙 조회 오류 {symbol}: {e}")
            return {}

    async def validate_order_amount(self, symbol: str, amount: Decimal) -> tuple[bool, str]:
        """주문 금액 검증"""
        try:
            rules = await self.get_trading_rules(symbol)
            ticker = await self.get_ticker(symbol)
            
            if not rules:
                return False, "거래 규칙을 가져올 수 없습니다"
            
            # 현재 가격으로 수량 계산
            current_price = ticker.price
            quantity = amount / current_price
            
            # 최소 수량 검증
            min_quantity = Decimal(str(rules.get('min_order_value', 0)))
            if quantity < min_quantity:
                min_value = min_quantity * current_price
                return False, f"최소 주문 금액: ${min_value:.2f} (현재: ${amount:.2f})"
            
            # OKX 일반적인 최소 금액 ($5-10)
            if amount < Decimal('5.0'):
                return False, f"OKX 최소 주문 금액 미만: ${amount:.2f} < $5.00"
            
            return True, "검증 통과"
            
        except Exception as e:
            return False, f"검증 오류: {str(e)}"

    def _parse_order(self, data: Dict) -> Order:
        """주문 데이터 파싱"""
        status_map = {
            'live': OrderStatus.OPEN,
            'filled': OrderStatus.CLOSED,
            'canceled': OrderStatus.CANCELLED
        }
        
        return Order(
            id=data.get('ordId', ''),
            symbol=data.get('instId', ''),
            side=OrderSide(data.get('side', 'buy')),
            type=OrderType.LIMIT if data.get('ordType', 'limit') == 'limit' else OrderType.MARKET,
            amount=Decimal(data.get('sz', '0')),
            price=Decimal(data.get('px', '0')) if data.get('px') else None,
            filled=Decimal(data.get('fillSz', '0')),
            remaining=Decimal(data.get('sz', '0')) - Decimal(data.get('fillSz', '0')),
            status=status_map.get(data.get('state', ''), OrderStatus.PENDING),
            timestamp=datetime.fromtimestamp(int(data.get('cTime', '0')) / 1000)
        )
    
    async def close(self):
        """세션 정리"""
        if self.session and not self.session.closed:
            await self.session.close()
