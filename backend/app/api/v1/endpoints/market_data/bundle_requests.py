"""
Bundle requests API endpoints for the central server.

Provides endpoints for bundling multiple API requests into a single call
for efficiency and reduced network overhead.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings
from app.schemas.market_data import BundleRequest, BundleResponse
from .recommendations import get_recommendations
from .support_levels import get_support_levels
from .market_status import get_market_status

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify API key for user server authentication."""
    if credentials.credentials != settings.user_server_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


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
