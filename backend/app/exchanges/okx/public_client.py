"""
OKX 퍼블릭 API 클라이언트 (인증 불필요)
"""
import aiohttp
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..base import BaseExchange, Ticker


class OKXPublicClient:
    """OKX 퍼블릭 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://www.okx.com"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_symbols(self) -> List[str]:
        """거래 가능한 심볼 목록 조회"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/v5/public/instruments?instType=SPOT") as response:
                data = await response.json()
                
                if data.get('code') != '0':
                    return []
                
                symbols = []
                for instrument in data.get('data', []):
                    symbols.append(instrument['instId'])
                
                return symbols
                
        except Exception as e:
            print(f"OKX get_symbols 오류: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """개별 심볼의 티커 정보 조회"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/v5/market/ticker?instId={symbol}") as response:
                data = await response.json()
                
                if data.get('code') != '0' or not data.get('data'):
                    raise Exception(f"OKX API 오류: {data.get('msg', 'Unknown error')}")
                
                ticker_data = data['data'][0]
                
                return Ticker(
                    symbol=ticker_data['instId'],
                    price=Decimal(ticker_data['last']),
                    bid=Decimal(ticker_data['bidPx'] or '0'),
                    ask=Decimal(ticker_data['askPx'] or '0'),
                    volume=Decimal(ticker_data['vol24h'] or '0'),
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            raise Exception(f"OKX get_ticker 오류 ({symbol}): {e}")
    
    async def get_all_tickers(self) -> List[Ticker]:
        """모든 심볼의 티커 정보 조회"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/v5/market/tickers?instType=SPOT") as response:
                data = await response.json()
                
                if data.get('code') != '0':
                    return []
                
                tickers = []
                for ticker_data in data.get('data', []):
                    try:
                        ticker = Ticker(
                            symbol=ticker_data['instId'],
                            price=Decimal(ticker_data['last']),
                            bid=Decimal(ticker_data['bidPx'] or '0'),
                            ask=Decimal(ticker_data['askPx'] or '0'),
                            volume=Decimal(ticker_data['vol24h'] or '0'),
                            timestamp=datetime.now()
                        )
                        tickers.append(ticker)
                    except Exception as e:
                        continue
                
                return tickers
                
        except Exception as e:
            print(f"OKX get_all_tickers 오류: {e}")
            return []
