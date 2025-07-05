"""
Market Data API modules

This package contains all market data related endpoints organized by functionality:
- recommendations: Coin recommendation endpoints
- support_levels: Support/resistance level calculation endpoints  
- market_status: Market health and status endpoints
- bundle_requests: Multi-request bundling endpoints
- coin_rankings: Coin ranking and top performer endpoints
"""

from fastapi import APIRouter
from .recommendations import router as recommendations_router
from .support_levels import router as support_levels_router
from .market_status import router as market_status_router
from .bundle_requests import router as bundle_requests_router
from .coin_rankings import router as coin_rankings_router

# Create combined router
router = APIRouter()

# Include all sub-routers
router.include_router(recommendations_router, tags=["recommendations"])
router.include_router(support_levels_router, tags=["support-levels"])
router.include_router(market_status_router, tags=["market-status"])
router.include_router(bundle_requests_router, tags=["bundle-requests"])
router.include_router(coin_rankings_router, tags=["coin-rankings"])

__all__ = [
    "router",
    "recommendations_router",
    "support_levels_router", 
    "market_status_router",
    "bundle_requests_router",
    "coin_rankings_router"
]
