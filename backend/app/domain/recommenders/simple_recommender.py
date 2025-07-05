"""
Enhanced coin recommendation engine with advanced analysis.
"""
from typing import List, Dict, Optional
from decimal import Decimal
import asyncio
import time
import logging
from dataclasses import dataclass

# Import advanced analyzers
from app.domain.analyzers import (
    TechnicalAnalyzer, VolumeAnalyzer, VolatilityAnalyzer, RiskAnalyzer
)
from app.core.config import settings

logger = logging.getLogger(__name__)

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
    confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'symbol': self.symbol,
            'total_score': self.score / 100.0,  # Convert to 0-1 scale
            'component_scores': {
                'technical': self.technical_score / 100.0,
                'volume': self.volume_score / 100.0,
                'volatility': self.volatility_score / 100.0,
                'risk': self.risk_score / 100.0
            },
            'recommendation_strength': self._get_strength_label(),
            'metadata': self.metadata,
            'timestamp': None
        }
    
    def _get_strength_label(self) -> str:
        """Get recommendation strength label."""
        if self.score >= 70:
            return "STRONG_BUY"
        elif self.score >= 50:
            return "BUY"
        elif self.score >= 30:
            return "HOLD"
        else:
            return "WEAK_SELL"

class CoinRecommender:
    """Enhanced coin recommendation engine."""
    
    def __init__(self):
        self.analyzers = [
            TechnicalAnalyzer(),
            VolumeAnalyzer(),
            VolatilityAnalyzer(),
            RiskAnalyzer()
        ]
        
    async def get_recommendations(self, limit: int = 50) -> List[CoinScore]:
        try:
            market_data = self._generate_mock_data()
            coin_scores = []
            for symbol, data in market_data.items():
                score = await self._analyze_coin(symbol, data)
                coin_scores.append(score)
            coin_scores.sort(key=lambda x: x.score, reverse=True)
            return coin_scores[:limit]
        except Exception as e:
            logger.error(f"[SimpleRecommender] Error getting recommendations: {e}")
            return []
    
    async def _analyze_coin(self, symbol: str, market_data: Dict) -> CoinScore:
        """Analyze a single coin using all analyzers."""
        try:
            # Run all analyzers
            analyzer_results = []
            for analyzer in self.analyzers:
                result = await analyzer.analyze(symbol, market_data)
                analyzer_results.append((analyzer, result))
            
            # Combine scores with weights
            total_score = 0.0
            total_weight = 0.0
            individual_scores = {}
            combined_metadata = {}
            
            for analyzer, result in analyzer_results:
                if isinstance(result, dict) and 'score' in result:
                    score = result['score']
                    weight = analyzer.weight
                    
                    total_score += score * weight
                    total_weight += weight
                    
                    individual_scores[analyzer.name] = score
                    combined_metadata[analyzer.name] = result
            
            # Calculate final score
            final_score = total_score / total_weight if total_weight > 0 else 0.0
            
            return CoinScore(
                symbol=symbol,
                score=final_score,
                technical_score=individual_scores.get('technical', 0.0),
                volume_score=individual_scores.get('volume', 0.0),
                volatility_score=individual_scores.get('volatility', 0.0),
                risk_score=individual_scores.get('risk', 0.0),
                metadata=combined_metadata,
                confidence=min(1.0, final_score / 100.0)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return CoinScore(
                symbol=symbol,
                score=0.0,
                technical_score=0.0,
                volume_score=0.0,
                volatility_score=0.0,
                risk_score=0.0,
                metadata={'error': str(e)},
                confidence=0.0
            )
    
    def _generate_mock_data(self) -> Dict[str, Dict]:
        """Generate mock market data for testing."""
        import random
        
        coins = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'MATIC', 'AVAX', 'ATOM', 'NEAR', 'FTM']
        mock_data = {}
        
        for coin in coins:
            # Generate realistic price history
            base_price = random.uniform(100, 50000)
            prices = []
            for i in range(30):
                price = base_price * (1 + random.uniform(-0.1, 0.1))
                prices.append(price)
                base_price = price
            
            volumes = [random.uniform(1000000, 10000000) for _ in range(30)]
            
            mock_data[coin] = {
                'current_price': prices[-1],
                'price_change_24h': (prices[-1] - prices[-2]) / prices[-2] * 100,
                'volume_24h': volumes[-1],
                'market_cap': prices[-1] * random.uniform(1000000, 100000000),
                'prices': prices,
                'volumes': volumes
            }
        
        return mock_data
