"""
Upbit 메인 클라이언트
모든 Upbit 기능을 통합하는 파사드 클래스
"""

from typing import Dict, List, Optional
from decimal import Decimal
from ..base import BaseExchange, Balance, Ticker, OrderBook, Order, Trade, OrderSide, OrderType
from .http_client import UpbitHttpClient
from .account import UpbitAccount
from .market_data import UpbitMarketData
from .trading import UpbitTrading
from .validators import UpbitValidators


class UpbitExchange(BaseExchange):
    """Upbit 거래소 통합 클라이언트"""
    
    def __init__(self, api_key: str, secret_key: str, **kwargs):
        super().__init__(api_key, secret_key, **kwargs)
        
        # HTTP 클라이언트 초기화
        self.http_client = UpbitHttpClient(api_key, secret_key)
        
        # 각 기능별 모듈 초기화
        self.account = UpbitAccount(self.http_client)
        self.market_data = UpbitMarketData(self.http_client)
        self.trading = UpbitTrading(self.http_client)
        self.validators = UpbitValidators()
    
    # ==================== 계정 관련 메서드 ====================
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        """잔고 조회"""
        return await self.account.get_balance(currency)
    
    # ==================== 시장 데이터 메서드 ====================
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """시세 정보 조회"""
        return await self.market_data.get_ticker(symbol)
    
    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        """호가 정보 조회"""
        return await self.market_data.get_orderbook(symbol, limit)
    
    async def get_symbols(self) -> List[str]:
        """전체 거래쌍 목록 조회"""
        return await self.market_data.get_symbols()
    
    # ==================== 거래 관련 메서드 ====================
    
    async def create_market_order(self, symbol: str, side: OrderSide, amount: Decimal) -> Order:
        """시장가 주문 생성"""
        # 주문 파라미터 검증
        is_valid, error_msg = self.validators.validate_order_params(symbol, side, amount)
        if not is_valid:
            raise ValueError(error_msg)
        
        return await self.trading.create_market_order(symbol, side, amount)
    
    async def create_limit_order(self, symbol: str, side: OrderSide, amount: Decimal, price: Decimal) -> Order:
        """지정가 주문 생성"""
        # 주문 파라미터 검증
        is_valid, error_msg = self.validators.validate_order_params(symbol, side, amount, price)
        if not is_valid:
            raise ValueError(error_msg)
        
        return await self.trading.create_limit_order(symbol, side, amount, price)
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """주문 취소"""
        return await self.trading.cancel_order(order_id, symbol)
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """주문 조회"""
        return await self.trading.get_order(order_id, symbol)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """미체결 주문 목록 조회"""
        return await self.trading.get_open_orders(symbol)
    
    async def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """주문 내역 조회"""
        return await self.trading.get_order_history(symbol, limit)
    
    async def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Trade]:
        """거래 내역 조회"""
        return await self.trading.get_trade_history(symbol, limit)
    
    # ==================== 추가 기능 메서드 ====================
    
    async def get_trading_rules(self, symbol: str) -> Dict:
        """
        거래 규칙 조회
        
        Args:
            symbol: 거래쌍
            
        Returns:
            Dict: 거래 규칙 정보
        """
        return {
            'symbol': symbol,
            'min_order_amount': str(self.validators.get_min_order_amount(symbol)),
            'price_precision': 8,
            'quantity_precision': 8,
            'base_currency': symbol.split('-')[0],
            'quote_currency': symbol.split('-')[1],
        }
    
    async def get_candles(self, symbol: str, interval: str = '1m', count: int = 100) -> List[dict]:
        """캔들 차트 데이터 조회"""
        return await self.market_data.get_candles(symbol, interval, count)
    
    async def get_recent_trades(self, symbol: str, count: int = 100) -> List[dict]:
        """최근 체결 내역 조회"""
        return await self.market_data.get_recent_trades(symbol, count)
    
    # ==================== 리소스 관리 ====================
    
    async def close(self):
        """연결 종료"""
        await self.http_client.close()
    
    # ==================== 컨텍스트 매니저 지원 ====================
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
