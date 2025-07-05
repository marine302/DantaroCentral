"""
Background task for continuous market analysis.

This module implements scheduled tasks for:
- Fetching latest market data from exchanges
- Updating support levels and recommendations
- Cleaning old data and maintaining cache

Runs every 5 minutes as configured in settings.
"""
import asyncio
import logging
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any
import json
from dataclasses import asdict

from app.core.config import settings
from app.services.market_data_service import MarketDataService
from app.services.real_market_service import RealMarketDataService
from app.services.cache_service import CacheService
from app.domain.recommenders.advanced_recommender import CoinRecommender
from app.domain.recommenders.volume_recommender import VolumeBasedRecommender
from app.domain.calculators.support_calculator import SupportLevelCalculator
from app.database.redis_cache import redis_manager

# 로거 설정
logger = structlog.get_logger(__name__)
logging.getLogger(__name__).setLevel(logging.INFO)

# 서비스 로거 설정
logging.getLogger('app.services.real_market_service').setLevel(logging.INFO)


class MarketAnalyzer:
    """
    Background task manager for continuous market analysis.
    
    This class handles periodic market data updates and analysis
    to keep the central server's recommendations fresh.
    """
    
    def __init__(self):
        self.market_service = MarketDataService()
        self.real_market_service = RealMarketDataService()
        self.cache_service = CacheService()
        # 기존 추천기 및 새로운 거래량 기반 추천기 초기화
        self.coin_recommender = CoinRecommender()
        self.volume_recommender = VolumeBasedRecommender()  # 거래량 기반 단타 추천기
        self.last_analysis: Dict[str, datetime] = {}
        self.is_running = False
        self.worker_id = "market_analyzer_main"
        self.start_time = datetime.utcnow()
    
    async def start_continuous_analysis(self):
        """Start the continuous analysis loop."""
        if self.is_running:
            logger.warning("Market analyzer already running")
            return
        
        logger.info("��� 시작: 실시간 시장 분석 루프 시작")
        
        try:
            # 확실하게 실행 상태 설정
            self.is_running = True
            
            # 초기 상태 업데이트 및 하트비트 설정
            self._update_worker_status()
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Run first analysis cycle immediately
            logger.info("🔄 즉시 첫 번째 분석 사이클 실행 시작")
            await self.run_analysis_cycle()
            logger.info("✅ 첫 번째 분석 사이클 완료, 주기적 루프 시작")
            
            # 상태 재확인
            if not self.is_running:
                logger.error("❌ 첫 번째 분석 후 is_running이 False로 변경됨. 다시 시작")
                self.is_running = True
                self._update_worker_status()
            
            # 주기적 실행 루프
            while self.is_running:
                logger.info(f"⏰ 다음 분석 사이클까지 대기 중... ({settings.market_analysis_interval}초)")
                await asyncio.sleep(settings.market_analysis_interval)
                logger.info("🔄 예약된 분석 사이클 실행 중")
                await self.run_analysis_cycle()
                
                # 분석 후 상태 업데이트
                self._update_worker_status()
        except Exception as e:
            logger.error(f"❌ 시장 분석 루프 실패: {e}", exc_info=True)
            self.is_running = False
        finally:
            # 혹시라도 루프가 종료되면 상태 업데이트
            if self.is_running:
                logger.warning("⚠️ 예상치 않게 분석 루프 종료됨")
                self.is_running = False
                self._update_worker_status()
    
    async def stop_analysis(self):
        """Stop the continuous analysis loop."""
        logger.info("Stopping market analysis")
        self.is_running = False
    
    async def run_analysis_cycle(self):
        """Run a single analysis cycle."""
        try:
            cycle_start = datetime.utcnow()
            logger.info("Starting market analysis cycle")
            
            # Step 1: Fetch latest market data
            logger.info("Step 1: Fetching market data")
            market_data = await self._fetch_market_data()
            
            if not market_data:
                logger.warning("No market data available for analysis")
                return
            
            # Step 2: Update recommendations
            logger.info("Step 2: Updating recommendations")
            await self._update_recommendations(market_data)
            
            # Step 3: Update support levels for top coins
            logger.info("Step 3: Updating support levels")
            await self._update_support_levels(market_data)
            
            # Step 4: Clean old cache entries
            logger.info("Step 4: Cleaning cache")
            await self._cleanup_cache()
            
            # Step 5: Log analysis completion
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
            logger.info(f"Analysis cycle completed in {cycle_duration:.2f}s")
            
            # Update last analysis timestamp
            self.last_analysis['full_cycle'] = cycle_start
            
        except Exception as e:
            logger.error(f"Analysis cycle failed: {e}", exc_info=True)
    
    async def _fetch_market_data(self) -> Dict[str, Dict]:
        """Fetch latest market data from all sources."""
        try:
            logger.debug("Fetching market data from exchanges")
            
            # Get real market data first
            market_data = await self.real_market_service.get_market_data()
            
            # Fallback to mock data if real data fails
            if not market_data:
                logger.warning("Real market data unavailable, using fallback service")
                market_data = await self.market_service.get_all_market_data()
            
            if market_data:
                logger.info(f"Fetched data for {len(market_data)} symbols")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return {}
    
    async def _update_recommendations(self, market_data: Dict[str, Dict]):
        """Update coin recommendations based on fresh market data."""
        try:
            logger.debug("Updating coin recommendations")
            
            # 거래량 기반 단타 추천 생성 (기본 사용 모드)
            logger.info("Generating volume-based scalping recommendations")
            volume_recommendations = await self.volume_recommender.get_recommendations(
                market_data, 
                settings.top_recommendations_count
            )
            
            # 기존 다중 전략 추천도 생성 (백업 및 비교용)
            logger.info("Generating traditional multi-strategy recommendations")
            traditional_recommendations = await self.coin_recommender.get_recommendations(
                market_data, 
                settings.top_recommendations_count
            )
            
            # 거래량 기반 단타 추천 캐시
            if volume_recommendations:
                volume_cache_key = f"recommendations:volume:{settings.top_recommendations_count}"
                
                volume_response_data = {
                    'recommendations': volume_recommendations,
                    'total_analyzed': len(market_data),
                    'cache_timestamp': datetime.utcnow().isoformat(),
                    'metadata': {
                        'analysis_method': 'volume_based_scalping',
                        'criteria': ['volume', 'volatility', 'liquidity'],
                        'top_n': settings.top_recommendations_count,
                        'auto_generated': True
                    }
                }
                
                await self.cache_service.set(
                    volume_cache_key,
                    volume_response_data,
                    ttl=settings.strategy_cache_ttl
                )
                
                logger.info(f"Updated volume-based recommendations for {len(volume_recommendations)} coins")
                
                # 기본 추천 키에도 거래량 기반 추천 저장 (기본 모드)
                await self.cache_service.set(
                    f"recommendations:{settings.top_recommendations_count}",
                    volume_response_data,
                    ttl=settings.strategy_cache_ttl
                )
            
            # 기존 다중 전략 추천 캐시 (백업용)
            if traditional_recommendations:
                traditional_cache_key = f"recommendations:traditional:{settings.top_recommendations_count}"
                
                traditional_response_data = {
                    'recommendations': traditional_recommendations,
                    'total_analyzed': len(market_data),
                    'cache_timestamp': datetime.utcnow().isoformat(),
                    'metadata': {
                        'analysis_methods': ['technical', 'volume', 'volatility'],
                        'top_n': settings.top_recommendations_count,
                        'auto_generated': True
                    }
                }
                
                await self.cache_service.set(
                    traditional_cache_key,
                    traditional_response_data,
                    ttl=settings.strategy_cache_ttl
                )
                
                logger.info(f"Cached traditional recommendations for {len(traditional_recommendations)} coins")
            
            # Redis에 추천 결과 저장
            try:
                # CoinRecommendation 객체를 딕셔너리로 변환
                def convert_to_dict(obj) -> Dict[str, Any]:
                    if isinstance(obj, dict):
                        return obj
                    elif hasattr(obj, '__dict__'):
                        return dict(obj.__dict__)
                    else:
                        return {"data": str(obj)}
                
                volume_dicts = [convert_to_dict(rec) for rec in volume_recommendations]
                traditional_dicts = [convert_to_dict(rec) for rec in traditional_recommendations]
                
                # 동기 호출로 변경
                result = redis_manager.save_recommendations_to_redis(volume_dicts, traditional_dicts)
                logger.debug(f"Redis save result: {result}")
            except Exception as e:
                logger.error(f"Failed to save recommendations to Redis: {e}")
            
            # WebSocket을 통한 브로드캐스트 (모든 클라이언트에게 최신 추천 전송)
            try:
                # CoinRecommendation 객체를 딕셔너리로 변환
                def convert_to_dict(obj) -> Dict[str, Any]:
                    if isinstance(obj, dict):
                        return obj
                    elif hasattr(obj, '__dict__'):
                        return dict(obj.__dict__)
                    else:
                        return {"data": str(obj)}
                        
                volume_dicts = [convert_to_dict(rec) for rec in volume_recommendations]
                # 동기 호출로 변경
                result = redis_manager.broadcast_recommendations(volume_dicts)
                logger.debug(f"Broadcast result: {result}")
            except Exception as e:
                logger.error(f"Failed to broadcast recommendations via WebSocket: {e}")
            
        except Exception as e:
            logger.error(f"Failed to update recommendations: {e}", exc_info=True)
    
    async def _update_support_levels(self, market_data: Dict[str, Dict]):
        """Update support levels for top performing coins."""
        try:
            logger.debug("Updating support levels")
            
            # Get top coins (first 20 from recommendations)
            top_symbols = list(market_data.keys())[:20]
            
            updated_count = 0
            
            for symbol in top_symbols:
                try:
                    # Get price history
                    price_history = await self.market_service.get_price_history(
                        symbol, 
                        settings.support_level_lookback_days
                    )
                    
                    if not price_history:
                        continue
                    
                    # Calculate support levels
                    support_levels = SupportLevelCalculator.calculate_support_levels(price_history)
                    
                    if support_levels:
                        # Format and cache the results
                        response_data = {
                            'symbol': symbol,
                            'support_levels': {},
                            'calculation_timestamp': datetime.utcnow().isoformat(),
                            'metadata': {
                                'price_data_points': len(price_history),
                                'lookback_days': settings.support_level_lookback_days,
                                'auto_generated': True
                            }
                        }
                        
                        # Convert support levels to response format
                        for level_type, level_data in support_levels.items():
                            response_data['support_levels'][level_type] = {
                                'price': float(level_data.price),
                                'confidence': level_data.confidence,
                                'calculation_method': level_data.calculation_method,
                                'lookback_days': level_data.lookback_days,
                                'metadata': level_data.metadata
                            }
                        
                        # Cache the support levels
                        cache_key = f"support_levels:{symbol}"
                        await self.cache_service.set(
                            cache_key,
                            response_data,
                            ttl=settings.strategy_cache_ttl
                        )
                        
                        updated_count += 1
                
                except Exception as e:
                    logger.warning(f"Failed to update support levels for {symbol}: {e}")
                    continue
            
            logger.info(f"Updated support levels for {updated_count} symbols")
            
        except Exception as e:
            logger.error(f"Failed to update support levels: {e}")
    
    async def _cleanup_cache(self):
        """Clean up old cache entries and expired data."""
        try:
            logger.debug("Cleaning up cache")
            
            # Get cache statistics
            stats = await self.cache_service.get_stats()
            
            if stats.get('expired_keys', 0) > 0:
                logger.info(f"Cache cleanup: {stats['expired_keys']} expired entries found")
            
            # Note: The cache service automatically removes expired entries
            # when they are accessed, so no manual cleanup is needed for the
            # in-memory implementation. In a Redis implementation, you would
            # run SCAN and DELETE commands here.
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    def _update_worker_status(self):
        """워커 상태 업데이트 및 Redis에 하트비트 기록"""
        try:
            worker_status = {
                'worker_id': self.worker_id,
                'last_heartbeat': datetime.utcnow().isoformat(),
                'is_running': self.is_running,
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'stats': {
                    'last_analysis_time': self.last_analysis.get('full_cycle', datetime.utcnow()).isoformat() if self.last_analysis.get('full_cycle') else None,
                    'analysis_count': len(self.last_analysis),
                    'volume_recommender': self.volume_recommender.get_stats() if hasattr(self.volume_recommender, 'get_stats') else {},
                }
            }
            
            # Redis에 상태 저장
            redis_manager.set_worker_status(self.worker_id, worker_status)
            logger.debug(f"Worker status updated: {self.worker_id} is {'running' if self.is_running else 'stopped'}")
            
        except Exception as e:
            logger.error(f"Failed to update worker status: {e}")
    
    async def _send_heartbeat(self):
        """주기적으로 워커 하트비트 전송"""
        try:
            self._update_worker_status()
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
    
    async def _heartbeat_loop(self):
        """주기적으로 하트비트 전송"""
        while self.is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(60)  # 1분마다 하트비트 전송
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(60)  # 오류가 발생해도 계속 시도


