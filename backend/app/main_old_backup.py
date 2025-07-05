"""
Main FastAPI application module for Dantaro Central server.
Real-time version that collects and serves dynamic market data.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import structlog
import time
import os
import asyncio
from datetime import datetime

from app.core.config import settings
from app.api.v1.endpoints import market_data_light
from app.api.v1.endpoints import websocket as websocket_endpoints
from app.api.v1.endpoints import admin
from app.database.manager import db_manager
from app.database.redis_cache import redis_manager
from prometheus_fastapi_instrumentator import Instrumentator

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
    
    # Include Admin router
    app.include_router(
        admin.router,
        prefix=f"{settings.api_v1_str}/admin",
        tags=["Admin"]
    )
    
    # Include WebSocket router
    app.include_router(
        websocket_endpoints.router,
        tags=["WebSocket"]
    )
    
    # Setup static files and templates
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    frontend_dir = os.path.join(project_root, "frontend")

    logger.info(
        "경로 확인",
        backend_dir=backend_dir,
        project_root=project_root,
        frontend_dir=frontend_dir,
        frontend_exists=os.path.exists(frontend_dir),
    )

    if os.path.exists(frontend_dir):
        # Mount static files
        static_path = os.path.join(frontend_dir, "static")
        app.mount("/static", StaticFiles(directory=static_path), name="static")

        # Setup templates
        templates_path = os.path.join(frontend_dir, "templates")
        templates = Jinja2Templates(directory=templates_path)

        logger.info(
            "정적 파일 및 템플릿 경로",
            static_path=static_path,
            templates_path=templates_path,
        )

        # Dashboard route
        @app.get("/", response_class=HTMLResponse)
        @app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page (simplified)."""
            return templates.TemplateResponse("dashboard_simple.html", {"request": request})
        
        # Debug route
        @app.get("/debug", response_class=HTMLResponse)
        async def debug_dashboard(request: Request):
            """Debug dashboard page."""
            return templates.TemplateResponse("debug.html", {"request": request})
        
        # Simple WebSocket test route
        @app.get("/simple-test", response_class=HTMLResponse)
        async def simple_websocket_test(request: Request):
            """Simple WebSocket test page."""
            return templates.TemplateResponse("simple_test.html", {"request": request})
        
        # Markets page route
        @app.get("/markets", response_class=HTMLResponse)
        async def markets_page(request: Request):
            """거래소별 전체 시세 페이지."""
            return templates.TemplateResponse("markets.html", {"request": request})
        
        # Recommendations page route  
        @app.get("/recommendations", response_class=HTMLResponse)
        async def recommendations_page(request: Request):
            """AI 추천 코인 페이지."""
            return templates.TemplateResponse("recommendations.html", {"request": request})
        

        
        # Dashboard API for volume recommendations
        @app.get("/api/dashboard/volume-recommendations")
        async def get_dashboard_volume_recommendations():
            """대시보드용 볼륨 기반 추천 데이터"""
            try:
                import aiohttp
                # 내부 API 호출
                async with aiohttp.ClientSession() as session:
                    headers = {"X-API-Key": "test-api-key-for-enterprise-servers"}
                    
                    # 추천 데이터 가져오기
                    async with session.get("http://localhost:8001/api/v1/recommendations", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            recommendations = data.get('recommendations', [])
                            
                            # 대시보드 형식으로 변환
                            dashboard_data = []
                            for rec in recommendations[:10]:  # 상위 10개만
                                dashboard_data.append({
                                    "symbol": rec.get("symbol", ""),
                                    "score": rec.get("total_score", 0),
                                    "volume_score": rec.get("volume_score", 0),
                                    "volatility_score": rec.get("volatility_score", 0),
                                    "price": rec.get("current_price", 0),
                                    "change_24h": rec.get("price_change_24h", 0),
                                    "volume_24h": rec.get("volume_24h", 0),
                                    "strength": rec.get("recommendation_strength", ""),
                                    "analysis_method": rec.get("analysis_details", {}).get("analysis_method", "volume_based")
                                })
                            
                            return {
                                "success": True,
                                "recommendations": dashboard_data,
                                "metadata": data.get("metadata", {}),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"API 호출 실패: {response.status}",
                                "recommendations": [],
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "recommendations": [],
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # WebSocket status endpoint
        @app.get("/api/websocket/status")
        async def get_websocket_status():
            """WebSocket 연결 상태 확인"""
            from app.api.v1.endpoints.websocket import connection_manager
            return {
                "active_connections": len(connection_manager.active_connections),
                "stats": connection_manager.get_stats(),
                "timestamp": datetime.now().isoformat()
            }
        
        # Test data broadcast endpoint
        @app.post("/api/websocket/broadcast-test-data")
        async def broadcast_test_data():
            """테스트 데이터를 모든 WebSocket 연결에 브로드캐스트"""
            from app.api.v1.endpoints.websocket import connection_manager
            import random
            
            if not connection_manager.active_connections:
                return {"error": "활성화된 WebSocket 연결이 없습니다", "active_connections": 0}
            
            # 모의 가격 데이터
            price_data = []
            exchanges = ['OKX', 'Upbit', 'Coinone', 'Gate.io']
            symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL']
            
            for exchange in exchanges:
                for symbol in symbols:
                    price_data.append({
                        'exchange': exchange,
                        'symbol': symbol,
                        'price': round(random.uniform(30000, 70000), 2) if symbol == 'BTC' else round(random.uniform(1000, 5000), 2),
                        'volume': round(random.uniform(1000000, 10000000), 2),
                        'change_24h': round(random.uniform(-10, 10), 2),
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 모의 김치 프리미엄
            kimchi_data = []
            for symbol in ['BTC', 'ETH', 'ADA']:
                korean_price = round(random.uniform(30000, 35000), 2)
                global_price = round(korean_price * random.uniform(0.95, 1.05), 2)
                premium = round(((korean_price - global_price) / global_price) * 100, 2)
                
                kimchi_data.append({
                    'symbol': symbol,
                    'korean_exchange': 'Upbit',
                    'global_exchange': 'OKX',
                    'korean_price': korean_price,
                    'global_price': global_price,
                    'premium_percentage': premium,
                    'status': 'positive' if premium > 0 else 'negative'
                })
            
            # 데이터 전송
            connection_count = len(connection_manager.active_connections)
            
            # 가격 데이터 전송
            await connection_manager.broadcast({
                "type": "price_update",
                "data": price_data,
                "timestamp": datetime.now().isoformat()
            })
            
            # 김치 프리미엄 데이터 전송
            await connection_manager.broadcast({
                "type": "kimchi_premium",
                "data": kimchi_data,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": f"{connection_count}개 연결에 테스트 데이터 전송 완료",
                "active_connections": connection_count,
                "data_sent": {
                    "prices": len(price_data),
                    "kimchi_premiums": len(kimchi_data)
                }
            }
        
    else:
        logger.warning(f"Frontend 디렉토리를 찾을 수 없습니다: {frontend_dir}")
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
    
    # Prometheus metrics 등록 (FastAPI 0.104+ 호환)
    # try:
    #     Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    #     logger.info("Prometheus Instrumentator 미들웨어 등록 완료")
    # except Exception as e:
    #     logger.error(f"Instrumentator 미들웨어 등록 실패: {e}")
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """서버 시작 시 실시간 데이터 수집 활성화"""
        try:
            logger.info("Starting Dantaro Central API server (real-time mode)...")
            
            # 거래량 기반 모드 환경 변수 설정
            os.environ['DANTARO_MODE'] = 'volume_based'
            
            # 코인 최대 개수와 메모리 설정
            os.environ['MAX_SYMBOLS'] = '100'
            os.environ['DATA_RETENTION_MINUTES'] = '10'
            
            logger.info("🔄 볼륨 기반 코인 추천 모드 활성화")
            logger.info("📊 전체 코인을 대상으로 거래량 상위 코인을 선별하고, 단타 거래 적합성을 평가합니다")
            
            # 데이터베이스 연결 확인
            try:
                recommendations = db_manager.get_latest_recommendations(limit=1)
                logger.info(f"Database connection OK - {len(recommendations)} recommendations available")
            except Exception as e:
                logger.warning(f"Database connection issue: {e}")
            
            # Redis 연결 확인
            try:
                redis_healthy = redis_manager.health_check()
                if redis_healthy:
                    logger.info("Redis connection OK")
                else:
                    logger.warning("Redis connection issue")
            except Exception as e:
                logger.warning(f"Redis connection issue: {e}")
                
            # 실시간 데이터 수집 시작
            from app.tasks.market_analyzer import start_background_tasks, market_analyzer
            
            # 기존 워커 상태 초기화
            try:
                redis_manager.set_worker_status('market_analyzer_main', {
                    'is_running': False,
                    'last_heartbeat': datetime.utcnow().isoformat(),
                    'status': 'initializing',
                    'start_time': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to reset worker status: {e}")
            
            logger.info("🚀 Starting real-time market data collection...")
            try:
                # 백그라운드 작업 실행 상태 확인 및 재시작
                if not market_analyzer.is_running:
                    logger.info("🔄 Market analyzer not running, starting now...")
                    
                    # 워커 상태 업데이트
                    redis_manager.set_worker_status('market_analyzer_main', {
                        'is_running': True,
                        'last_heartbeat': datetime.utcnow().isoformat(),
                        'status': 'starting',
                        'app_server': 'main_fastapi_process'
                    })
                    
                    # 백그라운드 작업 시작
                    background_task = asyncio.create_task(start_background_tasks())
                    app.state.background_task = background_task
                    
                    # 작업이 시작되었는지 확인 (타임아웃 증가)
                    await asyncio.wait_for(asyncio.shield(asyncio.gather(
                        # 작업 자체는 계속 실행되도록 shield 사용
                        asyncio.create_task(asyncio.sleep(5))
                    )), timeout=5)
                    
                    # 워커 상태 다시 확인하고 업데이트
                    if market_analyzer.is_running:
                        logger.info(f"✅ Real-time data collection started and verified (is_running={market_analyzer.is_running})")
                        redis_manager.set_worker_status('market_analyzer_main', {
                            'is_running': True,
                            'last_heartbeat': datetime.utcnow().isoformat(),
                            'status': 'running',
                            'app_server': 'main_fastapi_process',
                            'verification': 'successful'
                        })
                    else:
                        logger.warning(f"⚠️ Market analyzer not showing as running despite task start (is_running={market_analyzer.is_running})")
                        redis_manager.set_worker_status('market_analyzer_main', {
                            'is_running': False,
                            'last_heartbeat': datetime.utcnow().isoformat(),
                            'status': 'failed_to_start',
                            'app_server': 'main_fastapi_process',
                            'verification': 'failed'
                        })
                else:
                    logger.info(f"✓ Market analyzer already running (is_running={market_analyzer.is_running})")
                    redis_manager.set_worker_status('market_analyzer_main', {
                        'is_running': True,
                        'last_heartbeat': datetime.utcnow().isoformat(),
                        'status': 'already_running',
                        'app_server': 'main_fastapi_process'
                    })
                
                # 상태에 관계없이 강제로 첫 분석 실행
                first_analysis_task = asyncio.create_task(market_analyzer.run_analysis_cycle())
                app.state.first_analysis_task = first_analysis_task
                logger.info("✅ First analysis cycle triggered manually")
                
                # 분석 작업 상태 업데이트
                redis_manager.set_worker_status('first_analysis_cycle', {
                    'is_running': True,
                    'last_heartbeat': datetime.utcnow().isoformat(),
                    'status': 'running',
                    'app_server': 'main_fastapi_process'
                })
                
            except asyncio.TimeoutError:
                logger.warning("⚠️ Real-time data collection started but verification timed out")
            except Exception as e:
                logger.error(f"❌ Error starting real-time data collection: {e}", exc_info=True)
            
            # WebSocket 매니저 초기화
            from app.api.v1.endpoints.websocket import connection_manager
            app.state.websocket_manager = connection_manager
            logger.info("✅ WebSocket manager initialized")
            
            # 실제 데이터 서비스 초기화
            try:
                from app.services.real_data_service import backend_real_data_service
                await backend_real_data_service.initialize_exchanges()
                logger.info("✅ 실제 데이터 서비스 초기화 완료")
            except Exception as e:
                logger.error(f"❌ 실제 데이터 서비스 초기화 실패: {e}")
            
            # WebSocket 실시간 데이터 수집 시작
            try:
                from app.services.websocket_data_manager import MultiExchangeWebSocketManager
                
                # WebSocket 매니저 초기화
                websocket_manager = MultiExchangeWebSocketManager()
                
                # 거래소별 설정 (API 키 없이도 공개 데이터 수집 가능)
                exchange_configs = {
                    'upbit': {},  # 공개 데이터 - API 키 불필요
                    'okx': {},    # 공개 데이터 - API 키 불필요  
                    'coinone': {},  # 공개 데이터 - API 키 불필요
                    'gate': {}    # 공개 데이터 - API 키 불필요
                }
                
                # WebSocket 클라이언트 초기화
                await websocket_manager.initialize_websockets(exchange_configs)
                
                # 주요 코인들 구독 시작
                main_symbols = [
                    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'XRP/USDT',
                    'DOT/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT', 'LTC/USDT'
                ]
                
                krw_symbols = [
                    'KRW-BTC', 'KRW-ETH', 'KRW-SOL', 'KRW-ADA', 'KRW-XRP',
                    'KRW-DOT', 'KRW-AVAX', 'KRW-LINK', 'KRW-UNI', 'KRW-LTC'
                ]
                
                # 거래소별 구독
                await websocket_manager.subscribe_tickers(['upbit'], krw_symbols)
                await websocket_manager.subscribe_tickers(['okx'], main_symbols)
                
                # WebSocket 매니저 시작
                await websocket_manager.start()
                
                # 상태 저장
                app.state.realtime_websocket_manager = websocket_manager
                logger.info("✅ 실시간 WebSocket 데이터 수집 시작됨")
                
            except Exception as e:
                logger.error(f"❌ WebSocket 실시간 데이터 수집 시작 실패: {e}")
            
            logger.info("✅ Dantaro Central API server started successfully (real-time mode)")
            logger.info("📊 서버는 이제 거래량 기반 실시간 데이터 수집 및 분석을 수행합니다")
            
        except Exception as e:
            logger.error(f"Startup failed: {e}", exc_info=True)
    
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
