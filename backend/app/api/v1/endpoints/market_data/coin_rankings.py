"""
코인 랭킹 API 엔드포인트 - 간소화된 버전
거래소별 거래량 상위 코인 순위 제공
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from datetime import datetime

from app.core.config import settings
from app.domain.recommenders.coin_recommender import coin_recommender

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """API 키 검증"""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="API key required")
    
    expected_key = getattr(settings, 'api_key', 'dantaro-central-2024')
    if credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


@router.get("/coin-rankings")
async def get_coin_rankings(
    background_tasks: BackgroundTasks,
    api_key_valid: bool = Depends(verify_api_key),
    exchange: str = Query("all", description="거래소 선택"),
    top_n: int = Query(10, ge=1, le=50, description="상위 N개 코인")
) -> Dict[str, Any]:
    """코인 랭킹 조회 API"""
    try:
        logger.info(f"코인 랭킹 요청: exchange={exchange}, top_n={top_n}")
        
        if exchange == "all":
            recommendations_by_exchange = await coin_recommender.get_recommendations_by_exchange(
                exchange_names=["upbit", "okx", "coinone", "gateio", "bybit", "bithumb"], 
                limit=top_n
            )
        else:
            recommendations = await coin_recommender.get_recommendations(
                exchange=exchange, 
                limit=top_n
            )
            recommendations_by_exchange = {exchange: recommendations}
        
        return {
            "status": "success",
            "data": recommendations_by_exchange,
            "metadata": {
                "exchange": exchange,
                "top_n": top_n,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"코인 랭킹 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
