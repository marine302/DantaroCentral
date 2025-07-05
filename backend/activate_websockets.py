#!/usr/bin/env python3
"""
기존 WebSocket 시스템 활성화 스크립트
이미 구축된 다중 거래소 WebSocket을 간단히 활성화
"""

import asyncio
import logging
from app.services.websocket_data_manager import MultiExchangeWebSocketManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def activate_websockets():
    """기존 WebSocket 시스템 활성화"""
    
    # WebSocket 매니저 생성
    manager = MultiExchangeWebSocketManager()
    
    # 거래소 설정 (API 키 없이도 공개 데이터 수집 가능)
    exchange_configs = {
        'okx': {},
        'upbit': {},
        'coinone': {},
        'gate': {}
    }
    
    # WebSocket 초기화
    await manager.initialize_websockets(exchange_configs)
    
    # 주요 심볼 구독
    symbols = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'XRP/USDT',
        'DOT/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT', 'MATIC/USDT'
    ]
    
    # 각 거래소에서 심볼 구독
    symbols_by_exchange = {exchange: symbols for exchange in exchange_configs.keys()}
    await manager.subscribe_to_symbols(symbols_by_exchange)
    
    # 데이터 수집 시작
    await manager.start_listening()
    
    logger.info("✅ WebSocket 시스템 활성화 완료")
    
    # 계속 실행
    try:
        while True:
            await asyncio.sleep(10)
            stats = manager.get_stats()
            logger.info(f"📊 수집 통계: {stats}")
    except KeyboardInterrupt:
        logger.info("WebSocket 시스템 종료")
        await manager.stop_all_websockets()

if __name__ == "__main__":
    asyncio.run(activate_websockets())
