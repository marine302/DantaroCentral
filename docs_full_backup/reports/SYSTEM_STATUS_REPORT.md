# Dantaro Central - 전체 시스템 현황 분석 및 기록

## 🎯 핵심 목적
**사용자 서버(DantaroEnterprise)가 본사 중앙 서버 API를 호출하여 코인 추천 정보와 저점 정보를 실시간으로 받아가는 시스템**

---

## 📊 현재 구현된 API 엔드포인트 (2025-07-03 기준)

### 🔑 API 인증
- **방식**: Bearer Token (HTTP Authorization Header)
- **키**: `settings.user_server_api_key` (개발용: "development-user-server-key")
- **위치**: 모든 API 엔드포인트에 `dependencies=[Depends(verify_api_key)]` 적용

### 📍 Core API Endpoints (`/api/v1/`)

#### 1. **코인 추천 정보** ✅ 구현완료
```
GET /api/v1/recommendations
```
**기능**: 사용자 서버가 호출하여 AI 분석 기반 코인 추천 정보를 받아감
**파라미터**:
- `top_n`: 추천 개수 (1-100, 기본값: 50)
- `use_cache`: 캐시 우선 사용 여부 (기본값: true)

**응답 데이터**:
```json
{
  "success": true,
  "recommendations": [
    {
      "symbol": "BTC",
      "total_score": 0.85,
      "technical_score": 0.9,
      "volume_score": 0.8,
      "volatility_score": 0.7,
      "risk_score": 0.6,
      "recommendation_strength": "STRONG_BUY",
      "current_price": 65000.0,
      "price_change_24h": 2.5,
      "volume_24h": 1234567890,
      "market_cap": 1280000000000,
      "analysis_details": {},
      "updated_at": "2025-07-03T04:00:00Z"
    }
  ],
  "total_analyzed": 50,
  "cache_timestamp": "2025-07-03T04:15:00Z",
  "generated_at": 1720000000.0,
  "data_source": "cache"
}
```

#### 2. **저점/지지선 정보** ✅ 구현완료  
```
GET /api/v1/support-levels/{symbol}
```
**기능**: 특정 코인의 지지선/저항선 정보 (전체 간격 계산용)
**파라미터**:
- `symbol`: 코인 심볼 (예: BTC, ETH)
- `use_cache`: 캐시 우선 사용 여부

**응답 데이터**:
```json
{
  "success": true,
  "symbol": "BTC",
  "support_levels": {
    "symbol": "BTC",
    "aggressive_support": 62000.0,
    "moderate_support": 60000.0,
    "conservative_support": 58000.0,
    "aggressive_resistance": 70000.0,
    "moderate_resistance": 72000.0,
    "conservative_resistance": 75000.0,
    "calculation_method": "fibonacci_bollinger",
    "data_points_count": 1000,
    "updated_at": "2025-07-03T04:00:00Z"
  },
  "cache_timestamp": "2025-07-03T04:15:00Z",
  "data_source": "cache"
}
```

#### 3. **시장 상태 정보** ✅ 구현완료
```
GET /api/v1/market-status
```
**기능**: 전체 시장 트렌드 및 상태 정보
**응답 데이터**: 시장 트렌드, 센티먼트, 전체 점수 등

#### 4. **번들 요청** ✅ 구현완료
```
POST /api/v1/bundle
```
**기능**: 여러 데이터를 한 번에 요청 (네트워크 최적화)
**요청 본문**:
```json
{
  "include_recommendations": true,
  "recommendations_count": 20,
  "include_support_levels": true,
  "symbols": ["BTC", "ETH", "ADA"],
  "include_market_status": true
}
```

#### 5. **헬스 체크** ✅ 구현완료
```
GET /api/v1/health
GET /health
```
**기능**: 시스템 상태 확인 (DB, 캐시, 워커 상태)

---

## 🔄 데이터 흐름 아키텍처

### 📊 데이터 소스 계층
1. **1차**: Redis 캐시 (실시간 캐시된 분석 결과)
2. **2차**: PostgreSQL 데이터베이스 (영구 저장된 분석 결과)
3. **백그라운드**: 분석 워커들이 지속적으로 데이터 분석 및 업데이트

