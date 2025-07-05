# 🤖 단타로 AI Copilot 개발 가이드 - 본사/사용자 서버 분리 버전

## 📋 프로젝트 구조 개요

단타로 AI는 **2개의 독립된 시스템**으로 구성됩니다:

1. **본사 서버 (Central Server)**: 시장 분석 및 정보 제공 API
2. **사용자 서버 (User Server)**: 실제 거래 실행 및 봇 관리

**통신 방식**: 사용자 서버가 본사 서버의 REST API를 Pull 방식으로 호출

---

# 🏢 Part 1: 본사 서버 (Central Server)

## 📁 본사 서버 디렉토리 구조

```bash
# Copilot: Create directory structure for Dantaro Central Server
# This server provides market analysis data via REST API
# No trading execution, only data analysis and recommendations

mkdir -p dantaro-central/{
  src/{
    api/v1/{endpoints,middleware},
    core/{config,logging},
    domain/{
      analyzers,     # 시장 분석 로직
      calculators,   # 저점값 계산
      recommenders   # 코인 추천 엔진
    },
    infrastructure/{
      database,      # 분석 데이터 저장
      exchanges,     # 시세 데이터 수집
      cache         # Redis 캐싱
    },
    services,       # 비즈니스 로직
    models,         # 데이터 모델
    tasks          # 백그라운드 작업
  },
  tests,
  docs
}
```

## 🎯 본사 서버 핵심 기능

### 1.1 코인 추천 엔진

```python
# Copilot: Create dantaro-central/src/domain/recommenders/coin_recommender.py
# Purpose: Analyze and rank coins for recommendation
# Features:
# - Technical analysis scoring
# - Volume analysis
# - Volatility assessment
# - Risk scoring
# Output: Top 50 coins with scores and metadata
# Clean code: Strategy pattern for different analysis methods

from abc import ABC, abstractmethod
from typing import List, Dict
from decimal import Decimal

class CoinAnalyzer(ABC):
    """Abstract base for coin analysis strategies"""
    
    @abstractmethod
    async def analyze(self, symbol: str) -> Dict:
        """Analyze a single coin"""
        pass

class CoinRecommender:
    """Main recommender that combines multiple analyzers"""
    
    def __init__(self, analyzers: List[CoinAnalyzer]):
        self.analyzers = analyzers
    
    async def get_recommendations(self) -> List[Dict]:
        """Get top 50 coin recommendations"""
        # Implementation
```

### 1.2 저점값 계산 서비스

```python
# Copilot: Create dantaro-central/src/domain/calculators/support_calculator.py
# Purpose: Calculate support levels for each coin
# Methods:
# - calculate_aggressive_support(symbol, days=7) -> price
# - calculate_moderate_support(symbol, days=30) -> price
# - calculate_conservative_support(symbol, days=90) -> price
# Data source: Historical price data from database
# Clean code: Pure functions, clear naming

class SupportLevelCalculator:
    """Calculate various support levels for trading"""
    
    @staticmethod
    def calculate_support_levels(price_history: List[Dict]) -> Dict:
        """Calculate three types of support levels"""
        # Implementation
```

### 1.3 API 엔드포인트 (본사)

```python
# Copilot: Create dantaro-central/src/api/v1/endpoints/market_data.py
# FastAPI endpoints for market data
# Endpoints:
# - GET /api/v1/recommendations - Get coin recommendations
# - GET /api/v1/support-levels/{symbol} - Get support levels
# - GET /api/v1/market-status - Get market status
# - POST /api/v1/bundle - Bundle multiple requests
# Features: Rate limiting, caching, API key authentication

from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter

router = APIRouter()

@router.get("/recommendations", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def get_recommendations():
    """Get current coin recommendations"""
    # Implementation
```

### 1.4 백그라운드 태스크

```python
# Copilot: Create dantaro-central/src/tasks/market_analyzer.py
# Background task for continuous market analysis
# Schedule: Every 5 minutes
# Tasks:
# - Fetch latest price data from exchanges
# - Update support levels
# - Recalculate coin scores
# - Clean old data
# Use: Celery or APScheduler
```

