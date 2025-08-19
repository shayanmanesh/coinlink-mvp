"""
Observability module for CoinLink MVP
Production monitoring, logging, and error tracking
"""

import logging
import asyncio
from typing import Optional

from .log_config import configure_logging, set_trace_id, get_trace_id, app_logger
from .sentry import configure_sentry, capture_exception, capture_message
from .metrics import coinlink_metrics, create_instrumentator, start_system_metrics_collection, get_metrics_response

logger = logging.getLogger(__name__)

# Global metrics collection task
_metrics_task: Optional[asyncio.Task] = None

async def initialize_observability():
    """
    Initialize all observability components
    """
    global _metrics_task
    
    try:
        # Configure structured logging
        configure_logging()
        app_logger.info("Structured logging initialized")
        
        # Configure Sentry error tracking
        configure_sentry() 
        app_logger.info("Sentry error tracking initialized")
        
        # Start system metrics collection
        _metrics_task = asyncio.create_task(start_system_metrics_collection())
        app_logger.info("System metrics collection started")
        
        app_logger.info("Observability stack fully initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize observability: {e}")
        raise

async def shutdown_observability():
    """
    Shutdown observability components
    """
    global _metrics_task
    
    try:
        # Stop metrics collection
        if _metrics_task and not _metrics_task.done():
            _metrics_task.cancel()
            try:
                await _metrics_task
            except asyncio.CancelledError:
                pass
        
        app_logger.info("Observability shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during observability shutdown: {e}")

__all__ = [
    # Logging
    'configure_logging',
    'set_trace_id',
    'get_trace_id',
    'app_logger',
    
    # Sentry
    'configure_sentry',
    'capture_exception',
    'capture_message',
    
    # Metrics
    'coinlink_metrics',
    'create_instrumentator',
    'get_metrics_response',
    
    # Initialization
    'initialize_observability',
    'shutdown_observability'
]