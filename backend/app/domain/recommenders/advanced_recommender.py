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

from app.domain.analyzers import (
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

class CoinRecommender:
    """
    Main recommendation engine that combines multiple analyzers.
    Uses strategy pattern for different analysis methods.
    """
    
    def __init__(self, analyzers: Optional[List[CoinAnalyzer]] = None):
        """
        Initialize recommender with analyzers.
        
        Args:
            analyzers: List of analyzer strategies. If None, uses default set.
        """
        if analyzers is None:
            self.analyzers = [
                TechnicalAnalyzer(),
                VolumeAnalyzer(),
                VolatilityAnalyzer(),
                RiskAnalyzer()
            ]
        else:
            self.analyzers = analyzers
        
        # Validate weights sum to approximately 1.0
        total_weight = sum(analyzer.weight for analyzer in self.analyzers)
        if abs(total_weight - 1.0) > 0.1:
            logger.warning(f"Analyzer weights sum to {total_weight}, expected ~1.0")
    
    async def get_recommendations(
        self, 
        coin_data: Dict[str, Dict],
        limit: int = 50,
        min_score: float = 30.0
    ) -> List[CoinRecommendation]:
        """
        Get top coin recommendations based on analysis.
        
        Args:
            coin_data: Dict mapping coin symbols to their market data
            limit: Maximum number of recommendations to return
            min_score: Minimum score threshold for recommendations
            
        Returns:
            List of CoinRecommendation objects, sorted by score (highest first)
        """
        logger.info(f"Analyzing {len(coin_data)} coins for recommendations")
        
        # Analyze all coins concurrently
        analysis_tasks = []
        for symbol, data in coin_data.items():
            task = asyncio.create_task(self._analyze_coin(symbol, data))
            analysis_tasks.append(task)
        
        # Wait for all analysis to complete
        analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Filter out failed analyses and convert to recommendations
        recommendations = []
        for i, result in enumerate(analysis_results):
            if isinstance(result, Exception):
                symbol = list(coin_data.keys())[i]
                logger.error(f"Analysis failed for {symbol}: {result}")
                continue
            
            # Ensure result is CoinAnalysisResult
            if not isinstance(result, CoinAnalysisResult):
                symbol = list(coin_data.keys())[i]
                logger.warning(f"Invalid analysis result for {symbol}")
                continue
            
            if result.score >= min_score:
                recommendation = self._create_recommendation(result, coin_data[result.symbol])
                recommendations.append(recommendation)
        
        # Sort by score (highest first) and limit results
        recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        recommendations = recommendations[:limit]
        
        # Add rankings
        for i, rec in enumerate(recommendations):
            rec.rank = i + 1
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    async def _analyze_coin(self, symbol: str, price_data: Dict) -> CoinAnalysisResult:
        """
        Analyze a single coin using all available analyzers.
        
        Args:
            symbol: Coin symbol
            price_data: Market data for the coin
            
        Returns:
            CoinAnalysisResult with combined analysis
        """
        # Run all analyzers concurrently
        analyzer_tasks = []
        for analyzer in self.analyzers:
            task = asyncio.create_task(analyzer.analyze(symbol, price_data))
            analyzer_tasks.append(task)
        
        # Wait for all analyzers to complete
        analyzer_results = await asyncio.gather(*analyzer_tasks, return_exceptions=True)
        
        # Combine results with weighted scoring
        total_score = 0.0
        total_weight = 0.0
        combined_metadata = {}
        
        for i, (analyzer, result) in enumerate(zip(self.analyzers, analyzer_results)):
            if isinstance(result, Exception):
                logger.error(f"Analyzer {analyzer.name} failed for {symbol}: {result}")
                continue
            
            # Ensure result is a dict with score
            if not isinstance(result, dict) or 'score' not in result:
                logger.warning(f"Analyzer {analyzer.name} returned invalid result for {symbol}")
                continue
            
            score = result['score']
            weight = analyzer.weight
            
            total_score += score * weight
            total_weight += weight
            
            # Store individual analyzer results
            combined_metadata[analyzer.name] = result
        
        # Calculate final weighted score
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.0
        
        # Extract individual scores for detailed reporting
        technical_score = combined_metadata.get('technical', {}).get('score', 0.0)
        volume_score = combined_metadata.get('volume', {}).get('score', 0.0)
        volatility_score = combined_metadata.get('volatility', {}).get('score', 0.0)
        risk_score = combined_metadata.get('risk', {}).get('score', 0.0)
        
        return CoinAnalysisResult(
            symbol=symbol,
            score=final_score,
            technical_score=technical_score,
            volume_score=volume_score,
            volatility_score=volatility_score,
            risk_score=risk_score,
            metadata=combined_metadata,
            timestamp=time.time()
        )
    
    def _create_recommendation(
        self, 
        analysis: CoinAnalysisResult, 
        market_data: Dict
    ) -> CoinRecommendation:
        """
        Create a recommendation object from analysis result and market data.
        
        Args:
            analysis: Analysis result
            market_data: Market data for the coin
            
        Returns:
            CoinRecommendation object
        """
        # Determine strength based on score
        if analysis.score >= 70:
            strength = AnalysisStrength.STRONG
        elif analysis.score >= 50:
            strength = AnalysisStrength.MODERATE
        else:
            strength = AnalysisStrength.WEAK
        
        return CoinRecommendation(
            symbol=analysis.symbol,
            rank=0,  # Will be set later
            overall_score=analysis.score,
            technical_score=analysis.technical_score,
            volume_score=analysis.volume_score,
            volatility_score=analysis.volatility_score,
            risk_score=analysis.risk_score,
            strength=strength,
            current_price=market_data.get('current_price', 0.0),
            price_change_24h=market_data.get('price_change_24h', 0.0),
            volume_24h=market_data.get('volume_24h', 0.0),
            market_cap=market_data.get('market_cap'),
            analysis_details=analysis.metadata,
            timestamp=analysis.timestamp
        )
    
    async def analyze_single_coin(
        self, 
        symbol: str, 
        price_data: Dict
    ) -> CoinAnalysisResult:
        """
        Analyze a single coin and return detailed results.
        
        Args:
            symbol: Coin symbol
            price_data: Market data for the coin
            
        Returns:
            Detailed analysis result
        """
        return await self._analyze_coin(symbol, price_data)
    
    def add_analyzer(self, analyzer: CoinAnalyzer):
        """Add a new analyzer to the recommendation engine."""
        self.analyzers.append(analyzer)
        logger.info(f"Added analyzer: {analyzer.name}")
    
    def remove_analyzer(self, analyzer_name: str):
        """Remove an analyzer by name."""
        original_count = len(self.analyzers)
        self.analyzers = [a for a in self.analyzers if a.name != analyzer_name]
        
        if len(self.analyzers) < original_count:
            logger.info(f"Removed analyzer: {analyzer_name}")
        else:
            logger.warning(f"Analyzer not found: {analyzer_name}")
    
    def get_analyzer_info(self) -> List[Dict]:
        """Get information about all configured analyzers."""
        return [
            {
                'name': analyzer.name,
                'weight': analyzer.weight,
                'class': analyzer.__class__.__name__
            }
            for analyzer in self.analyzers
        ]

class RecommendationCache:
    """Simple cache for recommendation results."""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self.ttl_seconds = ttl_seconds
        self._cache = {}
    
    def get(self, key: str) -> Optional[List[CoinRecommendation]]:
        """Get cached recommendations if still valid."""
        if key not in self._cache:
            return None
        
        data, timestamp = self._cache[key]
        
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            return None
        
        return data
    
    def set(self, key: str, recommendations: List[CoinRecommendation]):
        """Cache recommendations with timestamp."""
        self._cache[key] = (recommendations, time.time())
    
    def clear(self):
        """Clear all cached data."""
        self._cache.clear()
    
    def get_cache_info(self) -> Dict:
        """Get cache statistics."""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for key, (data, timestamp) in self._cache.items():
            if current_time - timestamp > self.ttl_seconds:
                expired_entries += 1
            else:
                valid_entries += 1
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'ttl_seconds': self.ttl_seconds
        }

