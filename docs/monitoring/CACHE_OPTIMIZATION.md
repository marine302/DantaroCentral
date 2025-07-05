# 캐시 최적화 및 성능 가이드

## 1. Redis 캐시 구조
- 마켓 데이터, 추천 결과 등 빈번 조회 데이터 Redis에 저장
- TTL(만료) 설정으로 실시간성/성능 균형

## 2. FastAPI 비동기 캐시
- aioredis 등 비동기 클라이언트 사용
- 서비스 계층에서 await 패턴 적용

## 3. 캐시 무효화/갱신
- force_refresh 파라미터로 강제 갱신 지원
- 데이터 변경 시 관련 캐시 키 삭제

## 4. 모니터링
- Redis INFO, hit/miss 통계, latency 측정

## 참고
- [FastAPI + Redis 예시](https://fastapi.tiangolo.com/advanced/async-sql-databases/)
- [Redis 공식](https://redis.io/)
