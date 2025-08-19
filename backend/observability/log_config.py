"""
Structured JSON logging with trace IDs for production observability
Centralized logging configuration with correlation tracking
"""

import logging
import logging.config
import json
import sys
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from functools import wraps

from ..config.settings import settings

# Context variable for trace ID correlation
trace_id_context: ContextVar[str] = ContextVar('trace_id', default='')
user_id_context: ContextVar[str] = ContextVar('user_id', default='')

class TraceIDFilter(logging.Filter):
    """
    Logging filter to add trace ID and user ID to log records
    """
    
    def filter(self, record):
        # Add trace ID from context
        trace_id = trace_id_context.get('')
        if not trace_id:
            trace_id = str(uuid.uuid4())
            trace_id_context.set(trace_id)
        
        record.trace_id = trace_id
        record.user_id = user_id_context.get('')
        
        return True

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def __init__(self, include_trace_id=True):
        super().__init__()
        self.include_trace_id = include_trace_id
        self.hostname = settings.get('HOSTNAME', 'coinlink-api')
        self.service_name = 'coinlink-production'
        self.service_version = '2.0.0'
    
    def format(self, record):
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': {
                'name': self.service_name,
                'version': self.service_version,
                'hostname': self.hostname
            },
            'process': {
                'pid': record.process,
                'thread': record.thread,
                'thread_name': record.threadName
            },
            'source': {
                'file': record.pathname,
                'line': record.lineno,
                'function': record.funcName
            }
        }
        
        # Add trace ID if available
        if self.include_trace_id and hasattr(record, 'trace_id') and record.trace_id:
            log_entry['trace_id'] = record.trace_id
        
        # Add user ID if available
        if hasattr(record, 'user_id') and record.user_id:
            log_entry['user_id'] = record.user_id
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from record
        extra_fields = {}
        skip_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'message', 'exc_info',
            'exc_text', 'stack_info', 'trace_id', 'user_id'
        }
        
        for key, value in record.__dict__.items():
            if key not in skip_fields and not key.startswith('_'):
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False)

