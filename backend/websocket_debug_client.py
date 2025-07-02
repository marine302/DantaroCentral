#!/usr/bin/env python3
"""
웹소켓 요청 및 응답 디버깅 서버
실제 클라이언트처럼 동작하며 서버 응답을 로깅합니다
"""

import asyncio
import json
import websockets
import logging
import time
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("websocket_debug.log")
    ]
)
logger = logging.getLogger(__name__)

async def websocket_client():
    """웹소켓 클라이언트 시뮬레이션"""
    uri = "ws://localhost:8000/ws/realtime"
    
    try:
        logger.info(f"🔌 서버에 연결 시도: {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ 연결 성공")
            
            # 핑-퐁 메시지
            ping_msg = json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()})
            await websocket.send(ping_msg)
            logger.info(f"📤 전송: {ping_msg}")
            
            # 메시지 수신 루프
            while True:
                try:
                    message = await websocket.recv()
                    try:
                        # JSON으로 파싱
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")
                        
                        # 메시지 타입에 따라 다른 로깅
                        if msg_type == "welcome":
                            logger.info(f"👋 환영 메시지: {data.get('message')}")
                        elif msg_type == "price_update":
                            logger.info(f"💹 가격 업데이트: {len(data.get('data', {}))} 거래소")
                        elif msg_type == "arbitrage_opportunities":
                            opps = data.get("data", [])
                            logger.info(f"🔄 차익거래 기회: {len(opps)}개")
                            for opp in opps[:2]:  # 처음 2개만 출력
                                logger.info(f"  - {opp.get('coin')}: {opp.get('spread_pct')}% ({opp.get('buy_exchange')} → {opp.get('sell_exchange')})")
                        elif msg_type == "kimchi_premium":
                            premiums = data.get("data", [])
                            logger.info(f"🇰🇷 김치 프리미엄: {len(premiums)}개")
                            for premium in premiums:
                                logger.info(f"  - {premium.get('coin')}: {premium.get('premium_pct')}%")
                        elif msg_type == "alert":
                            alert_data = data.get("data", {})
                            logger.info(f"⚠️ 알림: [{alert_data.get('level')}] {alert_data.get('message')}")
                        else:
                            logger.info(f"📩 기타 메시지 수신: {msg_type}")
                            
                    except json.JSONDecodeError:
                        logger.error(f"❌ JSON 파싱 실패: {message[:100]}...")
                    
                    await asyncio.sleep(0.1)  # 메시지 처리 간격
                    
                except Exception as e:
                    logger.error(f"❌ 메시지 수신 오류: {str(e)}")
                    break
    
    except Exception as e:
        logger.error(f"❌ 웹소켓 연결 오류: {str(e)}")
    
    logger.info("👋 연결 종료")

async def main():
    """메인 함수"""
    logger.info("🚀 웹소켓 디버깅 클라이언트 시작")
    
    try:
        # 최대 30초 동안 실행
        await asyncio.wait_for(websocket_client(), timeout=30)
    except asyncio.TimeoutError:
        logger.info("⏱️ 30초 시간제한 도달")
    except Exception as e:
        logger.error(f"❌ 예기치 않은 오류: {str(e)}")
    
    logger.info("✅ 디버깅 클라이언트 종료")

if __name__ == "__main__":
    asyncio.run(main())
