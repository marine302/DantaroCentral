#!/usr/bin/env python3
"""
거래량 정렬 검증 테스트
"""

import asyncio
import sys
import os

# 경로 추가
sys.path.append('/Users/danielkwon/DantaroCentral/backend')

from app.domain.recommenders.coin_recommender import CoinRecommender


async def verify_volume_sorting():
    """거래량 정렬이 올바른지 검증"""
    print("=" * 80)
    print("🔍 거래량 정렬 검증 테스트")
    print("=" * 80)
    
    recommender = CoinRecommender()
    
    exchanges = ['upbit', 'okx', 'gateio', 'bybit', 'bithumb', 'coinone']
    
    for exchange in exchanges:
        print(f"\n📊 {exchange.upper()} 거래소 - 거래량 정렬 검증")
        print("-" * 60)
        
        try:
            # 상위 10개만 확인
            top_coins = await recommender.get_recommendations(
                exchange=exchange, 
                limit=10
            )
            
            if top_coins:
                print(f"✅ 총 {len(top_coins)}개 코인")
                
                # 거래량 필드 확인
                volume_key = None
                if exchange in ['upbit', 'bithumb', 'coinone']:
                    volume_key = 'volume_24h_krw'
                    currency = '원'
                else:
                    volume_key = 'volume_24h_usdt'
                    currency = 'USD'
                
                print(f"정렬 기준: {volume_key}")
                print()
                
                prev_volume = float('inf')
                is_sorted = True
                
                for i, coin in enumerate(top_coins, 1):
                    volume = coin.get(volume_key, 0)
                    
                    # 정렬 검증
                    if volume > prev_volume:
                        is_sorted = False
                        status = "❌ 정렬 오류"
                    else:
                        status = "✅"
                    
                    print(f"{i:2d}. {coin['symbol']:12s} "
                          f"📊 {volume:15,.0f}{currency} "
                          f"{status}")
                    
                    prev_volume = volume
                
                print(f"\n🎯 정렬 상태: {'✅ 올바름' if is_sorted else '❌ 오류 발견'}")
                
                if not is_sorted:
                    print("⚠️  정렬 알고리즘 확인 필요!")
                    
            else:
                print(f"❌ {exchange}: 데이터 없음")
                
        except Exception as e:
            print(f"❌ {exchange}: 오류 - {e}")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(verify_volume_sorting())
