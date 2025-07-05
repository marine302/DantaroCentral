"""
Base classes and common types for coin analysis.

This module contains the abstract base classes and data types
used by all analyzer components.
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
