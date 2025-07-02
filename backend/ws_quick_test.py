#!/usr/bin/env python3
"""
간단한 WebSocket 클라이언트 테스트
"""
import asyncio
import websockets
import sys
import json
import time
from datetime import datetime

# 테스트할 URL
WS_URL = "ws://127.0.0.1:8000/ws/realtime"

async def test_connection():
    """WebSocket 연결 테스트"""
    print(f"연결 시도 중: {WS_URL}")
    
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ 연결 성공!")
            
            # 초기 메시지 수신 대기
            print("메시지 대기 중...")
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            print(f"📥 수신: {msg}")
            
            # 핑 전송
            ping = json.dumps({"type": "ping", "time": datetime.now().isoformat()})
            print(f"📤 전송: {ping}")
            await ws.send(ping)
            
            # 응답 대기
            print("응답 대기 중...")
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            print(f"📥 수신: {response}")
            
            print("✅ 테스트 완료")
            return True
    
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 함수"""
    success = await test_connection()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
