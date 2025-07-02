"""
거래소 팩토리
단일 책임: 거래소 인스턴스 생성 및 관리

통합 거래소 인터페이스를 통해 각 거래소별 구현체를 관리합니다.
"""

from typing import Dict, Type, Optional
from .base import BaseExchange

# Modularized exchanges
from .okx import OKXExchange
from .coinone import CoinoneExchange
from .gateio import GateExchange
from .upbit import UpbitExchange
from .bithumb import BithumbClient
from .bybit import BybitClient


class ExchangeFactory:
    """거래소 팩토리 클래스"""
    
    _exchanges: Dict[str, Type[BaseExchange]] = {
        # Core exchanges (Binance removed for optimization)
        'okx': OKXExchange,
        'coinone': CoinoneExchange,
        'gateio': GateExchange,
        'upbit': UpbitExchange,
        'bithumb': BithumbClient,
        'bybit': BybitClient,
    }
    
    @classmethod
    def create_exchange(cls, exchange_name: str, **credentials) -> BaseExchange:
        """
        거래소 인스턴스 생성
        
        Args:
            exchange_name: 거래소 이름 ('okx', 'coinone', 'gateio', 'upbit', 'bithumb', 'bybit')
            **credentials: 거래소별 API 인증 정보
        
        Returns:
            BaseExchange: 거래소 인스턴스
        
        Raises:
            ValueError: 지원하지 않는 거래소인 경우
        """
        exchange_name = exchange_name.lower()
        
        if exchange_name not in cls._exchanges:
            supported = ", ".join(cls._exchanges.keys())
            raise ValueError(f"지원하지 않는 거래소: {exchange_name}. 지원되는 거래소: {supported}")
        
        exchange_class = cls._exchanges[exchange_name]
        
        # 거래소별 필수 인증 정보 검증
        if exchange_name == 'okx':
            if not all(key in credentials for key in ['api_key', 'secret_key', 'passphrase']):
                raise ValueError("OKX는 api_key, secret_key, passphrase가 필요합니다")
            return exchange_class(
                api_key=credentials['api_key'],
                secret_key=credentials['secret_key'],
                passphrase=credentials['passphrase'],
                environment=credentials.get('environment', 'production')
            )
        
        elif exchange_name == 'gateio':
            if 'api_key' not in credentials or 'secret_key' not in credentials:
                raise ValueError("Gate.io는 api_key와 secret_key가 필요합니다")
            return exchange_class(
                api_key=credentials['api_key'],
                secret_key=credentials['secret_key']
            )
        
        elif exchange_name == 'coinone':
            if 'api_key' not in credentials or 'secret_key' not in credentials:
                raise ValueError("Coinone은 api_key와 secret_key가 필요합니다")
            return exchange_class(
                api_key=credentials['api_key'],
                secret_key=credentials['secret_key']
            )
        
        elif exchange_name == 'upbit':
            if 'api_key' not in credentials or 'secret_key' not in credentials:
                raise ValueError("Upbit는 api_key와 secret_key가 필요합니다")
            return exchange_class(
                api_key=credentials['api_key'],
                secret_key=credentials['secret_key']
            )
        
        elif exchange_name == 'bithumb':
            if 'api_key' not in credentials or 'secret_key' not in credentials:
                raise ValueError("Bithumb은 api_key와 secret_key가 필요합니다")
            return exchange_class(
                api_key=credentials['api_key'],
                secret_key=credentials['secret_key']
            )
        
        elif exchange_name == 'bybit':
            if 'api_key' not in credentials or 'secret_key' not in credentials:
                raise ValueError("Bybit는 api_key와 secret_key가 필요합니다")
            return exchange_class(
                api_key=credentials['api_key'],
                secret_key=credentials['secret_key']
            )
        
        # 이 부분에 도달할 수 없지만 타입 체커를 위한 코드
        raise ValueError(f"알 수 없는 거래소: {exchange_name}")
    
    @classmethod
    def get_supported_exchanges(cls) -> list[str]:
        """지원되는 거래소 목록 반환"""
        return list(cls._exchanges.keys())
    
    @classmethod
    def register_exchange(cls, name: str, exchange_class: Type[BaseExchange]) -> None:
        """새로운 거래소 등록"""
        cls._exchanges[name.lower()] = exchange_class
