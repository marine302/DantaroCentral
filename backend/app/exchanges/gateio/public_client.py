"""
Gate.io 퍼블릭 API 클라이언트
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class GateIOPublicClient:
    """Gate.io 퍼블릭 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.gateio.ws/api/v4"
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
                    logger.error(f"Gate.io API 요청 실패: {response.status}")
                    return {}
        except asyncio.TimeoutError:
            logger.error("Gate.io API 요청 타임아웃")
            return {}
        except Exception as e:
            logger.error(f"Gate.io API 요청 오류: {e}")
            return {}
    
    async def get_tickers(self) -> List[Dict[str, Any]]:
        """
        모든 티커 정보 조회
        
        Returns:
            List[Dict]: 티커 정보 리스트
        """
        try:
            data = await self._request("/spot/tickers")
            
            if not data:
                return []
            
            tickers = []
            for ticker in data:
                try:
                    # USDT 페어만 필터링
                    symbol = ticker.get('currency_pair', '')
                    if not symbol.endswith('_USDT'):
                        continue
                    
                    # 코인 이름 추출 (예: BTC_USDT -> BTC)
                    coin = symbol.replace('_USDT', '')
                    
                    # 24시간 거래량이 있는지 확인
                    volume_24h = ticker.get('base_volume', '0')
                    if not volume_24h or float(volume_24h) <= 0:
                        continue
                    
                    # 가격 정보
                    current_price = ticker.get('last', '0')
                    if not current_price or float(current_price) <= 0:
                        continue
                    
                    # 24시간 변화율 계산
                    change_percentage = ticker.get('change_percentage', '0')
                    if change_percentage:
                        change_percentage = float(change_percentage)
                    else:
                        change_percentage = 0.0
                    
                    # 거래량 계산 (USDT 기준)
                    volume_usdt = float(volume_24h) * float(current_price)
                    
                    ticker_info = {
                        'symbol': symbol,
                        'coin': coin,
                        'current_price': float(current_price),
                        'volume_24h': float(volume_24h),
                        'volume_24h_usdt': volume_usdt,
                        'change_24h': change_percentage,
                        'high_24h': float(ticker.get('high_24h', current_price)),
                        'low_24h': float(ticker.get('low_24h', current_price)),
                        'exchange': 'gateio'
                    }
                    
                    tickers.append(ticker_info)
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.debug(f"Gate.io 티커 파싱 오류 {symbol}: {e}")
                    continue
            
            # 거래량 기준으로 정렬
            tickers.sort(key=lambda x: x['volume_24h_usdt'], reverse=True)
            
            logger.info(f"Gate.io 티커 수집 완료: {len(tickers)}개")
            return tickers
            
        except Exception as e:
            logger.error(f"Gate.io 티커 수집 오류: {e}")
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
            symbol: 코인 심볼 (예: BTC_USDT)
            
        Returns:
            Dict: 코인 정보
        """
        try:
            data = await self._request(f"/spot/tickers", params={'currency_pair': symbol})
            
            if not data or not isinstance(data, list) or len(data) == 0:
                return None
            
            ticker = data[0]
            coin = symbol.replace('_USDT', '')
            
            volume_24h = float(ticker.get('base_volume', 0))
            current_price = float(ticker.get('last', 0))
            volume_usdt = volume_24h * current_price
            
            return {
                'symbol': symbol,
                'coin': coin,
                'current_price': current_price,
                'volume_24h': volume_24h,
                'volume_24h_usdt': volume_usdt,
                'change_24h': float(ticker.get('change_percentage', 0)),
                'high_24h': float(ticker.get('high_24h', current_price)),
                'low_24h': float(ticker.get('low_24h', current_price)),
                'exchange': 'gateio'
            }
            
        except Exception as e:
            logger.error(f"Gate.io 코인 정보 조회 오류 {symbol}: {e}")
            return None
