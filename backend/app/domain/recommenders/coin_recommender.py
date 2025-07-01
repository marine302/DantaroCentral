"""
Advanced coin recommendation engine with strategy pattern.
Combines multiple analysis strategies to provide comprehensive coin recommendations.
"""
from typing import List, Dict, Optional
from decimal import Decimal
import asyncio
import time
import logging
from dataclasses import dataclass

from backend.app.domain.analyzers import (
    CoinAnalyzer, CoinAnalysisResult, AnalysisStrength,
    TechnicalAnalyzer, VolumeAnalyzer, VolatilityAnalyzer, RiskAnalyzer
)

logger = logging.getLogger(__name__)

@dataclass
class CoinRecommendation:
    """Complete coin recommendation with analysis details."""
    symbol: str
    rank: int
    overall_score: float
    technical_score: float
    volume_score: float
    volatility_score: float
    risk_score: float
    strength: AnalysisStrength
    current_price: float
    price_change_24h: float
    volume_24h: float
    market_cap: Optional[float]
    analysis_details: Dict
    timestamp: float

@dataclass
class CoinScore:
    """Data class for coin analysis results."""
    symbol: str
    score: float
    volume_score: float
    volatility_score: float
    technical_score: float
    risk_score: float
    metadata: Dict


class CoinAnalyzer(ABC):
    """Abstract base class for coin analysis strategies."""
    
    @abstractmethod
    async def analyze(self, symbol: str, market_data: Dict) -> CoinScore:
        """
        Analyze a single coin and return a score.
        
        Args:
            symbol: The coin symbol (e.g., 'BTC/KRW')
            market_data: Market data including price, volume, etc.
            
        Returns:
            CoinScore object with analysis results
        """
        pass
    
    @abstractmethod
    def get_weight(self) -> float:
        """Return the weight of this analyzer in final scoring."""
        pass


class TechnicalAnalyzer(CoinAnalyzer):
    """Technical analysis implementation using various indicators."""
    
    def __init__(self, weight: float = 0.4):
        self.weight = weight
    
    async def analyze(self, symbol: str, market_data: Dict) -> CoinScore:
        """Perform technical analysis on the coin."""
        try:
            # Extract price data
            current_price = Decimal(str(market_data.get('current_price', 0)))
            price_history = market_data.get('price_history', [])
            
            # Calculate technical indicators
            rsi_score = self._calculate_rsi_score(price_history)
            macd_score = self._calculate_macd_score(price_history)
            bollinger_score = self._calculate_bollinger_score(price_history, current_price)
            
            # Combine technical scores
            technical_score = (rsi_score + macd_score + bollinger_score) / 3
            
            return CoinScore(
                symbol=symbol,
                score=technical_score * self.weight,
                volume_score=0,
                volatility_score=0,
                technical_score=technical_score,
                risk_score=0,
                metadata={
                    'rsi_score': rsi_score,
                    'macd_score': macd_score,
                    'bollinger_score': bollinger_score
                }
            )
            
        except Exception as e:
            logger.error(f"Technical analysis failed for {symbol}: {e}")
            return CoinScore(
                symbol=symbol,
                score=0,
                volume_score=0,
                volatility_score=0,
                technical_score=0,
                risk_score=1.0,  # High risk on error
                metadata={'error': str(e)}
            )
    
    def get_weight(self) -> float:
        return self.weight
    
    def _calculate_rsi_score(self, price_history: List[Dict]) -> float:
        """Calculate RSI-based score (0-1)."""
        if len(price_history) < 14:
            return 0.5  # Neutral score for insufficient data
        
        # Simplified RSI calculation
        gains = []
        losses = []
        
        for i in range(1, min(15, len(price_history))):
            change = price_history[i]['close'] - price_history[i-1]['close']
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0.001
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Score: prefer RSI between 30-70 (avoid overbought/oversold)
        if 30 <= rsi <= 70:
            return 0.8
        elif rsi < 30:
            return 0.6  # Oversold might be buying opportunity
        else:  # rsi > 70
            return 0.3  # Overbought
    
    def _calculate_macd_score(self, price_history: List[Dict]) -> float:
        """Calculate MACD-based score (0-1)."""
        if len(price_history) < 26:
            return 0.5
        
        # Simplified MACD calculation
        prices = [p['close'] for p in price_history[-26:]]
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd = ema_12 - ema_26
        
        # Positive MACD is bullish
        return min(max(macd / ema_26 + 0.5, 0), 1) if ema_26 != 0 else 0.5
    
    def _calculate_bollinger_score(self, price_history: List[Dict], current_price: Decimal) -> float:
        """Calculate Bollinger Bands score (0-1)."""
        if len(price_history) < 20:
            return 0.5
        
        prices = [p['close'] for p in price_history[-20:]]
        sma = sum(prices) / len(prices)
        variance = sum((p - sma) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)
        
        current = float(current_price)
        
        # Score based on position relative to bands
        if current <= lower_band:
            return 0.8  # Near lower band - potential buy
        elif current >= upper_band:
            return 0.2  # Near upper band - potential sell
        else:
            # Linear interpolation between bands
            band_position = (current - lower_band) / (upper_band - lower_band)
            return 0.8 - (0.6 * band_position)  # Prefer lower positions
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if not prices or period <= 0:
            return 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema


