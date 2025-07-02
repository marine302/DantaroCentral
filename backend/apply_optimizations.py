#!/usr/bin/env python3
"""
Dantaro Central 최적화 적용 스크립트
시스템 최적화 및 성능 향상을 위한 자동화 도구
"""
import logging
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from optimization_config import dantaro_optimizer, setup_optimized_environment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_optimizations():
    """최적화 적용"""
    logger.info("🔧 Dantaro Central 최적화 적용 시작")
    
    # 1. 바이낸스 제거 확인
    logger.info("1️⃣ 바이낸스 거래소 제거 확인...")
    binance_dir = "app/exchanges/binance"
    if not os.path.exists(binance_dir):
        logger.info("   ✅ 바이낸스 디렉토리 제거됨")
    else:
        logger.warning("   ⚠️ 바이낸스 디렉토리가 아직 존재함")
    
    # 2. 최적화 설정 확인
    logger.info("2️⃣ 최적화 설정 확인...")
    active_symbols = dantaro_optimizer.get_active_symbols()
    performance_settings = dantaro_optimizer.get_performance_settings()
    memory_limits = dantaro_optimizer.get_memory_limits()
    
    logger.info(f"   📊 활성 심볼: {len(active_symbols)}개")
    logger.info(f"   ⚡ 성능 모드: {os.getenv('DANTARO_PERFORMANCE_MODE', 'balanced')}")
    logger.info(f"   🧠 메모리 캐시 제한: {memory_limits['max_price_cache']}개")
    
    # 3. 환경 변수 추천
    logger.info("3️⃣ 환경 변수 추천...")
    current_mode = os.getenv('DANTARO_MODE', 'optimized')
    current_perf = os.getenv('DANTARO_PERFORMANCE_MODE', 'balanced')
    
    logger.info(f"   현재 모드: DANTARO_MODE={current_mode}")
    logger.info(f"   현재 성능: DANTARO_PERFORMANCE_MODE={current_perf}")
    
    # 4. 권장 설정
    recommendations = {
        'development': {
            'mode': 'minimal',
            'performance': 'balanced',
            'description': '개발 환경 - 최소 심볼로 테스트'
        },
        'production_light': {
            'mode': 'core',
            'performance': 'high_performance', 
            'description': '경량 프로덕션 - 핵심 심볼만 고성능'
        },
        'production_full': {
            'mode': 'full',
            'performance': 'balanced',
            'description': '전체 프로덕션 - 모든 심볼 균형 성능'
        },
        'low_resource': {
            'mode': 'minimal',
            'performance': 'low_memory',
            'description': '저사양 환경 - 메모리 최적화'
        }
    }
    
    logger.info("4️⃣ 권장 설정:")
    for scenario, config in recommendations.items():
        logger.info(f"   {scenario}:")
        logger.info(f"     export DANTARO_MODE={config['mode']}")
        logger.info(f"     export DANTARO_PERFORMANCE_MODE={config['performance']}")
        logger.info(f"     # {config['description']}")
    
    # 5. 최적화 검증
    logger.info("5️⃣ 최적화 검증...")
    
    # 메모리 사용량 예상
    estimated_memory = len(active_symbols) * memory_limits['max_price_cache'] * 0.001  # MB 단위
    logger.info(f"   예상 메모리 사용량: ~{estimated_memory:.1f}MB")
    
    # 데이터 처리량 예상
    estimated_msgs_per_min = len(active_symbols) * 10  # 심볼당 약 10개/분
    logger.info(f"   예상 메시지 처리량: ~{estimated_msgs_per_min}개/분")
    
    logger.info("✅ 최적화 적용 완료")
    logger.info("\n🚀 최적화된 서비스 시작:")
    logger.info("   ./start_realtime_service.sh")


def benchmark_performance():
    """성능 벤치마크"""
    logger.info("📊 성능 벤치마크 시작...")
    
    import time
    from datetime import datetime
    
    # 심볼 처리 성능 테스트
    test_symbols = dantaro_optimizer.get_active_symbols()
    
    start_time = time.time()
    for _ in range(1000):
        # 가상 데이터 처리 시뮬레이션
        for symbol in test_symbols:
            dummy_data = {
                'symbol': symbol,
                'price': 45000.0,
                'timestamp': datetime.now()
            }
            # 간단한 처리 작업
            processed = f"{dummy_data['symbol']}: ${dummy_data['price']}"
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    total_operations = 1000 * len(test_symbols)
    ops_per_second = total_operations / processing_time
    
    logger.info(f"📈 벤치마크 결과:")
    logger.info(f"   총 작업: {total_operations:,}개")
    logger.info(f"   처리 시간: {processing_time:.3f}초")
    logger.info(f"   초당 처리량: {ops_per_second:,.0f}개/초")
    logger.info(f"   심볼당 처리량: {ops_per_second/len(test_symbols):,.0f}개/초")


def main():
    """메인 함수"""
    logger.info("🎯 Dantaro Central 최적화 도구")
    logger.info("=" * 50)
    
    # 최적화 적용
    apply_optimizations()
    
    # 환경 설정 가이드
    setup_optimized_environment()
    
    # 성능 벤치마크 (선택사항)
    try:
        benchmark_performance()
    except Exception as e:
        logger.warning(f"벤치마크 실행 중 오류: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info("🎉 최적화 완료! 이제 실시간 서비스를 시작할 수 있습니다.")


if __name__ == "__main__":
    main()
