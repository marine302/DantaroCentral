"""
Real-time data buffer for WebSocket market data.

This module provides data structures for buffering and managing
real-time market data updates from WebSocket connections.
"""
from datetime import datetime
from typing import List
from dataclasses import dataclass, field


@dataclass
class RealTimeDataBuffer:
    """실시간 데이터 버퍼"""
    symbol: str
    exchange: str
    latest_price: float = 0.0
    latest_volume: float = 0.0
    price_updates: List[tuple] = field(default_factory=list)  # (timestamp, price)
    volume_updates: List[tuple] = field(default_factory=list)  # (timestamp, volume)
    last_update: datetime = field(default_factory=datetime.now)
    
    def add_update(self, price: float, volume: float):
        """새로운 업데이트 추가"""
        now = datetime.now()
        
        self.latest_price = price
        self.latest_volume = volume
        self.last_update = now
        
        # 최근 100개 업데이트만 유지
        self.price_updates.append((now, price))
        self.volume_updates.append((now, volume))
        
        if len(self.price_updates) > 100:
            self.price_updates = self.price_updates[-100:]
        if len(self.volume_updates) > 100:
            self.volume_updates = self.volume_updates[-100:]
