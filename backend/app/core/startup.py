"""
서버 시작시 초기화 서비스들
기존 main.py의 startup 로직을 분리
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def startup_services():
    """모든 시작 서비스 초기화"""
    
    logger.info("🔧 서비스 초기화 시작")
    
    # 1. 데이터베이스 초기화
    await init_database()
    
    # 2. Redis 캐시 초기화  
    await init_redis()
    
    # 3. WebSocket 매니저 초기화
    await init_websocket_manager()
    
    # 4. 실제 데이터 서비스 초기화
    await init_real_data_service()
    
    # 5. 코인 추천 시스템 초기화
    await init_coin_recommender()
    
    logger.info("✅ 모든 서비스 초기화 완료")


async def init_database():
    """데이터베이스 초기화"""
    try:
        from app.database.manager import db_manager
        await db_manager.initialize()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.warning(f"⚠️ 데이터베이스 초기화 실패: {e}")


async def init_redis():
    """Redis 캐시 초기화"""
    try:
        from app.database.redis_cache import redis_manager
        await redis_manager.initialize()
        logger.info("✅ Redis 캐시 초기화 완료")
    except Exception as e:
        logger.warning(f"⚠️ Redis 초기화 실패: {e}")


async def init_websocket_manager():
    """WebSocket 매니저 초기화"""
    try:
        from app.api.v1.endpoints.websocket import connection_manager
        # 매니저는 이미 초기화되어 있으므로 상태만 확인
        logger.info(f"✅ WebSocket 매니저 준비 완료 (연결: {len(connection_manager.active_connections)}개)")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket 매니저 초기화 실패: {e}")


async def init_real_data_service():
    """실제 데이터 서비스 초기화"""
    try:
        # 새로운 클린 서비스 테스트
        from app.services.real_data_service import backend_real_data_service
        
        # 간단한 테스트 수집
        async with backend_real_data_service as service:
            test_data = await service.get_market_data_only()
            data_count = len(test_data) if test_data else 0
            
        logger.info(f"✅ 실제 데이터 서비스 준비 완료 (테스트 데이터: {data_count}개)")
        
    except Exception as e:
        logger.warning(f"⚠️ 실제 데이터 서비스 초기화 실패: {e}")


async def init_coin_recommender():
    """코인 추천 시스템 초기화"""
    try:
        from app.domain.recommenders.coin_recommender import coin_recommender
        
        # 백그라운드 태스크로 추천 데이터 갱신 시작
        asyncio.create_task(coin_recommender.start_background_update())
        
        logger.info("✅ 코인 추천 시스템 초기화 완료 (백그라운드 갱신 시작)")
        
    except Exception as e:
        logger.warning(f"⚠️ 코인 추천 시스템 초기화 실패: {e}")

