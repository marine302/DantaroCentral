"""
Cache service for storing and retrieving cached data.

This service provides a unified interface for caching
analysis results and market data to improve performance.
"""
from typing import Any, Optional
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache service for storing analysis results and market data.
    
    In production, this would use Redis. For development,
    we'll use an in-memory cache.
    """
    
    def __init__(self):
        # In-memory cache for development
        self._cache: dict = {}
        self._expiry: dict = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            # Check if key exists and not expired
            if key in self._cache:
                if key in self._expiry:
                    if datetime.utcnow() > self._expiry[key]:
                        # Remove expired entry
                        del self._cache[key]
                        del self._expiry[key]
                        return None
                
                logger.debug(f"Cache hit for key: {key}")
                return self._cache[key]
            
            logger.debug(f"Cache miss for key: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._cache[key] = value
            
            if ttl > 0:
                self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
            
            logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        try:
            if key in self._cache:
                del self._cache[key]
                if key in self._expiry:
                    del self._expiry[key]
                logger.debug(f"Deleted cache key: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete from cache: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful
        """
        try:
            self._cache.clear()
            self._expiry.clear()
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache (and not expired).
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and not expired
        """
        try:
            if key in self._cache:
                if key in self._expiry:
                    if datetime.utcnow() > self._expiry[key]:
                        # Remove expired entry
                        del self._cache[key]
                        del self._expiry[key]
                        return False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check cache existence: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            now = datetime.utcnow()
            expired_count = 0
            
            # Count expired entries
            for key, expiry_time in self._expiry.items():
                if now > expiry_time:
                    expired_count += 1
            
            return {
                'total_keys': len(self._cache),
                'expired_keys': expired_count,
                'active_keys': len(self._cache) - expired_count,
                'memory_usage': 'N/A (in-memory cache)',
                'hit_rate': 'N/A (not tracked in dev mode)'
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# Global cache service instance
cache_service = CacheService()