# Legacy compatibility - keep existing classes for backward compatibility
@dataclass
class CoinScore:
    """Legacy data class for coin analysis results."""
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
            'score': self.score,
            'volume_score': self.volume_score,
            'volatility_score': self.volatility_score,
            'technical_score': self.technical_score,
            'risk_score': self.risk_score,
            'metadata': self.metadata,
            'confidence': self.confidence
        }

class LegacyCoinRecommender:
    """Legacy recommender for backward compatibility."""
    
    def __init__(self):
        self.modern_recommender = CoinRecommender()
    
    async def get_recommendations(self, limit: int = 50) -> List[CoinScore]:
        """Get recommendations in legacy format."""
        # Use mock data for compatibility
        mock_data = self._generate_mock_data()
        recommendations = await self.modern_recommender.get_recommendations(mock_data, limit)
        
        # Convert to legacy format
        legacy_results = []
        for rec in recommendations:
            legacy_score = CoinScore(
                symbol=rec.symbol,
                score=rec.overall_score,
                volume_score=rec.volume_score,
                volatility_score=rec.volatility_score,
                technical_score=rec.technical_score,
                risk_score=rec.risk_score,
                metadata=rec.analysis_details,
                confidence=rec.overall_score / 100.0
            )
            legacy_results.append(legacy_score)
        
        return legacy_results
    
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
