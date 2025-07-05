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
from fastapi.responses import HTMLResponse

from app.services.websocket_data_manager import MultiExchangeWebSocketManager
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 실제 데이터 서비스 import 추가
try:
    from app.services.real_data_service import backend_real_data_service
    real_data_service = backend_real_data_service
    logger.info("백엔드 실제 데이터 서비스 로드됨")
except ImportError as e:
    real_data_service = None
    logger.warning(f"실제 데이터 서비스를 로드할 수 없습니다: {e}")


class WebSocketConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결들
        self.active_connections: Set[WebSocket] = set()
        
        # 데이터 관리자들
        self.websocket_manager = None
        
        # 마지막 전송 데이터 캐시
        self.last_prices = {}
        self.last_kimchi_premiums = []
        
        # 전송 제한 (초당 최대 전송 횟수)
        self.max_sends_per_second = getattr(settings, "ws_max_sends_per_second", 10)
        self.last_send_time = datetime.now()
        
        # 활성 거래소 목록
        self.active_exchanges = getattr(settings, "active_exchanges", ["OKX", "Upbit", "Coinone", "Gate.io"])
        
    def get_connection_stats(self):
        """연결 통계 반환"""
        return {
            "active_connections": len(self.active_connections),
            "last_update": self.last_send_time.isoformat(),
            "active_exchanges": self.active_exchanges
        }
        
    async def connect(self, websocket: WebSocket):
        """새로운 WebSocket 연결"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"[WebSocket] 연결됨. 총 {len(self.active_connections)}개 연결")
        
        # 초기 데이터 전송
        await self.send_initial_data(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        self.active_connections.discard(websocket)
        logger.info(f"[WebSocket] 연결 해제됨. 총 {len(self.active_connections)}개 연결")
    
    async def send_initial_data(self, websocket: WebSocket):
        """초기 데이터 전송"""
        try:
            # 환영 메시지
            await self.send_to_websocket(websocket, {
                "type": "welcome",
                "message": "Dantaro Central 실시간 대시보드에 연결되었습니다",
                "timestamp": datetime.now().isoformat(),
                "active_exchanges": self.active_exchanges
            })
            
            # 마지막 캐시된 데이터 전송
            if self.last_prices:
                await self.send_to_websocket(websocket, {
                    "type": "price_update",
                    "data": self.last_prices
                })
                
            if self.last_kimchi_premiums:
                await self.send_to_websocket(websocket, {
                    "type": "kimchi_premium",
                    "data": self.last_kimchi_premiums
                })
                
        except Exception as e:
            logger.error(f"[WebSocket] 초기 데이터 전송 오류: {e}")
    
    async def send_to_websocket(self, websocket: WebSocket, data: dict):
        """단일 WebSocket에 데이터 전송"""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"[WebSocket] 데이터 전송 오류: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, data: dict):
        """모든 연결된 WebSocket에 브로드캐스트"""
        if not self.active_connections:
            logger.info("브로드캐스트 시도했지만 활성 연결이 없음")
            return
        
        logger.info(f"브로드캐스트 시작: {data.get('type', 'unknown')} -> {len(self.active_connections)}개 연결")
        
        # 전송 속도 제한
        now = datetime.now()
        time_diff = (now - self.last_send_time).total_seconds()
        if time_diff < (1.0 / self.max_sends_per_second):
            logger.debug("전송 속도 제한으로 브로드캐스트 건너뜀")
            return
        
        self.last_send_time = now
        
        # 연결이 끊어진 WebSocket 제거를 위한 임시 리스트
        disconnected = set()
        
        for websocket in self.active_connections.copy():
            try:
                await websocket.send_text(json.dumps(data))
                logger.debug(f"메시지 전송 성공: {data.get('type', 'unknown')}")
            except Exception as e:
                logger.warning(f"WebSocket 전송 실패: {e}")
                disconnected.add(websocket)
        
        # 끊어진 연결 정리
        for websocket in disconnected:
            self.disconnect(websocket)
            
        logger.info(f"브로드캐스트 완료: {data.get('type', 'unknown')} -> {len(self.active_connections) - len(disconnected)}개 연결 성공")
    
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
            
        except Exception as e:
            logger.error(f"가격 업데이트 처리 오류: {e}")
    
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
            "last_kimchi_premiums": len(self.last_kimchi_premiums)
        }
    
    async def start_test_data_loop(self):
        """테스트 데이터를 주기적으로 전송"""
        logger.info("🧪 테스트 데이터 루프 시작")
        
        while True:
            try:
                if self.active_connections:
                    # 모의 가격 데이터
                    price_data = []
                    exchanges = ['OKX', 'Upbit', 'Coinone', 'Gate.io']
                    symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL']
                    
                    import random
                    
                    for exchange in exchanges:
                        for symbol in symbols:
                            price_data.append({
                                'exchange': exchange,
                                'symbol': symbol,
                                'price': round(random.uniform(30000, 70000), 2) if symbol == 'BTC' else round(random.uniform(1000, 5000), 2),
                                'volume': round(random.uniform(1000000, 10000000), 2),
                                'change_24h': round(random.uniform(-10, 10), 2),
                                'timestamp': datetime.now().isoformat()
                            })
                    
                    # 모의 김치 프리미엄
                    kimchi_data = []
                    for symbol in ['BTC', 'ETH', 'ADA']:
                        korean_price = round(random.uniform(30000, 35000), 2)
                        global_price = round(korean_price * random.uniform(0.95, 1.05), 2)
                        premium = round(((korean_price - global_price) / global_price) * 100, 2)
                        
                        kimchi_data.append({
                            'symbol': symbol,
                            'korean_exchange': 'Upbit',
                            'global_exchange': 'OKX',
                            'korean_price': korean_price,
                            'global_price': global_price,
                            'premium_percentage': premium,
                            'status': 'positive' if premium > 0 else 'negative'
                        })
                    
                    # 데이터 브로드캐스트
                    await self.broadcast({
                        "type": "price_update",
                        "data": price_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    await self.broadcast({
                        "type": "kimchi_premium",
                        "data": kimchi_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    logger.info(f"📡 테스트 데이터 전송 완료 ({len(self.active_connections)}개 연결)")
                
                # 10초 대기
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"테스트 데이터 전송 오류: {e}")
                await asyncio.sleep(10)


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


@router.post("/api/dashboard/send-test-data")
async def send_test_data():
    """테스트 데이터 전송 API"""
    try:
        import random
        
        if not connection_manager.active_connections:
            return {"success": False, "message": "활성 WebSocket 연결이 없습니다"}
            
        # 모의 가격 데이터
        price_data = []
        exchanges = ['OKX', 'Upbit', 'Coinone', 'Gate.io']
        symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL']
        
        for exchange in exchanges:
            for symbol in symbols:
                price_data.append({
                    'exchange': exchange,
                    'symbol': symbol,
                    'price': round(random.uniform(30000, 70000), 2) if symbol == 'BTC' else round(random.uniform(1000, 5000), 2),
                    'volume': round(random.uniform(1000000, 10000000), 2),
                    'change_24h': round(random.uniform(-10, 10), 2),
                    'timestamp': datetime.now().isoformat()
                })
        
        # 모의 김치 프리미엄
        kimchi_data = []
        for symbol in ['BTC', 'ETH', 'ADA']:
            korean_price = round(random.uniform(30000, 35000), 2)
            global_price = round(korean_price * random.uniform(0.95, 1.05), 2)
            premium = round(((korean_price - global_price) / global_price) * 100, 2)
            
            kimchi_data.append({
                'symbol': symbol,
                'korean_exchange': 'Upbit',
                'global_exchange': 'OKX',
                'korean_price': korean_price,
                'global_price': global_price,
                'premium_percentage': premium,
                'status': 'positive' if premium > 0 else 'negative'
            })
        
        # 데이터 브로드캐스트
        await connection_manager.broadcast({
            "type": "price_update",
            "data": price_data,
            "timestamp": datetime.now().isoformat()
        })
        
        await connection_manager.broadcast({
            "type": "kimchi_premium",
            "data": kimchi_data,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True, 
            "message": f"테스트 데이터를 {len(connection_manager.active_connections)}개 연결에 전송했습니다",
            "connections": len(connection_manager.active_connections),
            "data_sent": {
                "prices": len(price_data),
                "kimchi": len(kimchi_data)
            }
        }
        
    except Exception as e:
        logger.error(f"테스트 데이터 전송 오류: {e}")
        return {"success": False, "message": f"오류: {str(e)}"}
    

@router.get("/api/dashboard/test-ui")
async def test_dashboard_ui():
    """대시보드 UI 테스트용 간단한 HTML 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dantaro WebSocket Test</title>
        <script>
            let ws = null;
            let messageCount = 0;
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;
                
                console.log('연결 시도:', wsUrl);
                document.getElementById('status').textContent = '연결 중...';
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    console.log('WebSocket 연결 성공');
                    document.getElementById('status').textContent = '연결됨';
                    document.getElementById('status').style.color = 'green';
                };
                
                ws.onmessage = function(event) {
                    messageCount++;
                    console.log('메시지 수신:', event.data);
                    
                    const data = JSON.parse(event.data);
                    const messageDiv = document.createElement('div');
                    messageDiv.innerHTML = `
                        <strong>[${messageCount}] ${data.type}</strong><br>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                        <hr>
                    `;
                    document.getElementById('messages').insertBefore(messageDiv, document.getElementById('messages').firstChild);
                    
                    // 최대 10개 메시지만 보관
                    const messages = document.getElementById('messages').children;
                    if (messages.length > 10) {
                        document.getElementById('messages').removeChild(messages[messages.length - 1]);
                    }
                };
                
                ws.onclose = function(event) {
                    console.log('WebSocket 연결 종료');
                    document.getElementById('status').textContent = '연결 종료';
                    document.getElementById('status').style.color = 'red';
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket 오류:', error);
                    document.getElementById('status').textContent = ' 오류';
                    document.getElementById('status').style.color = 'red';
                };
            }
            
            function sendTestData() {
                fetch('/api/dashboard/send-test-data', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        console.log('테스트 데이터 전송 결과:', data);
                        document.getElementById('testResult').textContent = JSON.stringify(data, null, 2);
                    })
                    .catch(error => {
                        console.error('테스트 데이터 전송 오류:', error);
                        document.getElementById('testResult').textContent = '오류: ' + error.message;
                    });
            }
            
            window.onload = connect;
        </script>
    </head>
    <body>
        <h1>Dantaro WebSocket 테스트</h1>
        <p>상태: <span id="status">연결 중...</span></p>
        <button onclick="sendTestData()">테스트 데이터 전송</button>
        <pre id="testResult"></pre>
        <h2>수신 메시지</h2>
        <div id="messages"></div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("/api/websocket/broadcast-real-data")
