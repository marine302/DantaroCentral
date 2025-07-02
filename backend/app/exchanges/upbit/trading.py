"""
Upbit 거래 실행
주문 생성, 취소, 조회 등 거래 관련 기능
"""

from typing import List, Optional
from decimal import Decimal
from ..base import Order, Trade, OrderSide, OrderType
from .http_client import UpbitHttpClient
from .data_mapper import UpbitDataMapper


class UpbitTrading:
    """Upbit 거래 실행"""
    
    def __init__(self, http_client: UpbitHttpClient):
        self.http_client = http_client
        self.data_mapper = UpbitDataMapper()
    
    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        """
        시장가 주문 생성
        
        Args:
            symbol: 거래쌍 (예: KRW-BTC)
            side: 주문 방향 (BUY/SELL)
            amount: 주문 수량 (매수시 KRW 금액, 매도시 코인 수량)
            
        Returns:
            Order: 생성된 주문 정보
        """
        upbit_side = 'bid' if side == OrderSide.BUY else 'ask'
        
        data = {
            'market': symbol,
            'side': upbit_side,
        }
        
        if side == OrderSide.BUY:
            # 매수: 원화 금액으로 주문
            data['ord_type'] = 'price'
            data['price'] = str(amount)
        else:
            # 매도: 코인 수량으로 주문
            data['ord_type'] = 'market'
            data['volume'] = str(amount)
        
        response = await self.http_client.request('POST', '/v1/orders', data=data)
        return self.data_mapper.parse_order(response)
    
    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        """
        지정가 주문 생성
        
        Args:
            symbol: 거래쌍 (예: KRW-BTC)
            side: 주문 방향 (BUY/SELL)
            amount: 주문 수량
            price: 주문 가격
            
        Returns:
            Order: 생성된 주문 정보
        """
        upbit_side = 'bid' if side == OrderSide.BUY else 'ask'
        
        data = {
            'market': symbol,
            'side': upbit_side,
            'ord_type': 'limit',
            'volume': str(amount),
            'price': str(price)
        }
        
        response = await self.http_client.request('POST', '/v1/orders', data=data)
        return self.data_mapper.parse_order(response)
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        주문 취소
        
        Args:
            order_id: 주문 ID
            symbol: 거래쌍 (사용되지 않음)
            
        Returns:
            bool: 취소 성공 여부
        """
        data = {'uuid': order_id}
        
        try:
            await self.http_client.request('DELETE', '/v1/order', data=data)
            return True
        except Exception:
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """
        주문 조회
        
        Args:
            order_id: 주문 ID
            symbol: 거래쌍 (사용되지 않음)
            
        Returns:
            Order: 주문 정보
        """
        params = {'uuid': order_id}
        response = await self.http_client.request('GET', '/v1/order', params=params)
        return self.data_mapper.parse_order(response)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        미체결 주문 목록 조회
        
        Args:
            symbol: 거래쌍 (None이면 전체)
            
        Returns:
            List[Order]: 미체결 주문 목록
        """
        params = {'state': 'wait'}
        if symbol:
            params['market'] = symbol
        
        data = await self.http_client.request('GET', '/v1/orders', params=params)
        return [self.data_mapper.parse_order(item) for item in data]
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """
        주문 내역 조회
        
        Args:
            symbol: 거래쌍 (None이면 전체)
            limit: 조회할 주문 개수
            
        Returns:
            List[Order]: 주문 내역 목록
        """
        params = {'state': 'done', 'limit': limit}
        if symbol:
            params['market'] = symbol
        
        data = await self.http_client.request('GET', '/v1/orders', params=params)
        return [self.data_mapper.parse_order(item) for item in data]
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        """
        거래 내역 조회
        
        Args:
            symbol: 거래쌍 (None이면 전체)
            limit: 조회할 거래 개수
            
        Returns:
            List[Trade]: 거래 내역 목록
        """
        params = {'limit': limit}
        if symbol:
            params['market'] = symbol
        
        data = await self.http_client.request('GET', '/v1/orders', params=params)
        
        trades = []
        for order_data in data:
            if order_data['state'] == 'done':  # 체결된 주문만
                trade = self.data_mapper.parse_trade(order_data)
                trades.append(trade)
        
        return trades
