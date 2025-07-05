"""
Coin analysis strategies for recommendation engine.
Implements Strategy pattern for different analysis methods.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
import asyncio
from dataclasses import dataclass
from enum import Enum
import math
from app.core.config import settings

@dataclass
class CoinAnalysisResult:
    """Result of coin analysis."""
    symbol: str
    score: float  # 0-100 scale
    technical_score: float
    volume_score: float
    volatility_score: float
    risk_score: float
    metadata: Dict
    timestamp: float

class AnalysisStrength(Enum):
    """Analysis strength levels."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"

class CoinAnalyzer(ABC):
    """Abstract base class for coin analysis strategies."""
    
    @abstractmethod
    async def analyze(self, symbol: str, price_data: Dict) -> Dict:
        """
        Analyze a single coin and return analysis metrics.
        
        Args:
            symbol: Coin symbol (e.g., 'BTC')
            price_data: Dict containing price history and current data
            
        Returns:
            Dict with analysis results
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the analysis strategy."""
        pass
    
    @property
    @abstractmethod
    def weight(self) -> float:
        """Weight of this analyzer in final score (0.0-1.0)."""
        pass

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

class VolumeAnalyzer(CoinAnalyzer):
    """Volume-based analysis."""
    
    @property
    def name(self) -> str:
        return "volume"
    
    @property
    def weight(self) -> float:
        return 0.3  # 30% weight
    
    async def analyze(self, symbol: str, price_data: Dict) -> Dict:
        """Perform volume analysis."""
        try:
            volumes = price_data.get('volumes', [])
            prices = price_data.get('prices', [])
            
            if len(volumes) < 10 or len(prices) < 10:
                return {'score': 50, 'reason': 'insufficient_volume_data'}
            
            # Volume trend analysis
            volume_trend = self._calculate_volume_trend(volumes)
            
            # Price-volume correlation
            pv_correlation = self._calculate_price_volume_correlation(prices, volumes)
            
            # Volume spike detection
            volume_spike = self._detect_volume_spike(volumes)
            
            # Combine into final score
            trend_score = self._score_volume_trend(volume_trend)
            correlation_score = self._score_pv_correlation(pv_correlation)
            spike_score = self._score_volume_spike(volume_spike)
            
            final_score = (trend_score + correlation_score + spike_score) / 3
            
            return {
                'score': final_score,
                'volume_trend': volume_trend,
                'pv_correlation': pv_correlation,
                'volume_spike': volume_spike,
                'trend_score': trend_score,
                'correlation_score': correlation_score,
                'spike_score': spike_score
            }
            
        except Exception as e:
            return {'score': 50, 'error': str(e)}
    
    def _calculate_volume_trend(self, volumes: List[float]) -> float:
        """Calculate volume trend (positive = increasing)."""
        if len(volumes) < 5:
            return 0.0
        
        recent = volumes[-5:]
        older = volumes[-10:-5] if len(volumes) >= 10 else volumes[:-5]
        
        if not older:
            return 0.0
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        if older_avg == 0:
            return 0.0
        
        return (recent_avg - older_avg) / older_avg
    
    def _calculate_price_volume_correlation(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate correlation between price and volume changes."""
        if len(prices) < 2 or len(volumes) < 2:
            return 0.0
        
        min_len = min(len(prices), len(volumes))
        
        price_changes = [prices[i] - prices[i-1] for i in range(1, min_len)]
        volume_changes = [volumes[i] - volumes[i-1] for i in range(1, min_len)]
        
        if not price_changes or not volume_changes:
            return 0.0
        
        # Simple correlation calculation
        n = len(price_changes)
        if n < 3:
            return 0.0
        
        sum_xy = sum(price_changes[i] * volume_changes[i] for i in range(n))
        sum_x = sum(price_changes)
        sum_y = sum(volume_changes)
        sum_x2 = sum(x**2 for x in price_changes)
        sum_y2 = sum(y**2 for y in volume_changes)
        
        denominator = math.sqrt((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))
        
        if denominator == 0:
            return 0.0
        
        correlation = (n * sum_xy - sum_x * sum_y) / denominator
        return correlation
    
    def _detect_volume_spike(self, volumes: List[float]) -> float:
        """Detect volume spikes (current vs average)."""
        if len(volumes) < 10:
            return 1.0
        
        current = volumes[-1]
        avg_volume = sum(volumes[-10:-1]) / 9
        
        if avg_volume == 0:
            return 1.0
        
        return current / avg_volume
    
    def _score_volume_trend(self, trend: float) -> float:
        """Score volume trend."""
        if trend > 0.2:
            return 80  # Strong increasing volume
        elif trend > 0:
            return 60  # Moderate increasing volume
        elif trend > -0.1:
            return 50  # Stable volume
        else:
            return 30  # Decreasing volume
    
    def _score_pv_correlation(self, correlation: float) -> float:
        """Score price-volume correlation."""
        if correlation > 0.3:
            return 70  # Good positive correlation
        elif correlation > 0:
            return 55  # Weak positive correlation
        elif correlation > -0.3:
            return 50  # No clear correlation
        else:
            return 40  # Negative correlation
    
    def _score_volume_spike(self, spike: float) -> float:
        """Score volume spike."""
        if spike > 2.0:
            return 75  # High volume spike
        elif spike > 1.5:
            return 60  # Moderate volume spike
        else:
            return 50  # Normal volume

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

class RiskAnalyzer(CoinAnalyzer):
    """Risk assessment analyzer."""
    
    @property
    def name(self) -> str:
        return "risk"
    
    @property
    def weight(self) -> float:
        return 0.1  # 10% weight
    
    async def analyze(self, symbol: str, price_data: Dict) -> Dict:
        """Perform risk analysis."""
        try:
            prices = price_data.get('prices', [])
            volumes = price_data.get('volumes', [])
            market_cap = price_data.get('market_cap', 0)
            
            # Calculate risk factors
            liquidity_risk = self._calculate_liquidity_risk(volumes)
            price_stability_risk = self._calculate_price_stability_risk(prices)
            market_cap_risk = self._calculate_market_cap_risk(market_cap)
            
            # Combine risk factors (lower risk = higher score)
            liquidity_score = 100 - min(100, liquidity_risk * 100)
            stability_score = 100 - min(100, price_stability_risk * 100)
            market_cap_score = 100 - min(100, market_cap_risk * 100)
            
            final_score = (liquidity_score + stability_score + market_cap_score) / 3
            
            return {
                'score': final_score,
                'liquidity_risk': liquidity_risk,
                'price_stability_risk': price_stability_risk,
                'market_cap_risk': market_cap_risk,
                'liquidity_score': liquidity_score,
                'stability_score': stability_score,
                'market_cap_score': market_cap_score
            }
            
        except Exception as e:
            return {'score': 50, 'error': str(e)}
    
    def _calculate_liquidity_risk(self, volumes: List[float]) -> float:
        """Calculate liquidity risk based on volume."""
        if not volumes:
            return 1.0  # High risk
        
        avg_volume = sum(volumes[-7:]) / min(len(volumes), 7)
        
        # Define risk thresholds (adjust based on market)
        if avg_volume > 1000000:  # High volume
            return 0.1
        elif avg_volume > 100000:  # Medium volume
            return 0.3
        elif avg_volume > 10000:  # Low volume
            return 0.6
        else:  # Very low volume
            return 0.9
    
    def _calculate_price_stability_risk(self, prices: List[float]) -> float:
        """Calculate price stability risk."""
        if len(prices) < 7:
            return 0.5
        
        # Calculate coefficient of variation
        recent_prices = prices[-7:]
        mean_price = sum(recent_prices) / len(recent_prices)
        
        if mean_price == 0:
            return 1.0
        
        variance = sum((p - mean_price)**2 for p in recent_prices) / len(recent_prices)
        std_dev = math.sqrt(variance)
        
        cv = std_dev / mean_price  # Coefficient of variation
        
        # Higher CV = higher risk
        return min(1.0, cv * 2)  # Scale to 0-1
    
    def _calculate_market_cap_risk(self, market_cap: float) -> float:
        """Calculate market cap risk (smaller cap = higher risk)."""
        if market_cap is None or market_cap == 0:
            return 0.8  # Unknown market cap = high risk
        
        # Define risk levels based on market cap (in USD)
        if market_cap > 10_000_000_000:  # > 10B (Large cap)
            return 0.1
        elif market_cap > 1_000_000_000:  # > 1B (Mid cap)
            return 0.3
        elif market_cap > 100_000_000:  # > 100M (Small cap)
            return 0.5
        else:  # < 100M (Micro cap)
            return 0.8
