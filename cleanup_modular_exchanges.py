#!/usr/bin/env python3
"""
DantaroCentral 모듈화 기반 클린업 스크립트
Exchange Factory 패턴을 기준으로 레거시 파일들을 정리합니다.
"""
import os
import shutil
from pathlib import Path

def cleanup_legacy_exchanges():
    """레거시 거래소 파일들 정리"""
    exchanges_dir = Path(__file__).parent / "backend" / "app" / "exchanges"
    
    print("🧹 Exchange 모듈화 기반 클린업 시작...")
    
    # 이미 모듈화된 거래소들 (디렉토리로 존재)
    modularized_exchanges = [
        "okx",
        "coinone", 
        "gateio",
        "upbit",
        "binance",
        "bithumb",
        "bybit"
    ]
    
    # 제거할 레거시 파일들
    legacy_files = [
        "okx.py",          # okx/ 디렉토리로 모듈화됨
        "okx_legacy.py",   # 완전히 레거시
        "coinone.py",      # coinone/ 디렉토리로 모듈화됨
        "gate.py",         # gateio/ 디렉토리로 모듈화됨
        "upbit.py",        # upbit/ 디렉토리로 모듈화됨
        "upbit_old.py",    # 완전히 레거시
        "bithumb.py",      # bithumb/ 디렉토리로 모듈화됨
        "bybit.py",        # bybit/ 디렉토리로 모듈화됨
    ]
    
    # 백업 디렉토리 생성
    backup_dir = exchanges_dir / "legacy_backup"
    backup_dir.mkdir(exist_ok=True)
    
    removed_count = 0
    
    # 레거시 파일들을 백업으로 이동
    for legacy_file in legacy_files:
        file_path = exchanges_dir / legacy_file
        if file_path.exists():
            backup_path = backup_dir / legacy_file
            print(f"📦 백업 이동: {legacy_file} → legacy_backup/")
            shutil.move(str(file_path), str(backup_path))
            removed_count += 1
    
    print(f"\n✅ 레거시 Exchange 파일 정리 완료! {removed_count}개 파일 백업됨")
    
    # 모듈화된 거래소 확인
    print(f"\n🔧 모듈화된 거래소 확인:")
    for exchange in modularized_exchanges:
        exchange_dir = exchanges_dir / exchange
        if exchange_dir.exists() and exchange_dir.is_dir():
            client_file = exchange_dir / "client.py"
            init_file = exchange_dir / "__init__.py"
            if client_file.exists() and init_file.exists():
                print(f"  ✅ {exchange}/ (완전 모듈화)")
            else:
                print(f"  ⚠️  {exchange}/ (불완전 모듈화)")
        else:
            print(f"  ❌ {exchange}/ (누락)")

def update_exchanges_init():
    """__init__.py 파일을 모듈화된 거래소만 포함하도록 업데이트"""
    exchanges_dir = Path(__file__).parent / "backend" / "app" / "exchanges"
    init_file = exchanges_dir / "__init__.py"
    
    print("\n📝 __init__.py 업데이트 중...")
    
    # 모듈화된 모든 거래소 import
    new_content = '''"""
거래소 API 연동을 위한 공통 인터페이스 모듈
모든 거래소는 Factory 패턴을 통해 접근하세요.
"""

# 기본 타입과 클래스들을 base에서 import
from .base import (
    BaseExchange, Balance, Ticker, OrderBook, Order, Trade,
    OrderSide, OrderType, OrderStatus
)

# 모듈화된 거래소들
from .okx import OKXExchange
from .coinone import CoinoneExchange  
from .gateio import GateExchange
from .upbit import UpbitExchange
from .binance import BinanceClient
from .bithumb import BithumbClient  
from .bybit import BybitClient

# 팩토리 (권장 사용 방법)
from .factory import ExchangeFactory

__all__ = [
    # Base types
    'BaseExchange', 'Balance', 'Ticker', 'OrderBook', 'Order', 'Trade',
    'OrderSide', 'OrderType', 'OrderStatus',
    
    # 모듈화된 거래소들
    'OKXExchange', 'CoinoneExchange', 'GateExchange', 'UpbitExchange',
    'BinanceClient', 'BithumbClient', 'BybitClient',
    
    # Factory (권장)
    'ExchangeFactory'
]

# 사용 예시:
# from app.exchanges import ExchangeFactory
# exchange = ExchangeFactory.create_exchange('okx', api_key='...', secret_key='...', passphrase='...')
'''
    
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("✅ __init__.py 업데이트 완료")

