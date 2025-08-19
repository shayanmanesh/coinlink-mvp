"""
Prometheus metrics for production observability
Custom metrics for API performance, business logic, and system health
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import Request, Response
import psutil
import asyncio

from ..config.settings import settings

logger = logging.getLogger(__name__)

class CoinLinkMetrics:
    """
    Custom metrics for CoinLink application
    Tracks business logic, performance, and system health
    """
    
    def __init__(self):
        # API Performance Metrics
        self.api_requests_total = Counter(
            'coinlink_api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.api_request_duration = Histogram(
            'coinlink_api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.05, 0.1, 0.15, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]  # SLA target: p95 < 150ms
        )
        
        # WebSocket Metrics
        self.websocket_connections_total = Gauge(
            'coinlink_websocket_connections_total',
            'Total number of active WebSocket connections'
        )
        
        self.websocket_connections_authenticated = Gauge(
            'coinlink_websocket_connections_authenticated',
            'Number of authenticated WebSocket connections'
        )
        
        self.websocket_message_duration = Histogram(
            'coinlink_websocket_message_duration_seconds',
            'WebSocket message processing duration',
            ['message_type'],
            buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]  # SLA target: p95 < 250ms
        )
        
        self.websocket_messages_total = Counter(
            'coinlink_websocket_messages_total',
            'Total WebSocket messages processed',
            ['message_type', 'status']
        )
        
        # Authentication Metrics
        self.auth_attempts_total = Counter(
            'coinlink_auth_attempts_total',
            'Total authentication attempts',
            ['method', 'status']  # method: login/signup/refresh, status: success/failure
        )
        
        self.auth_tokens_issued_total = Counter(
            'coinlink_auth_tokens_issued_total',
            'Total JWT tokens issued',
            ['token_type']  # access/refresh
        )
        
        self.auth_sessions_active = Gauge(
            'coinlink_auth_sessions_active',
            'Number of active user sessions'
        )
        
        # Database Metrics
        self.database_connections_active = Gauge(
            'coinlink_database_connections_active',
            'Active database connections'
        )
        
        self.database_query_duration = Histogram(
            'coinlink_database_query_duration_seconds',
            'Database query duration',
            ['operation'],  # select/insert/update/delete
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )
        
        self.database_errors_total = Counter(
            'coinlink_database_errors_total',
            'Total database errors',
            ['error_type']
        )
        
        # Business Logic Metrics
        self.users_registered_total = Counter(
            'coinlink_users_registered_total',
            'Total users registered'
        )
        
        self.users_active_24h = Gauge(
            'coinlink_users_active_24h',
            'Number of users active in last 24 hours'
        )
        
        self.price_alerts_triggered_total = Counter(
            'coinlink_price_alerts_triggered_total',
            'Total price alerts triggered',
            ['symbol', 'condition']
        )
        
        self.market_data_requests_total = Counter(
            'coinlink_market_data_requests_total',
            'Total market data API requests',
            ['endpoint', 'symbol']
        )
        
        # System Health Metrics
        self.system_cpu_usage = Gauge(
            'coinlink_system_cpu_usage_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory_usage = Gauge(
            'coinlink_system_memory_usage_bytes',
            'System memory usage in bytes'
        )
        
        self.system_disk_usage = Gauge(
            'coinlink_system_disk_usage_percent',
            'System disk usage percentage'
        )
        
        # Redis Metrics
        self.redis_connections_active = Gauge(
            'coinlink_redis_connections_active',
            'Active Redis connections'
        )
        
        self.redis_operations_total = Counter(
            'coinlink_redis_operations_total',
            'Total Redis operations',
            ['operation']  # get/set/del/pub/sub
        )
        
        self.redis_operation_duration = Histogram(
            'coinlink_redis_operation_duration_seconds',
            'Redis operation duration',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        # Error Tracking Metrics
        self.errors_total = Counter(
            'coinlink_errors_total',
            'Total application errors',
            ['error_type', 'severity']
        )
        
        self.rate_limit_exceeded_total = Counter(
            'coinlink_rate_limit_exceeded_total',
            'Total rate limit exceeded events',
            ['endpoint', 'user_type']
        )
        
        # Application Info
        self.app_info = Info(
            'coinlink_app_info',
            'Application information'
        )
        
        # Set application info
        self.app_info.info({
            'version': '2.0.0',
            'environment': 'production',
            'features': 'jwt_auth,websockets,redis_pubsub,postgresql'
        })
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics"""
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint, 
            status_code=status_code
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_websocket_message(self, message_type: str, duration: float, success: bool):
        """Record WebSocket message metrics"""
        status = "success" if success else "error"
        
        self.websocket_messages_total.labels(
            message_type=message_type,
            status=status
        ).inc()
        
        self.websocket_message_duration.labels(
            message_type=message_type
        ).observe(duration)
    
    def update_websocket_connections(self, total: int, authenticated: int):
        """Update WebSocket connection counts"""
        self.websocket_connections_total.set(total)
        self.websocket_connections_authenticated.set(authenticated)
    
    def record_auth_attempt(self, method: str, success: bool):
        """Record authentication attempt"""
        status = "success" if success else "failure"
        self.auth_attempts_total.labels(
            method=method,
            status=status
        ).inc()
    
    def record_token_issued(self, token_type: str):
        """Record JWT token issuance"""
        self.auth_tokens_issued_total.labels(token_type=token_type).inc()
    
    def update_active_sessions(self, count: int):
        """Update active sessions count"""
        self.auth_sessions_active.set(count)
    
    def record_database_query(self, operation: str, duration: float):
        """Record database query metrics"""
        self.database_query_duration.labels(operation=operation).observe(duration)
    
    def record_database_error(self, error_type: str):
        """Record database error"""
        self.database_errors_total.labels(error_type=error_type).inc()
    
    def update_database_connections(self, count: int):
        """Update database connection count"""
        self.database_connections_active.set(count)
    
    def record_user_registration(self):
        """Record user registration"""
        self.users_registered_total.inc()
    
    def update_active_users_24h(self, count: int):
        """Update 24h active users count"""
        self.users_active_24h.set(count)
    
    def record_price_alert(self, symbol: str, condition: str):
        """Record price alert triggered"""
        self.price_alerts_triggered_total.labels(
            symbol=symbol,
            condition=condition
        ).inc()
    
    def record_market_data_request(self, endpoint: str, symbol: str = ""):
        """Record market data API request"""
        self.market_data_requests_total.labels(
            endpoint=endpoint,
            symbol=symbol
        ).inc()
    
    def record_redis_operation(self, operation: str, duration: float):
        """Record Redis operation metrics"""
        self.redis_operations_total.labels(operation=operation).inc()
        self.redis_operation_duration.labels(operation=operation).observe(duration)
    
    def update_redis_connections(self, count: int):
        """Update Redis connection count"""
        self.redis_connections_active.set(count)
    
    def record_error(self, error_type: str, severity: str):
        """Record application error"""
        self.errors_total.labels(
            error_type=error_type,
            severity=severity
        ).inc()
    
    def record_rate_limit_exceeded(self, endpoint: str, user_type: str):
        """Record rate limit exceeded event"""
        self.rate_limit_exceeded_total.labels(
            endpoint=endpoint,
            user_type=user_type
        ).inc()
    
    async def update_system_metrics(self):
        """Update system health metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_usage.set(disk_percent)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")


# Global metrics instance
coinlink_metrics = CoinLinkMetrics()


def create_instrumentator() -> Instrumentator:
    """
    Create and configure FastAPI Instrumentator for automatic metrics
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/readyz", "/livez"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="coinlink_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add default metrics
    instrumentator.add(metrics.default())
    instrumentator.add(metrics.combined_size())
    
    # Add custom metric for SLA tracking
    def track_sla_compliance():
        def instrumentation(info: metrics.Info) -> None:
            duration = info.modified_duration
            
            # Track SLA compliance (150ms for REST API)
            if duration > 0.150:  # 150ms
                coinlink_metrics.record_error("sla_violation", "performance")
            
            # Record in our custom metrics
            coinlink_metrics.record_api_request(
                method=info.method,
                endpoint=info.modified_handler,
                status_code=info.response.status_code,
                duration=duration
            )
        
        return instrumentation
    
    instrumentator.add(track_sla_compliance())
    
    return instrumentator


async def start_system_metrics_collection():
    """Start background task for system metrics collection"""
    logger.info("Starting system metrics collection")
    
    while True:
        try:
            await coinlink_metrics.update_system_metrics()
            await asyncio.sleep(30)  # Update every 30 seconds
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in system metrics collection: {e}")
            await asyncio.sleep(60)  # Wait longer on error


def get_metrics_response() -> Response:
    """Get Prometheus metrics response"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )