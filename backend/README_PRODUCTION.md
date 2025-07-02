# Dantaro Central - 다중 거래소 실시간 데이터 시스템

## 🌟 새로운 기능: 다중 거래소 지원!

**OKX + Upbit** WebSocket 동시 연결로 더 풍부한 실시간 데이터를 제공합니다!

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# API 키 설정 (OKX는 선택사항, Upbit는 공개 API)
python3 setup_production_keys.py

# 시스템 검증
python3 verify_realtime_system.py
```

### 2. 서비스 시작

#### 다중 거래소 서비스 (권장)
```bash
# 새로운 다중 거래소 서비스
./start_multi_exchange_service.sh

# 또는 직접 실행
python3 dantaro_multi_exchange_service.py
```

#### 기존 OKX 전용 서비스
```bash
# 기존 서비스 (OKX만)
./start_realtime_service.sh

# 또는 직접 실행
python3 dantaro_realtime_service.py
```

## 📊 지원 거래소

| 거래소 | WebSocket | API 키 필요 | 상태 |
|--------|-----------|-------------|------|
| **OKX** | ✅ | ✅ | 완전 지원 |
| **Upbit** | ✅ | ❌ (공개) | 완전 지원 |
| **Coinone** | 🔄 | ✅ | 개발중 |
| **Gate.io** | 📋 | ✅ | 계획 |

## 📋 주요 파일

### 다중 거래소 시스템 (New!)
- `dantaro_multi_exchange_service.py` - **새로운 다중 거래소 서비스**
- `start_multi_exchange_service.sh` - **다중 거래소 시작 스크립트**
- `app/services/upbit_websocket.py` - **Upbit WebSocket 클라이언트**
- `app/services/websocket_data_manager.py` - **향상된 데이터 관리자**

### 기존 시스템
- `dantaro_realtime_service.py` - 기존 OKX 전용 서비스
- `verify_realtime_system.py` - 시스템 검증 도구
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
