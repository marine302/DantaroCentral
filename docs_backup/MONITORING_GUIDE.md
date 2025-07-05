# 프로덕션 모니터링/알림 가이드

## 1. Prometheus + Grafana
- FastAPI/uvicorn에 [prometheus_fastapi_instrumentator](https://github.com/trallard/prometheus-fastapi-instrumentator) 적용
- `/metrics` 엔드포인트 노출 후 Prometheus에서 scrape
- Grafana에서 대시보드 시각화

## 2. ELK(Elasticsearch, Logstash, Kibana)
- 로그를 파일/JSON으로 저장 → Filebeat/Logstash로 수집
- Elasticsearch에 저장, Kibana로 대시보드/검색

## 3. Alertmanager/Slack 연동
- Prometheus Alertmanager로 임계치 알림
- Slack Webhook 연동

## 샘플 docker-compose
```yaml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports: [9090:9090]
  grafana:
    image: grafana/grafana
    ports: [3000:3000]
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
    ports: [9200:9200]
  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports: [5601:5601]
```

## Grafana 대시보드 샘플
- `docs/GRAFANA_DASHBOARD_SAMPLE.json` 파일을 Grafana에서 import하면 FastAPI 요청 지연/카운트 등 주요 지표를 바로 시각화할 수 있습니다.

1. Grafana → Dashboards → Import → json 파일 업로드
2. 데이터소스: Prometheus 선택

## 참고
- [FastAPI 모니터링 공식 가이드](https://fastapi.tiangolo.com/advanced/metrics/)
- [Prometheus + Grafana](https://grafana.com/docs/grafana/latest/getting-started/getting-started-prometheus/)
