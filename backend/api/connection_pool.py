"""
Connection pooling for external APIs
Optimizes performance and prevents connection exhaustion
"""
import aiohttp
from typing import Optional, Dict, Any
import asyncio
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class APIConnectionPool:
    """Manages connection pools for external API calls"""
    
    def __init__(self):
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.connectors: Dict[str, aiohttp.TCPConnector] = {}
        self.lock = asyncio.Lock()
        
    async def get_session(self, service_name: str, base_url: Optional[str] = None) -> aiohttp.ClientSession:
        """Get or create a session for a specific service"""
        async with self.lock:
            if service_name not in self.sessions:
                # Create connector with connection pooling
                connector = aiohttp.TCPConnector(
                    limit=100,  # Total connection pool size
                    limit_per_host=30,  # Connections per host
                    ttl_dns_cache=300,  # DNS cache TTL
                    keepalive_timeout=30,
                    force_close=False,
                    enable_cleanup_closed=True
                )
                
                # Create session with timeout settings
                timeout = aiohttp.ClientTimeout(
                    total=30,
                    connect=5,
                    sock_connect=5,
                    sock_read=10
                )
                
                session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'CoinLink/1.0',
                        'Accept': 'application/json'
                    }
                )
                
                self.sessions[service_name] = session
                self.connectors[service_name] = connector
                logger.info(f"Created connection pool for {service_name}")
                
            return self.sessions[service_name]
    
    @asynccontextmanager
    async def request(self, service_name: str, method: str, url: str, **kwargs):
        """Make an HTTP request with automatic retry and error handling"""
        session = await self.get_session(service_name)
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    yield response
                    return
            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request to {url} failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Request to {url} failed after {max_retries} attempts: {e}")
                    raise
    
    async def close_all(self):
        """Close all sessions and connectors"""
        async with self.lock:
            for service_name, session in self.sessions.items():
                await session.close()
                logger.info(f"Closed session for {service_name}")
            
            # Wait for connectors to close
            await asyncio.sleep(0.25)
            
            self.sessions.clear()
            self.connectors.clear()
    
    def get_stats(self, service_name: str) -> Dict[str, Any]:
        """Get connection pool statistics for a service"""
        if service_name not in self.connectors:
            return {"status": "not_initialized"}
        
        connector = self.connectors[service_name]
        return {
            "status": "active",
            "total_connections": len(connector._conns),
            "available_connections": len(connector._available),
            "limit": connector.limit,
            "limit_per_host": connector.limit_per_host
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all connection pools"""
        return {
            service: self.get_stats(service)
            for service in self.sessions.keys()
        }

# Global connection pool instance
api_pool = APIConnectionPool()

async def init_connection_pools():
    """Initialize connection pools on startup"""
    # Pre-create pools for known services
    services = [
        "coinbase",
        "coingecko", 
        "newsapi",
        "reddit",
        "messari"
    ]
    
    for service in services:
        await api_pool.get_session(service)
    
    logger.info("Connection pools initialized")

async def close_connection_pools():
    """Close all connection pools on shutdown"""
    await api_pool.close_all()
    logger.info("Connection pools closed")