#!/usr/bin/env python3
"""
View cached data without heavy processing.
"""
import requests
import json
from datetime import datetime

def view_cached_data():
    """View only cached data for quick results."""
    print("🔍 Viewing Cached Collected Data")
    print("=" * 50)
    
    # Check if server is running
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Server status: {health.json()['status']}")
    except:
        print("❌ Server not running - starting minimal data view")
        return show_offline_data()
    
    headers = {"Authorization": "Bearer development-user-server-key"}
    
    try:
        # Get cached recommendations (should be fast)
        print("\n📊 Top Coin Recommendations (Cached):")
        resp = requests.get("http://localhost:8000/api/v1/recommendations", 
                          headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   📈 Total analyzed: {data['total_analyzed']} coins")
            print(f"   🕐 Cache timestamp: {data.get('cache_timestamp', 'N/A')}")
            
            print("\n🏆 Top 5 Recommendations:")
            for i, rec in enumerate(data['recommendations'][:5], 1):
                score = rec['total_score']
                symbol = rec['symbol']
                strength = rec['recommendation_strength']
                price = rec['metadata']['current_price']
                change = rec['metadata']['price_change_24h'] * 100
                
                print(f"   {i}. {symbol:<12} Score: {score:.3f} ({strength})")
                print(f"      Price: ₩{price:,.0f} ({change:+.1f}%)")
                
        else:
            print(f"   ❌ Error getting recommendations: {resp.status_code}")
            
    except requests.exceptions.Timeout:
        print("   ⏰ Request timeout - server is processing")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Quick market status
    try:
        print(f"\n🌍 Market Status:")
        resp = requests.get("http://localhost:8000/api/v1/market-status", 
                          headers=headers, timeout=10)
        
        if resp.status_code == 200:
            status = resp.json()
            print(f"   📊 Market sentiment: {status.get('market_status', 'Unknown')}")
            print(f"   💰 Total volume: ₩{status.get('total_volume_24h', 0):,.0f}")
            print(f"   📈 Data freshness: {status.get('data_freshness', 'N/A')}")
        
    except requests.exceptions.Timeout:
        print("   ⏰ Market status timeout")
    except Exception as e:
        print(f"   ❌ Market status error: {e}")
    
    print(f"\n🕐 Data viewed at: {datetime.now().strftime('%H:%M:%S')}")

def show_offline_data():
    """Show what data would be collected when server is running."""
    print("\n📋 Data Types Available When Server is Running:")
    print("=" * 50)
    
    print("🎯 1. Coin Recommendations (50 coins)")
    print("   - Technical analysis scores (RSI, MACD, Bollinger)")
    print("   - Volume trend analysis")
    print("   - Volatility metrics")
    print("   - Risk assessment")
    print("   - Combined recommendation strength")
    
    print("\n📈 2. Support/Resistance Levels")
    print("   - Aggressive support (7-day basis)")
    print("   - Moderate support (30-day basis)")  
    print("   - Conservative support (90-day basis)")
    
    print("\n🌍 3. Market Status")
    print("   - Overall market sentiment")
    print("   - Total 24h trading volume")
    print("   - Average market volatility")
    print("   - System health status")
    
    print("\n💾 4. Cached Performance")
    print("   - First call: ~100 seconds (real-time analysis)")
    print("   - Cached calls: ~0.01 seconds (200x faster)")
    print("   - Auto-refresh: Every 30 seconds")

if __name__ == "__main__":
    view_cached_data()
