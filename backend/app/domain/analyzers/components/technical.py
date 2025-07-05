"""
Technical analysis component for coin analysis.

This module implements technical indicators like RSI, MACD, and Bollinger Bands
for analyzing coin price movements and trends.
"""
from typing import Dict, List
import math
from app.core.config import settings
from .base import CoinAnalyzer


class TechnicalAnalyzer(CoinAnalyzer):
    """Technical analysis using common indicators."""
    
    @property
    def name(self) -> str:
        return "technical"
    
    @property
    def weight(self) -> float:
        return getattr(settings, "technical_analyzer_weight", 0.4)  # settings 기반화
    
    async def analyze(self, symbol: str, price_data: Dict) -> Dict:
        """Perform technical analysis."""
        try:
            prices = price_data.get('prices', [])
            if len(prices) < 20:
                return {'score': 0, 'reason': 'insufficient_data'}
            
            # Calculate RSI (Relative Strength Index)
            rsi = self._calculate_rsi(prices, period=14)
            
            # Calculate MACD
            macd_line, signal_line = self._calculate_macd(prices)
            
            # Calculate Bollinger Bands position
            bb_position = self._calculate_bollinger_position(prices)
            
            # Combine indicators into score
            rsi_score = self._score_rsi(rsi)
            macd_score = self._score_macd(macd_line, signal_line)
            bb_score = self._score_bollinger(bb_position)
            
            final_score = (rsi_score + macd_score + bb_score) / 3
            
            return {
                'score': final_score,
                'rsi': rsi,
                'rsi_score': rsi_score,
                'macd_line': macd_line,
                'signal_line': signal_line,
                'macd_score': macd_score,
                'bb_position': bb_position,
                'bb_score': bb_score
            }
            
        except Exception as e:
            return {'score': 0, 'error': str(e)}
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0  # Neutral
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> tuple:
        """Calculate MACD and signal line."""
        if len(prices) < 26:
            return 0.0, 0.0
        
        # EMA calculation
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        
        # Signal line (9-period EMA of MACD)
        macd_history = [macd_line] * 9  # Simplified
        signal_line = sum(macd_history) / len(macd_history)
        
        return macd_line, signal_line
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_position(self, prices: List[float], period: int = 20) -> float:
        """Calculate position within Bollinger Bands."""
        if len(prices) < period:
            return 0.5  # Middle position
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / len(recent_prices)
        
        variance = sum((p - sma) ** 2 for p in recent_prices) / len(recent_prices)
        std_dev = math.sqrt(variance)
        
        current_price = prices[-1]
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)
        
        if upper_band == lower_band:
            return 0.5
        
        position = (current_price - lower_band) / (upper_band - lower_band)
        return max(0, min(1, position))  # Clamp between 0 and 1
    
    def _score_rsi(self, rsi: float) -> float:
        """Score RSI value (oversold is bullish)."""
        if rsi < 30:
            return 80  # Oversold, potentially bullish
        elif rsi > 70:
            return 20  # Overbought, potentially bearish
        else:
            return 50  # Neutral
    
    def _score_macd(self, macd_line: float, signal_line: float) -> float:
        """Score MACD crossover."""
        if macd_line > signal_line:
            return 70  # Bullish crossover
        else:
            return 30  # Bearish
    
    def _score_bollinger(self, position: float) -> float:
        """Score Bollinger Band position."""
        if position < 0.2:
            return 80  # Near lower band, potentially oversold
        elif position > 0.8:
            return 20  # Near upper band, potentially overbought
        else:
            return 50  # Neutral
