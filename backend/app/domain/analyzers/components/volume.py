"""
Volume analysis component for coin analysis.

This module analyzes trading volume patterns, price-volume correlations,
and volume spikes to assess market interest and momentum.
"""
from typing import Dict, List
import math
from .base import CoinAnalyzer


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
