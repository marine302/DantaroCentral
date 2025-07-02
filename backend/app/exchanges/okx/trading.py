"""
OKX 거래 모듈
단일 책임: 주문 생성, 취소, 조회, 체결 내역 등 거래 관련 기능
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from ..base import Order, Trade, OrderSide, OrderType, OrderStatus
from .data_mapper import OKXDataMapper
from .http_client import OKXHttpClient


class OKXTrading:
    """OKX 거래 관리"""
    
    def __init__(self, http_client: OKXHttpClient):
        self.http_client = http_client
    
    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        """
        시장가 주문
        
        Args:
            symbol: 거래쌍 심볼
            side: 주문 방향 (buy/sell)
            amount: 주문 수량
            
        Returns:
            주문 정보
        """
        params = {
            'instId': symbol,
            'tdMode': 'cash',
            'side': side.value,
            'ordType': 'market',
            'sz': str(amount)
        }
        
        data = await self.http_client.request('POST', '/api/v5/trade/order', params, auth=True)
        
        if not data:
            raise Exception("주문 생성 실패")
        
        order_data = data[0]
        return OKXDataMapper.map_order(
            order_data, symbol=symbol, side=side, 
            order_type=OrderType.MARKET, amount=amount
        )
    
    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        """
        지정가 주문
        
        Args:
            symbol: 거래쌍 심볼
            side: 주문 방향 (buy/sell)
            amount: 주문 수량
            price: 주문 가격
            
        Returns:
            주문 정보
        """
        params = {
            'instId': symbol,
            'tdMode': 'cash',
            'side': side.value,
            'ordType': 'limit',
            'sz': str(amount),
            'px': str(price)
        }
        
        data = await self.http_client.request('POST', '/api/v5/trade/order', params, auth=True)
        
        if not data:
            raise Exception("주문 생성 실패")
        
        order_data = data[0]
        return OKXDataMapper.map_order(
            order_data, symbol=symbol, side=side, 
            order_type=OrderType.LIMIT, amount=amount, price=price
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        주문 취소
        
        Args:
            order_id: 주문 ID
            symbol: 거래쌍 심볼
            
        Returns:
            취소 성공 여부
        """
        params = {
            'instId': symbol,
            'ordId': order_id
        }
        
        try:
            await self.http_client.request('POST', '/api/v5/trade/cancel-order', params, auth=True)
            return True
        except Exception:
            return False
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """
        주문 조회
        
        Args:
            order_id: 주문 ID
            symbol: 거래쌍 심볼
            
        Returns:
            주문 정보
        """
        params = {
            'instId': symbol,
            'ordId': order_id
        }
        
        data = await self.http_client.request('GET', '/api/v5/trade/order', params, auth=True)
        
        if not data:
            raise Exception(f"주문 {order_id}를 찾을 수 없습니다")
        
        return OKXDataMapper.map_order(data[0])
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        미체결 주문 조회
        
        Args:
            symbol: 거래쌍 심볼 (None이면 전체)
            
        Returns:
            미체결 주문 목록
        """
        params = {}
        if symbol:
            params['instId'] = symbol
        
        data = await self.http_client.request('GET', '/api/v5/trade/orders-pending', params, auth=True)
        return OKXDataMapper.map_order_list(data)
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """
        주문 내역 조회
        
        Args:
            symbol: 거래쌍 심볼 (None이면 전체)
            limit: 조회 개수
            
        Returns:
            주문 내역 목록
        """
        params = {'limit': str(limit)}
        if symbol:
            params['instId'] = symbol
        
        data = await self.http_client.request('GET', '/api/v5/trade/orders-history', params, auth=True)
        return OKXDataMapper.map_order_list(data)
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        """
        체결 내역 조회
        
        Args:
            symbol: 거래쌍 심볼 (None이면 전체)
            limit: 조회 개수
            
        Returns:
            체결 내역 목록
        """
        params = {'limit': str(limit)}
        if symbol:
            params['instId'] = symbol
        
        data = await self.http_client.request('GET', '/api/v5/trade/fills', params, auth=True)
        return OKXDataMapper.map_trade_history(data)
