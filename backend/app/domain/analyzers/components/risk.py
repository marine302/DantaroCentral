"""
Risk analysis component for coin analysis.

This module assesses various risk factors including liquidity risk,
price stability risk, and market cap risk for comprehensive risk evaluation.
"""
from typing import Dict, List
import math
from .base import CoinAnalyzer


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
