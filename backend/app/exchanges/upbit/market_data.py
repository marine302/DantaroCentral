"""
Upbit 시장 데이터
시세, 호가, 거래 내역 등 공개 데이터 조회
"""

from typing import List, Optional
from ..base import Ticker, OrderBook
from .http_client import UpbitHttpClient
from .data_mapper import UpbitDataMapper


class UpbitMarketData:
    """Upbit 시장 데이터 관리"""
    
    def __init__(self, http_client: UpbitHttpClient):
        self.http_client = http_client
        self.data_mapper = UpbitDataMapper()
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        시세 정보 조회
        
        Args:
            symbol: 거래쌍 (예: KRW-BTC)
            
        Returns:
            Ticker: 시세 정보
        """
        params = {'markets': symbol}
        data = await self.http_client.request('GET', '/v1/ticker', params=params, auth_required=False)
        
        if not data:
            raise Exception(f"시세 정보를 찾을 수 없습니다: {symbol}")
        
        return self.data_mapper.parse_ticker(data[0])
    
    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        """
        호가 정보 조회
        
        Args:
            symbol: 거래쌍 (예: KRW-BTC)
            limit: 호가 개수 (사용되지 않음 - Upbit는 고정)
            
        Returns:
            OrderBook: 호가 정보
        """
        params = {'markets': symbol}
        data = await self.http_client.request('GET', '/v1/orderbook', params=params, auth_required=False)
        
        if not data:
            raise Exception(f"호가 정보를 찾을 수 없습니다: {symbol}")
        
        return self.data_mapper.parse_orderbook(data[0])
    
    async def get_symbols(self) -> List[str]:
        """
        전체 거래쌍 목록 조회
        
        Returns:
            List[str]: 거래쌍 목록
        """
        data = await self.http_client.request('GET', '/v1/market/all', auth_required=False)
        return [item['market'] for item in data]
    
    async def get_candles(self, symbol: str, interval: str = '1m', count: int = 100) -> List[dict]:
        """
        캔들 차트 데이터 조회
        
        Args:
            symbol: 거래쌍 (예: KRW-BTC)
            interval: 간격 (1m, 3m, 5m, 15m, 10m, 30m, 1h, 4h, 1d, 1w, 1M)
            count: 조회할 캔들 개수
            
        Returns:
            List[dict]: 캔들 데이터 목록
        """
        # Upbit 캔들 간격 매핑
        interval_map = {
            '1m': 'minutes/1',
            '3m': 'minutes/3',
            '5m': 'minutes/5',
            '15m': 'minutes/15',
            '10m': 'minutes/10',
            '30m': 'minutes/30',
            '1h': 'minutes/60',
            '4h': 'minutes/240',
            '1d': 'days',
            '1w': 'weeks',
            '1M': 'months'
        }
        
        upbit_interval = interval_map.get(interval, 'minutes/1')
        params = {
            'market': symbol,
            'count': count
        }
        
        endpoint = f'/v1/candles/{upbit_interval}'
        return await self.http_client.request('GET', endpoint, params=params, auth_required=False)
    
    async def get_recent_trades(self, symbol: str, count: int = 100) -> List[dict]:
        """
        최근 체결 내역 조회
        
        Args:
            symbol: 거래쌍 (예: KRW-BTC)
            count: 조회할 체결 내역 개수
            
        Returns:
            List[dict]: 체결 내역 목록
        """
        params = {
            'market': symbol,
            'count': count
        }
        
        return await self.http_client.request('GET', '/v1/trades/ticks', params=params, auth_required=False)
