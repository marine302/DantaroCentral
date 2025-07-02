#!/usr/bin/env python3
"""
Dantaro Central의 원래 서버 규격에 맞춘 테스트 서버
실시간 데이터를 생성하여 WebSocket을 통해 전송
"""
import os
import asyncio
import json
import random
import time
from pathlib import Path
from datetime import datetime
import logging

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 디렉토리 설정
current_dir = Path(os.path.abspath(os.path.dirname(__file__)))
project_root = current_dir.parent
frontend_dir = project_root / "frontend"
static_dir = frontend_dir / "static"
templates_dir = frontend_dir / "templates"

# 경로 출력
print(f"프로젝트 루트: {project_root}")
print(f"프론트엔드 디렉토리: {frontend_dir}")
print(f"정적 파일 디렉토리: {static_dir}")
print(f"템플릿 디렉토리: {templates_dir}")

# FastAPI 앱 생성
app = FastAPI(
    title="Dantaro Central 테스트 서버",
    description="차익거래 대시보드 테스트",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory=str(templates_dir))

# WebSocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ 새 연결 수락됨. 현재 연결 수: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"❌ 연결 종료. 현재 연결 수: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"메시지 전송 오류: {str(e)}")
                
manager = ConnectionManager()

# 라우트 설정
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """대시보드 페이지"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# 실시간 데이터 생성기
async def generate_realtime_data():
    """테스트용 실시간 데이터 생성"""
    # 테스트용 가상 거래소와 코인 목록
    exchanges = ["Upbit", "Coinone", "OKX", "Gate.io", "Binance"]
    coins = ["BTC", "ETH", "XRP", "SOL", "ADA", "MATIC", "DOT"]
    
    # 거래소별 초기 가격 설정 (비트코인 약 4천만원 기준)
    base_prices = {
        "BTC": 40000000,
        "ETH": 2500000,
        "XRP": 500,
        "SOL": 100000,
        "ADA": 400,
        "MATIC": 800,
        "DOT": 7000
    }
    
    # 거래소별 가격 초기화
    prices = {}
    for exchange in exchanges:
        prices[exchange] = {}
        for coin in coins:
            # 거래소별로 약간의 가격 차이 설정
            variation = random.uniform(0.97, 1.03)
            prices[exchange][coin] = base_prices[coin] * variation
    
    # 데이터 생성 및 전송 루프
    counter = 0
    while True:
        try:
            if not manager.active_connections:
                await asyncio.sleep(1)
                continue
                
            counter += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 가격 데이터 업데이트
            for exchange in exchanges:
                for coin in coins:
                    # 가격 변동 시뮬레이션 (±1%)
                    change = random.uniform(-0.01, 0.01)
                    prices[exchange][coin] *= (1 + change)
            
            # 각 코인별 실시간 가격 데이터 (Dantaro 원래 서버 형식)
            realtime_data = {}
            for coin in coins:
                coin_prices = {}
                for exchange in exchanges:
                    coin_prices[exchange] = round(prices[exchange][coin], 2)
                
                # 원래 서버 형식: { "BTC": { "Upbit": 42000000, "OKX": 41000000, ... } }
                realtime_data[coin] = coin_prices
                
            # 서버 원래 형식에 맞게 realtime_data 메시지 전송
            await manager.broadcast({
                "type": "realtime_data",
                "data": realtime_data,
                "timestamp": now
            })
            
            # 차익거래 기회 계산 및 전송
            if counter % 3 == 0:  # 3초마다 차익거래/김치프리미엄 데이터 전송
                # 차익거래 기회
                arbitrage_data = []
                for coin in coins:
                    for buy_ex in exchanges:
                        for sell_ex in exchanges:
                            if buy_ex != sell_ex:
                                buy_price = prices[buy_ex][coin]
                                sell_price = prices[sell_ex][coin]
                                
                                if sell_price > buy_price:
                                    spread = ((sell_price - buy_price) / buy_price) * 100
                                    if spread > 0.8:  # 0.8% 이상 차이가 있는 경우만
                                        arbitrage_data.append({
                                            "coin": coin,
                                            "buy_exchange": buy_ex,
                                            "sell_exchange": sell_ex,
                                            "buy_price": round(buy_price, 2),
                                            "sell_price": round(sell_price, 2),
                                            "spread": round(spread, 2),
                                            "timestamp": now
                                        })
                
                # 상위 10개만 선택                
                arbitrage_data = sorted(arbitrage_data, key=lambda x: x["spread"], reverse=True)[:10]
                
                # 원래 서버 형식에 맞게 arbitrage_data 메시지 전송
                await manager.broadcast({
                    "type": "arbitrage_data",
                    "data": arbitrage_data,
                    "timestamp": now
                })
                
                # 김치 프리미엄 계산 및 전송
                korean_exchanges = ["Upbit", "Coinone"]
                global_exchanges = ["OKX", "Gate.io", "Binance"]
                
                kimchi_data = []
                for coin in ["BTC", "ETH", "XRP"]:
                    korean_prices = [prices[ex][coin] for ex in korean_exchanges]
                    global_prices = [prices[ex][coin] for ex in global_exchanges]
                    
                    avg_korean = sum(korean_prices) / len(korean_prices)
                    avg_global = sum(global_prices) / len(global_prices)
                    premium = ((avg_korean - avg_global) / avg_global) * 100
                    
                    kimchi_data.append({
                        "coin": coin,
                        "korean_price": round(avg_korean, 2),
                        "global_price": round(avg_global, 2),
                        "premium": round(premium, 2),
                        "timestamp": now
                    })
                
                # 원래 서버 형식에 맞게 kimchi_premium 메시지 전송
                await manager.broadcast({
                    "type": "kimchi_premium",
                    "data": kimchi_data,
                    "timestamp": now
                })
            
            # 가끔 알림 메시지 전송
            if counter % 15 == 0:  # 15초마다 알림 전송
                alert_types = ["info", "warning", "success", "danger"]
                alert_weight = [0.7, 0.1, 0.15, 0.05]  # 메시지 타입별 가중치
                alert_type = random.choices(alert_types, weights=alert_weight)[0]
                
                messages = [
                    f"BTC 김치 프리미엄 {random.uniform(1.5, 7.0):.2f}% 감지",
                    f"ETH/MATIC 페어 차익거래 기회 {random.uniform(1.0, 3.0):.2f}%",
                    f"{random.choice(['Upbit', 'Coinone'])}에서 {random.choice(['BTC', 'ETH'])} 가격 급등",
                    f"{random.choice(['OKX', 'Gate.io'])}에서 {random.choice(['SOL', 'ADA'])} 가격 급락",
                    f"새로운 분석 데이터 업데이트 완료"
                ]
                
                # 원래 서버 형식에 맞게 alert 메시지 전송
                await manager.broadcast({
                    "type": "alert",
                    "data": {
                        "message": random.choice(messages),
                        "level": alert_type,
                        "timestamp": now
                    }
                })
                
                if counter % 30 == 0:
                    logger.info(f"📊 데이터 생성 중... (메시지 카운터: {counter})")
            
            # 주기 (1초)
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"데이터 생성 오류: {str(e)}")
            await asyncio.sleep(5)  # 오류 시 잠시 대기

# WebSocket 엔드포인트
@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 WebSocket 엔드포인트"""
    # 상세 연결 정보 기록
    client = websocket.client
    headers = websocket.headers
    
    # 연결 시도 정보 로깅
    print("="*80)
    print(f"⚡ 새로운 WebSocket 연결 시도")
    print(f"👤 클라이언트: {client}")
    print(f"🔗 경로: {websocket.url.path}")
    print(f"📨 헤더: {dict(headers)}")
    print("="*80)
    
    # WebSocket 수락
    await websocket.accept()
    print(f"✅ WebSocket 연결 수락됨: {client}")
    
    # 매니저에 연결 추가
    await manager.connect(websocket)
    
    # 환영 메시지
    welcome_msg = {
        "type": "welcome",
        "message": "Dantaro Central WebSocket 서버에 연결되었습니다.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    await websocket.send_json(welcome_msg)
    print(f"📤 환영 메시지 전송 완료: {welcome_msg['message']}")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (비동기적으로 대기)
            # 실제로는 ping/pong, 구독 요청 등을 처리할 수 있음
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type", "unknown")
                
                # ping 메시지는 pong으로 응답
                if msg_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                elif msg_type == "request_data":
                    # 데이터 요청 시 빈 응답 (실제 데이터는 실시간 생성기에서 전송)
                    await websocket.send_json({
                        "type": "info",
                        "message": "데이터 요청 수신됨. 실시간 데이터 전송이 곧 시작됩니다.",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            except json.JSONDecodeError:
                logger.warning(f"잘못된 JSON 형식: {data[:100]}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 오류: {str(e)}")
        manager.disconnect(websocket)

# 시작 이벤트
@app.on_event("startup")
async def startup_event():
    # 데이터 생성기 백그라운드 작업 시작
    asyncio.create_task(generate_realtime_data())
    logger.info("✅ 실시간 데이터 생성기 시작")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
