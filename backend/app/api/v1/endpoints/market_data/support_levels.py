"""
Support levels API endpoints for the central server.

Provides endpoints for calculating support and resistance levels
for specific coins based on historical price data.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings
from app.domain.calculators.support_calculator import SupportLevelCalculator
from app.schemas.market_data import SupportLevelResponse
from app.services.market_data_collector import MarketDataCollector
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
market_data_collector = MarketDataCollector()
cache_service = CacheService()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify API key for user server authentication."""
    if credentials.credentials != settings.user_server_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


@router.get(
    "/support-levels/{symbol}",
    response_model=SupportLevelResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Get support levels for a specific coin",
    description="Calculate aggressive, moderate, and conservative support levels for trading"
)
async def get_support_levels(
    symbol: str,
    force_refresh: bool = Query(default=False, description="Force refresh of cached data"),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> SupportLevelResponse:
    """
    Get support levels for a specific coin.
    
    Returns three types of support levels:
    - Aggressive: 7-day lookback for short-term support
    - Moderate: 30-day lookback for medium-term support
    - Conservative: 90-day lookback for long-term support
    """
    try:
        # Validate symbol format
        symbol = symbol.upper()
        
        # Check cache first
        cache_key = f"support_levels:{symbol}"
        
        if not force_refresh:
            cached_result = await cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached support levels for {symbol}")
                return SupportLevelResponse(**cached_result)
        
        # Get real price history for the symbol
        # Convert symbol format if needed (e.g., BTC -> BTC/KRW)
        if '/' not in symbol:
            symbol_with_pair = f"{symbol}/KRW"
        else:
            symbol_with_pair = symbol
            
        # Get real market data for this symbol
        # 시장 데이터 가져오기 (임시로 빈 데이터 반환)
        symbol_data = {}
        
        if not symbol_data:
            raise HTTPException(
                status_code=404,
                detail=f"Price history not found for symbol: {symbol}"
            )
        
        # Format price history for calculator
        prices = symbol_data.get('prices', [])
        volumes = symbol_data.get('volumes', [])
        
        if not prices:
            raise HTTPException(
                status_code=404,
                detail=f"No price data available for symbol: {symbol}"
            )
        
        # Create price history in the format expected by calculator
        price_history = []
        for i, price in enumerate(prices):
            if i < len(volumes):
                price_history.append({
                    'timestamp': i,  # Use index as timestamp for simplicity
                    'open': price,
                    'high': price * 1.02,  # Approximate high
                    'low': price * 0.98,   # Approximate low
                    'close': price,
                    'volume': volumes[i]
                })
        
        # Calculate support levels
        support_levels = SupportLevelCalculator.calculate_support_levels(price_history)
        
        if not support_levels:
            raise HTTPException(
                status_code=422,
                detail=f"Unable to calculate support levels for symbol: {symbol}"
            )
        
        # Format response
        response_data = {
            'symbol': symbol,
            'support_levels': {},
            'calculation_timestamp': None,
            'metadata': {
                'price_data_points': len(price_history),
                'lookback_days': settings.support_level_lookback_days
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
        
        response = SupportLevelResponse(**response_data)
        
        # Cache the result
        background_tasks.add_task(
            cache_service.set,
            cache_key,
            response.model_dump(),
            ttl=settings.strategy_cache_ttl
        )
        
        logger.info(f"Calculated support levels for {symbol}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get support levels for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while calculating support levels for {symbol}"
        )