class StructuredLogger:
    """
    Structured logger with convenience methods for different log types
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        extra = self._prepare_extra(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        extra = self._prepare_extra(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        extra = self._prepare_extra(kwargs)
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data"""
        extra = self._prepare_extra(kwargs)
        self.logger.critical(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data"""
        extra = self._prepare_extra(kwargs)
        self.logger.debug(message, extra=extra)
    
    def api_request(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log API request with standard fields"""
        extra = self._prepare_extra(kwargs)
        extra.update({
            'event_type': 'api_request',
            'http_method': method,
            'http_path': path,
            'http_status_code': status_code,
            'duration_ms': duration_ms
        })
        
        level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
        self.logger.log(level, f"{method} {path} {status_code} {duration_ms:.2f}ms", extra=extra)
    
    def auth_event(self, event_type: str, user_id: str = None, success: bool = True, **kwargs):
        """Log authentication events"""
        extra = self._prepare_extra(kwargs)
        extra.update({
            'event_type': 'auth_event',
            'auth_event_type': event_type,
            'auth_success': success
        })
        
        if user_id:
            extra['auth_user_id'] = user_id
        
        level = logging.INFO if success else logging.WARNING
        message = f"Auth {event_type}: {'success' if success else 'failure'}"
        self.logger.log(level, message, extra=extra)
    
    def websocket_event(self, event_type: str, connection_id: str, user_id: str = None, **kwargs):
        """Log WebSocket events"""
        extra = self._prepare_extra(kwargs)
        extra.update({
            'event_type': 'websocket_event',
            'ws_event_type': event_type,
            'ws_connection_id': connection_id
        })
        
        if user_id:
            extra['ws_user_id'] = user_id
        
        self.logger.info(f"WebSocket {event_type}: {connection_id}", extra=extra)
    
    def database_event(self, operation: str, table: str, duration_ms: float, success: bool = True, **kwargs):
        """Log database operations"""
        extra = self._prepare_extra(kwargs)
        extra.update({
            'event_type': 'database_event',
            'db_operation': operation,
            'db_table': table,
            'db_duration_ms': duration_ms,
            'db_success': success
        })
        
        level = logging.ERROR if not success else logging.DEBUG
        message = f"DB {operation} {table}: {duration_ms:.2f}ms"
        self.logger.log(level, message, extra=extra)
    
    def business_event(self, event_type: str, **kwargs):
        """Log business logic events"""
        extra = self._prepare_extra(kwargs)
        extra.update({
            'event_type': 'business_event',
            'business_event_type': event_type
        })
        
        self.logger.info(f"Business event: {event_type}", extra=extra)
    
    def security_event(self, event_type: str, severity: str = 'medium', **kwargs):
        """Log security events"""
        extra = self._prepare_extra(kwargs)
        extra.update({
            'event_type': 'security_event',
            'security_event_type': event_type,
            'security_severity': severity
        })
        
        level_map = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }
        
        level = level_map.get(severity, logging.WARNING)
        self.logger.log(level, f"Security event: {event_type}", extra=extra)
    
    def _prepare_extra(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare extra fields for logging"""
        extra = {}
        for key, value in kwargs.items():
            # Convert complex objects to strings
            if isinstance(value, (dict, list)):
                extra[key] = json.dumps(value, default=str)
            elif not isinstance(value, (str, int, float, bool, type(None))):
                extra[key] = str(value)
            else:
                extra[key] = value
        
        return extra


def configure_logging():
    """
    Configure application logging with structured JSON format
    """
    
    # Determine log level
    log_level = getattr(settings, 'LOG_LEVEL', 'INFO').upper()
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JSONFormatter,
                'include_trace_id': True
            },
            'console': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'filters': {
            'trace_id': {
                '()': TraceIDFilter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'json',
                'filters': ['trace_id'],
                'level': log_level
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'coinlink': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
            'fastapi': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            },
            'sqlalchemy.engine': {
                'handlers': ['console'],
                'level': 'WARNING',  # Reduce SQL query noise
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(config)
    
    # Get root logger and log startup
    logger = logging.getLogger('coinlink.startup')
    logger.info(
        "Structured logging configured",
        extra={
            'log_level': log_level,
            'json_format': True,
            'trace_id_enabled': True
        }
    )


def set_trace_id(trace_id: str = None) -> str:
    """
    Set trace ID in context for request correlation
    """
    if not trace_id:
        trace_id = str(uuid.uuid4())
    
    trace_id_context.set(trace_id)
    return trace_id


def get_trace_id() -> str:
    """
    Get current trace ID from context
    """
    return trace_id_context.get('')


def set_user_id(user_id: str):
    """
    Set user ID in context for request correlation
    """
    user_id_context.set(user_id)


def get_user_id() -> str:
    """
    Get current user ID from context
    """
    return user_id_context.get('')


def trace_async(func):
    """
    Decorator to automatically add trace ID to async functions
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Set trace ID if not already set
        if not get_trace_id():
            set_trace_id()
        
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            logger.error(
                f"Exception in {func.__name__}",
                extra={
                    'function': func.__name__,
                    'exception_type': type(e).__name__,
                    'exception_message': str(e)
                }
            )
            raise
    
    return wrapper


def trace_sync(func):
    """
    Decorator to automatically add trace ID to sync functions
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Set trace ID if not already set
        if not get_trace_id():
            set_trace_id()
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            logger.error(
                f"Exception in {func.__name__}",
                extra={
                    'function': func.__name__,
                    'exception_type': type(e).__name__,
                    'exception_message': str(e)
                }
            )
            raise
    
    return wrapper


# Create application loggers
app_logger = StructuredLogger('coinlink.app')
api_logger = StructuredLogger('coinlink.api')
auth_logger = StructuredLogger('coinlink.auth')
websocket_logger = StructuredLogger('coinlink.websocket')
db_logger = StructuredLogger('coinlink.database')
security_logger = StructuredLogger('coinlink.security')