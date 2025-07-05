"""
Dantaro Central 서버의 백그라운드 작업 상태를 확인하는 테스트 스크립트
"""
import asyncio
import json
import time
import sys
import aiohttp
from datetime import datetime

# 서버 URL 및 엔드포인트 설정
BASE_URL = "http://localhost:8001"
HEALTH_URL = f"{BASE_URL}/api/v1/health"
RECOMMENDATIONS_URL = f"{BASE_URL}/api/v1/recommendations"
MARKET_STATUS_URL = f"{BASE_URL}/api/v1/market-status"

async def check_background_tasks():
    """백그라운드 작업이 제대로 실행되고 있는지 확인"""
    print("\n====== Dantaro Central 백그라운드 태스크 상태 확인 ======")
    
    # 비동기 HTTP 클라이언트 생성
    async with aiohttp.ClientSession() as session:
        # 1. 서버 상태 확인
        print("\n1. 서버 상태 확인 중...")
        try:
            async with session.get(HEALTH_URL) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ 서버 상태: {health_data.get('api_server', 'unknown')}")
                    print(f"✅ 데이터베이스 상태: {health_data.get('database', {}).get('status', 'unknown')}")
                    print(f"✅ 캐시 상태: {health_data.get('cache', {}).get('status', 'unknown')}")
                    print(f"✅ 워커 상태: {health_data.get('workers', {}).get('status', 'unknown')}")
                    
                    # 워커 활동 확인
                    if health_data.get('workers', {}).get('active_count', 0) == 0:
                        print("⚠️ 주의: 활성화된 워커가 없습니다! 백그라운드 작업이 실행되지 않을 수 있습니다.")
                    
                else:
                    print(f"❌ 서버 상태 확인 실패: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 서버 연결 실패: {e}")
            return False
        
        # 2. 추천 데이터 확인
        print("\n2. 추천 데이터 확인 중...")
        try:
            async with session.get(RECOMMENDATIONS_URL) as response:
                if response.status == 200:
                    rec_data = await response.json()
                    print(f"✅ 추천 데이터 소스: {rec_data.get('data_source', 'unknown')}")
                    print(f"✅ 캐시 타임스탬프: {rec_data.get('cache_timestamp', 'unknown')}")
                    print(f"✅ 추천 코인 수: {len(rec_data.get('recommendations', []))}")
                    
                    # 데이터가 최신인지 확인
                    if rec_data.get('cache_timestamp'):
                        cache_time = datetime.fromisoformat(rec_data['cache_timestamp'].replace('Z', '+00:00'))
                        now = datetime.utcnow()
                        age_minutes = (now - cache_time).total_seconds() / 60
                        
                        if age_minutes > 10:
                            print(f"⚠️ 주의: 데이터가 {age_minutes:.1f}분 지났습니다! 백그라운드 작업이 실행되지 않을 수 있습니다.")
                        else:
                            print(f"✅ 데이터 나이: {age_minutes:.1f}분 (최신 상태)")
                    
                    # 첫 번째 추천 데이터 확인
                    if rec_data.get('recommendations'):
                        first_rec = rec_data['recommendations'][0]
                        print("\n첫 번째 추천 코인 정보:")
                        print(f"  심볼: {first_rec.get('symbol')}")
                        print(f"  총점: {first_rec.get('total_score')}")
                        print(f"  거래량 점수: {first_rec.get('volume_score')}")
                        print(f"  변동성 점수: {first_rec.get('volatility_score')}")
                        print(f"  현재 가격: {first_rec.get('current_price')}")
                        
                        # 이 부분이 매우 중요: 실제 추천이 볼륨 기반인지 확인
                        if first_rec.get('analysis_details') and first_rec['analysis_details'].get('analysis_method') == 'volume_based':
                            print("✅ 거래량 기반 분석 방식이 사용되었습니다!")
                        else:
                            print("⚠️ 주의: 추천에 거래량 기반 분석 표시가 없습니다.")
                else:
                    print(f"❌ 추천 데이터 확인 실패: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 추천 데이터 확인 실패: {e}")
        
        # 3. 시장 상태 확인
        print("\n3. 시장 상태 확인 중...")
        try:
            async with session.get(MARKET_STATUS_URL) as response:
                if response.status == 200:
                    market_data = await response.json()
                    print(f"✅ 시장 상태: {market_data.get('market_status', {}).get('overall_sentiment', 'unknown')}")
                    print(f"✅ 데이터 소스: {market_data.get('data_source', 'unknown')}")
                    print(f"✅ 데이터 타임스탬프: {market_data.get('cache_timestamp', 'unknown')}")
                else:
                    print(f"❌ 시장 상태 확인 실패: HTTP {response.status}")
        except Exception as e:
            print(f"❌ 시장 상태 확인 실패: {e}")
        
        print("\n====== 확인 완료 ======")
        print("참고: 백그라운드 작업이 정상적으로 실행되는지 확인하려면 서버 로그에서 다음과 같은 내용을 찾아보세요:")
        print("- '🔄 Analysis cycle completed'")
        print("- '✅ Updated volume-based recommendations'")
        print("- '총 {n}개 코인 데이터 수집 시작'")
        print("- '배치 수집 중: {x}-{y}/{z} 코인'")
        
        return True

if __name__ == "__main__":
    asyncio.run(check_background_tasks())
