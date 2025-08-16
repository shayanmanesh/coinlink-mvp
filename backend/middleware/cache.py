"""
CDN and Caching Middleware - Non-invasive performance layer
Adds caching headers without modifying agent responses
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import hashlib
import json
from typing import Callable
from datetime import datetime, timedelta

class CacheMiddleware:
    """Add caching headers to optimize CDN delivery"""
    
    # Cache durations for different endpoints (in seconds)
    CACHE_RULES = {
        "/api/bitcoin/price": 10,  # 10 seconds for price data
        "/api/bitcoin/sentiment": 60,  # 1 minute for sentiment
        "/api/bitcoin/market-summary": 30,  # 30 seconds for summary
        "/api/bitcoin/news": 300,  # 5 minutes for news
        "/api/prompts": 60,  # 1 minute for prompts
        "/health": 5,  # 5 seconds for health checks
        "/": 3600,  # 1 hour for root
    }
    
    # Static assets get long cache
    STATIC_EXTENSIONS = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2']
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and add appropriate cache headers"""
        
        # Get response from existing handlers
        response = await call_next(request)
        
        # Don't cache WebSocket or POST requests
        if request.url.path == "/ws" or request.method == "POST":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        
        # Check if path matches cache rules
        cache_duration = self.CACHE_RULES.get(request.url.path)
        
        # Check for static assets
        if not cache_duration:
            for ext in self.STATIC_EXTENSIONS:
                if request.url.path.endswith(ext):
                    cache_duration = 86400 * 30  # 30 days for static assets
                    break
        
        if cache_duration:
            # Add cache headers
            response.headers["Cache-Control"] = f"public, max-age={cache_duration}"
            
            # Add ETag for conditional requests
            if hasattr(response, 'body'):
                etag = hashlib.md5(response.body).hexdigest()
                response.headers["ETag"] = f'"{etag}"'
                
                # Check if client has matching ETag
                if request.headers.get("If-None-Match") == f'"{etag}"':
                    return Response(status_code=304)  # Not Modified
            
            # Add expires header
            expires = datetime.utcnow() + timedelta(seconds=cache_duration)
            response.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        else:
            # Default to no-cache for unmatched paths
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        
        # Add CDN-friendly headers
        response.headers["Vary"] = "Accept-Encoding"
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        return response

def setup_caching(app):
    """Setup caching middleware on FastAPI app"""
    app.middleware("http")(CacheMiddleware())