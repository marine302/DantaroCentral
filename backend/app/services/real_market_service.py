"""
Real market data service using CCXT for multiple exchanges.
"""
import ccxt
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class RealMarketDataService:
    """Real market data service using CCXT."""
    
    def __init__(self):
        # Initialize exchanges
        self.exchanges = {
            'upbit': ccxt.upbit(),
            'bithumb': ccxt.bithumb(), 
            'coinone': ccxt.coinone()
        }
        
        self.cache = {}
        self.cache_ttl = 60  # 1 minute cache
        
    async def get_market_data(self) -> Dict[str, Dict]:
        """Get real market data from Korean exchanges."""
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.info("Using cached market data")
                return self.cache.get('data', {})
            
            logger.info("Fetching fresh market data...")
            
            # Get data from Upbit (most reliable Korean exchange)
            upbit_data = await self._fetch_upbit_data()
            
            # Cache the data
            self.cache = {
                'data': upbit_data,
                'timestamp': time.time()
            }
            
            logger.info(f"Fetched data for {len(upbit_data)} symbols")
            return upbit_data
            
        except Exception as e:
            logger.error(f"Failed to fetch real market data: {e}")
            # Fallback to empty data rather than mock
            return {}
    
    async def _fetch_upbit_data(self) -> Dict[str, Dict]:
        """Fetch data from Upbit exchange."""
        try:
            upbit = self.exchanges['upbit']
            
            # Get all KRW markets
            markets = upbit.load_markets()
            krw_symbols = [symbol for symbol in markets.keys() if '/KRW' in symbol]
            
            # Limit to top coins to avoid rate limits
            top_symbols = krw_symbols[:50]
            
            market_data = {}
            
            for symbol in top_symbols:
                try:
                    # Get ticker data
                    ticker = upbit.fetch_ticker(symbol)
                    
                    # Get OHLCV data for technical analysis
                    ohlcv = upbit.fetch_ohlcv(symbol, '1d', limit=30)
                    
                    # Format data
                    prices = [float(candle[4]) for candle in ohlcv]  # closing prices
                    volumes = [float(candle[5]) for candle in ohlcv]  # volumes
                    
                    market_data[symbol] = {
                        'current_price': float(ticker['last']),
                        'price_change_24h': float(ticker['percentage'] or 0),
                        'volume_24h': float(ticker['quoteVolume'] or 0),
                        'market_cap': None,  # Upbit doesn't provide market cap
                        'prices': prices,
                        'volumes': volumes,
                        'high_24h': float(ticker['high']),
                        'low_24h': float(ticker['low']),
                        'timestamp': ticker['timestamp']
                    }
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol}: {e}")
                    continue
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to fetch Upbit data: {e}")
            raise
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.cache:
            return False
        
        cache_age = time.time() - self.cache.get('timestamp', 0)
        return cache_age < self.cache_ttl
    
    async def get_symbol_data(self, symbol: str) -> Optional[Dict]:
        """Get data for a specific symbol."""
        all_data = await self.get_market_data()
        return all_data.get(symbol)
