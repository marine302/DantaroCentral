"""
Admin API endpoints for system monitoring and management.
"""
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import psutil
import time
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# 어드민 인증 (간단한 API 키 방식)
ADMIN_API_KEY = "dantaro-admin-2024"  # 실제 운영시에는 환경변수로 관리

async def verify_admin_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """어드민 API 키 검증"""
    if credentials.credentials != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key"
        )
    return True


@router.get(
    "/system-status",
    summary="Get overall system status",
    description="Get comprehensive system health and performance metrics"
)
async def get_system_status(
    admin_auth: bool = Depends(verify_admin_key)
) -> Dict[str, Any]:
    """
    시스템 전체 상태 조회
    
    Returns:
        - 서버 리소스 사용률
        - 서비스 상태
        - 업타임 정보
    """
    try:
        # 시스템 리소스 정보
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 네트워크 정보
        network = psutil.net_io_counters()
        
        # 프로세스 정보
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            },
            "application": {
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "process_cpu_percent": process.cpu_percent(),
                "uptime_seconds": time.time() - process.create_time(),
                "environment": settings.environment,
                "project_name": settings.project_name
            }
        }
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 상태 조회 중 오류: {str(e)}")


@router.get(
    "/exchange-status",
    summary="Get exchange connection status",
    description="Get status of all exchange connections and WebSocket streams"
)
async def get_exchange_status(
    admin_auth: bool = Depends(verify_admin_key)
) -> Dict[str, Any]:
    """
    거래소 연결 상태 조회
    
    Returns:
        - 각 거래소별 연결 상태
        - WebSocket 연결 정보
        - 마지막 데이터 수신 시간
    """
    try:
        # WebSocket 연결 관리자에서 상태 가져오기
        from app.api.v1.endpoints.websocket import connection_manager
        
        # 거래소별 상태 (mock 데이터 - 실제로는 각 거래소 모듈에서 상태 조회)
        exchanges = {
            "OKX": {
                "status": "connected",
                "websocket_active": True,
                "last_data_time": datetime.utcnow().isoformat(),
                "error_count": 0,
                "reconnect_count": 0
            },
            "Upbit": {
                "status": "connected", 
                "websocket_active": True,
                "last_data_time": datetime.utcnow().isoformat(),
                "error_count": 0,
                "reconnect_count": 1
            },
            "Coinone": {
                "status": "connected",
                "websocket_active": True,
                "last_data_time": datetime.utcnow().isoformat(),
                "error_count": 0,
                "reconnect_count": 0
            },
            "Gate.io": {
                "status": "connected",
                "websocket_active": False,  # REST only
                "last_data_time": datetime.utcnow().isoformat(),
                "error_count": 2,
                "reconnect_count": 0
            },
            "Bithumb": {
                "status": "disconnected",
                "websocket_active": False,
                "last_data_time": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "error_count": 5,
                "reconnect_count": 3
            },
            "Bybit": {
                "status": "connected",
                "websocket_active": False,  # REST only
                "last_data_time": datetime.utcnow().isoformat(),
                "error_count": 1,
                "reconnect_count": 0
            }
        }
        
        # WebSocket 통계
        ws_stats = connection_manager.get_stats()
        
        # 전체 통계 계산
        total_exchanges = len(exchanges)
        connected_exchanges = len([ex for ex in exchanges.values() if ex['status'] == 'connected'])
        websocket_active = len([ex for ex in exchanges.values() if ex['websocket_active']])
        total_errors = sum(ex['error_count'] for ex in exchanges.values())
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_exchanges": total_exchanges,
                "connected_exchanges": connected_exchanges,
                "websocket_active": websocket_active,
                "connection_rate": round((connected_exchanges / total_exchanges) * 100, 2),
                "total_error_count": total_errors
            },
            "exchanges": exchanges,
            "websocket": {
                "active_connections": ws_stats.get("active_connections", 0),
                "cached_prices": ws_stats.get("cached_prices", 0),
                "last_kimchi_premiums": ws_stats.get("last_kimchi_premiums", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"거래소 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"거래소 상태 조회 중 오류: {str(e)}")


@router.get(
    "/api-statistics",
    summary="Get API call statistics",
    description="Get statistics about API endpoint usage and performance"
)
async def get_api_statistics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to analyze (1-168)"),
    admin_auth: bool = Depends(verify_admin_key)
) -> Dict[str, Any]:
    """
    API 호출 통계 조회
    
    Args:
        hours: 분석할 시간 범위 (1-168시간)
        
    Returns:
        - 엔드포인트별 호출 통계
        - 응답 시간 분석
        - 에러율
    """
    try:
        # Mock 데이터 - 실제로는 로그 분석이나 메트릭 수집 시스템에서 가져와야 함
        endpoints_stats = {
            "/api/v1/top-coins-by-volume": {
                "total_calls": 1250,
                "success_calls": 1200,
                "error_calls": 50,
                "avg_response_time_ms": 150,
                "min_response_time_ms": 50,
                "max_response_time_ms": 2500,
                "error_rate_percent": 4.0
            },
            "/api/v1/recommendations": {
                "total_calls": 890,
                "success_calls": 885,
                "error_calls": 5,
                "avg_response_time_ms": 300,
                "min_response_time_ms": 200,
                "max_response_time_ms": 1200,
                "error_rate_percent": 0.56
            },
            "/ws/realtime": {
                "total_connections": 45,
                "active_connections": 12,
                "messages_sent": 15600,
                "connection_errors": 8,
                "avg_connection_duration_minutes": 25
            },
            "/api/v1/market-data/all": {
                "total_calls": 2100,
                "success_calls": 2050,
                "error_calls": 50,
                "avg_response_time_ms": 80,
                "min_response_time_ms": 30,
                "max_response_time_ms": 500,
                "error_rate_percent": 2.38
            }
        }
        
        # 전체 통계 계산
        total_calls = sum(stat.get('total_calls', 0) for stat in endpoints_stats.values())
        total_errors = sum(stat.get('error_calls', 0) for stat in endpoints_stats.values())
        overall_error_rate = (total_errors / total_calls * 100) if total_calls > 0 else 0
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "period": {
                "hours_analyzed": hours,
                "start_time": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
                "end_time": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_api_calls": total_calls,
                "total_errors": total_errors,
                "overall_error_rate_percent": round(overall_error_rate, 2),
                "endpoints_monitored": len(endpoints_stats)
            },
            "endpoints": endpoints_stats
        }
        
    except Exception as e:
        logger.error(f"API 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"API 통계 조회 중 오류: {str(e)}")
