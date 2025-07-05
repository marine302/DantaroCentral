"""
Main FastAPI application module for Dantaro Central server.
Clean and optimized version.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.startup import startup_services
from app.core.shutdown import shutdown_services

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Dantaro Central 서버 시작")
    try:
        await startup_services()
        logger.info("✅ 모든 서비스 초기화 완료")
        yield
    except Exception as e:
        logger.error(f"❌ 서버 시작 실패: {e}", exc_info=True)
        raise
    finally:
        # Shutdown
        logger.info("🔄 Dantaro Central 서버 종료")
        await shutdown_services()
        logger.info("✅ 서버 종료 완료")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.project_name,
        description="Dantaro Central - AI Trading Bot Platform Central Server",
        version="1.0.0",
        openapi_url=f"{settings.api_v1_str}/openapi.json" if settings.is_development else None,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan
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
    async def add_process_time_header(request, call_next):
        import time
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Include routers manually for now
    from app.api.v1.router import api_router
    from app.routes.frontend import frontend_router
    from app.routes.health import health_router
    
    app.include_router(api_router, prefix=settings.api_v1_str)
    app.include_router(frontend_router)
    app.include_router(health_router)
    
    return app


# Create application instance
app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_clean:app",
        host="0.0.0.0",
        port=8003,  # 다른 포트 사용
        reload=settings.is_development,
        log_level="info"
    )
