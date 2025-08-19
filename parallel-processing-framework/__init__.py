"""
Parallel Processing Framework

A high-performance, modular framework for parallel and concurrent task processing in Python.
"""

__version__ = "1.0.0"
__author__ = "Parallel Processing Framework Team"

# Core exports
from orchestrator.main import (
    ParallelProcessingOrchestrator,
    get_orchestrator,
    run_with_orchestrator
)

from core.interfaces import (
    Task,
    TaskResult,
    TaskStatus,
    TaskPriority
)

from core.task_queue import RedisTaskQueue
from core.result_store import RedisResultStore, ResultAggregator
from core.event_loop_manager import EventLoopManager, get_event_loop_manager
from core.circuit_breaker import (
    AsyncCircuitBreaker,
    CircuitBreakerConfig,
    get_circuit_breaker,
    circuit_breaker
)

from workers.async_worker import AsyncWorker
from workers.worker_pool import DynamicWorkerPool

from config.settings import settings

# Convenience imports
ParallelProcessor = ParallelProcessingOrchestrator

__all__ = [
    # Main classes
    'ParallelProcessingOrchestrator',
    'ParallelProcessor',
    
    # Core interfaces
    'Task',
    'TaskResult', 
    'TaskStatus',
    'TaskPriority',
    
    # Queue and storage
    'RedisTaskQueue',
    'RedisResultStore',
    'ResultAggregator',
    
    # Event loop
    'EventLoopManager',
    'get_event_loop_manager',
    
    # Circuit breaker
    'AsyncCircuitBreaker',
    'CircuitBreakerConfig',
    'get_circuit_breaker',
    'circuit_breaker',
    
    # Workers
    'AsyncWorker',
    'DynamicWorkerPool',
    
    # Utilities
    'get_orchestrator',
    'run_with_orchestrator',
    'settings'
]