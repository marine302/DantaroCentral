#!/usr/bin/env python3
"""
WebSocket 연결 오류 로깅 수집기
"""
import asyncio
import websockets
import logging
import json
import sys
import time
from datetime import datetime

# 로그 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("websocket_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 연결할 WebSocket URL
WS_URL = "ws://127.0.0.1:8000/ws/realtime"

async def test_websocket_connection():
    """WebSocket 연결 테스트 및 오류 로깅"""
    logger.info(f"WebSocket 연결 테스트 시작: {WS_URL}")
    
    # 연결 상태 추적
    connection_attempts = 0
    max_attempts = 5
    
    while connection_attempts < max_attempts:
        connection_attempts += 1
        
        try:
            logger.info(f"연결 시도 #{connection_attempts}...")
            
            # 연결 타임아웃 5초 설정
            start_time = time.time()
            async with websockets.connect(WS_URL, max_size=None, ping_interval=None, ping_timeout=None, close_timeout=5) as websocket:
                connect_time = time.time() - start_time
                logger.info(f"✅ 연결 성공! (소요 시간: {connect_time:.2f}초)")
                
                # 환영 메시지 수신 대기
                logger.info("초기 메시지 대기 중...")
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    logger.info(f"📥 메시지 수신: {message[:200]}")
                    
                    # JSON 파싱
                    try:
                        data = json.loads(message)
                        logger.info(f"메시지 타입: {data.get('type')}")
                        logger.info(f"메시지 내용: {data.get('message', '내용 없음')}")
                    except json.JSONDecodeError:
                        logger.error(f"JSON 파싱 실패: {message[:50]}...")
                    
                except asyncio.TimeoutError:
                    logger.warning("⚠️ 초기 메시지 타임아웃")
                
                # 핑 메시지 전송
                ping_msg = json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()})
                logger.info(f"📤 핑 메시지 전송: {ping_msg}")
                await websocket.send(ping_msg)
                
                # 응답 대기
                try:
                    pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"📥 응답 수신: {pong[:200]}")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ 핑 응답 타임아웃")
                
                # 테스트용 데이터 요청
                request_msg = json.dumps({"type": "request_data", "timestamp": datetime.now().isoformat()})
                logger.info(f"📤 데이터 요청 메시지 전송: {request_msg}")
                await websocket.send(request_msg)
                
                # 60초 동안 메시지 수신 대기
                logger.info("📡 60초 동안 메시지 수신 대기...")
                message_count = 0
                start_listen = time.time()
                
                while time.time() - start_listen < 60:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        message_count += 1
                        
                        # 메시지 정보 기록
                        try:
                            data = json.loads(message)
                            logger.info(f"📩 메시지 #{message_count} 수신 - 타입: {data.get('type')}")
                        except:
                            logger.info(f"📩 메시지 #{message_count} 수신 - 일반 텍스트: {message[:50]}...")
                        
                    except asyncio.TimeoutError:
                        logger.info("⏱️ 5초 타임아웃, 계속 대기...")
                    
                    # 간격 유지
                    await asyncio.sleep(1)
                
                logger.info(f"📊 총 {message_count}개 메시지 수신됨")
                
                # 연결 종료 전 메시지 전송
                close_msg = json.dumps({"type": "goodbye", "message": "테스트 완료", "timestamp": datetime.now().isoformat()})
                logger.info(f"📤 종료 메시지 전송: {close_msg}")
                await websocket.send(close_msg)
                
                # 연결 정상 종료
                logger.info("🔌 WebSocket 연결 정상 종료")
                return True
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ 연결 오류 (시도 #{connection_attempts}, {elapsed:.2f}초 경과): {str(e)}")
            
            # 상세 오류 정보 수집
            import traceback
            logger.error(f"상세 오류:\n{traceback.format_exc()}")
            
            # 재시도 전 대기
            await asyncio.sleep(2)
    
    logger.error(f"❌ 최대 시도 횟수 도달 ({max_attempts}회). WebSocket 연결 실패.")
    return False

async def main():
    """메인 함수"""
    try:
        logger.info("="*50)
        logger.info("WebSocket 연결 디버깅 도구 시작")
        logger.info("="*50)
        
        # 시스템 정보 로깅
        import platform
        import websockets
        logger.info(f"Python 버전: {platform.python_version()}")
        logger.info(f"WebSockets 라이브러리 버전: {websockets.__version__}")
        logger.info(f"OS: {platform.system()} {platform.version()}")
        logger.info(f"WebSocket URL: {WS_URL}")
        logger.info("="*50)
        
        # 연결 테스트 실행
        success = await test_websocket_connection()
        
        # 결과 요약
        logger.info("="*50)
        if success:
            logger.info("✅ WebSocket 연결 테스트 성공")
        else:
            logger.info("❌ WebSocket 연결 테스트 실패")
        logger.info("="*50)
        
    except Exception as e:
        logger.critical(f"치명적 오류: {str(e)}")
        import traceback
        logger.critical(f"상세 오류:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
