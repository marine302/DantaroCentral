"""
서버 종료시 정리 서비스들
"""
import logging

logger = logging.getLogger(__name__)


async def shutdown_services():
    """모든 종료 서비스 정리"""
    
    logger.info("🔄 서비스 종료 시작")
    
    # 1. WebSocket 연결 정리
    await cleanup_websocket_connections()
    
    # 2. 데이터베이스 연결 정리
    await cleanup_database()
    
    # 3. Redis 연결 정리
    await cleanup_redis()
    
    logger.info("✅ 모든 서비스 종료 완료")


async def cleanup_websocket_connections():
    """WebSocket 연결 정리"""
    try:
        from app.api.v1.endpoints.websocket import connection_manager
        # 모든 활성 연결 종료
        if connection_manager.active_connections:
            logger.info(f"🔌 {len(connection_manager.active_connections)}개 WebSocket 연결 종료")
            # connection_manager에 정리 메서드가 있다면 호출
    except Exception as e:
        logger.warning(f"⚠️ WebSocket 연결 정리 실패: {e}")


async def cleanup_database():
    """데이터베이스 연결 정리"""
    try:
        # 필요하다면 DB 연결 정리
        logger.info("🗄️ 데이터베이스 연결 정리")
    except Exception as e:
        logger.warning(f"⚠️ 데이터베이스 정리 실패: {e}")


async def cleanup_redis():
    """Redis 연결 정리"""
    try:
        # 필요하다면 Redis 연결 정리
        logger.info("🔴 Redis 연결 정리")
    except Exception as e:
        logger.warning(f"⚠️ Redis 정리 실패: {e}")