async def broadcast_real_data():
    """실제 거래소 데이터 수집 및 브로드캐스트"""
    try:
        if not connection_manager.active_connections:
            return {"success": False, "message": "활성 WebSocket 연결이 없습니다"}
        
        # 실제 데이터 서비스를 통한 데이터 수집 및 브로드캐스트
        if real_data_service:
            result = await real_data_service.collect_and_send_real_data()
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"실제 거래소 데이터를 {len(connection_manager.active_connections)}개 연결에 브로드캐스트 완료",
                    "active_connections": len(connection_manager.active_connections),
                    "data_points": result.get("data_points", 0),
                    "kimchi_premiums": result.get("kimchi_premiums", 0),
                    "timestamp": result.get("timestamp"),
                    "source": "real_exchange_apis"
                }
            else:
                return {
                    "success": False,
                    "message": result.get("error", "데이터 수집 실패"),
                    "active_connections": len(connection_manager.active_connections)
                }
        else:
            return {"success": False, "message": "실제 데이터 서비스가 초기화되지 않았습니다"}
            
    except Exception as e:
        logger.error(f"실제 데이터 브로드캐스트 오류: {e}")
        return {"success": False, "message": f"오류: {str(e)}"}


@router.post("/api/websocket/start-real-data-stream")
async def start_real_data_stream():
    """실제 데이터 스트림 시작"""
    try:
        if real_data_service and not real_data_service.running:
            # 실제 데이터 서비스 초기화 및 시작
            await real_data_service.initialize_exchanges()
            
            # 백그라운드 태스크로 데이터 수집 루프 시작
            import asyncio
            asyncio.create_task(real_data_service.start_collection_loop())
            
            return {
                "success": True,
                "message": "실제 거래소 데이터 스트림 시작",
                "active_exchanges": real_data_service.stats['active_exchanges'],
                "collection_interval": real_data_service.collection_interval
            }
        elif real_data_service and real_data_service.running:
            return {
                "success": True,
                "message": "실제 데이터 스트림이 이미 실행 중입니다",
                "stats": real_data_service.stats
            }
        else:
            return {"success": False, "message": "실제 데이터 서비스를 로드할 수 없습니다"}
            
    except Exception as e:
        logger.error(f"실제 데이터 스트림 시작 오류: {e}")
        return {"success": False, "message": f"오류: {str(e)}"}


@router.post("/api/websocket/stop-real-data-stream")
async def stop_real_data_stream():
    """실제 데이터 스트림 중지"""
    try:
        if real_data_service:
            real_data_service.stop()
            return {
                "success": True,
                "message": "실제 거래소 데이터 스트림 중지",
                "final_stats": real_data_service.stats
            }
        else:
            return {"success": False, "message": "실제 데이터 서비스가 로드되지 않았습니다"}
            
    except Exception as e:
        logger.error(f"실제 데이터 스트림 중지 오류: {e}")
        return {"success": False, "message": f"오류: {str(e)}"}


@router.get("/api/websocket/real-data-stats")
async def get_real_data_stats():
    """실제 데이터 서비스 통계"""
    try:
        if real_data_service:
            stats = real_data_service.get_stats()
            return {
                "success": True,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "실제 데이터 서비스를 사용할 수 없습니다",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"실제 데이터 통계 조회 오류: {e}")
        return {
            "success": False,
            "message": f"오류: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
