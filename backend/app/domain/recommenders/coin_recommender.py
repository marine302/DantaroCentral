"""
코인 추천 시스템
거래소별 거래량 상위 50개 코인을 실시간으로 조회하여 추천
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json

from app.exchanges.factory import ExchangeFactory
from app.database.redis_cache import redis_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class CoinRecommender:
    """코인 추천 시스템 - 거래소별 거래량 상위 50개 코인 추천"""
    
    def __init__(self):
        self.name = "CoinRecommender"
        self.exchange_factory = ExchangeFactory()
        self.cache_duration = 300  # 5분 캐시
        self._running = False
        logger.info("CoinRecommender 초기화됨")
    
    async def get_recommendations(self, 
                                exchange: str = "upbit", 
                                symbol: Optional[str] = None,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """코인 추천 목록 반환 (거래량 기준 상위)"""
        try:
            # 캐시에서 먼저 확인
            cache_key = f"coin_recommendations:{exchange}"
            cached_data = redis_manager.get_recommendations(exchange)
            
            if cached_data:
                recommendations = cached_data
                logger.info(f"캐시에서 {exchange} 추천 데이터 반환: {len(recommendations)}개")
            else:
                # 실시간 데이터 조회
                recommendations = await self._fetch_recommendations_from_exchange(exchange)
                
                # 캐시에 저장
                redis_manager.cache_recommendations(recommendations, exchange)
                logger.info(f"{exchange}에서 새로운 추천 데이터 조회: {len(recommendations)}개")
            
            # 특정 심볼 필터링
            if symbol:
                recommendations = [r for r in recommendations if r["symbol"] == symbol.upper()]
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"추천 생성 오류 ({exchange}): {e}")
            return []
    
    async def get_recommendations_by_exchange(self, 
                                            exchange_names: Optional[List[str]] = None,
                                            limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """여러 거래소별 추천 목록 반환"""
        if not exchange_names:
            exchange_names = ["upbit", "okx", "coinone", "gateio", "bybit", "bithumb"]
        
        results = {}
        
        # 병렬로 여러 거래소 조회
        tasks = []
        for exchange in exchange_names:
            task = self.get_recommendations(exchange=exchange, limit=limit)
            tasks.append((exchange, task))
        
        for exchange, task in tasks:
            try:
                recommendations = await task
                results[exchange] = recommendations
            except Exception as e:
                logger.error(f"{exchange} 추천 조회 오류: {e}")
                results[exchange] = []
        
        return results
    
    async def _fetch_recommendations_from_exchange(self, exchange_name: str) -> List[Dict[str, Any]]:
        """거래소에서 거래량 상위 50개 코인 조회"""
        try:
            # 거래소 인스턴스 생성
            exchange = self.exchange_factory.create_exchange(exchange_name)
            if not exchange:
                logger.error(f"지원하지 않는 거래소: {exchange_name}")
                return []
            
            # 모든 심볼 조회
            symbols = await exchange.get_symbols()
            if not symbols:
                logger.warning(f"{exchange_name}에서 심볼 목록을 가져올 수 없음")
                return []
            
            # USDT 페어만 필터링 (거래소별로 조정)
            if exchange_name.lower() == "upbit":
                # 업비트는 KRW 페어
                filtered_symbols = [s for s in symbols if s.endswith("-KRW")]
            else:
                # 다른 거래소는 USDT 페어
                filtered_symbols = [s for s in symbols if s.endswith("USDT")]
            
            # 각 심볼에 대해 티커 정보 조회
            tickers = []
            for symbol in filtered_symbols[:100]:  # 최대 100개만 조회
                try:
                    ticker = await exchange.get_ticker(symbol)
                    if ticker and ticker.volume:
                        tickers.append(ticker)
                except Exception as e:
                    logger.debug(f"{symbol} 티커 조회 실패: {e}")
                    continue
            
            if not tickers:
                logger.warning(f"{exchange_name}에서 티커 데이터를 가져올 수 없음")
                return []
            
            # 거래량 기준으로 정렬 (상위 50개)
            sorted_tickers = sorted(
                tickers, 
                key=lambda x: float(x.volume) if x.volume else 0, 
                reverse=True
            )[:50]
            
            # 추천 형태로 변환
            recommendations = []
            for i, ticker in enumerate(sorted_tickers):
                try:
                    # 심볼에서 기본 코인명 추출
                    base_symbol = ticker.symbol.split('-')[0] if '-' in ticker.symbol else ticker.symbol.replace('USDT', '')
                    
                    # 변화율 계산 (임시로 0으로 설정)
                    change_24h = 0.0  # BaseExchange에 change_24h 필드가 없음
                    
                    # 추천 등급은 거래량 순위에 따라 결정
                    if i < 10:
                        recommendation = "STRONG_BUY"
                        confidence = 0.9
                    elif i < 20:
                        recommendation = "BUY"
                        confidence = 0.8
                    elif i < 30:
                        recommendation = "HOLD"
                        confidence = 0.6
                    else:
                        recommendation = "WATCH"
                        confidence = 0.5
                    
                    recommendations.append({
                        "symbol": base_symbol,
                        "full_symbol": ticker.symbol,
                        "exchange": exchange_name,
                        "rank": i + 1,
                        "price": float(ticker.price) if ticker.price else 0,
                        "volume_24h": float(ticker.volume) if ticker.volume else 0,
                        "change_24h": change_24h,
                        "recommendation": recommendation,
                        "confidence": confidence,
                        "reason": f"거래량 {i+1}위",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.warning(f"티커 처리 오류 ({ticker.symbol}): {e}")
                    continue
            
            logger.info(f"{exchange_name}에서 {len(recommendations)}개 추천 생성")
            return recommendations
            
        except Exception as e:
            logger.error(f"{exchange_name} 추천 데이터 조회 오류: {e}")
            return []
    
    async def update_all_recommendations(self):
        """모든 거래소의 추천 데이터 갱신"""
        exchange_names = ["upbit", "okx", "coinone", "gateio", "bybit", "bithumb"]
        
        logger.info("모든 거래소 추천 데이터 갱신 시작")
        
        for exchange in exchange_names:
            try:
                # 캐시 무효화 후 새로운 데이터 조회
                recommendations = await self._fetch_recommendations_from_exchange(exchange)
                
                if recommendations:
                    # 캐시에 저장
                    redis_manager.cache_recommendations(recommendations, exchange)
                    logger.info(f"{exchange} 추천 데이터 갱신 완료: {len(recommendations)}개")
                else:
                    logger.warning(f"{exchange} 추천 데이터 갱신 실패")
                    
            except Exception as e:
                logger.error(f"{exchange} 추천 데이터 갱신 오류: {e}")
        
        logger.info("모든 거래소 추천 데이터 갱신 완료")
    
    async def start_background_update(self):
        """백그라운드에서 주기적으로 추천 데이터 갱신"""
        if self._running:
            return
            
        self._running = True
        logger.info("코인 추천 백그라운드 갱신 시작")
        
        while self._running:
            try:
                await self.update_all_recommendations()
                # 5분마다 갱신
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"백그라운드 갱신 오류: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 후 재시도
    
    def stop_background_update(self):
        """백그라운드 갱신 중지"""
        self._running = False
        logger.info("코인 추천 백그라운드 갱신 중지")


# 글로벌 인스턴스
coin_recommender = CoinRecommender()
