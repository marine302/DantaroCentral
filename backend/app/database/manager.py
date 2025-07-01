"""
Database operations for analysis worker.
Handles saving analysis results to database.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.database import (
    CoinRecommendation,
    SupportLevel,
    MarketStatus,
    AnalysisJob,
    CacheMetadata
)


class DatabaseManager:
    """데이터베이스 저장 관리자."""
    
    def __init__(self):
        pass
    
    def get_db_session(self) -> Session:
        """데이터베이스 세션 가져오기."""
        return SessionLocal()
    
    def save_coin_recommendations(self, recommendations: List[Dict]) -> bool:
        """코인 추천 결과를 데이터베이스에 저장."""
        try:
            with self.get_db_session() as db:
                # 기존 추천 결과 삭제 (최신 데이터만 유지)
                db.query(CoinRecommendation).delete()
                
                # 새 추천 결과 저장
                for rec in recommendations:
                    db_rec = CoinRecommendation(
                        symbol=rec['symbol'],
                        total_score=Decimal(str(rec['total_score'])),
                        technical_score=Decimal(str(rec['technical_score'])),
                        volume_score=Decimal(str(rec['volume_score'])),
                        volatility_score=Decimal(str(rec['volatility_score'])),
                        risk_score=Decimal(str(rec['risk_score'])),
                        recommendation_strength=rec['recommendation_strength'],
                        current_price=Decimal(str(rec['current_price'])) if rec.get('current_price') else None,
                        price_change_24h=Decimal(str(rec['price_change_24h'])) if rec.get('price_change_24h') else None,
                        volume_24h=Decimal(str(rec['volume_24h'])) if rec.get('volume_24h') else None,
                        market_cap=Decimal(str(rec['market_cap'])) if rec.get('market_cap') else None,
                        analysis_details=rec.get('analysis_details', {}),
                    )
                    db.add(db_rec)
                
                db.commit()
                return True
                
        except Exception as e:
            print(f"Error saving coin recommendations: {e}")
            return False
    
    def save_support_levels(self, symbol: str, support_data: Dict) -> bool:
        """지지/저항선을 데이터베이스에 저장."""
        try:
            with self.get_db_session() as db:
                # 해당 심볼의 기존 데이터 삭제
                db.query(SupportLevel).filter(SupportLevel.symbol == symbol).delete()
                
                # 새 데이터 저장
                db_support = SupportLevel(
                    symbol=symbol,
                    aggressive_support=Decimal(str(support_data['aggressive_support'])) if support_data.get('aggressive_support') else None,
                    moderate_support=Decimal(str(support_data['moderate_support'])) if support_data.get('moderate_support') else None,
                    conservative_support=Decimal(str(support_data['conservative_support'])) if support_data.get('conservative_support') else None,
                    aggressive_resistance=Decimal(str(support_data['aggressive_resistance'])) if support_data.get('aggressive_resistance') else None,
                    moderate_resistance=Decimal(str(support_data['moderate_resistance'])) if support_data.get('moderate_resistance') else None,
                    conservative_resistance=Decimal(str(support_data['conservative_resistance'])) if support_data.get('conservative_resistance') else None,
                    calculation_method=support_data.get('calculation_method'),
                    data_points_count=support_data.get('data_points_count'),
                )
                db.add(db_support)
                db.commit()
                return True
                
        except Exception as e:
            print(f"Error saving support levels for {symbol}: {e}")
            return False
    
    def save_market_status(self, market_data: Dict) -> bool:
        """시장 상태를 데이터베이스에 저장."""
        try:
            with self.get_db_session() as db:
                # 기존 시장 상태 삭제 (최신 데이터만 유지)
                db.query(MarketStatus).delete()
                
                # 새 시장 상태 저장
                db_market = MarketStatus(
                    market_trend=market_data['market_trend'],
                    market_sentiment=market_data['market_sentiment'],
                    overall_score=Decimal(str(market_data['overall_score'])),
                    active_coins_count=market_data.get('active_coins_count'),
                    total_market_cap=Decimal(str(market_data['total_market_cap'])) if market_data.get('total_market_cap') else None,
                    total_volume_24h=Decimal(str(market_data['total_volume_24h'])) if market_data.get('total_volume_24h') else None,
                    analysis_summary=market_data.get('analysis_summary', {}),
                )
                db.add(db_market)
                db.commit()
                return True
                
        except Exception as e:
            print(f"Error saving market status: {e}")
            return False
    
    def save_analysis_job(self, job_type: str, job_status: str, **kwargs) -> Optional[int]:
        """분석 작업 기록을 저장."""
        try:
            with self.get_db_session() as db:
                job = AnalysisJob(
                    job_type=job_type,
                    job_status=job_status,
                    started_at=kwargs.get('started_at'),
                    completed_at=kwargs.get('completed_at'),
                    execution_time_seconds=kwargs.get('execution_time_seconds'),
                    processed_items_count=kwargs.get('processed_items_count'),
                    error_message=kwargs.get('error_message'),
                    worker_id=kwargs.get('worker_id'),
                    job_metadata=kwargs.get('job_metadata', {}),
                )
                db.add(job)
                db.commit()
                db.refresh(job)
                return job.id
                
        except Exception as e:
            print(f"Error saving analysis job: {e}")
            return None
    
    def update_cache_metadata(self, cache_key: str, cache_type: str, **kwargs) -> bool:
        """캐시 메타데이터 업데이트."""
        try:
            with self.get_db_session() as db:
                # 기존 메타데이터 확인
                metadata = db.query(CacheMetadata).filter(CacheMetadata.cache_key == cache_key).first()
                
                if metadata:
                    # 업데이트
                    metadata.last_updated = kwargs.get('last_updated', datetime.now())
                    metadata.expires_at = kwargs.get('expires_at')
                    metadata.is_valid = kwargs.get('is_valid', 'true')
                    metadata.error_count = kwargs.get('error_count', 0)
                    metadata.last_error = kwargs.get('last_error')
                else:
                    # 새로 생성
                    metadata = CacheMetadata(
                        cache_key=cache_key,
                        cache_type=cache_type,
                        data_source=kwargs.get('data_source'),
                        last_updated=kwargs.get('last_updated', datetime.now()),
                        expires_at=kwargs.get('expires_at'),
                        is_valid=kwargs.get('is_valid', 'true'),
                        error_count=kwargs.get('error_count', 0),
                        last_error=kwargs.get('last_error'),
                    )
                    db.add(metadata)
                
                db.commit()
                return True
                
        except Exception as e:
            print(f"Error updating cache metadata: {e}")
            return False
    
    def get_latest_recommendations(self, limit: int = 50) -> List[Dict]:
        """최신 추천 결과 조회."""
        try:
            with self.get_db_session() as db:
                recommendations = db.query(CoinRecommendation)\
                    .order_by(CoinRecommendation.total_score.desc())\
                    .limit(limit).all()
                
                return [
                    {
                        'symbol': rec.symbol,
                        'total_score': float(rec.total_score),
                        'technical_score': float(rec.technical_score),
                        'volume_score': float(rec.volume_score),
                        'volatility_score': float(rec.volatility_score),
                        'risk_score': float(rec.risk_score),
                        'recommendation_strength': rec.recommendation_strength,
                        'current_price': float(rec.current_price) if rec.current_price else None,
                        'price_change_24h': float(rec.price_change_24h) if rec.price_change_24h else None,
                        'volume_24h': float(rec.volume_24h) if rec.volume_24h else None,
                        'market_cap': float(rec.market_cap) if rec.market_cap else None,
                        'analysis_details': rec.analysis_details,
                        'updated_at': rec.updated_at.isoformat() if rec.updated_at else None,
                    }
                    for rec in recommendations
                ]
                
        except Exception as e:
            print(f"Error getting latest recommendations: {e}")
            return []
    
    def get_support_levels(self, symbol: str) -> Optional[Dict]:
        """지지/저항선 조회."""
        try:
            with self.get_db_session() as db:
                support = db.query(SupportLevel)\
                    .filter(SupportLevel.symbol == symbol)\
                    .order_by(SupportLevel.updated_at.desc())\
                    .first()
                
                if support:
                    return {
                        'symbol': support.symbol,
                        'aggressive_support': float(support.aggressive_support) if support.aggressive_support else None,
                        'moderate_support': float(support.moderate_support) if support.moderate_support else None,
                        'conservative_support': float(support.conservative_support) if support.conservative_support else None,
                        'aggressive_resistance': float(support.aggressive_resistance) if support.aggressive_resistance else None,
                        'moderate_resistance': float(support.moderate_resistance) if support.moderate_resistance else None,
                        'conservative_resistance': float(support.conservative_resistance) if support.conservative_resistance else None,
                        'calculation_method': support.calculation_method,
                        'data_points_count': support.data_points_count,
                        'updated_at': support.updated_at.isoformat() if support.updated_at else None,
                    }
                return None
                
        except Exception as e:
            print(f"Error getting support levels for {symbol}: {e}")
            return None
    
    def get_market_status(self) -> Optional[Dict]:
        """최신 시장 상태 조회."""
        try:
            with self.get_db_session() as db:
                market = db.query(MarketStatus)\
                    .order_by(MarketStatus.updated_at.desc())\
                    .first()
                
                if market:
                    return {
                        'market_trend': market.market_trend,
                        'market_sentiment': market.market_sentiment,
                        'overall_score': float(market.overall_score),
                        'active_coins_count': market.active_coins_count,
                        'total_market_cap': float(market.total_market_cap) if market.total_market_cap else None,
                        'total_volume_24h': float(market.total_volume_24h) if market.total_volume_24h else None,
                        'analysis_summary': market.analysis_summary,
                        'updated_at': market.updated_at.isoformat() if market.updated_at else None,
                    }
                return None
                
        except Exception as e:
            print(f"Error getting market status: {e}")
            return None


# 글로벌 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()
