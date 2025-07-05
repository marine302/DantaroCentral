# 🔧 Services Layer - Dantaro Central

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
