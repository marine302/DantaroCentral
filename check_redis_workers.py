"""
Redis 워커 상태 직접 확인 스크립트
"""
import sys
import os
import time
import asyncio
import json

# 환경 설정
os.environ['DATABASE_URL'] = 'sqlite:///./dantaro_central.db'
sys.path.insert(0, os.path.abspath('backend'))

try:
    from app.database.redis_cache import redis_manager
    print("✅ Redis 매니저 로드 성공")
except ImportError as e:
    print(f"❌ 모듈 로드 실패: {e}")
    sys.exit(1)

def check_redis_worker_status():
    """Redis에 저장된 워커 상태 확인"""
    print("\n===== Redis 워커 상태 확인 =====")
    
    try:
        # 모든 워커 상태 조회
        worker_statuses = redis_manager.get_all_worker_status()
        
        if not worker_statuses:
            print("❌ Redis에 등록된 워커가 없습니다.")
            return
        
        print(f"✅ Redis에서 {len(worker_statuses)}개의 워커 상태를 발견했습니다:")
        
        for worker_id, status in worker_statuses.items():
            print(f"\n워커 ID: {worker_id}")
            print(f"  - 실행 상태: {status.get('is_running', 'unknown')}")
            print(f"  - 마지막 하트비트: {status.get('last_heartbeat', 'unknown')}")
            print(f"  - 상태: {status.get('status', 'unknown')}")
            print(f"  - 서버: {status.get('app_server', 'unknown')}")
            
            if 'stats' in status:
                print(f"  - 통계:")
                stats = status['stats']
                for key, value in stats.items():
                    print(f"    * {key}: {value}")
                    
    except Exception as e:
        print(f"❌ Redis 워커 상태 확인 실패: {e}")

def check_redis_health():
    """Redis 연결 상태 확인"""
    print("\n===== Redis 연결 상태 확인 =====")
    
    try:
        health = redis_manager.health_check()
        print(f"✅ Redis 연결 상태: {'정상' if health else '오류'}")
        
        # 캐시 통계 확인
        stats = redis_manager.get_cache_stats()
        print(f"✅ 캐시 통계:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
            
    except Exception as e:
        print(f"❌ Redis 연결 확인 실패: {e}")

if __name__ == "__main__":
    check_redis_health()
    check_redis_worker_status()
    
    print("\n===== 완료 =====")
    print("Redis에 워커 상태가 저장되어 있다면 백그라운드 작업이 실행 중입니다.")
    print("워커가 없다면 백그라운드 작업 시작에 문제가 있을 수 있습니다.")
