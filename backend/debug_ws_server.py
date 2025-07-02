#!/usr/bin/env python3
"""
WebSocket 연결 문제 디버깅을 위한 최소화된 서버
"""
import asyncio
import uvicorn
import logging
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# 디렉토리 설정
current_dir = Path(os.path.abspath(os.path.dirname(__file__)))
project_root = current_dir.parent
frontend_dir = project_root / "frontend"
static_dir = frontend_dir / "static"
templates_dir = frontend_dir / "templates"

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정 - 모든 출처 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 템플릿
templates = Jinja2Templates(directory=str(templates_dir))

# 대시보드 라우트
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# 활성 WebSocket 연결 추적
active_connections = []

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """테스트용 WebSocket 엔드포인트"""
    # 디버그 정보 출력
    print("="*80)
    print("✨ WebSocket 연결 시도 감지")
    print(f"✓ 클라이언트: {websocket.client}")
    print(f"✓ 경로: {websocket.url.path}")
    print(f"✓ 헤더: {dict(websocket.headers)}")
    print("="*80)
    
    # 연결 수락
    await websocket.accept()
    print("✅ WebSocket 연결 수락됨")
    active_connections.append(websocket)
    
    # 초기 메시지 전송
    await websocket.send_json({
        "type": "welcome",
        "message": "디버그 WebSocket 서버에 연결되었습니다",
        "timestamp": datetime.now().isoformat()
    })
    print("📨 환영 메시지 전송됨")
    
    # 테스트용 데이터 전송
    count = 0
    try:
        while True:
            count += 1
            now = datetime.now().isoformat()
            
            # 10초마다 테스트 메시지 전송
            if count % 10 == 0:
                # 가격 데이터
                price_data = {
                    "BTC": {
                        "Upbit": 40000000 + count * 1000,
                        "OKX": 39500000 + count * 800
                    },
                    "ETH": {
                        "Upbit": 2500000 + count * 500,
                        "OKX": 2450000 + count * 400
                    }
                }
                
                await websocket.send_json({
                    "type": "realtime_data",
                    "data": price_data,
                    "timestamp": now
                })
                print(f"📊 테스트 데이터 #{count} 전송됨")
            
            # 메시지 수신 대기 (비동기)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                print(f"📥 클라이언트로부터 메시지 수신: {data[:50]}...")
                
                # 간단한 응답
                await websocket.send_json({
                    "type": "echo",
                    "message": f"메시지 수신됨: {data[:20]}...",
                    "timestamp": now
                })
                
            except asyncio.TimeoutError:
                # 타임아웃은 정상적인 상황
                pass
            
            # 잠시 대기
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ WebSocket 오류: {str(e)}")
    finally:
        # 연결 목록에서 제거
        if websocket in active_connections:
            active_connections.remove(websocket)
        print("❌ WebSocket 연결 종료")

# 연결 테스트용 엔드포인트
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "connections": len(active_connections),
        "time": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print(f"🚀 디버그 서버 시작")
    print(f"✓ 프론트엔드 경로: {frontend_dir}")
    print(f"✓ 템플릿 경로: {templates_dir}")
    print(f"✓ 정적 파일 경로: {static_dir}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
