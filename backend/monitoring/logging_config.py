"""
Production logging configuration for CoinLink
Supports multiple outputs: console, file, Sentry, and structured logging
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Try to import Sentry (optional dependency)
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs for production"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_name': record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'alert_type'):
            log_obj['alert_type'] = record.alert_type
        if hasattr(record, 'symbol'):
            log_obj['symbol'] = record.symbol
        
        return json.dumps(log_obj)


class ProductionLogConfig:
    """Production logging configuration manager"""
    
    def __init__(self):
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_format = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'
        self.log_dir = Path('/var/log/coinlink')
        self.enable_sentry = os.getenv('SENTRY_DSN') is not None
        
    def setup_logging(self) -> None:
        """Configure production logging with multiple handlers"""
        
        # Create log directory if it doesn't exist
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # Remove default handlers
        root_logger.handlers = []
        
        # Console Handler
        self._add_console_handler(root_logger)
        
        # File Handlers
        self._add_file_handlers(root_logger)
        
        # Sentry Integration
        if self.enable_sentry and SENTRY_AVAILABLE:
            self._setup_sentry()
        
        # Configure specific loggers
        self._configure_app_loggers()
        
    def _add_console_handler(self, logger: logging.Logger) -> None:
        """Add console handler with appropriate formatter"""
        console_handler = logging.StreamHandler(sys.stdout)
        
        if self.log_format == 'json':
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        console_handler.setLevel(getattr(logging, self.log_level))
        logger.addHandler(console_handler)
    
    def _add_file_handlers(self, logger: logging.Logger) -> None:
        """Add rotating file handlers for different log types"""
        
        # Application logs
        app_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'app.log',
            maxBytes=10_485_760,  # 10MB
            backupCount=10
        )
        app_handler.setFormatter(StructuredFormatter())
        app_handler.setLevel(logging.INFO)
        logger.addHandler(app_handler)
        
        # Error logs
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'error.log',
            maxBytes=10_485_760,  # 10MB
            backupCount=10
        )
        error_handler.setFormatter(StructuredFormatter())
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
        
        # Alert logs (custom for trading alerts)
        alert_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'alerts.log',
            maxBytes=10_485_760,  # 10MB
            backupCount=20
        )
        alert_handler.setFormatter(StructuredFormatter())
        alert_logger = logging.getLogger('alerts')
        alert_logger.addHandler(alert_handler)
        
    def _setup_sentry(self) -> None:
        """Configure Sentry error tracking"""
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            integrations=[sentry_logging],
            environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            attach_stacktrace=True,
            send_default_pii=False
        )
        
    def _configure_app_loggers(self) -> None:
        """Configure specific application loggers"""
        
        # Reduce noise from external libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('websockets').setLevel(logging.WARNING)
        
        # Configure app-specific loggers
        loggers_config = {
            'coinlink.api': logging.INFO,
            'coinlink.alerts': logging.INFO,
            'coinlink.websocket': logging.INFO,
            'coinlink.monitoring': logging.DEBUG,
            'coinlink.agents': logging.INFO,
            'coinlink.sentiment': logging.INFO,
        }
        
        for logger_name, level in loggers_config.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)


class MetricsLogger:
    """Custom metrics logger for performance monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('metrics')
        self.metrics_file = Path('/var/log/coinlink/metrics.jsonl')
        
        # Setup metrics file handler
        if not self.metrics_file.parent.exists():
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(self.metrics_file)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_metric(self, metric_name: str, value: float, tags: Dict[str, Any] = None) -> None:
        """Log a metric with optional tags"""
        extra = {
            'metric_name': metric_name,
            'metric_value': value,
            'tags': tags or {}
        }
        self.logger.info(f"Metric: {metric_name}={value}", extra=extra)
    
    def log_api_request(self, endpoint: str, method: str, duration_ms: float, status_code: int) -> None:
        """Log API request metrics"""
        self.log_metric(
            'api_request_duration',
            duration_ms,
            {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code
            }
        )
    
    def log_websocket_message(self, message_type: str, symbol: str, processing_time_ms: float) -> None:
        """Log WebSocket message processing metrics"""
        self.log_metric(
            'websocket_processing_time',
            processing_time_ms,
            {
                'message_type': message_type,
                'symbol': symbol
            }
        )
    
    def log_alert_triggered(self, alert_type: str, symbol: str, price: float, threshold: float) -> None:
        """Log alert trigger events"""
        self.log_metric(
            'alert_triggered',
            1,
            {
                'alert_type': alert_type,
                'symbol': symbol,
                'price': price,
                'threshold': threshold
            }
        )


# Singleton instances
log_config = ProductionLogConfig()
metrics_logger = MetricsLogger()


def setup_production_logging():
    """Main entry point to setup production logging"""
    log_config.setup_logging()
    logging.info("Production logging configured", extra={
        'log_level': log_config.log_level,
        'log_format': log_config.log_format,
        'sentry_enabled': log_config.enable_sentry
    })


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(f"coinlink.{name}")


def log_alert(alert_type: str, symbol: str, message: str, **kwargs):
    """Specialized function for logging trading alerts"""
    alert_logger = logging.getLogger('alerts')
    alert_logger.info(message, extra={
        'alert_type': alert_type,
        'symbol': symbol,
        **kwargs
    })


# Export main functions and objects
__all__ = [
    'setup_production_logging',
    'get_logger',
    'log_alert',
    'metrics_logger',
    'MetricsLogger',
    'StructuredFormatter'
]