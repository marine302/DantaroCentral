# 🏗️ DantaroCentral - 클린 아키텍처 가이드

## 📊 **최적화 완료 요약**

### ✅ **정리된 항목들**
- **88개 불필요한 테스트/임시 파일 제거**
- **5개 중복 서비스 모듈 정리**  
- **레거시 서비스들 archive 디렉토리로 이동**
- **빈 디렉토리 정리**

### 🏗️ **현재 클린 아키텍처**

```
DantaroCentral/
├── 📱 frontend/                    # 웹 인터페이스
│   ├── templates/                  # HTML 템플릿
│   └── static/                     # CSS, JS, Assets
│
├── 🔧 backend/                     # FastAPI 백엔드 
│   ├── app/                        # 메인 애플리케이션
│   │   ├── 🌐 api/v1/             # REST API 엔드포인트
│   │   │   ├── endpoints/          # API 라우터들
│   │   │   └── router.py           # API 라우터 통합
│   │   │
│   │   ├── ⚙️ core/               # 핵심 설정
│   │   │   ├── config.py           # 환경 설정
│   │   │   ├── startup.py          # 시작 로직
│   │   │   └── shutdown.py         # 종료 로직
│   │   │
│   │   ├── 🗄️ database/           # 데이터베이스 레이어
│   │   │   ├── connection.py       # DB 연결 관리
│   │   │   ├── manager.py          # DB 작업 관리
│   │   │   └── redis_cache.py      # Redis 캐시
│   │   │
│   │   ├── 🧠 domain/              # 비즈니스 로직
│   │   │   ├── analyzers/          # 시장 분석기
│   │   │   ├── calculators/        # 계산 엔진
│   │   │   └── recommenders/       # 추천 엔진
│   │   │
│   │   ├── 💼 services/            # **[정리완료]** 비즈니스 서비스
│   │   │   ├── real_data_service.py         # 🌟 메인 실시간 데이터
│   │   │   ├── market_data_collector.py     # 📊 통합 데이터 수집
│   │   │   ├── simple_recommender.py        # 🤖 추천 엔진
│   │   │   ├── websocket_data_manager.py    # 🔌 WebSocket 관리
│   │   │   ├── cache_service.py             # 💾 캐시 서비스
│   │   │   ├── notification_service.py      # 📢 알림 서비스
│   │   │   ├── real_market_service.py       # 📈 마켓 분석
│   │   │   └── **WebSocket 클라이언트들**
│   │   │       ├── okx_websocket.py         # OKX 거래소
│   │   │       ├── upbit_websocket.py       # Upbit 거래소
│   │   │       ├── coinone_websocket.py     # Coinone 거래소
│   │   │       └── gate_websocket.py        # Gate.io 거래소
│   │   │
│   │   ├── 🔍 monitoring/          # 모니터링 시스템
│   │   ├── 📝 schemas/             # API 스키마 정의
│   │   ├── 🏢 models/              # 데이터 모델
│   │   ├── 🔗 routes/              # 웹 라우터
│   │   └── 📊 exchanges/           # 거래소 통합
│   │
│   ├── 📦 archive/                 # **[NEW]** 레거시 파일들
│   │   ├── dantaro_orchestrator.py
│   │   ├── dantaro_multi_exchange_service.py
│   │   └── 보고서들...
│   │
│   ├── 🧪 tests/                   # 통합 테스트
│   ├── analysis_worker.py          # 백그라운드 분석 워커
│   ├── migrate.py                  # DB 마이그레이션
│   └── requirements.txt            # Python 의존성
│
├── 🧪 tests/                       # 프로젝트 통합 테스트
├── 📚 docs/                        # 문서화
├── 🚀 deployment/                  # 배포 설정
├── 🐳 Dockerfile                   # Docker 설정
├── 🔧 docker-compose.yml           # 개발 환경 구성
└── 📊 prometheus.yml               # 모니터링 설정
```

## 🎯 **핵심 아키텍처 원칙**

### 1. **관심사 분리 (Separation of Concerns)**
- **API Layer**: 요청/응답 처리만
- **Service Layer**: 비즈니스 로직만  
- **Database Layer**: 데이터 저장/조회만
- **Domain Layer**: 핵심 비즈니스 룰만

### 2. **의존성 역전 (Dependency Inversion)**
- 고수준 모듈이 저수준 모듈에 의존하지 않음
- 추상화(인터페이스)에 의존
- 테스트 가능한 구조

### 3. **단일 책임 원칙 (Single Responsibility)**
- 각 클래스/모듈은 하나의 책임만
- 변경 사유가 하나여야 함
- 높은 응집도, 낮은 결합도

### 4. **확장성 (Scalability)**
- 새로운 거래소 추가 용이
- 새로운 기능 추가 시 기존 코드 변경 최소화
- 마이크로서비스 전환 가능한 구조

## 🔧 **서비스 의존성 다이어그램**

```
📱 Frontend (React/HTML)
    ↓
🌐 API Layer (FastAPI)
    ↓
💼 Service Layer
    ├── RealDataService
    │   ├── MarketDataCollector
    │   └── WebSocketManager
    │       ├── OKXWebSocket
    │       ├── UpbitWebSocket  
    │       ├── CoinoneWebSocket
    │       └── GateWebSocket
    │
    ├── SimpleRecommender
    │   └── RealMarketService
    │
    └── CacheService
        └── NotificationService
    ↓
🗄️ Database Layer (PostgreSQL + Redis)
```

## 📋 **다음 최적화 단계**

### Phase 1: 코드 품질 (진행 중)
- [x] 불필요한 파일 정리 (88개 제거)
- [x] 중복 서비스 제거 (5개 정리)
- [x] 아키텍처 문서화
- [ ] 타입 힌트 완성도 100%
- [ ] 린터/포매터 적용 (black, isort, mypy)

### Phase 2: 성능 최적화
- [ ] Redis 캐싱 전략 최적화
- [ ] 데이터베이스 쿼리 최적화  
- [ ] 비동기 처리 개선
- [ ] 메모리 사용량 최적화

### Phase 3: 모니터링 강화
- [ ] 프로메테우스 메트릭 추가
- [ ] 로깅 시스템 개선
- [ ] 알림 시스템 확장
- [ ] 대시보드 고도화

### Phase 4: 테스트 커버리지
- [ ] 단위 테스트 100% 커버리지
- [ ] 통합 테스트 자동화
- [ ] E2E 테스트 추가
- [ ] 성능 테스트 자동화

---

**📅 최종 업데이트**: 2025-07-05  
**🎯 목표**: 엔터프라이즈급 안정성과 확장성  
**🔄 상태**: 아키텍처 정리 완료, 최적화 진행 중
