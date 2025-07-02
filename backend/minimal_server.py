#!/usr/bin/env python3
"""
최소화된 Dantaro Central 웹 서버
대시보드 접속 테스트용
"""
import os
import sys
from pathlib import Path
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
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
    title="Dantaro Central 최소화 서버",
    description="차익거래 대시보드 접속 테스트",
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

# 라우트 설정
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """대시보드 페이지"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# 간단한 API 엔드포인트
@app.get("/api/v1/status")
async def status():
    """서버 상태 API"""
    return {
        "status": "online",
        "service": "dantaro-central",
        "features": {
            "dashboard": "active",
            "websocket": "inactive",
            "data_collection": "inactive",
        }
    }

# WebSocket 실시간 데이터 엔드포인트
import asyncio
import random
import json
import time
from datetime import datetime
from fastapi import WebSocket

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 전송 WebSocket 엔드포인트"""
    print("="*80)
    print("🔌 새 WebSocket 연결 요청 수신")
    print(f"🌐 클라이언트: {websocket.client}")
    print(f"🛣️ 경로: {websocket.url.path}")
    print("="*80)
    
    await websocket.accept()
    print("✅ WebSocket 연결 수락됨")
    logger.info("✅ 새로운 WebSocket 연결 수락됨")
    
    # 테스트용 가상 거래소와 코인 목록
    exchanges = ["Upbit", "Coinone", "OKX", "Gate.io", "Binance"]
    coins = ["BTC", "ETH", "XRP", "SOL", "ADA", "MATIC", "DOT"]
    
    try:
        # 첫 연결 시 환영 메시지 전송 (welcome 타입으로 변경)
        await websocket.send_json({
            "type": "welcome",
            "message": "Dantaro Central 웹소켓 서버에 연결되었습니다.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
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
        
        price_data = {}
        for exchange in exchanges:
            price_data[exchange] = {}
            for coin in coins:
                # 거래소별로 약간의 가격 차이 설정
                variation = random.uniform(0.97, 1.03)
                price_data[exchange][coin] = base_prices[coin] * variation
        
        # 실시간 데이터 전송 루프
        counter = 0
        while True:
            counter += 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 가격 데이터 업데이트
            for exchange in exchanges:
                for coin in coins:
                    # 가격 변동 시뮬레이션 (±1%)
                    change = random.uniform(-0.01, 0.01)
                    price_data[exchange][coin] *= (1 + change)
            
            # 차익거래 기회 계산
            arbitrage_opportunities = []
            for coin in coins:
                prices = [price_data[exchange][coin] for exchange in exchanges]
                min_price = min(prices)
                max_price = max(prices)
                min_exchange = exchanges[prices.index(min_price)]
                max_exchange = exchanges[prices.index(max_price)]
                
                spread_pct = ((max_price - min_price) / min_price) * 100
                
                if spread_pct > 1.0:  # 1% 이상의 차익만 표시
                    arbitrage_opportunities.append({
                        "coin": coin,
                        "buy_exchange": min_exchange,
                        "sell_exchange": max_exchange,
                        "buy_price": round(min_price, 2),
                        "sell_price": round(max_price, 2),
                        "spread_pct": round(spread_pct, 2),
                        "timestamp": now
                    })
            
            # 김치 프리미엄 계산 (한국 거래소 vs 해외 거래소)
            kimchi_premiums = []
            korean_exchanges = ["Upbit", "Coinone"]
            global_exchanges = ["OKX", "Gate.io", "Binance"]
            
            for coin in ["BTC", "ETH", "XRP"]:
                korean_prices = [price_data[exchange][coin] for exchange in korean_exchanges if exchange in price_data]
                global_prices = [price_data[exchange][coin] for exchange in global_exchanges if exchange in price_data]
                
                if korean_prices and global_prices:
                    avg_korean = sum(korean_prices) / len(korean_prices)
                    avg_global = sum(global_prices) / len(global_prices)
                    premium_pct = ((avg_korean - avg_global) / avg_global) * 100
                    
                    kimchi_premiums.append({
                        "coin": coin,
                        "korean_price": round(avg_korean, 2),
                        "global_price": round(avg_global, 2),
                        "premium_pct": round(premium_pct, 2),
                        "timestamp": now
                    })
            
            # 각 데이터 타입별로 개별 메시지 전송 (프론트엔드 기대 형식에 맞춤)
            # 1. 가격 데이터
            price_message = {
                "type": "price_update",
                "data": price_data,
                "timestamp": now
            }
            await websocket.send_json(price_message)
            if counter % 5 == 0:  # 로그를 너무 많이 출력하지 않도록 5번에 한 번만 출력
                print(f"📤 가격 데이터 전송 완료 (counter: {counter})")
            
            # 2. 차익거래 기회 데이터
            arbitrage_message = {
                "type": "arbitrage_opportunities", 
                "data": arbitrage_opportunities,
                "timestamp": now
            }
            await websocket.send_json(arbitrage_message)
            if counter % 5 == 0:
                print(f"📤 차익거래 데이터 전송 완료 - {len(arbitrage_opportunities)}개 기회")
            
            # 3. 김치 프리미엄 데이터
            kimchi_message = {
                "type": "kimchi_premium",
                "data": kimchi_premiums,
                "timestamp": now
            }
            await websocket.send_json(kimchi_message)
            if counter % 5 == 0:
                print(f"📤 김치 프리미엄 데이터 전송 완료 - {len(kimchi_premiums)}개 코인")
            
            # 10개 데이터마다 별도의 알림 메시지 전송
            if counter % 10 == 0:
                if random.random() < 0.7:  # 70% 확률로 프리미엄 알림
                    premium_value = random.uniform(2.0, 8.0)
                    alert = {
                        "type": "alert",
                        "data": {
                            "message": f"높은 프리미엄 감지: BTC 김치 프리미엄 {premium_value:.2f}%",
                            "level": "info",
                            "timestamp": now
                        }
                    }
                else:  # 30% 확률로 차익거래 알림
                    spread_value = random.uniform(2.5, 5.0)
                    alert = {
                        "type": "alert",
                        "data": {
                            "message": f"차익거래 기회 발생: ETH {spread_value:.2f}% (Upbit-OKX)",
                            "level": "success", 
                            "timestamp": now
                        }
                    }
                await websocket.send_json(alert)
            
            # 잠시 대기 (1초)
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket 오류: {str(e)}")
    finally:
        logger.info("WebSocket 연결 종료")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
