"""
Gate.io 거래소 API 구현
단일 책임: Gate.io 공식 API를 통합 인터페이스로 변환

참고: https://www.gate.io/docs/developers/apiv4/
"""

import hashlib
import hmac
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

import aiohttp

from ..base import (
    BaseExchange, Balance, Ticker, OrderBook, Order, Trade,
    OrderSide, OrderType, OrderStatus
)


class GateExchange(BaseExchange):
    """Gate.io 거래소 구현"""
    
    BASE_URL = "https://api.gateio.ws"
    
    def __init__(self, api_key: str, secret_key: str, **kwargs):
        super().__init__(api_key, secret_key, **kwargs)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 관리"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _generate_auth_headers(self, method: str, url: str, query_string: str = "", body: str = "") -> Dict[str, str]:
        """Gate.io 인증 헤더 생성"""
        timestamp = str(int(time.time()))
        
        payload = f"{method}\n{url}\n{query_string}\n{hashlib.sha512(body.encode()).hexdigest()}\n{timestamp}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return {
            'KEY': self.api_key,
            'Timestamp': timestamp,
            'SIGN': signature,
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                      auth: bool = False) -> Any:
        """HTTP 요청 처리"""
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {'Content-Type': 'application/json'}
        query_string = ""
        body = ""
        
        if method.upper() == 'GET' and params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
        elif method.upper() == 'POST' and params:
            import json
            body = json.dumps(params)
        
        if auth:
            headers.update(self._generate_auth_headers(method, endpoint, query_string, body))
        
        try:
            if method.upper() == 'GET':
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, data=body, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'DELETE':
                async with session.delete(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                raise Exception(f"지원되지 않는 HTTP 메서드: {method}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"Gate.io API 오류: {str(e)}")
    
    # === 인터페이스 구현 ===
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        """잔고 조회"""
        data = await self._request('GET', '/api/v4/spot/accounts', auth=True)
        balances = {}
        
        if isinstance(data, list):
            for account in data:
                if not isinstance(account, dict):
                    continue
                curr = account.get('currency')
                if not curr or not isinstance(curr, str):
                    continue
                if currency and curr != currency:
                    continue
                
                available = Decimal(account.get('available', '0'))
                locked = Decimal(account.get('locked', '0'))
                
                balances[curr] = Balance(
                    currency=curr,
                    available=available,
                    locked=locked,
                    total=available + locked
                )
        
        return balances
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """현재가 조회"""
        data = await self._request('GET', f'/api/v4/spot/tickers/{symbol}')
        
        if not isinstance(data, dict):
            raise Exception(f"심볼 {symbol}의 시세 정보를 찾을 수 없습니다")
        
        return Ticker(
            symbol=symbol,
            price=Decimal(data.get('last', '0')),
            bid=Decimal(data.get('highest_bid', '0')),
            ask=Decimal(data.get('lowest_ask', '0')),
            volume=Decimal(data.get('base_volume', '0')),
            timestamp=datetime.now()
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        """호가 조회"""
        params = {'limit': str(limit)}
        data = await self._request('GET', f'/api/v4/spot/order_book/{symbol}', params)
        
        if not isinstance(data, dict):
            raise Exception(f"심볼 {symbol}의 호가 정보를 찾을 수 없습니다")
        
        bids = [[Decimal(bid[0]), Decimal(bid[1])] for bid in data.get('bids', [])]
        asks = [[Decimal(ask[0]), Decimal(ask[1])] for ask in data.get('asks', [])]
        
        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.now()
        )
    
    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        """시장가 주문"""
        params = {
            'currency_pair': symbol,
            'side': side.value,
            'type': 'market'
        }
        
        if side == OrderSide.BUY:
            params['amount'] = str(amount)  # 매수 시 금액
        else:
            # 매도 시에는 수량을 기준으로 하지만, 시장가이므로 금액으로 변환 필요
            params['amount'] = str(amount)
        
        data = await self._request('POST', '/api/v4/spot/orders', params, auth=True)
        
        if not isinstance(data, dict):
            raise Exception("주문 생성 실패")
        
        return Order(
            id=data.get('id', ''),
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
            'currency_pair': symbol,
            'side': side.value,
            'amount': str(amount),
            'price': str(price),
            'type': 'limit'
        }
        
        data = await self._request('POST', '/api/v4/spot/orders', params, auth=True)
        
        if not isinstance(data, dict):
            raise Exception("주문 생성 실패")
        
        return Order(
            id=data.get('id', ''),
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
        try:
            await self._request('DELETE', f'/api/v4/spot/orders/{order_id}', {'currency_pair': symbol}, auth=True)
            return True
        except Exception:
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """주문 조회"""
        params = {'currency_pair': symbol}
        data = await self._request('GET', f'/api/v4/spot/orders/{order_id}', params, auth=True)
        
        if not isinstance(data, dict):
            raise Exception(f"주문 {order_id}를 찾을 수 없습니다")
        
        return self._parse_order(data)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """미체결 주문 조회"""
        params = {'status': 'open'}
        if symbol:
            params['currency_pair'] = symbol
        
        data = await self._request('GET', '/api/v4/spot/orders', params, auth=True)
        
        if not isinstance(data, list):
            return []
        
        return [self._parse_order(order_data) for order_data in data if isinstance(order_data, dict)]
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """주문 내역 조회"""
        params = {'status': 'finished', 'limit': str(limit)}
        if symbol:
            params['currency_pair'] = symbol
        
        data = await self._request('GET', '/api/v4/spot/orders', params, auth=True)
        
        if not isinstance(data, list):
            return []
        
        return [self._parse_order(order_data) for order_data in data if isinstance(order_data, dict)]
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        """체결 내역 조회"""
        params = {'limit': str(limit)}
        if symbol:
            params['currency_pair'] = symbol
        
        data = await self._request('GET', '/api/v4/spot/my_trades', params, auth=True)
        trades = []
        
        if isinstance(data, list):
            for trade_data in data:
                if not isinstance(trade_data, dict):
                    continue
                
                trades.append(Trade(
                    id=trade_data.get('id', ''),
                    order_id=trade_data.get('order_id', ''),
                    symbol=trade_data.get('currency_pair', ''),
                    side=OrderSide(trade_data.get('side', 'buy')),
                    amount=Decimal(trade_data.get('amount', '0')),
                    price=Decimal(trade_data.get('price', '0')),
                    fee=Decimal(trade_data.get('fee', '0')),
                    timestamp=datetime.fromtimestamp(int(trade_data.get('create_time', '0')))
                ))
        
        return trades
    
    async def get_symbols(self) -> List[str]:
        """거래 가능한 심볼 목록"""
        data = await self._request('GET', '/api/v4/spot/currency_pairs')
        
        if not isinstance(data, list):
            return []
        
        return [pair.get('id', '') for pair in data if isinstance(pair, dict)]
    
    def _parse_order(self, data: Dict) -> Order:
        """주문 데이터 파싱"""
        status_map = {
            'open': OrderStatus.OPEN,
            'closed': OrderStatus.CLOSED,
            'cancelled': OrderStatus.CANCELLED
        }
        
        return Order(
            id=data.get('id', ''),
            symbol=data.get('currency_pair', ''),
            side=OrderSide(data.get('side', 'buy')),
            type=OrderType.LIMIT if data.get('type', 'limit') == 'limit' else OrderType.MARKET,
            amount=Decimal(data.get('amount', '0')),
            price=Decimal(data.get('price', '0')) if data.get('price') else None,
            filled=Decimal(data.get('filled_total', '0')),
            remaining=Decimal(data.get('left', '0')),
            status=status_map.get(data.get('status', ''), OrderStatus.PENDING),
            timestamp=datetime.fromtimestamp(int(data.get('create_time', '0')))
        )
    
    async def close(self):
        """세션 정리"""
        if self.session and not self.session.closed:
            await self.session.close()
