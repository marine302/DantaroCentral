# Dantaro Central 배포 가이드

## 1. Docker 이미지 빌드

```bash
docker build -t dantaro-central .
```

## 2. 환경 변수 파일(.env) 준비

```env
DATABASE_URL=postgresql://user:pass@db:5432/dantaro_central
REDIS_URL=redis://redis:6379/0
USER_SERVER_API_KEY=your-api-key
# 기타 설정은 README.md 환경변수 표 참고
```

## 3. 컨테이너 실행

```bash
docker run -d --name dantaro-central \
  -p 8000:8000 \
  --env-file .env \
  dantaro-central
```

## 4. 운영 환경 권장 사항
- PostgreSQL, Redis는 별도 컨테이너/클러스터로 운영
- .env 파일은 안전하게 관리
- 로그/모니터링: Prometheus, Grafana, ELK 등 연동 권장
- CI/CD: GitHub Actions 등으로 자동화

## 5. 기타
- 상세 설정/운영/보안은 README.md 및 SYSTEM_REFACTORING_REPORT.md 참고
