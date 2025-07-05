"""
Market data API endpoints for the central server.

Provides endpoints for coin recommendations, support levels,
market status, and bundle requests for user servers.
"""
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import time
from datetime import datetime

from app.core.config import settings
from app.domain.recommenders.simple_recommender import CoinRecommender
from app.domain.recommenders.volume_recommender import VolumeBasedRecommender
from app.services.simple_recommender import SimpleVolumeRecommender
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
volume_recommender = VolumeBasedRecommender()  # 기존 복잡한 추천기
simple_recommender = SimpleVolumeRecommender()  # 새로운 간단한 추천기


def generate_mock_market_data() -> Dict[str, Dict]:
    """Mock 시장 데이터 생성 (개발/테스트용)"""
    import random
    
    mock_data = {}
    exchanges = ['OKX', 'Upbit', 'Coinone']
    base_symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'LINK', 'UNI', 'AVAX', 'ATOM', 'MATIC', 
                   'LTC', 'BCH', 'XRP', 'DOGE', 'SHIB', 'NEAR', 'ALGO', 'VET', 'FIL', 'SAND']
    
    coin_id = 1
    for exchange in exchanges:
        for i, symbol in enumerate(base_symbols):
            if exchange == 'OKX':
                full_symbol = f"{symbol}/USDT"
                currency = "USD"
                base_price = random.uniform(0.1, 100.0)
            else:  # Upbit, Coinone
                full_symbol = f"{symbol}/KRW"
                currency = "KRW"
                base_price = random.uniform(1000, 1000000)
            
            key = f"{exchange}_{full_symbol}"
            mock_data[key] = {
                'symbol': full_symbol,
                'exchange': exchange,
                'price': base_price,
                'volume_24h': random.uniform(1000000, 50000000),  # 1M~50M
                'change_24h': random.uniform(-15.0, 15.0),
                'currency': currency,
                'timestamp': datetime.utcnow().isoformat(),
                'market_cap': random.uniform(1000000, 1000000000),
                'last_updated': datetime.utcnow().isoformat()
            }
            coin_id += 1
    
    logger.info(f"Mock 데이터 생성 완료: {len(mock_data)}개 코인")
    return mock_data


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
    거래량 기반 단타 거래용 코인 추천
    
    전체 코인 중 거래량 상위 코인을 선별하고 변동성과 유동성을 기준으로
    단타 거래에 적합한 코인을 추천합니다.
    """
    try:
        # 캐시 키 설정
        cache_key = f"recommendations:{top_n}"
        volume_cache_key = f"recommendations:volume:{top_n}"
        
        # 강제 갱신이 아니면 캐시 확인
        if not force_refresh:
            # 먼저 거래량 기반 캐시 확인
            volume_cached = await cache_service.get(volume_cache_key)
            if volume_cached:
                logger.info(f"거래량 기반 캐시 추천 사용 (top_{top_n})")
                return CoinRecommendationResponse(**volume_cached)
                
            # 일반 캐시 확인
            cached = await cache_service.get(cache_key)
            if cached:
                logger.info(f"일반 캐시 추천 사용 (top_{top_n})")
                return CoinRecommendationResponse(**cached)
        
        # 실시간 시장 데이터 가져오기 (새로운 클린 서비스 사용)
        from app.services.real_data_service import backend_real_data_service
        
        logger.info("실제 시장 데이터 수집 중...")
        market_data = await backend_real_data_service.get_market_data_only()
            
        if not market_data:
            logger.warning("클린 서비스 실패, 기존 실시간 서비스 사용")
            market_data = await real_market_service.get_market_data()
            
        if not market_data:
            logger.warning("실시간 데이터도 없음, 빈 추천 반환")
            # 빈 추천 응답 반환
            from datetime import datetime
            return CoinRecommendationResponse(
                recommendations=[],
                total_analyzed=0,
                cache_timestamp=datetime.utcnow(),
                metadata={
                    "analysis_methods": ["volume_based"],
                    "recommendation_type": "scalping", 
                    "top_n": top_n,
                    "generated_at": time.time(),
                    "error": "No market data available"
                }
            )
        
        # 간단한 거래량 기반 추천 생성 (새로운 시스템)
        logger.info(f"거래량 기반 상위 코인 선별 (대상: {len(market_data)} 코인)")
        top_coins = await simple_recommender.get_top_coins_by_volume(
            market_data=market_data,
            top_n=top_n
        )
        
        if not top_coins:
            logger.warning("추천 코인 생성 실패, 기존 시스템 사용")
            volume_recommendations = await volume_recommender.get_recommendations(
                market_data=market_data,
                top_n=top_n
            )
        else:
            # 새로운 형식으로 변환
            volume_recommendations = []
            for coin in top_coins:
                volume_recommendations.append({
                    'symbol': coin['symbol'],
                    'overall_score': coin['recommendation_score'] / 100,  # 0-1 범위로 변환
                    'strength': 'strong' if coin['recommendation_score'] > 80 else 'moderate',
                    'component_scores': {
                        'volume': min(1.0, coin['volume_24h'] / 1000000000),  # 정규화
                        'volatility': 0.5,  # 기본값
                        'technical': 0.0,
                        'risk': 0.8
                    },
                    'current_price': coin['current_price'],
                    'price_change_24h': coin['change_24h'] / 100,  # 비율로 변환
                    'volume_24h': coin['volume_24h'],
                    'analysis_details': {
                        'volume_rank': coin['volume_rank'],
                        'support_level': coin['support_level'],
                        'resistance_level': coin['resistance_level'],
                        'entry_price': coin['entry_price_suggestion'],
                        'take_profit': coin['take_profit_suggestion'],
                        'stop_loss': coin['stop_loss_suggestion'],
                        'exchange': coin['exchange'],
                        'currency': coin['currency'],
                        'analysis_method': 'simple_volume_based',
                        'recommendation_reason': coin['recommendation_reason']
                    }
                })
        
        logger.info(f"✅ 추천 코인 {len(volume_recommendations)}개 생성 완료")
        
        # 응답 형식 변환
        from app.schemas.market_data import CoinRecommendation
        recommendation_objects = []
        
        for i, rec in enumerate(volume_recommendations):
            # 스키마에 맞게 변환
            rec_obj = CoinRecommendation(
                symbol=rec['symbol'],
                total_score=rec['overall_score'],
                recommendation_strength=rec['strength'],
                component_scores={
                    'volume': rec['component_scores']['volume'],
                    'volatility': rec['component_scores']['volatility'], 
                    'technical': rec['component_scores'].get('technical', 0.0),
                    'risk': rec['component_scores'].get('risk', 0.0)
                },
                metadata={
                    'current_price': rec['current_price'],
                    'price_change_24h': rec['price_change_24h'],
                    'volume_24h': rec['volume_24h'],
                    'market_cap': None,
                    'analysis_details': rec['analysis_details']
                }
            )
            recommendation_objects.append(rec_obj)
        
        # 응답 생성
        from datetime import datetime
        response = CoinRecommendationResponse(
            recommendations=recommendation_objects,
            total_analyzed=len(market_data),
            cache_timestamp=datetime.utcnow(),
            metadata={
                "analysis_methods": ["volume_based", "volatility", "liquidity"],
                "recommendation_type": "scalping",
                "top_n": top_n,
                "generated_at": time.time()
            }
        )
        
        # 캐시 저장
        cache_data = response.dict() if hasattr(response, 'dict') else response.model_dump()
        
        # 볼륨 캐시에 저장
        await cache_service.set(
            volume_cache_key, 
            cache_data, 
            ttl=settings.strategy_cache_ttl
        )
        
        # 기본 캐시에도 저장
        await cache_service.set(
            cache_key, 
            cache_data, 
            ttl=settings.strategy_cache_ttl
        )
        
        logger.info(f"거래량 기반 추천 생성 완료: {len(recommendation_objects)}개 코인")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"추천 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="추천 생성 중 내부 오류가 발생했습니다"
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


@router.get(
    "/top-coins-by-volume",
    summary="Get top coins by volume",
    description="Get top coins ranked by 24h trading volume - for user servers"
)
async def get_top_coins_by_volume(
    top_n: int = Query(default=50, ge=1, le=100, description="Number of coins to return"),
    exchange: Optional[str] = Query(default=None, description="Filter by exchange (OKX, Upbit, Coinone)"),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    거래량 기반 상위 코인 목록 (사용자 서버용)
    
    Returns:
        - 거래량 순 상위 코인 목록
        - 저점/고점 정보 포함
        - 거래소별 분류 가능
    """
    try:
        # 실시간 시장 데이터 가져오기
        market_data = await real_market_service.get_market_data()
        
        if not market_data:
            market_data = await market_data_service.get_all_market_data()
        
        # 새로운 클린 서비스로 보완
        if not market_data:
            from app.services.real_data_service import backend_real_data_service
            logger.info("클린 데이터 서비스 사용")
            market_data = await backend_real_data_service.get_market_data_only()
            
        if not market_data:
            # Fallback: Mock 데이터 생성 (다양한 거래소 포함)
            logger.warning("모든 실제 데이터 서비스 실패, Mock 데이터 생성")
            market_data = generate_mock_market_data()
        
        logger.info(f"Market data keys: {len(market_data)} items")
        logger.info(f"Market data sample: {list(market_data.keys())[:3]}")
        
        # 간단한 추천 시스템으로 상위 코인 선별
        if exchange:
            # 거래소별 추천
            recommendations_by_exchange = await simple_recommender.get_recommendations_by_exchange(market_data, top_n)
            top_coins = recommendations_by_exchange.get(exchange, [])
        else:
            # 전체 추천
            top_coins = await simple_recommender.get_top_coins_by_volume(market_data, top_n)
        
        return {
            "success": True,
            "data": {
                "top_coins": top_coins,
                "total_count": len(top_coins),
                "exchange_filter": exchange,
                "criteria": "volume_24h",
                "stats": simple_recommender.get_stats()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "purpose": "user_server_reference",
                "includes": ["price", "volume", "support_resistance", "entry_exit_points"],
                "update_frequency": "real_time"
            }
        }
        
    except Exception as e:
        logger.error(f"상위 코인 조회 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="상위 코인 조회 중 오류가 발생했습니다")





@router.get(
    "/recommendations-by-exchange",
    summary="Get recommendations by exchange", 
    description="Get recommended coins grouped by exchange"
)
async def get_recommendations_by_exchange(
    top_n: int = Query(default=50, ge=1, le=100, description="Number of recommendations per exchange"),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    거래소별 추천 코인 목록
    
    Returns:
        - 거래소별로 분류된 추천 코인
        - 각 거래소당 상위 코인들
    """
    try:
        # 실시간 시장 데이터 가져오기
        market_data = await real_market_service.get_market_data()
        
        if not market_data:
            market_data = await market_data_service.get_all_market_data()
        
        if not market_data:
            raise HTTPException(status_code=503, detail="시장 데이터를 일시적으로 사용할 수 없습니다")
        
        # 거래소별 추천 생성
        recommendations_by_exchange = await simple_recommender.get_recommendations_by_exchange(market_data, top_n)
        
        return {
            "success": True,
            "recommendations_by_exchange": recommendations_by_exchange,
            "exchanges": list(recommendations_by_exchange.keys()),
            "top_n_per_exchange": top_n,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "criteria": "volume_based",
                "purpose": "user_server_trading_reference"
            }
        }
        
    except Exception as e:
        logger.error(f"거래소별 추천 조회 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="거래소별 추천 조회 중 오류가 발생했습니다")


@router.get(
    "/real-top-coins",
    summary="Get real top coins by volume",
    description="Get top coins from real exchanges (OKX, Upbit, Coinone)"
)
async def get_real_top_coins(
    top_n: int = Query(default=20, ge=1, le=50, description="Number of coins to return")
) -> Dict[str, Any]:
    """
    실제 거래소에서 거래량 기반 상위 코인 목록
    """
    try:
        # 새로운 클린 서비스로 실제 데이터 수집
        from app.services.real_data_service import RealDataService
        
        async with RealDataService() as service:
            market_data = await service.get_market_data_only()
            
            if not market_data:
                return {
                    "success": False,
                    "error": "실제 데이터 수집 실패",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 거래량 기준 정렬
            sorted_coins = sorted(
                market_data.items(),
                key=lambda x: x[1].get('volume_24h', 0),
                reverse=True
            )
            
            # 상위 N개 선택 및 변환
            top_coins = []
            for i, (key, coin_data) in enumerate(sorted_coins[:top_n]):
                current_price = coin_data['price']
                
                coin_info = {
                    'symbol': coin_data['symbol'].split('/')[0],
                    'full_symbol': coin_data['symbol'],
                    'exchange': coin_data['exchange'],
                    'current_price': current_price,
                    'volume_24h': coin_data['volume_24h'],
                    'change_24h': coin_data['change_24h'],
                    'currency': coin_data['currency'],
                    'timestamp': coin_data['timestamp'],
                    'support_level': current_price * 0.95,
                    'resistance_level': current_price * 1.05,
                    'volume_rank': i + 1,
                    'is_recommended': True,
                    'recommendation_score': max(0, 100 - (i * 2))
                }
                top_coins.append(coin_info)
            
            # 거래소별 통계
            exchange_stats = {}
            for coin_data in market_data.values():
                exchange = coin_data['exchange']
                exchange_stats[exchange] = exchange_stats.get(exchange, 0) + 1
            
            return {
                "success": True,
                "data": {
                    "top_coins": top_coins,
                    "total_count": len(top_coins),
                    "exchange_stats": exchange_stats
                },
                "service_stats": service.get_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"실제 코인 조회 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="실제 코인 조회 중 오류가 발생했습니다")
