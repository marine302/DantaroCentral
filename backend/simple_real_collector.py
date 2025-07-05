#!/usr/bin/env python3
"""
간단한 실제 데이터 수집기 - HTTP API 기반
기존에 이미 검증된 HTTP API들을 활용
"""

import asyncio
import aiohttp
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRealDataCollector:
    """간단한 실제 데이터 수집기"""
    
    def __init__(self):
        self.session = None
        self.collected_data = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def collect_upbit_data(self):
        """Upbit 데이터 수집 (이미 검증됨)"""
        try:
            url = "https://api.upbit.com/v1/ticker"
            params = {
                'markets': 'KRW-BTC,KRW-ETH,KRW-SOL,KRW-ADA,KRW-XRP,KRW-DOT,KRW-AVAX,KRW-LINK,KRW-UNI,KRW-MATIC'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    upbit_data = {}
                    for coin in data:
                        symbol = coin['market'].replace('KRW-', '') + '/KRW'
                        key = f"Upbit_{symbol}"
                        
                        upbit_data[key] = {
                            'symbol': symbol,
                            'exchange': 'Upbit',
                            'price': coin['trade_price'],
                            'volume_24h': coin['acc_trade_volume_24h'],
                            'change_24h': coin['signed_change_rate'] * 100,
                            'currency': 'KRW',
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    logger.info(f"✅ Upbit 데이터 수집 완료: {len(upbit_data)}개")
                    return upbit_data
                    
        except Exception as e:
            logger.error(f"❌ Upbit 데이터 수집 실패: {e}")
            return {}
    
    async def collect_coinone_data(self):
        """Coinone 데이터 수집 (이미 검증됨)"""
        try:
            url = "https://api.coinone.co.kr/ticker_all"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    coinone_data = {}
                    # BTC, ETH, SOL 등 주요 코인만
                    major_coins = ['btc', 'eth', 'sol', 'ada', 'xrp', 'dot', 'avax', 'link']
                    
                    for coin_key in major_coins:
                        if coin_key in data:
                            coin = data[coin_key]
                            symbol = coin_key.upper() + '/KRW'
                            key = f"Coinone_{symbol}"
                            
                            coinone_data[key] = {
                                'symbol': symbol,
                                'exchange': 'Coinone',
                                'price': float(coin.get('last', 0)),
                                'volume_24h': float(coin.get('volume', 0)),
                                'change_24h': 0,  # Coinone API에서 직접 제공하지 않음
                                'currency': 'KRW',
                                'timestamp': datetime.now().isoformat()
                            }
                    
                    logger.info(f"✅ Coinone 데이터 수집 완료: {len(coinone_data)}개")
                    return coinone_data
                    
        except Exception as e:
            logger.error(f"❌ Coinone 데이터 수집 실패: {e}")
            return {}
    
    async def collect_okx_data(self):
        """OKX 데이터 수집 (공개 API)"""
        try:
            url = "https://www.okx.com/api/v5/market/tickers"
            params = {'instType': 'SPOT'}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('code') == '0':
                        okx_data = {}
                        # 주요 USDT 페어만
                        major_pairs = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'ADA-USDT', 'XRP-USDT']
                        
                        for ticker in data['data']:
                            if ticker['instId'] in major_pairs:
                                symbol = ticker['instId'].replace('-', '/') 
                                key = f"OKX_{symbol}"
                                
                                okx_data[key] = {
                                    'symbol': symbol,
                                    'exchange': 'OKX',
                                    'price': float(ticker.get('last', 0)),
                                    'volume_24h': float(ticker.get('volCcy24h', 0)),
                                    'change_24h': float(ticker.get('chgUtc0', 0)) * 100,
                                    'currency': 'USD',
                                    'timestamp': datetime.now().isoformat()
                                }
                        
                        logger.info(f"✅ OKX 데이터 수집 완료: {len(okx_data)}개")
                        return okx_data
                    
        except Exception as e:
            logger.error(f"❌ OKX 데이터 수집 실패: {e}")
            return {}
    
    async def collect_all_data(self):
        """모든 거래소 데이터 수집"""
        all_data = {}
        
        # 병렬로 모든 거래소 데이터 수집
        tasks = [
            self.collect_upbit_data(),
            self.collect_coinone_data(),
            self.collect_okx_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                all_data.update(result)
            elif isinstance(result, Exception):
                logger.error(f"데이터 수집 중 오류: {result}")
        
        self.collected_data = all_data
        logger.info(f"🎯 총 {len(all_data)}개 코인 데이터 수집 완료")
        
        # 거래소별 통계
        exchange_stats = {}
        for key in all_data:
            exchange = key.split('_')[0]
            exchange_stats[exchange] = exchange_stats.get(exchange, 0) + 1
        
        logger.info(f"📊 거래소별 수집 통계: {exchange_stats}")
        return all_data

async def test_real_data_collection():
    """실제 데이터 수집 테스트"""
    async with SimpleRealDataCollector() as collector:
        while True:
            data = await collector.collect_all_data()
            
            # 샘플 출력
            if data:
                print("\n=== 실제 수집 데이터 샘플 ===")
                for i, (key, value) in enumerate(list(data.items())[:5]):
                    print(f"{i+1}. {key}: {value['price']:,} {value['currency']} (거래량: {value['volume_24h']:,.0f})")
                print(f"총 {len(data)}개 코인")
            
            await asyncio.sleep(30)  # 30초마다 수집

if __name__ == "__main__":
    asyncio.run(test_real_data_collection())
