#!/usr/bin/env python3
"""
Display collected market data in a readable format.
"""
import requests
import json
from datetime import datetime

def display_recommendations():
    """Display current coin recommendations."""
    url = "http://localhost:8000/api/v1/recommendations"
    headers = {"Authorization": "Bearer development-user-server-key"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            print("🏆 DANTARO CENTRAL - 코인 추천 현황")
            print("=" * 80)
            print(f"📅 캐시 타임스탬프: {data.get('cache_timestamp', 'N/A')}")
            print(f"📊 분석된 코인 수: {data.get('total_analyzed', 0)}")
            print(f"🎯 추천 코인 수: {len(data.get('recommendations', []))}")
            print()
            
            recommendations = data.get('recommendations', [])[:10]  # Top 10
            
            print("🥇 상위 10개 추천 코인")
            print("-" * 80)
            print(f"{'순위':<4} {'코인':<12} {'점수':<6} {'현재가':<12} {'24h 변동':<10} {'거래량(24h)':<15}")
            print("-" * 80)
            
            for i, rec in enumerate(recommendations, 1):
                symbol = rec.get('symbol', 'N/A')
                score = rec.get('total_score', 0)
                metadata = rec.get('metadata', {})
                price = metadata.get('current_price', 0)
                change = metadata.get('price_change_24h', 0)
                volume = metadata.get('volume_24h', 0)
                
                # Format numbers
                price_str = f"{price:,.0f}" if price else "N/A"
                change_str = f"{change*100:+.2f}%" if change else "N/A"
                volume_str = f"{volume/1e9:.1f}B" if volume > 1e9 else f"{volume/1e6:.1f}M" if volume > 1e6 else f"{volume:,.0f}"
                
                print(f"{i:<4} {symbol:<12} {score:.3f} {price_str:<12} {change_str:<10} {volume_str:<15}")
            
            return True
        else:
            print(f"❌ API 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        return False

def display_market_status():
    """Display market status."""
    url = "http://localhost:8000/api/v1/market-status"
    headers = {"Authorization": "Bearer development-user-server-key"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            print("\n📈 시장 상태 정보")
            print("=" * 80)
            
            status = data.get('market_status', {})
            print(f"💹 시장 심리: {status.get('sentiment', 'N/A')}")
            print(f"📊 총 거래량(24h): {status.get('total_volume_24h', 0)/1e12:.2f}조 KRW")
            print(f"📈 평균 변동성: {status.get('avg_volatility', 0)*100:.2f}%")
            print(f"🔄 마지막 업데이트: {status.get('last_update', 'N/A')}")
            
            # System health
            health = data.get('system_health', {})
            exchanges = health.get('exchanges', {})
            print(f"\n🏥 시스템 상태")
            print(f"   🟢 업비트: {exchanges.get('upbit', 'unknown')}")
            print(f"   ⚪ 바이낸스: {exchanges.get('binance', 'unknown')}")
            print(f"   ⚪ 빗썸: {exchanges.get('bithumb', 'unknown')}")
            
            return True
        else:
            print(f"❌ 시장 상태 API 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 시장 상태 연결 오류: {e}")
        return False

def display_support_levels(symbol="BTC"):
    """Display support levels for a specific coin."""
    url = f"http://localhost:8000/api/v1/support-levels/{symbol}"
    headers = {"Authorization": "Bearer development-user-server-key"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n🎯 {symbol} 지지선 분석")
            print("=" * 80)
            
            levels = data.get('support_levels', {})
            for level_type, level_data in levels.items():
                if isinstance(level_data, dict):
                    print(f"📊 {level_type.upper()}:")
                    print(f"   💰 지지선: {level_data.get('support', 'N/A'):,}")
                    print(f"   🎯 신뢰도: {level_data.get('confidence', 0)*100:.1f}%")
                    print(f"   📈 저항선: {level_data.get('resistance', 'N/A'):,}")
            
            metadata = data.get('metadata', {})
            print(f"\n📋 분석 정보")
            print(f"   📊 데이터 포인트: {metadata.get('price_data_points', 'N/A')}")
            print(f"   📅 조회 기간: {metadata.get('lookback_days', 'N/A')}일")
            
            return True
        else:
            print(f"❌ {symbol} 지지선 API 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ {symbol} 지지선 연결 오류: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DANTARO CENTRAL 수집 정보 현황")
    print("=" * 80)
    
    # Display recommendations
    if display_recommendations():
        print("\n" + "="*80)
    
    # Display market status
    if display_market_status():
        print("\n" + "="*80)
    
    # Display support levels for top coins
    top_coins = ["BTC", "ETH"]
    for coin in top_coins:
        if display_support_levels(coin):
            print("\n" + "="*80)
    
    print("\n✅ 데이터 조회 완료")
