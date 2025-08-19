"""
Observability middleware for request tracing and performance monitoring
Automatic trace ID generation, performance tracking, and error correlation
"""

import time
import uuid
import logging
from typing import Callable, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import set_trace_id, get_trace_id, set_user_id, api_logger
from .metrics import coinlink_metrics
from .sentry import add_breadcrumb, set_user_context
from ..auth.jwt import extract_bearer_token, jwt_service

logger = logging.getLogger(__name__)

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request tracing and performance monitoring
    """
    
    def __init__(self, app: Any, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/health', '/readyz', '/livez', '/metrics', '/docs', '/openapi.json']
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tracing for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate or extract trace ID
        trace_id = request.headers.get('X-Trace-ID') or str(uuid.uuid4())
        set_trace_id(trace_id)
        
        # Try to extract user ID from JWT token
        user_id = None
        authorization = request.headers.get('Authorization')
        if authorization:
            token = extract_bearer_token(authorization)
            if token:
                user_id = jwt_service.get_token_user_id(token)
                if user_id:
                    set_user_id(user_id)
                    set_user_context(user_id)
        
        # Add breadcrumb for request start
        add_breadcrumb(
            message=f"Request started: {request.method} {request.url.path}",
            category="http",
            data={
                'method': request.method,
                'url': str(request.url),
                'user_agent': request.headers.get('User-Agent'),
                'trace_id': trace_id,
                'user_id': user_id
            }
        )
        
        # Record request start time
        start_time = time.time()
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
            
        except Exception as e:
            error = e
            # Create error response
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_server_error",
                        "message": "Internal server error",
                        "trace_id": trace_id
                    }
                }
            )
            
            # Log error with context
            api_logger.error(
                f"Request error: {request.method} {request.url.path}",
                error_type=type(e).__name__,
                error_message=str(e),
                http_method=request.method,
                http_path=request.url.path,
                user_id=user_id
            )
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Add trace ID to response headers
        response.headers['X-Trace-ID'] = trace_id
        
        # Log request completion
        status_code = response.status_code
        api_logger.api_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.client.host if request.client else None
        )
        
        # Record metrics
        coinlink_metrics.record_api_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=status_code,
            duration=duration
        )
        
        # Add breadcrumb for request completion
        add_breadcrumb(
            message=f"Request completed: {request.method} {request.url.path} {status_code}",
            category="http",
            data={
                'status_code': status_code,
                'duration_ms': duration_ms,
                'trace_id': trace_id
            }
        )
        
        # Log SLA violations
        if duration_ms > 150:  # 150ms SLA target
            api_logger.warning(
                f"SLA violation: {request.method} {request.url.path} took {duration_ms:.2f}ms",
                sla_violation=True,
                target_ms=150,
                actual_ms=duration_ms,
                http_method=request.method,
                http_path=request.url.path
            )
        
        return response

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware specifically for collecting detailed metrics
    """
    
    def __init__(self, app: Any):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for metrics endpoint itself
        if request.url.path == '/metrics':
            return await call_next(request)
        
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        user_agent = request.headers.get('User-Agent', 'unknown')
        
        # Update active requests metric
        with coinlink_metrics.api_request_duration.labels(method=method, endpoint=path).time():
            response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record additional business metrics based on endpoint
        if path.startswith('/api/v2/market'):
            # Extract symbol from query params if present
            symbol = request.query_params.get('symbols', '').split(',')[0] if request.query_params.get('symbols') else 'unknown'
            coinlink_metrics.record_market_data_request(path, symbol)
        
        elif path.startswith('/api/v2/auth'):
            # Record auth metrics
            if path.endswith('/login') and response.status_code == 200:
                coinlink_metrics.record_auth_attempt('login', True)
                coinlink_metrics.record_token_issued('access')
                coinlink_metrics.record_token_issued('refresh')
            elif path.endswith('/login') and response.status_code >= 400:
                coinlink_metrics.record_auth_attempt('login', False)
            elif path.endswith('/signup') and response.status_code == 201:
                coinlink_metrics.record_auth_attempt('signup', True)
                coinlink_metrics.record_user_registration()
            elif path.endswith('/refresh') and response.status_code == 200:
                coinlink_metrics.record_token_issued('access')
                coinlink_metrics.record_token_issued('refresh')
        
        # Record rate limiting
        if response.status_code == 429:
            user_type = 'authenticated' if request.headers.get('Authorization') else 'anonymous'
            coinlink_metrics.record_rate_limit_exceeded(path, user_type)
        
        # Record errors
        if response.status_code >= 500:
            coinlink_metrics.record_error('http_5xx', 'error')
        elif response.status_code >= 400:
            coinlink_metrics.record_error('http_4xx', 'warning')
        
        return response

class WebSocketMetricsMiddleware:
    """
    Helper class for WebSocket metrics tracking
    """
    
    @staticmethod
    def record_connection(total: int, authenticated: int):
        """Record WebSocket connection metrics"""
        coinlink_metrics.update_websocket_connections(total, authenticated)
    
    @staticmethod
    def record_message(message_type: str, duration: float, success: bool):
        """Record WebSocket message metrics"""
        coinlink_metrics.record_websocket_message(message_type, duration, success)
        
        # Log SLA violation for WebSocket (250ms target)
        if duration > 0.25:  # 250ms
            api_logger.warning(
                f"WebSocket SLA violation: {message_type} took {duration*1000:.2f}ms",
                sla_violation=True,
                target_ms=250,
                actual_ms=duration*1000,
                message_type=message_type
            )

# Global instance for WebSocket metrics
websocket_metrics = WebSocketMetricsMiddleware()