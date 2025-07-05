# 통합 테스트 자동화 가이드

## 목적
- API, 서비스, 실시간 데이터 등 전체 시스템의 통합 시나리오 검증

## 실행 방법
```
pytest tests/test_integration_realtime.py
```

## 주요 시나리오
- 헬스체크 → 인증 실패/성공 → 추천 응답
- 실시간 마켓 데이터 서비스 정상 동작

## 참고
- [pytest 공식](https://docs.pytest.org/)
- [FastAPI 테스트](https://fastapi.tiangolo.com/ko/tutorial/testing/)
