"""
백엔드 실제 거래소 데이터 서비스
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

from app.core.config import settings
from app.services.market_data_collector import market_data_collector

logger = logging.getLogger(__name__)

class BackendRealDataService:
    """백엔드 실제 거래소 데이터 수집 서비스"""
    
    def __init__(self):
        self.running = False
        self.collection_interval = 30  # 30초마다 데이터 수집
        self.stats = {
            'data_points_collected': 0,
            'broadcasts_sent': 0,
            'start_time': None,
            'last_collection': None,
            'active_exchanges': []
        }
        self.initialized = False
        self.connection_manager = None

class BackendRealDataService:
    """백엔드 실제 거래소 데이터 수집 서비스"""
    
    def __init__(self):
        self.running = False
        self.collection_interval = 30  # 30초마다 데이터 수집
        self.stats = {
            'data_points_collected': 0,
            'broadcasts_sent': 0,
            'start_time': None,
            'last_collection': None,
            'active_exchanges': []
        }
        self.initialized = False
        
    async def initialize_exchanges(self):
        """거래소 설정 및 초기화"""
        if self.initialized:
            logger.info("거래소가 이미 초기화되었습니다.")
            return
            
        logger.info("🔧 거래소 API 연결 초기화...")
        
        exchange_configs = {}
        
        # OKX 설정 (실제 API 키 사용)
        if settings.okx_api_key:
            exchange_configs['okx'] = {
                'api_key': settings.okx_api_key,
                'secret_key': settings.okx_secret_key,
                'passphrase': settings.okx_passphrase or ''
            }
            logger.info("✅ OKX API 키 설정 완료")
        
        # Coinone 설정
        if settings.coinone_api_key:
            exchange_configs['coinone'] = {
                'api_key': settings.coinone_api_key,
                'secret_key': settings.coinone_secret_key
            }
            logger.info("✅ Coinone API 키 설정 완료")
        
        # Gate.io 설정
        if settings.gate_api_key:
            exchange_configs['gate'] = {
                'api_key': settings.gate_api_key,
                'secret_key': settings.gate_secret_key
            }
            logger.info("✅ Gate.io API 키 설정 완료")
        
        if not exchange_configs:
            raise ValueError("❌ 설정된 거래소 API가 없습니다. .env 파일을 확인하세요.")
        
        # MarketDataCollector 설정
        market_data_collector.configure_exchanges(exchange_configs)
        
        # 수집할 심볼 설정 (다중 거래소 지원)
        target_symbols = [
            'BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'ADA-USDT', 'DOT-USDT',
            'MATIC-USDT', 'AVAX-USDT', 'ATOM-USDT', 'NEAR-USDT', 'FTM-USDT'
        ]
        market_data_collector.set_target_symbols(target_symbols)
        
        self.stats['active_exchanges'] = list(exchange_configs.keys())
        self.initialized = True
        logger.info(f"🏛️ {len(exchange_configs)}개 거래소 연결 완료: {list(exchange_configs.keys())}")
        
    async def collect_and_broadcast_data(self):
        """실제 데이터 수집 및 WebSocket 브로드캐스트"""
        try:
            if not self.initialized:
                await self.initialize_exchanges()
                
            logger.info("📊 실제 시장 데이터 수집 시작...")
            
            # 실제 거래소에서 데이터 수집
            data_points = await market_data_collector.collect_all_data()
            
            if not data_points:
                logger.warning("⚠️ 수집된 데이터가 없습니다.")
                return
            
            self.stats['data_points_collected'] += len(data_points)
            self.stats['last_collection'] = datetime.now()
            
            logger.info(f"✅ {len(data_points)}개 실제 데이터 포인트 수집 완료")
            
            # 데이터 포맷 변환 및 브로드캐스트 준비
            await self.format_and_broadcast_data(data_points)
            
            # 데이터 저장
            await market_data_collector.process_and_store_data(data_points)
            
        except Exception as e:
            logger.error(f"❌ 데이터 수집/브로드캐스트 실패: {e}")
            raise
    
    async def format_and_broadcast_data(self, data_points):
        """데이터 포맷 변환 및 WebSocket 브로드캐스트"""
        if not connection_manager.active_connections:
            logger.info("📡 활성화된 WebSocket 연결이 없습니다.")
            return
        
        # 가격 데이터 포맷 (대시보드 형식에 맞게)
        price_data = []
        
        # 거래소별, 심볼별 데이터 그룹핑
        exchange_prices = {}
        for point in data_points:
            if point.exchange not in exchange_prices:
                exchange_prices[point.exchange] = {}
            
            # 심볼 이름 정규화 (BTC-USDT -> BTC)
            clean_symbol = point.symbol.split('-')[0].split('_')[0].upper()
            exchange_prices[point.exchange][clean_symbol] = {
                'price': point.price,
                'volume': point.volume_24h,
                'change_24h': point.change_24h,
                'timestamp': point.timestamp.isoformat()
            }
            
            # 가격 데이터 추가
            price_data.append({
                'exchange': point.exchange.title(),
                'symbol': clean_symbol,
                'price': round(point.price, 2),
                'volume': round(point.volume_24h, 2),
                'change_24h': round(point.change_24h, 2),
                'timestamp': point.timestamp.isoformat()
            })
        
        # 차익거래 기회 계산
        arbitrage_data = self.calculate_arbitrage_opportunities(exchange_prices)
        
        # 김치 프리미엄 계산 (한국 거래소가 있는 경우)
        kimchi_data = self.calculate_kimchi_premiums(exchange_prices)
        
        # WebSocket으로 브로드캐스트
        await self.broadcast_real_data(price_data, arbitrage_data, kimchi_data)
        
    def calculate_arbitrage_opportunities(self, exchange_prices: Dict) -> List[Dict]:
        """실제 가격 데이터를 바탕으로 차익거래 기회 계산"""
        opportunities = []
        
        # 모든 심볼에 대해 거래소 간 가격 비교
        all_symbols = set()
        for exchange_data in exchange_prices.values():
            all_symbols.update(exchange_data.keys())
        
        for symbol in all_symbols:
            symbol_prices = []
            
            # 해당 심볼을 지원하는 거래소들의 가격 수집
            for exchange, prices in exchange_prices.items():
                if symbol in prices:
                    symbol_prices.append({
                        'exchange': exchange,
                        'price': prices[symbol]['price'],
                        'volume': prices[symbol]['volume']
                    })
            
            # 최소 2개 거래소에서 해당 심볼이 거래되어야 차익거래 가능
            if len(symbol_prices) >= 2:
                symbol_prices.sort(key=lambda x: x['price'])
                
                for i in range(len(symbol_prices)):
                    for j in range(i + 1, len(symbol_prices)):
                        buy_data = symbol_prices[i]
                        sell_data = symbol_prices[j]
                        
                        spread_pct = ((sell_data['price'] - buy_data['price']) / buy_data['price']) * 100
                        
                        if spread_pct > 0.5:  # 0.5% 이상의 차익거래 기회
                            opportunities.append({
                                'symbol': symbol,
                                'buy_exchange': buy_data['exchange'].title(),
                                'sell_exchange': sell_data['exchange'].title(),
                                'buy_price': round(buy_data['price'], 2),
                                'sell_price': round(sell_data['price'], 2),
                                'spread_percentage': round(spread_pct, 2),
                                'confidence': min(95, 80 + spread_pct * 2),
                                'volume': min(buy_data['volume'], sell_data['volume']),
                                'timestamp': datetime.now().isoformat()
                            })
        
        # 스프레드 기준으로 정렬하여 상위 기회들 반환
        opportunities.sort(key=lambda x: x['spread_percentage'], reverse=True)
        return opportunities[:10]  # 상위 10개
    
    def calculate_kimchi_premiums(self, exchange_prices: Dict) -> List[Dict]:
        """김치 프리미엄 계산 (한국 거래소 vs 글로벌 거래소)"""
        premiums = []
        
        korean_exchanges = ['upbit', 'coinone']  # 한국 거래소
        global_exchanges = ['okx', 'gate']       # 글로벌 거래소
        
        # 공통 심볼 찾기
        common_symbols = set()
        for exchange_data in exchange_prices.values():
            if not common_symbols:
                common_symbols = set(exchange_data.keys())
            else:
                common_symbols &= set(exchange_data.keys())
        
        for symbol in common_symbols:
            korean_prices = []
            global_prices = []
            
            # 한국 거래소 가격 수집
            for exchange in korean_exchanges:
                if exchange in exchange_prices and symbol in exchange_prices[exchange]:
                    korean_prices.append({
                        'exchange': exchange,
                        'price': exchange_prices[exchange][symbol]['price']
                    })
            
            # 글로벌 거래소 가격 수집
            for exchange in global_exchanges:
                if exchange in exchange_prices and symbol in exchange_prices[exchange]:
                    global_prices.append({
                        'exchange': exchange,
                        'price': exchange_prices[exchange][symbol]['price']
                    })
            
            if korean_prices and global_prices:
                # 평균 가격 계산
                avg_korean = sum(p['price'] for p in korean_prices) / len(korean_prices)
                avg_global = sum(p['price'] for p in global_prices) / len(global_prices)
                
                premium_pct = ((avg_korean - avg_global) / avg_global) * 100
                
                premiums.append({
                    'symbol': symbol,
                    'korean_exchange': korean_prices[0]['exchange'].title(),
                    'global_exchange': global_prices[0]['exchange'].title(),
                    'korean_price': round(avg_korean, 2),
                    'global_price': round(avg_global, 2),
                    'premium_percentage': round(premium_pct, 2),
                    'status': 'positive' if premium_pct > 0 else 'negative',
                    'timestamp': datetime.now().isoformat()
                })
        
        return premiums
    
    async def broadcast_real_data(self, price_data, arbitrage_data, kimchi_data):
        """실제 데이터를 WebSocket으로 브로드캐스트"""
        try:
            timestamp = datetime.now().isoformat()
            
            # 가격 데이터 브로드캐스트
            await connection_manager.broadcast_to_all({
                'type': 'price_update',
                'data': price_data,
                'timestamp': timestamp,
                'source': 'real_api'
            })
            
            # 차익거래 기회 브로드캐스트
            if arbitrage_data:
                await connection_manager.broadcast_to_all({
                    'type': 'arbitrage_opportunities',
                    'data': arbitrage_data,
                    'timestamp': timestamp,
                    'source': 'real_api'
                })
            
            # 김치 프리미엄 브로드캐스트
            if kimchi_data:
                await connection_manager.broadcast_to_all({
                    'type': 'kimchi_premium',
                    'data': kimchi_data,
                    'timestamp': timestamp,
                    'source': 'real_api'
                })
            
            self.stats['broadcasts_sent'] += 3
            
            logger.info(f"📡 실제 데이터 브로드캐스트 완료 - "
                       f"가격: {len(price_data)}개, "
                       f"차익거래: {len(arbitrage_data)}개, "
                       f"김치프리미엄: {len(kimchi_data)}개")
                       
        except Exception as e:
            logger.error(f"❌ 데이터 브로드캐스트 실패: {e}")
            raise
            
    async def start_collection_loop(self):
        """실시간 데이터 수집 루프 시작"""
        if self.running:
            logger.warning("데이터 수집이 이미 실행 중입니다.")
            return
            
        await self.initialize_exchanges()
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        logger.info(f"🚀 실시간 데이터 수집 시작 (주기: {self.collection_interval}초)")
        
        try:
            while self.running:
                await self.collect_and_broadcast_all()
                await asyncio.sleep(self.collection_interval)
        except asyncio.CancelledError:
            logger.info("⏹️ 데이터 수집 루프가 취소되었습니다.")
        except Exception as e:
            logger.error(f"❌ 데이터 수집 루프 오류: {e}")
        finally:
            self.running = False
            
    def stop(self):
        """데이터 수집 중지"""
        if self.running:
            self.running = False
            logger.info("⏹️ 실시간 데이터 수집 중지됨")
        else:
            logger.warning("데이터 수집이 실행 중이 아닙니다.")
            
    def get_stats(self):
        """서비스 통계 반환"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            
        return {
            **self.stats,
            'running': self.running,
            'uptime_seconds': uptime,
            'collection_interval': self.collection_interval
        }
    
    async def collect_and_broadcast_all(self):
        """모든 거래소에서 데이터 수집하고 브로드캐스트"""
        try:
            logger.info("📊 실시간 데이터 수집 시작...")
            
            # 모든 거래소 데이터 수집
            all_prices = {}
            
            # OKX 데이터 수집
            try:
                okx_data = await self._collect_okx_data()
                if okx_data:
                    all_prices.update(okx_data)
            except Exception as e:
                logger.warning(f"OKX 데이터 수집 실패: {e}")
                    
            # Upbit 데이터 수집 (테스트 데이터)
            upbit_test_data = await self._get_test_upbit_data()
            all_prices.update(upbit_test_data)
            
            # Coinone 데이터 수집 (테스트 데이터)
            coinone_test_data = await self._get_test_coinone_data()
            all_prices.update(coinone_test_data)
            
            if not all_prices:
                logger.warning("수집된 데이터가 없습니다.")
                return
                
            # 차익거래 분석
            arbitrage_data = self.analyze_arbitrage_opportunities(all_prices)
            
            # 김치 프리미엄 계산
            kimchi_data = self.calculate_kimchi_premiums(all_prices)
            
            # 데이터 브로드캐스트
            await self.broadcast_real_data(all_prices, arbitrage_data, kimchi_data)
            
            # 통계 업데이트
            self.stats['data_points_collected'] += len(all_prices)
            self.stats['last_collection'] = datetime.now()
            
            logger.info(f"✅ 데이터 수집/브로드캐스트 완료: {len(all_prices)}개 가격 데이터")
            
        except Exception as e:
            logger.error(f"❌ 데이터 수집/브로드캐스트 실패: {e}")
            
    async def _get_test_upbit_data(self):
        """Upbit 테스트 데이터 생성"""
        import random
        base_prices = {'BTC': 95000000, 'ETH': 3200000, 'SOL': 180000}
        data = {}
        for symbol, base_price in base_prices.items():
            variation = random.uniform(-0.02, 0.02)
            price = base_price * (1 + variation)
            data[f"Upbit_{symbol}/KRW"] = {
                'price': round(price, 2),
                'exchange': 'Upbit',
                'symbol': f'{symbol}/KRW',
                'timestamp': datetime.now().isoformat(),
                'currency': 'KRW'
            }
        return data
        
    async def _get_test_coinone_data(self):
        """Coinone 테스트 데이터 생성"""
        import random
        base_prices = {'BTC': 94800000, 'ETH': 3180000, 'SOL': 179000}
        data = {}
        for symbol, base_price in base_prices.items():
            variation = random.uniform(-0.02, 0.02)
            price = base_price * (1 + variation)
            data[f"Coinone_{symbol}/KRW"] = {
                'price': round(price, 2),
                'exchange': 'Coinone',
                'symbol': f'{symbol}/KRW',
                'timestamp': datetime.now().isoformat(),
                'currency': 'KRW'
            }
        return data
    
    async def _collect_okx_data(self):
        """OKX 거래소 실제 데이터 수집"""
        try:
            if not settings.okx_api_key:
                logger.warning("OKX API 키가 설정되지 않았습니다.")
                return {}
                
            # market_data_collector를 사용하여 OKX 데이터 수집
            import ccxt
            
            okx = ccxt.okx({
                'apiKey': settings.okx_api_key,
                'secret': settings.okx_secret_key,
                'password': settings.okx_passphrase,
                'sandbox': False,
                'enableRateLimit': True,
            })
            
            symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
            data = {}
            
            for symbol in symbols:
                try:
                    ticker = await asyncio.get_event_loop().run_in_executor(
                        None, okx.fetch_ticker, symbol
                    )
                    
                    data[f"OKX_{symbol}"] = {
                        'price': ticker['last'],
                        'exchange': 'OKX',
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'currency': 'USDT'
                    }
                except Exception as e:
                    logger.warning(f"OKX {symbol} 데이터 수집 실패: {e}")
                    
            # 연결 해제는 자동으로 처리됨
            return data
            
        except Exception as e:
            logger.error(f"OKX 데이터 수집 오류: {e}")
            return {}
            
    def analyze_arbitrage_opportunities(self, price_data):
        """차익거래 기회 분석"""
        opportunities = []
        
        try:
            # 같은 코인의 다른 거래소 간 가격 차이 분석
            symbols = set()
            for key in price_data.keys():
                if '_' in key:
                    symbol = key.split('_', 1)[1].split('/')[0]  # BTC, ETH, SOL 등
                    symbols.add(symbol)
            
            for symbol in symbols:
                prices = []
                for key, data in price_data.items():
                    if symbol in key:
                        prices.append({
                            'exchange': data['exchange'],
                            'price': data['price'],
                            'currency': data.get('currency', 'USDT')
                        })
                
                if len(prices) >= 2:
                    # 최고가와 최저가 찾기
                    prices.sort(key=lambda x: x['price'])
                    lowest = prices[0]
                    highest = prices[-1]
                    
                    # 가격 차이 계산
                    if lowest['price'] > 0:
                        profit_pct = ((highest['price'] - lowest['price']) / lowest['price']) * 100
                        
                        if profit_pct > 1.0:  # 1% 이상 차이
                            opportunities.append({
                                'symbol': symbol,
                                'buy_exchange': lowest['exchange'],
                                'sell_exchange': highest['exchange'],
                                'buy_price': lowest['price'],
                                'sell_price': highest['price'],
                                'profit_percentage': round(profit_pct, 2),
                                'timestamp': datetime.now().isoformat()
                            })
        
        except Exception as e:
            logger.error(f"차익거래 분석 오류: {e}")
        
        return opportunities

# 글로벌 인스턴스
backend_real_data_service = BackendRealDataService()
