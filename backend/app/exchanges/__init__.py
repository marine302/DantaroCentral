"""
거래소 API 연동을 위한 공통 인터페이스 모듈
"""

# 기본 타입과 클래스들을 base에서 import
from .base import (
    BaseExchange, Balance, Ticker, OrderBook, Order, Trade,
    OrderSide, OrderType, OrderStatus
)

# Phase 6 priority exchanges
from .okx import OKXExchange
from .coinone import CoinoneExchange
from .gate import GateExchange

# 팩토리
from .factory import ExchangeFactory

__all__ = [
    # Base types
    'BaseExchange', 'Balance', 'Ticker', 'OrderBook', 'Order', 'Trade',
    'OrderSide', 'OrderType', 'OrderStatus',
    
    # Exchanges
    'OKXExchange', 'CoinoneExchange', 'GateExchange',
    
    # Factory
    'ExchangeFactory'
]

