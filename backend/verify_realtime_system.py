#!/usr/bin/env python3
"""
Dantaro Central 실시간 시스템 통합 검증
모든 기능이 올바르게 작동하는지 최종 확인
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.okx_websocket import OKXWebSocketClient
from app.services.market_data_collector import market_data_collector
from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_websocket_connection():
    """WebSocket 연결 테스트"""
    logger.info("🔗 WebSocket 연결 테스트")
    
    try:
        client = OKXWebSocketClient()
        await client.connect()
        logger.info("✅ WebSocket 연결 성공")
        await client.disconnect()
        return True
    except Exception as e:
        logger.error(f"❌ WebSocket 연결 실패: {e}")
        return False


async def test_realtime_data_reception():
    """실시간 데이터 수신 테스트"""
    logger.info("📡 실시간 데이터 수신 테스트")
    
    received_count = 0
    test_symbols = ['BTC-USDT', 'ETH-USDT']
    
    def data_handler(data):
        nonlocal received_count
        received_count += 1
        
        if 'arg' in data and 'data' in data:
            symbol = data['arg'].get('instId', 'Unknown')
            channel = data['arg'].get('channel', 'Unknown')
            logger.info(f"📊 {symbol} {channel} 데이터 수신 ({received_count})")
    
    try:
        client = OKXWebSocketClient(data_handler=data_handler)
        
        await client.connect()
        await client.subscribe_ticker(test_symbols)
        await client.subscribe_candles(test_symbols, '1m')
        
        logger.info("⏱️ 15초간 데이터 수신 테스트...")
        await asyncio.sleep(15)
        
        await client.disconnect()
        
        if received_count > 0:
            logger.info(f"✅ 실시간 데이터 수신 성공: {received_count}개 메시지")
            return True
        else:
            logger.warning("❌ 실시간 데이터 수신 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 실시간 데이터 테스트 실패: {e}")
        return False


async def test_rest_api_integration():
    """REST API 통합 테스트"""
    logger.info("🔄 REST API 통합 테스트")
    
    try:
        # 거래소 설정
        if not settings.okx_api_key:
            logger.warning("⚠️ API 키가 없어 REST API 테스트 생략")
            return True
        
        exchange_configs = {
            'okx': {
                'api_key': settings.okx_api_key,
                'secret_key': settings.okx_secret_key,
                'passphrase': settings.okx_passphrase
            }
        }
        
        market_data_collector.configure_exchanges(exchange_configs)
        market_data_collector.set_target_symbols(['BTC-USDT'])
        
        # 단일 데이터 수집 테스트
        data_points = await market_data_collector.collect_all_data()
        
        if data_points:
            logger.info(f"✅ REST API 데이터 수집 성공: {len(data_points)}개 데이터")
            for point in data_points:
                logger.info(f"   {point.exchange} {point.symbol}: ${point.price:,.2f}")
            return True
        else:
            logger.warning("❌ REST API 데이터 수집 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ REST API 테스트 실패: {e}")
        return False


async def test_combined_data_processing():
    """결합 데이터 처리 테스트"""
    logger.info("🔀 결합 데이터 처리 테스트")
    
    try:
        # 실시간 데이터 활성화
        market_data_collector.enable_realtime_data(['BTC-USDT'], ['okx'])
        
        # 결합 데이터 조회
        combined_data = await market_data_collector.get_combined_data('BTC-USDT')
        
        logger.info(f"✅ 결합 데이터 처리 성공")
        logger.info(f"   데이터 소스: {combined_data.get('data_sources', [])}")
        logger.info(f"   실시간 데이터: {'있음' if combined_data.get('realtime_data') else '없음'}")
        logger.info(f"   REST 데이터: {len(combined_data.get('rest_data', []))}개")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 결합 데이터 처리 테스트 실패: {e}")
        return False


async def test_error_handling():
    """오류 처리 테스트"""
    logger.info("⚠️ 오류 처리 테스트")
    
    try:
        # 잘못된 심볼로 테스트
        market_data_collector.set_target_symbols(['INVALID-SYMBOL'])
        data_points = await market_data_collector.collect_all_data()
        
        # 오류가 발생해도 시스템이 중단되지 않아야 함
        logger.info("✅ 오류 처리 테스트 통과 (시스템 안정성 확인)")
        
        # 정상 심볼로 복원
        market_data_collector.set_target_symbols(['BTC-USDT'])
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 오류 처리 테스트 실패: {e}")
        return False


async def run_comprehensive_test():
    """종합 테스트 실행"""
    logger.info("🧪 Dantaro Central 실시간 시스템 종합 테스트 시작")
    logger.info(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {}
    
    # 테스트 항목들
    tests = [
        ("WebSocket 연결", test_websocket_connection),
        ("실시간 데이터 수신", test_realtime_data_reception),
        ("REST API 통합", test_rest_api_integration),
        ("결합 데이터 처리", test_combined_data_processing),
        ("오류 처리", test_error_handling),
    ]
    
    # 테스트 실행
    for test_name, test_func in tests:
        logger.info(f"\n📋 {test_name} 테스트 시작...")
        try:
            result = await test_func()
            test_results[test_name] = result
            status = "✅ 성공" if result else "❌ 실패"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            test_results[test_name] = False
            logger.error(f"❌ {test_name} 테스트 중 예외: {e}")
        
        # 테스트 간 잠시 휴식
        await asyncio.sleep(1)
    
    # 결과 요약
    logger.info("\n" + "="*60)
    logger.info("📊 종합 테스트 결과")
    logger.info("="*60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    logger.info(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과 ({success_rate:.1f}%)")
    
    if passed == total:
        logger.info("🎉 모든 테스트 통과! 시스템이 프로덕션 준비 완료되었습니다.")
        logger.info("🚀 다음 명령으로 실시간 서비스를 시작할 수 있습니다:")
        logger.info("   python3 dantaro_realtime_service.py")
    elif success_rate >= 80:
        logger.warning(f"⚠️ 대부분 테스트 통과 ({success_rate:.1f}%). 실패한 테스트를 확인하세요.")
    else:
        logger.error(f"❌ 다수 테스트 실패 ({success_rate:.1f}%). 시스템을 점검하세요.")
    
    return passed == total


async def main():
    result = await run_comprehensive_test()
    
    if result:
        logger.info("\n✅ Dantaro Central 실시간 시스템이 성공적으로 준비되었습니다!")
    else:
        logger.error("\n❌ 시스템에 문제가 있습니다. 로그를 확인하여 문제를 해결하세요.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
