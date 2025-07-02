# Dantaro Central - 다중 거래소 WebSocket 시스템

## 🌟 개요

Dantaro Central이 한 단계 더 발전했습니다! 이제 **OKX와 Upbit** 두 거래소의 실시간 데이터를 동시에 수집할 수 있습니다.

### 🚀 새로운 기능

- **다중 거래소 지원**: OKX + Upbit WebSocket 동시 연결
- **통합 데이터 관리**: 단일 인터페이스로 모든 거래소 데이터 처리
- **성능 최적화**: 거래소별 독립적인 연결 및 데이터 처리
- **실시간 모니터링**: 거래소별 상태 및 통계 실시간 추적

## 📊 지원 거래소

| 거래소 | WebSocket | API 키 필요 | 지원 심볼 예시 |
|--------|-----------|-------------|----------------|
| **OKX** | ✅ | ✅ | BTC-USDT, ETH-USDT, SOL-USDT |
| **Upbit** | ✅ | ❌ (공개) | KRW-BTC, KRW-ETH |
| **Coinone** | 🔄 (개발중) | ✅ | BTC, ETH |
| **Gate.io** | 🔄 (계획) | ✅ | BTC_USDT, ETH_USDT |

## 🔧 설치 및 설정

### 1. 의존성 설치
```bash
pip install websockets aiohttp
```

### 2. API 키 설정 (선택사항)
```bash
# OKX API 키 설정 (더 많은 데이터 수집 가능)
python3 setup_production_keys.py
```

### 3. 서비스 시작
```bash
# 권장: 시작 스크립트 사용
./start_multi_exchange_service.sh

# 또는 직접 실행
python3 dantaro_multi_exchange_service.py
```

## 📈 실시간 데이터 수집

### 자동 심볼 매핑

시스템은 거래소에 맞는 심볼을 자동으로 매핑합니다:

```python
# OKX (국제 표준)
['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'ADA-USDT', 'DOT-USDT', 'MATIC-USDT']

# Upbit (한국 원화 기준)  
['KRW-BTC', 'KRW-ETH']
```

### 실시간 로그 예시

```
📊 [OKX] BTC-USDT: $96,234.56 (Vol: 1,234.56)
📊 [Upbit] KRW-BTC: ₩145,399,000 (Vol: 937.58)
📊 [OKX] ETH-USDT: $3,456.78 (Vol: 2,345.67)
📊 [Upbit] KRW-ETH: ₩3,326,000 (Vol: 24,680.37)
```

## 🏗️ 아키텍처

### 핵심 컴포넌트

```
dantaro_multi_exchange_service.py     # 메인 서비스
├── MultiExchangeWebSocketManager     # 다중 거래소 WebSocket 관리
│   ├── OKXWebSocketClient           # OKX WebSocket 클라이언트
│   └── UpbitWebSocketClient         # Upbit WebSocket 클라이언트
├── MarketDataCollector              # REST API 데이터 수집
└── OptimizationConfig               # 성능 최적화 설정
```

### 데이터 플로우

```
OKX WebSocket ──┐
                ├─→ MultiExchangeWebSocketManager ─→ 데이터 처리 ─→ Redis 캐시
Upbit WebSocket ─┘                                      ↓
                                                    실시간 로그
REST API ────────────────────────────────────────→ 배치 저장
```

## 📋 핵심 클래스

### 1. DantaroMultiExchangeService

메인 서비스 클래스로 모든 거래소를 통합 관리합니다.

```python
service = DantaroMultiExchangeService()
await service.run()
```

**주요 기능:**
- 거래소별 설정 관리
- WebSocket 연결 제어
- 서비스 상태 모니터링
- 리소스 정리

### 2. MultiExchangeWebSocketManager

다중 거래소 WebSocket을 통합 관리하는 클래스입니다.

```python
manager = MultiExchangeWebSocketManager()
await manager.initialize_websockets(exchange_configs)
await manager.connect_all_websockets()
```

**주요 기능:**
- 거래소별 WebSocket 클라이언트 관리
- 통합 데이터 처리 및 버퍼링
- 실시간 통계 및 모니터링
- 자동 재연결 처리

### 3. UpbitWebSocketClient

