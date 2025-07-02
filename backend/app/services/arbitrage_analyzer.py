#!/usr/bin/env python3
"""
차익거래 분석기 (Arbitrage Analyzer)
거래소간 가격 차이 분석 및 김치 프리미엄 계산

주요 기능:
- 거래소간 실시간 가격 차이 계산
- 김치 프리미엄 추적 (한국 vs 해외)
- 차익거래 기회 탐지
- 수익률 계산 및 알림
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
import json
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    """가격 데이터 클래스"""
    symbol: str
    exchange: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None


@dataclass
class ArbitrageOpportunity:
    """차익거래 기회 클래스"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_percentage: float
    potential_profit: float
    volume_score: float
    confidence_score: float
    timestamp: datetime


@dataclass
class KimchiPremium:
    """김치 프리미엄 데이터"""
    symbol: str
    korean_price: float
    international_price: float
    premium_percentage: float
    korean_exchange: str
    international_exchange: str
    timestamp: datetime


class ArbitrageAnalyzer:
    """차익거래 분석기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 가격 데이터 저장소
        self.price_data: Dict[str, Dict[str, PriceData]] = {}  # symbol -> exchange -> price_data
        
        # 차익거래 기회 저장소
        self.arbitrage_opportunities: List[ArbitrageOpportunity] = []
        self.kimchi_premiums: List[KimchiPremium] = []
        
        # 설정
        self.min_spread_percentage = 0.5  # 최소 0.5% 스프레드
        self.max_opportunities = 100  # 최대 100개 기회 저장
        self.analysis_interval = 5  # 5초마다 분석
        
        # 거래소 분류
        self.korean_exchanges = {'upbit', 'coinone', 'bithumb'}
        self.international_exchanges = {'okx', 'binance', 'gateio', 'bybit'}
        
        # 통계
        self.stats = {
            'total_analyses': 0,
            'opportunities_found': 0,
            'max_spread_seen': 0.0,
            'avg_kimchi_premium': 0.0
        }
        
        # 실행 상태
        self.running = False
        self.analysis_task = None
    
    def update_price_data(self, symbol: str, exchange: str, price: float, 
                         volume: float, timestamp: datetime = None,
                         bid: float = None, ask: float = None):
        """가격 데이터 업데이트"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # 기본 심볼 추출 (정규화)
        base_symbol = self._extract_base_symbol(symbol, exchange)
        
        if base_symbol not in self.price_data:
            self.price_data[base_symbol] = {}
        
        self.price_data[base_symbol][exchange] = PriceData(
            symbol=symbol,  # 원래 심볼 유지
            exchange=exchange,
            price=price,
            volume=volume,
            timestamp=timestamp,
            bid=bid,
            ask=ask
        )
        
        # 오래된 데이터 정리 (5분 이상)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        for sym in list(self.price_data.keys()):
            for exch in list(self.price_data[sym].keys()):
                if self.price_data[sym][exch].timestamp < cutoff_time:
                    del self.price_data[sym][exch]
            
            # 빈 심볼 제거
            if not self.price_data[sym]:
                del self.price_data[sym]
    
    def normalize_symbol(self, symbol: str, from_exchange: str, to_exchange: str) -> str:
        """거래소간 심볼 표준화"""
        # 기본 심볼 추출
        if from_exchange == 'coinone':
            # Coinone: BTC -> BTC-USDT (OKX), KRW-BTC (Upbit)
            if to_exchange == 'okx':
                return f"{symbol}-USDT"
            elif to_exchange == 'upbit':
                return f"KRW-{symbol}"
        elif from_exchange == 'upbit':
            # Upbit: KRW-BTC -> BTC (Coinone), BTC-USDT (OKX)
            if symbol.startswith('KRW-'):
                base = symbol[4:]  # KRW- 제거
                if to_exchange == 'coinone':
                    return base
                elif to_exchange == 'okx':
                    return f"{base}-USDT"
        elif from_exchange == 'okx':
            # OKX: BTC-USDT -> BTC (Coinone), KRW-BTC (Upbit)
            if symbol.endswith('-USDT'):
                base = symbol[:-5]  # -USDT 제거
                if to_exchange == 'coinone':
                    return base
                elif to_exchange == 'upbit':
                    return f"KRW-{base}"
        
        return symbol
    
    def find_arbitrage_opportunities(self) -> List[ArbitrageOpportunity]:
        """차익거래 기회 탐지"""
        opportunities = []
        
        self.logger.debug(f"분석 시작: {len(self.price_data)}개 기본 심볼")
        
        for base_symbol, exchange_data in self.price_data.items():
            self.logger.debug(f"기본 심볼 {base_symbol}: {len(exchange_data)}개 거래소 ({list(exchange_data.keys())})")
            
            if len(exchange_data) < 2:
                continue
            
            # 모든 거래소 쌍 비교
            exchanges = list(exchange_data.keys())
            for i in range(len(exchanges)):
                for j in range(i + 1, len(exchanges)):
                    exchange1, exchange2 = exchanges[i], exchanges[j]
                    data1, data2 = exchange_data[exchange1], exchange_data[exchange2]
                    
                    self.logger.debug(f"비교: {base_symbol} {exchange1}({data1.price}) vs {exchange2}({data2.price})")
                    
                    # 스프레드 계산
                    if data1.price > data2.price:
                        buy_exchange, sell_exchange = exchange2, exchange1
                        buy_price, sell_price = data2.price, data1.price
                        buy_volume, sell_volume = data2.volume, data1.volume
                        buy_symbol, sell_symbol = data2.symbol, data1.symbol
                    else:
                        buy_exchange, sell_exchange = exchange1, exchange2
                        buy_price, sell_price = data1.price, data2.price
                        buy_volume, sell_volume = data1.volume, data2.volume
                        buy_symbol, sell_symbol = data1.symbol, data2.symbol
                    
                    # 가격 정규화 (원화 -> 달러 변환 등)
                    buy_price_normalized, sell_price_normalized = self._normalize_prices(
                        buy_price, sell_price, buy_exchange, sell_exchange
                    )
                    
                    self.logger.debug(f"정규화된 가격: {buy_price_normalized} -> {sell_price_normalized}")
                    
                    if buy_price_normalized <= 0 or sell_price_normalized <= 0:
                        continue
                    
                    spread_percentage = ((sell_price_normalized - buy_price_normalized) / buy_price_normalized) * 100
                    
                    self.logger.debug(f"스프레드: {spread_percentage:.2f}%")
                    
                    # 최소 스프레드 체크
                    if spread_percentage >= self.min_spread_percentage:
                        # 거래량 점수 계산
                        volume_score = min(buy_volume, sell_volume) / max(buy_volume, sell_volume) * 100 if max(buy_volume, sell_volume) > 0 else 0
                        
                        # 신뢰도 점수 계산
                        confidence_score = self._calculate_confidence_score(
                            data1.timestamp, data2.timestamp, volume_score, spread_percentage
                        )
                        
                        opportunity = ArbitrageOpportunity(
                            symbol=base_symbol,  # 기본 심볼 사용
                            buy_exchange=buy_exchange,
                            sell_exchange=sell_exchange,
                            buy_price=buy_price_normalized,
                            sell_price=sell_price_normalized,
                            spread_percentage=spread_percentage,
                            potential_profit=sell_price_normalized - buy_price_normalized,
                            volume_score=volume_score,
                            confidence_score=confidence_score,
                            timestamp=datetime.now()
                        )
                        
                        opportunities.append(opportunity)
                        self.logger.debug(f"기회 발견: {base_symbol} {spread_percentage:.2f}%")
        
        # 스프레드 순으로 정렬
        opportunities.sort(key=lambda x: x.spread_percentage, reverse=True)
        return opportunities[:20]  # 상위 20개만 반환
    
    def calculate_kimchi_premium(self) -> List[KimchiPremium]:
        """김치 프리미엄 계산"""
        kimchi_premiums = []
        
        for symbol, exchange_data in self.price_data.items():
            korean_data = []
            international_data = []
            
            # 한국 거래소와 해외 거래소 데이터 분리
            for exchange, data in exchange_data.items():
                if exchange in self.korean_exchanges:
                    korean_data.append(data)
                elif exchange in self.international_exchanges:
                    international_data.append(data)
            
            if not korean_data or not international_data:
                continue
            
            # 각 쌍에 대해 김치 프리미엄 계산
            for korean in korean_data:
                for international in international_data:
                    # 가격 정규화 (같은 기준으로 변환)
                    korean_price_usd = self._convert_to_usd(korean.price, korean.exchange)
                    international_price_usd = self._convert_to_usd(international.price, international.exchange)
                    
                    if korean_price_usd <= 0 or international_price_usd <= 0:
                        continue
                    
                    premium_percentage = ((korean_price_usd - international_price_usd) / international_price_usd) * 100
                    
                    kimchi_premium = KimchiPremium(
                        symbol=symbol,
                        korean_price=korean_price_usd,
                        international_price=international_price_usd,
                        premium_percentage=premium_percentage,
                        korean_exchange=korean.exchange,
                        international_exchange=international.exchange,
                        timestamp=datetime.now()
                    )
                    
                    kimchi_premiums.append(kimchi_premium)
        
        return kimchi_premiums
    
    def _symbols_compatible(self, symbol: str, exchange1: str, exchange2: str) -> bool:
        """심볼 호환성 체크 (개선된 버전)"""
        base1 = self._extract_base_symbol(symbol, exchange1)
        base2 = self._extract_base_symbol(symbol, exchange2)
        
        self.logger.debug(f"심볼 호환성 체크: {symbol} -> {base1}({exchange1}) vs {base2}({exchange2})")
        
        return base1 == base2
    
    def _extract_base_symbol(self, symbol: str, exchange: str) -> str:
        """기본 심볼 추출 (개선된 버전)"""
        if exchange == 'coinone':
            # Coinone: BTC, ETH, DOGE 등 단순 형태
            return symbol.upper()
        elif exchange == 'upbit':
            # Upbit: KRW-BTC, KRW-ETH 등
            if symbol.startswith('KRW-'):
                return symbol[4:].upper()  # KRW- 제거
            else:
                return symbol.upper()
        elif exchange == 'okx':
            # OKX: BTC-USDT, ETH-USDT 등
            if symbol.endswith('-USDT'):
                return symbol[:-5].upper()  # -USDT 제거
            elif '-' in symbol:
                return symbol.split('-')[0].upper()  # 첫 번째 부분
            else:
                return symbol.upper()
        else:
            # 기타 거래소
            return symbol.replace('-', '').replace('_', '').replace('/', '').upper()
    
    def _normalize_prices(self, price1: float, price2: float, 
                         exchange1: str, exchange2: str) -> Tuple[float, float]:
        """가격 정규화 (USD 기준)"""
        price1_usd = self._convert_to_usd(price1, exchange1)
        price2_usd = self._convert_to_usd(price2, exchange2)
        return price1_usd, price2_usd
    
    def _convert_to_usd(self, price: float, exchange: str) -> float:
        """USD로 가격 변환"""
        if exchange in self.korean_exchanges:
            # KRW -> USD (대략적인 환율 1300 적용)
            return price / 1300.0
        else:
            # 이미 USD 기준
            return price
    
    def _calculate_confidence_score(self, timestamp1: datetime, timestamp2: datetime,
                                  volume_score: float, spread_percentage: float) -> float:
        """신뢰도 점수 계산"""
        # 시간 차이 점수 (최대 60초 차이까지 허용)
        time_diff = abs((timestamp1 - timestamp2).total_seconds())
        time_score = max(0, 100 - (time_diff / 60) * 100)
        
        # 거래량 점수 (이미 계산됨)
        
        # 스프레드 점수 (높을수록 좋지만 너무 높으면 의심)
        spread_score = min(spread_percentage * 10, 100)
        if spread_percentage > 10:  # 10% 이상은 의심스러움
            spread_score *= 0.5
        
        # 종합 점수
        confidence_score = (time_score * 0.4 + volume_score * 0.3 + spread_score * 0.3)
        return min(confidence_score, 100)
    
    async def start(self):
        """분석 시작"""
        self.running = True
        self.analysis_task = asyncio.create_task(self._analysis_loop())
        self.logger.info("🔍 차익거래 분석기 시작")
    
    async def stop(self):
        """분석 중지"""
        self.running = False
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        self.logger.info("🛑 차익거래 분석기 중지")
    
    async def _analysis_loop(self):
        """주기적 분석 루프"""
        while self.running:
            try:
                await asyncio.sleep(self.analysis_interval)
                
                if not self.running:
                    break
                
                # 차익거래 기회 분석
                opportunities = self.find_arbitrage_opportunities()
                self.arbitrage_opportunities = opportunities[:self.max_opportunities]
                
                # 김치 프리미엄 분석
                kimchi_premiums = self.calculate_kimchi_premium()
                self.kimchi_premiums = kimchi_premiums[:self.max_opportunities]
                
                # 통계 업데이트
                self.stats['total_analyses'] += 1
                if opportunities:
                    self.stats['opportunities_found'] += len(opportunities)
                    max_spread = max(opp.spread_percentage for opp in opportunities)
                    self.stats['max_spread_seen'] = max(self.stats['max_spread_seen'], max_spread)
                
                if kimchi_premiums:
                    avg_premium = sum(abs(kp.premium_percentage) for kp in kimchi_premiums) / len(kimchi_premiums)
                    self.stats['avg_kimchi_premium'] = avg_premium
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"분석 루프 오류: {e}")
    
    async def _log_analysis_results(self, opportunities: List[ArbitrageOpportunity],
                                  kimchi_premiums: List[KimchiPremium]):
        """분석 결과 로깅"""
        if opportunities:
            # 상위 3개 차익거래 기회 로깅
            self.logger.info(f"💰 차익거래 기회 {len(opportunities)}개 발견!")
            for i, opp in enumerate(opportunities[:3]):
                self.logger.info(
                    f"  {i+1}. {opp.symbol}: {opp.buy_exchange}(${opp.buy_price:.2f}) → "
                    f"{opp.sell_exchange}(${opp.sell_price:.2f}) "
                    f"| 스프레드: {opp.spread_percentage:.2f}% "
                    f"| 신뢰도: {opp.confidence_score:.1f}%"
                )
        
        if kimchi_premiums:
            # 김치 프리미엄 로깅
            significant_premiums = [kp for kp in kimchi_premiums if abs(kp.premium_percentage) > 1.0]
            if significant_premiums:
                self.logger.info(f"🌶️ 김치 프리미엄 {len(significant_premiums)}개 감지!")
                for kp in significant_premiums[:3]:
                    direction = "프리미엄" if kp.premium_percentage > 0 else "디스카운트"
                    self.logger.info(
                        f"  {kp.symbol}: {kp.korean_exchange} vs {kp.international_exchange} "
                        f"| {direction}: {abs(kp.premium_percentage):.2f}%"
                    )
    
    def get_top_opportunities(self, limit: int = 10) -> List[ArbitrageOpportunity]:
        """상위 차익거래 기회 반환"""
        return self.arbitrage_opportunities[:limit]
    
    def get_kimchi_premiums(self, limit: int = 10) -> List[KimchiPremium]:
        """김치 프리미엄 반환"""
        return self.kimchi_premiums[:limit]
    
    def get_stats(self) -> Dict:
        """통계 반환"""
        return {
            'price_data_count': sum(len(exchanges) for exchanges in self.price_data.values()),
            'symbols_tracked': len(self.price_data),
            **self.stats
        }


