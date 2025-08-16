"""
Health check monitoring - Non-invasive system health tracking
Preserves all existing agent operations
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import aiohttp
import redis.asyncio as redis
from config.settings import settings

class HealthMonitor:
    """Non-invasive health monitoring layer"""
    
    def __init__(self):
        self.checks = {}
        self.last_check = None
        
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity without affecting cache operations"""
        try:
            client = redis.from_url(settings.REDIS_URL)
            start = time.time()
            await client.ping()
            latency = (time.time() - start) * 1000
            await client.close()
            return {"status": "healthy", "latency_ms": round(latency, 2)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_coinbase_api(self) -> Dict[str, Any]:
        """Check Coinbase API availability without affecting agents"""
        try:
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get(
                    "https://api.coinbase.com/v2/exchange-rates?currency=BTC",
                    timeout=5
                ) as response:
                    latency = (time.time() - start) * 1000
                    if response.status == 200:
                        return {"status": "healthy", "latency_ms": round(latency, 2)}
                    return {"status": "degraded", "http_status": response.status}
        except asyncio.TimeoutError:
            return {"status": "timeout", "error": "Request timed out"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_websocket_connections(self) -> Dict[str, Any]:
        """Monitor WebSocket connection count without interference"""
        try:
            # Import dynamically to avoid circular dependency
            from api.websocket import manager
            active = len(manager.active_connections)
            return {
                "status": "healthy",
                "active_connections": active,
                "capacity_used": f"{(active/100)*100:.1f}%"  # Assume 100 max
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    async def check_ml_models(self) -> Dict[str, Any]:
        """Check ML model availability without triggering inference"""
        try:
            from sentiment.analyzer import BitcoinSentimentService
            # Just check if model is loaded, don't run inference
            if hasattr(BitcoinSentimentService, '_instance'):
                return {"status": "loaded", "model": "finbert"}
            return {"status": "not_initialized"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Aggregate all health checks without blocking operations"""
        checks = await asyncio.gather(
            self.check_redis(),
            self.check_coinbase_api(),
            self.check_websocket_connections(),
            self.check_ml_models(),
            return_exceptions=True
        )
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {
                "redis": checks[0] if not isinstance(checks[0], Exception) else {"status": "error"},
                "coinbase_api": checks[1] if not isinstance(checks[1], Exception) else {"status": "error"},
                "websocket": checks[2] if not isinstance(checks[2], Exception) else {"status": "error"},
                "ml_models": checks[3] if not isinstance(checks[3], Exception) else {"status": "error"}
            }
        }
        
        # Determine overall status
        statuses = [s.get("status", "unknown") for s in health_status["services"].values()]
        if any(s in ["unhealthy", "error"] for s in statuses):
            health_status["overall_status"] = "unhealthy"
        elif any(s in ["degraded", "timeout"] for s in statuses):
            health_status["overall_status"] = "degraded"
            
        self.last_check = health_status
        return health_status

# Singleton instance
health_monitor = HealthMonitor()