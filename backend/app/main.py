"""
Main FastAPI application module for Dantaro Central server.
Lightweight version that serves pre-computed data only.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from app.core.config import settings
from app.api.v1.endpoints import market_data_light
from app.database.manager import db_manager
from app.database.redis_cache import redis_manager

# Configure structured logging
logger = structlog.get_logger()


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.project_name,
        description="Dantaro Central - AI Trading Bot Platform Central Server",
        version="0.1.0",
        openapi_url=f"{settings.api_v1_str}/openapi.json" if settings.is_development else None,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request
        logger.info(
            "request_processed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
        )
        return response
    
    # Include API router
    app.include_router(
        market_data_light.router,
        prefix=settings.api_v1_str,
        tags=["Market Data Light"]
    )
    
    # Health check endpoint (both paths for compatibility)
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "dantaro-central"}
        
    @app.get(f"{settings.api_v1_str}/health")
    async def health_check_v1():
        """Health check endpoint for API v1."""
        return {"status": "healthy", "service": "dantaro-central"}
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Lightweight startup - just verify connections."""
        try:
            logger.info("Starting Dantaro Central API server (lightweight mode)...")
            
            # Test database connection
            try:
                recommendations = db_manager.get_latest_recommendations(limit=1)
                logger.info(f"Database connection OK - {len(recommendations)} recommendations available")
            except Exception as e:
                logger.warning(f"Database connection issue: {e}")
            
            # Test Redis connection
            try:
                redis_healthy = redis_manager.health_check()
                if redis_healthy:
                    logger.info("Redis connection OK")
                else:
                    logger.warning("Redis connection issue")
            except Exception as e:
                logger.warning(f"Redis connection issue: {e}")
            
            logger.info("✅ Dantaro Central API server started successfully (lightweight mode)")
            logger.info("📊 This server serves pre-computed data from analysis workers")
            
        except Exception as e:
            logger.error(f"Startup failed: {e}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Lightweight shutdown."""
        try:
            logger.info("Shutting down Dantaro Central API server...")
            logger.info("✅ Dantaro Central API server shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        logger.error(
            "unhandled_exception",
            error=str(exc),
            method=request.method,
            url=str(request.url),
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


app = create_application()
