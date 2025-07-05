# 🏢 Dantaro Central - AI Trading Central Server

**AI Trading Bot Platform - Central Analysis Server**

---

## 📑 문서/운영 안내 (2025-01-03 최신)

- **API 문서(OpenAPI/Swagger):**
  - 개발 서버 실행 후 [http://localhost:8001/docs](http://localhost:8001/docs) 접속
  - 모든 엔드포인트/스키마/예시 응답 자동 확인 가능
- **종합 문서:** [📚 **docs/** 디렉터리](./docs/) - 체계적으로 정리된 모든 문서
- **테스트 자동화:**
  - `pytest tests/`로 전체 단위/통합 테스트 실행
  - CI/CD 연동 예시 및 커버리지 리포트는 추후 확장 가능

[![CI](https://github.com/danielkwon/DantaroCentral/actions/workflows/ci.yml/badge.svg)](https://github.com/danielkwon/DantaroCentral/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/danielkwon/DantaroCentral/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN)](https://codecov.io/gh/danielkwon/DantaroCentral)

## 📚 문서 구조

### 개발자용 (Essential)
- [� 데이터베이스 스키마](./docs/development/database-schema.md) - DB 테이블 구조
- [⚙️ 환경설정](./docs/development/environment-config.md) - 환경변수 전체 목록
- [🔑 API 키 설정](./docs/development/api-key-setup.md) - 거래소 API 연동

### 배포/운영용
- [🚀 프로덕션 배포](./docs/deployment/production-setup.md) - 실제 배포 가이드
- [🏗️ 아키텍처](./docs/architecture/clean-architecture.md) - 시스템 전체 구조  
- [🔒 보안 체크리스트](./docs/security/security-checklist.md) - 보안 확인사항

### 📚 전체 문서
- [� **docs/** 디렉터리](./docs/) - 정리된 핵심 문서 (6개)
- [� **docs_archive/**](./docs_archive/) - 참고용 보관 문서 (2개)

### 주요 환경변수/설정 예시

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| **API 설정** |
| API_V1_STR | /api/v1 | API 버전 prefix |
| PROJECT_NAME | Dantaro Central | 프로젝트명 |
| ENVIRONMENT | development | 실행 환경 (development/production) |
| **데이터베이스** |
| DATABASE_URL | sqlite:///./dantaro_central.db | 데이터베이스 연결 |
| REDIS_URL | redis://localhost:6379/0 | Redis 연결 |
| **보안** |
| SECRET_KEY | (보안키 필요) | JWT 토큰 서명키 |
| USER_SERVER_API_KEY | (인증키 필요) | 사용자 서버 인증키 |
| **거래소 API** |
| BINANCE_API_KEY | (선택사항) | 바이낸스 API 키 |
| UPBIT_ACCESS_KEY | (선택사항) | 업비트 액세스 키 |
| OKX_API_KEY | (선택사항) | OKX API 키 |
| **시스템 설정** |
| RATE_LIMIT_REQUESTS | 100 | 분당 요청 제한 |
| RATE_LIMIT_SECONDS | 60 | 제한 시간(초) |
| MARKET_ANALYSIS_INTERVAL | 30 | 시장 분석 주기(초) |
| TOP_RECOMMENDATIONS_COUNT | 50 | 상위 추천 코인 수 |

> 📋 **설정 가이드**: [환경변수 상세 설정](./docs/guides/SETTINGS_REFERENCE.md)

---

## 📋 프로젝트 개요

Dantaro Central은 AI 트레이딩 봇 플랫폼의 **중앙 분석 서버**입니다. 

### 핵심 역할
- 🔍 **시장 분석**: 실시간 시장 데이터 수집 및 기술적 분석
- 🎯 **코인 추천**: AI 기반 고도화된 코인 추천 엔진 
- 📊 **저점값 계산**: 다양한 지지선 레벨 계산 (공격적, 온건, 보수적)
- 🌐 **API 제공**: 여러 사용자 서버(DantaroEnterprise)에 분석 데이터 제공

## 🏗️ 아키텍처

```
📡 Dantaro Central (본사 서버)
├── 🧠 AI 추천 엔진
├── 📈 시장 분석 모듈
├── 🔧 계산 엔진
└── 🌐 REST API
     ↓
🏢 User Servers (지점 서버들)
├── 🤖 실제 거래 실행
├── 👥 봇 관리
└── 💻 사용자 인터페이스
```

## 🚀 주요 API 엔드포인트

| 엔드포인트 | 기능 | 설명 |
|------------|------|------|
| `GET /api/v1/recommendations` | 코인 추천 | AI 기반 상위 코인 추천 (기술적 분석, 볼륨, 리스크) |
| `GET /api/v1/support-levels/{symbol}` | 저점값 계산 | 3가지 유형의 지지선 계산 |
| `GET /api/v1/market-status` | 시장 상태 | 전반적인 시장 지표 및 시스템 상태 |
| `POST /api/v1/bundle` | 번들 요청 | 다중 API 요청 일괄 처리 |

## 🛠️ 기술 스택

- **Backend**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Cache**: Redis
- **AI/ML**: 전략 패턴 기반 모듈러 추천 엔진
- **API**: RESTful API with OpenAPI/Swagger
- **Authentication**: API Key 기반 인증

## 🛠️ 기술 스택

## 📁 프로젝트 구조

```
DantaroCentral/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── api/v1/endpoints/  # API 엔드포인트
│   │   ├── core/              # 핵심 설정
│   │   ├── domain/            # 비즈니스 로직
│   │   │   ├── analyzers/     # 시장 분석기
│   │   │   ├── calculators/   # 계산 엔진
│   │   │   └── recommenders/  # 추천 엔진
│   │   ├── schemas/           # API 스키마
│   │   └── services/          # 서비스 계층
│   └── requirements.txt
├── tests/                     # 테스트 파일
├── docs/                      # 문서
└── venv/                      # Python 가상환경
```

## � 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd DantaroCentral

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r backend/requirements.txt
```

### 2. 서버 실행

```bash
# backend 디렉토리로 이동
cd backend

# PYTHONPATH 설정 및 서버 실행
export PYTHONPATH=/path/to/DantaroCentral/backend:$PYTHONPATH
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. API 테스트

```bash
# 테스트 실행
cd tests
python test_enhanced_api.py
```

## 🔧 설정

### 환경 변수 (backend/.env)

```env
# API 설정
API_V1_STR=/api/v1
PROJECT_NAME=Dantaro Central

# 데이터베이스
DATABASE_URL=postgresql://user:pass@localhost:5432/dantaro_central

# Redis 캐시
REDIS_URL=redis://localhost:6379/0

# 인증
USER_SERVER_API_KEY=your-api-key-here

# 거래소 API 키 (선택적)
COINBASE_API_KEY=your-key
BINANCE_API_KEY=your-key
UPBIT_ACCESS_KEY=your-key
```

## 🧠 AI 추천 엔진

### 핵심 컴포넌트

1. **Technical Analyzer**: 기술적 지표 분석 (RSI, MACD, Bollinger Bands)
2. **Volume Analyzer**: 거래량 패턴 분석
3. **Volatility Analyzer**: 변동성 및 트렌드 분석  
4. **Risk Analyzer**: 리스크 평가 및 점수화

### 추천 로직

```python
# 전략 패턴 기반 모듈러 설계
final_score = (
    technical_score * 0.4 +
    volume_score * 0.3 +
    volatility_score * 0.2 +
    risk_score * 0.1
)
```

## 📊 API 사용 예시

```python
import httpx

# 코인 추천 받기
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8001/api/v1/recommendations",
        headers={"Authorization": "Bearer your-api-key"},
        params={"top_n": 10}
    )
    recommendations = response.json()
```

## 🔒 보안

- API Key 기반 인증
- Rate Limiting
- 요청 데이터 검증
- 에러 핸들링 및 로깅

## 📈 성능 최적화

- Redis 캐싱 (5분 TTL)
- 비동기 처리 (async/await)
- 백그라운드 작업
- 데이터베이스 연결 풀링

## 📝 문서

- [시스템 분석](CENTRAL_SYSTEM_ANALYSIS.md) - 현재 상태 및 개선 계획
- [아키텍처 가이드](docs/copilot-guide-central.md) - 상세 설계 문서

## 🤝 기여

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch  
5. Create Pull Request

## 📄 라이센스

MIT License
- **작업**: 시장 데이터 수집, 추천 업데이트, 지지선 계산
- **캐싱**: 결과는 Redis에 캐시되어 빠른 응답 보장

## 🧪 테스트

```bash
# 단위 테스트 실행
pytest tests/

# 커버리지 포함 테스트
pytest --cov=app tests/

# 특정 테스트 실행
pytest tests/test_recommender.py -v
```

## 📊 모니터링

### 헬스 체크
- **기본**: `GET /health`
- **상세**: `GET /api/v1/market/market-status`

### 메트릭
- 응답 시간: `X-Process-Time` 헤더
- 시스템 상태: API 응답에 포함
- 로그: 구조화된 JSON 로그

## 🔐 보안

### API 인증
- **방식**: Bearer Token 인증
- **대상**: 모든 사용자 서버 요청
- **설정**: `USER_SERVER_API_KEY` 환경 변수

### Rate Limiting
- **기본**: 100 요청/분
- **적용**: 모든 API 엔드포인트
- **설정**: `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_SECONDS`

## 🚀 배포

### Docker 배포

```bash
# Docker 이미지 빌드
docker build -t dantaro-central .

# 컨테이너 실행
docker run -d --name dantaro-central \
  -p 8000:8000 \
  --env-file .env \
  dantaro-central
```

### 운영 환경 고려사항

1. **데이터베이스**: PostgreSQL 클러스터 구성
2. **캐시**: Redis Cluster 또는 Sentinel
3. **로드밸런싱**: 여러 인스턴스 운영
4. **모니터링**: Prometheus + Grafana
5. **로그 수집**: ELK Stack 또는 클라우드 로깅

## 📞 사용자 서버 연동

사용자 서버(DantaroEnterprise)는 다음과 같이 이 API를 사용합니다:

```python
# 사용자 서버에서의 API 호출 예시
import httpx

async def get_recommendations():
    headers = {"Authorization": "Bearer your-api-key"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://central-server:8000/api/v1/market/recommendations",
            headers=headers
        )
        return response.json()
```

## 📚 추가 문서

- [개발 가이드](docs/development/)
- [API 문서](docs/api/)
- [아키텍처 설계](docs/architecture/)
- [배포 가이드](docs/deployment/)

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**Dantaro Central** - AI 트레이딩 봇 플랫폼의 두뇌 역할을 하는 중앙 분석 서버 🧠⚡
