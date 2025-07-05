"""
Dantaro Central 연속 모니터링 스크립트

이 스크립트는 Dantaro Central 서버의 상태와 추천 데이터를 
지속적으로 확인하여 실시간 업데이트 여부를 모니터링합니다.
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

# 설정
API_BASE_URL = "http://localhost:8001/api/v1"
CHECK_INTERVAL = 10  # 초 단위
MAX_CHECKS = 6  # 총 확인 횟수 (CHECK_INTERVAL * MAX_CHECKS 초 동안 모니터링)
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "test-api-key-for-enterprise-servers"
}

async def monitor_server():
    """서버 상태 및 추천 데이터를 주기적으로 모니터링"""
    print("\n===== Dantaro Central 실시간 모니터링 =====")
    print(f"서버를 {CHECK_INTERVAL}초 간격으로 {MAX_CHECKS}회 확인합니다.")
    print("실시간 백그라운드 작업이 실행 중인지 확인합니다.\n")
    
    health_data_history = []
    recommendation_data_history = []
    
    async with aiohttp.ClientSession() as session:
        for i in range(MAX_CHECKS):
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time}] 확인 #{i+1}/{MAX_CHECKS} 시작...")
            
            # 헬스 체크
            try:
                async with session.get(f"{API_BASE_URL}/health", headers=HEADERS) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        worker_status = health_data.get('workers', {}).get('status', 'unknown')
                        worker_count = health_data.get('workers', {}).get('active_count', 0)
                        print(f"✅ 서버 상태: {health_data.get('api_server', 'unknown')}")
                        print(f"✅ 워커 상태: {worker_status}")
                        print(f"✅ 활성 워커: {worker_count}")
                        
                        health_data_history.append({
                            'time': current_time,
                            'worker_status': worker_status,
                            'worker_count': worker_count
                        })
                    else:
                        print(f"❌ 헬스 체크 실패: HTTP {response.status}")
            except Exception as e:
                print(f"❌ 헬스 체크 오류: {e}")
            
            # 추천 데이터
            try:
                async with session.get(f"{API_BASE_URL}/recommendations", headers=HEADERS) as response:
                    if response.status == 200:
                        rec_data = await response.json()
                        timestamp = rec_data.get('cache_timestamp', 'unknown')
                        data_source = rec_data.get('data_source', 'unknown')
                        rec_count = len(rec_data.get('recommendations', []))
                        
                        print(f"✅ 추천 코인 수: {rec_count}")
                        print(f"✅ 데이터 소스: {data_source}")
                        print(f"✅ 타임스탬프: {timestamp}")
                        
                        # 첫 번째 추천 확인
                        if rec_data.get('recommendations'):
                            rec = rec_data['recommendations'][0]
                            print(f"✅ 첫 번째 추천: {rec.get('symbol')} (점수: {rec.get('total_score')})")
                            
                            # 분석 방법 확인
                            if rec.get('analysis_details') and 'analysis_method' in rec.get('analysis_details', {}):
                                method = rec['analysis_details']['analysis_method']
                                print(f"✅ 분석 방법: {method}")
                                if method == 'volume_based':
                                    print("✅ 볼륨 기반 분석 확인됨!")
                                else:
                                    print("⚠️ 볼륨 기반 분석이 아닙니다.")
                            else:
                                print("⚠️ 분석 방법 정보가 없습니다.")
                        
                        recommendation_data_history.append({
                            'time': current_time,
                            'timestamp': timestamp,
                            'data_source': data_source,
                            'rec_count': rec_count
                        })
                    else:
                        print(f"❌ 추천 데이터 확인 실패: HTTP {response.status}")
            except Exception as e:
                print(f"❌ 추천 데이터 확인 오류: {e}")
            
            # 마지막 확인이 아니면 대기
            if i < MAX_CHECKS - 1:
                print(f"\n다음 확인까지 {CHECK_INTERVAL}초 대기 중...")
                await asyncio.sleep(CHECK_INTERVAL)
    
    # 결과 분석
    print("\n===== 모니터링 결과 분석 =====")
    
    # 워커 상태 변화 확인
    print("\n1. 워커 상태 변화:")
    for i, data in enumerate(health_data_history):
        print(f"  확인 #{i+1}: {data['time']} - 워커: {data['worker_count']}개 ({data['worker_status']})")
    
    # 추천 데이터 타임스탬프 변화 확인
    print("\n2. 추천 데이터 변화:")
    timestamps = [data['timestamp'] for data in recommendation_data_history]
    unique_timestamps = set(timestamps)
    
    for i, data in enumerate(recommendation_data_history):
        print(f"  확인 #{i+1}: {data['time']} - 소스: {data['data_source']}, 타임스탬프: {data['timestamp']}")
    
    print(f"\n총 {len(unique_timestamps)}개의 고유 타임스탬프가 관찰되었습니다.")
    
    if len(unique_timestamps) > 1:
        print("✅ 추천 데이터가 모니터링 중에 최소 한 번 업데이트되었습니다.")
        print("✅ 실시간 백그라운드 작업이 실행 중인 것으로 보입니다.")
    else:
        print("⚠️ 모니터링 중 추천 데이터 업데이트가 관찰되지 않았습니다.")
        print("⚠️ 실시간 백그라운드 작업이 실행되지 않거나 업데이트 간격이 모니터링 시간보다 깁니다.")

if __name__ == "__main__":
    asyncio.run(monitor_server())
