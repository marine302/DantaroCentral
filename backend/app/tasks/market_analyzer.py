"""
Background task for continuous market analysis.

This module implements scheduled tasks for:
- Fetching latest market data from exchanges
- Updating support levels and recommendations
- Cleaning old data and maintaining cache

Runs every 5 minutes as configured in settings.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.config import settings
from app.services.market_data_service import MarketDataService
from app.services.real_market_service import RealMarketDataService
from app.services.cache_service import CacheService
from app.domain.recommenders.advanced_recommender import CoinRecommender
from app.domain.calculators.support_calculator import SupportLevelCalculator

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Background task manager for continuous market analysis.
    
    This class handles periodic market data updates and analysis
    to keep the central server's recommendations fresh.
    """
    
    def __init__(self):
        self.market_service = MarketDataService()
        self.real_market_service = RealMarketDataService()
        self.cache_service = CacheService()
        self.coin_recommender = CoinRecommender()
        self.last_analysis: Dict[str, datetime] = {}
        self.is_running = False
    
    async def start_continuous_analysis(self):
        """Start the continuous analysis loop."""
        if self.is_running:
            logger.warning("Market analyzer already running")
            return
        
        self.is_running = True
        logger.info("Starting continuous market analysis")
        
        try:
            # Run first analysis cycle immediately
            logger.info("About to run first analysis cycle")
            await self.run_analysis_cycle()
            logger.info("First analysis cycle completed, starting periodic loop")
            
            while self.is_running:
                await asyncio.sleep(settings.market_analysis_interval)
                logger.info("Running scheduled analysis cycle")
                await self.run_analysis_cycle()
        except Exception as e:
            logger.error(f"Market analysis loop failed: {e}", exc_info=True)
            self.is_running = False
    
    async def stop_analysis(self):
        """Stop the continuous analysis loop."""
        logger.info("Stopping market analysis")
        self.is_running = False
    
    async def run_analysis_cycle(self):
        """Run a single analysis cycle."""
        try:
            cycle_start = datetime.utcnow()
            logger.info("Starting market analysis cycle")
            
            # Step 1: Fetch latest market data
            logger.info("Step 1: Fetching market data")
            market_data = await self._fetch_market_data()
            
            if not market_data:
                logger.warning("No market data available for analysis")
                return
            
            # Step 2: Update recommendations
            logger.info("Step 2: Updating recommendations")
            await self._update_recommendations(market_data)
            
            # Step 3: Update support levels for top coins
            logger.info("Step 3: Updating support levels")
            await self._update_support_levels(market_data)
            
            # Step 4: Clean old cache entries
            logger.info("Step 4: Cleaning cache")
            await self._cleanup_cache()
            
            # Step 5: Log analysis completion
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
            logger.info(f"Analysis cycle completed in {cycle_duration:.2f}s")
            
            # Update last analysis timestamp
            self.last_analysis['full_cycle'] = cycle_start
            
        except Exception as e:
            logger.error(f"Analysis cycle failed: {e}", exc_info=True)
    
    async def _fetch_market_data(self) -> Dict[str, Dict]:
        """Fetch latest market data from all sources."""
        try:
            logger.debug("Fetching market data from exchanges")
            
            # Get real market data first
            market_data = await self.real_market_service.get_market_data()
            
            # Fallback to mock data if real data fails
            if not market_data:
                logger.warning("Real market data unavailable, using fallback service")
                market_data = await self.market_service.get_all_market_data()
            
            if market_data:
                logger.info(f"Fetched data for {len(market_data)} symbols")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return {}
    
    async def _update_recommendations(self, market_data: Dict[str, Dict]):
        """Update coin recommendations based on fresh market data."""
        try:
            logger.debug("Updating coin recommendations")
            
            # Generate new recommendations
            recommendations = await self.coin_recommender.get_recommendations(
                market_data, 
                settings.top_recommendations_count
            )
            
            if recommendations:
                # Cache the new recommendations
                cache_key = f"recommendations:{settings.top_recommendations_count}"
                
                response_data = {
                    'recommendations': recommendations,
                    'total_analyzed': len(market_data),
                    'cache_timestamp': datetime.utcnow().isoformat(),
                    'metadata': {
                        'analysis_methods': ['technical', 'volume', 'volatility'],
                        'top_n': settings.top_recommendations_count,
                        'auto_generated': True
                    }
                }
                
                await self.cache_service.set(
                    cache_key,
                    response_data,
                    ttl=settings.strategy_cache_ttl
                )
                
                logger.info(f"Updated recommendations for {len(recommendations)} coins")
            
        except Exception as e:
            logger.error(f"Failed to update recommendations: {e}")
    
    async def _update_support_levels(self, market_data: Dict[str, Dict]):
        """Update support levels for top performing coins."""
        try:
            logger.debug("Updating support levels")
            
            # Get top coins (first 20 from recommendations)
            top_symbols = list(market_data.keys())[:20]
            
            updated_count = 0
            
            for symbol in top_symbols:
                try:
                    # Get price history
                    price_history = await self.market_service.get_price_history(
                        symbol, 
                        settings.support_level_lookback_days
                    )
                    
                    if not price_history:
                        continue
                    
                    # Calculate support levels
                    support_levels = SupportLevelCalculator.calculate_support_levels(price_history)
                    
                    if support_levels:
                        # Format and cache the results
                        response_data = {
                            'symbol': symbol,
                            'support_levels': {},
                            'calculation_timestamp': datetime.utcnow().isoformat(),
                            'metadata': {
                                'price_data_points': len(price_history),
                                'lookback_days': settings.support_level_lookback_days,
                                'auto_generated': True
                            }
                        }
                        
                        # Convert support levels to response format
                        for level_type, level_data in support_levels.items():
                            response_data['support_levels'][level_type] = {
                                'price': float(level_data.price),
                                'confidence': level_data.confidence,
                                'calculation_method': level_data.calculation_method,
                                'lookback_days': level_data.lookback_days,
                                'metadata': level_data.metadata
                            }
                        
                        # Cache the support levels
                        cache_key = f"support_levels:{symbol}"
                        await self.cache_service.set(
                            cache_key,
                            response_data,
                            ttl=settings.strategy_cache_ttl
                        )
                        
                        updated_count += 1
                
                except Exception as e:
                    logger.warning(f"Failed to update support levels for {symbol}: {e}")
                    continue
            
            logger.info(f"Updated support levels for {updated_count} symbols")
            
        except Exception as e:
            logger.error(f"Failed to update support levels: {e}")
    
    async def _cleanup_cache(self):
        """Clean up old cache entries and expired data."""
        try:
            logger.debug("Cleaning up cache")
            
            # Get cache statistics
            stats = await self.cache_service.get_stats()
            
            if stats.get('expired_keys', 0) > 0:
                logger.info(f"Cache cleanup: {stats['expired_keys']} expired entries found")
            
            # Note: The cache service automatically removes expired entries
            # when they are accessed, so no manual cleanup is needed for the
            # in-memory implementation. In a Redis implementation, you would
            # run SCAN and DELETE commands here.
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")


# Global market analyzer instance
market_analyzer = MarketAnalyzer()


async def start_background_tasks():
    """Start all background tasks."""
    logger.info("Starting background tasks")
    
    # Start market analysis in background
    task = asyncio.create_task(market_analyzer.start_continuous_analysis())
    
    return task


async def stop_background_tasks():
    """Stop all background tasks."""
    logger.info("Stopping background tasks")
    await market_analyzer.stop_analysis()
