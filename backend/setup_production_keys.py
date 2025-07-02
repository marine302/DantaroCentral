#!/usr/bin/env python3
"""
프로덕션 API 키 설정 및 검증 도구
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 백엔드 디렉토리를 Python 경로에 추가
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

class ProductionAPIKeyManager:
    """프로덕션 API 키 관리자"""
    
    def __init__(self):
        self.env_file = backend_dir / '.env'
        self.env_example_file = backend_dir / '.env.example'
        
    def check_env_file_exists(self) -> bool:
        """환경 변수 파일 존재 여부 확인"""
        return self.env_file.exists()
    
    def create_env_from_example(self) -> bool:
        """예시 파일에서 .env 파일 생성"""
        try:
            if self.env_example_file.exists():
                content = self.env_example_file.read_text()
                self.env_file.write_text(content)
                print(f"✅ .env 파일이 생성되었습니다: {self.env_file}")
                return True
            else:
                print(f"❌ .env.example 파일을 찾을 수 없습니다: {self.env_example_file}")
                return False
        except Exception as e:
            print(f"❌ .env 파일 생성 실패: {e}")
            return False
    
    def load_env_variables(self) -> Dict[str, str]:
        """환경 변수 파일 로드"""
        env_vars = {}
        if not self.env_file.exists():
            return env_vars
        
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            return env_vars
        except Exception as e:
            print(f"❌ 환경 변수 로드 실패: {e}")
            return {}
    
    def update_api_key(self, exchange: str, api_key: str, secret_key: str, passphrase: Optional[str] = None):
        """API 키 업데이트"""
        env_vars = self.load_env_variables()
        
        # 거래소별 환경 변수 키 매핑
        key_mapping = {
            'okx': ('OKX_API_KEY', 'OKX_SECRET_KEY', 'OKX_PASSPHRASE'),
            'coinone': ('COINONE_API_KEY', 'COINONE_SECRET_KEY', None),
            'gateio': ('GATE_API_KEY', 'GATE_SECRET_KEY', None),
            'upbit': ('UPBIT_ACCESS_KEY', 'UPBIT_SECRET_KEY', None),
            'binance': ('BINANCE_API_KEY', 'BINANCE_API_SECRET', None),
            'bithumb': ('BITHUMB_API_KEY', 'BITHUMB_SECRET_KEY', None),
            'bybit': ('BYBIT_API_KEY', 'BYBIT_SECRET_KEY', None)
        }
        
        if exchange not in key_mapping:
            print(f"❌ 지원하지 않는 거래소: {exchange}")
            return False
        
        api_key_var, secret_key_var, passphrase_var = key_mapping[exchange]
        
        # API 키 업데이트
        env_vars[api_key_var] = api_key
        env_vars[secret_key_var] = secret_key
        
        if passphrase_var and passphrase:
            env_vars[passphrase_var] = passphrase
        
        # 파일에 저장
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            print(f"✅ {exchange.upper()} API 키가 업데이트되었습니다")
            return True
        except Exception as e:
            print(f"❌ API 키 저장 실패: {e}")
            return False
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """설정된 API 키 검증"""
        env_vars = self.load_env_variables()
        validation_results = {}
        
        # 필수 키 정의
        required_keys = {
            'okx': ['OKX_API_KEY', 'OKX_SECRET_KEY', 'OKX_PASSPHRASE'],
            'coinone': ['COINONE_API_KEY', 'COINONE_SECRET_KEY'],
            'gateio': ['GATE_API_KEY', 'GATE_SECRET_KEY'],
            'upbit': ['UPBIT_ACCESS_KEY', 'UPBIT_SECRET_KEY'],
            'binance': ['BINANCE_API_KEY', 'BINANCE_API_SECRET'],
            'bithumb': ['BITHUMB_API_KEY', 'BITHUMB_SECRET_KEY'],
            'bybit': ['BYBIT_API_KEY', 'BYBIT_SECRET_KEY']
        }
        
        for exchange, keys in required_keys.items():
            all_keys_present = True
            for key in keys:
                if key not in env_vars or not env_vars[key] or env_vars[key].startswith('your-'):
                    all_keys_present = False
                    break
            validation_results[exchange] = all_keys_present
        
        return validation_results
    
    def interactive_setup(self):
        """대화형 API 키 설정"""
        print("🔑 Dantaro Central 프로덕션 API 키 설정")
        print("=" * 50)
        
        # .env 파일 확인 및 생성
        if not self.check_env_file_exists():
            print("📋 .env 파일이 존재하지 않습니다.")
            create = input("🔧 .env.example에서 .env 파일을 생성하시겠습니까? (y/n): ").lower()
            if create == 'y':
                if not self.create_env_from_example():
                    print("❌ .env 파일 생성에 실패했습니다.")
                    return
            else:
                print("❌ .env 파일이 필요합니다. 설정을 종료합니다.")
                return
        
        # 현재 설정 상태 확인
        validation_results = self.validate_api_keys()
        print("\n📊 현재 API 키 설정 상태:")
        for exchange, is_valid in validation_results.items():
            status = "✅ 설정됨" if is_valid else "❌ 미설정"
            print(f"  {exchange.upper()}: {status}")
        
        # 거래소별 설정
        exchanges = ['okx', 'coinone', 'gateio', 'upbit', 'binance', 'bithumb', 'bybit']
        
        print(f"\n🏗️  설정할 거래소를 선택하세요:")
        for i, exchange in enumerate(exchanges, 1):
            status = "✅" if validation_results.get(exchange, False) else "❌"
            print(f"  {i}. {exchange.upper()} {status}")
        print("  0. 완료")
        
        while True:
            try:
                choice = input("\n선택 (0-7): ").strip()
                if choice == '0':
                    break
                
                idx = int(choice) - 1
                if 0 <= idx < len(exchanges):
                    exchange = exchanges[idx]
                    self.setup_exchange_keys(exchange)
                else:
                    print("❌ 올바른 번호를 입력하세요.")
            except ValueError:
                print("❌ 숫자를 입력하세요.")
        
        print("\n🎉 API 키 설정이 완료되었습니다!")
        print("💡 다음 단계: python test_production_apis.py 실행하여 연결을 테스트하세요.")
    
    def setup_exchange_keys(self, exchange: str):
        """특정 거래소 API 키 설정"""
        print(f"\n🔑 {exchange.upper()} API 키 설정")
        print("-" * 30)
        
        api_key = input(f"API Key: ").strip()
        if not api_key:
            print("❌ API Key가 필요합니다.")
            return
        
        secret_key = input(f"Secret Key: ").strip()
        if not secret_key:
            print("❌ Secret Key가 필요합니다.")
            return
        
        passphrase = None
        if exchange == 'okx':
            passphrase = input(f"Passphrase: ").strip()
            if not passphrase:
                print("❌ OKX는 Passphrase가 필요합니다.")
                return
        
        # API 키 저장
        success = self.update_api_key(exchange, api_key, secret_key, passphrase)
        if success:
            print(f"✅ {exchange.upper()} API 키가 저장되었습니다.")
        else:
            print(f"❌ {exchange.upper()} API 키 저장에 실패했습니다.")

def main():
    manager = ProductionAPIKeyManager()
    manager.interactive_setup()

if __name__ == "__main__":
    main()
