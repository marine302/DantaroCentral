"""
OKX 검증 모듈
단일 책임: 주문 금액, 수량 등 각종 검증 로직
"""

from decimal import Decimal
from typing import Tuple

from .market_data import OKXMarketData


class OKXValidator:
    """OKX 거래 검증"""
    
    def __init__(self, market_data: OKXMarketData):
        self.market_data = market_data
    
    async def validate_order_amount(self, symbol: str, amount: Decimal) -> Tuple[bool, str]:
        """
        주문 금액 검증
        
        Args:
            symbol: 거래쌍 심볼
            amount: 주문 금액 (USD 기준)
            
        Returns:
            (검증 통과 여부, 메시지)
        """
        try:
            # 거래 규칙 및 현재 시세 조회
            rules = await self.market_data.get_trading_rules(symbol)
            ticker = await self.market_data.get_ticker(symbol)
            
            if not rules:
                return False, "거래 규칙을 가져올 수 없습니다"
            
            # 현재 가격으로 수량 계산
            current_price = ticker.price
            quantity = amount / current_price
            
            # 최소 수량 검증
            min_quantity = Decimal(str(rules.get('min_order_value', 0)))
            if quantity < min_quantity:
                min_value = min_quantity * current_price
                return False, f"최소 주문 금액: ${min_value:.2f} (현재: ${amount:.2f})"
            
            # OKX 일반적인 최소 금액 ($5-10)
            if amount < Decimal('5.0'):
                return False, f"OKX 최소 주문 금액 미만: ${amount:.2f} < $5.00"
            
            return True, "검증 통과"
            
        except Exception as e:
            return False, f"검증 오류: {str(e)}"
    
    async def validate_symbol(self, symbol: str) -> Tuple[bool, str]:
        """
        심볼 유효성 검증
        
        Args:
            symbol: 거래쌍 심볼
            
        Returns:
            (검증 통과 여부, 메시지)
        """
        try:
            rules = await self.market_data.get_trading_rules(symbol)
            
            if not rules:
                return False, f"지원되지 않는 심볼: {symbol}"
            
            if rules.get('status') != 'live':
                return False, f"거래 중단된 심볼: {symbol}"
            
            return True, "검증 통과"
            
        except Exception as e:
            return False, f"심볼 검증 오류: {str(e)}"
    
    def validate_price_precision(self, symbol: str, price: Decimal, rules: dict) -> Tuple[bool, str]:
        """
        가격 정밀도 검증
        
        Args:
            symbol: 거래쌍 심볼
            price: 주문 가격
            rules: 거래 규칙
            
        Returns:
            (검증 통과 여부, 메시지)
        """
        try:
            tick_size = Decimal(str(rules.get('tick_size', '0.000001')))
            
            # 가격이 tick_size의 배수인지 확인
            if price % tick_size != 0:
                return False, f"가격 단위 오류: {price} (단위: {tick_size})"
            
            return True, "검증 통과"
            
        except Exception as e:
            return False, f"가격 정밀도 검증 오류: {str(e)}"
