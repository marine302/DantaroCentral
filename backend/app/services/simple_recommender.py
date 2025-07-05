"""
Simple Volume-based Recommendation System
거래량 기반 단순 추천 시스템 - 사용자 서버용 실용적 접근
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleVolumeRecommender:
    """
    단순 거래량 기반 추천 시스템
    - 거래량 많은 순서대로 코인 선별
    - 나중에 다른 기준 추가 가능하도록 확장성 고려
    """
    
    def __init__(self):
        self.recommendation_criteria = "volume"  # 나중에 변경 가능
        self.min_volume_threshold = 1000000  # 최소 거래량 (1M)
        
    async def get_top_coins_by_volume(self, market_data: Dict[str, Dict], top_n: int = 50) -> List[Dict]:
        """
        거래량 기준 상위 코인 선별
        
        Args:
            market_data: 전체 시장 데이터
            top_n: 반환할 코인 수
            
        Returns:
            거래량 순 상위 코인 리스트
        """
        try:
            logger.info(f"거래량 기반 상위 {top_n}개 코인 선별 시작 (총 {len(market_data)}개 코인)")
            
            # 데이터 정리 및 필터링
            valid_coins = []
            for key, coin_data in market_data.items():
                try:
                    volume = coin_data.get('volume_24h', 0)
                    price = coin_data.get('price', 0)
                    symbol = coin_data.get('symbol', key)
                    exchange = coin_data.get('exchange', 'Unknown')
                    
                    # 최소 거래량 필터
                    if volume >= self.min_volume_threshold and price > 0:
                        # 저점 정보 계산 (단순히 현재가의 95%)
                        support_level = price * 0.95
                        resistance_level = price * 1.05
                        
                        coin_info = {
                            'symbol': symbol.replace('/USDT', '').replace('/KRW', ''),
                            'full_symbol': symbol,
                            'exchange': exchange,
                            'current_price': price,
                            'volume_24h': volume,
                            'change_24h': coin_data.get('change_24h', 0),
                            'currency': coin_data.get('currency', 'USD'),
                            'timestamp': coin_data.get('timestamp', datetime.now().isoformat()),
                            
                            # 저점/고점 정보 (사용자 서버용)
                            'support_level': support_level,
                            'resistance_level': resistance_level,
                            'entry_price_suggestion': price * 0.98,  # 진입 추천가
                            'take_profit_suggestion': price * 1.03,  # 익절 추천가
                            'stop_loss_suggestion': price * 0.97,   # 손절 추천가
                            
                            # 추천 메타데이터
                            'recommendation_reason': 'high_volume',
                            'volume_rank': 0,  # 나중에 설정
                            'is_recommended': True,
                            'recommendation_score': 0,  # 나중에 계산
                            'last_updated': datetime.now().isoformat()
                        }
                        
                        valid_coins.append(coin_info)
                        
                except Exception as e:
                    logger.warning(f"코인 데이터 처리 오류 ({key}): {e}")
                    continue
            
            # 거래량 기준 정렬
            valid_coins.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            # 순위 설정 및 점수 계산
            top_coins = valid_coins[:top_n]
            for i, coin in enumerate(top_coins):
                coin['volume_rank'] = i + 1
                # 간단한 점수 계산 (1위 = 100점, 순위별로 감점)
                coin['recommendation_score'] = max(0, 100 - (i * 2))
            
            logger.info(f"✅ 거래량 기준 상위 {len(top_coins)}개 코인 선별 완료")
            
            # 거래소별 통계 로깅
            exchange_stats = {}
            for coin in top_coins:
                exchange = coin['exchange']
                exchange_stats[exchange] = exchange_stats.get(exchange, 0) + 1
            
            logger.info(f"거래소별 추천 코인 분포: {exchange_stats}")
            
            return top_coins
            
        except Exception as e:
            logger.error(f"거래량 기반 추천 생성 실패: {e}")
            return []
    
    async def get_recommendations_by_exchange(self, market_data: Dict[str, Dict], top_n: int = 50) -> Dict[str, List[Dict]]:
        """
        거래소별로 추천 코인 분리하여 반환
        
        Returns:
            {
                'OKX': [...],
                'Upbit': [...], 
                'Coinone': [...]
            }
        """
        try:
            all_recommendations = await self.get_top_coins_by_volume(market_data, top_n * 3)  # 여유있게 가져오기
            
            exchange_recommendations = {
                'OKX': [],
                'Upbit': [],
                'Coinone': []
            }
            
            # 거래소별로 분류 (각 거래소당 최대 top_n개)
            for coin in all_recommendations:
                exchange = coin['exchange']
                if exchange in exchange_recommendations:
                    if len(exchange_recommendations[exchange]) < top_n:
                        exchange_recommendations[exchange].append(coin)
            
            logger.info(f"거래소별 추천 코인 분류 완료: "
                       f"OKX={len(exchange_recommendations['OKX'])}, "
                       f"Upbit={len(exchange_recommendations['Upbit'])}, "
                       f"Coinone={len(exchange_recommendations['Coinone'])}")
            
            return exchange_recommendations
            
        except Exception as e:
            logger.error(f"거래소별 추천 분류 실패: {e}")
            return {'OKX': [], 'Upbit': [], 'Coinone': []}
    
    def get_stats(self) -> Dict[str, Any]:
        """추천 시스템 통계 정보"""
        return {
            'criteria': self.recommendation_criteria,
            'min_volume_threshold': self.min_volume_threshold,
            'last_updated': datetime.now().isoformat()
        }
