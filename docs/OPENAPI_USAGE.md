# OpenAPI & FastAPI 문서 활용 가이드

## OpenAPI 문서 접근
- 개발 환경: `/docs` (Swagger UI), `/redoc` (ReDoc)
- 운영 환경: 보안상 비공개, 필요시 관리자 인증 후 임시 오픈

## 주요 엔드포인트 예시

### 헬스체크
```
GET /health
```

### 코인 추천 (인증 필요)
```
GET /api/v1/recommendations
Authorization: Bearer <API_KEY>
```

### 예시 응답
```json
{
  "recommendations": [
    {"symbol": "BTC-USDT", "score": 0.98, "reason": "High volume, uptrend"},
    ...
  ]
}
```

## Swagger/OpenAPI 스크린샷
![Swagger UI 예시](./images/swagger_example.png)

## 참고
- FastAPI 공식 문서: https://fastapi.tiangolo.com/ko/
- OpenAPI 스펙: https://swagger.io/specification/
