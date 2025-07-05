"""
WebSocket 기반 실시간 마켓 데이터 수집 관리자 (다중 거래소 지원)

This is the main WebSocket data manager that imports components
from the modularized websocket_manager package.
"""

# Import all components from the websocket_manager package
from .websocket_manager.data_buffer import RealTimeDataBuffer
from .websocket_manager.multi_exchange_manager import MultiExchangeWebSocketManager

# Alias for backward compatibility
WebSocketDataManager = MultiExchangeWebSocketManager

# Re-export everything for backward compatibility
__all__ = [
    "RealTimeDataBuffer",
    "MultiExchangeWebSocketManager", 
    "WebSocketDataManager"
]
