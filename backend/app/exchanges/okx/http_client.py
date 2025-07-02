"""
OKX HTTP 클라이언트 모듈
단일 책임: HTTP 세션 관리 및 요청/응답 처리
"""

import json
from typing import Any, Dict, Optional

import aiohttp

from .auth import OKXAuth


class OKXHttpClient:
    """OKX HTTP 통신 클라이언트"""
    
    def __init__(self, auth: OKXAuth, base_url: str):
        self.auth = auth
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 관리"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     auth: bool = False) -> Any:
        """
        HTTP 요청 처리
        
        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            params: 요청 파라미터
            auth: 인증 필요 여부
            
        Returns:
            API 응답 데이터
        """
        session = await self.get_session()
        url = f"{self.base_url}{endpoint}"
        
        headers = {'Content-Type': 'application/json'}
        body = ""
        
        # URL 및 body 구성
        if method.upper() == 'GET' and params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
        elif method.upper() == 'POST' and params:
            body = json.dumps(params)
        
        # 인증 헤더 추가
        if auth:
            auth_headers = self.auth.generate_auth_headers(method, endpoint.split('?')[0], body)
            headers.update(auth_headers)
        
        try:
            # 요청 실행
            if method.upper() == 'GET':
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, data=body, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
            else:
                raise Exception(f"지원되지 않는 HTTP 메서드: {method}")
            
            # OKX API 응답 검증
            if data.get('code') != '0':
                print(f"OKX API 응답: {data}")
                raise Exception(f"OKX API 오류: {data.get('msg', 'Unknown error')}")
            
            return data.get('data', [])
        
        except aiohttp.ClientError as e:
            raise Exception(f"OKX API 오류: {str(e)}")
    
    async def close(self):
        """세션 정리"""
        if self.session and not self.session.closed:
            await self.session.close()
