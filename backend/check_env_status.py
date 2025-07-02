#!/usr/bin/env python3
"""
환경 변수 및 API 키 상태 확인
"""

import os
import sys
from pathlib import Path

# 백엔드 디렉토리 추가
backend_dir = Path('/Users/danielkwon/DantaroCentral/backend')
sys.path.append(str(backend_dir))

def check_env_status():
    """환경 변수 상태 확인"""
    
    # .env 파일 로드
    env_file = backend_dir / '.env'
    if not env_file.exists():
        return "❌ .env 파일이 존재하지 않습니다."
    
    # 환경 변수 파싱
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # API 키 상태 확인
    results = []
    results.append("🔍 API 키 상태 확인:")
    results.append("=" * 40)
    
    # OKX 확인
    okx_keys = ['OKX_API_KEY', 'OKX_SECRET_KEY', 'OKX_PASSPHRASE']
    okx_status = all(
        key in env_vars and env_vars[key] and not env_vars[key].startswith('your-')
        for key in okx_keys
    )
    results.append(f"OKX: {'✅ 설정됨' if okx_status else '❌ 미설정'}")
    
    # Coinone 확인
    coinone_keys = ['COINONE_API_KEY', 'COINONE_SECRET_KEY']
    coinone_status = all(
        key in env_vars and env_vars[key] and not env_vars[key].startswith('your-')
        for key in coinone_keys
    )
    results.append(f"Coinone: {'✅ 설정됨' if coinone_status else '❌ 미설정'}")
    
    # Gate.io 확인
    gate_keys = ['GATE_API_KEY', 'GATE_SECRET_KEY']
    gate_status = all(
        key in env_vars and env_vars[key] and not env_vars[key].startswith('your-')
        for key in gate_keys
    )
    results.append(f"Gate.io: {'✅ 설정됨' if gate_status else '❌ 미설정'}")
    
    results.append("=" * 40)
    
    if okx_status:
        results.append("🎉 OKX API 키가 설정되어 있습니다!")
        results.append("💡 실제 데이터 수집이 가능합니다.")
    else:
        results.append("⚠️ 설정된 API 키가 없습니다.")
        results.append("💡 setup_production_keys.py 실행 필요")
    
    return '\n'.join(results)

def check_imports():
    """중요 모듈 import 확인"""
    results = []
    results.append("\n🔧 모듈 Import 상태:")
    results.append("=" * 30)
    
    try:
        from app.exchanges.factory import ExchangeFactory
        results.append("✅ ExchangeFactory")
    except Exception as e:
        results.append(f"❌ ExchangeFactory: {e}")
    
    try:
        from app.services.market_data_collector import MarketDataCollector
        results.append("✅ MarketDataCollector")
    except Exception as e:
        results.append(f"❌ MarketDataCollector: {e}")
    
    try:
        from dotenv import load_dotenv
        results.append("✅ python-dotenv")
    except Exception as e:
        results.append(f"❌ python-dotenv: {e}")
    
    return '\n'.join(results)

def main():
    print("🚀 Dantaro Central 환경 상태 확인")
    print("=" * 50)
    
    # 환경 변수 상태
    env_status = check_env_status()
    print(env_status)
    
    # Import 상태
    import_status = check_imports()
    print(import_status)
    
    print("\n📋 다음 단계:")
    print("1. API 키가 설정되어 있다면: python analysis_worker.py")
    print("2. API 키가 없다면: python setup_production_keys.py")

if __name__ == "__main__":
    main()
