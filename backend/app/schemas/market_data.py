"""
Pydantic schemas for market data API responses.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CoinRecommendation(BaseModel):
    """Single coin recommendation with analysis scores."""
    symbol: str
    total_score: float = Field(..., ge=0, le=1, description="Overall recommendation score")
    component_scores: Dict[str, float] = Field(
        ..., 
        description="Individual analysis component scores"
    )
    recommendation_strength: str = Field(
        ..., 
        description="Recommendation strength (STRONG_BUY, BUY, HOLD, WEAK_SELL, SELL)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class CoinRecommendationResponse(BaseModel):
    """Response model for coin recommendations endpoint."""
    recommendations: List[CoinRecommendation]
    total_analyzed: int = Field(..., description="Total number of coins analyzed")
    cache_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SupportLevelDetail(BaseModel):
    """Details for a single support level calculation."""
    price: float = Field(..., description="Calculated support price")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in the calculation")
    calculation_method: str = Field(..., description="Method used for calculation")
    lookback_days: int = Field(..., description="Number of days of data used")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SupportLevelResponse(BaseModel):
    """Response model for support levels endpoint."""
    symbol: str
    support_levels: Dict[str, SupportLevelDetail] = Field(
        ..., 
        description="Support levels by type (aggressive, moderate, conservative)"
    )
    calculation_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemHealth(BaseModel):
    """System health status."""
    database: str = Field(..., description="Database connection status")
    cache: str = Field(..., description="Cache service status")
    exchanges: Dict[str, str] = Field(default_factory=dict, description="Exchange API statuses")
    analysis_engine: str = Field(..., description="Analysis engine status")


class MarketStatusResponse(BaseModel):
    """Response model for market status endpoint."""
    status: str = Field(..., description="Overall market status")
    total_symbols: int = Field(..., description="Total number of symbols available")
    last_update: Optional[datetime] = None
    system_health: SystemHealth
    market_indicators: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Bundle request schemas
class RecommendationsParams(BaseModel):
    """Parameters for recommendations in bundle request."""
    top_n: int = Field(default=50, ge=1, le=100)
    force_refresh: bool = Field(default=False)


class SupportLevelParams(BaseModel):
    """Parameters for support levels in bundle request."""
    force_refresh: bool = Field(default=False)


class BundleRequest(BaseModel):
    """Request model for bundle endpoint."""
    include_recommendations: bool = Field(default=False)
    recommendations_params: Optional[RecommendationsParams] = None
    
    support_level_symbols: Optional[List[str]] = Field(default=None)
    support_level_params: Optional[SupportLevelParams] = None
    
    include_market_status: bool = Field(default=False)


class BundleResponse(BaseModel):
    """Response model for bundle endpoint."""
    results: Dict[str, Any] = Field(..., description="Successful results by request type")
    errors: Optional[Dict[str, Any]] = Field(default=None, description="Errors by request type")
    metadata: Dict[str, Any] = Field(default_factory=dict)
