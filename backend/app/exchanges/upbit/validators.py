"""
Upbit 데이터 검증
주문 파라미터 및 응답 데이터 검증
"""

from decimal import Decimal
from typing import Optional
from ..base import OrderSide


class UpbitValidators:
    """Upbit 데이터 검증자"""
    
    # Upbit 최소 주문 금액 (KRW)
    MIN_ORDER_AMOUNT = Decimal('5000')
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        거래쌍 형식 검증
        
        Args:
            symbol: 거래쌍 (예: KRW-BTC)
            
        Returns:
            bool: 유효한 형식 여부
        """
        if not symbol or '-' not in symbol:
            return False
        
        parts = symbol.split('-')
        if len(parts) != 2:
            return False
        
        base, quote = parts
        return len(base) > 0 and len(quote) > 0
    
    @staticmethod
    def validate_order_amount(symbol: str, side: OrderSide, amount: Decimal, price: Optional[Decimal] = None) -> bool:
        """
        주문 수량 검증
        
        Args:
            symbol: 거래쌍
            side: 주문 방향
            amount: 주문 수량
            price: 주문 가격 (지정가 주문시)
            
        Returns:
            bool: 유효한 수량 여부
        """
        if amount <= 0:
            return False
        
        # KRW 마켓의 경우 최소 주문 금액 검증
        if symbol.startswith('KRW-'):
            if side == OrderSide.BUY:
                # 매수시: 금액이 최소 주문 금액 이상이어야 함
                return amount >= UpbitValidators.MIN_ORDER_AMOUNT
            else:
                # 매도시: 금액 * 가격이 최소 주문 금액 이상이어야 함
                if price:
                    order_value = amount * price
                    return order_value >= UpbitValidators.MIN_ORDER_AMOUNT
                return True  # 시장가 매도는 별도 검증
        
        return True
    
    @staticmethod
    def validate_price(price: Decimal) -> bool:
        """
        가격 검증
        
        Args:
            price: 주문 가격
            
        Returns:
            bool: 유효한 가격 여부
        """
        return price > 0
    
    @staticmethod
    def validate_order_params(symbol: str, side: OrderSide, amount: Decimal, price: Optional[Decimal] = None) -> tuple[bool, str]:
        """
        주문 파라미터 종합 검증
        
        Args:
            symbol: 거래쌍
            side: 주문 방향
            amount: 주문 수량
            price: 주문 가격
            
        Returns:
            tuple[bool, str]: (유효성, 오류 메시지)
        """
        if not UpbitValidators.validate_symbol(symbol):
            return False, "잘못된 거래쌍 형식입니다"
        
        if not UpbitValidators.validate_order_amount(symbol, side, amount, price):
            return False, f"최소 주문 금액 {UpbitValidators.MIN_ORDER_AMOUNT}원 이상이어야 합니다"
        
        if price is not None and not UpbitValidators.validate_price(price):
            return False, "가격은 0보다 커야 합니다"
        
        return True, ""
    
    @staticmethod
    def get_min_order_amount(symbol: str) -> Decimal:
        """
        거래쌍별 최소 주문 금액 조회
        
        Args:
            symbol: 거래쌍
            
        Returns:
            Decimal: 최소 주문 금액
        """
        if symbol.startswith('KRW-'):
            return UpbitValidators.MIN_ORDER_AMOUNT
        
        # 다른 기준통화는 추후 추가
        return Decimal('0.00001')
    
    @staticmethod
    def format_symbol(base: str, quote: str) -> str:
        """
        거래쌍 형식 생성
        
        Args:
            base: 기준 통화 (예: KRW)
            quote: 거래 통화 (예: BTC)
            
        Returns:
            str: 거래쌍 (예: KRW-BTC)
        """
        return f"{base.upper()}-{quote.upper()}"
