"""
Coinone 퍼블릭 API 클라이언트
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class CoinonePublicClient:
    """Coinone 퍼블릭 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.coinone.co.kr"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 반환"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """세션 정리"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """API 요청"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}{endpoint}"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Coinone API 요청 실패: {response.status}")
                    return {}
        except asyncio.TimeoutError:
            logger.error("Coinone API 요청 타임아웃")
            return {}
        except Exception as e:
            logger.error(f"Coinone API 요청 오류: {e}")
            return {}
    
    async def get_tickers(self) -> List[Dict[str, Any]]:
        """
        모든 티커 정보 조회
        
        Returns:
            List[Dict]: 티커 정보 리스트
        """
        try:
            # 전체 티커 조회
            tickers_data = await self._request("/public/v2/ticker_new/KRW")
            
            if not tickers_data or tickers_data.get('result') != 'success':
                logger.error("Coinone 티커 데이터 조회 실패")
                return []
            
            tickers = []
            ticker_list = tickers_data.get('tickers', [])
            
            for ticker in ticker_list:
                try:
                    # 코인 이름
                    coin = ticker.get('target_currency', '').upper()
                    if not coin:
                        continue
                    
                    # 현재 가격
                    current_price = float(ticker.get('last', '0'))
                    if current_price <= 0:
                        continue
                    
                    # KRW 거래량 (quote_volume이 KRW 거래량)
                    volume_krw = float(ticker.get('quote_volume', '0'))
                    if volume_krw <= 0:
                        continue
                    
                    # 코인 거래량 (target_volume이 코인 수량)
                    volume_coin = float(ticker.get('target_volume', '0'))
                    
                    # 24시간 변화율 계산
                    first_price = float(ticker.get('first', current_price))
                    try:
                        change_percentage = ((current_price - first_price) / first_price) * 100
                    except (ValueError, ZeroDivisionError):
                        change_percentage = 0.0
                    
                    ticker_info = {
                        'symbol': f"KRW-{coin}",
                        'coin': coin,
                        'current_price': current_price,
                        'volume_24h': volume_coin,
                        'volume_24h_krw': volume_krw,
                        'volume_24h_usdt': volume_krw / 1300,  # 대략적인 USD 환산
                        'change_24h': change_percentage,
                        'high_24h': float(ticker.get('high', current_price)),
                        'low_24h': float(ticker.get('low', current_price)),
                        'exchange': 'coinone'
                    }
                    
                    tickers.append(ticker_info)
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.debug(f"Coinone 티커 파싱 오류 {coin}: {e}")
                    continue
            
            # KRW 거래량 기준으로 정렬
            tickers.sort(key=lambda x: x['volume_24h_krw'], reverse=True)
            
            logger.info(f"Coinone 티커 수집 완료: {len(tickers)}개")
            return tickers
            
        except Exception as e:
            logger.error(f"Coinone 티커 수집 오류: {e}")
            return []
    
    async def get_top_coins(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        거래량 상위 코인 조회
        
        Args:
            limit: 반환할 코인 수
            
        Returns:
            List[Dict]: 상위 코인 정보
        """
        tickers = await self.get_tickers()
        return tickers[:limit]
    
    async def get_coin_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        특정 코인 정보 조회
        
        Args:
            symbol: 코인 심볼 (예: BTC 또는 KRW-BTC)
            
        Returns:
            Dict: 코인 정보
        """
        try:
            # KRW- 제거
            coin = symbol.replace('KRW-', '').upper()
            
            data = await self._request(f"/public/v2/ticker_new/KRW/{coin}")
            
            if not data or data.get('result') != 'success':
                return None
            
            ticker_list = data.get('tickers', [])
            if not ticker_list:
                return None
            
            ticker = ticker_list[0]
            
            # 현재 가격
            current_price = float(ticker.get('last', 0))
            if current_price <= 0:
                return None
            
            # KRW 거래량 (quote_volume이 KRW 거래량)
            volume_krw = float(ticker.get('quote_volume', '0'))
            
            # 코인 거래량 (target_volume이 코인 수량)
            volume_coin = float(ticker.get('target_volume', '0'))
            
            # 24시간 변화율 계산
            first_price = float(ticker.get('first', current_price))
            try:
                change_percentage = ((current_price - first_price) / first_price) * 100
            except (ValueError, ZeroDivisionError):
                change_percentage = 0.0
            
            return {
                'symbol': f"KRW-{coin}",
                'coin': coin,
                'current_price': current_price,
                'volume_24h': volume_coin,
                'volume_24h_krw': volume_krw,
                'volume_24h_usdt': volume_krw / 1300,
                'change_24h': change_percentage,
                'high_24h': float(ticker.get('high', current_price)),
                'low_24h': float(ticker.get('low', current_price)),
                'exchange': 'coinone'
            }
            
        except Exception as e:
            logger.error(f"Coinone 코인 정보 조회 오류 {symbol}: {e}")
            return None
