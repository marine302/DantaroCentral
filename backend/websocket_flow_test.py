#!/usr/bin/env python3
"""
웹소켓 연결 상태 및 데이터 수신 테스트
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """웹소켓 연결 및 데이터 수신 테스트"""
    
    # 테스트할 URL들
    test_urls = [
        "ws://localhost:8000/ws/realtime",
        "ws://localhost:8001/ws/realtime",
        "ws://127.0.0.1:8000/ws/realtime"
    ]
    
    for url in test_urls:
        logger.info(f"🔍 {url} 연결 테스트 시작...")
        
        try:
            async with websockets.connect(url) as websocket:
                logger.info(f"✅ {url} 연결 성공!")
                
                # 환영 메시지 수신 대기 (최대 5초)
                try:
                    welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    welcome_data = json.loads(welcome_msg)
                    logger.info(f"📨 환영 메시지: {welcome_data}")
                except asyncio.TimeoutError:
                    logger.warning("⏰ 환영 메시지 수신 시간 초과")
                
                # 추가 메시지 수신 대기 (최대 10초)
                logger.info("🎧 실시간 데이터 수신 대기 중...")
                message_count = 0
                
                try:
                    for i in range(10):  # 최대 10개 메시지 수신
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        message_count += 1
                        
                        logger.info(f"📦 메시지 {message_count}: {data.get('type', 'unknown')} - {len(str(data))} bytes")
                        
                        # 메시지 타입별 상세 로그
                        if data.get('type') == 'price_update':
                            logger.info(f"💰 가격 업데이트: {list(data.get('data', {}).keys())}")
                        elif data.get('type') == 'arbitrage_opportunities':
                            logger.info(f"🔄 차익거래 기회: {len(data.get('data', []))}개")
                        elif data.get('type') == 'kimchi_premium':
                            logger.info(f"🇰🇷 김치 프리미엄 데이터")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ 추가 메시지 수신 시간 초과 (총 {message_count}개 메시지 수신)")
                
                # 연결 테스트 완료
                logger.info(f"✅ {url} 테스트 완료 - {message_count}개 메시지 수신")
                return url  # 성공한 첫 번째 URL 반환
                
        except Exception as e:
            logger.error(f"❌ {url} 연결 실패: {e}")
            continue
    
    logger.error("❌ 모든 웹소켓 URL 연결 실패")
    return None

async def test_message_flow():
    """메시지 흐름 상세 테스트"""
    url = await test_websocket_connection()
    
    if not url:
        return
    
    logger.info(f"🔄 {url}에서 메시지 흐름 상세 분석...")
    
    try:
        async with websockets.connect(url) as websocket:
            # 데이터 요청 메시지 전송
            request_msg = {
                "type": "request_data",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(request_msg))
            logger.info("📤 데이터 요청 메시지 전송")
            
            # 응답 대기
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    
                    logger.info(f"📨 응답 메시지 {i+1}:")
                    logger.info(f"   타입: {data.get('type')}")
                    logger.info(f"   크기: {len(str(data))} bytes")
                    
                    if data.get('type') == 'price_update':
                        price_data = data.get('data', {})
                        logger.info(f"   가격 데이터 키: {list(price_data.keys())}")
                        for key, value in list(price_data.items())[:3]:  # 처음 3개만 출력
                            logger.info(f"   {key}: {value}")
                    
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ 응답 {i+1} 수신 시간 초과")
                    break
                    
    except Exception as e:
        logger.error(f"❌ 메시지 흐름 테스트 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_message_flow())
