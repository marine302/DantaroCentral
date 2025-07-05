"""
데이터 방송/스트리밍 관련 API 엔드포인트
"""

import asyncio
import logging
from datetime import datetime
from fastapi.routing import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# 실제 데이터 서비스 import 추가
try:
    from app.services.real_data_service import backend_real_data_service
    real_data_service = backend_real_data_service
    logger.info("백엔드 실제 데이터 서비스 로드됨")
except ImportError as e:
    real_data_service = None
    logger.warning(f"실제 데이터 서비스를 로드할 수 없습니다: {e}")


@router.post("/api/websocket/broadcast-real-data")
async def broadcast_real_data():
    """실제 거래소 데이터 수집 및 브로드캐스트"""
    # connection_manager를 realtime에서 import
    from .realtime import connection_manager
    
    try:
        if not connection_manager.active_connections:
            return {"success": False, "message": "활성 WebSocket 연결이 없습니다"}
        
        # 실제 데이터 서비스를 통한 데이터 수집 및 브로드캐스트
        if real_data_service:
            result = await real_data_service.collect_and_send_real_data()
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"실제 거래소 데이터를 {len(connection_manager.active_connections)}개 연결에 브로드캐스트 완료",
                    "active_connections": len(connection_manager.active_connections),
                    "data_points": result.get("data_points", 0),
                    "kimchi_premiums": result.get("kimchi_premiums", 0),
                    "timestamp": result.get("timestamp"),
                    "source": "real_exchange_apis"
                }
            else:
                return {
                    "success": False,
                    "message": result.get("error", "데이터 수집 실패"),
                    "active_connections": len(connection_manager.active_connections)
                }
        else:
            return {"success": False, "message": "실제 데이터 서비스가 초기화되지 않았습니다"}
            
    except Exception as e:
        logger.error(f"실제 데이터 브로드캐스트 오류: {e}")
        return {"success": False, "message": f"오류: {str(e)}"}


@router.post("/api/websocket/start-real-data-stream")
async def start_real_data_stream():
    """실제 데이터 스트림 시작"""
    try:
        if real_data_service and not real_data_service.running:
            # 실제 데이터 서비스 초기화 및 시작
            await real_data_service.initialize_exchanges()
            
            # 백그라운드 태스크로 데이터 수집 루프 시작
            asyncio.create_task(real_data_service.start_collection_loop())
            
            return {
                "success": True,
                "message": "실제 거래소 데이터 스트림 시작",
                "active_exchanges": real_data_service.stats['active_exchanges'],
                "collection_interval": real_data_service.collection_interval
            }
        elif real_data_service and real_data_service.running:
            return {
                "success": True,
                "message": "실제 데이터 스트림이 이미 실행 중입니다",
                "stats": real_data_service.stats
            }
        else:
            return {"success": False, "message": "실제 데이터 서비스를 로드할 수 없습니다"}
            
    except Exception as e:
        logger.error(f"실제 데이터 스트림 시작 오류: {e}")
        return {"success": False, "message": f"오류: {str(e)}"}


@router.post("/api/websocket/stop-real-data-stream")
async def stop_real_data_stream():
    """실제 데이터 스트림 중지"""
    try:
        if real_data_service:
            real_data_service.stop()
            return {
                "success": True,
                "message": "실제 거래소 데이터 스트림 중지",
                "final_stats": real_data_service.stats
            }
        else:
            return {"success": False, "message": "실제 데이터 서비스가 로드되지 않았습니다"}
            
    except Exception as e:
        logger.error(f"실제 데이터 스트림 중지 오류: {e}")
        return {"success": False, "message": f"오류: {str(e)}"}


@router.get("/api/websocket/real-data-stats")
async def get_real_data_stats():
    """실제 데이터 서비스 통계"""
    try:
        if real_data_service:
            stats = real_data_service.get_stats()
            return {
                "success": True,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "실제 데이터 서비스를 사용할 수 없습니다",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"실제 데이터 통계 조회 오류: {e}")
        return {
            "success": False,
            "message": f"오류: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
