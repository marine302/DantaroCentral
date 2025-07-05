"""
WebSocket 엔드포인트 메인 모듈

이 파일은 모듈화된 WebSocket 엔드포인트들을 통합하여 제공합니다.
실제 구현은 websocket/ 폴더 내의 세부 모듈들에 있습니다.

- realtime.py: 실시간 WebSocket 연결 관리
- dashboard.py: 대시보드 관련 API
- broadcast.py: 데이터 방송/스트리밍 API
"""

# 모듈화된 websocket 패키지에서 통합 라우터 import
from .websocket import router

# 기존 코드와의 호환성을 위해 re-export
__all__ = ["router"]