class VolumeAnalyzer(CoinAnalyzer):
    """Volume analysis implementation."""
    
    def __init__(self, weight: float = 0.3):
        self.weight = weight
    
    async def analyze(self, symbol: str, market_data: Dict) -> CoinScore:
        """Analyze volume patterns and trends."""
        try:
            volume_24h = market_data.get('volume_24h', 0)
            volume_history = market_data.get('volume_history', [])
            
            # Calculate volume score
            volume_score = self._calculate_volume_score(volume_24h, volume_history)
            
            return CoinScore(
                symbol=symbol,
                score=volume_score * self.weight,
                volume_score=volume_score,
                volatility_score=0,
                technical_score=0,
                risk_score=0,
                metadata={
                    'volume_24h': volume_24h,
                    'avg_volume': sum(volume_history) / len(volume_history) if volume_history else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Volume analysis failed for {symbol}: {e}")
            return CoinScore(
                symbol=symbol,
                score=0,
                volume_score=0,
                volatility_score=0,
                technical_score=0,
                risk_score=1.0,
                metadata={'error': str(e)}
            )
    
    def get_weight(self) -> float:
        return self.weight
    
    def _calculate_volume_score(self, current_volume: float, volume_history: List[float]) -> float:
        """Calculate volume-based score (0-1)."""
        if not volume_history or current_volume <= 0:
            return 0
        
        avg_volume = sum(volume_history) / len(volume_history)
        if avg_volume <= 0:
            return 0
        
        volume_ratio = current_volume / avg_volume
        
        # Prefer higher volume but not extremely high
        if volume_ratio >= 2.0:
            return 0.9  # High volume is good
        elif volume_ratio >= 1.5:
            return 0.8
        elif volume_ratio >= 1.0:
            return 0.6
        elif volume_ratio >= 0.5:
            return 0.4
        else:
            return 0.2  # Very low volume


class VolatilityAnalyzer(CoinAnalyzer):
    """Volatility analysis for risk assessment."""
    
    def __init__(self, weight: float = 0.3):
        self.weight = weight
    
    async def analyze(self, symbol: str, market_data: Dict) -> CoinScore:
        """Analyze price volatility."""
        try:
            price_history = market_data.get('price_history', [])
            
            volatility_score, risk_score = self._calculate_volatility_scores(price_history)
            
            return CoinScore(
                symbol=symbol,
                score=volatility_score * self.weight,
                volume_score=0,
                volatility_score=volatility_score,
                technical_score=0,
                risk_score=risk_score,
                metadata={
                    'volatility': risk_score,
                    'price_points': len(price_history)
                }
            )
            
        except Exception as e:
            logger.error(f"Volatility analysis failed for {symbol}: {e}")
            return CoinScore(
                symbol=symbol,
                score=0,
                volume_score=0,
                volatility_score=0,
                technical_score=0,
                risk_score=1.0,
                metadata={'error': str(e)}
            )
    
    def get_weight(self) -> float:
        return self.weight
    
    def _calculate_volatility_scores(self, price_history: List[Dict]) -> tuple[float, float]:
        """Calculate volatility and risk scores."""
        if len(price_history) < 7:
            return 0.5, 0.5
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(price_history)):
            prev_price = price_history[i-1]['close']
            curr_price = price_history[i]['close']
            if prev_price > 0:
                daily_return = (curr_price - prev_price) / prev_price
                returns.append(daily_return)
        
        if not returns:
            return 0.5, 0.5
        
        # Calculate standard deviation of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5
        
        # Convert volatility to scores
        risk_score = min(volatility * 10, 1.0)  # Higher volatility = higher risk
        volatility_score = max(0, 1 - risk_score)  # Lower volatility = higher score
        
        return volatility_score, risk_score


class CoinRecommender:
    """
    Main recommender that combines multiple analyzers.
    
    Uses Strategy pattern to combine different analysis methods
    and provides ranked coin recommendations.
    """
    
    def __init__(self, analyzers: Optional[List[CoinAnalyzer]] = None):
        if analyzers is None:
            # Default analyzers with balanced weights
            self.analyzers = [
                TechnicalAnalyzer(weight=0.4),
                VolumeAnalyzer(weight=0.3),
                VolatilityAnalyzer(weight=0.3)
            ]
        else:
            self.analyzers = analyzers
    
    async def get_recommendations(self, market_data: Dict[str, Dict], top_n: int = 50) -> List[Dict]:
        """
        Get top N coin recommendations based on analysis.
        
        Args:
            market_data: Dictionary with symbol as key and market data as value
            top_n: Number of top recommendations to return
            
        Returns:
            List of dictionaries with coin recommendations
        """
        try:
            # Analyze all coins concurrently
            tasks = []
            for symbol, data in market_data.items():
                task = self._analyze_coin(symbol, data)
                tasks.append(task)
            
            # Wait for all analyses to complete
            coin_scores = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and combine scores
            final_scores = []
            for result in coin_scores:
                if isinstance(result, Exception):
                    logger.error(f"Analysis failed: {result}")
                    continue
                
                if result:
                    final_scores.append(result)
            
            # Sort by total score (descending)
            final_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Return top N recommendations
            return final_scores[:top_n]
            
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []
    
    async def _analyze_coin(self, symbol: str, market_data: Dict) -> Optional[Dict]:
        """Analyze a single coin using all analyzers."""
        try:
            # Run all analyzers concurrently
            tasks = [analyzer.analyze(symbol, market_data) for analyzer in self.analyzers]
            scores = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine scores
            total_score = 0
            combined_metadata = {}
            volume_score = 0
            volatility_score = 0
            technical_score = 0
            risk_score = 0
            
            valid_scores = 0
            for score in scores:
                if isinstance(score, Exception):
                    logger.warning(f"Analyzer failed for {symbol}: {score}")
                    continue
                
                if isinstance(score, CoinScore):
                    total_score += score.score
                    volume_score += score.volume_score
                    volatility_score += score.volatility_score
                    technical_score += score.technical_score
                    risk_score += score.risk_score
                    combined_metadata.update(score.metadata)
                    valid_scores += 1
            
            if valid_scores == 0:
                return None
            
            # Average the component scores
            volume_score /= valid_scores
            volatility_score /= valid_scores
            technical_score /= valid_scores
            risk_score /= valid_scores
            
            return {
                'symbol': symbol,
                'total_score': total_score,
                'component_scores': {
                    'technical': technical_score,
                    'volume': volume_score,
                    'volatility': volatility_score,
                    'risk': risk_score
                },
                'metadata': combined_metadata,
                'recommendation_strength': self._get_recommendation_strength(total_score),
                'timestamp': market_data.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze coin {symbol}: {e}")
            return None
    
    def _get_recommendation_strength(self, score: float) -> str:
        """Convert numerical score to recommendation strength."""
        if score >= 0.8:
            return "STRONG_BUY"
        elif score >= 0.6:
            return "BUY"
        elif score >= 0.4:
            return "HOLD"
        elif score >= 0.2:
            return "WEAK_SELL"
        else:
            return "SELL"
