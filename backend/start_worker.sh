#!/bin/bash
# Analysis Worker Startup Script

# 가상환경 활성화
source ../venv/bin/activate

# 워커 실행
echo "Starting Dantaro Central Analysis Worker..."
python analysis_worker.py
