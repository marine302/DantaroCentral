"""
OKX API 인증 헬퍼
단일 책임: OKX API 인증 및 서명 생성
"""

import base64
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict


class OKXAuth:
    """OKX API 인증 처리"""
    
    def __init__(self, api_key: str, secret_key: str, passphrase: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
    
    def generate_auth_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        """OKX 인증 헤더 생성"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        message = timestamp + method.upper() + request_path + body
        
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase
        }
