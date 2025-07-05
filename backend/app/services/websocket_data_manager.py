"""
WebSocket 데이터 관리자 - 임시로 단순화
"""
import logging

logger = logging.getLogger(__name__)

class MultiExchangeWebSocketManager:
    """임시 WebSocket 매니저 (단순화됨)"""
    
    def __init__(self):
        self.initialized = False
        logger.info("임시 WebSocket 매니저 초기화")
    
    async def initialize_exchanges(self):
        """임시 초기화 메서드"""
        logger.info("WebSocket 연결 임시로 비활성화")
        self.initialized = True
    
    async def start_data_collection(self):
        """임시 데이터 수집 시작"""
        logger.info("WebSocket 데이터 수집 임시로 비활성화")

# Alias for backward compatibility
WebSocketDataManager = MultiExchangeWebSocketManager