---

# 👤 Part 2: 사용자 서버 (User Server)

## 📁 사용자 서버 디렉토리 구조

```bash
# Copilot: Create directory structure for Dantaro User Server
# This server manages bots and executes trades
# Pulls data from Central Server API

mkdir -p dantaro-user/{
  src/{
    api/v1/{endpoints,dependencies},
    core/{config,security},
    domain/{
      entities,      # Bot, Position, Order
      services,      # State machine, Calculation engine
      repositories   # Data persistence interfaces
    },
    application/{
      use_cases,     # Business operations
      dto           # Data transfer objects
    },
    infrastructure/{
      database,      # Bot data storage
      exchanges,     # Trading execution
      central_api,   # Central server client
      cache         # Local cache
    }
  },
  tests,
  docs
}
```

## 🔧 사용자 서버 핵심 기능

### 2.1 Central API 클라이언트

```python
# Copilot: Create dantaro-user/src/infrastructure/central_api/client.py
# HTTP client for communicating with Central Server
# Features:
# - Async requests with httpx
# - Automatic retry with exponential backoff
# - Response caching
# - Fallback to cached data on failure
# Methods:
# - get_recommendations() -> List[Dict]
# - get_support_levels(symbol) -> Dict
# - get_market_status() -> Dict

import httpx
from typing import Dict, List, Optional
from functools import wraps
import asyncio

class CentralAPIClient:
    """Client for Central Server API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def get_recommendations(self) -> List[Dict]:
        """Pull coin recommendations from central server"""
        # Implementation with retry and cache fallback
```

### 2.2 봇 매니저

```python
# Copilot: Create dantaro-user/src/domain/services/bot_manager.py
# Bot lifecycle management
# Responsibilities:
# - Create bot with parameters from central server
# - Manage bot state transitions
# - Execute trading cycles
# Clean code: Separate bot logic from trading logic

class BotManager:
    """Manages bot lifecycle and operations"""
    
    def __init__(
        self,
        central_client: CentralAPIClient,
        exchange_client: ExchangeClient,
        calculation_engine: CalculationEngine
    ):
        self.central_client = central_client
        self.exchange_client = exchange_client
        self.calculation_engine = calculation_engine
    
    async def start_cycle(self, bot_id: str):
        """Start new trading cycle"""
        # 1. Pull data from central server
        # 2. Calculate parameters locally
        # 3. Execute trades
```

### 2.3 로컬 계산 엔진

```python
# Copilot: Create dantaro-user/src/domain/services/calculation_engine.py
# Local calculation engine for trading parameters
# Uses data from central server to calculate:
# - Order amounts based on budget
# - Intervals based on support levels
# - Take profit prices
# Clean code: Pure functions, no external dependencies

class CalculationEngine:
    """Local calculations for trading parameters"""
    
    @staticmethod
    def calculate_order_amounts(total_budget: Decimal, stages: int) -> List[Decimal]:
        """Calculate order amounts for each stage"""
        # Implementation
        
    @staticmethod
    def calculate_intervals(
        current_price: Decimal,
        support_level: Decimal,
        stages: int
    ) -> List[float]:
        """Calculate intervals with time-based seed"""
        # Implementation
```

### 2.4 거래 실행 서비스

```python
# Copilot: Create dantaro-user/src/infrastructure/exchanges/exchange_service.py
# Exchange interaction service
# Responsibilities:
# - Place orders
# - Check order status
# - Get balances
# - Handle exchange-specific logic
# Clean code: Adapter pattern for multiple exchanges

from abc import ABC, abstractmethod

class ExchangeAdapter(ABC):
    """Abstract adapter for exchange operations"""
    
    @abstractmethod
    async def place_market_order(self, symbol: str, side: str, amount: Decimal):
        pass

class UpbitAdapter(ExchangeAdapter):
    """Upbit exchange implementation"""
    # Implementation
```

---

# 🔄 Part 3: 통합 플로우

## 3.1 봇 생성 플로우

