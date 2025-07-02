"""
Upbit 거래소 모듈
한국 최대 암호화폐 거래소 Upbit API 통합 모듈

주요 기능:
- 🔐 인증 관리 (JWT 토큰)
- 💰 계정 관리 (잔고, 입출금)
- 📊 시장 데이터 (시세, 호가, 캔들)
- 🛒 거래 실행 (매수/매도, 주문 관리)
- ✅ 데이터 검증 (주문 파라미터 검증)

사용 예시:
    async with UpbitExchange(api_key, secret_key) as exchange:
        balance = await exchange.get_balance('KRW')
        ticker = await exchange.get_ticker('KRW-BTC')
        order = await exchange.create_market_order('KRW-BTC', OrderSide.BUY, Decimal('50000'))
"""

from .client import UpbitExchange
from .auth import UpbitAuth
from .http_client import UpbitHttpClient
from .account import UpbitAccount
from .market_data import UpbitMarketData
from .trading import UpbitTrading
from .data_mapper import UpbitDataMapper
from .validators import UpbitValidators

__all__ = [
    'UpbitExchange',
    'UpbitAuth',
    'UpbitHttpClient',
    'UpbitAccount',
    'UpbitMarketData',
    'UpbitTrading',
    'UpbitDataMapper',
    'UpbitValidators',
]

# 버전 정보
__version__ = '1.0.0'
__author__ = 'Dantaro Enterprise'
__description__ = 'Upbit 거래소 API 통합 모듈'
