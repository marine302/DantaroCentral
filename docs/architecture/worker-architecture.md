# 분석 워커 아키텍처 설계

## 🏗 워커 시스템 구조

### 워커 컴포넌트
```
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Worker                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Job Manager │ │ Scheduler   │ │    Analysis Engines     │ │
│  │             │ │             │ │  ┌─────────────────────┐ │ │
│  │             │ │             │ │  │ Recommendation     │ │ │
│  │             │ │             │ │  │ Engine             │ │ │
│  │             │ │             │ │  └─────────────────────┘ │ │
│  │             │ │             │ │  ┌─────────────────────┐ │ │
│  │             │ │             │ │  │ Support Level      │ │ │
│  │             │ │             │ │  │ Calculator         │ │ │
│  │             │ │             │ │  └─────────────────────┘ │ │
│  │             │ │             │ │  ┌─────────────────────┐ │ │
│  │             │ │             │ │  │ Market Status      │ │ │
│  │             │ │             │ │  │ Analyzer           │ │ │
│  │             │ │             │ │  └─────────────────────┘ │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ DB Writer   │ │ Cache       │ │    Market Data          │ │
│  │             │ │ Manager     │ │    Service              │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📋 워커 스케줄링 전략

### 1. 작업 우선순위
```python
JOB_PRIORITY = {
    'market_status': 1,          # 가장 높음 (시장 전반)
    'recommendations': 2,        # 높음 (핵심 기능)
    'support_levels': 3,         # 보통 (상세 분석)
    'cleanup': 4                 # 낮음 (유지보수)
}
```

### 2. 실행 주기
```python
SCHEDULE = {
    'market_status': '*/2 * * * *',        # 2분마다
    'recommendations': '*/5 * * * *',      # 5분마다
    'support_levels': '*/15 * * * *',      # 15분마다
    'cleanup': '0 */6 * * *'               # 6시간마다
}
```

### 3. 리소스 관리
```python
RESOURCE_LIMITS = {
    'max_concurrent_jobs': 3,
    'memory_limit_mb': 2048,
    'timeout_seconds': 300,
    'retry_attempts': 3
}
```

## 🔧 워커 구현 계획

### Phase 2-A: 기본 워커 프레임워크
```python
# worker/base_worker.py
class BaseAnalysisWorker:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_manager = DatabaseManager()
        self.cache_manager = CacheManager()
        
    async def start(self):
        """워커 시작"""
        
    async def stop(self):
        """워커 중지"""
        
    async def register_job(self, job_func, schedule, priority):
        """작업 등록"""
```

### Phase 2-B: 분석 엔진 분리
```python
# worker/engines/recommendation_engine.py
class RecommendationEngine:
    async def analyze(self) -> List[CoinRecommendation]:
        """코인 추천 분석 실행"""
        
# worker/engines/support_level_engine.py  
class SupportLevelEngine:
    async def calculate(self, symbols: List[str]) -> Dict[str, SupportLevel]:
        """지원/저항선 계산"""
        
# worker/engines/market_status_engine.py
class MarketStatusEngine:
    async def analyze(self) -> MarketStatus:
        """시장 상태 분석"""
```

### Phase 2-C: 데이터 저장 관리자
```python
# worker/data_manager.py
class DataManager:
    async def save_recommendations(self, recommendations: List[CoinRecommendation]):
        """추천 데이터 저장 (DB + Cache)"""
        
    async def save_support_levels(self, levels: Dict[str, SupportLevel]):
        """지원선 데이터 저장"""
        
    async def save_market_status(self, status: MarketStatus):
        """시장 상태 저장"""
```

## 🎛 워커 설정

### 환경 변수
```env
# 워커 설정
WORKER_ENABLED=true
WORKER_LOG_LEVEL=INFO
WORKER_MAX_WORKERS=3

# 스케줄 설정
RECOMMENDATIONS_INTERVAL=300    # 5분
SUPPORT_LEVELS_INTERVAL=900     # 15분
MARKET_STATUS_INTERVAL=120      # 2분

# 데이터베이스
DATABASE_URL=postgresql://user:pass@localhost:5432/dantaro
REDIS_URL=redis://localhost:6379/0

# 외부 API
UPBIT_API_TIMEOUT=30
MAX_SYMBOLS_PER_BATCH=50
```

### 설정 파일
```python
# worker/config.py
class WorkerConfig:
    # 스케줄링
    recommendations_interval: int = 300
    support_levels_interval: int = 900
    market_status_interval: int = 120
    
    # 리소스
    max_concurrent_jobs: int = 3
    job_timeout: int = 300
    retry_attempts: int = 3
    
    # 데이터
    max_symbols: int = 50
    cache_ttl: Dict[str, int] = {
        'recommendations': 300,
        'support_levels': 1800,
        'market_status': 300
    }
```

## 🚀 배포 및 실행

### 1. 독립 실행 스크립트
```python
# worker/main.py
async def main():
    worker = AnalysisWorker()
    
    try:
        await worker.start()
        logger.info("Analysis worker started successfully")
        
        # 무한 실행
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        await worker.stop()
```

### 2. systemd 서비스
```ini
# /etc/systemd/system/dantaro-worker.service
[Unit]
Description=Dantaro Central Analysis Worker
After=network.target

[Service]
Type=simple
User=dantaro
WorkingDirectory=/opt/dantaro-central
ExecStart=/opt/dantaro-central/venv/bin/python worker/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 📊 모니터링 및 로깅

### 1. 작업 상태 추적
```python
# 작업 실행 로그
JOB_LOG = {
    'job_id': 'uuid',
    'job_type': 'recommendations',
    'status': 'completed',
    'duration': 45.2,
    'symbols_processed': 50,
    'error': None,
    'timestamp': '2025-07-01T10:30:00Z'
}
```

### 2. 헬스 체크 엔드포인트
```python
# API에 워커 상태 확인 엔드포인트 추가
@router.get("/worker/status")
async def get_worker_status():
    return {
        'worker_active': check_worker_heartbeat(),
        'last_jobs': get_recent_jobs(),
        'uptime': get_worker_uptime()
    }
```

---
**다음 단계**: 데이터베이스 설정 및 모델 구현
