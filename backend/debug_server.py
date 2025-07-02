#!/usr/bin/env python3
"""
FastAPI 서버 디버깅을 위한 스크립트
"""

import os
import sys

# 로깅 설정
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 경로 확인 및 출력
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
frontend_dir = os.path.join(project_root, "frontend")

print("="*80)
print(f"Backend 디렉토리: {backend_dir}")
print(f"프로젝트 루트: {project_root}")
print(f"Frontend 디렉토리: {frontend_dir}")
print(f"Frontend 존재 여부: {os.path.exists(frontend_dir)}")

# 필수 경로가 있는지 확인
templates_dir = os.path.join(frontend_dir, "templates")
static_dir = os.path.join(frontend_dir, "static")
print(f"Templates 디렉토리 존재: {os.path.exists(templates_dir)}")
print(f"Static 디렉토리 존재: {os.path.exists(static_dir)}")

dashboard_html = os.path.join(templates_dir, "dashboard.html")
print(f"Dashboard HTML 존재: {os.path.exists(dashboard_html)}")

# FastAPI 앱을 직접 가져와서 모든 라우트 출력
try:
    from app.main import app
    print("\n✅ FastAPI 앱 임포트 성공")
    
    print("\n🛣️ 등록된 라우트:")
    for route in app.routes:
        print(f" - {route.path} [{', '.join(route.methods) if hasattr(route, 'methods') else 'WebSocket'}]")
    
except Exception as e:
    print(f"\n❌ FastAPI 앱 로딩 실패: {str(e)}")
    import traceback
    traceback.print_exc()
    
print("="*80)
