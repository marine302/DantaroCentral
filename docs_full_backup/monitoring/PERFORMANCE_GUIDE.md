# Dantaro Central 성능/운영 가이드

## 1. 캐싱/비동기화
- [x] Redis 캐시(5분 TTL, 설정 가능)
- [x] FastAPI async/await 기반 비동기 처리
- [x] DB/Redis 연결 풀링

## 2. 백그라운드 작업
- [x] 분석/추천/지지선 계산은 워커에서 비동기 처리
- [x] 실시간 데이터는 WebSocket/Queue로 분리

## 3. 모니터링/메트릭
- [x] 헬스체크: `/health`, `/api/v1/market-status`
- [x] 응답 시간: `X-Process-Time` 헤더
- [x] 시스템 상태/메트릭 API 제공
- [x] 로그: 구조화된 JSON 로그

## 4. 운영 환경 권장
- [x] PostgreSQL, Redis 클러스터/분산 운영
- [x] 여러 인스턴스 로드밸런싱
- [x] Prometheus, Grafana, ELK 등 연동

## 5. 배포 자동화
- [x] Dockerfile, .dockerignore 제공
- [x] GitHub Actions 기반 CI/CD 예시 제공

---
- 상세 운영/배포/모니터링은 README.md, SYSTEM_REFACTORING_REPORT.md 참고
