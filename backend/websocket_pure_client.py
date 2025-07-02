#!/usr/bin/env python3
"""
순수 Python WebSocket 클라이언트
테스트 및 연결 오류 확인용
"""
import websocket
import json
import time
import sys
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 설정
WS_URL = "ws://127.0.0.1:8000/ws/realtime"
TIMEOUT = 10  # 초

def on_message(ws, message):
    """메시지 수신 핸들러"""
    logger.info(f"메시지 수신: {message[:200]}")
    try:
        data = json.loads(message)
        logger.info(f"메시지 타입: {data.get('type')}")
    except json.JSONDecodeError:
        logger.warning("JSON 파싱 실패")

def on_error(ws, error):
    """오류 핸들러"""
    logger.error(f"WebSocket 오류: {str(error)}")

def on_close(ws, close_status_code, close_msg):
    """연결 종료 핸들러"""
    logger.info(f"WebSocket 연결 종료: {close_status_code} - {close_msg}")

def on_open(ws):
    """연결 성공 핸들러"""
    logger.info("WebSocket 연결 성공!")
    
    # 핑 메시지 전송
    ping_msg = json.dumps({
        "type": "ping",
        "timestamp": datetime.now().isoformat()
    })
    logger.info(f"핑 메시지 전송: {ping_msg}")
    ws.send(ping_msg)
    
    # 데이터 요청
    data_request = json.dumps({
        "type": "request_data",
        "timestamp": datetime.now().isoformat()
    })
    logger.info(f"데이터 요청 메시지 전송: {data_request}")
    ws.send(data_request)

def main():
    """메인 함수"""
    logger.info(f"WebSocket 연결 테스트 시작: {WS_URL}")
    logger.info("="*50)
    
    # 시스템 정보 로깅
    logger.info(f"Python 버전: {sys.version}")
    logger.info(f"websocket-client 버전: {websocket.__version__}")
    
    # WebSocket 인스턴스 생성
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # 연결 시도
    try:
        logger.info("연결 시도 중...")
        ws.run_forever(ping_interval=60, ping_timeout=10, ping_payload="ping")
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
    finally:
        logger.info("프로그램 종료")

if __name__ == "__main__":
    main()
