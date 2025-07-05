#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DantaroEnterprise - 사용자 서버 예제

이 스크립트는 DantaroEnterprise 사용자 서버가 Dantaro Central 본사 서버와
어떻게 통합되는지 보여주는 예제입니다.
"""

import time
import logging
import json
import pandas as pd
from datetime import datetime
from dantaro_central_client import DantaroCentralClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 클라이언트 설정
API_KEY = "b4e3e160ae14316e8d0e316c2aee78f65d14315ffbe9275ec134f806ce7e48a8"
CENTRAL_SERVER = "http://localhost:8001"

class DantaroEnterprise:
    """DantaroEnterprise 사용자 서버 예제 클래스"""
    
    def __init__(self):
        """초기화"""
        self.client = DantaroCentralClient(CENTRAL_SERVER, API_KEY)
        self.logger = logging.getLogger(__name__)
        self.recommendations_cache = []
        self.market_status_cache = {}
        self.support_levels_cache = {}
        self.last_check = None
    
    def connect_central_server(self) -> bool:
        """중앙 서버 연결 테스트"""
        try:
            health = self.client.check_health()
            self.logger.info(f"중앙 서버 연결 성공: {health['success']}")
            self.last_check = datetime.now()
            return True
        except Exception as e:
            self.logger.error(f"중앙 서버 연결 실패: {str(e)}")
            return False
    
    def fetch_recommendations(self) -> None:
        """추천 코인 정보 조회"""
        try:
            data = self.client.get_recommendations(top_n=10)
            if data['success']:
                self.recommendations_cache = data['recommendations']
                self.logger.info(f"추천 코인 {len(self.recommendations_cache)}개 받음")
                
                # 데이터 출력
                if self.recommendations_cache:
                    df = pd.DataFrame(self.recommendations_cache)
                    print("\n===== 추천 코인 목록 =====")
                    print(df[['symbol', 'total_score', 'recommendation_strength', 'current_price']].to_string(index=False))
            else:
                self.logger.warning("추천 코인 정보 조회 실패")
        except Exception as e:
            self.logger.error(f"추천 코인 조회 오류: {str(e)}")
    
    def fetch_market_status(self) -> None:
        """시장 상태 정보 조회"""
        try:
            data = self.client.get_market_status()
            if data['success']:
                self.market_status_cache = data['market_status']
                self.logger.info(f"시장 상태 정보 받음: {data['market_status']['market_trend']}")
                
                # 데이터 출력
                print("\n===== 시장 상태 =====")
                print(f"추세: {data['market_status']['market_trend']}")
                print(f"시장 분위기: {data['market_status']['market_sentiment']}")
                print(f"총점: {data['market_status']['overall_score']}")
                print(f"상승 코인: {data['market_status']['analysis_summary']['top_gainers']}")
                print(f"하락 코인: {data['market_status']['analysis_summary']['top_losers']}")
                print(f"안정 코인: {data['market_status']['analysis_summary']['stable_coins']}")
            else:
                self.logger.warning("시장 상태 정보 조회 실패")
        except Exception as e:
            self.logger.error(f"시장 상태 조회 오류: {str(e)}")
    
    def fetch_support_levels(self, symbols=['BTC', 'ETH']) -> None:
        """지지/저항선 정보 조회"""
        try:
            for symbol in symbols:
                data = self.client.get_support_levels(symbol)
                if data['success']:
                    self.support_levels_cache[symbol] = data['support_levels']
                    self.logger.info(f"{symbol} 지지/저항선 정보 받음")
                    
                    # 데이터 출력
                    levels = data['support_levels']
                    print(f"\n===== {symbol} 지지/저항선 =====")
                    print(f"공격적 지지선: {levels['aggressive_support']}")
                    print(f"보통 지지선: {levels['moderate_support']}")
                    print(f"보수적 지지선: {levels['conservative_support']}")
                    print(f"공격적 저항선: {levels['aggressive_resistance']}")
                    print(f"보통 저항선: {levels['moderate_resistance']}")
                    print(f"보수적 저항선: {levels['conservative_resistance']}")
                else:
                    self.logger.warning(f"{symbol} 지지/저항선 정보 조회 실패")
        except Exception as e:
            self.logger.error(f"지지/저항선 조회 오류: {str(e)}")

    def run_simulation(self) -> None:
        """사용자 서버 시뮬레이션 실행"""
        self.logger.info("DantaroEnterprise 서버 시작...")
        
        if not self.connect_central_server():
            self.logger.error("중앙 서버 연결 실패. 종료합니다.")
            return
        
        self.logger.info("중앙 서버에서 데이터 수집 시작...")
        
        # 데이터 조회
        self.fetch_recommendations()
        self.fetch_market_status()
        self.fetch_support_levels()
        
        self.logger.info("DantaroEnterprise 테스트 완료!")


if __name__ == "__main__":
    # 사용자 서버 실행
    enterprise = DantaroEnterprise()
    enterprise.run_simulation()
