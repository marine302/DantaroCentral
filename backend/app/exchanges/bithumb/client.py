"""
Bithumb 거래소 클라이언트
"""

import hmac
import hashlib
import time
import aiohttp
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from ..base import (
    BaseExchange, Balance, Ticker, OrderBook, Order, Trade,
    OrderSide, OrderType, OrderStatus
)

class BithumbClient(BaseExchange):
    """Bithumb 거래소 구현"""
    BASE_URL = "https://api.bithumb.com"

    def __init__(self, api_key: str, secret_key: str, **kwargs):
        super().__init__(api_key, secret_key, **kwargs)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def _sign(self, endpoint: str, params: Dict[str, Any], nonce: str) -> str:
        import base64
        str_data = urlencode(params)
        data = endpoint + chr(0) + str_data + chr(0) + nonce
        h = hmac.new(self.secret_key.encode(), data.encode(), hashlib.sha512)
        return base64.b64encode(h.digest()).decode()

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, auth: bool = False) -> Any:
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        headers = {}
        if auth:
            nonce = str(int(time.time() * 1000))
            headers['Api-Key'] = self.api_key
            headers['Api-Nonce'] = nonce
            headers['Api-Sign'] = self._sign(endpoint, params, nonce)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        try:
            if method.upper() == 'GET':
                async with session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, data=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                raise Exception(f"지원되지 않는 HTTP 메서드: {method}")
        except aiohttp.ClientError as e:
            raise Exception(f"Bithumb API 오류: {str(e)}")

    # === 인터페이스 구현 ===

    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        params = {'currency': currency or 'ALL'}
        data = await self._request('POST', '/info/balance', params, auth=True)
        balances = {}
        for curr in data.get('data', {}):
            if not curr.endswith('_available'):
                continue
            coin = curr.replace('_available', '')
            available = Decimal(data['data'].get(f'{coin}_available', '0'))
            locked = Decimal(data['data'].get(f'{coin}_in_use', '0'))
            total = available + locked
            balances[coin] = Balance(
                currency=coin,
                available=available,
                locked=locked,
                total=total
            )
        return balances

    async def get_ticker(self, symbol: str) -> Ticker:
        params = {'order_currency': symbol, 'payment_currency': 'KRW'}
        data = await self._request('GET', '/public/ticker/' + symbol, params)
        d = data.get('data', {})
        return Ticker(
            symbol=symbol,
            price=Decimal(d.get('closing_price', '0')),
            bid=Decimal(d.get('buy_price', '0')),
            ask=Decimal(d.get('sell_price', '0')),
            volume=Decimal(d.get('units_traded_24H', '0')),
            timestamp=datetime.now()
        )

    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        params = {'order_currency': symbol, 'payment_currency': 'KRW'}
        data = await self._request('GET', '/public/orderbook/' + symbol, params)
        d = data.get('data', {})
        bids = [[Decimal(b['price']), Decimal(b['quantity'])] for b in d.get('bids', [])[:limit]]
        asks = [[Decimal(a['price']), Decimal(a['quantity'])] for a in d.get('asks', [])[:limit]]
        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.now()
        )

    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        params = {
            'order_currency': symbol,
            'payment_currency': 'KRW',
            'units': str(amount),
            'type': side.value
        }
        data = await self._request('POST', '/trade/market_' + side.value, params, auth=True)
        return self._parse_order(data.get('data', {}), symbol)

    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        params = {
            'order_currency': symbol,
            'payment_currency': 'KRW',
            'units': str(amount),
            'price': str(price),
            'type': side.value
        }
        data = await self._request('POST', '/trade/place', params, auth=True)
        return self._parse_order(data.get('data', {}), symbol)

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        params = {'order_id': order_id, 'type': 'bid', 'order_currency': symbol, 'payment_currency': 'KRW'}
        try:
            await self._request('POST', '/trade/cancel', params, auth=True)
            return True
        except Exception:
            return False

    async def get_order(self, order_id: str, symbol: str) -> Order:
        params = {'order_id': order_id, 'order_currency': symbol, 'payment_currency': 'KRW'}
        data = await self._request('POST', '/info/order_detail', params, auth=True)
        return self._parse_order(data.get('data', {}), symbol)

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        params = {'order_currency': symbol, 'payment_currency': 'KRW'} if symbol else {}
        data = await self._request('POST', '/info/orders', params, auth=True)
        return [self._parse_order(order, symbol or order.get('order_currency', '')) for order in data.get('data', [])]

    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        params = {'order_currency': symbol, 'payment_currency': 'KRW'} if symbol else {}
        data = await self._request('POST', '/info/user_transactions', params, auth=True)
        return [self._parse_order(order, symbol or order.get('order_currency', '')) for order in data.get('data', [])][-limit:]

    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        params = {'order_currency': symbol, 'payment_currency': 'KRW'} if symbol else {}
        data = await self._request('POST', '/info/user_transactions', params, auth=True)
        trades = []
        for trade in data.get('data', [])[-limit:]:
            trades.append(Trade(
                id=str(trade.get('transaction_id', '')),
                order_id=str(trade.get('order_id', '')),
                symbol=symbol or trade.get('order_currency', ''),
                side=OrderSide.BUY if trade.get('type', '') == 'bid' else OrderSide.SELL,
                amount=Decimal(trade.get('units', '0')),
                price=Decimal(trade.get('price', '0')),
                fee=Decimal(trade.get('fee', '0')),
                timestamp=datetime.fromtimestamp(int(trade.get('transaction_date', time.time())))
            ))
        return trades

    async def get_symbols(self) -> List[str]:
        data = await self._request('GET', '/public/ticker/ALL_KRW', {})
        return [s for s in data.get('data', {}) if s not in ['date']]  # 'date'는 메타데이터

    def _parse_order(self, data: Dict, symbol: str) -> Order:
        status_map = {
            'placed': OrderStatus.OPEN,
            'completed': OrderStatus.FILLED,
            'cancelled': OrderStatus.CANCELLED,
            'partially_completed': OrderStatus.PARTIALLY_FILLED,
        }
        return Order(
            id=str(data.get('order_id', '')),
            symbol=symbol,
            side=OrderSide.BUY if data.get('type', '') == 'bid' else OrderSide.SELL,
            type=OrderType.LIMIT if data.get('order_type', 'limit') == 'limit' else OrderType.MARKET,
            amount=Decimal(data.get('units', '0')),
            price=Decimal(data.get('price', '0')) if data.get('price') else None,
            filled=Decimal(data.get('units_traded', '0')),
            remaining=Decimal(data.get('units', '0')) - Decimal(data.get('units_traded', '0')),
            status=status_map.get(data.get('status', ''), OrderStatus.UNKNOWN),
            timestamp=datetime.fromtimestamp(int(data.get('transaction_date', time.time())))
        )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
