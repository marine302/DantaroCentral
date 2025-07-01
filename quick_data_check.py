#!/usr/bin/env python3
"""
Quick data collection test without full server.
"""
import sys
import os
import asyncio
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def quick_data_check():
    """Quick check of collected data without starting full server."""
    print("🔍 Quick Data Collection Check")
    print("=" * 50)
    
    try:
        # Test 1: Real market service
        print("\n📊 1. Testing Real Market Data Service...")
        from app.services.real_market_service import RealMarketDataService
        
        market_service = RealMarketDataService()
        market_data = await market_service.get_market_data()
        
        if market_data:
            print(f"✅ Connected to Upbit - {len(market_data)} coins available")
            
            # Show sample of top 5 coins
            print("\n🏆 Top 5 Coins Sample:")
            count = 0
            for symbol, data in market_data.items():
                if count >= 5:
                    break
                print(f"   {symbol}: ${data.get('current_price', 0):,.0f} "
                      f"({data.get('price_change_24h', 0)*100:+.1f}%) "
                      f"Vol: ${data.get('volume_24h', 0):,.0f}")
                count += 1
        else:
            print("❌ No market data available")
            
    except Exception as e:
        print(f"❌ Market data error: {e}")
    
    try:
        # Test 2: Quick recommendation 
        print("\n🎯 2. Testing Quick Recommendation...")
        from app.domain.recommenders.advanced_recommender import CoinRecommender
        
        recommender = CoinRecommender()
        if market_data:
            # Just get top 5 for speed
            top_recommendations = await recommender.get_recommendations(market_data, limit=5)
            
            print(f"✅ Generated {len(top_recommendations)} quick recommendations:")
            for i, rec in enumerate(top_recommendations[:3], 1):
                print(f"   {i}. {rec.symbol}: Score {rec.total_score:.2f} "
                      f"({rec.recommendation_strength})")
        
    except Exception as e:
        print(f"❌ Recommendation error: {e}")
    
    try:
        # Test 3: Cache service
        print("\n💾 3. Testing Cache Service...")
        from app.services.cache_service import CacheService
        
        cache_service = CacheService()
        
        # Test cache operations
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        await cache_service.set("test_key", test_data, ttl=60)
        
        cached_data = await cache_service.get("test_key")
        if cached_data:
            print("✅ Cache service working")
        else:
            print("❌ Cache service not working")
            
    except Exception as e:
        print(f"❌ Cache error: {e}")
    
    print(f"\n🕐 Data collection completed at: {datetime.now()}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(quick_data_check())
