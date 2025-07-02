"""
실시간 WebSocket 엔드포인트
웹 대시보드를 위한 실시간 데이터 스트리밍
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from app.services.websocket_data_manager import MultiExchangeWebSocketManager
from app.services.arbitrage_analyzer import ArbitrageAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


class WebSocketConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결들
        self.active_connections: Set[WebSocket] = set()
        
        # 데이터 관리자들
        self.websocket_manager = None
        self.arbitrage_analyzer = ArbitrageAnalyzer()
        
        # 마지막 전송 데이터 캐시
        self.last_prices = {}
        self.last_opportunities = []
        self.last_kimchi_premiums = []
        
        # 전송 제한 (초당 최대 전송 횟수)
        self.max_sends_per_second = 10
        self.last_send_time = datetime.now()
        
    async def connect(self, websocket: WebSocket):
        """새로운 WebSocket 연결"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket 연결됨. 총 {len(self.active_connections)}개 연결")
        
        # 초기 데이터 전송
        await self.send_initial_data(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket 연결 해제됨. 총 {len(self.active_connections)}개 연결")
    
    async def send_initial_data(self, websocket: WebSocket):
        """초기 데이터 전송"""
        try:
            # 환영 메시지
            await self.send_to_websocket(websocket, {
                "type": "welcome",
                "message": "Dantaro Central 실시간 대시보드에 연결되었습니다",
                "timestamp": datetime.now().isoformat(),
                "active_exchanges": ["OKX", "Upbit", "Coinone", "Gate.io"]
            })
            
            # 마지막 캐시된 데이터 전송
            if self.last_prices:
                await self.send_to_websocket(websocket, {
                    "type": "price_update",
                    "data": self.last_prices
                })
            
            if self.last_opportunities:
                await self.send_to_websocket(websocket, {
                    "type": "arbitrage_opportunities",
                    "data": self.last_opportunities
                })
                
            if self.last_kimchi_premiums:
                await self.send_to_websocket(websocket, {
                    "type": "kimchi_premium",
                    "data": self.last_kimchi_premiums
                })
                
        except Exception as e:
            logger.error(f"초기 데이터 전송 오류: {e}")
    
    async def send_to_websocket(self, websocket: WebSocket, data: dict):
        """단일 WebSocket에 데이터 전송"""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"WebSocket 데이터 전송 오류: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, data: dict):
        """모든 연결된 WebSocket에 브로드캐스트"""
        if not self.active_connections:
            return
        
        # 전송 속도 제한
        now = datetime.now()
        time_diff = (now - self.last_send_time).total_seconds()
        if time_diff < (1.0 / self.max_sends_per_second):
            return
        
        self.last_send_time = now
        
        # 연결이 끊어진 WebSocket 제거를 위한 임시 리스트
        disconnected = set()
        
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.warning(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)
        
        # 끊어진 연결 정리
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def handle_price_update(self, exchange: str, symbol: str, data: dict):
        """가격 업데이트 처리"""
        try:
            # 가격 데이터 저장
            key = f"{exchange}:{symbol}"
            self.last_prices[key] = {
                "exchange": exchange,
                "symbol": symbol,
                "price": data.get("last_price", 0),
                "volume": data.get("volume", 0),
                "timestamp": data.get("timestamp", datetime.now().isoformat())
            }
            
            # 실시간 브로드캐스트
            await self.broadcast({
                "type": "price_update",
                "data": {key: self.last_prices[key]}
            })
            
            # 차익거래 분석 수행
            await self.analyze_arbitrage()
            
        except Exception as e:
            logger.error(f"가격 업데이트 처리 오류: {e}")
    
    async def analyze_arbitrage(self):
        """차익거래 분석 및 브로드캐스트"""
        try:
            # 현재 가격 데이터로 분석 수행
            opportunities = self.arbitrage_analyzer.find_arbitrage_opportunities()
            kimchi_premiums = self.arbitrage_analyzer.calculate_kimchi_premium()
            
            # 기회가 있으면 브로드캐스트
            if opportunities:
                self.last_opportunities = [
                    {
                        "symbol": opp.symbol,
                        "buy_exchange": opp.buy_exchange,
                        "sell_exchange": opp.sell_exchange,
                        "buy_price": float(opp.buy_price),
                        "sell_price": float(opp.sell_price),
                        "spread_percentage": float(opp.spread_percentage),
                        "confidence": float(opp.confidence),
                        "timestamp": opp.timestamp.isoformat()
                    }
                    for opp in opportunities[:10]  # 상위 10개만
                ]
                
                await self.broadcast({
                    "type": "arbitrage_opportunities",
                    "data": self.last_opportunities
                })
            
            # 김치 프리미엄
            if kimchi_premiums:
                self.last_kimchi_premiums = [
                    {
                        "symbol": kp.symbol,
                        "korean_exchange": kp.korean_exchange,
                        "global_exchange": kp.global_exchange,
                        "korean_price": float(kp.korean_price),
                        "global_price": float(kp.global_price),
                        "premium_percentage": float(kp.premium_percentage),
                        "timestamp": kp.timestamp.isoformat()
                    }
                    for kp in kimchi_premiums[:10]  # 상위 10개만
                ]
                
                await self.broadcast({
                    "type": "kimchi_premium",
                    "data": self.last_kimchi_premiums
                })
                
        except Exception as e:
            logger.error(f"차익거래 분석 오류: {e}")
    
    def set_websocket_manager(self, manager: MultiExchangeWebSocketManager):
        """WebSocket 데이터 매니저 설정"""
        self.websocket_manager = manager
        
        # 콜백 설정
        manager.set_data_callbacks(ticker_callback=self.handle_price_update)
    
    def get_stats(self) -> dict:
        """연결 통계"""
        return {
            "active_connections": len(self.active_connections),
            "cached_prices": len(self.last_prices),
            "last_opportunities": len(self.last_opportunities),
            "last_kimchi_premiums": len(self.last_kimchi_premiums)
        }


# 전역 연결 관리자
connection_manager = WebSocketConnectionManager()


@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 WebSocket 엔드포인트"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (핑퐁이나 요청)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                # 클라이언트 요청 처리
                if message.get("type") == "ping":
                    await connection_manager.send_to_websocket(websocket, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "request_data":
                    await connection_manager.send_initial_data(websocket)
                    
            except asyncio.TimeoutError:
                # 타임아웃 - 연결 유지를 위한 핑
                await connection_manager.send_to_websocket(websocket, {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
            except json.JSONDecodeError:
                logger.warning("잘못된 JSON 메시지 수신")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        connection_manager.disconnect(websocket)


@router.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """대시보드 통계 API"""
    return {
        "websocket_stats": connection_manager.get_stats(),
        "exchange_count": 4,
        "supported_exchanges": ["OKX", "Upbit", "Coinone", "Gate.io"],
        "timestamp": datetime.now().isoformat()
    }
