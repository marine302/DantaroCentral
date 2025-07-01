"""
Lightweight Pydantic schemas for the new market data API.
These schemas are optimized for serving pre-computed data.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class LightCoinRecommendation(BaseModel):
    """Single coin recommendation from database/cache."""
    symbol: str
    total_score: float = Field(..., ge=0, le=1, description="Overall recommendation score")
    technical_score: float = Field(..., ge=0, le=1, description="Technical analysis score")
    volume_score: float = Field(..., ge=0, le=1, description="Volume analysis score")
    volatility_score: float = Field(..., ge=0, le=1, description="Volatility analysis score")
    risk_score: float = Field(..., ge=0, le=1, description="Risk assessment score")
    recommendation_strength: str = Field(..., description="Recommendation strength")
    current_price: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    analysis_details: Dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[str] = None


class CoinRecommendationResponse(BaseModel):
    """Response model for coin recommendations endpoint."""
    success: bool = True
    recommendations: List[LightCoinRecommendation]
    total_analyzed: int = Field(..., description="Total number of recommendations returned")
    cache_timestamp: datetime
    generated_at: float = Field(..., description="Timestamp when data was generated")
    data_source: str = Field(..., description="Source of data (cache/database)")
    message: Optional[str] = None


class LightSupportLevel(BaseModel):
    """Support/resistance levels from database/cache."""
    symbol: str
    aggressive_support: Optional[float] = None
    moderate_support: Optional[float] = None
    conservative_support: Optional[float] = None
    aggressive_resistance: Optional[float] = None
    moderate_resistance: Optional[float] = None
    conservative_resistance: Optional[float] = None
    calculation_method: Optional[str] = None
    data_points_count: Optional[int] = None
    updated_at: Optional[str] = None


class SupportLevelResponse(BaseModel):
    """Response model for support levels endpoint."""
    success: bool = True
    symbol: str
    support_levels: LightSupportLevel
    cache_timestamp: datetime
    data_source: str = Field(..., description="Source of data (cache/database)")


class LightMarketStatus(BaseModel):
    """Market status from database/cache."""
    market_trend: str = Field(..., description="Overall market trend")
    market_sentiment: str = Field(..., description="Market sentiment")
    overall_score: float = Field(..., ge=0, le=1, description="Overall market score")
    active_coins_count: Optional[int] = None
    total_market_cap: Optional[float] = None
    total_volume_24h: Optional[float] = None
    analysis_summary: Dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[str] = None


class MarketStatusResponse(BaseModel):
    """Response model for market status endpoint."""
    success: bool = True
    status: str = Field(..., description="Overall API status")
    total_symbols: int = Field(..., description="Total symbols analyzed")
    system_health: Dict[str, str] = Field(default_factory=dict)
    market_status: LightMarketStatus
    cache_timestamp: datetime
    data_source: str = Field(..., description="Source of data (cache/database)")


# Bundle request schemas
class BundleRequest(BaseModel):
    """Request model for bundle endpoint."""
    include_recommendations: bool = Field(default=False)
    recommendations_count: int = Field(default=50, ge=1, le=100)
    
    include_support_levels: bool = Field(default=False)
    symbols: Optional[List[str]] = Field(default=None)
    
    include_market_status: bool = Field(default=False)


class BundleResponse(BaseModel):
    """Response model for bundle endpoint."""
    success: bool = True
    data: Dict[str, Any] = Field(..., description="Bundled data")
    cache_timestamp: datetime
    data_source: str = Field(..., description="Source of data (cache/database)")
    message: Optional[str] = None
