"""
Coinone 거래소 API 구현
단일 책임: Coinone 공식 API를 통합 인터페이스로 변환

참고: https://doc.coinone.co.kr/
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

class CoinoneExchange(BaseExchange):
    """Coinone 거래소 구현"""
    BASE_URL = "https://api.coinone.co.kr"

    def __init__(self, api_key: str, secret_key: str, **kwargs):
        super().__init__(api_key, secret_key, **kwargs)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def _sign(self, payload: Dict[str, Any]) -> str:
        import base64
        import json
        payload_str = json.dumps(payload, separators=(',', ':'))
        payload_b64 = base64.b64encode(payload_str.encode()).decode()
        signature = hmac.new(self.secret_key.encode(), payload_b64.encode(), hashlib.sha512).hexdigest()
        return signature

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, auth: bool = False) -> Any:
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}
        params = params or {}
        if auth:
            headers['X-COINONE-APIKEY'] = self.api_key
            headers['X-COINONE-SIGNATURE'] = self._sign(params)
            headers['Content-Type'] = 'application/json'
        try:
            if method.upper() == 'GET':
                async with session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, json=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                raise Exception(f"지원되지 않는 HTTP 메서드: {method}")
        except aiohttp.ClientError as e:
            raise Exception(f"Coinone API 오류: {str(e)}")

    # === 인터페이스 구현 ===

    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        data = await self._request('POST', '/v2/account/balance/', {}, auth=True)
        balances = {}
        for curr, info in data.items():
            if not isinstance(info, dict) or 'avail' not in info:
                continue
            if currency and curr != currency:
                continue
            available = Decimal(info.get('avail', '0'))
            locked = Decimal(info.get('balance', '0')) - available
            balances[curr] = Balance(
                currency=curr,
                available=available,
                locked=locked,
                total=Decimal(info.get('balance', '0'))
            )
        return balances

    async def get_ticker(self, symbol: str) -> Ticker:
        params = {'currency': symbol.lower()}
        data = await self._request('GET', '/ticker/', params)
        return Ticker(
            symbol=symbol,
            price=Decimal(data.get('last', '0')),
            bid=Decimal(data.get('bid', '0')),
            ask=Decimal(data.get('ask', '0')),
            volume=Decimal(data.get('volume', '0')),
            timestamp=datetime.now()
        )

    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        params = {'currency': symbol.lower()}
        data = await self._request('GET', '/orderbook/', params)
        bids = [[Decimal(b['price']), Decimal(b['qty'])] for b in data.get('bid', [])[:limit]]
        asks = [[Decimal(a['price']), Decimal(a['qty'])] for a in data.get('ask', [])[:limit]]
        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.now()
        )

    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        params = {
            'currency': symbol.lower(),
            'qty': str(amount),
            'is_quoted': False
        }
        endpoint = '/v2/order/market_buy/' if side == OrderSide.BUY else '/v2/order/market_sell/'
        data = await self._request('POST', endpoint, params, auth=True)
        return self._parse_order(data, symbol)

    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        params = {
            'currency': symbol.lower(),
            'qty': str(amount),
            'price': str(price)
        }
        endpoint = '/v2/order/limit_buy/' if side == OrderSide.BUY else '/v2/order/limit_sell/'
        data = await self._request('POST', endpoint, params, auth=True)
        return self._parse_order(data, symbol)

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        params = {'order_id': order_id, 'currency': symbol.lower()}
        try:
            await self._request('POST', '/v2/order/cancel/', params, auth=True)
            return True
        except Exception:
            return False

    async def get_order(self, order_id: str, symbol: str) -> Order:
        params = {'order_id': order_id, 'currency': symbol.lower()}
        data = await self._request('POST', '/v2/order/info/', params, auth=True)
        return self._parse_order(data, symbol)

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        params = {'currency': symbol.lower()} if symbol else {}
        data = await self._request('POST', '/v2/order/limit_orders/', params, auth=True)
        return [self._parse_order(order, symbol or order.get('currency', '')) for order in data.get('limitOrders', [])]

    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        params = {'currency': symbol.lower()} if symbol else {}
        data = await self._request('POST', '/v2/order/complete_orders/', params, auth=True)
        return [self._parse_order(order, symbol or order.get('currency', '')) for order in data.get('completeOrders', [])][-limit:]

    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        params = {'currency': symbol.lower()} if symbol else {}
        data = await self._request('POST', '/v2/order/complete_orders/', params, auth=True)
        trades = []
        for trade in data.get('completeOrders', [])[-limit:]:
            trades.append(Trade(
                id=str(trade.get('orderId', '')),
                order_id=str(trade.get('orderId', '')),
                symbol=symbol or trade.get('currency', ''),
                side=OrderSide.BUY if trade.get('is_ask', False) else OrderSide.SELL,
                amount=Decimal(trade.get('qty', '0')),
                price=Decimal(trade.get('price', '0')),
                fee=Decimal(trade.get('fee', '0')),
                timestamp=datetime.fromtimestamp(int(trade.get('timestamp', time.time())))
            ))
        return trades

    async def get_symbols(self) -> List[str]:
        data = await self._request('GET', '/v2/market/all/', params={})
        return [s.get('currency', '') for s in data.get('markets', [])]

    def _parse_order(self, data: Dict, symbol: str) -> Order:
        status_map = {
            'live': OrderStatus.OPEN,
            'filled': OrderStatus.FILLED,
            'cancel': OrderStatus.CANCELLED,
            'partially_filled': OrderStatus.PARTIALLY_FILLED,
        }
        return Order(
            id=str(data.get('orderId', '')),
            symbol=symbol,
            side=OrderSide.BUY if data.get('is_ask', False) else OrderSide.SELL,
            type=OrderType.LIMIT if data.get('type', 'limit') == 'limit' else OrderType.MARKET,
            amount=Decimal(data.get('qty', '0')),
            price=Decimal(data.get('price', '0')) if data.get('price') else None,
            filled=Decimal(data.get('filledQty', '0')),
            remaining=Decimal(data.get('qty', '0')) - Decimal(data.get('filledQty', '0')),
            status=status_map.get(data.get('status', ''), OrderStatus.UNKNOWN),
            timestamp=datetime.fromtimestamp(int(data.get('timestamp', time.time())))
        )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
