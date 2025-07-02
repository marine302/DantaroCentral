"""
Upbit 계정 관리
잔고 조회 및 계정 정보 관리
"""

from typing import Dict, Optional
from decimal import Decimal
from ..base import Balance
from .http_client import UpbitHttpClient
from .data_mapper import UpbitDataMapper


class UpbitAccount:
    """Upbit 계정 관리"""
    
    def __init__(self, http_client: UpbitHttpClient):
        self.http_client = http_client
        self.data_mapper = UpbitDataMapper()
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        """
        잔고 조회
        
        Args:
            currency: 특정 화폐 조회 (None이면 전체)
            
        Returns:
            Dict[str, Balance]: 화폐별 잔고 정보
        """
        data = await self.http_client.request('GET', '/v1/accounts')
        
        balances = {}
        for item in data:
            balance = self.data_mapper.parse_balance(item)
            if currency is None or balance.currency.upper() == currency.upper():
                balances[balance.currency] = balance
        
        return balances
    
    async def get_account_info(self) -> Dict:
        """계정 정보 조회"""
        return await self.http_client.request('GET', '/v1/accounts')
    
    async def get_deposit_address(self, currency: str) -> Dict:
        """입금 주소 조회"""
        params = {'currency': currency}
        return await self.http_client.request('GET', '/v1/deposits/coin_address', params=params)
    
    async def get_deposit_history(self, currency: Optional[str] = None) -> Dict:
        """입금 내역 조회"""
        params = {}
        if currency:
            params['currency'] = currency
        return await self.http_client.request('GET', '/v1/deposits', params=params)
    
    async def get_withdrawal_history(self, currency: Optional[str] = None) -> Dict:
        """출금 내역 조회"""
        params = {}
        if currency:
            params['currency'] = currency
        return await self.http_client.request('GET', '/v1/withdraws', params=params)
