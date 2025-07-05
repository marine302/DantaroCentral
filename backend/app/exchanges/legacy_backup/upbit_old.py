"""
Upbit 거래소 API 구현 (호환성 래퍼)
기존 코드와의 호환성을 위한 래퍼 파일

새로운 모듈화된 구조:
- /upbit/auth.py - 인증 관리
- /upbit/http_client.py - HTTP 클라이언트
- /upbit/account.py - 계정 관리
- /upbit/market_data.py - 시장 데이터
- /upbit/trading.py - 거래 실행
- /upbit/data_mapper.py - 데이터 변환
- /upbit/validators.py - 데이터 검증
- /upbit/client.py - 메인 클라이언트

참고: https://docs.upbit.com/docs/
"""

# 기존 코드 호환성을 위한 import
from .upbit.client import UpbitExchange

# 모든 exports는 새로운 모듈화된 클라이언트에서 가져옴
__all__ = ['UpbitExchange']
