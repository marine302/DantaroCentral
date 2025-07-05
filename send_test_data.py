#!/usr/bin/env python3
"""
WebSocket으로 테스트 데이터를 전송하는 스크립트
"""
import asyncio
import sys
import os
from datetime import datetime
import random

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.api.v1.endpoints.websocket import connection_manager

async def send_test_data():
    """테스트 데이터 전송"""
    print("🧪 테스트 데이터 전송 시작...")
    
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
    
    # 모의 차익거래 기회
    arbitrage_data = []
    for _ in range(3):
        symbol = random.choice(symbols)
        buy_exchange = random.choice(exchanges)
        sell_exchange = random.choice([ex for ex in exchanges if ex != buy_exchange])
        
        buy_price = round(random.uniform(30000, 35000), 2)
        sell_price = round(buy_price * random.uniform(1.001, 1.005), 2)
        spread = round(((sell_price - buy_price) / buy_price) * 100, 3)
        
        arbitrage_data.append({
            'symbol': symbol,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'spread_percentage': spread,
            'confidence': round(random.uniform(0.7, 0.99), 2),
            'volume': round(random.uniform(100000, 1000000), 2)
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
    
    # 데이터 전송
    if connection_manager.active_connections:
        print(f"📡 {len(connection_manager.active_connections)}개 연결에 데이터 전송 중...")
        
        # 가격 데이터 전송
        await connection_manager.broadcast_to_all({
            "type": "price_update",
            "data": price_data,
            "timestamp": datetime.now().isoformat()
        })
        print("✅ 가격 데이터 전송 완료")
        
        # 차익거래 데이터 전송
        await connection_manager.broadcast_to_all({
            "type": "arbitrage_opportunities",
            "data": arbitrage_data,
            "timestamp": datetime.now().isoformat()
        })
        print("✅ 차익거래 데이터 전송 완료")
        
        # 김치 프리미엄 데이터 전송
        await connection_manager.broadcast_to_all({
            "type": "kimchi_premium",
            "data": kimchi_data,
            "timestamp": datetime.now().isoformat()
        })
        print("✅ 김치 프리미엄 데이터 전송 완료")
        
    else:
        print("⚠️ 활성화된 WebSocket 연결이 없습니다.")

if __name__ == "__main__":
    asyncio.run(send_test_data())
