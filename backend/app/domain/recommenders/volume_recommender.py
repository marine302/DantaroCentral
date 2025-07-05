"""
Volume-based Scalping Recommendation System for Dantaro Central

이 모듈은 거래량 기반 단타 전략을 위한 추천 엔진을 제공합니다.
전체 코인을 대상으로 거래량 상위 코인을 선별하고 변동성과 유동성을 기준으로
단타 거래에 적합한 코인을 추천합니다.
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from app.domain.analyzers.volume_based_analyzer import HighVolumeScalpingAnalyzer, VolumeBasedRecommendation

logger = logging.getLogger(__name__)

@dataclass
class ScalpingRecommendation:
    """단타 거래용 코인 추천 결과"""
    symbol: str
    rank: int
    score: float
    volume_24h: float
    volume_rank: int
    volatility_score: float
    liquidity_score: float
    current_price: float
    price_change_24h: float
    is_suitable_for_scalping: bool
    recommendation_strength: str
    timestamp: float
    metadata: Dict[str, Any]


class VolumeBasedRecommender:
    """
    거래량 기반 단타 추천 엔진
    
    전체 코인 중 거래량 상위 코인을 선별하고 변동성과 유동성을 분석하여
    단타 거래에 적합한 코인을 추천합니다.
    """
    
    def __init__(self):
        """추천 엔진 초기화"""
        self.analyzer = HighVolumeScalpingAnalyzer()
        self.last_analysis_time = None
        self.last_recommendations = []
        self.analysis_count = 0
    
    async def get_recommendations(self, market_data: Dict[str, Dict], top_n: int = 50) -> List[Dict]:
        """
        거래량 기반 단타 거래 추천 코인 목록 반환
        
        Args:
            market_data: 전체 코인의 시장 데이터
            top_n: 반환할 추천 코인 수
            
        Returns:
            추천 코인 목록 (Dict 형태)
        """
        start_time = time.time()
        logger.info(f"단타 거래용 코인 추천 분석 시작 (대상: {len(market_data)}개 코인)")
        
        try:
            # 거래량 기반 분석 실행
            recommendations = await self.analyzer.analyze_all_coins(market_data)
            
            # 필요하다면 추천 수 제한
            recommendations = recommendations[:top_n]
            
            # 응답 형식으로 변환
            result = self._format_recommendations(recommendations)
            
            # 분석 정보 업데이트
            self.last_analysis_time = time.time()
            self.last_recommendations = [rec["symbol"] for rec in result[:10]]
            self.analysis_count += 1
            
            process_time = time.time() - start_time
            logger.info(f"단타 거래용 코인 추천 완료: {len(result)}개 코인 (처리 시간: {process_time:.2f}초)")
            
            return result
            
        except Exception as e:
            logger.error(f"단타 거래 추천 분석 실패: {str(e)}", exc_info=True)
            return []
    
    def _format_recommendations(self, recommendations: List[VolumeBasedRecommendation]) -> List[Dict]:
        """추천 결과를 API 응답 형식으로 변환"""
        result = []
        
        for i, rec in enumerate(recommendations):
            # 추천 강도 계산
            strength = self._calculate_recommendation_strength(rec)
            
            # 종합 점수 계산
            overall_score = self._calculate_overall_score(rec)
            
            # 볼륨 점수 계산 (역순위 기반)
            volume_score = 100 * (1 / rec.volume_rank if rec.volume_rank > 0 else 0) / 100
            
            # API 응답 형식으로 변환 (schema에 맞게 정확히 구성)
            formatted_rec = {
                "symbol": rec.symbol,
                "rank": i + 1,
                "overall_score": overall_score,
                "strength": strength,
                "component_scores": {
                    "volume": volume_score,
                    "volatility": rec.volatility_score / 100,
                    "liquidity": rec.liquidity_score / 100,
                    "technical": 0.0,  # 기술적 지표는 사용하지 않음
                    "risk": 1.0 - (rec.volatility_score / 100)  # 변동성을 리스크 점수로 변환
                },
                "current_price": rec.price,
                "price_change_24h": rec.price_change_24h,
                "volume_24h": rec.volume_24h,
                "analysis_details": {
                    "volume_rank": rec.volume_rank,
                    "volume_change_percent": rec.volume_change_percent,
                    "is_suitable_for_scalping": rec.is_suitable_for_scalping,
                    "avg_trade_size": rec.avg_trade_size,
                    "scalping_score": overall_score * 100,
                    "analysis_method": "volume_based",
                    "analysis_time": datetime.now().isoformat()
                }
            }
            
            result.append(formatted_rec)
        
        return result
    
    def _calculate_overall_score(self, rec: VolumeBasedRecommendation) -> float:
        """종합 점수 계산"""
        # 거래량, 변동성, 유동성 점수를 종합
        volume_weight = 0.6
        volatility_weight = 0.3
        liquidity_weight = 0.1
        
        volume_score = 100 * (1 / rec.volume_rank if rec.volume_rank > 0 else 0)
        
        # 점수 범위 조정 (0-100 -> 0-1)
        normalized_volume = volume_score / 100
        normalized_volatility = rec.volatility_score / 100
        normalized_liquidity = rec.liquidity_score / 100
        
        # 가중 평균 계산
        overall = (
            volume_weight * normalized_volume +
            volatility_weight * normalized_volatility +
            liquidity_weight * normalized_liquidity
        )
        
        return overall
    
    def _calculate_recommendation_strength(self, rec: VolumeBasedRecommendation) -> str:
        """추천 강도 계산"""
        # 단타 적합성 여부와 점수를 기반으로 추천 강도 결정
        if not rec.is_suitable_for_scalping:
            return "NOT_RECOMMENDED"
        
        # 거래량, 변동성 점수 조합으로 강도 결정
        overall_score = self._calculate_overall_score(rec)
        
        if overall_score >= 0.8:
            return "STRONG_BUY"
        elif overall_score >= 0.6:
            return "BUY"
        elif overall_score >= 0.4:
            return "NEUTRAL"
        elif overall_score >= 0.2:
            return "WEAK"
        else:
            return "NOT_RECOMMENDED"
    
    def get_stats(self) -> Dict[str, Any]:
        """분석 통계 정보 반환"""
        analyzer_stats = self.analyzer.get_stats()
        
        return {
            "last_analysis_time": datetime.fromtimestamp(self.last_analysis_time).strftime("%Y-%m-%d %H:%M:%S") if self.last_analysis_time else None,
            "analysis_count": self.analysis_count,
            "top_recommendations": self.last_recommendations,
            "analyzer_settings": analyzer_stats
        }
