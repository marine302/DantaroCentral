"""
OKX 데이터 변환 모듈
단일 책임: OKX API 응답을 통합 인터페이스 모델로 변환
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from ..base import (
    Balance, Ticker, OrderBook, Order, Trade,
    OrderSide, OrderType, OrderStatus
)


class OKXDataMapper:
    """OKX API 응답 데이터 변환기"""
    
    @staticmethod
    def map_balance(data: List[Dict]) -> Dict[str, Balance]:
        """잔고 데이터 변환"""
        balances = {}
        
        if isinstance(data, list) and len(data) > 0:
            details = data[0].get('details', []) if isinstance(data[0], dict) else []
            for detail in details:
                if not isinstance(detail, dict):
                    continue
                curr = detail.get('ccy')
                if not curr or not isinstance(curr, str):
                    continue
                
                balances[curr] = Balance(
                    currency=curr,
                    available=Decimal(detail.get('availBal', '0')),
                    locked=Decimal(detail.get('frozenBal', '0')),
                    total=Decimal(detail.get('bal', '0'))
                )
        
        return balances
    
    @staticmethod
    def map_ticker(data: List[Dict], symbol: str) -> Ticker:
        """시세 데이터 변환"""
        if not data:
            raise Exception(f"심볼 {symbol}의 시세 정보를 찾을 수 없습니다")
        
        ticker_data = data[0]
        return Ticker(
            symbol=symbol,
            price=Decimal(ticker_data.get('last', '0')),
            bid=Decimal(ticker_data.get('bidPx', '0')),
            ask=Decimal(ticker_data.get('askPx', '0')),
            volume=Decimal(ticker_data.get('vol24h', '0')),
            timestamp=datetime.fromtimestamp(int(ticker_data.get('ts', '0')) / 1000)
        )
    
    @staticmethod
    def map_orderbook(data: List[Dict], symbol: str) -> OrderBook:
        """호가 데이터 변환"""
        if not data:
            raise Exception(f"심볼 {symbol}의 호가 정보를 찾을 수 없습니다")
        
        orderbook_data = data[0]
        bids = [[Decimal(bid[0]), Decimal(bid[1])] for bid in orderbook_data.get('bids', [])]
        asks = [[Decimal(ask[0]), Decimal(ask[1])] for ask in orderbook_data.get('asks', [])]
        
        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.fromtimestamp(int(orderbook_data.get('ts', '0')) / 1000)
        )
    
    @staticmethod
    def map_order(data: Dict, symbol: Optional[str] = None, side: Optional[OrderSide] = None, 
                  order_type: Optional[OrderType] = None, amount: Optional[Decimal] = None, 
                  price: Optional[Decimal] = None) -> Order:
        """주문 데이터 변환"""
        status_map = {
            'live': OrderStatus.OPEN,
            'filled': OrderStatus.CLOSED,
            'canceled': OrderStatus.CANCELLED
        }
        
        return Order(
            id=data.get('ordId', ''),
            symbol=symbol or data.get('instId', ''),
            side=side or OrderSide(data.get('side', 'buy')),
            type=order_type or (OrderType.LIMIT if data.get('ordType', 'limit') == 'limit' else OrderType.MARKET),
            amount=amount or Decimal(data.get('sz', '0')),
            price=price or (Decimal(data.get('px', '0')) if data.get('px') else None),
            filled=Decimal(data.get('fillSz', '0')),
            remaining=Decimal(data.get('sz', '0')) - Decimal(data.get('fillSz', '0')),
            status=status_map.get(data.get('state', ''), OrderStatus.PENDING),
            timestamp=datetime.fromtimestamp(int(data.get('cTime', '0')) / 1000)
        )
    
    @staticmethod
    def map_trade_history(data: List[Dict]) -> List[Trade]:
        """체결 내역 변환"""
        trades = []
        
        for trade_data in data:
            trades.append(Trade(
                id=trade_data.get('tradeId', ''),
                order_id=trade_data.get('ordId', ''),
                symbol=trade_data.get('instId', ''),
                side=OrderSide(trade_data.get('side', 'buy')),
                amount=Decimal(trade_data.get('fillSz', '0')),
                price=Decimal(trade_data.get('fillPx', '0')),
                fee=Decimal(trade_data.get('fee', '0')),
                timestamp=datetime.fromtimestamp(int(trade_data.get('ts', '0')) / 1000)
            ))
        
        return trades
    
    @staticmethod
    def map_order_list(data: List[Dict]) -> List[Order]:
        """주문 목록 변환"""
        return [OKXDataMapper.map_order(order_data) for order_data in data]
    
    @staticmethod
    def map_symbols(data: List[Dict]) -> List[str]:
        """심볼 목록 변환"""
        return [instrument.get('instId', '') for instrument in data]