def verify_factory_imports():
    """Factory에서 사용하는 import들이 유효한지 확인"""
    exchanges_dir = Path(__file__).parent / "backend" / "app" / "exchanges"
    factory_file = exchanges_dir / "factory.py"
    
    print("\n🔍 Factory 파일 import 검증 중...")
    
    try:
        with open(factory_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 각 모듈화된 거래소가 제대로 import되는지 확인
        required_imports = [
            "from .okx import OKXExchange",
            "from .coinone import CoinoneExchange", 
            "from .gateio import GateExchange",
            "from .upbit import UpbitExchange",
            "from .bithumb import BithumbClient",
            "from .bybit import BybitClient"
        ]
        
        missing_imports = []
        for imp in required_imports:
            if imp not in content:
                missing_imports.append(imp)
        
        if missing_imports:
            print("⚠️  Factory에서 누락된 import들:")
            for imp in missing_imports:
                print(f"    {imp}")
        else:
            print("✅ Factory import 검증 완료")
            
    except Exception as e:
        print(f"❌ Factory 검증 실패: {e}")

def create_modular_readme():
    """모듈화된 구조에 대한 README 생성"""
    exchanges_dir = Path(__file__).parent / "backend" / "app" / "exchanges"
    readme_file = exchanges_dir / "README.md"
    
    readme_content = '''# 🏦 Exchanges Module - 모듈화된 거래소 인터페이스

## 🎯 설계 원칙

### 📦 모듈화 (Modularization)
- **각 거래소별로 독립된 디렉토리 구조**
- **공통 인터페이스 (BaseExchange) 구현**
- **Factory 패턴을 통한 통합 관리**

### 🏗️ 클린 아키텍처
- **단일 책임 원칙**: 각 모듈은 하나의 거래소만 담당
- **개방-폐쇄 원칙**: 새로운 거래소 추가가 용이
- **의존성 역전**: 구체적 구현이 아닌 인터페이스에 의존

## 📂 디렉토리 구조

```
exchanges/
├── base.py              # 기본 인터페이스 정의
├── factory.py           # Factory 패턴 구현 
├── manager.py           # 거래소 관리자
├── __init__.py          # 모듈 초기화
├── 
├── okx/                 # OKX 거래소 (완전 모듈화)
│   ├── __init__.py
│   ├── client.py
│   ├── auth.py
│   ├── http_client.py
│   ├── market_data.py
│   ├── trading.py
│   ├── account.py
│   ├── data_mapper.py
│   └── validators.py
├── 
├── upbit/               # Upbit 거래소 (완전 모듈화)
│   ├── __init__.py
│   ├── client.py
│   ├── auth.py
│   ├── http_client.py
│   ├── market_data.py
│   ├── trading.py
│   ├── account.py
│   ├── data_mapper.py
│   └── validators.py
├── 
├── coinone/             # Coinone 거래소
│   ├── __init__.py
│   └── client.py
├── 
├── gateio/              # Gate.io 거래소
│   ├── __init__.py
│   └── client.py
├── 
├── binance/             # Binance 거래소
│   ├── __init__.py
│   └── client.py
├── 
├── bithumb/             # Bithumb 거래소
│   ├── __init__.py
│   └── client.py
├── 
├── bybit/               # Bybit 거래소
│   ├── __init__.py
│   └── client.py
└── 
└── legacy_backup/       # 레거시 파일 백업
```

## 🔧 사용 방법

### ✅ 권장: Factory 패턴 사용
```python
from app.exchanges import ExchangeFactory

# OKX 거래소 인스턴스 생성
okx = ExchangeFactory.create_exchange('okx', 
    api_key='your-key',
    secret_key='your-secret', 
    passphrase='your-passphrase'
)

# Upbit 거래소 인스턴스 생성
upbit = ExchangeFactory.create_exchange('upbit',
    api_key='your-key',
    secret_key='your-secret'
)

# 지원되는 거래소 목록 확인
supported = ExchangeFactory.get_supported_exchanges()
print(supported)  # ['okx', 'coinone', 'gateio', 'upbit', 'binance', 'bithumb', 'bybit']
```

### ❌ 비권장: 직접 import
```python
# 직접 import는 권장하지 않습니다
from app.exchanges.okx import OKXExchange  # ❌
```

## 🌟 지원되는 거래소

| 거래소 | 상태 | 모듈화 레벨 | 특징 |
|--------|------|-------------|------|
| **OKX** | ✅ 완료 | 완전 모듈화 | 8개 하위 모듈 |
| **Upbit** | ✅ 완료 | 완전 모듈화 | 8개 하위 모듈 |
| **Coinone** | ✅ 완료 | 기본 모듈화 | 1개 클라이언트 |
| **Gate.io** | ✅ 완료 | 기본 모듈화 | 1개 클라이언트 |
| **Binance** | ✅ 완료 | 기본 모듈화 | 1개 클라이언트 |
| **Bithumb** | ✅ 완료 | 기본 모듈화 | 1개 클라이언트 |
| **Bybit** | ✅ 완료 | 기본 모듈화 | 1개 클라이언트 |

## 🔄 확장 가이드

### 새로운 거래소 추가
1. **디렉토리 생성**: `exchanges/new_exchange/`
2. **BaseExchange 구현**: `client.py`에서 필수 메서드 구현
3. **Factory 등록**: `factory.py`에 추가
4. **테스트 작성**: 기본 기능 테스트

### 기존 거래소 확장
1. **하위 모듈 추가**: `auth.py`, `market_data.py` 등
2. **기능별 분리**: 단일 책임 원칙 준수
3. **인터페이스 유지**: BaseExchange 호환성 보장

## 📋 품질 기준

- ✅ **타입 힌트**: 모든 메서드에 타입 정보 포함
- ✅ **에러 처리**: 적절한 예외 처리 및 로깅
- ✅ **문서화**: 클래스 및 메서드 docstring
- ✅ **테스트**: 단위 테스트 커버리지
- ✅ **일관성**: 동일한 인터페이스 및 네이밍 규칙

---
**모듈화 완료일**: 2025-07-05  
**Factory 패턴**: ✅ 구현 완료  
**클린 아키텍처**: ✅ 적용 완료
'''
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
        
    print("📝 모듈화 README.md 생성 완료")

if __name__ == "__main__":
    cleanup_legacy_exchanges()
    update_exchanges_init()
    verify_factory_imports() 
    create_modular_readme()
    print("\n🎉 모듈화 기반 클린업 완료!")
