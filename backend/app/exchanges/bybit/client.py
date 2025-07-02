"""
Bybit 거래소 클라이언트
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

class BybitClient(BaseExchange):
    """Bybit 거래소 구현"""
    BASE_URL = "https://api.bybit.com"

    def __init__(self, api_key: str, secret_key: str, **kwargs):
        super().__init__(api_key, secret_key, **kwargs)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(sorted(params.items()))
        ts = str(int(time.time() * 1000))
        params['api_key'] = self.api_key
        params['timestamp'] = ts
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(self.secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        params['sign'] = signature
        return params

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, auth: bool = False) -> Any:
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        headers = {}
        if auth:
            params = self._sign(params)
        try:
            if method.upper() == 'GET':
                async with session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, data=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'DELETE':
                async with session.delete(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                raise Exception(f"지원되지 않는 HTTP 메서드: {method}")
        except aiohttp.ClientError as e:
            raise Exception(f"Bybit API 오류: {str(e)}")

    # === 인터페이스 구현 ===

    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        data = await self._request('GET', '/v5/account/wallet-balance', auth=True)
        balances = {}
        for asset in data.get('result', {}).get('list', [{}])[0].get('coin', []):
            curr = asset.get('coin')
            if currency and curr != currency:
                continue
            available = Decimal(asset.get('availableToWithdraw', '0'))
            locked = Decimal(asset.get('locked', '0'))
            balances[curr] = Balance(
                currency=curr,
                available=available,
                locked=locked,
                total=available + locked
            )
        return balances

    async def get_ticker(self, symbol: str) -> Ticker:
        params = {'symbol': symbol}
        data = await self._request('GET', '/v5/market/tickers', params)
        ticker_data = None
        for t in data.get('result', {}).get('list', []):
            if t.get('symbol') == symbol:
                ticker_data = t
                break
        if not ticker_data:
            raise Exception(f"심볼 {symbol}의 시세 정보를 찾을 수 없습니다")
        return Ticker(
            symbol=symbol,
            price=Decimal(ticker_data.get('lastPrice', '0')),
            bid=Decimal(ticker_data.get('bid1Price', '0')),
            ask=Decimal(ticker_data.get('ask1Price', '0')),
            volume=Decimal(ticker_data.get('turnover24h', '0')),
            timestamp=datetime.now()
        )

    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        params = {'symbol': symbol, 'limit': limit}
        data = await self._request('GET', '/v5/market/orderbook', params)
        orderbook = data.get('result', {})
        bids = [[Decimal(b[0]), Decimal(b[1])] for b in orderbook.get('b', [])[:limit]]
        asks = [[Decimal(a[0]), Decimal(a[1])] for a in orderbook.get('a', [])[:limit]]
        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.now()
        )

    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        params = {
            'symbol': symbol,
            'side': side.value.upper(),
            'orderType': 'Market',
            'qty': str(amount)
        }
        data = await self._request('POST', '/v5/order/create', params, auth=True)
        return self._parse_order(data.get('result', {}), symbol)

    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        params = {
            'symbol': symbol,
            'side': side.value.upper(),
            'orderType': 'Limit',
            'qty': str(amount),
            'price': str(price),
            'timeInForce': 'GTC'
        }
        data = await self._request('POST', '/v5/order/create', params, auth=True)
        return self._parse_order(data.get('result', {}), symbol)

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        params = {'symbol': symbol, 'orderId': order_id}
        try:
            await self._request('POST', '/v5/order/cancel', params, auth=True)
            return True
        except Exception:
            return False

    async def get_order(self, order_id: str, symbol: str) -> Order:
        params = {'symbol': symbol, 'orderId': order_id}
        data = await self._request('GET', '/v5/order', params, auth=True)
        return self._parse_order(data.get('result', {}), symbol)

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        params = {'symbol': symbol} if symbol else {}
        data = await self._request('GET', '/v5/order/realtime', params, auth=True)
        return [self._parse_order(order, symbol or order.get('symbol', '')) for order in data.get('result', {}).get('list', [])]

    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        params = {'symbol': symbol} if symbol else {}
        data = await self._request('GET', '/v5/order/history', params, auth=True)
        return [self._parse_order(order, symbol or order.get('symbol', '')) for order in data.get('result', {}).get('list', [])][-limit:]

    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        params = {'symbol': symbol} if symbol else {}
        data = await self._request('GET', '/v5/execution/list', params, auth=True)
        trades = []
        for trade in data.get('result', {}).get('list', [])[-limit:]:
            trades.append(Trade(
                id=str(trade.get('execId', '')),
                order_id=str(trade.get('orderId', '')),
                symbol=symbol or trade.get('symbol', ''),
                side=OrderSide.BUY if trade.get('side', '').upper() == 'BUY' else OrderSide.SELL,
                amount=Decimal(trade.get('execQty', '0')),
                price=Decimal(trade.get('execPrice', '0')),
                fee=Decimal(trade.get('execFee', '0')),
                timestamp=datetime.fromtimestamp(int(trade.get('execTime', time.time()*1000)) / 1000)
            ))
        return trades

    async def get_symbols(self) -> List[str]:
        data = await self._request('GET', '/v5/market/instruments-info')
        return [s.get('symbol', '') for s in data.get('result', {}).get('list', [])]

    def _parse_order(self, data: Dict, symbol: str) -> Order:
        status_map = {
            'Created': OrderStatus.OPEN,
            'Filled': OrderStatus.FILLED,
            'Cancelled': OrderStatus.CANCELLED,
            'Rejected': OrderStatus.CANCELLED,
            'PartiallyFilled': OrderStatus.PARTIALLY_FILLED,
        }
        return Order(
            id=str(data.get('orderId', '')),
            symbol=symbol,
            side=OrderSide(data.get('side', 'Buy').lower()),
            type=OrderType(data.get('orderType', 'Market').lower()),
            amount=Decimal(data.get('qty', '0')),
            price=Decimal(data.get('price', '0')) if data.get('price') else None,
            filled=Decimal(data.get('cumExecQty', '0')),
            remaining=Decimal(data.get('qty', '0')) - Decimal(data.get('cumExecQty', '0')),
            status=status_map.get(data.get('orderStatus', ''), OrderStatus.UNKNOWN),
            timestamp=datetime.fromtimestamp(int(data.get('createdTime', time.time()*1000)) / 1000)
        )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
