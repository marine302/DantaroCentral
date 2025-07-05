"""
Coin analysis strategies for recommendation engine.

This is the main analyzer module that imports all analyzer components
from the modularized components package.
"""

# Import all analyzer components from the components package
from .components.base import CoinAnalyzer, CoinAnalysisResult, AnalysisStrength
from .components.technical import TechnicalAnalyzer
from .components.volume import VolumeAnalyzer
from .components.volatility import VolatilityAnalyzer
from .components.risk import RiskAnalyzer

# Re-export everything for backward compatibility
__all__ = [
    "CoinAnalyzer",
    "CoinAnalysisResult",
    "AnalysisStrength", 
    "TechnicalAnalyzer",
    "VolumeAnalyzer",
    "VolatilityAnalyzer",
    "RiskAnalyzer"
]