Upbit 전용 WebSocket 클라이언트입니다.

```python
client = UpbitWebSocketClient(data_handler=my_handler)
await client.connect()
await client.subscribe_ticker(['KRW-BTC', 'KRW-ETH'])
```

**특징:**
- 바이너리 메시지 처리 (JSON)
- 한국 원화 기준 심볼 지원
- 공개 API 사용 (인증 불필요)

## 🔍 모니터링 및 통계

### 실시간 통계 로그

```
💡 서비스 상태: 연결 2개, 메시지 1,234개, 오류 0개
  📊 OKX: 789개 메시지
  📊 UPBIT: 445개 메시지
```

### 데이터 메트릭

- **총 메시지 수**: 모든 거래소에서 수신한 총 메시지
- **활성 연결**: 현재 활성화된 WebSocket 연결 수
- **거래소별 메시지**: 각 거래소에서 수신한 메시지 수
- **버퍼 크기**: 각 거래소별 심볼 버퍼 수

## 🚀 성능 최적화

### 메모리 최적화

```python
# 버퍼 크기 제한
max_buffer_size = 1000

# 오래된 데이터 자동 정리
cleanup_interval = 300  # 5분

# 최근 업데이트만 유지
recent_updates = buffer.price_updates[-100:]
```

### 네트워크 최적화

```python
# 중요한 심볼만 로깅
if symbol in ['BTC-USDT', 'KRW-BTC']:
    logger.info(f"📊 {symbol}: {price}")

# 배치 처리
batch_interval = 10  # 10초마다
```

## 🧪 테스트

### 빠른 연결 테스트

```bash
python3 tests/test_quick_multi_exchange.py
```

### 전체 시스템 테스트

```bash
python3 tests/test_multi_exchange_websocket.py
```

### 서비스 통합 테스트

```bash
python3 tests/test_multi_exchange_service.py
```

## 🔧 설정 옵션

### 환경 변수

```bash
# 성능 모드 설정
export DANTARO_PERFORMANCE_MODE=high     # high, balanced, eco

# 최대 심볼 수 제한
export DANTARO_MAX_SYMBOLS=20

# 로그 레벨
export DANTARO_LOG_LEVEL=INFO
```

### 최적화 설정

```python
# optimization_config.py에서 조정 가능
core_symbols = ['BTC-USDT', 'ETH-USDT', 'KRW-BTC', 'KRW-ETH']
max_buffer_size = 1000
monitoring_interval = 60  # 1분
```

## 🛠️ 문제 해결

### 자주 발생하는 문제

**1. WebSocket 연결 실패**
```bash
# 네트워크 연결 확인
ping ws.okx.com
ping api.upbit.com

# 방화벽 설정 확인
```

**2. 데이터 수신 없음**
```bash
# API 키 확인
python3 check_env_status.py

# 심볼 형식 확인 (OKX: BTC-USDT, Upbit: KRW-BTC)
```

**3. 메모리 사용량 증가**
```python
# 버퍼 크기 조정
max_buffer_size = 500  # 기본값: 1000

# 정리 주기 단축
cleanup_interval = 180  # 기본값: 300초
```

## 📅 로드맵

### Phase 9 (현재)
- ✅ OKX + Upbit WebSocket 통합
- ✅ 다중 거래소 데이터 관리
- ✅ 실시간 모니터링 시스템

### Phase 10 (다음 단계)
- 🔄 Coinone WebSocket 추가
- 🔄 Gate.io WebSocket 추가
- 🔄 고급 데이터 분석 기능
- 🔄 알림 시스템 통합

### Phase 11 (미래)
- 📋 데이터 시각화 대시보드
- 📋 API 엔드포인트 확장
- 📋 클라우드 배포 지원

## 🎯 핵심 장점

1. **확장성**: 새로운 거래소 쉽게 추가 가능
2. **안정성**: 거래소별 독립적인 연결 관리
3. **성능**: 최적화된 메모리 및 네트워크 사용
4. **모니터링**: 실시간 상태 추적 및 통계
5. **유지보수**: 모듈화된 구조로 쉬운 관리

---

**Dantaro Central** - 다중 거래소 실시간 데이터의 새로운 표준 🚀
