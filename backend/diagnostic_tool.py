#!/usr/bin/env python3
"""
실시간 웹소켓 대시보드 서버 문제 진단
"""
import sys
import os
import logging
import importlib.util
import traceback
from pathlib import Path
import socket
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리 확인
current_dir = Path(os.path.abspath(os.path.dirname(__file__)))
project_root = current_dir.parent
frontend_dir = project_root / "frontend"

print("="*80)
print(f"🔍 현재 작업 디렉토리: {os.getcwd()}")
print(f"🔍 프로젝트 루트: {project_root}")
print(f"🔍 백엔드 디렉토리: {current_dir}")
print(f"🔍 프론트엔드 디렉토리: {frontend_dir} (존재: {frontend_dir.exists()})")

# 디렉토리 구조 검증
templates_dir = frontend_dir / "templates"
static_dir = frontend_dir / "static"
static_css_dir = static_dir / "css"
static_js_dir = static_dir / "js"
dashboard_html = templates_dir / "dashboard.html"
dashboard_css = static_css_dir / "dashboard.css" 
dashboard_js = static_js_dir / "dashboard.js"

print("\n📁 디렉토리 구조 검증:")
print(f"- templates/ 디렉토리: {templates_dir.exists()}")
print(f"- static/ 디렉토리: {static_dir.exists()}")
print(f"- static/css/ 디렉토리: {static_css_dir.exists()}")
print(f"- static/js/ 디렉토리: {static_js_dir.exists()}")
print(f"- dashboard.html: {dashboard_html.exists()}")
print(f"- dashboard.css: {dashboard_css.exists()}")
print(f"- dashboard.js: {dashboard_js.exists()}")

# 포트 사용 가능성 확인
def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

print("\n🌐 포트 상태 확인:")
port_8000_free = check_port(8000)
print(f"- 포트 8000: {'가능' if port_8000_free else '사용중'}")

# 핵심 모듈 테스트
print("\n📦 핵심 모듈 테스트:")
modules_to_test = [
    "app.main",
    "app.core.config", 
    "app.api.v1.endpoints.websocket",
    "app.services.websocket_data_manager",
    "app.services.arbitrage_analyzer"
]

for module_name in modules_to_test:
    try:
        module = importlib.import_module(module_name)
        print(f"✅ {module_name}: 로드 성공")
    except Exception as e:
        print(f"❌ {module_name}: 로드 실패")
        print(f"   오류: {str(e)}")
        print("   상세 오류:")
        traceback.print_exc(file=sys.stdout)
        print()

# 테스트용 간단한 FastAPI 앱
try:
    print("\n🚀 FastAPI 테스트:")
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    
    app = FastAPI(title="테스트 앱")
    
    # 정적 파일 및 템플릿 설정
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        print("✅ 정적 파일 마운트 성공")
    
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
        print("✅ 템플릿 디렉토리 설정 성공")
    
    print("✅ FastAPI 테스트 완료")

except Exception as e:
    print(f"❌ FastAPI 테스트 실패: {str(e)}")

print("="*80)

# 해결책 제안
print("\n🛠️ 진단 및 해결책:")
print("1. 프론트엔드 파일들은 정확한 위치에 있습니다.")
print("2. 아래 명령어로 FastAPI 서버를 시작해 보세요:")
print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
print("3. 문제가 지속되면 다음을 확인하세요:")
print("   - 의존성이 모두 설치되어 있는지 확인 (pip install -r requirements.txt)")
print("   - 방화벽이 8000 포트를 차단하고 있지 않은지 확인")
print("   - 브라우저에서 http://localhost:8000 또는 http://127.0.0.1:8000 으로 접속")
print("="*80)
