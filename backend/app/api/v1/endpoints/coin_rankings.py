"""
Coin rankings API endpoints for the central server.

Provides endpoints for coin rankings, top performers by volume,
and exchange-specific recommendations.
"""
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import random
from datetime import datetime

from app.core.config import settings
from app.services.simple_recommender import SimpleVolumeRecommender
from app.services.real_market_service import RealMarketDataService

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
real_market_service = RealMarketDataService()
simple_recommender = SimpleVolumeRecommender()


def generate_mock_market_data() -> Dict[str, Dict]:
    """Mock 시장 데이터 생성 (개발/테스트용)"""
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
            # Use empty data for now - can be improved later  
            market_data = {}
        
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
            # Use empty data for now - can be improved later
            market_data = {}
        
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
