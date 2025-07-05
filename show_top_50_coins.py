#!/usr/bin/env python3
"""
모든 거래소에서 거래량 상위 50개 코인 조회
"""

import asyncio
import sys
import os

# 경로 추가
sys.path.append('/Users/danielkwon/DantaroCentral/backend')

from app.domain.recommenders.coin_recommender import CoinRecommender


async def show_top_50_coins():
    """모든 거래소에서 거래량 상위 50개 코인 출력"""
    print("=" * 80)
    print("🏆 거래량 기준 상위 50개 코인 - 전체 거래소")
    print("=" * 80)
    
    recommender = CoinRecommender()
    
    exchanges = ['upbit', 'okx', 'gateio', 'bybit', 'bithumb', 'coinone']
    
    for exchange in exchanges:
        print(f"\n📊 {exchange.upper()} 거래소 - 상위 50개 코인")
        print("-" * 60)
        
        try:
            # 상위 50개 코인 조회
            top_coins = await recommender.get_recommendations(
                exchange=exchange, 
                limit=50
            )
            
            if top_coins:
                print(f"✅ 총 {len(top_coins)}개 코인 발견\n")
                
                for i, coin in enumerate(top_coins, 1):
                    # 거래량 정보
                    if exchange in ['upbit', 'bithumb', 'coinone']:
                        volume_display = f"{coin.get('volume_24h_krw', 0):,.0f}원"
                    else:
                        volume_display = f"${coin.get('volume_24h_usdt', 0):,.0f}"
                    
                    # 가격 정보
                    price = coin.get('price', coin.get('current_price', 0))
                    change_24h = coin.get('change_24h', 0)
                    recommendation = coin.get('recommendation', 'N/A')
                    confidence = coin.get('confidence', 0)
                    
                    print(f"{i:2d}. {coin['symbol']:12s} "
                          f"💰 {price:12,.4f} "
                          f"📈 {change_24h:+6.2f}% "
                          f"📊 {volume_display:>15s} "
                          f"🎯 {recommendation:12s} "
                          f"✨ {confidence:.2f}")
                    
                    # 10개마다 구분선
                    if i % 10 == 0 and i < len(top_coins):
                        print("   " + "·" * 50)
                        
            else:
                print(f"❌ {exchange}: 데이터를 가져올 수 없음")
                
        except Exception as e:
            print(f"❌ {exchange}: 오류 발생 - {e}")
        
        print("\n" + "=" * 80)
    
    # 전체 요약
    print("\n🔍 전체 거래소 요약")
    print("-" * 40)
    
    try:
        all_results = await recommender.get_recommendations_by_exchange(
            exchange_names=exchanges,
            limit=50
        )
        
        total_coins = 0
        working_exchanges = 0
        
        for exchange, coins in all_results.items():
            coin_count = len(coins)
            total_coins += coin_count
            if coin_count > 0:
                working_exchanges += 1
            
            status = "✅" if coin_count > 0 else "❌"
            print(f"{status} {exchange:10s}: {coin_count:2d}개 코인")
        
        print(f"\n📊 전체 통계:")
        print(f"   - 작동 중인 거래소: {working_exchanges}/{len(exchanges)}개")
        print(f"   - 총 추천 코인: {total_coins}개")
        print(f"   - 평균 코인/거래소: {total_coins/max(working_exchanges, 1):.1f}개")
        
    except Exception as e:
        print(f"❌ 전체 요약 오류: {e}")


if __name__ == "__main__":
    asyncio.run(show_top_50_coins())
