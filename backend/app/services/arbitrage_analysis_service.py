#!/usr/bin/env python3
"""
차익거래 분석 서비스
실시간 차익거래 기회 탐지 및 김치 프리미엄 분석 전담
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from app.services.arbitrage_analyzer import ArbitrageAnalyzer, ArbitrageOpportunity, KimchiPremium


@dataclass
class AnalysisServiceConfig:
    """분석 서비스 설정"""
    analysis_interval: int = 10  # 분석 간격 (초)
    min_spread_percentage: float = 0.5  # 최소 스프레드 (%)
    min_premium_for_alert: float = 2.0  # 최소 프리미엄 알림 기준 (%)
    max_opportunities: int = 20  # 최대 기회 저장 수
    enable_auto_analysis: bool = True  # 자동 분석 활성화


class ArbitrageAnalysisService:
    """차익거래 분석 서비스"""
    
    def __init__(self, config: AnalysisServiceConfig = None):
        self.logger = logging.getLogger(f"{__name__}.ArbitrageAnalysisService")
        
        # 설정
        self.config = config or AnalysisServiceConfig()
        
        # 차익거래 분석기
        self.analyzer = ArbitrageAnalyzer()
        self.analyzer.min_spread_percentage = self.config.min_spread_percentage
        self.analyzer.max_opportunities = self.config.max_opportunities
        
        # 상태 관리
        self.running = False
        self.last_analysis = datetime.now()
        self.analysis_task = None
        
        # 콜백 함수들
        self.opportunity_callbacks: List[Callable] = []
        self.premium_callbacks: List[Callable] = []
        
        # 결과 저장소
        self.latest_opportunities: List[ArbitrageOpportunity] = []
        self.latest_premiums: List[KimchiPremium] = []
        
        # 통계
        self.stats = {
            'start_time': None,
            'total_analyses': 0,
            'opportunities_found': 0,
            'premiums_found': 0,
            'max_spread_seen': 0.0,
            'avg_analysis_time': 0.0
        }
    
    def add_opportunity_callback(self, callback: Callable[[List[ArbitrageOpportunity]], None]):
        """차익거래 기회 발견 시 콜백 추가"""
        self.opportunity_callbacks.append(callback)
        self.logger.info("차익거래 기회 콜백 추가됨")
    
    def add_premium_callback(self, callback: Callable[[List[KimchiPremium]], None]):
        """김치 프리미엄 발견 시 콜백 추가"""
        self.premium_callbacks.append(callback)
        self.logger.info("김치 프리미엄 콜백 추가됨")
    
    def update_price_data(self, symbol: str, exchange: str, price: float, volume: float, **kwargs):
        """가격 데이터 업데이트"""
        try:
            self.analyzer.update_price_data(
                symbol=symbol,
                exchange=exchange,
                price=price,
                volume=volume,
                **kwargs
            )
            
            # 자동 분석 체크
            if self.config.enable_auto_analysis:
                self._check_auto_analysis()
                
        except Exception as e:
            self.logger.error(f"가격 데이터 업데이트 오류: {e}")
    
    def _check_auto_analysis(self):
        """자동 분석 체크"""
        now = datetime.now()
        
        if (now - self.last_analysis).total_seconds() >= self.config.analysis_interval:
            if self.running:
                asyncio.create_task(self.perform_analysis())
            self.last_analysis = now
    
    async def perform_analysis(self):
        """차익거래 분석 수행"""
        analysis_start = datetime.now()
        
        try:
            # 차익거래 기회 탐지
            opportunities = self.analyzer.find_arbitrage_opportunities()
            
            # 김치 프리미엄 계산
            premiums = self.analyzer.calculate_kimchi_premium()
            
            # 결과 저장
            self.latest_opportunities = opportunities
            self.latest_premiums = premiums
            
            # 통계 업데이트
            self.stats['total_analyses'] += 1
            if opportunities:
                self.stats['opportunities_found'] += len(opportunities)
                max_spread = max(opp.spread_percentage for opp in opportunities)
                self.stats['max_spread_seen'] = max(self.stats['max_spread_seen'], max_spread)
            
            if premiums:
                self.stats['premiums_found'] += len(premiums)
            
            # 분석 시간 통계
            analysis_time = (datetime.now() - analysis_start).total_seconds()
            if self.stats['total_analyses'] > 0:
                self.stats['avg_analysis_time'] = (
                    (self.stats['avg_analysis_time'] * (self.stats['total_analyses'] - 1) + analysis_time) / 
                    self.stats['total_analyses']
                )
            
            # 콜백 호출
            await self._notify_callbacks(opportunities, premiums)
            
        except Exception as e:
            self.logger.error(f"차익거래 분석 오류: {e}")
    
    async def _notify_callbacks(self, opportunities: List[ArbitrageOpportunity], premiums: List[KimchiPremium]):
        """콜백 함수들 호출"""
        try:
            # 차익거래 기회 콜백
            if opportunities and self.opportunity_callbacks:
                significant_opportunities = [
                    opp for opp in opportunities 
                    if opp.spread_percentage >= self.config.min_spread_percentage
                ]
                
                if significant_opportunities:
                    for callback in self.opportunity_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(significant_opportunities)
                            else:
                                callback(significant_opportunities)
                        except Exception as e:
                            self.logger.error(f"차익거래 콜백 오류: {e}")
            
            # 김치 프리미엄 콜백
            if premiums and self.premium_callbacks:
                significant_premiums = [
                    premium for premium in premiums 
                    if abs(premium.premium_percentage) >= self.config.min_premium_for_alert
                ]
                
                if significant_premiums:
                    for callback in self.premium_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(significant_premiums)
                            else:
                                callback(significant_premiums)
                        except Exception as e:
                            self.logger.error(f"김치 프리미엄 콜백 오류: {e}")
                            
        except Exception as e:
            self.logger.error(f"콜백 알림 오류: {e}")
    
    async def start(self):
        """분석 서비스 시작"""
        self.logger.info("차익거래 분석 서비스 시작...")
        
        try:
            # 분석기 시작
            await self.analyzer.start()
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            self.logger.info("✅ 차익거래 분석 서비스 시작 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 분석 서비스 시작 실패: {e}")
            raise
    
    async def stop(self):
        """분석 서비스 중지"""
        self.logger.info("차익거래 분석 서비스 중지...")
        
        try:
            self.running = False
            
            # 분석기 중지
            await self.analyzer.stop()
            
            # 실행 통계 출력
            if self.stats['start_time']:
                runtime = datetime.now() - self.stats['start_time']
                self.logger.info(f"📊 실행 시간: {runtime}")
                self.logger.info(f"📈 총 분석 횟수: {self.stats['total_analyses']:,}회")
                self.logger.info(f"🎯 발견한 기회: {self.stats['opportunities_found']:,}개")
                self.logger.info(f"🍡 발견한 프리미엄: {self.stats['premiums_found']:,}개")
                self.logger.info(f"📊 최대 스프레드: {self.stats['max_spread_seen']:.2f}%")
                self.logger.info(f"⏱️ 평균 분석 시간: {self.stats['avg_analysis_time']:.3f}초")
            
            self.logger.info("✅ 차익거래 분석 서비스 중지 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 분석 서비스 중지 중 오류: {e}")
    
    def get_latest_opportunities(self, limit: int = None) -> List[ArbitrageOpportunity]:
        """최신 차익거래 기회 반환"""
        if limit:
            return self.latest_opportunities[:limit]
        return self.latest_opportunities
    
    def get_latest_premiums(self, limit: int = None) -> List[KimchiPremium]:
        """최신 김치 프리미엄 반환"""
        if limit:
            return self.latest_premiums[:limit]
        return self.latest_premiums
    
    def get_stats(self) -> Dict:
        """분석 통계 반환"""
        return {
            **self.stats,
            'analyzer_stats': self.analyzer.get_stats() if self.analyzer else {}
        }
    
    def is_running(self) -> bool:
        """실행 상태 확인"""
        return self.running
    
    def get_tracked_symbols(self) -> List[str]:
        """추적 중인 심볼 반환"""
        return list(self.analyzer.price_data.keys()) if self.analyzer else []