```python
# Copilot: Create integration example showing bot creation flow
# Flow:
# 1. User requests bot creation
# 2. User server pulls recommendations from central
# 3. User selects coin (or auto-select)
# 4. User server pulls support levels
# 5. Local calculation of parameters
# 6. Bot created and first order placed

# In user server:
async def create_bot_flow(user_id: str, budget: Decimal):
    # Step 1: Get recommendations
    recommendations = await central_client.get_recommendations()
    
    # Step 2: Select coin
    selected_coin = select_coin_from_recommendations(recommendations)
    
    # Step 3: Get support levels
    support_levels = await central_client.get_support_levels(selected_coin)
    
    # Step 4: Calculate parameters locally
    params = calculation_engine.calculate_parameters(budget, support_levels)
    
    # Step 5: Create bot
    bot = Bot(user_id, selected_coin, params)
    
    # Step 6: Start trading
    await bot_manager.start_cycle(bot.id)
```

## 3.2 환경 설정

### 본사 서버 설정

```python
# Copilot: Create dantaro-central/.env.example
# Environment variables for central server
# Database for analysis data
# Redis for caching
# Exchange APIs for data collection

DATABASE_URL=postgresql://user:pass@localhost/dantaro_central
REDIS_URL=redis://localhost:6379/0
EXCHANGE_API_KEYS=...
```

### 사용자 서버 설정

```python
# Copilot: Create dantaro-user/.env.example
# Environment variables for user server
# Central API configuration
# User database
# Exchange APIs for trading

CENTRAL_API_URL=https://api.dantaro-central.com
CENTRAL_API_KEY=your-api-key
DATABASE_URL=postgresql://user:pass@localhost/dantaro_user
REDIS_URL=redis://localhost:6379/1
UPBIT_ACCESS_KEY=...
UPBIT_SECRET_KEY=...
```

---

# 🧪 Part 4: 테스트 전략

## 4.1 본사 서버 테스트

```python
# Copilot: Create tests for central server
# Test recommendation engine with mock data
# Test support level calculations
# Test API rate limiting
# Test caching behavior
```

## 4.2 사용자 서버 테스트

```python
# Copilot: Create tests for user server
# Test central API client with mock responses
# Test bot state transitions
# Test calculation engine with various inputs
# Test fallback behavior when central API fails
```

## 4.3 통합 테스트

```python
# Copilot: Create integration tests
# Test complete flow from central to user server
# Test failover scenarios
# Test performance under load
```

---

# 📝 개발 순서 (수정됨)

## Week 1: 본사 서버

### Day 1-2: 본사 서버 Core
- [ ] 프로젝트 구조 설정
- [ ] 코인 분석 엔진
- [ ] 저점값 계산기
- [ ] 추천 시스템

### Day 3-4: 본사 서버 API
- [ ] FastAPI 엔드포인트
- [ ] 인증 및 Rate limiting
- [ ] 캐싱 레이어
- [ ] 백그라운드 태스크

### Day 5: 본사 서버 완성
- [ ] 통합 테스트
- [ ] 문서화
- [ ] 배포 준비

## Week 2: 사용자 서버

### Day 1-2: 사용자 서버 Core
- [ ] Central API 클라이언트
- [ ] 계산 엔진
- [ ] 봇 상태 관리
- [ ] 거래소 연동

### Day 3-4: 사용자 서버 API
- [ ] 봇 관리 엔드포인트
- [ ] 프론트엔드 연동
- [ ] 실시간 업데이트

### Day 5: 통합 및 테스트
- [ ] 전체 플로우 테스트
- [ ] 성능 최적화
- [ ] 최종 배포

---

# 🎯 핵심 포인트

1. **완전한 분리**: 본사와 사용자 서버는 API로만 통신
2. **Pull 방식**: 사용자 서버가 필요시 정보 요청
3. **로컬 계산**: 모든 거래 관련 계산은 사용자 서버에서
4. **장애 격리**: 한쪽 장애가 다른 쪽에 영향 없음
5. **확장성**: 각각 독립적으로 스케일링 가능

**이제 진정한 분산 아키텍처로 단타로 AI를 구현할 수 있습니다!** 🚀