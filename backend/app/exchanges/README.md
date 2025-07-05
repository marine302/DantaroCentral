# 🏦 Exchanges Module - 모듈화된 거래소 인터페이스

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
