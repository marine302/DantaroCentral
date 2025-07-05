"""
Real market data service using CCXT for multiple exchanges.
"""
import ccxt
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

class RealMarketDataService:
    """Real market data service using CCXT."""
    
    def __init__(self):
        # Initialize exchanges
        self.exchanges = {
            'upbit': ccxt.upbit(),
            'bithumb': ccxt.bithumb(), 
            'coinone': ccxt.coinone()
        }
        self.cache = {}
        self.cache_ttl = getattr(settings, "real_market_cache_ttl", 60)  # seconds
        
    async def get_market_data(self) -> Dict[str, Dict]:
        """Get real market data from Korean exchanges."""
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.info("Using cached market data")
                return self.cache.get('data', {})
            
            logger.info("Fetching fresh market data...")
            
            # Get data from Upbit (most reliable Korean exchange)
            upbit_data = await self._fetch_upbit_data()
            
            # Cache the data
            self.cache = {
                'data': upbit_data,
                'timestamp': time.time()
            }
            
            logger.info(f"Fetched data for {len(upbit_data)} symbols")
            return upbit_data
            
        except Exception as e:
            logger.error(f"Failed to fetch real market data: {e}")
            # Fallback to empty data rather than mock
            return {}
    
    async def _fetch_upbit_data(self) -> Dict[str, Dict]:
        """
        거래소에서 전체 코인 데이터 가져오기
        
        전체 코인 데이터를 가져와 거래량 기반으로 정렬하고
        추가 분석에 필요한 데이터를 포함합니다.
        
        최적화: fetchTickers API 호출 제한을 피하기 위해 
        코인을 50개씩 배치로 나누어 데이터를 가져옵니다.
        """
        try:
            upbit = self.exchanges['upbit']
            
            # 모든 KRW 마켓 가져오기
            markets = upbit.load_markets()
            krw_symbols = [symbol for symbol in markets.keys() if '/KRW' in symbol]
            
            # 1단계: 모든 코인의 기본 데이터와 거래량 가져오기
            logger.info(f"총 {len(krw_symbols)}개 코인 데이터 수집 시작")
            
            # 심볼을 작은 배치로 나누어 요청 (URL 길이 제한 초과 방지)
            batch_size = 50  # 한번에 50개씩만 요청
            all_tickers = {}
            
            for i in range(0, len(krw_symbols), batch_size):
                batch_symbols = krw_symbols[i:i+batch_size]
                logger.info(f"배치 수집 중: {i+1}-{i+len(batch_symbols)}/{len(krw_symbols)} 코인")
                try:
                    # 배치별로 티커 데이터 요청
                    batch_tickers = upbit.fetch_tickers(symbols=batch_symbols)
                    all_tickers.update(batch_tickers)
                    await asyncio.sleep(0.5)  # API 속도 제한 고려
                except Exception as e:
                    logger.warning(f"배치 {i//batch_size + 1} 데이터 수집 실패: {str(e)}")
                    continue
            
            # 거래량으로 정렬할 임시 데이터
            volume_data = []
            
            # 모든 코인 기본 정보 수집
            for symbol in krw_symbols:
                try:
                    if symbol in all_tickers:
                        ticker = all_tickers[symbol]
                        
                        # 거래량 기준 추적
                        volume = float(ticker.get('quoteVolume', 0) or 0)
                        volume_data.append((symbol, volume))
                except Exception as e:
                    logger.debug(f"{symbol} 기본 데이터 수집 실패: {e}")
                    continue
            
            # 2단계: 거래량 기준 정렬
            volume_data.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 100개 코인만 선택 (API 제한 고려)
            max_symbols_to_analyze = 100
            top_volume_symbols = [s[0] for s in volume_data[:max_symbols_to_analyze]]
            
            logger.info(f"거래량 상위 {len(top_volume_symbols)}개 코인 선별 완료")
            
            # 3단계: 선별된 코인 상세 데이터 수집
            market_data = {}
            
            for i, symbol in enumerate(top_volume_symbols):
                try:
                    ticker = all_tickers.get(symbol)
                    
                    if not ticker:
                        continue
                        
                    # OHLCV 데이터 (차트 분석용)
                    # 1일 캔들 30개와 1시간 캔들 24개 가져오기
                    ohlcv_daily = upbit.fetch_ohlcv(symbol, '1d', limit=30)
                    ohlcv_hourly = upbit.fetch_ohlcv(symbol, '1h', limit=24)
                    
                    # 데이터 가공
                    daily_prices = [float(candle[4]) for candle in ohlcv_daily]
                    daily_volumes = [float(candle[5]) for candle in ohlcv_daily]
                    
                    # 시간별 고가/저가 계산 (변동성 분석용)
                    hourly_high = max([float(candle[2]) for candle in ohlcv_hourly[-6:]], default=0)
                    hourly_low = min([float(candle[3]) for candle in ohlcv_hourly[-6:]], default=0)
                    
                    # 시간당 평균 거래 건수 추정 (유동성 분석용)
                    hourly_volume = sum([float(candle[5]) for candle in ohlcv_hourly[-6:]])
                    estimated_trades = int(hourly_volume / float(ticker['last'] or 1) / 100)
                    
                    # 데이터 포맷팅 (분석기에 필요한 모든 정보 포함)
                    market_data[symbol] = {
                        'current_price': float(ticker['last']),
                        'price_change_24h': float(ticker.get('percentage', 0) or 0),
                        'volume_24h': float(ticker.get('quoteVolume', 0) or 0),
                        'volume_rank': i + 1,  # 거래량 순위 기록
                        'volume_change_24h': 0,  # 기본값, 이전 데이터와 비교해야 계산 가능
                        'market_cap': None,  # 업비트는 시가총액 제공하지 않음
                        
                        # 가격 이력 데이터
                        'price_history': [{'close': p} for p in daily_prices],
                        'volume_history': daily_volumes,
                        
                        # 1시간 변동성 데이터
                        'high_1h': hourly_high,
                        'low_1h': hourly_low,
                        'trades_count_1h': max(1, estimated_trades),  # 최소 1
                        
                        # 기타 메타데이터
                        'timestamp': ticker['timestamp'],
                        'symbol_name': markets[symbol]['base'],  # 코인 이름 (BTC, ETH 등)
                    }
                    
                    # API 속도 제한 회피
                    if i > 0 and i % 10 == 0:
                        logger.info(f"진행 중: {i}/{len(top_volume_symbols)} 코인 데이터 수집")
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"{symbol} 상세 데이터 수집 실패: {str(e)}")
                    continue
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to fetch Upbit data: {e}")
            raise
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.cache:
            return False
        
        cache_age = time.time() - self.cache.get('timestamp', 0)
        return cache_age < self.cache_ttl
    
    async def get_symbol_data(self, symbol: str) -> Optional[Dict]:
        """Get data for a specific symbol."""
        all_data = await self.get_market_data()
        return all_data.get(symbol)
