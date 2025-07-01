"""
Market data API endpoints for the central server.

Provides endpoints for coin recommendations, support levels,
market status, and bundle requests for user servers.
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import time

from app.core.config import settings
from app.domain.recommenders.simple_recommender import CoinRecommender
from app.domain.calculators.support_calculator import SupportLevelCalculator
from app.schemas.market_data import (
    CoinRecommendationResponse,
    SupportLevelResponse,
    MarketStatusResponse,
    BundleRequest,
    BundleResponse
)
from app.services.market_data_service import MarketDataService
from app.services.real_market_service import RealMarketDataService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
market_data_service = MarketDataService()
real_market_service = RealMarketDataService()
cache_service = CacheService()
coin_recommender = CoinRecommender()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify API key for user server authentication."""
    if credentials.credentials != settings.user_server_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


@router.get(
    "/recommendations",
    response_model=CoinRecommendationResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Get coin recommendations",
    description="Get top coin recommendations based on technical analysis, volume, and volatility"
)
async def get_recommendations(
    top_n: int = Query(default=50, ge=1, le=100, description="Number of recommendations to return"),
    force_refresh: bool = Query(default=False, description="Force refresh of cached data"),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> CoinRecommendationResponse:
    """
    Get current coin recommendations.
    
    Returns a list of coins ranked by their analysis scores,
    including technical, volume, and volatility metrics.
    """
    try:
        # Check cache first (unless force refresh)
        cache_key = f"recommendations:{top_n}"
        
        if not force_refresh:
            cached_result = await cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached recommendations for top_{top_n}")
                # Ensure cache timestamp is set
                if 'cache_timestamp' not in cached_result or cached_result['cache_timestamp'] is None:
                    from datetime import datetime
                    generated_at = cached_result.get('generated_at')
                    if generated_at:
                        cached_result['cache_timestamp'] = datetime.fromtimestamp(generated_at)
                    else:
                        cached_result['cache_timestamp'] = datetime.utcnow()
                return CoinRecommendationResponse(**cached_result)
        
        # Get fresh real market data
        real_market_data = await real_market_service.get_market_data()
        
        if not real_market_data:
            logger.warning("Real market data unavailable, using fallback")
            # Fallback to mock data service if real data fails
            real_market_data = await market_data_service.get_all_market_data()
        
        if not real_market_data:
            raise HTTPException(
                status_code=503,
                detail="Market data temporarily unavailable"
            )
        
        # Get recommendations using real market data
        from app.domain.recommenders.advanced_recommender import CoinRecommender as AdvancedRecommender
        advanced_recommender = AdvancedRecommender()
        
        recommendations = await advanced_recommender.get_recommendations(
            coin_data=real_market_data, 
            limit=top_n
        )
        
        # Convert recommendations to proper format
        recommendation_objects = []
        for rec in recommendations:
            from app.schemas.market_data import CoinRecommendation
            rec_dict = {
                'symbol': rec.symbol,
                'total_score': rec.overall_score / 100.0,  # Convert to 0-1 range
                'recommendation_strength': rec.strength.value,
                'component_scores': {
                    'technical': rec.technical_score / 100.0,
                    'volume': rec.volume_score / 100.0,
                    'volatility': rec.volatility_score / 100.0,
                    'risk': rec.risk_score / 100.0
                },
                'metadata': {
                    'current_price': rec.current_price,
                    'price_change_24h': rec.price_change_24h,
                    'volume_24h': rec.volume_24h,
                    'market_cap': rec.market_cap,
                    'analysis_details': rec.analysis_details
                }
            }
            recommendation_objects.append(CoinRecommendation(**rec_dict))
        
        from datetime import datetime
        
        response = CoinRecommendationResponse(
            recommendations=recommendation_objects,
            total_analyzed=len(real_market_data),
            cache_timestamp=datetime.utcnow(),  # Current timestamp for fresh data
            metadata={
                "analysis_methods": ["technical", "volume", "volatility"],
                "top_n": top_n,
                "force_refresh": force_refresh,
                "generated_at": time.time()
            }
        )
        
        # Cache the result for future requests
        cache_data = response.dict()
        cache_data['generated_at'] = time.time()
        await cache_service.set(
            cache_key, 
            cache_data, 
            ttl=300  # 5 minutes
        )
        
        # Cache the result
        background_tasks.add_task(
            cache_service.set,
            cache_key,
            response.model_dump(),
            ttl=settings.strategy_cache_ttl
        )
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating recommendations"
        )


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
        symbol_data = await real_market_service.get_symbol_data(symbol_with_pair)
        
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


