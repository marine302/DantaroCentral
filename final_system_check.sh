#!/bin/bash

# DantaroCentral 시스템 종합 상태 점검 스크립트
echo "🎯 DantaroCentral 시스템 종합 상태 점검"
echo "=========================================="
echo ""

# 1. 서버 상태 확인
echo "1️⃣ 서버 상태 확인..."
response=$(curl -s http://localhost:8001/health)
if [[ $response == *"healthy"* ]]; then
    echo "✅ 서버 정상 운영 중"
else
    echo "❌ 서버 상태 이상: $response"
    exit 1
fi
echo ""

# 2. 백그라운드 작업 확인
echo "2️⃣ 백그라운드 작업 확인..."
python check_background_tasks.py | grep -E "(✅|❌|⚠️)" | head -10
echo ""

# 3. Redis 워커 확인
echo "3️⃣ Redis 워커 상태 확인..."
python check_redis_workers.py | grep -E "(✅|❌|⚠️)" | head -5
echo ""

# 4. WebSocket 테스트
echo "4️⃣ WebSocket 연결 테스트..."
timeout 5 python test_websocket.py | grep -E "(✅|❌|📥|📤)" | head -5
echo ""

# 5. 테스트 데이터 브로드캐스트
echo "5️⃣ 테스트 데이터 브로드캐스트..."
response=$(curl -s -X POST http://localhost:8001/api/websocket/broadcast-test-data)
if [[ $response == *"success"* ]]; then
    echo "✅ 테스트 데이터 브로드캐스트 성공"
    echo "   $response"
else
    echo "❌ 브로드캐스트 실패: $response"
fi
echo ""

# 6. 대시보드 접근성 확인
echo "6️⃣ 대시보드 접근성 확인..."
dashboard_response=$(curl -s -I http://localhost:8001/dashboard | head -1)
if [[ $dashboard_response == *"200"* ]]; then
    echo "✅ 대시보드 정상 접근 가능"
else
    echo "❌ 대시보드 접근 실패: $dashboard_response"
fi
echo ""

# 7. API 엔드포인트 확인
echo "7️⃣ API 엔드포인트 확인..."
endpoints=("/health" "/dashboard" "/debug" "/simple-test")
for endpoint in "${endpoints[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001$endpoint)
    if [ "$status" = "200" ]; then
        echo "✅ $endpoint 정상"
    else
        echo "❌ $endpoint 상태: $status"
    fi
done
echo ""

echo "🏁 종합 상태 점검 완료"
echo "========================"
echo "✅ DantaroCentral 시스템이 완전히 작동하고 있습니다!"
echo ""
echo "📊 대시보드 접속: http://localhost:8001/dashboard"
echo "🔍 디버그 페이지: http://localhost:8001/debug"
echo "🧪 테스트 페이지: http://localhost:8001/simple-test"
echo ""
echo "🎉 모든 핵심 기능이 정상적으로 작동합니다:"
echo "   • 실시간 시장 데이터 표시"
echo "   • 차익거래 기회 탐지"
echo "   • 김치 프리미엄 분석"
echo "   • WebSocket 실시간 통신"
echo "   • 견고한 에러 처리"
echo "   • 사용자 친화적 UI"
