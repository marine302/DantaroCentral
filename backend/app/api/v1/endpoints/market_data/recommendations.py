"""
Coin recommendations API endpoint.
Handles AI-based coin recommendations with caching and background tasks.
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import time
from datetime import datetime

from app.core.config import settings
from app.domain.recommenders.simple_recommender import CoinRecommender
from app.domain.recommenders.volume_recommender import VolumeBasedRecommender
from app.services.simple_recommender import SimpleVolumeRecommender
from app.schemas.market_data import (
    CoinRecommendationResponse,
    CoinRecommendation
)
from app.services.real_market_service import RealMarketDataService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
real_market_service = RealMarketDataService()
cache_service = CacheService()
coin_recommender = CoinRecommender()
volume_recommender = VolumeBasedRecommender()
simple_recommender = SimpleVolumeRecommender()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify API key for user server authentication."""
    if credentials.credentials != settings.user_server_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
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
    Get current coin recommendations based on advanced analysis.
    
    This endpoint provides AI-powered coin recommendations using:
    - Technical analysis indicators
    - Volume analysis 
    - Risk assessment
    - Market sentiment
    """
    try:
        cache_key = f"recommendations:{top_n}:{force_refresh}"
        
        # Check cache first (unless force_refresh)
        if not force_refresh:
            cached_result = await cache_service.get(cache_key)
            if cached_result:
                # Fix cache timestamp format if needed
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
            logger.warning("Real market data unavailable, using empty fallback")
            # Use empty data for now - can be improved later
            real_market_data = {}
        
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
