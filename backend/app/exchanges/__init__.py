"""
거래소 API 연동을 위한 공통 인터페이스 모듈
모든 거래소는 Factory 패턴을 통해 접근하세요.
"""

# 기본 타입과 클래스들을 base에서 import
from .base import (
    BaseExchange, Balance, Ticker, OrderBook, Order, Trade,
    OrderSide, OrderType, OrderStatus
)

# 모듈화된 거래소들
from .okx import OKXExchange
from .coinone import CoinoneExchange  
from .gateio import GateExchange
from .upbit import UpbitExchange
from .binance import BinanceClient
from .bithumb import BithumbClient  
from .bybit import BybitClient

# 팩토리 (권장 사용 방법)
from .factory import ExchangeFactory

__all__ = [
    # Base types
    'BaseExchange', 'Balance', 'Ticker', 'OrderBook', 'Order', 'Trade',
    'OrderSide', 'OrderType', 'OrderStatus',
    
    # 모듈화된 거래소들
    'OKXExchange', 'CoinoneExchange', 'GateExchange', 'UpbitExchange',
    'BinanceClient', 'BithumbClient', 'BybitClient',
    
    # Factory (권장)
    'ExchangeFactory'
]

# 사용 예시:
# from app.exchanges import ExchangeFactory
# exchange = ExchangeFactory.create_exchange('okx', api_key='...', secret_key='...', passphrase='...')
