"""
Upbit 데이터 변환기
Upbit API 응답을 공통 인터페이스로 변환
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any
from ..base import Balance, Ticker, OrderBook, Order, Trade, OrderSide, OrderType, OrderStatus


class UpbitDataMapper:
    """Upbit 데이터 변환기"""
    
    @staticmethod
    def parse_balance(data: Dict) -> Balance:
        """잔고 데이터 변환"""
        return Balance(
            currency=data['currency'],
            free=Decimal(data['balance']),
            locked=Decimal(data['locked']),
            total=Decimal(data['balance']) + Decimal(data['locked'])
        )
    
    @staticmethod
    def parse_ticker(data: Dict) -> Ticker:
        """시세 데이터 변환"""
        return Ticker(
            symbol=data['market'],
            price=Decimal(str(data['trade_price'])),
            high=Decimal(str(data['high_price'])),
            low=Decimal(str(data['low_price'])),
            volume=Decimal(str(data['trade_volume'])),
            change_percent=Decimal(str(data['change_rate'] * 100)),
            timestamp=datetime.fromisoformat(data['trade_date_utc'] + 'T' + data['trade_time_utc'])
        )
    
    @staticmethod
    def parse_orderbook(data: Dict) -> OrderBook:
        """호가 데이터 변환"""
        bids = []
        asks = []
        
        for item in data['orderbook_units']:
            bids.append([
                Decimal(str(item['bid_price'])),
                Decimal(str(item['bid_size']))
            ])
            asks.append([
                Decimal(str(item['ask_price'])),
                Decimal(str(item['ask_size']))
            ])
        
        return OrderBook(
            symbol=data['market'],
            bids=bids,
            asks=asks,
            timestamp=datetime.fromisoformat(data['timestamp'])
        )
    
    @staticmethod
    def parse_order(data: Dict) -> Order:
        """주문 데이터 변환"""
        # Upbit 주문 상태 매핑
        status_map = {
            'wait': OrderStatus.OPEN,
            'watch': OrderStatus.OPEN,
            'done': OrderStatus.FILLED,
            'cancel': OrderStatus.CANCELLED
        }
        
        # Upbit 주문 타입 매핑
        type_map = {
            'limit': OrderType.LIMIT,
            'price': OrderType.MARKET,  # 시장가 매수
            'market': OrderType.MARKET  # 시장가 매도
        }
        
        # 주문 방향 매핑
        side_map = {
            'bid': OrderSide.BUY,
            'ask': OrderSide.SELL
        }
        
        return Order(
            id=data['uuid'],
            symbol=data['market'],
            side=side_map.get(data['side'], OrderSide.BUY),
            type=type_map.get(data['ord_type'], OrderType.LIMIT),
            amount=Decimal(str(data.get('volume', '0'))),
            price=Decimal(str(data.get('price', '0'))),
            filled=Decimal(str(data.get('executed_volume', '0'))),
            remaining=Decimal(str(data.get('remaining_volume', '0'))),
            status=status_map.get(data['state'], OrderStatus.OPEN),
            timestamp=datetime.fromisoformat(data['created_at']),
            fee=Decimal(str(data.get('paid_fee', '0')))
        )
    
    @staticmethod
    def parse_trade(data: Dict) -> Trade:
        """거래 내역 변환"""
        side_map = {
            'bid': OrderSide.BUY,
            'ask': OrderSide.SELL
        }
        
        return Trade(
            id=data['uuid'],
            symbol=data['market'],
            side=side_map.get(data['side'], OrderSide.BUY),
            amount=Decimal(str(data['volume'])),
            price=Decimal(str(data['price'])),
            fee=Decimal(str(data.get('fee', '0'))),
            timestamp=datetime.fromisoformat(data['created_at'])
        )
