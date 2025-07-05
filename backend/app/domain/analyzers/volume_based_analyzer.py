#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dantaro Volume Analyzer - 거래량 기반 코인 선별 시스템

이 모듈은 전체 코인 중 거래량 상위 코인을 선별하고
단타 거래에 적합한 변동성 지표를 분석하는 기능을 제공합니다.
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import heapq

logger = logging.getLogger(__name__)

@dataclass
class VolumeBasedRecommendation:
    """거래량 기반 코인 추천 결과"""
    symbol: str
    volume_rank: int  # 거래량 순위
    volume_24h: float  # 24시간 거래량
    volume_change_percent: float  # 거래량 변화율(%)
    volatility_score: float  # 변동성 점수
    liquidity_score: float  # 유동성 점수
    price: float  # 현재 가격
    price_change_24h: float  # 24시간 가격 변화율(%)
    avg_trade_size: float  # 평균 거래 크기
    is_suitable_for_scalping: bool  # 단타 적합성
    timestamp: float  # 분석 시간


class HighVolumeScalpingAnalyzer:
    """
    고거래량 기반 단타 매매용 코인 분석기
    전체 코인을 대상으로 거래량과 변동성을 분석하여 단타 거래에 적합한 코인을 추천
    """
    
    def __init__(self, volume_weight: float = 0.6, volatility_weight: float = 0.3, 
                 liquidity_weight: float = 0.1):
        """
        분석기 초기화
        
        Args:
            volume_weight: 거래량 가중치 (기본값 0.6)
            volatility_weight: 변동성 가중치 (기본값 0.3)
            liquidity_weight: 유동성 가중치 (기본값 0.1)
        """
        self.volume_weight = volume_weight
        self.volatility_weight = volatility_weight
        self.liquidity_weight = liquidity_weight
        
        # 거래량 필터링 기준
        self.min_volume_usd = 1_000_000  # 최소 100만 달러 거래량
        self.max_coins_to_analyze = 100  # 분석할 최대 코인 수
        self.top_recommendations = 50    # 추천할 상위 코인 수
        
        # 단타 거래 적합성 기준
        self.min_volatility_percent = 1.0  # 최소 변동성 (1시간 기준)
        self.max_volatility_percent = 10.0  # 최대 변동성 (1시간 기준)
        self.min_trades_per_minute = 5   # 분당 최소 거래 수
        
        # 추적 데이터
        self.analysis_timestamp = None
        self.analyzed_coins_count = 0
        self.last_top_coins = []
        
    async def analyze_all_coins(self, market_data: Dict[str, Dict]) -> List[VolumeBasedRecommendation]:
        """
        전체 코인 분석 및 단타 거래 적합성 평가
        
        Args:
            market_data: 모든 코인의 시장 데이터
            
        Returns:
            단타 거래에 적합한 상위 코인 목록
        """
        start_time = time.time()
        logger.info(f"전체 {len(market_data)} 코인에 대한 거래량 기반 분석 시작")
        
        # 1단계: 거래량 기준으로 1차 필터링
        volume_filtered_coins = await self._filter_by_volume(market_data)
        logger.info(f"거래량 기준 필터링 후 {len(volume_filtered_coins)}개 코인 선별")
        
        # 2단계: 선별된 코인 상세 분석
        analysis_results = await self._analyze_coins(volume_filtered_coins)
        
        # 3단계: 단타 거래 적합성 점수 계산 및 정렬
        scored_coins = self._calculate_scalping_suitability(analysis_results)
        
        # 4단계: 상위 코인 선별
        top_recommendations = scored_coins[:self.top_recommendations]
        
        self.analysis_timestamp = time.time()
        self.analyzed_coins_count = len(market_data)
        self.last_top_coins = [rec.symbol for rec in top_recommendations[:10]]
        
        logger.info(f"거래량 기반 분석 완료: 상위 {len(top_recommendations)}개 코인 선별 "
                   f"(처리 시간: {time.time() - start_time:.2f}초)")
        logger.info(f"상위 10개 코인: {', '.join(self.last_top_coins)}")
        
        return top_recommendations
    
    async def _filter_by_volume(self, market_data: Dict[str, Dict]) -> List[Tuple[str, Dict]]:
        """거래량 기준으로 코인 필터링"""
        volume_heap = []
        
        for symbol, data in market_data.items():
            volume_24h = data.get('volume_24h', 0)
            
            # 최소 거래량보다 큰 코인만 선별
            if volume_24h >= self.min_volume_usd:
                # 최대 힙을 사용하여 상위 코인 추적 (음수 사용)
                heapq.heappush(volume_heap, (-volume_24h, symbol, data))
        
        # 거래량 상위 코인 추출 (최대 100개)
        top_volume_coins = []
        count = 0
        
        while volume_heap and count < self.max_coins_to_analyze:
            neg_volume, symbol, data = heapq.heappop(volume_heap)
            top_volume_coins.append((symbol, data))
            count += 1
        
        return top_volume_coins
    
    async def _analyze_coins(self, coins: List[Tuple[str, Dict]]) -> List[Dict]:
        """선별된 코인 상세 분석"""
        analysis_results = []
        
        # 각 코인 상세 분석
        for rank, (symbol, data) in enumerate(coins, 1):
            try:
                # 기본 데이터 추출
                volume_24h = data.get('volume_24h', 0)
                volume_change = data.get('volume_change_24h', 0)
                price = data.get('current_price', 0)
                price_change = data.get('price_change_24h', 0)
                
                # 변동성 계산
                high_1h = data.get('high_1h', price * 1.005)
                low_1h = data.get('low_1h', price * 0.995)
                volatility_1h = ((high_1h - low_1h) / low_1h) * 100 if low_1h > 0 else 0
                
                # 유동성 지표 계산
                trades_per_minute = data.get('trades_count_1h', 300) / 60
                avg_trade_size = volume_24h / (trades_per_minute * 1440) if trades_per_minute > 0 else 0
                
                # 단타 적합성 평가
                is_suitable = (
                    volatility_1h >= self.min_volatility_percent and
                    volatility_1h <= self.max_volatility_percent and
                    trades_per_minute >= self.min_trades_per_minute
                )
                
                # 결과 저장
                analysis_results.append({
                    'symbol': symbol,
                    'volume_rank': rank,
                    'volume_24h': volume_24h,
                    'volume_change_percent': volume_change,
                    'volatility_1h': volatility_1h,
                    'trades_per_minute': trades_per_minute,
                    'price': price,
                    'price_change_24h': price_change,
                    'avg_trade_size': avg_trade_size,
                    'is_suitable_for_scalping': is_suitable
                })
                
            except Exception as e:
                logger.warning(f"{symbol} 분석 중 오류 발생: {str(e)}")
                continue
        
        return analysis_results
    
    def _calculate_scalping_suitability(self, analysis_results: List[Dict]) -> List[VolumeBasedRecommendation]:
        """단타 거래 적합성 점수 계산 및 정렬"""
        scored_recommendations = []
        
        for result in analysis_results:
            # 기본 정보 추출
            symbol = result['symbol']
            volume_rank = result['volume_rank']
            
            # 각 지표별 점수 계산 (0-100)
            volume_score = 100 * (1 / volume_rank) if volume_rank > 0 else 0
            
            # 변동성 점수 (1-5%가 가장 높은 점수)
            volatility = result['volatility_1h']
            if volatility < 1:
                volatility_score = volatility * 50  # 0-1% 구간: 0-50점
            elif 1 <= volatility <= 5:
                volatility_score = 50 + (volatility - 1) * 12.5  # 1-5% 구간: 50-100점
            elif 5 < volatility <= 10:
                volatility_score = 100 - (volatility - 5) * 10  # 5-10% 구간: 100-50점
            else:
                volatility_score = max(0, 50 - (volatility - 10) * 5)  # 10%+ 구간: 50-0점
            
            # 유동성 점수 (거래 빈도)
            trades_per_minute = result['trades_per_minute']
            liquidity_score = min(100, trades_per_minute * 5)  # 20회/분 이상이면 만점
            
            # 종합 점수
            total_score = (
                self.volume_weight * volume_score +
                self.volatility_weight * volatility_score +
                self.liquidity_weight * liquidity_score
            )
            
            # 추천 객체 생성
            recommendation = VolumeBasedRecommendation(
                symbol=symbol,
                volume_rank=volume_rank,
                volume_24h=result['volume_24h'],
                volume_change_percent=result['volume_change_percent'],
                volatility_score=volatility_score,
                liquidity_score=liquidity_score,
                price=result['price'],
                price_change_24h=result['price_change_24h'],
                avg_trade_size=result['avg_trade_size'],
                is_suitable_for_scalping=result['is_suitable_for_scalping'],
                timestamp=time.time()
            )
            
            scored_recommendations.append((total_score, recommendation))
        
        # 점수 기준 내림차순 정렬
        scored_recommendations.sort(reverse=True)
        
        # 최종 추천 목록 반환
        return [rec for _, rec in scored_recommendations]
    
    def get_stats(self) -> Dict[str, Any]:
        """분석 통계 정보 반환"""
        return {
            'analyzed_coins_count': self.analyzed_coins_count,
            'last_analysis_time': datetime.fromtimestamp(self.analysis_timestamp).strftime('%Y-%m-%d %H:%M:%S') if self.analysis_timestamp else None,
            'top_coins': self.last_top_coins,
            'weights': {
                'volume': self.volume_weight,
                'volatility': self.volatility_weight,
                'liquidity': self.liquidity_weight
            },
            'filters': {
                'min_volume_usd': self.min_volume_usd,
                'max_coins_analyzed': self.max_coins_to_analyze,
                'top_recommendations': self.top_recommendations
            }
        }
