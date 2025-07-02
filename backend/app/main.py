"""
Main FastAPI application module for Dantaro Central server.
Lightweight version that serves pre-computed data + real-time dashboard.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import structlog
import time
import os

from app.core.config import settings
from app.api.v1.endpoints import market_data_light
from app.api.v1.endpoints import websocket as websocket_endpoints
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
    
    # Include API routers
    app.include_router(
        market_data_light.router,
        prefix=settings.api_v1_str,
        tags=["Market Data Light"]
    )
    
    # Include WebSocket router
    app.include_router(
        websocket_endpoints.router,
        tags=["WebSocket"]
    )
    
    # Setup static files and templates
    # 백엔드 디렉토리에서 프론트엔드 디렉토리로의 정확한 경로
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    frontend_dir = os.path.join(project_root, "frontend")
    
    print(f"🔍 경로 확인:")
    print(f"  Backend 디렉토리: {backend_dir}")
    print(f"  프로젝트 루트: {project_root}")
    print(f"  Frontend 디렉토리: {frontend_dir}")
    print(f"  Frontend 존재 여부: {os.path.exists(frontend_dir)}")
    
    if os.path.exists(frontend_dir):
        # Mount static files
        static_path = os.path.join(frontend_dir, "static")
        app.mount("/static", StaticFiles(directory=static_path), name="static")
        
        # Setup templates
        templates_path = os.path.join(frontend_dir, "templates")
        templates = Jinja2Templates(directory=templates_path)
        
        print(f"✅ 정적 파일 경로: {static_path}")
        print(f"✅ 템플릿 경로: {templates_path}")
        
        # Dashboard route
        @app.get("/", response_class=HTMLResponse)
        @app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page."""
            return templates.TemplateResponse("dashboard.html", {"request": request})
    
    else:
        print(f"❌ Frontend 디렉토리를 찾을 수 없습니다: {frontend_dir}")
        # Fallback if frontend not found
        @app.get("/")
        async def root():
            return {"message": "Dantaro Central API Server", "error": f"Frontend not found at {frontend_dir}"}
    
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
