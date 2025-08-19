"""
Security middleware for API protection
Production-ready security measures for coin.link
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import fastapi_limiter
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from typing import Dict, Optional, List, Any
import logging
import time
import json
import hashlib
import re
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import uuid

# Configure security logger
security_logger = logging.getLogger("coinlink.security")
security_logger.setLevel(logging.INFO)

# Request logger for monitoring
request_logger = logging.getLogger("coinlink.requests")
request_logger.setLevel(logging.INFO)


class SecurityMiddleware:
    """Comprehensive security middleware for API protection"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Rate limiting configuration per endpoint
        self.rate_limits = {
            "/api/chat": "20/minute",
            "/api/bitcoin/price": "60/minute",
            "/api/bitcoin/sentiment": "30/minute",
            "/api/bitcoin/market-summary": "30/minute",
            "/api/bitcoin/analyze": "10/minute",
            "/api/bitcoin/news": "30/minute",
            "/api/alerts": "30/minute",
            "/api/alerts/history": "30/minute",
            "/api/chat/history": "30/minute",
            "/api/connections": "60/minute",
            "/api/prompts": "60/minute",
            "/api/correlation": "60/minute",
            "/api/sentiment/test": "5/minute",
            "/api/debug/tick": "10/minute",
            "/health": "120/minute",
            "/": "120/minute",
            # Health endpoints
            "/readyz": "60/minute",
            "/livez": "120/minute",
            # Auth endpoints with stricter limits
            "/api/v2/auth/signup": "5/minute",
            "/api/v2/auth/login": "10/minute",
            "/api/v2/auth/refresh": "20/minute",
            "/api/v2/auth/logout": "20/minute",
            "/api/v2/auth/verify": "60/minute",
            "/api/v2/auth/rate-limit": "30/minute",
            # Metrics and monitoring
            "/metrics": "60/minute",
            "/api/monitoring/unified": "30/minute",
        }
        
        # Track request patterns for anomaly detection
        self.request_patterns = defaultdict(list)
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r"(?i)(script|eval|exec|system|cmd|shell)",  # Code injection
            r"(?i)(union|select|insert|drop|delete|update|alter)",  # SQL injection
            r"(?i)(\.\./|\.\.\\)",  # Path traversal
            r"(?i)(javascript:|data:text/html)",  # XSS attempts
            r"(?i)(passwd|shadow|etc/)",  # System file access
        ]
        
        # Initialize rate limiter (fallback to slowapi if Redis not available)
        self.limiter = Limiter(key_func=self.get_client_identifier)
        
    async def initialize_redis(self):
        """Initialize Redis connection for rate limiting"""
        if self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                await self.redis_client.ping()
                security_logger.info("Redis connection established for rate limiting")
                
                # Initialize FastAPI-Limiter with Redis
                await FastAPILimiter.init(self.redis_client)
                security_logger.info("FastAPI-Limiter initialized with Redis backend")
                
            except Exception as e:
                security_logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
                security_logger.warning("Rate limiting will degrade gracefully without Redis")
                self.redis_client = None
    
    async def close_redis(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            await FastAPILimiter.close()
    
    def get_rate_limiter(self, path: str):
        """Get rate limiter for specific path"""
        rate_limit = self.get_rate_limit(path)
        return RateLimiter(times=int(rate_limit.split('/')[0]), 
                          seconds=60 if 'minute' in rate_limit else 1)
        
    def get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get real IP from various headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def log_request(self, request: Request, response_time: float = None, status_code: int = None):
        """Log request for monitoring and analysis"""
        client_id = self.get_client_identifier(request)
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "origin": request.headers.get("Origin", "unknown"),
            "referer": request.headers.get("Referer", "unknown"),
        }
        
        if response_time:
            log_data["response_time_ms"] = round(response_time * 1000, 2)
        
        if status_code:
            log_data["status_code"] = status_code
        
        # Log as JSON for easy parsing
        request_logger.info(json.dumps(log_data))
        
        # Track patterns for anomaly detection
        self.track_request_pattern(client_id, request)
    
    def track_request_pattern(self, client_id: str, request: Request):
        """Track request patterns for anomaly detection"""
        now = time.time()
        
        # Store request timestamp
        self.request_patterns[client_id].append({
            "timestamp": now,
            "path": request.url.path,
            "method": request.method
        })
        
        # Clean old entries (keep last 5 minutes)
        cutoff = now - 300
        self.request_patterns[client_id] = [
            r for r in self.request_patterns[client_id] 
            if r["timestamp"] > cutoff
        ]
        
        # Check for suspicious patterns
        recent_requests = self.request_patterns[client_id]
        
        # Detect rapid-fire requests (more than 100 in 1 minute)
        one_minute_ago = now - 60
        recent_count = sum(1 for r in recent_requests if r["timestamp"] > one_minute_ago)
        
        if recent_count > 100:
            security_logger.warning(f"Suspicious activity detected from {client_id}: {recent_count} requests in 1 minute")
            self.blocked_ips.add(client_id)
    
    def validate_input(self, data: Any, endpoint: str) -> bool:
        """Validate input data for security threats"""
        if isinstance(data, dict):
            return self._validate_dict(data)
        elif isinstance(data, str):
            return self._validate_string(data)
        elif isinstance(data, list):
            return all(self.validate_input(item, endpoint) for item in data)
        return True
    
    def _validate_dict(self, data: Dict) -> bool:
        """Recursively validate dictionary inputs"""
        for key, value in data.items():
            # Check key for injection attempts
            if not self._validate_string(str(key)):
                return False
            # Recursively check value
            if not self.validate_input(value, ""):
                return False
        return True
    
    def _validate_string(self, text: str) -> bool:
        """Check string for malicious patterns"""
        if not text:
            return True
        
        # Check against suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text):
                security_logger.warning(f"Potentially malicious input detected: {text[:100]}")
                return False
        
        # Check for excessive length (prevent DoS)
        if len(text) > 10000:
            security_logger.warning(f"Input exceeds maximum length: {len(text)} characters")
            return False
        
        return True
    
    def is_blocked(self, request: Request) -> bool:
        """Check if client is blocked"""
        client_id = self.get_client_identifier(request)
        return client_id in self.blocked_ips
    
    def get_rate_limit(self, path: str) -> str:
        """Get rate limit for specific path"""
        # Find matching rate limit
        for pattern, limit in self.rate_limits.items():
            if path.startswith(pattern):
                return limit
        # Default rate limit
        return "100/minute"


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with standardized JSON response"""
    trace_id = str(uuid.uuid4())
    
    # Log the rate limit event
    security_logger.warning(f"Rate limit exceeded for {request.client.host if request.client else 'unknown'} on {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "rate_limit_exceeded", 
                "message": "Too many requests. Please try again later.",
                "details": {
                    "retry_after": "60 seconds",
                    "endpoint": request.url.path
                },
                "trace_id": trace_id
            }
        },
        headers={"Retry-After": "60"}
    )


class RequestLoggingMiddleware:
    """Middleware for comprehensive request logging"""
    
    async def __call__(self, request: Request, call_next):
        """Log all requests with timing information"""
        start_time = time.time()
        
        # Log incoming request
        security_middleware = request.app.state.security_middleware
        await security_middleware.log_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log completed request
        await security_middleware.log_request(
            request, 
            response_time=response_time,
            status_code=response.status_code
        )
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class InputValidationMiddleware:
    """Middleware for input validation"""
    
    async def __call__(self, request: Request, call_next):
        """Validate all incoming request data"""
        security_middleware = request.app.state.security_middleware
        
        # Check if client is blocked
        if security_middleware.is_blocked(request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Validate request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Get body
                body = await request.body()
                if body:
                    # Store original body for later use
                    request._body = body
                    
                    # Parse and validate JSON
                    try:
                        data = json.loads(body)
                        if not security_middleware.validate_input(data, request.url.path):
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Invalid input detected"}
                            )
                    except json.JSONDecodeError:
                        # Not JSON, could be form data or other format
                        # Validate as string
                        if not security_middleware._validate_string(body.decode('utf-8', errors='ignore')):
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Invalid input detected"}
                            )
            except Exception as e:
                security_logger.error(f"Error validating request body: {e}")
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if not security_middleware._validate_string(key) or not security_middleware._validate_string(value):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid query parameters"}
                )
        
        # Process request
        response = await call_next(request)
        return response


class APIKeyValidator:
    """Validate and manage API keys"""
    
    def __init__(self):
        self.required_keys = {
            "COINBASE_API_KEY": "Coinbase API",
            "COINBASE_API_SECRET": "Coinbase Secret",
            "HF_TOKEN": "Hugging Face Token",
            "NEWSAPI_API_KEY": "News API Key",
        }
        self.optional_keys = {
            "COINBASE_KEY_JSON": "Coinbase Advanced Trade Key",
            "COINGECKO_API_KEY": "CoinGecko API Key",
            "REDDIT_CLIENT_ID": "Reddit Client ID",
            "REDDIT_API_SECRET": "Reddit API Secret",
            "MESSARI_API_KEY": "Messari API Key",
        }
        
    def validate_environment(self) -> Dict[str, bool]:
        """Validate all API keys are properly loaded"""
        import os
        results = {}
        
        # Check required keys
        for key, name in self.required_keys.items():
            value = os.getenv(key)
            if value and len(value) > 0:
                results[name] = True
                security_logger.info(f"✓ {name} loaded successfully")
            else:
                results[name] = False
                security_logger.error(f"✗ {name} not found in environment")
        
        # Check optional keys
        for key, name in self.optional_keys.items():
            value = os.getenv(key)
            if value and len(value) > 0:
                results[name] = True
                security_logger.info(f"✓ {name} loaded (optional)")
            else:
                results[name] = None
                security_logger.info(f"- {name} not configured (optional)")
        
        return results
    
    def mask_key(self, key: str) -> str:
        """Mask API key for logging"""
        if not key or len(key) < 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"


# Export middleware instances
security_middleware = SecurityMiddleware()
request_logging_middleware = RequestLoggingMiddleware()
input_validation_middleware = InputValidationMiddleware()
api_key_validator = APIKeyValidator()