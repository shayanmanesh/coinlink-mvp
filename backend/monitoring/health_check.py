"""
Production health check and monitoring endpoints for CoinLink
Provides comprehensive health status and metrics for monitoring
"""

import os
import time
import psutil
import asyncio
import aioredis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class HealthStatus(BaseModel):
    """Health check response model"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    uptime_seconds: float
    version: str
    environment: str
    checks: Dict[str, Dict[str, Any]]
    metrics: Optional[Dict[str, Any]] = None


class ComponentHealth:
    """Individual component health checker"""
    
    def __init__(self, name: str):
        self.name = name
        self.last_check_time = None
        self.last_status = None
        self.consecutive_failures = 0
        
    async def check(self) -> Dict[str, Any]:
        """Override in subclasses"""
        raise NotImplementedError


class RedisHealthCheck(ComponentHealth):
    """Redis connectivity and performance check"""
    
    def __init__(self):
        super().__init__("redis")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    async def check(self) -> Dict[str, Any]:
        try:
            start_time = time.time()
            
            # Try to connect and ping Redis
            redis = await aioredis.from_url(self.redis_url)
            await redis.ping()
            
            # Test write/read
            test_key = "health_check_test"
            test_value = str(time.time())
            await redis.set(test_key, test_value, ex=10)
            retrieved = await redis.get(test_key)
            
            # Get Redis info
            info = await redis.info()
            
            await redis.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "write_read_test": "passed" if retrieved == test_value.encode() else "failed"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self.consecutive_failures += 1
            return {
                "status": "unhealthy",
                "error": str(e),
                "consecutive_failures": self.consecutive_failures
            }


class CoinbaseWebSocketHealthCheck(ComponentHealth):
    """Coinbase WebSocket connection health check"""
    
    def __init__(self):
        super().__init__("coinbase_websocket")
        self.last_message_time = None
        self.message_count = 0
    
    async def check(self) -> Dict[str, Any]:
        try:
            # Check if WebSocket manager exists and is connected
            from backend.realtime.crypto_websocket import websocket_manager
            
            if websocket_manager and websocket_manager.is_connected:
                time_since_last = None
                if self.last_message_time:
                    time_since_last = (datetime.now() - self.last_message_time).total_seconds()
                
                status = "healthy"
                if time_since_last and time_since_last > 60:
                    status = "degraded"
                elif time_since_last and time_since_last > 300:
                    status = "unhealthy"
                
                return {
                    "status": status,
                    "connected": True,
                    "subscribed_symbols": len(websocket_manager.subscribed_symbols),
                    "message_count": self.message_count,
                    "seconds_since_last_message": time_since_last
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "WebSocket not connected"
                }
        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class APIHealthCheck(ComponentHealth):
    """External API connectivity checks"""
    
    def __init__(self):
        super().__init__("external_apis")
    
    async def check(self) -> Dict[str, Any]:
        results = {}
        
        # Check Coinbase API
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.coinbase.com/v2/exchange-rates",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    results["coinbase_api"] = {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "status_code": response.status
                    }
        except Exception as e:
            results["coinbase_api"] = {"status": "unhealthy", "error": str(e)}
        
        # Check if HuggingFace is accessible (for sentiment analysis)
        if os.getenv("HF_TOKEN"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://huggingface.co/api/models/ProsusAI/finbert",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        results["huggingface"] = {
                            "status": "healthy" if response.status == 200 else "degraded",
                            "status_code": response.status
                        }
            except Exception as e:
                results["huggingface"] = {"status": "degraded", "error": str(e)}
        
        # Overall status
        all_healthy = all(api.get("status") == "healthy" for api in results.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "apis": results
        }


class SystemHealthCheck(ComponentHealth):
    """System resources health check"""
    
    def __init__(self):
        super().__init__("system")
        self.start_time = time.time()
    
    async def check(self) -> Dict[str, Any]:
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85:
                status = "degraded"
            elif cpu_percent > 95 or memory.percent > 95:
                status = "unhealthy"
            
            return {
                "status": status,
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory.percent, 2),
                "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "disk_percent": round(disk.percent, 2),
                "process_memory_mb": round(process_memory.rss / 1024 / 1024, 2),
                "uptime_seconds": round(time.time() - self.start_time, 2)
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class HealthMonitor:
    """Main health monitoring coordinator"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = {
            "redis": RedisHealthCheck(),
            "websocket": CoinbaseWebSocketHealthCheck(),
            "external_apis": APIHealthCheck(),
            "system": SystemHealthCheck()
        }
        self.last_full_check = None
        self.cache_duration = 10  # Cache health results for 10 seconds
    
    async def get_health_status(self, detailed: bool = False) -> HealthStatus:
        """Get comprehensive health status"""
        
        # Use cached result if available and fresh
        if self.last_full_check and not detailed:
            if (time.time() - self.last_full_check["timestamp"]) < self.cache_duration:
                return HealthStatus(**self.last_full_check)
        
        # Run all health checks in parallel
        check_results = {}
        tasks = []
        
        for name, checker in self.checks.items():
            tasks.append(self._run_check(name, checker))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(self.checks.keys(), results):
            if isinstance(result, Exception):
                check_results[name] = {
                    "status": "unhealthy",
                    "error": str(result)
                }
            else:
                check_results[name] = result
        
        # Determine overall status
        statuses = [check.get("status", "unhealthy") for check in check_results.values()]
        
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        # Compile metrics if detailed
        metrics = None
        if detailed:
            metrics = await self._get_detailed_metrics()
        
        health_status = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "production"),
            "checks": check_results,
            "metrics": metrics
        }
        
        # Cache the result
        self.last_full_check = health_status
        self.last_full_check["timestamp"] = time.time()
        
        return HealthStatus(**health_status)
    
    async def _run_check(self, name: str, checker: ComponentHealth) -> Dict[str, Any]:
        """Run a single health check with timeout"""
        try:
            return await asyncio.wait_for(checker.check(), timeout=5.0)
        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "error": "Health check timed out"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed application metrics"""
        try:
            # Import metrics from the application
            from backend.monitoring.logging_config import metrics_logger
            
            # Get recent metrics (this would typically query a metrics store)
            return {
                "requests_per_minute": 0,  # Would be calculated from actual metrics
                "average_response_time_ms": 0,
                "active_websocket_connections": 0,
                "alerts_triggered_last_hour": 0,
                "cache_hit_rate": 0
            }
        except Exception as e:
            logger.error(f"Failed to get detailed metrics: {e}")
            return {}


# Create router for health endpoints
health_router = APIRouter(tags=["monitoring"])
health_monitor = HealthMonitor()


@health_router.get("/health")
async def health_check():
    """Basic health check endpoint for load balancers"""
    try:
        health_status = await health_monitor.get_health_status(detailed=False)
        
        if health_status.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status.dict()
            )
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": str(e)}
        )


@health_router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all metrics"""
    try:
        return await health_monitor.get_health_status(detailed=True)
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": str(e)}
        )


@health_router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@health_router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe endpoint"""
    health_status = await health_monitor.get_health_status(detailed=False)
    
    if health_status.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": health_status.checks}
        )
    
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@health_router.get("/metrics")
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint"""
    # This would typically return metrics in Prometheus format
    # For now, return JSON metrics
    health_status = await health_monitor.get_health_status(detailed=True)
    return {
        "metrics": health_status.metrics,
        "health": health_status.status,
        "timestamp": health_status.timestamp
    }


# Export router and monitor
__all__ = ['health_router', 'health_monitor', 'HealthMonitor']