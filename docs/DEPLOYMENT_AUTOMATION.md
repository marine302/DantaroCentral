# 배포 자동화 가이드

## 1. Docker 빌드/배포
```
docker build -t dantaro-central .
docker run -d -p 8000:8000 --env-file .env dantaro-central
```

## 2. GitHub Actions + DockerHub/Registry
- `.github/workflows/ci.yml`에 빌드/푸시 단계 추가
- 예시:
```
    - name: Build Docker image
      run: docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/dantaro-central:${{ github.sha }} .
    - name: Push Docker image
      run: docker push ${{ secrets.DOCKERHUB_USERNAME }}/dantaro-central:${{ github.sha }}
```

## 3. 환경 변수/시크릿 관리
- `.env` 파일 또는 GitHub Secrets 사용

## 참고
- [FastAPI Docker 공식](https://fastapi.tiangolo.com/deployment/docker/)
