"""
Main analysis worker for Dantaro Central.
Runs 24/7 to keep market analysis and recommendations up-to-date.
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import time
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import get_sync_db
from app.database.redis_cache import redis_manager
from app.database.manager import db_manager
from app.models.database import AnalysisJob, CoinRecommendation, SupportLevel, MarketStatus
from app.core.config import settings


class AnalysisWorker:
    """
    Main analysis worker class.
    Runs scheduled analysis jobs and maintains system health.
    """
    
    def __init__(self):
        self.worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        self.scheduler = AsyncIOScheduler()
        self.running = False
        self.logger = self._setup_logging()
        
        # 종료 신호 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 작업 통계
        self.stats = {
            'jobs_completed': 0,
            'jobs_failed': 0,
            'last_heartbeat': None,
            'started_at': datetime.now(),
            'current_jobs': {}
        }
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정."""
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - {self.worker_id} - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'worker-{self.worker_id}.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """종료 신호 처리."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    async def start(self):
        """워커 시작."""
        try:
            self.logger.info(f"Starting analysis worker {self.worker_id}")
            self.running = True
            
            # 스케줄러 작업 등록
            await self._register_jobs()
            
            # 스케줄러 시작
            self.scheduler.start()
            self.logger.info("Scheduler started")
            
            # 하트비트 시작
            await self._start_heartbeat()
            
            # 메인 루프
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Worker startup failed: {e}")
            raise
    
    def stop(self):
        """워커 중지."""
        self.logger.info("Stopping analysis worker...")
        self.running = False
        
        if self.scheduler.running:
            self.scheduler.shutdown()
        
        self.logger.info("Analysis worker stopped")
    
    async def _register_jobs(self):
        """스케줄러에 작업 등록."""
        # 시장 상태 분석 - 2분마다
        self.scheduler.add_job(
            self.analyze_market_status,
            CronTrigger(minute='*/2'),
            id='market_status_analysis',
            name='Market Status Analysis',
            max_instances=1,
            coalesce=True
        )
        
        # 코인 추천 분석 - 5분마다
        self.scheduler.add_job(
            self.analyze_coin_recommendations,
            CronTrigger(minute='*/5'),
            id='coin_recommendations_analysis',
            name='Coin Recommendations Analysis',
            max_instances=1,
            coalesce=True
        )
        
        # 지지/저항선 분석 - 15분마다
        self.scheduler.add_job(
            self.analyze_support_levels,
            CronTrigger(minute='*/15'),
            id='support_levels_analysis',
            name='Support Levels Analysis',
            max_instances=1,
            coalesce=True
        )
        
        # 정리 작업 - 매시간
        self.scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(minute=0),
            id='cleanup_data',
            name='Cleanup Old Data',
            max_instances=1,
            coalesce=True
        )
        
        self.logger.info("All jobs registered")
    
    async def _start_heartbeat(self):
        """하트비트 시작."""
        async def heartbeat():
            while self.running:
                try:
                    status = {
                        'worker_id': self.worker_id,
                        'status': 'running',
                        'stats': self.stats,
                        'uptime_seconds': (datetime.now() - self.stats['started_at']).total_seconds()
                    }
                    redis_manager.set_worker_status(self.worker_id, status)
                    self.stats['last_heartbeat'] = datetime.now()
                    await asyncio.sleep(30)  # 30초마다 하트비트
                except Exception as e:
                    self.logger.error(f"Heartbeat failed: {e}")
                    await asyncio.sleep(5)
        
        asyncio.create_task(heartbeat())
    
    async def analyze_market_status(self):
        """시장 상태 분석."""
        job_id = await self._start_job('market_status')
        try:
            self.logger.info("Starting market status analysis...")
            
            # TODO: 실제 시장 분석 로직 구현
            # 현재는 더미 데이터
            market_data = {
                'market_trend': 'bullish',
                'market_sentiment': 'positive',
                'overall_score': 0.75,
                'active_coins_count': 50,
                'total_market_cap': 1000000000,
                'total_volume_24h': 50000000,
                'analysis_summary': {
                    'top_gainers': 10,
                    'top_losers': 5,
                    'stable_coins': 35
                }
            }
            
            # 캐시에 저장
            redis_manager.cache_market_status(market_data)
            
            # 데이터베이스에 저장
            db_manager.save_market_status(market_data)
            
            await self._complete_job(job_id, 1)
            self.logger.info("Market status analysis completed")
            
        except Exception as e:
            await self._fail_job(job_id, str(e))
            self.logger.error(f"Market status analysis failed: {e}")
    
    async def analyze_coin_recommendations(self):
        """코인 추천 분석."""
        job_id = await self._start_job('recommendations')
        try:
            self.logger.info("Starting coin recommendations analysis...")
            
            # TODO: 실제 추천 분석 로직 구현
            # 현재는 더미 데이터
            recommendations = [
                {
                    'symbol': 'BTC',
                    'total_score': 0.85,
                    'technical_score': 0.80,
                    'volume_score': 0.90,
                    'volatility_score': 0.75,
                    'risk_score': 0.85,
                    'recommendation_strength': 'strong',
                    'current_price': 50000.0,
                    'price_change_24h': 0.05,
                    'volume_24h': 1000000000,
                    'market_cap': 950000000000,
                    'analysis_details': {'rsi': 65, 'macd': 'bullish'}
                }
            ]
            
            # 캐시에 저장
            redis_manager.cache_recommendations(recommendations)
            
            # 데이터베이스에 저장
            db_manager.save_coin_recommendations(recommendations)
            
            await self._complete_job(job_id, len(recommendations))
            self.logger.info(f"Coin recommendations analysis completed: {len(recommendations)} coins")
            
        except Exception as e:
            await self._fail_job(job_id, str(e))
            self.logger.error(f"Coin recommendations analysis failed: {e}")
    
    async def analyze_support_levels(self):
        """지지/저항선 분석."""
        job_id = await self._start_job('support_levels')
        try:
            self.logger.info("Starting support levels analysis...")
            
            # TODO: 실제 지지/저항선 분석 로직 구현
            # 현재는 더미 데이터
            symbols = ['BTC', 'ETH', 'ADA']
            processed_count = 0
            
            for symbol in symbols:
                support_data = {
                    'aggressive_support': 48000.0,
                    'moderate_support': 47000.0,
                    'conservative_support': 46000.0,
                    'aggressive_resistance': 52000.0,
                    'moderate_resistance': 53000.0,
                    'conservative_resistance': 54000.0,
                    'calculation_method': 'fibonacci',
                    'data_points_count': 100
                }
                
                # 캐시에 저장
                redis_manager.cache_support_levels(symbol, support_data)
                
                # 데이터베이스에 저장
                db_manager.save_support_levels(symbol, support_data)
                processed_count += 1
            
            await self._complete_job(job_id, processed_count)
            self.logger.info(f"Support levels analysis completed: {processed_count} symbols")
            
        except Exception as e:
            await self._fail_job(job_id, str(e))
            self.logger.error(f"Support levels analysis failed: {e}")
    
    async def cleanup_old_data(self):
        """오래된 데이터 정리."""
        job_id = await self._start_job('cleanup')
        try:
            self.logger.info("Starting cleanup of old data...")
            
            # TODO: 실제 정리 로직 구현
            cleaned_count = 0
            
            await self._complete_job(job_id, cleaned_count)
            self.logger.info(f"Cleanup completed: {cleaned_count} items removed")
            
        except Exception as e:
            await self._fail_job(job_id, str(e))
            self.logger.error(f"Cleanup failed: {e}")
    
    async def _start_job(self, job_type: str) -> str:
        """작업 시작 기록."""
        job_id = f"{job_type}-{uuid.uuid4().hex[:8]}"
        self.stats['current_jobs'][job_id] = {
            'type': job_type,
            'started_at': datetime.now(),
            'status': 'running'
        }
        return job_id
    
    async def _complete_job(self, job_id: str, processed_count: int):
        """작업 완료 기록."""
        if job_id in self.stats['current_jobs']:
            job_info = self.stats['current_jobs'][job_id]
            execution_time = (datetime.now() - job_info['started_at']).total_seconds()
            
            # 데이터베이스에 작업 기록 저장
            db_manager.save_analysis_job(
                job_type=job_info['type'],
                job_status='completed',
                started_at=job_info['started_at'],
                completed_at=datetime.now(),
                execution_time_seconds=execution_time,
                processed_items_count=processed_count,
                worker_id=self.worker_id
            )
            
            del self.stats['current_jobs'][job_id]
            self.stats['jobs_completed'] += 1
    
    async def _fail_job(self, job_id: str, error_message: str):
        """작업 실패 기록."""
        if job_id in self.stats['current_jobs']:
            job_info = self.stats['current_jobs'][job_id]
            execution_time = (datetime.now() - job_info['started_at']).total_seconds()
            
            # 데이터베이스에 실패 기록 저장
            db_manager.save_analysis_job(
                job_type=job_info['type'],
                job_status='failed',
                started_at=job_info['started_at'],
                completed_at=datetime.now(),
                execution_time_seconds=execution_time,
                error_message=error_message,
                worker_id=self.worker_id
            )
            
            del self.stats['current_jobs'][job_id]
            self.stats['jobs_failed'] += 1


async def main():
    """메인 함수."""
    worker = AnalysisWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.logger.info("Received keyboard interrupt")
    except Exception as e:
        worker.logger.error(f"Unexpected error: {e}")
    finally:
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
