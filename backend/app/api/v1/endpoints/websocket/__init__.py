"""
WebSocket 관련 엔드포인트 모듈

실시간 데이터 전송, 대시보드, 브로드캐스트 기능 등을 제공합니다.
"""

from fastapi.routing import APIRouter

# 각 서브 모듈에서 라우터 import
from .realtime import router as realtime_router
from .dashboard import router as dashboard_router  
from .broadcast import router as broadcast_router

# 통합 라우터 생성
router = APIRouter()

# 각 서브 라우터를 통합 라우터에 포함
router.include_router(realtime_router, tags=["websocket-realtime"])
router.include_router(dashboard_router, tags=["websocket-dashboard"])
router.include_router(broadcast_router, tags=["websocket-broadcast"])

# 모든 것을 export
__all__ = [
    "router",
    "realtime_router",
    "dashboard_router", 
    "broadcast_router"
]
