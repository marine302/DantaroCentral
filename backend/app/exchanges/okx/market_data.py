"""
OKX 시장 데이터 모듈
단일 책임: 시세, 호가, 심볼 정보 조회
"""

from typing import Any, Dict, List

from ..base import Ticker, OrderBook
from .data_mapper import OKXDataMapper
from .http_client import OKXHttpClient


class OKXMarketData:
    """OKX 시장 데이터 관리"""
    
    def __init__(self, http_client: OKXHttpClient):
        self.http_client = http_client
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        현재가 조회
        
        Args:
            symbol: 거래쌍 심볼
            
        Returns:
            시세 정보
        """
        params = {'instId': symbol}
        data = await self.http_client.request('GET', '/api/v5/market/ticker', params)
        return OKXDataMapper.map_ticker(data, symbol)
    
    async def get_orderbook(self, symbol: str, limit: int = 10) -> OrderBook:
        """
        호가 조회
        
        Args:
            symbol: 거래쌍 심볼
            limit: 호가 수량
            
        Returns:
            호가 정보
        """
        params = {'instId': symbol, 'sz': str(limit)}
        data = await self.http_client.request('GET', '/api/v5/market/books', params)
        return OKXDataMapper.map_orderbook(data, symbol)
    
    async def get_symbols(self) -> List[str]:
        """
        거래 가능한 심볼 목록
        
        Returns:
            심볼 목록
        """
        data = await self.http_client.request('GET', '/api/v5/public/instruments', {'instType': 'SPOT'})
        return OKXDataMapper.map_symbols(data)
    
    async def get_trading_rules(self, symbol: str) -> Dict[str, Any]:
        """
        거래 규칙 조회 (최소 주문 금액, 수량 단위 등)
        
        Args:
            symbol: 거래쌍 심볼
            
        Returns:
            거래 규칙 정보
        """
        try:
            data = await self.http_client.request('GET', f'/api/v5/public/instruments?instType=SPOT&instId={symbol}')
            
            if data and len(data) > 0:
                instrument = data[0]
                return {
                    'symbol': symbol,
                    'min_order_value': float(instrument.get('minSz', '0')),  # 최소 주문 수량
                    'tick_size': float(instrument.get('tickSz', '0.000001')),  # 가격 단위
                    'lot_size': float(instrument.get('lotSz', '0.1')),  # 수량 단위
                    'base_currency': instrument.get('baseCcy', ''),
                    'quote_currency': instrument.get('quoteCcy', ''),
                    'status': instrument.get('state', ''),
                }
            else:
                return {}
                
        except Exception as e:
            print(f"거래 규칙 조회 오류 {symbol}: {e}")
            return {}
