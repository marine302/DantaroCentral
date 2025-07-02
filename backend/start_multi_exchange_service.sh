#!/bin/bash
"""
Dantaro Central 다중 거래소 실시간 서비스 시작 스크립트
OKX + Upbit WebSocket 통합 시스템
"""

# 컬러 출력 함수
print_header() {
    echo "🚀 Dantaro Central Multi-Exchange Service"
    echo "=================================================="
    echo "OKX + Upbit 실시간 데이터 수집 시스템"
    echo "시작 시간: $(date)"
    echo "=================================================="
}

print_status() {
    echo "📋 $1"
}

print_success() {
    echo "✅ $1"
}

print_error() {
    echo "❌ $1"
}

print_warning() {
    echo "⚠️ $1"
}

# 메인 실행
main() {
    print_header
    
    # Python 환경 확인
    if ! command -v python3 &> /dev/null; then
        print_error "Python3가 설치되지 않았습니다"
        exit 1
    fi
    
    print_success "Python3 환경 확인됨"
    
    # 작업 디렉토리 이동
    cd "$(dirname "$0")" || exit 1
    print_success "작업 디렉토리: $(pwd)"
    
    # 의존성 확인
    print_status "의존성 패키지 확인 중..."
    python3 -c "import websockets, aiohttp" 2>/dev/null
    if [ $? -ne 0 ]; then
        print_warning "일부 패키지가 누락되었을 수 있습니다"
        print_status "pip install -r requirements.txt 실행을 권장합니다"
    else
        print_success "필수 패키지 확인됨"
    fi
    
    # 환경설정 확인
    print_status "환경설정 확인 중..."
    if [ -f ".env" ]; then
        print_success "환경설정 파일 발견됨"
        
        # API 키 상태 체크
        python3 -c "
from app.core.config import settings
import sys

exchanges = []
if settings.okx_api_key:
    exchanges.append('OKX')
exchanges.append('Upbit')  # 공개 API

if exchanges:
    print('✅ 사용 가능한 거래소:', ', '.join(exchanges))
else:
    print('❌ 설정된 거래소가 없습니다')
    sys.exit(1)
"
        if [ $? -ne 0 ]; then
            print_error "API 키 설정을 확인하세요"
            print_status "python3 setup_production_keys.py 실행 권장"
            exit 1
        fi
    else
        print_error ".env 파일이 없습니다"
        print_status "python3 setup_production_keys.py 실행 필요"
        exit 1
    fi
    
    # 로그 디렉토리 생성
    mkdir -p logs
    print_success "로그 디렉토리 준비됨"
    
    # 서비스 시작
    print_status "다중 거래소 실시간 서비스 시작..."
    echo ""
    
    # 서비스 실행 (Ctrl+C로 종료 가능)
    python3 dantaro_multi_exchange_service.py
    
    echo ""
    print_status "서비스가 종료되었습니다"
}

# 시그널 핸들러
trap 'echo ""; print_status "서비스 종료 중..."; exit 0' INT TERM

# 스크립트 실행
main "$@"
