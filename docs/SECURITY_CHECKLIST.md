# Dantaro Central 보안 점검 체크리스트

## 1. 인증/인가
- [x] 모든 API에 API Key 인증 적용 (USER_SERVER_API_KEY)
- [x] 인증 실패 시 401/403 반환
- [x] 민감 정보(키, 비밀번호 등) .env로 분리

## 2. 데이터 검증/방어
- [x] 모든 입력값 Pydantic/스키마 검증
- [x] SQL Injection, XSS 등 방어
- [x] 응답 데이터 타입/스키마 일관성

## 3. Rate Limiting/DoS 방어
- [x] 기본 100req/분 제한 (설정 가능)
- [x] Redis 등으로 분산 rate limit 가능

## 4. 로깅/모니터링
- [x] 모든 주요 에러/이벤트 logger로 기록
- [x] 구조화된 로그(JSON 등) 지원
- [x] 헬스체크/메트릭 API 제공

## 5. 운영/배포
- [x] Docker 기반 배포/격리
- [x] DB/Redis 별도 운영 권장
- [x] .env, secrets 안전 관리

## 6. 기타
- [x] 테스트 자동화 및 CI 통과
- [x] 최신 패키지/의존성 유지

---
- 상세 보안/운영 가이드는 README.md, SYSTEM_REFACTORING_REPORT.md 참고
