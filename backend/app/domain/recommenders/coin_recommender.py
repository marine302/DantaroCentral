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
            if exchange_name.lower() == "upbit":
                return await self._fetch_upbit_recommendations()
            elif exchange_name.lower() == "okx":
                return await self._fetch_okx_recommendations()
            elif exchange_name.lower() == "coinone":
                return await self._fetch_coinone_recommendations()
            elif exchange_name.lower() == "gateio":
                return await self._fetch_gateio_recommendations()
            elif exchange_name.lower() == "bybit":
                return await self._fetch_bybit_recommendations()
            elif exchange_name.lower() == "bithumb":
                return await self._fetch_bithumb_recommendations()
            else:
                logger.warning(f"{exchange_name}는 지원되지 않는 거래소입니다")
                return []
            
        except Exception as e:
            logger.error(f"{exchange_name} 추천 데이터 조회 오류: {e}")
            return []
    
    async def _fetch_upbit_recommendations(self) -> List[Dict[str, Any]]:
        """업비트에서 실제 데이터 조회"""
        try:
            import requests
            
            logger.info("업비트 실시간 데이터 조회 시작")
            
            # 1. 전체 KRW 마켓 코드 조회
            market_url = 'https://api.upbit.com/v1/market/all'
            market_response = requests.get(market_url)
            markets = market_response.json()
            
            krw_markets = [m['market'] for m in markets if m['market'].startswith('KRW-')]
            logger.info(f"업비트 KRW 페어 {len(krw_markets)}개 발견")
            
            # 2. 전체 시세 조회
            ticker_url = 'https://api.upbit.com/v1/ticker'
            markets_param = ','.join(krw_markets)
            ticker_response = requests.get(ticker_url, params={'markets': markets_param})
            tickers = ticker_response.json()
            
            # 3. 거래량 기준으로 정렬 (상위 50개)
            sorted_tickers = sorted(
                tickers,
                key=lambda x: float(x['acc_trade_price_24h']) if x['acc_trade_price_24h'] else 0,
                reverse=True
            )[:50]
            
            # 4. 추천 형태로 변환
            recommendations = []
            for i, ticker in enumerate(sorted_tickers):
                try:
                    symbol = ticker['market'].replace('KRW-', '')
                    price = float(ticker['trade_price'])
                    volume_krw = float(ticker['acc_trade_price_24h'])  # KRW 거래량
                    change_24h = float(ticker['change_rate']) * 100
                    
                    # 변화율과 거래량 기준으로 추천 등급 결정
                    if change_24h > 10:
                        recommendation = "STRONG_BUY"
                        confidence = 0.9
                    elif change_24h > 5:
                        recommendation = "BUY"
                        confidence = 0.8
                    elif change_24h > -5:
                        recommendation = "HOLD"
                        confidence = 0.6
                    elif change_24h > -10:
                        recommendation = "SELL"
                        confidence = 0.7
                    else:
                        recommendation = "STRONG_SELL"
                        confidence = 0.8
                    
                    # 거래량이 높으면 신뢰도 증가
                    if i < 10:  # 상위 10개는 신뢰도 증가
                        confidence = min(0.95, confidence + 0.1)
                    
                    recommendations.append({
                        "symbol": symbol,
                        "full_symbol": ticker['market'],
                        "exchange": "upbit",
                        "rank": i + 1,
                        "price": price,
                        "volume_24h_krw": volume_krw,
                        "volume_24h": float(ticker['acc_trade_volume_24h']),  # 코인 수량
                        "change_24h": change_24h,
                        "recommendation": recommendation,
                        "confidence": round(confidence, 2),
                        "reason": f"거래량 {i+1}위 (24h: {volume_krw:,.0f}원), 변동률 {change_24h:+.2f}%",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.warning(f"업비트 티커 처리 오류 ({ticker.get('market', 'unknown')}): {e}")
                    continue
            
            logger.info(f"업비트에서 {len(recommendations)}개 추천 생성 완료")
            return recommendations
            
        except Exception as e:
            logger.error(f"업비트 추천 데이터 조회 오류: {e}")
            return []
    
    async def _fetch_okx_recommendations(self) -> List[Dict[str, Any]]:
        """OKX에서 거래량 상위 50개 코인 조회"""
        try:
            from app.exchanges.okx.public_client import OKXPublicClient
            
            okx = OKXPublicClient()
            try:
                # 모든 티커 데이터 조회
                tickers = await okx.get_all_tickers()
                if not tickers:
                    logger.warning("OKX에서 티커 데이터를 가져올 수 없음")
                    return []
                
                # USDT 페어만 필터링 및 거래량 USD 계산
                filtered_tickers = []
                for t in tickers:
                    if t.symbol.endswith('-USDT'):
                        volume_usd = float(t.price) * float(t.volume) if t.volume else 0
                        filtered_tickers.append((t, volume_usd))
                
                # 거래량 USD 기준으로 정렬 (상위 50개)
                sorted_tickers = sorted(
                    filtered_tickers, 
                    key=lambda x: x[1],  # volume_usd 기준
                    reverse=True
                )[:50]
                
                # 추천 형태로 변환
                recommendations = []
                for i, (ticker, volume_usd) in enumerate(sorted_tickers):
                    try:
                        # 심볼에서 기본 코인명 추출 (BTC-USDT -> BTC)
                        base_symbol = ticker.symbol.replace('-USDT', '')
                        
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
                            "exchange": "okx",
                            "rank": i + 1,
                            "price": float(ticker.price),
                            "volume_24h": float(ticker.volume),
                            "volume_24h_usdt": volume_usd,  # 필드명 통일
                            "change_24h": 0.0,  # OKX API에서 변동률 추가 필요시
                            "recommendation": recommendation,
                            "confidence": confidence,
                            "reason": f"거래량 {i+1}위 (24h: ${volume_usd:,.0f})",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.warning(f"OKX 티커 처리 오류 ({ticker.symbol}): {e}")
                        continue
                
                logger.info(f"OKX에서 {len(recommendations)}개 추천 생성")
                return recommendations
                
            finally:
                await okx.close()
                
        except Exception as e:
            logger.error(f"OKX 추천 데이터 조회 오류: {e}")
            return []
    
    async def _fetch_coinone_recommendations(self) -> List[Dict[str, Any]]:
        """Coinone에서 거래량 상위 50개 코인 조회"""
        try:
            from app.exchanges.coinone.public_client import CoinonePublicClient
            
            coinone = CoinonePublicClient()
            try:
                # 상위 50개 코인 조회
                tickers = await coinone.get_top_coins(50)
                if not tickers:
                    logger.warning("Coinone에서 티커 데이터를 가져올 수 없음")
                    return []
                
                recommendations = []
                for i, ticker in enumerate(tickers):
                    try:
                        change_24h = ticker.get('change_24h', 0)
                        volume_krw = ticker.get('volume_24h_krw', 0)
                        
                        # 변화율과 거래량 기준으로 추천 등급 결정
                        if change_24h > 10:
                            recommendation = "STRONG_BUY"
                            confidence = 0.9
                        elif change_24h > 5:
                            recommendation = "BUY"
                            confidence = 0.8
                        elif change_24h > -5:
                            recommendation = "HOLD"
                            confidence = 0.6
                        elif change_24h > -10:
                            recommendation = "SELL"
                            confidence = 0.7
                        else:
                            recommendation = "STRONG_SELL"
                            confidence = 0.8
                        
                        # 상위권은 신뢰도 증가
                        if i < 10:
                            confidence = min(0.95, confidence + 0.1)
                        
                        recommendations.append({
                            "symbol": ticker['coin'],
                            "full_symbol": ticker['symbol'],
                            "exchange": "coinone",
                            "rank": i + 1,
                            "price": ticker['current_price'],
                            "volume_24h_krw": volume_krw,
                            "volume_24h": ticker['volume_24h'],
                            "change_24h": change_24h,
                            "recommendation": recommendation,
                            "confidence": round(confidence, 2),
                            "reason": f"거래량 {i+1}위 (24h: {volume_krw:,.0f}원), 변동률 {change_24h:+.2f}%",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.warning(f"Coinone 티커 처리 오류 ({ticker.get('symbol', 'unknown')}): {e}")
                        continue
                
                logger.info(f"Coinone에서 {len(recommendations)}개 추천 생성 완료")
                return recommendations
                
            finally:
                await coinone.close()
                
        except Exception as e:
            logger.error(f"Coinone 추천 데이터 조회 오류: {e}")
            return []
    
    async def _fetch_gateio_recommendations(self) -> List[Dict[str, Any]]:
        """Gate.io에서 거래량 상위 50개 코인 조회"""
        try:
            from app.exchanges.gateio.public_client import GateIOPublicClient
            
            gateio = GateIOPublicClient()
            try:
                # 상위 50개 코인 조회
                tickers = await gateio.get_top_coins(50)
                if not tickers:
                    logger.warning("Gate.io에서 티커 데이터를 가져올 수 없음")
                    return []
                
                recommendations = []
                for i, ticker in enumerate(tickers):
                    try:
                        change_24h = ticker.get('change_24h', 0)
                        volume_usdt = ticker.get('volume_24h_usdt', 0)
                        
                        # 변화율과 거래량 기준으로 추천 등급 결정
                        if change_24h > 10:
                            recommendation = "STRONG_BUY"
                            confidence = 0.9
                        elif change_24h > 5:
                            recommendation = "BUY"
                            confidence = 0.8
                        elif change_24h > -5:
                            recommendation = "HOLD"
                            confidence = 0.6
                        elif change_24h > -10:
                            recommendation = "SELL"
                            confidence = 0.7
                        else:
                            recommendation = "STRONG_SELL"
                            confidence = 0.8
                        
                        # 상위권은 신뢰도 증가
                        if i < 10:
                            confidence = min(0.95, confidence + 0.1)
                        
                        recommendations.append({
                            "symbol": ticker['coin'],
                            "full_symbol": ticker['symbol'],
                            "exchange": "gateio",
                            "rank": i + 1,
                            "price": ticker['current_price'],
                            "volume_24h_usdt": volume_usdt,
                            "volume_24h": ticker['volume_24h'],
                            "change_24h": change_24h,
                            "recommendation": recommendation,
                            "confidence": round(confidence, 2),
                            "reason": f"거래량 {i+1}위 (24h: ${volume_usdt:,.0f}), 변동률 {change_24h:+.2f}%",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.warning(f"Gate.io 티커 처리 오류 ({ticker.get('symbol', 'unknown')}): {e}")
                        continue
                
                logger.info(f"Gate.io에서 {len(recommendations)}개 추천 생성 완료")
                return recommendations
                
            finally:
                await gateio.close()
                
        except Exception as e:
            logger.error(f"Gate.io 추천 데이터 조회 오류: {e}")
            return []
    
    async def _fetch_bybit_recommendations(self) -> List[Dict[str, Any]]:
        """Bybit에서 거래량 상위 50개 코인 조회"""
        try:
            from app.exchanges.bybit.public_client import BybitPublicClient
            
            bybit = BybitPublicClient()
            try:
                # 상위 50개 코인 조회
                tickers = await bybit.get_top_coins(50)
                if not tickers:
                    logger.warning("Bybit에서 티커 데이터를 가져올 수 없음")
                    return []
                
                recommendations = []
                for i, ticker in enumerate(tickers):
                    try:
                        change_24h = ticker.get('change_24h', 0)
                        volume_usdt = ticker.get('volume_24h_usdt', 0)
                        
                        # 변화율과 거래량 기준으로 추천 등급 결정
                        if change_24h > 10:
                            recommendation = "STRONG_BUY"
                            confidence = 0.9
                        elif change_24h > 5:
                            recommendation = "BUY"
                            confidence = 0.8
                        elif change_24h > -5:
                            recommendation = "HOLD"
                            confidence = 0.6
                        elif change_24h > -10:
                            recommendation = "SELL"
                            confidence = 0.7
                        else:
                            recommendation = "STRONG_SELL"
                            confidence = 0.8
                        
                        # 상위권은 신뢰도 증가
                        if i < 10:
                            confidence = min(0.95, confidence + 0.1)
                        
                        recommendations.append({
                            "symbol": ticker['coin'],
                            "full_symbol": ticker['symbol'],
                            "exchange": "bybit",
                            "rank": i + 1,
                            "price": ticker['current_price'],
                            "volume_24h_usdt": volume_usdt,
                            "volume_24h": ticker['volume_24h'],
                            "change_24h": change_24h,
                            "recommendation": recommendation,
                            "confidence": round(confidence, 2),
                            "reason": f"거래량 {i+1}위 (24h: ${volume_usdt:,.0f}), 변동률 {change_24h:+.2f}%",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.warning(f"Bybit 티커 처리 오류 ({ticker.get('symbol', 'unknown')}): {e}")
                        continue
                
                logger.info(f"Bybit에서 {len(recommendations)}개 추천 생성 완료")
                return recommendations
                
            finally:
                await bybit.close()
                
        except Exception as e:
            logger.error(f"Bybit 추천 데이터 조회 오류: {e}")
            return []
    
    async def _fetch_bithumb_recommendations(self) -> List[Dict[str, Any]]:
        """Bithumb에서 거래량 상위 50개 코인 조회"""
        try:
            from app.exchanges.bithumb.public_client import BithumbPublicClient
            
            bithumb = BithumbPublicClient()
            try:
                # 상위 50개 코인 조회
                tickers = await bithumb.get_top_coins(50)
                if not tickers:
                    logger.warning("Bithumb에서 티커 데이터를 가져올 수 없음")
                    return []
                
                recommendations = []
                for i, ticker in enumerate(tickers):
                    try:
                        change_24h = ticker.get('change_24h', 0)
                        volume_krw = ticker.get('volume_24h_krw', 0)
                        
                        # 변화율과 거래량 기준으로 추천 등급 결정
                        if change_24h > 10:
                            recommendation = "STRONG_BUY"
                            confidence = 0.9
                        elif change_24h > 5:
                            recommendation = "BUY"
                            confidence = 0.8
                        elif change_24h > -5:
                            recommendation = "HOLD"
                            confidence = 0.6
                        elif change_24h > -10:
                            recommendation = "SELL"
                            confidence = 0.7
                        else:
                            recommendation = "STRONG_SELL"
                            confidence = 0.8
                        
                        # 상위권은 신뢰도 증가
                        if i < 10:
                            confidence = min(0.95, confidence + 0.1)
                        
                        recommendations.append({
                            "symbol": ticker['coin'],
                            "full_symbol": ticker['symbol'],
                            "exchange": "bithumb",
                            "rank": i + 1,
                            "price": ticker['current_price'],
                            "volume_24h_krw": volume_krw,
                            "volume_24h": ticker['volume_24h'],
                            "change_24h": change_24h,
                            "recommendation": recommendation,
                            "confidence": round(confidence, 2),
                            "reason": f"거래량 {i+1}위 (24h: {volume_krw:,.0f}원), 변동률 {change_24h:+.2f}%",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.warning(f"Bithumb 티커 처리 오류 ({ticker.get('symbol', 'unknown')}): {e}")
                        continue
                
                logger.info(f"Bithumb에서 {len(recommendations)}개 추천 생성 완료")
                return recommendations
                
            finally:
                await bithumb.close()
                
        except Exception as e:
            logger.error(f"Bithumb 추천 데이터 조회 오류: {e}")
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
