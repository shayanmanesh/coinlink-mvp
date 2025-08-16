"""
Performance metrics tracking for backend monitoring
"""
import time
import asyncio
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Track and report performance metrics"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.request_times: deque = deque(maxlen=window_size)
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.start_time = time.time()
        
    def record_request(self, duration_ms: float):
        """Record a request duration"""
        self.request_times.append({
            'timestamp': time.time(),
            'duration_ms': duration_ms
        })
    
    def record_cache_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1
    
    def record_api_call(self, service: str):
        """Record an API call to an external service"""
        self.api_calls[service] = self.api_calls.get(service, 0) + 1
    
    def record_error(self, error_type: str):
        """Record an error occurrence"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        uptime_seconds = time.time() - self.start_time
        
        # Calculate request statistics
        if self.request_times:
            durations = [r['duration_ms'] for r in self.request_times]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # Calculate requests per second (last minute)
            recent_requests = [r for r in self.request_times 
                             if r['timestamp'] > time.time() - 60]
            rps = len(recent_requests) / min(60, uptime_seconds)
        else:
            avg_duration = max_duration = min_duration = rps = 0
        
        # Calculate cache hit rate
        total_cache_ops = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_formatted": str(timedelta(seconds=int(uptime_seconds))),
            "request_metrics": {
                "total_requests": len(self.request_times),
                "requests_per_second": round(rps, 2),
                "avg_duration_ms": round(avg_duration, 2),
                "max_duration_ms": round(max_duration, 2),
                "min_duration_ms": round(min_duration, 2)
            },
            "cache_metrics": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate_percent": round(cache_hit_rate, 2)
            },
            "api_calls": self.api_calls,
            "error_counts": self.error_counts
        }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        self.request_times.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls.clear()
        self.error_counts.clear()
        self.start_time = time.time()

# Global metrics instance
performance_metrics = PerformanceMetrics()

class RequestTimer:
    """Context manager for timing requests"""
    
    def __init__(self, metrics: Optional[PerformanceMetrics] = None):
        self.metrics = metrics or performance_metrics
        self.start_time = None
        
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics.record_request(duration_ms)
        
        if exc_type:
            self.metrics.record_error(exc_type.__name__)

def track_request():
    """Decorator for tracking request performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with RequestTimer():
                return await func(*args, **kwargs)
        return wrapper
    return decorator