"""
Health monitoring and metrics for Dantaro Central.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil
import logging

from app.database.manager import db_manager
from app.database.redis_cache import redis_manager


class HealthMonitor:
    """시스템 상태 모니터링."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
    
    def get_system_health(self) -> Dict:
        """전체 시스템 상태 확인."""
        try:
            health_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': time.time() - self.start_time,
                'database': self._check_database_health(),
                'cache': self._check_cache_health(),
                'workers': self._check_worker_health(),
                'system_resources': self._check_system_resources(),
                'data_freshness': self._check_data_freshness(),
                'overall_status': 'healthy'
            }
            
            # 전체 상태 결정
            if any(status.get('status') == 'error' for status in [
                health_status['database'], 
                health_status['cache']
            ]):
                health_status['overall_status'] = 'unhealthy'
            elif any(status.get('status') == 'warning' for status in [
                health_status['database'], 
                health_status['cache'],
                health_status['data_freshness']
            ]):
                health_status['overall_status'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _check_database_health(self) -> Dict:
        """데이터베이스 상태 확인."""
        try:
            start_time = time.time()
            recommendations = db_manager.get_latest_recommendations(limit=1)
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2),
                'recommendations_available': len(recommendations),
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def _check_cache_health(self) -> Dict:
        """캐시 상태 확인."""
        try:
            start_time = time.time()
            cache_healthy = redis_manager.health_check()
            response_time = time.time() - start_time
            
            cache_stats = redis_manager.get_cache_stats()
            
            return {
                'status': 'healthy' if cache_healthy else 'error',
                'response_time_ms': round(response_time * 1000, 2),
                'stats': cache_stats,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def _check_worker_health(self) -> Dict:
        """워커 상태 확인."""
        try:
            worker_statuses = redis_manager.get_all_worker_status()
            active_workers = []
            inactive_workers = []
            
            now = datetime.utcnow()
            
            # 실시간 배경 작업자 존재 여부 확인
            has_market_analyzer = False
            
            for worker_id, status in worker_statuses.items():
                if worker_id == 'market_analyzer_main':
                    has_market_analyzer = True
                
                last_heartbeat = status.get('last_heartbeat')
                if last_heartbeat:
                    try:
                        heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                        time_diff = (now - heartbeat_time.replace(tzinfo=None)).total_seconds()
                        
                        if time_diff < 120:  # 2분 이내
                            active_workers.append({
                                'worker_id': worker_id,
                                'last_heartbeat': last_heartbeat,
                                'is_running': status.get('is_running', False),
                                'uptime_seconds': status.get('uptime_seconds', 0),
                                'stats': status.get('stats', {})
                            })
                        else:
                            inactive_workers.append({
                                'worker_id': worker_id,
                                'last_heartbeat': last_heartbeat,
                                'time_since_heartbeat': time_diff
                            })
                    except Exception as e:
                        inactive_workers.append({
                            'worker_id': worker_id,
                            'error': f'Invalid heartbeat timestamp: {str(e)}'
                        })
            
            # 시장 분석기가 없으면 기본 분석기 상태 확인
            if not has_market_analyzer:
                self.logger.warning("No market_analyzer_main worker found in Redis. Checking for background task...")
                import asyncio
                import inspect
                from app.main import app
                
                # FastAPI 앱의 상태에서 백그라운드 태스크 확인
                if hasattr(app, 'state') and hasattr(app.state, 'background_task'):
                    task = app.state.background_task
                    if task and not task.done() and not task.cancelled():
                        self.logger.info("Found active background task in app.state")
                        active_workers.append({
                            'worker_id': 'background_task_from_state',
                            'last_heartbeat': datetime.utcnow().isoformat(),
                            'is_running': True
                        })
            
            status = 'healthy'
            if len(active_workers) == 0:
                status = 'error'
            elif len(inactive_workers) > 0:
                status = 'warning'
            
            return {
                'status': status,
                'active_count': len(active_workers),
                'inactive_count': len(inactive_workers),
                'status': f"{len(active_workers)} active workers",
                'workers': active_workers,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def _check_system_resources(self) -> Dict:
        """시스템 리소스 상태 확인."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory': {
                    'used_percent': memory.percent,
                    'available_gb': round(memory.available / (1024**3), 2),
                    'total_gb': round(memory.total / (1024**3), 2)
                },
                'disk': {
                    'used_percent': disk.percent,
                    'free_gb': round(disk.free / (1024**3), 2),
                    'total_gb': round(disk.total / (1024**3), 2)
                },
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def _check_data_freshness(self) -> Dict:
        """데이터 신선도 확인."""
        try:
            # 추천 데이터 신선도
            recommendations = db_manager.get_latest_recommendations(limit=1)
            market_status = db_manager.get_market_status()
            
            now = datetime.utcnow()
            status = 'healthy'
            issues = []
            
            # 추천 데이터 확인
            if recommendations:
                rec_time = datetime.fromisoformat(recommendations[0]['updated_at'].replace('Z', ''))
                rec_age = (now - rec_time).total_seconds()
                if rec_age > 900:  # 15분 초과
                    status = 'warning'
                    issues.append(f"Recommendations are {rec_age/60:.1f} minutes old")
            else:
                status = 'error'
                issues.append("No recommendations available")
            
            # 시장 상태 확인
            if market_status:
                market_time = datetime.fromisoformat(market_status['updated_at'].replace('Z', ''))
                market_age = (now - market_time).total_seconds()
                if market_age > 300:  # 5분 초과
                    if status != 'error':
                        status = 'warning'
                    issues.append(f"Market status is {market_age/60:.1f} minutes old")
            else:
                status = 'error'
                issues.append("No market status available")
            
            return {
                'status': status,
                'issues': issues,
                'recommendations_count': len(recommendations),
                'market_status_available': market_status is not None,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }


# 글로벌 모니터 인스턴스
health_monitor = HealthMonitor()
