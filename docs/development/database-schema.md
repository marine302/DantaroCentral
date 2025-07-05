# 데이터베이스 스키마 설계

## 📊 데이터베이스 구조 개요

### PostgreSQL 테이블 설계

#### 1. `coin_recommendations` 테이블
```sql
CREATE TABLE coin_recommendations (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    total_score DECIMAL(5,4) NOT NULL,
    technical_score DECIMAL(5,4) NOT NULL,
    volume_score DECIMAL(5,4) NOT NULL,
    volatility_score DECIMAL(5,4) NOT NULL,
    risk_score DECIMAL(5,4) NOT NULL,
    recommendation_strength VARCHAR(20) NOT NULL,
    current_price DECIMAL(20,8),
    price_change_24h DECIMAL(10,8),
    volume_24h DECIMAL(20,2),
    market_cap DECIMAL(20,2),
    analysis_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_coin_recommendations_symbol ON coin_recommendations(symbol);
CREATE INDEX idx_coin_recommendations_created_at ON coin_recommendations(created_at);
CREATE INDEX idx_coin_recommendations_total_score ON coin_recommendations(total_score DESC);
```

#### 2. `support_levels` 테이블
```sql
CREATE TABLE support_levels (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    aggressive_support DECIMAL(20,8),
    moderate_support DECIMAL(20,8),
    conservative_support DECIMAL(20,8),
    aggressive_resistance DECIMAL(20,8),
    moderate_resistance DECIMAL(20,8),
    conservative_resistance DECIMAL(20,8),
    calculation_method VARCHAR(50),
    data_points_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_support_levels_symbol ON support_levels(symbol);
CREATE INDEX idx_support_levels_created_at ON support_levels(created_at);
```

#### 3. `market_status` 테이블
```sql
CREATE TABLE market_status (
    id SERIAL PRIMARY KEY,
    market_sentiment VARCHAR(20) NOT NULL, -- 'bullish', 'bearish', 'neutral'
    total_volume_24h DECIMAL(20,2),
    average_volatility DECIMAL(10,8),
    total_symbols_analyzed INTEGER,
    positive_movements INTEGER,
    negative_movements INTEGER,
    system_health JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_market_status_created_at ON market_status(created_at);
```

#### 4. `analysis_jobs` 테이블 (워커 관리용)
```sql
CREATE TABLE analysis_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL, -- 'recommendations', 'support_levels', 'market_status'
    status VARCHAR(20) NOT NULL, -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    symbols_processed INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX idx_analysis_jobs_created_at ON analysis_jobs(created_at);
```

### Redis 캐시 구조

#### 캐시 키 네이밍 컨벤션
```
# 추천 데이터
recommendations:latest           # 최신 추천 리스트
recommendations:count:{n}        # 상위 N개 추천

# 지원/저항 레벨
support_levels:{symbol}          # 특정 코인 지원선

# 시장 상태  
market_status:latest             # 최신 시장 상태

# 워커 상태
worker:last_run:{job_type}       # 마지막 실행 시간
worker:status:{job_type}         # 워커 실행 상태
```

#### 캐시 TTL 설정
```python
CACHE_TTL = {
    'recommendations': 300,      # 5분
    'support_levels': 1800,      # 30분
    'market_status': 300,        # 5분
    'worker_status': 60          # 1분
}
```

## 🔄 데이터 플로우

### 1. 분석 워커 → 데이터베이스
```
워커 실행 → 시장 데이터 수집 → 분석 → PostgreSQL 저장 → Redis 캐시 업데이트
```

### 2. API 서버 → 사용자
```
API 요청 → Redis 캐시 확인 → 캐시 있으면 반환 → 없으면 PostgreSQL 조회 → 응답
```

## 📋 구현 순서

### Phase 1-A: 데이터베이스 설정
- [ ] PostgreSQL 설치 및 설정
- [ ] 테이블 생성 스크립트 작성
- [ ] Redis 설정

### Phase 1-B: 데이터 모델 구현
- [ ] SQLAlchemy 모델 정의
- [ ] 데이터베이스 연결 관리자
- [ ] 마이그레이션 스크립트

---
**다음 문서**: [워커 아키텍처 설계](worker-architecture.md)
