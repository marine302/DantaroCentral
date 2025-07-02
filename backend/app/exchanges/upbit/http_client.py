"""
Upbit HTTP 클라이언트
API 요청/응답 처리
"""

import aiohttp
import asyncio
from typing import Dict, Optional, Any
from .auth import UpbitAuth


class UpbitHttpClient:
    """Upbit HTTP 클라이언트"""
    
    BASE_URL = "https://api.upbit.com"
    
    def __init__(self, api_key: str, secret_key: str):
        self.auth = UpbitAuth(api_key, secret_key)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 관리"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, auth_required: bool = True) -> Dict[str, Any]:
        """
        API 요청 실행
        
        Args:
            method: HTTP 메서드 (GET, POST, DELETE)
            endpoint: API 엔드포인트
            params: 쿼리 파라미터
            data: 요청 바디 데이터
            auth_required: 인증 필요 여부
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {}
        if auth_required:
            # 인증이 필요한 경우 (private endpoints)
            auth_params = params if method == 'GET' else data
            headers.update(self.auth.generate_auth_headers(auth_params))
        
        try:
            if method == 'GET':
                async with session.get(url, params=params, headers=headers) as response:
                    return await self._handle_response(response)
            elif method == 'POST':
                async with session.post(url, json=data, headers=headers) as response:
                    return await self._handle_response(response)
            elif method == 'DELETE':
                async with session.delete(url, params=params, headers=headers) as response:
                    return await self._handle_response(response)
            else:
                raise ValueError(f"지원되지 않는 HTTP 메서드: {method}")
                
        except aiohttp.ClientError as e:
            raise Exception(f"Upbit API 요청 실패: {e}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """응답 처리"""
        try:
            data = await response.json()
        except Exception:
            data = {}
        
        if response.status >= 400:
            error_message = data.get('error', {}).get('message', '알 수 없는 오류')
            raise Exception(f"Upbit API 오류 [{response.status}]: {error_message}")
        
        return data
    
    async def close(self):
        """세션 종료"""
        if self.session and not self.session.closed:
            await self.session.close()
