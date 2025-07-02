"""
거래소 통합 인터페이스 - 추상 기본 클래스
단일 책임: 모든 거래소가 구현해야 하는 공통 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"  
    CANCELLED = "cancelled"
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    UNKNOWN = "unknown"


@dataclass
class Balance:
    """잔고 정보"""
    currency: str
    available: Decimal
    locked: Decimal
    total: Decimal


@dataclass
class Ticker:
    """시세 정보"""
    symbol: str
    price: Decimal
    bid: Decimal
    ask: Decimal
    volume: Decimal
    timestamp: datetime


@dataclass
class OrderBook:
    """호가 정보"""
    symbol: str
    bids: List[List[Decimal]]  # [[price, amount], ...]
    asks: List[List[Decimal]]
    timestamp: datetime


@dataclass
class Order:
    """주문 정보"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    amount: Decimal
    price: Optional[Decimal]
    filled: Decimal
    remaining: Decimal
    status: OrderStatus
    timestamp: datetime
    fee: Optional[Decimal] = None


@dataclass
class Trade:
    """체결 정보"""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    amount: Decimal
    price: Decimal
    fee: Decimal
    timestamp: datetime


class BaseExchange(ABC):
    """
    거래소 기본 인터페이스
    모든 거래소는 이 인터페이스를 구현해야 함
    """
    
    def __init__(self, api_key: str, secret_key: str, **kwargs):
        self.api_key = api_key
        self.secret_key = secret_key
        self.name = self.__class__.__name__.lower().replace('exchange', '')
    
    # === 필수 구현 메서드 ===
    
    @abstractmethod
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        """잔고 조회"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """현재가 조회"""
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        """호가 조회"""
        pass
    
    @abstractmethod
    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        """시장가 주문"""
        pass
    
    @abstractmethod
    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        """지정가 주문"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """주문 취소"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """주문 조회"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """미체결 주문 조회"""
        pass
    
    @abstractmethod
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """주문 내역 조회"""
        pass
    
    @abstractmethod
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        """체결 내역 조회"""
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """거래 가능한 심볼 목록"""
        pass
    
    async def close(self):
        """리소스 정리 (세션 종료 등)"""
        pass
    
    # === 헬퍼 메서드 ===
    
    def format_symbol(self, base: str, quote: str) -> str:
        """심볼 포맷 (거래소별로 오버라이드)"""
        return f"{base}-{quote}"
    
    def parse_symbol(self, symbol: str) -> tuple[str, str]:
        """심볼 파싱 (거래소별로 오버라이드)"""
        parts = symbol.split('-')
        return parts[0], parts[1] if len(parts) > 1 else parts[0]
    
    async def health_check(self) -> bool:
        """거래소 연결 상태 확인"""
        try:
            await self.get_symbols()
            return True
        except Exception:
            return False
