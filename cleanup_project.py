#!/usr/bin/env python3
"""
DantaroCentral 프로젝트 클린업 스크립트
불필요한 파일들과 중복 파일들을 정리합니다.
"""
import os
import sys
import shutil
from pathlib import Path

def cleanup_project():
    """프로젝트 정리 작업 수행"""
    project_root = Path(__file__).parent
    
    print("🧹 DantaroCentral 프로젝트 클린업 시작...")
    
    # 정리할 파일 패턴들
    cleanup_patterns = [
        # 루트 디렉토리의 임시/테스트 파일들
        "test_*.py",
        "quick_*.py", 
        "simple_*.py",
        "client_test.py",
        "compatibility_test.py",
        "send_test_data.py",
        "view_*.py",
        "usage_example.py",
        "enterprise_examples.py",
        "enterprise_usage_examples.py",
        "dantaro_enterprise_integration.py",
        "dantaro_integration.py",
        
        # 백엔드 디렉토리의 임시/테스트 파일들
        "backend/test_*.py",
        "backend/quick_*.py",
        "backend/debug_*.py",
        "backend/diagnostic_*.py",
        "backend/websocket_*.py", 
        "backend/ws_*.py",
        "backend/simple_*.py",
        "backend/minimal_server.py",
        "backend/standard_server.py",
        "backend/api_test.py",
        "backend/performance_test.py",
        "backend/activate_websockets.py",
        "backend/apply_optimizations.py",
        "backend/check_env_status.py",
        "backend/cleanup_and_finalize.py",
        "backend/dashboard_monitor.py",
        "backend/run_realtime_service.py",
        "backend/save_test_results.py",
        "backend/setup_production_keys.py",
        "backend/verify_realtime_system.py",
        
        # 로그 파일들
        "backend/worker-*.log",
        "backend/logs/*.log",
        "logs/*.log",
        
        # HTML 테스트 파일들
        "*.html",
        "backend/*.html"
    ]
    
    # 보존할 중요 파일들 (실수로 삭제 방지)
    preserve_files = [
        "README.md",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "frontend/templates/*.html",
        "test_api_call.html"  # API 테스트용 유지
    ]
    
    total_removed = 0
    
    for pattern in cleanup_patterns:
        if "/" in pattern:
            # 하위 디렉토리 패턴
            base_dir = project_root / pattern.split("/")[0]
            file_pattern = pattern.split("/")[1]
        else:
            # 루트 디렉토리 패턴
            base_dir = project_root
            file_pattern = pattern
            
        if base_dir.exists():
            for file_path in base_dir.glob(file_pattern):
                # 보존 파일 체크
                should_preserve = False
                for preserve in preserve_files:
                    if preserve in str(file_path):
                        should_preserve = True
                        break
                        
                if not should_preserve and file_path.is_file():
                    print(f"🗑️  제거: {file_path.relative_to(project_root)}")
                    file_path.unlink()
                    total_removed += 1
    
    print(f"\n✅ 정리 완료! {total_removed}개 파일 제거됨")
    
    # 빈 디렉토리 정리
    empty_dirs = []
    for root, dirs, files in os.walk(project_root):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            if not any(dir_path.iterdir()) and "venv" not in str(dir_path) and ".git" not in str(dir_path):
                empty_dirs.append(dir_path)
    
    for empty_dir in empty_dirs:
        print(f"📁 빈 디렉토리 제거: {empty_dir.relative_to(project_root)}")
        empty_dir.rmdir()
    
    print(f"\n🎉 프로젝트 클린업 완료!")

if __name__ == "__main__":
    cleanup_project()
