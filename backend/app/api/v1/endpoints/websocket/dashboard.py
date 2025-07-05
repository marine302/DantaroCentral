"""
대시보드 관련 API 엔드포인트
"""

import logging
import random
from datetime import datetime
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """대시보드 통계 API"""
    # connection_manager를 realtime에서 import
    from .realtime import connection_manager
    
    return {
        "websocket_stats": connection_manager.get_stats(),
        "exchange_count": 4,
        "supported_exchanges": ["OKX", "Upbit", "Coinone", "Gate.io"],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/api/dashboard/send-test-data")
async def send_test_data():
    """테스트 데이터 전송 API"""
    # connection_manager를 realtime에서 import
    from .realtime import connection_manager
    
    try:
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
