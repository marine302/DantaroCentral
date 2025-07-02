"""
Upbit 인증 관리
JWT 토큰 생성 및 인증 헤더 처리
"""

import hashlib
import hmac
import uuid
import jwt
from typing import Dict, Optional
from urllib.parse import urlencode


class UpbitAuth:
    """Upbit API 인증 처리"""
    
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
    
    def generate_auth_headers(self, query_params: Optional[Dict] = None) -> Dict[str, str]:
        """Upbit 인증 헤더 생성"""
        payload = {
            'access_key': self.api_key,
            'nonce': str(uuid.uuid4()),
        }
        
        if query_params:
            query_string = urlencode(query_params, doseq=True, safe='', encoding='utf-8')
            m = hashlib.sha512()
            m.update(query_string.encode('utf-8'))
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
        
        jwt_token = self._create_jwt_token(payload)
        return {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    def _create_jwt_token(self, payload: Dict) -> str:
        """JWT 토큰 생성"""
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
