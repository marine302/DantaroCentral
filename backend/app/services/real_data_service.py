"""
실제 거래소 데이터 수집 서비스 (Clean Version)
DantaroCentral - Real Data Collection Service

목적:
- 다중 거래소에서 실시간 시세 데이터 수집
- HTTP API 기반으로 안정적인 데이터 제공
- API 키 없이도 공개 데이터 접근 가능

지원 거래소:
- OKX: 공개 API (API 키 선택사항)
- Upbit: 공개 API (API 키 불필요)
- Coinone: 공개 API (API 키 불필요)
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CoinData:
    """코인 데이터 표준 포맷"""
    symbol: str           # 심볼 (예: BTC/USDT, BTC/KRW)
    exchange: str         # 거래소 (OKX, Upbit, Coinone)
    price: float          # 현재가
    volume_24h: float     # 24시간 거래량
    change_24h: float     # 24시간 변동률 (%)
    currency: str         # 기준통화 (USD, KRW)
    timestamp: str        # 데이터 수집 시간


class RealDataService:
    """실제 거래소 데이터 수집 서비스"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.collected_data: Dict[str, Dict] = {}  # 타입 수정
        self.stats = {
            'total_collected': 0,
            'last_update': None,
            'exchange_status': {}
        }
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def collect_okx_data(self) -> Dict[str, CoinData]:
        """OKX 거래소 데이터 수집"""
        try:
            url = "https://www.okx.com/api/v5/market/tickers"
            params = {'instType': 'SPOT'}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"OKX API 응답 오류: {response.status}")
                    return {}
                
                data = await response.json()
                
                if data.get('code') != '0':
                    logger.warning(f"OKX API 오류: {data.get('msg', 'Unknown')}")
                    return {}
                
                # 주요 USDT 페어 추출
                major_pairs = [
                    'BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'ADA-USDT', 'XRP-USDT',
                    'DOT-USDT', 'AVAX-USDT', 'LINK-USDT', 'UNI-USDT', 'MATIC-USDT',
                    'LTC-USDT', 'BCH-USDT', 'ATOM-USDT', 'FIL-USDT', 'NEAR-USDT'
                ]
                
                okx_data = {}
                for ticker in data['data']:
                    if ticker['instId'] in major_pairs:
                        symbol = ticker['instId'].replace('-', '/')
                        key = f"OKX_{symbol}"
                        
                        coin_data = CoinData(
                            symbol=symbol,
                            exchange='OKX',
                            price=float(ticker.get('last', 0)),
                            volume_24h=float(ticker.get('volCcy24h', 0)),
                            change_24h=float(ticker.get('chgUtc0', 0)) * 100,
                            currency='USD',
                            timestamp=datetime.now().isoformat()
                        )
                        okx_data[key] = coin_data
                
                logger.info(f"✅ OKX 데이터 수집 완료: {len(okx_data)}개")
                self.stats['exchange_status']['OKX'] = 'success'
                return okx_data
                
        except Exception as e:
            logger.error(f"❌ OKX 데이터 수집 실패: {e}")
            self.stats['exchange_status']['OKX'] = 'failed'
            return {}
    
    async def collect_upbit_data(self) -> Dict[str, CoinData]:
        """Upbit 거래소 데이터 수집"""
        try:
            # 주요 KRW 마켓을 작은 그룹으로 나누어 요청
            market_groups = [
                ['KRW-BTC', 'KRW-ETH', 'KRW-SOL', 'KRW-ADA', 'KRW-XRP'],
                ['KRW-DOT', 'KRW-AVAX', 'KRW-LINK', 'KRW-UNI', 'KRW-MATIC'],
                ['KRW-LTC', 'KRW-BCH', 'KRW-ATOM', 'KRW-NEAR', 'KRW-SAND']
            ]
            
            upbit_data = {}
            
            for markets in market_groups:
                url = "https://api.upbit.com/v1/ticker"
                params = {'markets': ','.join(markets)}
                
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(f"Upbit API 응답 오류: {response.status}")
                        continue
                    
                    data = await response.json()
                    
                    for coin in data:
                        market = coin['market']
                        symbol = market.replace('KRW-', '') + '/KRW'
                        key = f"Upbit_{symbol}"
                        
                        coin_data = CoinData(
                            symbol=symbol,
                            exchange='Upbit',
                            price=float(coin['trade_price']),
                            volume_24h=float(coin['acc_trade_volume_24h']),
                            change_24h=float(coin['signed_change_rate']) * 100,
                            currency='KRW',
                            timestamp=datetime.now().isoformat()
                        )
                        upbit_data[key] = coin_data
                
                # API 요청 간 잠시 대기
                await asyncio.sleep(0.1)
            
            logger.info(f"✅ Upbit 데이터 수집 완료: {len(upbit_data)}개")
            self.stats['exchange_status']['Upbit'] = 'success'
            return upbit_data
                
        except Exception as e:
            logger.error(f"❌ Upbit 데이터 수집 실패: {e}")
            self.stats['exchange_status']['Upbit'] = 'failed'
            return {}
    
    async def collect_coinone_data(self) -> Dict[str, CoinData]:
        """Coinone 거래소 데이터 수집"""
        try:
            url = "https://api.coinone.co.kr/ticker_all"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Coinone API 응답 오류: {response.status}")
                    return {}
                
                data = await response.json()
                
                # 주요 코인만 선별
                major_coins = [
                    'btc', 'eth', 'sol', 'ada', 'xrp', 
                    'dot', 'avax', 'link', 'ltc', 'bch'
                ]
                
                coinone_data = {}
                for coin_key in major_coins:
                    if coin_key in data and isinstance(data[coin_key], dict):
                        coin = data[coin_key]
                        symbol = coin_key.upper() + '/KRW'
                        key = f"Coinone_{symbol}"
                        
                        # Coinone API는 변동률을 직접 제공하지 않으므로 0으로 설정
                        coin_data = CoinData(
                            symbol=symbol,
                            exchange='Coinone',
                            price=float(coin.get('last', 0)),
                            volume_24h=float(coin.get('volume', 0)),
                            change_24h=0.0,  # Coinone API 한계
                            currency='KRW',
                            timestamp=datetime.now().isoformat()
                        )
                        coinone_data[key] = coin_data
                
                logger.info(f"✅ Coinone 데이터 수집 완료: {len(coinone_data)}개")
                self.stats['exchange_status']['Coinone'] = 'success'
                return coinone_data
                
        except Exception as e:
            logger.error(f"❌ Coinone 데이터 수집 실패: {e}")
            self.stats['exchange_status']['Coinone'] = 'failed'
            return {}
    
    async def get_market_data_only(self) -> Dict[str, Dict]:
        """
        모든 거래소에서 시장 데이터 수집
        
        Returns:
            Dict[str, Dict]: 시장 데이터 (키: "거래소_심볼", 값: 코인 데이터)
        """
        if not self.session:
            async with self:
                return await self._collect_all_data()
        else:
            return await self._collect_all_data()
    
    async def _collect_all_data(self) -> Dict[str, Dict]:
        """내부: 모든 거래소 데이터 수집"""
        logger.info("🚀 다중 거래소 데이터 수집 시작")
        
        # 병렬로 모든 거래소 데이터 수집
        tasks = [
            self.collect_okx_data(),
            self.collect_upbit_data(),
            self.collect_coinone_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 통합
        all_data = {}
        for result in results:
            if isinstance(result, dict):
                for key, coin_data in result.items():
                    # CoinData를 dict로 변환
                    all_data[key] = {
                        'symbol': coin_data.symbol,
                        'exchange': coin_data.exchange,
                        'price': coin_data.price,
                        'volume_24h': coin_data.volume_24h,
                        'change_24h': coin_data.change_24h,
                        'currency': coin_data.currency,
                        'timestamp': coin_data.timestamp
                    }
            elif isinstance(result, Exception):
                logger.error(f"데이터 수집 중 예외 발생: {result}")
        
        # 통계 업데이트
        self.collected_data = all_data
        self.stats['total_collected'] = len(all_data)
        self.stats['last_update'] = datetime.now().isoformat()
        
        # 거래소별 통계 로깅
        exchange_stats = {}
        for key in all_data:
            exchange = key.split('_')[0]
            exchange_stats[exchange] = exchange_stats.get(exchange, 0) + 1
        
        logger.info(f"🎯 총 {len(all_data)}개 코인 데이터 수집 완료")
        logger.info(f"📊 거래소별 통계: {exchange_stats}")
        
        return all_data
    
    def get_stats(self) -> Dict[str, Any]:
        """수집 통계 반환"""
        return self.stats.copy()


# 싱글톤 인스턴스
backend_real_data_service = RealDataService()


# 편의 함수들
async def get_real_market_data() -> Dict[str, Dict]:
    """실제 시장 데이터 가져오기 (외부 사용용)"""
    async with backend_real_data_service as service:
        return await service.get_market_data_only()


async def test_real_data_service():
    """서비스 테스트 함수"""
    async with RealDataService() as service:
        data = await service.get_market_data_only()
        stats = service.get_stats()
        
        print(f"✅ 수집 완료: {len(data)}개 코인")
        print(f"📊 통계: {stats}")
        
        # 샘플 데이터 출력
        for i, (key, value) in enumerate(list(data.items())[:5]):
            print(f"{i+1}. {key}: {value['price']:,} {value['currency']}")


if __name__ == "__main__":
    # 직접 실행시 테스트
    asyncio.run(test_real_data_service())