### 🔄 사용자 서버 호출 패턴
```
DantaroEnterprise → API 호출 → DantaroCentral
                              ↓
                         캐시 확인 → DB 확인 → 분석 결과 반환
```

---

## 🚀 현재 구현된 추가 기능들

### 🌐 WebSocket 실시간 대시보드 ✅ 구현완료
- **엔드포인트**: `/ws/realtime`
- **기능**: 브라우저용 실시간 대시보드
- **메시지 타입**: `price_update`, `arbitrage_opportunities`, `kimchi_premium`

### 🔧 실시간 모니터링 시스템 ✅ 구현완료
- **파일**: `dashboard_monitor.py`
- **기능**: 자동 진단, 상태 모니터링, 문제점 발견 및 해결책 제안

### 🏗️ 다중 거래소 연동 ✅ 구현완료
- **거래소**: OKX, Upbit, Coinone, Gate.io
- **기능**: 실시간 가격 수집, 차익거래 분석, 김치 프리미엄 계산

### 📊 데이터베이스 및 캐시 시스템 ✅ 구현완료
- **DB**: PostgreSQL (추천 정보, 지지선 정보 영구 저장)
- **캐시**: Redis (실시간 캐시, 성능 최적화)
- **관리자**: `db_manager`, `redis_manager`

---

## 🎯 **핵심 기능 구현 상태**

### ✅ **완전히 구현된 기능**
1. **코인 추천 정보 API** - 사용자 서버가 호출 가능
2. **저점/지지선 정보 API** - 전체 간격 계산용 데이터 제공
3. **API 인증 시스템** - Bearer Token 기반
4. **캐시 우선 로직** - 성능 최적화
5. **에러 핸들링** - 적절한 HTTP 상태 코드 및 메시지

### ⚠️ **확인 필요한 사항**
1. **분석 워커 동작 여부** - 실제 추천 데이터 생성되는지
2. **저점 계산 로직** - 정확한 지지선/저항선 계산되는지
3. **사용자 서버 호출 예제** - DantaroEnterprise에서 실제 호출 테스트

---

## 📝 사용자 서버 호출 예제

### Python 예제 (DantaroEnterprise용)
```python
import requests

# API 설정
BASE_URL = "http://dantaro-central-server:8000/api/v1"
API_KEY = "your-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# 1. 코인 추천 정보 요청
def get_recommendations(top_n=20):
    response = requests.get(
        f"{BASE_URL}/recommendations",
        params={"top_n": top_n, "use_cache": True},
        headers=HEADERS
    )
    return response.json()

# 2. 저점 정보 요청
def get_support_levels(symbol):
    response = requests.get(
        f"{BASE_URL}/support-levels/{symbol}",
        params={"use_cache": True},
        headers=HEADERS
    )
    return response.json()

# 3. 번들 요청 (최적화된 호출)
def get_bundle_data(symbols):
    payload = {
        "include_recommendations": True,
        "recommendations_count": 20,
        "include_support_levels": True,
        "symbols": symbols,
        "include_market_status": True
    }
    response = requests.post(
        f"{BASE_URL}/bundle",
        json=payload,
        headers=HEADERS
    )
    return response.json()
```

---

## 🔍 **결론 및 다음 단계**

### ✅ **현재 상태**
**핵심 기능(코인 추천 + 저점 정보 API)이 완전히 구현되어 있음**
- 사용자 서버가 필요한 모든 데이터를 API로 호출 가능
- 인증, 캐싱, 에러 핸들링 모두 구현됨

### 🔄 **확인해야 할 사항**
1. **분석 워커 실행 상태** - 실제 추천 데이터가 생성되고 있는지
2. **데이터베이스 상태** - 추천 정보와 지지선 정보가 저장되어 있는지
3. **사용자 서버 연동 테스트** - DantaroEnterprise에서 실제 API 호출 테스트

### 🎯 **우선순위**
1. **분석 워커 상태 확인 및 실행**
2. **실제 데이터 생성 확인**
3. **사용자 서버 연동 테스트**

---

**📅 마지막 업데이트**: 2025-07-03
**🏷️ 상태**: 핵심 API 구현 완료, 데이터 생성 확인 필요
