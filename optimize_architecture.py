#!/usr/bin/env python3
"""
DantaroCentral 아키텍처 최적화 스크립트
중복된 서비스들을 정리하고 핵심 서비스만 유지합니다.
"""
import os
import shutil
from pathlib import Path

def optimize_services():
    """서비스 디렉토리 최적화"""
    services_dir = Path(__file__).parent / "backend" / "app" / "services"
    
    print("🔧 서비스 아키텍처 최적화 시작...")
    
    # 제거할 중복/임시 서비스들
    services_to_remove = [
        "real_data_service.py",  # 새로운 clean 버전으로 대체됨
        "real_data_service_new.py",  # 실험 버전
        "real_data_service_old.py",  # 백업 버전
        "market_data_service.py",  # 중복
        "realtime_data_service.py",  # 중복
    ]
    
    # 유지할 핵심 서비스들
    core_services = [
        "real_data_service_clean.py",  # 메인 실시간 데이터 서비스
        "market_data_collector.py",   # 통합 데이터 수집기
        "simple_recommender.py",      # 추천 엔진
        "websocket_data_manager.py",  # WebSocket 관리
        "cache_service.py",           # 캐시 서비스
        "notification_service.py",    # 알림 서비스
        "real_market_service.py",     # 실제 마켓 서비스
        # WebSocket 클라이언트들
        "okx_websocket.py",
        "upbit_websocket.py", 
        "coinone_websocket.py",
        "gate_websocket.py"
    ]
    
    removed_count = 0
    
    # 중복 서비스 제거
    for service_file in services_to_remove:
        service_path = services_dir / service_file
        if service_path.exists():
            print(f"🗑️  제거: {service_file}")
            service_path.unlink()
            removed_count += 1
    
    print(f"\n✅ 서비스 최적화 완료! {removed_count}개 중복 서비스 제거됨")
    print(f"📦 유지된 핵심 서비스: {len(core_services)}개")
    
    # 핵심 서비스 목록 출력
    print("\n🔧 핵심 서비스 목록:")
    for service in core_services:
        service_path = services_dir / service
        if service_path.exists():
            print(f"  ✅ {service}")
        else:
            print(f"  ❌ {service} (누락)")

def rename_main_service():
    """메인 실시간 데이터 서비스의 이름을 정리"""
    services_dir = Path(__file__).parent / "backend" / "app" / "services"
    
    old_path = services_dir / "real_data_service_clean.py"
    new_path = services_dir / "real_data_service.py"
    
    if old_path.exists() and not new_path.exists():
        print(f"📝 {old_path.name} → {new_path.name}")
        shutil.move(str(old_path), str(new_path))
        print("✅ 메인 서비스 이름 정리 완료")

def create_services_readme():
    """서비스 디렉토리에 README 생성"""
    services_dir = Path(__file__).parent / "backend" / "app" / "services"
    readme_path = services_dir / "README.md"
    
    readme_content = """# 🔧 Services Layer - Dantaro Central

## 📦 핵심 서비스 구조

### 🌐 **데이터 수집 서비스**
- `real_data_service.py` - 메인 실시간 데이터 수집 서비스
- `market_data_collector.py` - 통합 마켓 데이터 수집기
- `websocket_data_manager.py` - WebSocket 연결 관리

### 🤖 **WebSocket 클라이언트**
- `okx_websocket.py` - OKX 거래소 WebSocket 클라이언트
- `upbit_websocket.py` - Upbit 거래소 WebSocket 클라이언트
- `coinone_websocket.py` - Coinone 거래소 WebSocket 클라이언트
- `gate_websocket.py` - Gate.io 거래소 WebSocket 클라이언트

### 🧠 **분석 및 추천**
- `simple_recommender.py` - 코인 추천 엔진
- `real_market_service.py` - 실제 마켓 분석 서비스

### 🗄️ **지원 서비스**
- `cache_service.py` - Redis 캐시 서비스
- `notification_service.py` - 알림 시스템

## 🔄 서비스 의존성

```
real_data_service.py
├── market_data_collector.py
├── websocket_data_manager.py
├── okx_websocket.py
├── upbit_websocket.py
├── coinone_websocket.py
└── gate_websocket.py

simple_recommender.py
├── real_market_service.py
└── cache_service.py

notification_service.py
└── cache_service.py
```

## 📋 설계 원칙

1. **단일 책임 원칙**: 각 서비스는 하나의 책임만 담당
2. **의존성 역전**: 인터페이스를 통한 느슨한 결합
3. **확장성**: 새로운 거래소 추가가 용이한 구조
4. **모니터링**: 모든 서비스에 로깅 및 상태 체크 포함

---
**최종 업데이트**: 2025-07-05
"""
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("📝 서비스 README.md 생성 완료")

if __name__ == "__main__":
    optimize_services()
    rename_main_service() 
    create_services_readme()
    print("\n🎉 아키텍처 최적화 완료!")
