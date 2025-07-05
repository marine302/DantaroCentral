#!/usr/bin/env python3
"""
Dantaro Central 실시간 시스템 최적화 설정
성능 및 메모리 사용량 최적화를 위한 설정 관리
"""
import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """최적화 설정 클래스"""
    
    # 심볼 관리
    core_symbols: List[str]
    extended_symbols: List[str]
    max_symbols: int = 100  # 분석 대상 최대 코인 수 증가 (20 -> 100)
    
    # 메모리 최적화
    max_buffer_size: int = 2000  # 버퍼 크기 증가 (1000 -> 2000)
    cleanup_interval: int = 300  # 5분
    data_retention_minutes: int = 10  # 데이터 보존 시간 증가 (5 -> 10)
    
    # 성능 최적화
    monitoring_interval: int = 60  # 1분
    reconnect_threshold: int = 180  # 3분
    heartbeat_interval: int = 30  # 30초
    
    # 로깅 최적화
    log_level: str = "INFO"
    log_rotation_size: str = "10MB"
    max_log_files: int = 5
    
    # WebSocket 설정
    connection_timeout: int = 10
    max_reconnect_attempts: int = 5
    reconnect_delay: int = 5


class DantaroOptimizer:
    """Dantaro Central 최적화 관리자"""
    
    def __init__(self):
        self.config = self._load_config()
        self.performance_mode = os.getenv('DANTARO_PERFORMANCE_MODE', 'balanced')
        
    def _load_config(self) -> OptimizationConfig:
        """환경에 따른 최적화 설정 로드"""
        
        # 핵심 심볼 (기본 모니터링)
        core_symbols = [
            'BTC-USDT',    # 비트코인
            'ETH-USDT',    # 이더리움
            'SOL-USDT',    # 솔라나
            'XRP-USDT',    # 리플
            'DOGE-USDT',   # 도지코인
        ]
        
        # 확장 심볼 (단타 거래에 좋은 코인들)
        extended_symbols = [
            'SHIB-USDT',   # 시바이누
            'MATIC-USDT',  # 폴리곤
            'LINK-USDT',   # 체인링크
            'UNI-USDT',    # 유니스왑
            'AVAX-USDT',   # 아발란체
            'LTC-USDT',    # 라이트코인
            'NEAR-USDT',   # 니어
            'FTM-USDT',    # 팬텀
            'TRX-USDT',    # 트론
            'ETC-USDT',    # 이더리움 클래식
            'ICP-USDT',    # 인터넷 컴퓨터
            'APE-USDT',    # 에이프코인
            'FIL-USDT',    # 파일코인
            'AXS-USDT',    # 엑시 인피니티
            'SAND-USDT',   # 샌드박스
        ]
        
        return OptimizationConfig(
            core_symbols=core_symbols,
            extended_symbols=extended_symbols
        )
    
    def get_active_symbols(self) -> List[str]:
        """활성 심볼 목록 반환"""
        mode = os.getenv('DANTARO_MODE', 'volume_based')  # 기본값을 volume_based로 변경
        
        if mode == 'minimal':
            # 최소 모드: BTC, ETH만
            return self.config.core_symbols[:2]
        elif mode == 'core':
            # 핵심 모드: 핵심 심볼만
            return self.config.core_symbols
        elif mode == 'full':
            # 전체 모드: 모든 심볼
            return self.config.core_symbols + self.config.extended_symbols
        elif mode == 'volume_based':
            # 거래량 기반 모드: 모든 모니터링 대상 코인
            # 처음엔 기본 목록으로 시작하고, 이후 동적으로 업데이트됨
            return self.config.core_symbols + self.config.extended_symbols
        else:
            # 기본 최적화 모드: 핵심 + 일부 확장
            return self.config.core_symbols + self.config.extended_symbols[:2]
    
    def get_performance_settings(self) -> Dict:
        """성능 설정 반환"""
        mode = self.performance_mode
        
        if mode == 'high_performance':
            return {
                'monitoring_interval': 30,
                'cleanup_interval': 180,
                'max_buffer_size': 500,
                'log_level': 'WARNING'
            }
        elif mode == 'low_memory':
            return {
                'monitoring_interval': 120,
                'cleanup_interval': 120,
                'max_buffer_size': 300,
                'log_level': 'ERROR'
            }
        else:  # balanced
            return {
                'monitoring_interval': 60,
                'cleanup_interval': 300,
                'max_buffer_size': 1000,
                'log_level': 'INFO'
            }
    
    def optimize_logging(self) -> Dict:
        """로깅 최적화 설정"""
        settings = self.get_performance_settings()
        
        return {
            'level': settings['log_level'],
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'handlers': {
                'file': {
                    'filename': 'logs/dantaro_realtime.log',
                    'maxBytes': 10 * 1024 * 1024,  # 10MB
                    'backupCount': 3,
                    'encoding': 'utf-8'
                },
                'console': {
                    'stream': 'ext://sys.stdout'
                }
            }
        }
    
    def get_memory_limits(self) -> Dict:
        """메모리 사용량 제한 설정"""
        settings = self.get_performance_settings()
        
        return {
            'max_price_cache': settings['max_buffer_size'],
            'max_active_symbols': len(self.get_active_symbols()),
            'data_retention_seconds': 300,  # 5분
            'cleanup_threshold': 0.8  # 80% 사용 시 정리
        }
    
    def print_optimization_summary(self):
        """최적화 설정 요약 출력"""
        active_symbols = self.get_active_symbols()
        performance_settings = self.get_performance_settings()
        memory_limits = self.get_memory_limits()
        
        logger.info("🔧 Dantaro Central 최적화 설정")
        logger.info("=" * 50)
        logger.info(f"📊 모니터링 모드: {os.getenv('DANTARO_MODE', 'optimized')}")
        logger.info(f"⚡ 성능 모드: {self.performance_mode}")
        logger.info(f"🎯 활성 심볼: {len(active_symbols)}개")
        logger.info(f"   {', '.join(active_symbols)}")
        logger.info(f"🧠 메모리 제한: {memory_limits['max_price_cache']}개 캐시")
        logger.info(f"📈 모니터링 간격: {performance_settings['monitoring_interval']}초")
        logger.info(f"🧹 정리 간격: {performance_settings['cleanup_interval']}초")
        logger.info(f"📝 로그 레벨: {performance_settings['log_level']}")
        logger.info("=" * 50)


# 전역 최적화 인스턴스
dantaro_optimizer = DantaroOptimizer()


def setup_optimized_environment():
    """최적화된 환경 설정"""
    # 환경 변수 설정 가이드
    env_guide = """
🔧 Dantaro Central 최적화 환경 변수:

# 모니터링 모드 설정
export DANTARO_MODE=optimized    # 기본: 핵심 + 일부 확장 심볼
export DANTARO_MODE=minimal      # 최소: BTC, ETH만
export DANTARO_MODE=core         # 핵심: 주요 4개 심볼
export DANTARO_MODE=full         # 전체: 모든 심볼

# 성능 모드 설정
export DANTARO_PERFORMANCE_MODE=balanced        # 기본: 균형
export DANTARO_PERFORMANCE_MODE=high_performance # 고성능
export DANTARO_PERFORMANCE_MODE=low_memory      # 저메모리

# 사용 예시:
export DANTARO_MODE=core && export DANTARO_PERFORMANCE_MODE=high_performance
"""
    
    print(env_guide)
    
    # 현재 설정 표시
    dantaro_optimizer.print_optimization_summary()


if __name__ == "__main__":
    setup_optimized_environment()