# Global market analyzer instance
market_analyzer = MarketAnalyzer()


async def start_background_tasks():
    """Start all background tasks."""
    logger.info("🚀🚀🚀 시작: 백그라운드 작업 시작")
    
    try:
        # 백그라운드 작업 상태 확인 및 재설정
        if market_analyzer.is_running:
            logger.warning("⚠️ Market analyzer was already running. Restarting...")
            await market_analyzer.stop_analysis()
            await asyncio.sleep(1)  # 상태 초기화 대기
        
        # 로깅 레벨 상향 조정 (디버깅)
        logging.getLogger('app.tasks.market_analyzer').setLevel(logging.DEBUG)
        logging.getLogger('app.services.real_market_service').setLevel(logging.DEBUG)
        
        # Start market analysis in background
        logger.info("🔄 Starting continuous analysis task...")
        task = asyncio.create_task(market_analyzer.start_continuous_analysis())
        
        # Wait longer to ensure the task really starts
        await asyncio.sleep(3)
        
        logger.info(f"✓ 백그라운드 작업 상태: {market_analyzer.is_running}")
        
        # 디버깅 정보 기록
        if market_analyzer.is_running:
            logger.info("✅✅✅ 완료: market_analyzer.start_continuous_analysis() 작업이 성공적으로 시작됨")
        else:
            logger.error("❌❌❌ 오류: market_analyzer.start_continuous_analysis() 작업이 생성되었지만 is_running이 False임")
            # 강제로 첫 분석 실행 시도
            logger.info("💢 수동으로 첫 번째 분석 사이클 실행 시도...")
            await market_analyzer.run_analysis_cycle()
        
        return task
    except Exception as e:
        logger.error(f"❌❌❌ 백그라운드 작업 시작 실패: {e}", exc_info=True)
        raise


async def stop_background_tasks():
    """Stop all background tasks."""
    logger.info("Stopping background tasks")
    await market_analyzer.stop_analysis()
