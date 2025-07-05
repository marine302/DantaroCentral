#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DantaroCentralClient - DantaroEnterprise에서 중앙 서버에 연결하기 위한 클라이언트

이 클라이언트는 DantaroEnterprise(사용자 서버)가 Dantaro Central(본사 서버)의 
API에 접근하기 위한 파이썬 래퍼입니다.
"""

import requests
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

class DantaroCentralClient:
    """DantaroCentral API에 접근하기 위한 클라이언트"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        클라이언트 초기화
        
        Args:
            base_url: Dantaro Central 서버 URL (예: http://localhost:8001)
            api_key: API 키
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_version = 'v1'
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        API 요청 전송
        
        Args:
            endpoint: API 엔드포인트 경로
            method: HTTP 메서드 (GET, POST, PUT, DELETE)
            params: URL 쿼리 파라미터
            data: 요청 본문 데이터
            
        Returns:
            API 응답 (dict)
        """
        url = f"{self.base_url}/api/{self.api_version}/{endpoint}"
        self.logger.debug(f"요청: {method} {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = self.session.post(url, headers=self.headers, params=params, json=data)
            elif method == 'PUT':
                response = self.session.put(url, headers=self.headers, params=params, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=self.headers, params=params)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            # 응답 상태 확인
            response.raise_for_status()
            
            # JSON으로 파싱
            result = response.json()
            return result
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API 요청 오류: {str(e)}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"응답 코드: {e.response.status_code}")
                self.logger.error(f"응답 본문: {e.response.text}")
            raise
    
    def check_health(self) -> Dict:
        """
        서버 상태 확인
        
        Returns:
            서버 상태 정보
        """
        return self._make_request('health')
    
    def get_recommendations(self, top_n: int = 10) -> Dict:
        """
        코인 추천 목록 조회
        
        Args:
            top_n: 추천 코인 수
            
        Returns:
            코인 추천 목록
        """
        return self._make_request('recommendations', params={'top_n': top_n})
    
    def get_market_status(self) -> Dict:
        """
        전체 시장 상태 조회
        
        Returns:
            시장 상태 정보
        """
        return self._make_request('market-status')
    
    def get_support_levels(self, symbol: str) -> Dict:
        """
        지지/저항선 정보 조회
        
        Args:
            symbol: 코인 심볼 (예: BTC)
            
        Returns:
            지지/저항선 정보
        """
        return self._make_request(f'support-levels/{symbol}')


if __name__ == "__main__":
    # 테스트 코드
    API_KEY = "b4e3e160ae14316e8d0e316c2aee78f65d14315ffbe9275ec134f806ce7e48a8"
    BASE_URL = "http://localhost:8001"
    
    client = DantaroCentralClient(BASE_URL, API_KEY)
    
    try:
        # 서버 상태 확인
        health = client.check_health()
        print("서버 상태:", json.dumps(health, indent=2, ensure_ascii=False))
        
        # 추천 코인 목록
        recommendations = client.get_recommendations(top_n=5)
        print("\n추천 코인:", json.dumps(recommendations, indent=2, ensure_ascii=False))
        
        # 시장 상태
        market_status = client.get_market_status()
        print("\n시장 상태:", json.dumps(market_status, indent=2, ensure_ascii=False))
        
        # BTC 지지/저항선
        support_levels = client.get_support_levels("BTC")
        print("\nBTC 지지/저항선:", json.dumps(support_levels, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
