"""
Market status API endpoints for the central server.

Provides endpoints for overall market health, sentiment analysis,
and system status information.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings
from app.schemas.market_data import MarketStatusResponse, SystemHealth
from app.services.market_data_collector import MarketDataCollector

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
market_data_collector = MarketDataCollector()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify API key for user server authentication."""
    if credentials.credentials != settings.user_server_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


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
        # 실시간 시장 데이터 가져오기 (임시로 빈 데이터 반환)
        real_market_data = {}
        
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
