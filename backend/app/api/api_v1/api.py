"""
API v1 router module.
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    market_analysis,
    strategy,
    bot_config,
    user_servers,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    market_analysis.router, 
    prefix="/market-analysis", 
    tags=["market-analysis"]
)
api_router.include_router(
    strategy.router, 
    prefix="/strategy", 
    tags=["strategy"]
)
api_router.include_router(
    bot_config.router, 
    prefix="/bot-config", 
    tags=["bot-config"]
)
api_router.include_router(
    user_servers.router, 
    prefix="/user-servers", 
    tags=["user-servers"]
)