# 전역 인스턴스
arbitrage_analyzer = ArbitrageAnalyzer()


async def test_arbitrage_analyzer():
    """차익거래 분석기 테스트"""
    
    # 테스트 데이터 추가
    analyzer = ArbitrageAnalyzer()
    
    # OKX 데이터 (USD)
    analyzer.update_price_data('BTC-USDT', 'okx', 96000.0, 1234.56)
    analyzer.update_price_data('ETH-USDT', 'okx', 3400.0, 2345.67)
    
    # Upbit 데이터 (KRW)
    analyzer.update_price_data('KRW-BTC', 'upbit', 125000000.0, 987.65)  # 125M KRW = ~96K USD
    analyzer.update_price_data('KRW-ETH', 'upbit', 4420000.0, 1876.54)    # 4.42M KRW = ~3.4K USD
    
    # Coinone 데이터 (KRW)
    analyzer.update_price_data('BTC', 'coinone', 126500000.0, 543.21)     # 126.5M KRW = ~97.3K USD
    analyzer.update_price_data('ETH', 'coinone', 4550000.0, 876.43)       # 4.55M KRW = ~3.5K USD
    
    # 분석 실행
    opportunities = analyzer.find_arbitrage_opportunities()
    kimchi_premiums = analyzer.calculate_kimchi_premium()
    
    print("🔍 차익거래 분석 결과:")
    for opp in opportunities:
        print(f"  {opp.symbol}: {opp.spread_percentage:.2f}% 스프레드")
    
    print("\n🌶️ 김치 프리미엄 결과:")
    for kp in kimchi_premiums:
        print(f"  {kp.symbol}: {kp.premium_percentage:.2f}% 프리미엄")


if __name__ == "__main__":
    asyncio.run(test_arbitrage_analyzer())
