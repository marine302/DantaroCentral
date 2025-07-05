"""
Dantaro Central 직접 API 테스트 스크립트

이 스크립트는 실행 중인 서버에 직접 API 요청을 보내 응답을 확인합니다.
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8001/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "test-api-key-for-enterprise-servers"
}

# 테스트할 엔드포인트 목록
ENDPOINTS = [
    "/health",
    "/recommendations",
    "/market-status",
    "/support-levels/BTC",
]

async def test_api():
    """모든 엔드포인트에 요청을 보내고 응답을 확인"""
    print("\n===== Dantaro Central API 직접 테스트 =====\n")
    
    async with aiohttp.ClientSession() as session:
        for endpoint in ENDPOINTS:
            url = f"{API_BASE_URL}{endpoint}"
            print(f"엔드포인트 테스트 중: {endpoint}...")
            
            try:
                start_time = time.time()
                async with session.get(url, headers=HEADERS) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 성공 ({response_time:.2f}초)")
                        
                        # 특별 처리 - 추천 데이터
                        if endpoint == "/recommendations":
                            print(f"  - 추천 코인 수: {len(data.get('recommendations', []))}")
                            print(f"  - 데이터 소스: {data.get('data_source', 'unknown')}")
                            print(f"  - 캐시 타임스탬프: {data.get('cache_timestamp', 'unknown')}")
                            
                            # 첫 번째 추천 분석
                            if data.get('recommendations'):
                                rec = data['recommendations'][0]
                                print(f"\n  첫 번째 추천 코인: {rec.get('symbol', 'unknown')}")
                                print(f"  - 총점: {rec.get('total_score', 0)}")
                                print(f"  - 거래량 점수: {rec.get('volume_score', 0)}")
                                
                                # 볼륨 기반 분석 확인
                                if rec.get('analysis_details') and 'analysis_method' in rec.get('analysis_details', {}):
                                    print(f"  - 분석 방법: {rec['analysis_details']['analysis_method']}")
                                    if rec['analysis_details']['analysis_method'] == 'volume_based':
                                        print("  ✅ 볼륨 기반 분석 확인됨!")
                                    else:
                                        print("  ⚠️ 분석 방법이 볼륨 기반이 아닙니다.")
                                else:
                                    print("  ⚠️ 분석 방법 정보가 없습니다.")
                        
                        # 특별 처리 - 상태 정보
                        elif endpoint == "/health":
                            print(f"  - 서버 상태: {data.get('api_server', 'unknown')}")
                            print(f"  - 워커 상태: {data.get('workers', {}).get('status', 'unknown')}")
                            print(f"  - 활성 워커: {data.get('workers', {}).get('active_count', 0)}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 실패 ({response.status}): {error_text}")
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
            
            print("")  # 줄바꿈
    
    print("===== 모든 테스트 완료 =====")

if __name__ == "__main__":
    asyncio.run(test_api())
