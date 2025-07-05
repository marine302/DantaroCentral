"""
헬스체크 라우터 모듈  
서버 상태 확인 엔드포인트들
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 라우터 생성
health_router = APIRouter()


@health_router.get("/health")
@health_router.get(f"{settings.api_v1_str}/health")
async def health_check():
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Dantaro Central",
        "version": "1.0.0"
    }


@health_router.get("/api/websocket/status")
async def websocket_status():
    """WebSocket 연결 상태 확인"""
    try:
        from app.api.v1.endpoints.websocket import connection_manager
        
        stats = {
            "active_connections": len(connection_manager.active_connections),
            "cached_prices": len(connection_manager.last_prices),
            "last_kimchi_premiums": len(connection_manager.last_kimchi_premiums)
        }
        
        return {
            "active_connections": len(connection_manager.active_connections),
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"WebSocket 상태 확인 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "WebSocket 상태 확인 실패", "detail": str(e)}
        )
