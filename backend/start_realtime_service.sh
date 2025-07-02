#!/bin/bash
# Dantaro Central 실시간 데이터 수집 서비스 시작 스크립트

echo "🚀 Dantaro Central 실시간 데이터 수집 서비스 시작"
echo "====================================================="

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 작업 디렉토리: $SCRIPT_DIR"

# Python 환경 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되지 않았습니다."
    exit 1
fi

echo "✅ Python3 확인됨: $(python3 --version)"

# 로그 디렉토리 생성
mkdir -p logs
echo "✅ 로그 디렉토리 생성됨"

# API 키 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다."
    echo "다음 명령을 실행하여 API 키를 설정하세요:"
    echo "python3 setup_production_keys.py"
    exit 1
fi

echo "✅ 환경 설정 파일 확인됨"

# 시스템 검증 (선택사항)
read -p "🔍 시작 전 시스템 검증을 실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 시스템 검증 실행 중..."
    python3 verify_realtime_system.py
    
    if [ $? -ne 0 ]; then
        echo "❌ 시스템 검증 실패. 문제를 해결한 후 다시 시도하세요."
        exit 1
    fi
    
    echo "✅ 시스템 검증 완료"
fi

# 실시간 서비스 시작
echo "🚀 실시간 데이터 수집 서비스를 시작합니다..."
echo "중지하려면 Ctrl+C를 누르세요."
echo ""

# 서비스 실행
python3 dantaro_realtime_service.py

echo "✅ 서비스가 종료되었습니다."
