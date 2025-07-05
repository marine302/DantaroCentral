# Dantaro Central 코드베이스 클린 코드/리팩터링/최적화 적용 내역 (2025-07-03)

## 1. 전체 적용 원칙
- 하드코딩/임시코드 제거 및 settings 기반화
- logger 일관화(정보성, 한글/영문 혼재 정리)
- try-except 내 에러처리/로깅 표준화
- 테스트/임시코드 분리(주석 처리 또는 별도 test 디렉터리로 이동)
- 공통/중복 로직은 베이스/유틸로 추출
- 데이터/스키마 일관성 유지

## 2. 주요 적용 내역

### 도메인 계층
- 분석기/추천기/계산기(`coin_analyzer.py`, `support_calculator.py`, `coin_recommender.py`, `advanced_recommender.py`, `simple_recommender.py` 등)
    - weight, interval 등 하드코딩 → settings 기반화
    - logger 메시지 정보성/일관성 강화
    - try-except 내 에러처리 표준화
    - 중복/임시코드 제거, 공통 로직은 베이스 클래스로 유지
    - 테스트/임시코드 분리

### 서비스 계층
- 데이터/실시간/WebSocket/Collector 등 주요 서비스
    - interval, batch_size, cache_ttl 등 하드코딩 → settings 기반화
    - logger 메시지 정보성/일관성 강화
    - try-except 내 에러처리 표준화
    - mock/test 함수 분리(주석 처리 또는 별도 test 파일로 이동)
    - WebSocket 클라이언트 생성 시 config None → 빈 문자열로 보완
    - get_latest_data(symbol) 등 인자 누락 오류 보완

### 엔드포인트 계층
- REST/WebSocket API(`market_data_light.py`, `websocket.py` 등)
    - active_exchanges, max_sends_per_second 등 하드코딩 → settings 기반화
    - logger 메시지 정보성/일관성 강화
    - try-except 내 에러처리 표준화
    - ArbitrageOpportunity, KimchiPremium 등 객체 속성명 오류 보완
    - API 응답/스키마 일관성 유지

## 3. 대표적 코드 패턴 예시
- `getattr(settings, "파라미터명", 기본값)` 패턴으로 모든 하드코딩 제거
- logger: `logger.info(f"[모듈명] 메시지: ...")` 등 정보성 강화
- try-except 내 에러: `logger.error(f"[모듈명] 에러: {e}")`
- 테스트/임시코드: 서비스 코드에서 분리 또는 주석 처리

## 4. 추가 개선/확장 가능 영역
- 테스트 커버리지 확대 및 test 디렉터리 구조화
- 문서화 자동화(Sphinx, OpenAPI 등)
- 배포 자동화(CI/CD)
- 성능 모니터링/로깅 고도화

---

이 리포트는 2025-07-03 기준 전체 코드베이스 클린 코드/리팩터링/최적화 적용 내역을 요약합니다.
