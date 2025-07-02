"""
Lightweight market data API endpoints for the central server.
Serves cached/database results only - no heavy analysis.
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from datetime import datetime

from app.core.config import settings
from app.database.manager import db_manager
from app.database.redis_cache import redis_manager
from app.monitoring.health import health_monitor
from app.schemas.market_data_light import (
    CoinRecommendationResponse,
    SupportLevelResponse,
    MarketStatusResponse,
    BundleRequest,
    BundleResponse,
    LightCoinRecommendation,
    LightSupportLevel,
    LightMarketStatus
)

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


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
    description="Get top coin recommendations from pre-analyzed database/cache"
)
async def get_recommendations(
    top_n: int = Query(default=50, ge=1, le=100, description="Number of recommendations to return"),
    use_cache: bool = Query(default=True, description="Try cache first before database")
) -> CoinRecommendationResponse:
    """
    Get current coin recommendations from cache or database.
    
    This endpoint is read-only and serves pre-computed analysis results.
    Analysis is performed by the background worker.
    """
    try:
        recommendations = []
        data_source = "cache"
        
        # Try cache first if requested
        if use_cache:
            cached_recommendations = redis_manager.get_recommendations()
            if cached_recommendations:
                recommendations = cached_recommendations[:top_n]
                logger.info(f"Served {len(recommendations)} recommendations from cache")
            else:
                logger.info("No cached recommendations found")
        
        # Fallback to database if cache miss or cache disabled
        if not recommendations:
            recommendations = db_manager.get_latest_recommendations(limit=top_n)
            data_source = "database"
            logger.info(f"Served {len(recommendations)} recommendations from database")
        
        if not recommendations:
            # Return empty result with metadata
            return CoinRecommendationResponse(
                success=True,
                recommendations=[],
                total_analyzed=0,
                cache_timestamp=datetime.utcnow(),
                generated_at=datetime.utcnow().timestamp(),
                data_source=data_source,
                message="No recommendations available. Worker may be initializing."
            )
        
        # Convert recommendations to schema format
        formatted_recommendations = []
        for rec in recommendations:
            formatted_rec = LightCoinRecommendation(**rec)
            formatted_recommendations.append(formatted_rec)
        
        # Format response
        return CoinRecommendationResponse(
            success=True,
            recommendations=formatted_recommendations,
            total_analyzed=len(recommendations),
            cache_timestamp=datetime.utcnow(),
            generated_at=datetime.utcnow().timestamp(),
            data_source=data_source
        )
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get(
    "/support-levels/{symbol}",
    response_model=SupportLevelResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Get support and resistance levels",
    description="Get support and resistance levels for a specific symbol from pre-analyzed data"
)
async def get_support_levels(
    symbol: str,
    use_cache: bool = Query(default=True, description="Try cache first before database")
) -> SupportLevelResponse:
    """
    Get support and resistance levels for a symbol from cache or database.
    
    This endpoint serves pre-computed support/resistance analysis.
    """
    try:
        symbol = symbol.upper()
        support_data = None
        data_source = "cache"
        
        # Try cache first if requested
        if use_cache:
            support_data = redis_manager.get_support_levels(symbol)
            if support_data:
                logger.info(f"Served support levels for {symbol} from cache")
            else:
                logger.info(f"No cached support levels found for {symbol}")
        
        # Fallback to database if cache miss or cache disabled
        if not support_data:
            support_data = db_manager.get_support_levels(symbol)
            data_source = "database"
            if support_data:
                logger.info(f"Served support levels for {symbol} from database")
        
        if not support_data:
            raise HTTPException(
                status_code=404,
                detail=f"Support levels not available for {symbol}. Worker may not have analyzed this symbol yet."
            )
        
        # Ensure symbol is included in the data
        support_data['symbol'] = symbol
        
        # Convert support data to schema format
        formatted_support = LightSupportLevel(**support_data)
        
        # Format response
        return SupportLevelResponse(
            success=True,
            symbol=symbol,
            support_levels=formatted_support,
            cache_timestamp=datetime.utcnow(),
            data_source=data_source
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting support levels for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get support levels: {str(e)}"
        )


@router.get(
    "/market-status",
    response_model=MarketStatusResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Get market status",
    description="Get overall market status and trends from pre-analyzed data"
)
async def get_market_status(
    use_cache: bool = Query(default=True, description="Try cache first before database")
) -> MarketStatusResponse:
    """
    Get current market status from cache or database.
    
    This endpoint serves pre-computed market analysis.
    """
    try:
        market_data = None
        data_source = "cache"
        
        # Try cache first if requested
        if use_cache:
            market_data = redis_manager.get_market_status()
            if market_data:
                logger.info("Served market status from cache")
            else:
                logger.info("No cached market status found")
        
        # Fallback to database if cache miss or cache disabled
        if not market_data:
            market_data = db_manager.get_market_status()
            data_source = "database"
            if market_data:
                logger.info("Served market status from database")
        
        if not market_data:
            # Return default status if no data available
            default_market = LightMarketStatus(
                market_trend='unknown',
                market_sentiment='neutral',
                overall_score=0.5,
                active_coins_count=0,
                analysis_summary={'message': 'Market analysis unavailable. Worker may be initializing.'}
            )
            return MarketStatusResponse(
                success=True,
                status="degraded",
                total_symbols=0,
                system_health={"worker": "initializing"},
                market_status=default_market,
                cache_timestamp=datetime.utcnow(),
                data_source="default"
            )
        
        # Convert market data to schema format
        formatted_market = LightMarketStatus(**market_data)
        
        # Format response
        return MarketStatusResponse(
            success=True,
            status="healthy",
            total_symbols=market_data.get('active_coins_count', 0),
            system_health={"worker": "active", "data": "fresh"},
            market_status=formatted_market,
            cache_timestamp=datetime.utcnow(),
            data_source=data_source
        )
        
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get market status: {str(e)}"
        )


@router.post(
    "/bundle",
    response_model=BundleResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Get bundled market data",
    description="Get multiple market data types in a single request"
)
async def get_bundle(
    request: BundleRequest,
    use_cache: bool = Query(default=True, description="Try cache first before database")
) -> BundleResponse:
    """
    Get multiple market data types in a single request.
    
    This optimizes network calls for user servers that need multiple data types.
    All data comes from pre-computed cache/database.
    """
    try:
        bundle_data = {}
        
        # Get recommendations if requested
        if request.include_recommendations:
            try:
                recommendations = []
                if use_cache:
                    recommendations = redis_manager.get_recommendations()
                if not recommendations:
                    recommendations = db_manager.get_latest_recommendations(limit=request.recommendations_count)
                
                bundle_data['recommendations'] = recommendations[:request.recommendations_count] if recommendations else []
            except Exception as e:
                logger.error(f"Error getting recommendations for bundle: {e}")
                bundle_data['recommendations'] = []
        
        # Get support levels if requested
        if request.include_support_levels and request.symbols:
            bundle_data['support_levels'] = {}
            for symbol in request.symbols:
                try:
                    support_data = None
                    if use_cache:
                        support_data = redis_manager.get_support_levels(symbol.upper())
                    if not support_data:
                        support_data = db_manager.get_support_levels(symbol.upper())
                    
                    if support_data:
                        bundle_data['support_levels'][symbol.upper()] = support_data
                except Exception as e:
                    logger.error(f"Error getting support levels for {symbol}: {e}")
        
        # Get market status if requested
        if request.include_market_status:
            try:
                market_data = None
                if use_cache:
                    market_data = redis_manager.get_market_status()
                if not market_data:
                    market_data = db_manager.get_market_status()
                
                bundle_data['market_status'] = market_data
            except Exception as e:
                logger.error(f"Error getting market status for bundle: {e}")
                bundle_data['market_status'] = None
        
        return BundleResponse(
            success=True,
            data=bundle_data,
            cache_timestamp=datetime.utcnow(),
            data_source="cache+database" if use_cache else "database"
        )
        
    except Exception as e:
        logger.error(f"Error creating bundle response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create bundle: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check API server health and data freshness"
)
async def health_check():
    """
    Health check endpoint that also reports data freshness.
    """
    try:
        # Check database connection
        try:
            recommendations = db_manager.get_latest_recommendations(limit=1)
            db_status = "healthy"
            db_recommendations_count = len(recommendations)
        except Exception as e:
            db_status = f"error: {str(e)}"
            db_recommendations_count = 0
        
        # Check Redis connection
        try:
            redis_healthy = redis_manager.health_check()
            redis_status = "healthy" if redis_healthy else "unhealthy"
            cache_stats = redis_manager.get_cache_stats()
        except Exception as e:
            redis_status = f"error: {str(e)}"
            cache_stats = {}
        
        # Check worker status
        try:
            worker_statuses = redis_manager.get_all_worker_status()
            active_workers = len([w for w in worker_statuses.values() if w.get('status') == 'running'])
            worker_status = f"{active_workers} active workers"
        except Exception as e:
            worker_status = f"error: {str(e)}"
            active_workers = 0
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "api_server": "healthy",
            "database": {
                "status": db_status,
                "recommendations_available": db_recommendations_count
            },
            "cache": {
                "status": redis_status,
                "stats": cache_stats
            },
            "workers": {
                "status": worker_status,
                "active_count": active_workers
            },
            "data_sources": ["database", "cache"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
