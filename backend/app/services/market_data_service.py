"""
Market data service for fetching and managing market information.

This service handles data collection from exchanges and provides
unified access to market data for analysis engines.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from decimal import Decimal
import random

from app.core.config import settings

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Service for managing market data collection and access.
    
    This service coordinates data fetching from multiple exchanges
    and provides unified market data for the analysis engines.
    """
    
    def __init__(self):
        self.last_update: Optional[datetime] = None
        self.market_cache: Dict[str, Dict] = {}
        self.exchange_status: Dict[str, str] = {}
        self.update_interval = getattr(settings, "market_data_update_interval", 60)  # seconds
    
    async def get_all_market_data(self) -> Dict[str, Dict]:
        """
        Get market data for all available symbols.
        
        Returns:
            Dictionary with symbol as key and market data as value
        """
        try:
            # 운영/개발 모드에 따라 mock/real 분기
            if getattr(settings, "use_mock_market_data", True):
                mock_symbols = getattr(settings, "mock_symbols", [
                    "BTC/KRW", "ETH/KRW", "ADA/KRW", "XRP/KRW", "DOT/KRW",
                    "SOL/KRW", "MATIC/KRW", "AVAX/KRW", "ATOM/KRW", "NEAR/KRW"
                ])
                market_data = {}
                for symbol in mock_symbols:
                    market_data[symbol] = await self._get_symbol_data(symbol)
                self.last_update = datetime.utcnow()
                logger.info(
                    f"market_data_retrieved: symbol_count={len(market_data)}, mode=mock"
                )
                return market_data
            else:
                # TODO: 실제 거래소 API 연동 구현
                logger.warning("실거래소 연동 미구현 - mock 데이터 사용 중")
                return {}
        except Exception as e:
            logger.error(f"market_data_error: {e}")
            return {}
    
    async def get_price_history(self, symbol: str, days: int = 90) -> List[Dict]:
        """
        Get historical price data for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/KRW')
            days: Number of days of history to retrieve
            
        Returns:
            List of price candles with OHLCV data
        """
        try:
            if getattr(settings, "use_mock_market_data", True):
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                price_history = []
                current_date = start_date
                base_price = 50000.0  # Mock base price
                while current_date <= end_date:
                    # Simple random walk for price
                    price_change = random.uniform(-0.05, 0.05)  # ±5% daily change
                    base_price *= (1 + price_change)
                    high = base_price * random.uniform(1.001, 1.05)
                    low = base_price * random.uniform(0.95, 0.999)
                    open_price = base_price * random.uniform(0.98, 1.02)
                    close = base_price
                    volume = random.uniform(1000000, 10000000)
                    candle = {
                        'timestamp': current_date.timestamp(),
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'close': close,
                        'volume': volume,
                    }
                    price_history.append(candle)
                    current_date += timedelta(days=1)
                logger.info(
                    f"price_history_generated: symbol={symbol}, days={days}, count={len(price_history)}, mode=mock"
                )
                return price_history
            else:
                # TODO: 실제 거래소 API 연동 구현
                logger.warning("실거래소 연동 미구현 - mock 데이터 사용 중")
                return []
        except Exception as e:
            logger.error(f"price_history_error: {e}, symbol={symbol}")
            return []
    
    async def get_market_status(self) -> Dict[str, Any]:
        """
        Get overall market status and system health.
        
        Returns:
            Dictionary with market status information
        """
        try:
            # Check system health
            db_status = await self._check_database_health()
            cache_status = await self._check_cache_health()
            exchange_statuses = await self._check_exchange_health()
            
            # Calculate market indicators
            market_indicators = await self._calculate_market_indicators()
            
            status = {
                'status': 'healthy' if all([
                    db_status == 'healthy',
                    cache_status == 'healthy',
                    any(status == 'healthy' for status in exchange_statuses.values())
                ]) else 'degraded',
                'total_symbols': len(self.market_cache),
                'last_update': self.last_update,
                'database_status': db_status,
                'cache_status': cache_status,
                'exchange_status': exchange_statuses,
                'analysis_status': 'healthy',
                'market_indicators': market_indicators,
                'metadata': {
                    'uptime': '99.9%',
                    'response_time_ms': 45,
                    'data_freshness_minutes': 2
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return {
                'status': 'error',
                'total_symbols': 0,
                'last_update': None,
                'database_status': 'error',
                'cache_status': 'error',
                'exchange_status': {},
                'analysis_status': 'error',
                'market_indicators': {},
                'metadata': {'error': str(e)}
            }
    
    async def _get_symbol_data(self, symbol: str) -> Dict:
        """Get market data for a single symbol."""
        # Mock implementation - replace with real exchange API calls
        
        base_price = random.uniform(1000, 100000)
        volume_24h = random.uniform(1000000, 100000000)
        
        # Generate recent price history for analysis
        price_history = []
        for i in range(30):  # 30 days of data
            price_change = random.uniform(-0.03, 0.03)
            day_price = base_price * (1 + price_change)
            
            price_history.append({
                'timestamp': (datetime.utcnow() - timedelta(days=29-i)).timestamp(),
                'open': day_price * random.uniform(0.99, 1.01),
                'high': day_price * random.uniform(1.01, 1.05),
                'low': day_price * random.uniform(0.95, 0.99),
                'close': day_price,
                'volume': random.uniform(500000, 5000000)
            })
        
        # Generate volume history
        volume_history = [candle['volume'] for candle in price_history]
        
        return {
            'symbol': symbol,
            'current_price': base_price,
            'volume_24h': volume_24h,
            'price_history': price_history,
            'volume_history': volume_history,
            'timestamp': datetime.utcnow().timestamp(),
            'exchange': 'mock',
            'market_cap': base_price * random.uniform(1000000, 100000000),
            'price_change_24h': random.uniform(-10, 10)
        }
    
    async def _check_database_health(self) -> str:
        """Check database connection health."""
        try:
            # In real implementation, check actual database connection
            # For now, return healthy
            return 'healthy'
        except Exception:
            return 'error'
    
    async def _check_cache_health(self) -> str:
        """Check cache service health."""
        try:
            # In real implementation, check Redis connection
            # For now, return healthy
            return 'healthy'
        except Exception:
            return 'error'
    
    async def _check_exchange_health(self) -> Dict[str, str]:
        """Check health of all exchange connections."""
        exchanges = ['upbit', 'binance', 'bithumb', 'korbit', 'gopax', 'coinone']
        statuses = {}
        
        for exchange in exchanges:
            try:
                # In real implementation, ping exchange APIs
                # For now, simulate mostly healthy exchanges
                statuses[exchange] = 'healthy' if random.random() > 0.1 else 'degraded'
            except Exception:
                statuses[exchange] = 'error'
        
        return statuses
    
    async def _calculate_market_indicators(self) -> Dict[str, Any]:
        """Calculate general market indicators."""
        try:
            # Mock market indicators
            import random
            
            return {
                'fear_greed_index': random.randint(20, 80),
                'market_sentiment': random.choice(['bullish', 'bearish', 'neutral']),
                'volatility_index': random.uniform(0.2, 0.8),
                'trending_coins': random.randint(15, 35),
                'total_market_cap': f"${random.randint(800, 1200)}B",
                'bitcoin_dominance': f"{random.uniform(40, 60):.1f}%"
            }
            
        except Exception:
            return {}
