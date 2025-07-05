# Sphinx 문서화 가이드

## 1. 설치 및 초기화
```
pip install sphinx sphinx-autodoc-typehints
sphinx-quickstart docs/sphinx
```

## 2. conf.py 설정
- `extensions`에 `sphinx.ext.autodoc`, `sphinx_autodoc_typehints` 추가
- `autodoc_typehints = "description"`

## 3. 자동 API 문서 생성
```
sphinx-apidoc -o docs/sphinx/source backend/app
```

## 4. 빌드
```
make html
```

## 5. 결과 확인
- `docs/sphinx/build/html/index.html`에서 문서 확인

## 참고
- [Sphinx 공식](https://www.sphinx-doc.org/)
- [FastAPI + Sphinx 예시](https://fastapi.tiangolo.com/advanced/extending-openapi/)
