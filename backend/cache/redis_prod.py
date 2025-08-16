"""
Production Redis Configuration - Enhanced caching layer
Non-invasive caching that preserves all agent operations
"""
import os
import redis.asyncio as redis
from typing import Optional, Any
import json
import asyncio
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class ProductionRedisCache:
    """Production-ready Redis cache with fallback mechanisms and connection pooling"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.connected = False
        self.connection_retries = 0
        self.max_retries = 3
        self.pool: Optional[redis.ConnectionPool] = None
        
    async def connect(self):
        """Connect to Redis with retry logic and connection pooling"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        for attempt in range(self.max_retries):
            try:
                # Create connection pool for better performance
                self.pool = redis.ConnectionPool.from_url(
                    redis_url,
                    max_connections=50,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPIDLE
                        2: 3,  # TCP_KEEPINTVL
                        3: 5,  # TCP_KEEPCNT
                    },
                    health_check_interval=30
                )
                
                self.client = redis.Redis(
                    connection_pool=self.pool,
                    encoding="utf-8",
                    decode_responses=True,
                    retry_on_timeout=True
                )
                
                # Test connection
                await self.client.ping()
                self.connected = True
                logger.info(f"Redis connected successfully to {redis_url}")
                return
                
            except Exception as e:
                self.connection_retries += 1
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Redis connection failed after all retries - operating without cache")
                    self.connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback"""
        if not self.connected or not self.client:
            return None
            
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value) if value.startswith('{') else value
            return None
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self.connected or not self.client:
            return False
            
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.debug(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.connected or not self.client:
            return False
            
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.connected or not self.client:
            return False
            
        try:
            return await self.client.exists(key) > 0
        except Exception:
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache"""
        if not self.connected or not self.client:
            return None
            
        try:
            return await self.client.incrby(key, amount)
        except Exception:
            return None
    
    async def get_connection_pool_stats(self) -> dict:
        """Get connection pool statistics for monitoring"""
        if not self.client or not self.pool:
            return {"status": "disconnected"}
            
        try:
            return {
                "status": "connected" if self.connected else "disconnected",
                "created_connections": self.pool.created_connections,
                "available_connections": len(self.pool._available_connections),
                "in_use_connections": len(self.pool._in_use_connections),
                "max_connections": self.pool.max_connections,
                "connection_retries": self.connection_retries
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {"status": "error"}
    
    async def close(self):
        """Gracefully close Redis connection and pool"""
        if self.client:
            await self.client.close()
            self.connected = False
        if self.pool:
            await self.pool.disconnect()
            self.pool = None

# Global cache instance
production_cache = ProductionRedisCache()

async def init_production_cache():
    """Initialize production cache on startup"""
    await production_cache.connect()

async def close_production_cache():
    """Close production cache on shutdown"""
    await production_cache.close()