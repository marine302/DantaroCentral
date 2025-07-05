"""
Redis cache management for Dantaro Central.
Handles caching of analysis results and market data.
"""
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

import redis
from app.core.config import settings


@dataclass
class CacheConfig:
    """캐시 설정 클래스."""
    
    # TTL 설정 (초 단위)
    RECOMMENDATIONS_TTL = 300  # 5분
    SUPPORT_LEVELS_TTL = 900   # 15분
    MARKET_STATUS_TTL = 120    # 2분
    PRICE_DATA_TTL = 60        # 1분
    ANALYSIS_RESULTS_TTL = 600 # 10분
    
    # 키 프리픽스
    RECOMMENDATIONS_PREFIX = "rec:"
    SUPPORT_LEVELS_PREFIX = "sup:"
    MARKET_STATUS_PREFIX = "mkt:"
    PRICE_DATA_PREFIX = "price:"
    ANALYSIS_PREFIX = "analysis:"
    WORKER_STATUS_PREFIX = "worker:"


class RedisManager:
    """Redis 캐시 관리자."""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=False,  # pickle 사용을 위해 False
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        self.config = CacheConfig()
    
    def _make_key(self, prefix: str, key: str) -> str:
        """캐시 키 생성."""
        return f"{prefix}{key}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """데이터를 바이트로 직렬화."""
        return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """바이트 데이터를 역직렬화."""
        return pickle.loads(data)
    
    def _serialize_data(self, data: Any) -> bytes:
        """데이터 직렬화."""
        if isinstance(data, (dict, list)):
            return json.dumps(data, default=str).encode('utf-8')
        else:
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """데이터 역직렬화."""
        try:
            # JSON 먼저 시도
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # pickle 시도
            return pickle.loads(data)
    
    # 추천 결과 캐시
    def cache_recommendations(self, recommendations: List[Dict]) -> bool:
        """코인 추천 결과를 캐시에 저장."""
        try:
            key = self._make_key(self.config.RECOMMENDATIONS_PREFIX, "latest")
            data = self._serialize_data({
                'recommendations': recommendations,
                'cached_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=self.config.RECOMMENDATIONS_TTL)).isoformat()
            })
            return self.redis_client.setex(key, self.config.RECOMMENDATIONS_TTL, data)
        except Exception as e:
            print(f"Error caching recommendations: {e}")
            return False
    
    def get_recommendations(self) -> Optional[List[Dict]]:
        """캐시된 추천 결과 조회."""
        try:
            key = self._make_key(self.config.RECOMMENDATIONS_PREFIX, "latest")
            data = self.redis_client.get(key)
            if data:
                cached_data = self._deserialize_data(data)
                return cached_data.get('recommendations')
            return None
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return None
    
    # 지지/저항선 캐시
    def cache_support_levels(self, symbol: str, support_data: Dict) -> bool:
        """지지/저항선 데이터를 캐시에 저장."""
        try:
            key = self._make_key(self.config.SUPPORT_LEVELS_PREFIX, symbol.lower())
            data = self._serialize_data({
                'symbol': symbol,
                'support_data': support_data,
                'cached_at': datetime.now().isoformat(),
            })
            return self.redis_client.setex(key, self.config.SUPPORT_LEVELS_TTL, data)
        except Exception as e:
            print(f"Error caching support levels for {symbol}: {e}")
            return False
    
    def get_support_levels(self, symbol: str) -> Optional[Dict]:
        """캐시된 지지/저항선 데이터 조회."""
        try:
            key = self._make_key(self.config.SUPPORT_LEVELS_PREFIX, symbol.lower())
            data = self.redis_client.get(key)
            if data:
                cached_data = self._deserialize_data(data)
                return cached_data.get('support_data')
            return None
        except Exception as e:
            print(f"Error getting support levels for {symbol}: {e}")
            return None
    
    # 시장 상태 캐시
    def cache_market_status(self, market_data: Dict) -> bool:
        """시장 상태 데이터를 캐시에 저장."""
        try:
            key = self._make_key(self.config.MARKET_STATUS_PREFIX, "current")
            data = self._serialize_data({
                'market_data': market_data,
                'cached_at': datetime.now().isoformat(),
            })
            return self.redis_client.setex(key, self.config.MARKET_STATUS_TTL, data)
        except Exception as e:
            print(f"Error caching market status: {e}")
            return False
    
    def get_market_status(self) -> Optional[Dict]:
        """캐시된 시장 상태 조회."""
        try:
            key = self._make_key(self.config.MARKET_STATUS_PREFIX, "current")
            data = self.redis_client.get(key)
            if data:
                cached_data = self._deserialize_data(data)
                return cached_data.get('market_data')
            return None
        except Exception as e:
            print(f"Error getting market status: {e}")
            return None
    
    # 추천 데이터 관련 메서드 추가
    def save_recommendations_to_redis(self, volume_recommendations: List[Dict], 
                                    traditional_recommendations: List[Dict]) -> bool:
        """추천 데이터를 Redis에 저장 (동기 버전)."""
        try:
            # 거래량 기반 추천 저장
            if volume_recommendations:
                self.cache_recommendations(volume_recommendations, "volume")
            
            # 전통적 추천 저장
            if traditional_recommendations:
                self.cache_recommendations(traditional_recommendations, "traditional")
            
            return True
        except Exception as e:
            print(f"Error saving recommendations to Redis: {e}")
            return False
    
    def broadcast_recommendations(self, recommendations: List[Dict]) -> bool:
        """WebSocket을 통해 추천 데이터 브로드캐스트 (동기 버전)."""
        try:
            # WebSocket 채널에 메시지 발행 (간단한 구현)
            broadcast_key = "websocket:recommendations"
            message_data = {
                'type': 'recommendations_update',
                'data': recommendations,
                'timestamp': datetime.now().isoformat(),
            }
            
            # Redis의 pub/sub 기능 사용하여 WebSocket 서버에 알림
            try:
                self.redis_client.publish(broadcast_key, json.dumps(message_data))
            except:
                pass  # Redis 실패 시 무시
            return True
        except Exception as e:
            print(f"Error broadcasting recommendations: {e}")
            return False
    
    # 가격 데이터 캐시
    def cache_price_data(self, symbol: str, price_data: Dict) -> bool:
        """가격 데이터를 캐시에 저장."""
        try:
            key = self._make_key(self.config.PRICE_DATA_PREFIX, symbol.lower())
            data = self._serialize_data(price_data)
            return self.redis_client.setex(key, self.config.PRICE_DATA_TTL, data)
        except Exception as e:
            print(f"Error caching price data for {symbol}: {e}")
            return False
    
    def get_price_data(self, symbol: str) -> Optional[Dict]:
        """캐시된 가격 데이터 조회."""
        try:
            key = self._make_key(self.config.PRICE_DATA_PREFIX, symbol.lower())
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
        except Exception as e:
            print(f"Error getting price data for {symbol}: {e}")
            return None
    
    # 워커 상태 관리
    def set_worker_status(self, worker_id: str, status: Dict) -> bool:
        """워커 상태를 캐시에 저장."""
        try:
            key = self._make_key(self.config.WORKER_STATUS_PREFIX, worker_id)
            data = self._serialize_data({
                **status,
                'last_heartbeat': datetime.now().isoformat()
            })
            return self.redis_client.setex(key, 300, data)  # 5분 TTL
        except Exception as e:
            print(f"Error setting worker status for {worker_id}: {e}")
            return False
    
    def get_worker_status(self, worker_id: str) -> Optional[Dict]:
        """워커 상태 조회."""
        try:
            key = self._make_key(self.config.WORKER_STATUS_PREFIX, worker_id)
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
        except Exception as e:
            print(f"Error getting worker status for {worker_id}: {e}")
            return None
    
    def get_all_worker_status(self) -> Dict[str, Dict]:
        """모든 워커 상태 조회."""
        try:
            pattern = self._make_key(self.config.WORKER_STATUS_PREFIX, "*")
            keys = self.redis_client.keys(pattern)
            result = {}
            for key in keys:
                worker_id = key.decode('utf-8').replace(self.config.WORKER_STATUS_PREFIX, '')
                data = self.redis_client.get(key)
                if data:
                    result[worker_id] = self._deserialize_data(data)
            return result
        except Exception as e:
            print(f"Error getting all worker status: {e}")
            return {}
    
    # 캐시 유틸리티
    def clear_cache(self, pattern: str = "*") -> int:
        """캐시 삭제."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict:
        """캐시 통계 정보."""
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'expired_keys': info.get('expired_keys', 0),
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Redis 연결 상태 확인."""
        try:
            return self.redis_client.ping()
        except Exception as e:
            print(f"Redis health check failed: {e}")
            return False


# 글로벌 Redis 매니저 인스턴스
redis_manager = RedisManager()
