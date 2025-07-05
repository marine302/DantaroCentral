# Dantaro Central 테스트 가이드

## 1. 단위/통합 테스트 실행

```bash
# (가상환경 활성화 후)
PYTHONPATH=./backend pytest tests --maxfail=3 --disable-warnings -v
```

## 2. 주요 테스트 파일
- `tests/test_market_data_service.py`: 서비스 계층 단위 테스트
- `tests/test_support_calculator.py`: 도메인 계산기 테스트
- `tests/test_api_endpoints.py`: API 엔드포인트 테스트

## 3. CI 자동화
- `.github/workflows/ci.yml` 참고 (GitHub Actions 기반)
- PR/Push 시 자동 테스트 및 DB/Redis 연동

## 4. 커버리지 측정

```bash
pytest --cov=app tests/
```

## 5. 테스트 작성 권장 패턴
- Given-When-Then 구조, mock 데이터 활용, 비동기 함수는 pytest-asyncio 사용
