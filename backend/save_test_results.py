#!/usr/bin/env python3
"""
실제 데이터 수집 결과를 파일로 저장하는 테스트
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 백엔드 디렉토리 추가
backend_dir = Path('/Users/danielkwon/DantaroCentral/backend')
sys.path.append(str(backend_dir))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

async def run_test_and_save_results():
    """테스트 실행 및 결과 저장"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'status': 'starting',
        'message': '',
        'data': [],
        'errors': []
    }
    
    try:
        # 환경 변수 확인
        okx_api_key = os.getenv('OKX_API_KEY', '')
        okx_secret_key = os.getenv('OKX_SECRET_KEY', '')
        okx_passphrase = os.getenv('OKX_PASSPHRASE', '')
        
        if okx_api_key and not okx_api_key.startswith('your-'):
            results['message'] = 'OKX API 키 발견됨'
            
            # 모듈 import 테스트
            try:
                from app.core.config import Settings
                from app.services.market_data_collector import MarketDataCollector
                
                settings = Settings()
                
                # 거래소 설정
                exchange_configs = {
                    'okx': {
                        'api_key': settings.okx_api_key,
                        'secret_key': settings.okx_secret_key,
                        'passphrase': settings.okx_passphrase
                    }
                }
                
                # 데이터 수집 테스트
                collector = MarketDataCollector()
                collector.configure_exchanges(exchange_configs)
                collector.set_target_symbols(['BTC-USDT', 'ETH-USDT'])
                
                start_time = datetime.now()
                data_points = await collector.collect_all_data()
                end_time = datetime.now()
                
                # 결과 저장
                results['status'] = 'success'
                results['message'] = f'{len(data_points)}개 데이터 포인트 수집 완료'
                results['collection_time'] = (end_time - start_time).total_seconds()
                results['data_count'] = len(data_points)
                
                for point in data_points:
                    results['data'].append({
                        'symbol': point.symbol,
                        'exchange': point.exchange,
                        'price': float(point.price),
                        'volume_24h': float(point.volume_24h),
                        'timestamp': point.timestamp.isoformat()
                    })
                
                # 리소스 정리
                for exchange in collector.exchanges.values():
                    if hasattr(exchange, 'close'):
                        await exchange.close()
                
            except Exception as e:
                results['status'] = 'error'
                results['message'] = f'데이터 수집 실패: {str(e)}'
                results['errors'].append(str(e))
        else:
            results['status'] = 'no_api_key'
            results['message'] = 'API 키가 설정되지 않음'
    
    except Exception as e:
        results['status'] = 'error'
        results['message'] = f'테스트 실행 실패: {str(e)}'
        results['errors'].append(str(e))
    
    # 결과를 파일로 저장
    results_file = backend_dir / 'test_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 간단한 텍스트 결과도 저장
    summary_file = backend_dir / 'test_summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"테스트 시간: {results['timestamp']}\n")
        f.write(f"상태: {results['status']}\n")
        f.write(f"메시지: {results['message']}\n")
        
        if results['data']:
            f.write(f"\n수집된 데이터 ({len(results['data'])}개):\n")
            for data in results['data']:
                f.write(f"- {data['symbol']}: ${data['price']:,.2f} ({data['exchange']})\n")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_test_and_save_results())
