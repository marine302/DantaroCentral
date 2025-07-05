"""
API Router 통합 모듈
모든 API 라우터를 한 곳에서 관리
"""
from fastapi import APIRouter

from app.api.v1.endpoints import market_data
from app.api.v1.endpoints import websocket as websocket_endpoints  
from app.api.v1.endpoints import admin

# 메인 API 라우터 생성
api_router = APIRouter()

# API 엔드포인트 라우터들 포함
api_router.include_router(
    market_data.router,
    prefix="/market-data",
    tags=["Market Data"]
)

api_router.include_router(
    websocket_endpoints.router,
    tags=["WebSocket"]
)

api_router.include_router(
    admin.router,
    prefix="/admin", 
    tags=["Admin"]
)
