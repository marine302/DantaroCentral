"""
Market data API endpoints for the central server.

This is the main market data router that includes endpoints
from all modularized components.
"""
from fastapi import APIRouter

# Import all sub-routers
from app.api.v1.endpoints.recommendations import router as recommendations_router
from app.api.v1.endpoints.support_levels import router as support_levels_router
from app.api.v1.endpoints.market_status import router as market_status_router
from app.api.v1.endpoints.bundle_requests import router as bundle_requests_router
from app.api.v1.endpoints.coin_rankings import router as coin_rankings_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(recommendations_router, tags=["recommendations"])
router.include_router(support_levels_router, tags=["support-levels"])
router.include_router(market_status_router, tags=["market-status"])
router.include_router(bundle_requests_router, tags=["bundle-requests"])
router.include_router(coin_rankings_router, tags=["coin-rankings"])
