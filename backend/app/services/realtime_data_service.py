#!/usr/bin/env python3
"""
실시간 데이터 수집 서비스
WebSocket 기반 다중 거래소 데이터 수집 전담
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from app.services.websocket_data_manager import MultiExchangeWebSocketManager
from app.core.config import settings


@dataclass
class DataServiceConfig:
    """데이터 서비스 설정"""
    analysis_interval: int = 10  # 분석 간격 (초)
    symbol_refresh_interval: int = 300  # 심볼 갱신 간격 (초)
    reconnect_attempts: int = 5  # 재연결 시도 횟수
    enable_logging: bool = True


class RealTimeDataService:
    """실시간 데이터 수집 서비스"""
    
    def __init__(self, config: DataServiceConfig = None):
        self.logger = logging.getLogger(f"{__name__}.RealTimeDataService")
        
        # 설정
        self.config = config or DataServiceConfig()
        
        # WebSocket 매니저
        self.websocket_manager = MultiExchangeWebSocketManager()
        
        # 상태 관리
        self.running = False
        self.exchange_configs = {}
        self.active_symbols = {}
        
        # 콜백 함수들
        self.data_callbacks: Dict[str, Callable] = {}
        
        # 통계
        self.stats = {
            'start_time': None,
            'total_messages': 0,
            'messages_per_exchange': {},
            'active_connections': 0,
            'last_data_time': None
        }
    
    def set_data_callback(self, callback_type: str, callback: Callable):
        """데이터 처리 콜백 설정"""
        self.data_callbacks[callback_type] = callback
        self.logger.info(f"데이터 콜백 설정: {callback_type}")
    
    def configure_exchanges(self, exchange_configs: Dict[str, Dict]):
        """거래소 설정"""
        self.exchange_configs = exchange_configs
        self.logger.info(f"거래소 설정 완료: {list(exchange_configs.keys())}")
    
    def set_symbols(self, symbols_by_exchange: Dict[str, List[str]]):
        """심볼 설정"""
        self.active_symbols = symbols_by_exchange
        self.logger.info(f"심볼 설정 완료: {sum(len(symbols) for symbols in symbols_by_exchange.values())}개")
    
    async def initialize(self):
        """서비스 초기화"""
        self.logger.info("실시간 데이터 서비스 초기화 시작...")
        
        try:
            # WebSocket 매니저 초기화
            await self.websocket_manager.initialize_websockets(self.exchange_configs)
            
            # 데이터 처리 콜백 설정
            self._setup_websocket_callbacks()
            
            self.logger.info("✅ 실시간 데이터 서비스 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 서비스 초기화 실패: {e}")
            raise
    
    def _setup_websocket_callbacks(self):
        """WebSocket 콜백 설정"""
        def on_ticker_data(exchange: str, symbol: str, data: dict):
            """티커 데이터 처리"""
            try:
                self.stats['total_messages'] += 1
                self.stats['last_data_time'] = datetime.now()
                
                if exchange not in self.stats['messages_per_exchange']:
                    self.stats['messages_per_exchange'][exchange] = 0
                self.stats['messages_per_exchange'][exchange] += 1
                
                # 등록된 콜백 호출
                if 'ticker' in self.data_callbacks:
                    self.data_callbacks['ticker'](exchange, symbol, data)
                    
            except Exception as e:
                self.logger.error(f"티커 데이터 처리 오류 ({exchange}, {symbol}): {e}")
        
        def on_orderbook_data(exchange: str, symbol: str, data: dict):
            """호가 데이터 처리"""
            try:
                # 등록된 콜백 호출
                if 'orderbook' in self.data_callbacks:
                    self.data_callbacks['orderbook'](exchange, symbol, data)
                    
            except Exception as e:
                self.logger.error(f"호가 데이터 처리 오류 ({exchange}, {symbol}): {e}")
        
        # WebSocket 매니저에 콜백 등록
        self.websocket_manager.set_data_callbacks(
            ticker_callback=on_ticker_data,
            orderbook_callback=on_orderbook_data
        )
    
    async def start(self):
        """데이터 수집 시작"""
        self.logger.info("실시간 데이터 수집 시작...")
        
        try:
            # WebSocket 연결
            await self.websocket_manager.connect_all_websockets()
            
            # 심볼 구독
            if self.active_symbols:
                await self.websocket_manager.subscribe_to_symbols(self.active_symbols)
            
            # 리스닝 시작
            await self.websocket_manager.start_listening()
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            self.stats['active_connections'] = self.websocket_manager.stats['active_connections']
            
            self.logger.info("✅ 실시간 데이터 수집 시작 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 수집 시작 실패: {e}")
            raise
    
    async def stop(self):
        """데이터 수집 중지"""
        self.logger.info("실시간 데이터 수집 중지...")
        
        try:
            self.running = False
            await self.websocket_manager.stop()
            
            # 실행 통계 출력
            if self.stats['start_time']:
                runtime = datetime.now() - self.stats['start_time']
                self.logger.info(f"📊 실행 시간: {runtime}")
                self.logger.info(f"📈 총 메시지: {self.stats['total_messages']:,}개")
                
                for exchange, count in self.stats['messages_per_exchange'].items():
                    self.logger.info(f"  {exchange}: {count:,}개")
            
            self.logger.info("✅ 실시간 데이터 수집 중지 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 수집 중지 중 오류: {e}")
    
    def get_stats(self) -> Dict:
        """통계 반환"""
        return {
            **self.stats,
            'websocket_stats': self.websocket_manager.stats if self.websocket_manager else {}
        }
    
    def is_running(self) -> bool:
        """실행 상태 확인"""
        return self.running
    
    def get_connection_status(self) -> Dict[str, bool]:
        """연결 상태 확인"""
        if not self.websocket_manager:
            return {}
        
        return {
            exchange: bool(client and hasattr(client, 'connected') and client.connected)
            for exchange, client in self.websocket_manager.websocket_clients.items()
        }
