#!/usr/bin/env python3
"""
빠른 프로덕션 API 테스트
"""

import asyncio
import os
import sys
from pathlib import Path

# 환경 변수 로드
sys.path.append('/Users/danielkwon/DantaroCentral/backend')
from dotenv import load_dotenv
load_dotenv('/Users/danielkwon/DantaroCentral/backend/.env')

from app.exchanges.factory import ExchangeFactory

async def quick_api_test():
    """빠른 API 연결 테스트"""
    print("🚀 프로덕션 API 키 테스트 시작...")
    
    # OKX 테스트 (이미 설정되어 있음)
    okx_credentials = {
        'api_key': os.getenv('OKX_API_KEY'),
        'secret_key': os.getenv('OKX_SECRET_KEY'),
        'passphrase': os.getenv('OKX_PASSPHRASE')
    }
    
    if all(okx_credentials.values()) and not any(v and v.startswith('your-') for v in okx_credentials.values()):
        print("🔧 OKX API 키 발견, 연결 테스트 중...")
        
        try:
            # OKX 거래소 인스턴스 생성
            exchange = ExchangeFactory.create_exchange('okx', **okx_credentials)
            
            # BTC 시세 가져오기
            ticker = await exchange.get_ticker('BTC-USDT')
            
            print(f"✅ OKX 연결 성공!")
            print(f"📈 BTC-USDT: ${ticker.price:,.2f}")
            print(f"📊 24h Volume: {ticker.volume:,.0f}")
            print(f"🕒 시간: {ticker.timestamp}")
            
            # 리소스 정리
            if hasattr(exchange, 'close'):
                await exchange.close()
            
            return True
            
        except Exception as e:
            print(f"❌ OKX 연결 실패: {e}")
            return False
    else:
        print("❌ OKX API 키가 설정되지 않았습니다.")
        return False

async def test_market_data_collector():
    """MarketDataCollector 테스트"""
    print("\n🔧 MarketDataCollector 테스트...")
    
    try:
        from app.services.market_data_collector import MarketDataCollector
        
        # MarketDataCollector 생성
        collector = MarketDataCollector()
        
        # OKX 설정
        okx_config = {
            'okx': {
                'api_key': os.getenv('OKX_API_KEY'),
                'secret_key': os.getenv('OKX_SECRET_KEY'),
                'passphrase': os.getenv('OKX_PASSPHRASE')
            }
        }
        
        if all(okx_config['okx'].values()):
            collector.configure_exchanges(okx_config)
            collector.set_target_symbols(['BTC-USDT', 'ETH-USDT', 'SOL-USDT'])
            
            print("📊 실제 데이터 수집 중...")
            data_points = await collector.collect_all_data()
            
            print(f"✅ {len(data_points)}개 데이터 포인트 수집 완료!")
            
            for point in data_points:
                print(f"📈 {point.symbol}: ${point.price:,.2f} | 거래량: {point.volume_24h:,.0f} | 거래소: {point.exchange}")
            
            # 리소스 정리
            for exchange in collector.exchanges.values():
                if hasattr(exchange, 'close'):
                    await exchange.close()
            
            return True
        else:
            print("❌ API 키가 설정되지 않았습니다.")
            return False
            
    except Exception as e:
        print(f"❌ MarketDataCollector 테스트 실패: {e}")
        return False

async def main():
    print("🎯 Dantaro Central 프로덕션 API 테스트")
    print("=" * 50)
    
    # 1. 기본 API 연결 테스트
    api_success = await quick_api_test()
    
    # 2. MarketDataCollector 테스트
    if api_success:
        collector_success = await test_market_data_collector()
        
        if collector_success:
            print("\n🎉 모든 테스트 성공!")
            print("💡 다음 단계: Analysis Worker 실행 가능")
            print("   실행 명령: python analysis_worker.py")
        else:
            print("\n⚠️ MarketDataCollector 테스트 실패")
    else:
        print("\n❌ API 연결 테스트 실패")
        print("💡 API 키를 다시 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())
