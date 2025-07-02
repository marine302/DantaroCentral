"""
OKX 거래소 API 구현 (호환성 래퍼)
기존 코드와의 호환성을 위한 래퍼 파일

새로운 모듈화된 구조:
- backend/app/exchanges/okx/ (모듈화된 구현)
- backend/app/exchanges/okx.py (호환성 래퍼)
"""

# 새로운 모듈화된 OKX 구현을 import
from .okx.client import OKXExchange

# 기존 코드에서 사용하던 모든 클래스와 함수들을 그대로 export
__all__ = ['OKXExchange']

# 기존 코드와 100% 호환되도록 동일한 인터페이스 제공
# from .okx import OKXExchange 형태로 import 가능
