"""
OKX 계정 관리 모듈
단일 책임: 계정 관련 기능 (잔고 조회 등)
"""

from typing import Dict, Optional

from ..base import Balance
from .data_mapper import OKXDataMapper
from .http_client import OKXHttpClient


class OKXAccount:
    """OKX 계정 관리"""
    
    def __init__(self, http_client: OKXHttpClient):
        self.http_client = http_client
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        """
        잔고 조회
        
        Args:
            currency: 특정 통화만 조회 (None이면 전체)
            
        Returns:
            통화별 잔고 정보
        """
        data = await self.http_client.request('GET', '/api/v5/account/balance', auth=True)
        balances = OKXDataMapper.map_balance(data)
        
        # 특정 통화만 필터링
        if currency:
            return {currency: balances[currency]} if currency in balances else {}
        
        return balances
