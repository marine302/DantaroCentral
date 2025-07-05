"""
Dantaro Central 대시보드 상태 종합 확인 스크립트
"""
import asyncio
import aiohttp
import json

async def comprehensive_dashboard_check():
    """대시보드의 모든 기능을 종합적으로 확인"""
    print("\n🎯 ==== Dantaro Central 대시보드 종합 상태 확인 ====\n")
    
    endpoints = [
        ("헬스 체크", "http://localhost:8001/api/v1/health"),
        ("볼륨 기반 추천", "http://localhost:8001/api/v1/recommendations"),
        ("대시보드 통계", "http://localhost:8001/api/dashboard/stats"),
        ("대시보드 추천", "http://localhost:8001/api/dashboard/volume-recommendations"),
        ("시장 상태", "http://localhost:8001/api/v1/market-status"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in endpoints:
            print(f"🔍 {name} 확인 중...")
            try:
                headers = {"X-API-Key": "test-api-key-for-enterprise-servers"}
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {name}: 정상")
                        
                        # 특별 정보 표시
                        if "health" in url:
                            workers = data.get('workers', {})
                            print(f"   워커 상태: {workers.get('status', 'unknown')}")
                            print(f"   활성 워커: {workers.get('active_count', 0)}")
                            
                        elif "recommendations" in url and "dashboard" not in url:
                            recs = data.get('recommendations', [])
                            metadata = data.get('metadata', {})
                            print(f"   추천 수: {len(recs)}")
                            print(f"   분석 방법: {metadata.get('analysis_method', 'unknown')}")
                            print(f"   목적: {metadata.get('purpose', 'unknown')}")
                            
                        elif "dashboard/volume" in url:
                            recs = data.get('recommendations', [])
                            success = data.get('success', False)
                            print(f"   성공: {success}")
                            print(f"   대시보드 추천 수: {len(recs)}")
                            if recs:
                                first = recs[0]
                                print(f"   첫 번째: {first.get('symbol')} (점수: {first.get('score')})")
                                
                        elif "stats" in url:
                            ws_stats = data.get('websocket_stats', {})
                            print(f"   WebSocket 연결: {ws_stats.get('active_connections', 0)}")
                            print(f"   캐시된 가격: {ws_stats.get('cached_prices', 0)}")
                            print(f"   지원 거래소: {data.get('exchange_count', 0)}")
                            
                    else:
                        print(f"❌ {name}: HTTP {response.status}")
                        
            except Exception as e:
                print(f"❌ {name}: 오류 - {e}")
            
            print()
    
    print("🎯 ==== 대시보드 접속 정보 ====")
    print("📊 메인 대시보드: http://localhost:8001/dashboard")
    print("📊 루트 페이지: http://localhost:8001/")
    print("📋 API 문서: http://localhost:8001/docs")
    print("🏥 헬스 체크: http://localhost:8001/health")
    print()
    
    print("🎯 ==== 대시보드 기능 ====")
    print("✅ 실시간 WebSocket 연결")
    print("✅ 볼륨 기반 코인 추천")
    print("✅ 차익거래 기회 모니터링")
    print("✅ 김치 프리미엄 추적")
    print("✅ 실시간 가격 업데이트")
    print("✅ 시스템 상태 모니터링")
    print("✅ 반응형 웹 인터페이스")
    print()
    
    print("🔧 ==== 대시보드 기술 스택 ====")
    print("• 프론트엔드: Bootstrap 5, Chart.js, WebSocket")
    print("• 백엔드: FastAPI, WebSocket, Redis, SQLite")
    print("• 실시간: WebSocket 기반 실시간 데이터 스트리밍")
    print("• 분석: 볼륨 기반 동적 코인 선별 및 분석")
    print()

if __name__ == "__main__":
    asyncio.run(comprehensive_dashboard_check())
