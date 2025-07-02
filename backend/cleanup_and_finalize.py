#!/usr/bin/env python3
"""
테스트 코드 정리 스크립트
개발/테스트용 파일들을 정리하고 프로덕션 파일만 유지
"""
import os
import shutil
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_test_files():
    """테스트 파일들 정리"""
    logger.info("🧹 테스트 파일 정리 시작")
    
    # 개발/테스트용 파일들 (선택적 정리)
    test_files = [
        'test_simple_websocket.py',
        'test_simple_data.py', 
        'test_quick_realtime.py',
        'test_websocket_realtime.py',
        'test_realtime_integration.py',
        'test_final_verification.py',
        'run_realtime_service.py',  # 이전 버전, dantaro_realtime_service.py로 대체됨
    ]
    
    # 테스트 파일들을 test/ 디렉토리로 이동
    test_dir = 'tests'
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        logger.info(f"✅ {test_dir} 디렉토리 생성")
    
    moved_count = 0
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                shutil.move(test_file, os.path.join(test_dir, test_file))
                logger.info(f"📁 {test_file} → {test_dir}/")
                moved_count += 1
            except Exception as e:
                logger.warning(f"⚠️ {test_file} 이동 실패: {e}")
    
    logger.info(f"✅ {moved_count}개 테스트 파일 정리 완료")

def create_production_readme():
    """프로덕션 환경용 README 생성"""
    readme_content = """# Dantaro Central - 실시간 데이터 수집 시스템

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# API 키 설정
python3 setup_production_keys.py

# 시스템 검증
python3 verify_realtime_system.py
```

### 2. 서비스 시작
```bash
# 권장: 스타트업 스크립트 사용
./start_realtime_service.sh

# 또는 직접 실행
python3 dantaro_realtime_service.py
```

## 📋 주요 파일

- `dantaro_realtime_service.py` - 메인 실시간 서비스
- `verify_realtime_system.py` - 시스템 검증 도구
- `start_realtime_service.sh` - 서비스 시작 스크립트
- `setup_production_keys.py` - API 키 설정 도구

## 📁 디렉토리 구조

```
backend/
├── dantaro_realtime_service.py      # 메인 서비스
├── verify_realtime_system.py        # 검증 도구
├── start_realtime_service.sh        # 시작 스크립트
├── app/services/                    # 핵심 서비스들
│   ├── okx_websocket.py            # OKX WebSocket 클라이언트
│   ├── websocket_data_manager.py   # 실시간 데이터 관리
│   └── market_data_collector.py    # 통합 데이터 수집
├── tests/                          # 테스트 파일들
└── logs/                           # 서비스 로그
```

## 🔍 모니터링

서비스 실행 시 실시간 로그를 통해 상태를 확인할 수 있습니다:

```
📊 BTC-USDT: $45,123.45 (Vol: 1,234,567)
📈 서비스 상태 - 가동시간: 15.3분, 총 메시지: 1,247개
```

자세한 내용은 `docs/production-realtime-system.md`를 참조하세요.
"""
    
    with open('README_PRODUCTION.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logger.info("✅ 프로덕션 README 생성 완료")

def main():
    logger.info("📦 Dantaro Central 프로덕션 적용 정리")
    
    # 테스트 파일 정리
    cleanup_test_files()
    
    # 프로덕션 README 생성
    create_production_readme()
    
    logger.info("\n🎉 프로덕션 적용 정리 완료!")
    logger.info("✅ 핵심 프로덕션 파일들:")
    logger.info("   - dantaro_realtime_service.py (메인 서비스)")
    logger.info("   - verify_realtime_system.py (시스템 검증)")
    logger.info("   - start_realtime_service.sh (시작 스크립트)")
    logger.info("   - README_PRODUCTION.md (운영 가이드)")
    
    logger.info("\n🚀 실시간 서비스 시작:")
    logger.info("   ./start_realtime_service.sh")

if __name__ == "__main__":
    main()
