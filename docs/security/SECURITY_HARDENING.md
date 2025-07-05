# 보안 강화 및 침투 테스트 가이드

## 1. API Key/인증
- 모든 API 요청에 API Key 필수 (FastAPI HTTPBearer)
- 키는 환경변수/시크릿으로 관리, 코드에 하드코딩 금지

## 2. Rate Limiting
- [slowapi](https://github.com/laurentS/slowapi) 등으로 IP/Key별 요청 제한
- 예시: 1분 100회 제한

## 3. 데이터 검증/정제
- Pydantic 스키마로 입력값 검증
- SQL Injection, XSS 방지

## 4. HTTPS 적용
- 운영 환경은 반드시 HTTPS (프록시/로드밸런서 포함)

## 5. 침투 테스트
- [OWASP ZAP](https://www.zaproxy.org/) 등 자동화 도구로 취약점 점검
- 주요 체크: 인증 우회, Rate Limit 우회, 민감 데이터 노출, 에러 메시지 노출 등

## 6. 로그/모니터링
- 모든 인증 실패/비정상 요청 로그 기록 및 모니터링

## 참고
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI 보안 가이드](https://fastapi.tiangolo.com/ko/advanced/security/)
