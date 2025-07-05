"""
거래소 팩토리
단일 책임: 거래소 인스턴스 생성 및 관리

통합 거래소 인터페이스를 통해 각 거래소별 구현체를 관리합니다.
"""

from typing import Dict, Type, Optional, Any
from .base import BaseExchange

# Modularized exchanges
from .okx import OKXExchange
from .okx.public_client import OKXPublicClient
from .coinone import CoinoneExchange
from .coinone.public_client import CoinonePublicClient
from .gateio import GateExchange
from .gateio.public_client import GateIOPublicClient
from .upbit import UpbitExchange
from .bithumb import BithumbClient
from .bithumb.public_client import BithumbPublicClient
from .bybit import BybitClient
from .bybit.public_client import BybitPublicClient


class ExchangeFactory:
    """거래소 팩토리 클래스"""
    
    _exchanges: Dict[str, Type[Any]] = {
        # Core exchanges (Binance removed for optimization)
        'okx': OKXPublicClient,  # 퍼블릭 API 사용
        'coinone': CoinonePublicClient,  # 퍼블릭 API 사용
        'gateio': GateIOPublicClient,  # 퍼블릭 API 사용
        'upbit': UpbitExchange,
        'bithumb': BithumbPublicClient,  # 퍼블릭 API 사용
        'bybit': BybitPublicClient,  # 퍼블릭 API 사용
    }
    
    @classmethod
    def create_exchange(cls, exchange_name: str, **credentials) -> Any:
        """
        거래소 인스턴스 생성
        
        Args:
            exchange_name: 거래소 이름 ('okx', 'coinone', 'gateio', 'upbit', 'bithumb', 'bybit')
            **credentials: 거래소별 API 인증 정보
        
        Returns:
            거래소 인스턴스
        
        Raises:
            ValueError: 지원하지 않는 거래소인 경우
        """
        exchange_name = exchange_name.lower()
        
        if exchange_name not in cls._exchanges:
            raise ValueError(f"지원하지 않는 거래소: {exchange_name}")
        
        exchange_class = cls._exchanges[exchange_name]
        
        # 퍼블릭 클라이언트는 credentials 없이 생성
        if exchange_name in ['okx', 'coinone', 'gateio', 'bithumb', 'bybit']:
            return exchange_class()
        else:
            # 기존 거래소는 credentials 필요
            return exchange_class(**credentials)
    
    @classmethod
    def get_supported_exchanges(cls) -> list:
        """
        지원하는 거래소 목록 반환
        
        Returns:
            list: 지원하는 거래소 이름 목록
        """
        return list(cls._exchanges.keys())
    
    @classmethod
    def create_public_client(cls, exchange_name: str) -> Any:
        """
        퍼블릭 클라이언트 생성 (인증 불필요)
        
        Args:
            exchange_name: 거래소 이름
            
        Returns:
            퍼블릭 클라이언트 인스턴스
        """
        return cls.create_exchange(exchange_name)


# 편의 함수들
def create_okx_client() -> OKXPublicClient:
    """OKX 퍼블릭 클라이언트 생성"""
    return OKXPublicClient()


def create_coinone_client() -> CoinonePublicClient:
    """Coinone 퍼블릭 클라이언트 생성"""
    return CoinonePublicClient()


def create_gateio_client() -> GateIOPublicClient:
    """Gate.io 퍼블릭 클라이언트 생성"""
    return GateIOPublicClient()


def create_bithumb_client() -> BithumbPublicClient:
    """Bithumb 퍼블릭 클라이언트 생성"""
    return BithumbPublicClient()


def create_bybit_client() -> BybitPublicClient:
    """Bybit 퍼블릭 클라이언트 생성"""
    return BybitPublicClient()


def create_upbit_client(**credentials) -> UpbitExchange:
    """Upbit 클라이언트 생성"""
    return UpbitExchange(**credentials)
