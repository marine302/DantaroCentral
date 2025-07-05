"""
Volatility analysis component for coin analysis.

This module analyzes price volatility patterns, price ranges,
and volatility trends to assess market stability and trading opportunities.
"""
from typing import Dict, List
import math
from .base import CoinAnalyzer


class VolatilityAnalyzer(CoinAnalyzer):
    """Volatility-based analysis."""
    
    @property
    def name(self) -> str:
        return "volatility"
    
    @property
    def weight(self) -> float:
        return 0.2  # 20% weight
    
    async def analyze(self, symbol: str, price_data: Dict) -> Dict:
        """Perform volatility analysis."""
        try:
            prices = price_data.get('prices', [])
            
            if len(prices) < 10:
                return {'score': 50, 'reason': 'insufficient_price_data'}
            
            # Calculate different volatility measures
            daily_volatility = self._calculate_daily_volatility(prices)
            price_range = self._calculate_price_range(prices)
            volatility_trend = self._calculate_volatility_trend(prices)
            
            # Score volatility (moderate volatility is preferred)
            volatility_score = self._score_volatility(daily_volatility)
            range_score = self._score_price_range(price_range)
            trend_score = self._score_volatility_trend(volatility_trend)
            
            final_score = (volatility_score + range_score + trend_score) / 3
            
            return {
                'score': final_score,
                'daily_volatility': daily_volatility,
                'price_range': price_range,
                'volatility_trend': volatility_trend,
                'volatility_score': volatility_score,
                'range_score': range_score,
                'trend_score': trend_score
            }
            
        except Exception as e:
            return {'score': 50, 'error': str(e)}
    
    def _calculate_daily_volatility(self, prices: List[float], days: int = 7) -> float:
        """Calculate daily volatility over specified days."""
        if len(prices) < days + 1:
            return 0.0
        
        recent_prices = prices[-days-1:]
        daily_returns = []
        
        for i in range(1, len(recent_prices)):
            if recent_prices[i-1] != 0:
                return_rate = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
                daily_returns.append(return_rate)
        
        if len(daily_returns) < 2:
            return 0.0
        
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return)**2 for r in daily_returns) / len(daily_returns)
        
        return math.sqrt(variance)
    
    def _calculate_price_range(self, prices: List[float], days: int = 7) -> float:
        """Calculate price range over specified days."""
        if len(prices) < days:
            return 0.0
        
        recent_prices = prices[-days:]
        max_price = max(recent_prices)
        min_price = min(recent_prices)
        
        if max_price == 0:
            return 0.0
        
        return (max_price - min_price) / max_price
    
    def _calculate_volatility_trend(self, prices: List[float]) -> float:
        """Calculate if volatility is increasing or decreasing."""
        if len(prices) < 20:
            return 0.0
        
        # Compare recent volatility with older volatility
        recent_vol = self._calculate_daily_volatility(prices[-10:], 7)
        older_vol = self._calculate_daily_volatility(prices[-20:-10], 7)
        
        if older_vol == 0:
            return 0.0
        
        return (recent_vol - older_vol) / older_vol
    
    def _score_volatility(self, volatility: float) -> float:
        """Score volatility (moderate is best for trading)."""
        if volatility < 0.01:
            return 30  # Too low volatility
        elif volatility < 0.05:
            return 80  # Good volatility for trading
        elif volatility < 0.1:
            return 60  # High but manageable
        else:
            return 20  # Too volatile/risky
    
    def _score_price_range(self, price_range: float) -> float:
        """Score price range."""
        if price_range < 0.02:
            return 30  # Too narrow range
        elif price_range < 0.08:
            return 70  # Good range for trading
        elif price_range < 0.15:
            return 50  # Wide range
        else:
            return 25  # Too wide/risky
    
    def _score_volatility_trend(self, trend: float) -> float:
        """Score volatility trend."""
        if trend > 0.2:
            return 40  # Rapidly increasing volatility
        elif trend > 0:
            return 60  # Moderate increase
        elif trend > -0.2:
            return 70  # Stable or slight decrease
        else:
            return 50  # Rapidly decreasing
