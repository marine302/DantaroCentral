"""
Database models for Dantaro Central.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class CoinRecommendation(Base):
    """코인 추천 분석 결과를 저장하는 테이블."""
    
    __tablename__ = "coin_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # 스코어 정보
    total_score = Column(Numeric(5, 4), nullable=False, index=True)
    technical_score = Column(Numeric(5, 4), nullable=False)
    volume_score = Column(Numeric(5, 4), nullable=False)
    volatility_score = Column(Numeric(5, 4), nullable=False)
    risk_score = Column(Numeric(5, 4), nullable=False)
    
    # 추천 강도
    recommendation_strength = Column(String(20), nullable=False)
    
    # 가격 정보
    current_price = Column(Numeric(20, 8))
    price_change_24h = Column(Numeric(10, 8))
    volume_24h = Column(Numeric(20, 2))
    market_cap = Column(Numeric(20, 2))
    
    # 상세 분석 정보 (JSON)
    analysis_details = Column(JSON)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<CoinRecommendation(symbol='{self.symbol}', score={self.total_score})>"


class SupportLevel(Base):
    """지지/저항선 분석 결과를 저장하는 테이블."""
    
    __tablename__ = "support_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # 지지선
    aggressive_support = Column(Numeric(20, 8))
    moderate_support = Column(Numeric(20, 8))
    conservative_support = Column(Numeric(20, 8))
    
    # 저항선
    aggressive_resistance = Column(Numeric(20, 8))
    moderate_resistance = Column(Numeric(20, 8))
    conservative_resistance = Column(Numeric(20, 8))
    
    # 계산 정보
    calculation_method = Column(String(50))
    data_points_count = Column(Integer)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SupportLevel(symbol='{self.symbol}', support={self.moderate_support})>"


class MarketStatus(Base):
    """전체 시장 상태 분석 결과를 저장하는 테이블."""
    
    __tablename__ = "market_status"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 시장 상태
    market_trend = Column(String(20), nullable=False)  # bullish, bearish, neutral
    market_sentiment = Column(String(20), nullable=False)  # positive, negative, neutral
    overall_score = Column(Numeric(5, 4), nullable=False)
    
    # 상세 정보
    active_coins_count = Column(Integer)
    total_market_cap = Column(Numeric(30, 2))
    total_volume_24h = Column(Numeric(30, 2))
    
    # 분석 결과 (JSON)
    analysis_summary = Column(JSON)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MarketStatus(trend='{self.market_trend}', score={self.overall_score})>"


class AnalysisJob(Base):
    """분석 작업 실행 상태를 추적하는 테이블."""
    
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 작업 정보
    job_type = Column(String(50), nullable=False, index=True)  # recommendations, support_levels, market_status
    job_status = Column(String(20), nullable=False, index=True)  # pending, running, completed, failed
    
    # 실행 정보
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    execution_time_seconds = Column(Numeric(10, 3))
    
    # 결과 정보
    processed_items_count = Column(Integer)
    error_message = Column(Text)
    
    # 메타데이터
    worker_id = Column(String(100))
    job_metadata = Column(JSON)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AnalysisJob(type='{self.job_type}', status='{self.job_status}')>"


class CacheMetadata(Base):
    """캐시 메타데이터를 관리하는 테이블."""
    
    __tablename__ = "cache_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 캐시 정보
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    cache_type = Column(String(50), nullable=False, index=True)  # redis, database
    
    # 데이터 정보
    data_source = Column(String(100))  # 데이터 소스 (upbit, binance, etc.)
    last_updated = Column(DateTime(timezone=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    
    # 상태 정보
    is_valid = Column(String(10), default="true")  # true, false, stale
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CacheMetadata(key='{self.cache_key}', type='{self.cache_type}')>"