@router.get(
    "/market-status",
    response_model=MarketStatusResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Get overall market status",
    description="Get general market indicators and system health status"
)
async def get_market_status() -> MarketStatusResponse:
    """
    Get current market status and system health.
    
    Returns information about:
    - Market sentiment
    - Data freshness
    - System performance
    - Available symbols
    """
    try:
        # Get real market data status
        real_market_data = await real_market_service.get_market_data()
        
        # Calculate real market indicators
        total_symbols = len(real_market_data)
        
        # Calculate basic market metrics from real data
        total_volume_24h = 0
        price_changes = []
        
        for symbol_data in real_market_data.values():
            total_volume_24h += symbol_data.get('volume_24h', 0)
            price_change = symbol_data.get('price_change_24h', 0)
            if price_change is not None:
                price_changes.append(price_change)
        
        # Calculate market sentiment based on price changes
        positive_changes = len([p for p in price_changes if p > 0])
        negative_changes = len([p for p in price_changes if p < 0])
        
        if positive_changes > negative_changes:
            sentiment = "bullish"
        elif negative_changes > positive_changes:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        # Calculate average volatility
        avg_volatility = sum(abs(p) for p in price_changes) / len(price_changes) if price_changes else 0
        
        from app.schemas.market_data import SystemHealth
        system_health = SystemHealth(
            database='healthy',  # Assume healthy for now
            cache='healthy',
            exchanges={
                'upbit': 'healthy' if real_market_data else 'degraded',
                'binance': 'unavailable',
                'bithumb': 'unavailable'
            },
            analysis_engine='healthy'
        )
        
        return MarketStatusResponse(
            status='healthy' if real_market_data else 'degraded',
            total_symbols=total_symbols,
            last_update=None,  # Could add timestamp from real service
            system_health=system_health,
            market_indicators={
                'market_sentiment': sentiment,
                'total_volume_24h_krw': total_volume_24h,
                'average_volatility': avg_volatility,
                'positive_movers': positive_changes,
                'negative_movers': negative_changes,
                'active_symbols': total_symbols
            },
            metadata={
                'data_source': 'upbit_real_time',
                'update_frequency': '1_minute',
                'coverage': 'korean_markets'
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get market status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting market status"
        )


@router.post(
    "/bundle",
    response_model=BundleResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Bundle multiple requests",
    description="Execute multiple API requests in a single call for efficiency"
)
async def bundle_requests(
    bundle_request: BundleRequest,
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> BundleResponse:
    """
    Execute multiple API requests in a single call.
    
    This endpoint allows user servers to efficiently fetch
    multiple pieces of data with a single HTTP request.
    """
    try:
        results = {}
        errors = {}
        
        # Process recommendations request
        if bundle_request.include_recommendations:
            try:
                rec_params = bundle_request.recommendations_params
                top_n = rec_params.top_n if rec_params else 50
                force_refresh = rec_params.force_refresh if rec_params else False
                
                recommendations_response = await get_recommendations(
                    top_n=top_n,
                    force_refresh=force_refresh,
                    background_tasks=background_tasks
                )
                results['recommendations'] = recommendations_response.model_dump()
                
            except Exception as e:
                logger.error(f"Bundle recommendations error: {e}")
                errors['recommendations'] = str(e)
        
        # Process support levels requests
        if bundle_request.support_level_symbols:
            results['support_levels'] = {}
            errors_support = {}
            
            for symbol in bundle_request.support_level_symbols:
                try:
                    support_params = bundle_request.support_level_params
                    force_refresh = support_params.force_refresh if support_params else False
                    
                    support_response = await get_support_levels(
                        symbol=symbol,
                        force_refresh=force_refresh,
                        background_tasks=background_tasks
                    )
                    results['support_levels'][symbol] = support_response.model_dump()
                    
                except Exception as e:
                    logger.error(f"Bundle support levels error for {symbol}: {e}")
                    errors_support[symbol] = str(e)
                    
            if errors_support:
                errors['support_levels'] = errors_support
        
        # Process market status request
        if bundle_request.include_market_status:
            try:
                market_status_response = await get_market_status()
                results['market_status'] = market_status_response.model_dump()
                
            except Exception as e:
                logger.error(f"Bundle market status error: {e}")
                errors['market_status'] = str(e)
        
        # Check if we have any results
        if not results:
            raise HTTPException(
                status_code=400,
                detail="No valid requests in bundle or all requests failed"
            )
        
        return BundleResponse(
            results=results,
            errors=errors if errors else None,
            metadata={
                'total_requests': (
                    (1 if bundle_request.include_recommendations else 0) +
                    (len(bundle_request.support_level_symbols) if bundle_request.support_level_symbols else 0) +
                    (1 if bundle_request.include_market_status else 0)
                ),
                'successful_requests': len(results),
                'failed_requests': len(errors) if errors else 0
            }
        )
        
    except Exception as e:
        logger.error(f"Bundle request failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing bundle request"
        )
