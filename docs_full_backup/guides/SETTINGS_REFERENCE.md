# Dantaro Central 주요 환경변수/설정 레퍼런스

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| API_V1_STR | /api/v1 | API 버전 prefix |
| PROJECT_NAME | Dantaro Central | 프로젝트명 |
| DATABASE_URL | postgresql://... | PostgreSQL 연결 |
| REDIS_URL | redis://... | Redis 연결 |
| USER_SERVER_API_KEY | (직접 입력) | 사용자 서버 인증키 |
| RATE_LIMIT_REQUESTS | 100 | 분당 요청 제한 |
| RATE_LIMIT_SECONDS | 60 | 제한 시간(초) |
| market_data_update_interval | 60 | 시장 데이터 갱신 주기(초) |
| websocket_batch_interval | 10 | WebSocket 배치 주기(초) |
| websocket_batch_size | 100 | WebSocket 배치 크기 |
| real_market_cache_ttl | 60 | 실시간 마켓 캐시 TTL(초) |
| support_aggressive_days | 7 | 공격적 지지선 lookback |
| support_moderate_days | 30 | 온건 지지선 lookback |
| support_conservative_days | 90 | 보수 지지선 lookback |
| technical_analyzer_weight | 0.4 | 기술분석 가중치 |
| volume_analyzer_weight | 0.2 | 볼륨 가중치 |
| volatility_analyzer_weight | 0.2 | 변동성 가중치 |
| risk_analyzer_weight | 0.2 | 리스크 가중치 |
| ... | ... | ... |

- 기타 상세 설정은 README.md, SYSTEM_REFACTORING_REPORT.md 참고
