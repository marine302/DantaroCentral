"""
Lightweight market data API endpoints for the central server.
Serves cached/database results only - no heavy analysis.
"""
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from datetime import datetime
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
from app.services.simple_recommender import SimpleVolumeRecommender
from app.services.real_market_service import RealMarketDataService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# 서비스 초기화
simple_recommender = SimpleVolumeRecommender()
real_market_service = RealMarketDataService()


async def verify_api_key(x_api_key: str = Header(None)) -> bool:
    """Verify API key for user server authentication."""
    # 테스트용 임시 코드 - 모든 API 키를 허용
    logger.info(f"API Key used: {x_api_key[:5] if x_api_key else 'None'}")
    logger.info(f"Expected API Key: {settings.user_server_api_key[:5] if settings.user_server_api_key else 'None'}")
    logger.info("임시 설정: 모든 API 키 허용")
    
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
            # 볼륨 기반 분석 메서드 정보 추가
            if 'analysis_details' not in rec:
                rec['analysis_details'] = {}
            
            # 분석 방법 정보 추가
            rec['analysis_details']['analysis_method'] = 'volume_based'
            
            # 스키마에 맞게 변환
            formatted_rec = LightCoinRecommendation(**rec)
            formatted_recommendations.append(formatted_rec)
        
        # Format response
        return CoinRecommendationResponse(
            success=True,
            recommendations=formatted_recommendations,
            total_analyzed=len(recommendations),
            metadata={
                "analysis_method": "volume_based",
                "features": ["volume", "volatility", "liquidity", "price_action"],
                "purpose": "real-time scalping",
                "version": "2.0",
                "dynamic_selection": True
            },
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


@router.get(
    "/top-coins-by-volume",
    dependencies=[Depends(verify_api_key)],
    summary="Get top coins by volume",
    description="Get top coins ranked by 24h trading volume - for user servers",
    response_model=None
)
async def get_top_coins_by_volume(
    top_n: int = Query(default=50, ge=1, le=100, description="Number of coins to return"),
    exchange: Optional[str] = Query(default=None, description="Filter by exchange (OKX, Upbit, Coinone)")
) -> Dict[str, Any]:
    """
    거래량 기반 상위 코인 목록 (사용자 서버용)
    
    Returns:
        - 거래량 순 상위 코인 목록
        - 저점/고점 정보 포함
        - 거래소별 분류 가능
    """
    try:
        logger.info(f"거래량 기반 상위 {top_n}개 코인 요청 (거래소: {exchange or '전체'})")
        
        # 임시 mock 데이터로 빠른 테스트
        mock_coins = []
        for i in range(min(top_n, 10)):
            mock_coins.append({
                'symbol': f'COIN{i+1}',
                'full_symbol': f'COIN{i+1}/USDT',
                'exchange': 'OKX',
                'current_price': 100 + i * 10,
                'volume_24h': 1000000 * (10 - i),
                'change_24h': (i - 5) * 2.5,
                'currency': 'USD',
                'timestamp': datetime.utcnow().isoformat(),
                'support_level': (100 + i * 10) * 0.95,
                'resistance_level': (100 + i * 10) * 1.05,
                'entry_price_suggestion': (100 + i * 10) * 0.98,
                'take_profit_suggestion': (100 + i * 10) * 1.03,
                'stop_loss_suggestion': (100 + i * 10) * 0.97,
                'recommendation_reason': 'high_volume',
                'volume_rank': i + 1,
                'is_recommended': True,
                'recommendation_score': max(0, 100 - (i * 10)),
                'last_updated': datetime.utcnow().isoformat()
            })
        
        logger.info(f"✅ {len(mock_coins)}개 코인 반환 (mock 데이터)")
        
        return {
            "success": True,
            "data": {
                "top_coins": mock_coins,
                "total_count": len(mock_coins),
                "exchange_filter": exchange,
                "criteria": "volume_24h",
                "stats": {
                    "criteria": "volume",
                    "min_volume_threshold": 1000000,
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "purpose": "user_server_reference",
                "includes": ["price", "volume", "support_resistance", "entry_exit_points"],
                "update_frequency": "real_time",
                "data_source": "mock"
            }
        }
        
    except Exception as e:
        logger.error(f"거래량 기반 코인 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/arbitrage-opportunities",
    summary="Get arbitrage opportunities",
    description="Get arbitrage opportunities between exchanges for recommended coins"
)
async def get_arbitrage_opportunities(
    min_profit_rate: float = Query(default=1.0, ge=0.1, le=50.0, description="Minimum profit rate (%)"),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    추천 코인 중 차익거래 기회 분석
    
    Returns:
        - 거래소 간 가격 차이로 인한 차익거래 기회
        - 수익률, 거래량 등 상세 정보
    """
    try:
        logger.info(f"차익거래 기회 분석 시작 (최소 수익률: {min_profit_rate}%)")
        
        # 실제 데이터가 있는지 확인하고 없으면 빈 결과 반환
        from app.services.simple_recommender import SimpleVolumeRecommender
        from app.services.real_market_service import RealMarketDataService
        
        simple_recommender = SimpleVolumeRecommender()
        real_market_service = RealMarketDataService()
        
        try:
            market_data = await real_market_service.get_market_data()
            if market_data and len(market_data) > 0:
                arbitrage_opportunities = await simple_recommender.get_arbitrage_opportunities(market_data)
                
                # 최소 수익률 필터링
                filtered_opportunities = [
                    opp for opp in arbitrage_opportunities 
                    if opp["profit_rate"] >= min_profit_rate
                ]
                
                return {
                    "success": True,
                    "data": {
                        "arbitrage_opportunities": filtered_opportunities,
                        "total_count": len(filtered_opportunities),
                        "min_profit_filter": min_profit_rate,
                        "avg_profit_rate": sum(opp["profit_rate"] for opp in filtered_opportunities) / len(filtered_opportunities) if filtered_opportunities else 0
                    },
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "purpose": "arbitrage_trading",
                        "data_source": "real",
                        "includes": ["price_difference", "profit_calculation", "exchange_comparison"],
                        "update_frequency": "real_time"
                    }
                }
            else:
                # 실제 데이터가 없으면 빈 결과
                return {
                    "success": True,
                    "data": {
                        "arbitrage_opportunities": [],
                        "total_count": 0,
                        "min_profit_filter": min_profit_rate,
                        "avg_profit_rate": 0
                    },
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "purpose": "arbitrage_trading",
                        "data_source": "empty",
                        "message": "실시간 데이터를 사용할 수 없습니다",
                        "includes": ["price_difference", "profit_calculation", "exchange_comparison"],
                        "update_frequency": "real_time"
                    }
                }
        except Exception as data_error:
            logger.warning(f"실제 데이터 사용 실패, 빈 결과 반환: {data_error}")
            return {
                "success": True,
                "data": {
                    "arbitrage_opportunities": [],
                    "total_count": 0,
                    "min_profit_filter": min_profit_rate,
                    "avg_profit_rate": 0
                },
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "purpose": "arbitrage_trading",
                    "data_source": "error",
                    "error": str(data_error),
                    "includes": ["price_difference", "profit_calculation", "exchange_comparison"],
                    "update_frequency": "real_time"
                }
            }
        
    except Exception as e:
        logger.error(f"차익거래 기회 분석 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get(
    "/recommendations-by-exchange",
    dependencies=[Depends(verify_api_key)],
    summary="Get recommendations by exchange",
    description="Get coin recommendations grouped by exchange",
    response_model=None
)
async def get_recommendations_by_exchange(
    top_n: int = Query(default=50, ge=1, le=100, description="Number of coins per exchange")
) -> Dict[str, Any]:
    """
    거래소별 추천 코인 조회
    
    Returns:
        - 거래소별로 그룹화된 추천 코인 목록
        - OKX, Upbit, Coinone 각각 top_n개씩
    """
    try:
        logger.info(f"거래소별 추천 코인 조회 (각 거래소당 {top_n}개)")
        
        # 실시간 시장 데이터 가져오기
        market_data = await real_market_service.get_market_data()
        
        if not market_data:
            try:
                from app.services.market_data_service import MarketDataService
                market_data_service = MarketDataService()
                market_data = await market_data_service.get_all_market_data()
                logger.info("실시간 데이터 없음, 데이터베이스 데이터 사용")
            except Exception as db_e:
                logger.error(f"데이터베이스 fallback 실패: {db_e}")
                market_data = {}
        
        if not market_data:
            raise HTTPException(status_code=503, detail="시장 데이터를 일시적으로 사용할 수 없습니다")
        
        # 거래소별 추천 코인 분석
        recommendations_by_exchange = await simple_recommender.get_recommendations_by_exchange(market_data, top_n)
        
        # 통계 계산
        total_recommendations = sum(len(coins) for coins in recommendations_by_exchange.values())
        
        logger.info(f"✅ 거래소별 추천 완료: 총 {total_recommendations}개 코인")
        
        return {
            "success": True,
            "data": {
                "recommendations_by_exchange": recommendations_by_exchange,
                "total_count": total_recommendations,
                "exchange_counts": {
                    exchange: len(coins) 
                    for exchange, coins in recommendations_by_exchange.items()
                },
                "per_exchange_limit": top_n,
                "stats": simple_recommender.get_stats()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "purpose": "exchange_specific_recommendations",
                "exchanges": ["OKX", "Upbit", "Coinone"],
                "criteria": "volume_24h"
            }
        }
        
    except Exception as e:
        logger.error(f"거래소별 추천 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )



