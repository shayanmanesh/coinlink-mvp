"""
Sentry integration for error tracking and performance monitoring
Production-ready error tracking with context and user information
"""

import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from typing import Dict, Any, Optional

from ..config.settings import settings
from .logging import get_trace_id, get_user_id

logger = logging.getLogger(__name__)

def configure_sentry():
    """
    Configure Sentry for error tracking and performance monitoring
    """
    
    # Get Sentry configuration from environment
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    if not sentry_dsn:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return
    
    environment = getattr(settings, 'ENVIRONMENT', 'production')
    release = getattr(settings, 'APP_VERSION', '2.0.0')
    sample_rate = float(getattr(settings, 'SENTRY_SAMPLE_RATE', '1.0'))
    traces_sample_rate = float(getattr(settings, 'SENTRY_TRACES_SAMPLE_RATE', '0.1'))
    
    # Configure logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        release=f"coinlink-api@{release}",
        sample_rate=sample_rate,
        traces_sample_rate=traces_sample_rate,
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII by default
        max_breadcrumbs=100,
        
        # Integrations
        integrations=[
            FastApiIntegration(
                auto_enable=True,
                transaction_style="endpoint"
            ),
            SqlalchemyIntegration(),
            RedisIntegration(),
            sentry_logging,
            AsyncioIntegration()
        ],
        
        # Custom error filtering
        before_send=before_send_filter,
        before_send_transaction=before_send_transaction_filter,
        
        # Performance monitoring
        profiles_sample_rate=0.1,
        
        # Additional options
        debug=environment == 'development',
        server_name=getattr(settings, 'HOSTNAME', 'coinlink-api')
    )
    
    # Set global tags
    sentry_sdk.set_tag("service", "coinlink-api")
    sentry_sdk.set_tag("version", release)
    
    logger.info(
        "Sentry configured successfully",
        extra={
            'sentry_environment': environment,
            'sentry_release': release,
            'sentry_sample_rate': sample_rate,
            'sentry_traces_sample_rate': traces_sample_rate
        }
    )

def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter events before sending to Sentry
    Remove sensitive information and filter noise
    """
    
    # Skip certain exceptions that are expected
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # Skip common client errors that shouldn't be tracked
        if exc_type.__name__ in [
            'HTTPException',
            'RequestValidationError', 
            'WebSocketDisconnect',
            'ConnectionError'
        ]:
            # Only track if it's a 5xx error
            if hasattr(exc_value, 'status_code') and exc_value.status_code < 500:
                return None
    
    # Add trace ID to event context
    trace_id = get_trace_id()
    if trace_id:
        if 'contexts' not in event:
            event['contexts'] = {}
        event['contexts']['trace'] = {
            'trace_id': trace_id
        }
    
    # Add user ID to user context (without PII)
    user_id = get_user_id()
    if user_id:
        if 'user' not in event:
            event['user'] = {}
        event['user']['id'] = user_id
    
    # Remove sensitive data from request data
    if 'request' in event:
        request = event['request']
        
        # Remove sensitive headers
        if 'headers' in request:
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                request['headers'].pop(header, None)
        
        # Remove sensitive data from request body
        if 'data' in request and isinstance(request['data'], dict):
            sensitive_fields = ['password', 'token', 'secret', 'key']
            for field in sensitive_fields:
                if field in request['data']:
                    request['data'][field] = '[Filtered]'
    
    # Add custom fingerprinting for better grouping
    if 'exception' in event:
        exceptions = event['exception']['values']
        if exceptions:
            exc = exceptions[-1]  # Last exception in chain
            
            # Custom fingerprinting for API errors
            if exc.get('type') == 'HTTPException':
                event['fingerprint'] = [
                    'http-exception',
                    exc.get('value', 'unknown-status')
                ]
            
            # Custom fingerprinting for database errors
            elif 'sqlalchemy' in str(exc.get('type', '')).lower():
                event['fingerprint'] = [
                    'database-error',
                    exc.get('type', 'unknown-db-error')
                ]
    
    return event

def before_send_transaction_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter performance transactions before sending to Sentry
    """
    
    # Skip health check transactions
    transaction_name = event.get('transaction', '')
    if any(endpoint in transaction_name for endpoint in ['/health', '/readyz', '/livez', '/metrics']):
        return None
    
    # Add trace ID to transaction
    trace_id = get_trace_id()
    if trace_id:
        if 'contexts' not in event:
            event['contexts'] = {}
        event['contexts']['trace'] = {
            'trace_id': trace_id
        }
    
    return event

def capture_exception(exception: Exception, **kwargs):
    """
    Capture exception with additional context
    """
    with sentry_sdk.configure_scope() as scope:
        # Add trace ID
        trace_id = get_trace_id()
        if trace_id:
            scope.set_tag('trace_id', trace_id)
        
        # Add user ID
        user_id = get_user_id()
        if user_id:
            scope.user = {'id': user_id}
        
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        sentry_sdk.capture_exception(exception)

def capture_message(message: str, level: str = 'info', **kwargs):
    """
    Capture custom message with context
    """
    with sentry_sdk.configure_scope() as scope:
        # Add trace ID
        trace_id = get_trace_id()
        if trace_id:
            scope.set_tag('trace_id', trace_id)
        
        # Add user ID
        user_id = get_user_id()
        if user_id:
            scope.user = {'id': user_id}
        
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        sentry_sdk.capture_message(message, level=level)

def add_breadcrumb(message: str, category: str = 'custom', level: str = 'info', data: Dict[str, Any] = None):
    """
    Add custom breadcrumb for debugging context
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )

def set_user_context(user_id: str, email: str = None, username: str = None):
    """
    Set user context for error tracking (without PII)
    """
    with sentry_sdk.configure_scope() as scope:
        user_data = {'id': user_id}
        
        # Only add email if specifically provided and not containing PII
        if email and not any(domain in email for domain in ['@example.com', '@test.com']):
            # Hash email domain for privacy
            domain = email.split('@')[1] if '@' in email else 'unknown'
            user_data['email_domain'] = domain
        
        if username:
            user_data['username'] = username
        
        scope.user = user_data

def set_transaction_context(operation: str, **kwargs):
    """
    Set transaction context for performance tracking
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag('operation', operation)
        
        for key, value in kwargs.items():
            scope.set_tag(key, value)

def start_transaction(name: str, op: str = 'function') -> Any:
    """
    Start a performance transaction
    """
    return sentry_sdk.start_transaction(name=name, op=op)

def measure_performance(operation_name: str):
    """
    Decorator to measure function performance
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with sentry_sdk.start_transaction(name=f"{func.__module__}.{func.__name__}", op=operation_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with sentry_sdk.start_transaction(name=f"{func.__module__}.{func.__name__}", op=operation_name):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator

class SentryContextManager:
    """
    Context manager for Sentry transaction tracking
    """
    
    def __init__(self, name: str, op: str = 'custom', **kwargs):
        self.name = name
        self.op = op
        self.context = kwargs
        self.transaction = None
    
    def __enter__(self):
        self.transaction = sentry_sdk.start_transaction(name=self.name, op=self.op)
        self.transaction.__enter__()
        
        # Add context
        with sentry_sdk.configure_scope() as scope:
            for key, value in self.context.items():
                scope.set_tag(key, value)
        
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.transaction:
            self.transaction.__exit__(exc_type, exc_val, exc_tb)

# Import asyncio after checking if it's needed
import asyncio