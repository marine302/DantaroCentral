#!/bin/bash

# Dantaro Central 시작 스크립트

echo "🚀 Starting Dantaro Central Server..."
echo "======================================"

# 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다."
    echo "   다음 명령어를 실행하세요: source venv/bin/activate"
    exit 1
fi

# backend 디렉토리로 이동
cd "$(dirname "$0")/backend"

# PYTHONPATH 설정
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 서버 실행
echo "🌐 서버가 http://localhost:8001 에서 시작됩니다..."
echo "📚 API 문서: http://localhost:8001/docs"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
