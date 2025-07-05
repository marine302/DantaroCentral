# Dantaro Central - FastAPI + PostgreSQL + Redis
FROM python:3.9-slim

# 환경 변수
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 작업 디렉토리 생성
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# requirements 복사 및 설치
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Prometheus metrics 지원을 위한 패키지 추가
RUN pip install prometheus-fastapi-instrumentator

# jwt 모듈(Python용 PyJWT) 설치
RUN pip install PyJWT

# 소스 복사
COPY backend/app ./app

# 엔트리포인트
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
