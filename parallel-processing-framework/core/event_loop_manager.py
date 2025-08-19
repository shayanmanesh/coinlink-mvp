"""
AsyncIO-based Event Loop Manager with uvloop optimization
"""
import asyncio
import logging
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union, Coroutine
import uvloop
import os
from contextlib import asynccontextmanager

from config.settings import settings

logger = logging.getLogger(__name__)


class EventLoopManager:
    """High-performance event loop manager with uvloop optimization"""
    
    def __init__(self,
                 use_uvloop: bool = None,
                 max_workers: int = None,
                 thread_pool_size: int = None,
                 process_pool_size: int = None):
        
        self.use_uvloop = use_uvloop if use_uvloop is not None else settings.event_loop.use_uvloop
        self.max_workers = max_workers or settings.event_loop.max_connections
        self.thread_pool_size = thread_pool_size or min(32, (os.cpu_count() or 1) + 4)
        self.process_pool_size = process_pool_size or (os.cpu_count() or 1)
        
        # Event loop and executors
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        self.process_executor: Optional[ProcessPoolExecutor] = None
        
        # State management
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.shutdown_callbacks: List[Callable] = []
        self.startup_callbacks: List[Callable] = []
        
        # Performance monitoring
        self.task_count = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Signal handling
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
        
        # Lock for thread safety
        self._lock = threading.Lock()
    
    def setup_event_loop(self) -> asyncio.AbstractEventLoop:
        """Set up and configure the event loop"""
        if self.use_uvloop and uvloop is not None:
            try:
                # Install uvloop as the default event loop
                uvloop.install()
                loop = asyncio.new_event_loop()
                logger.info("Using uvloop for enhanced performance")
            except Exception as e:
                logger.warning(f"Failed to setup uvloop, falling back to default: {e}")
                loop = asyncio.new_event_loop()
        else:
            loop = asyncio.new_event_loop()
            logger.info("Using default asyncio event loop")
        
        # Configure loop settings
        loop.set_debug(settings.debug)
        
        # Set custom exception handler
        loop.set_exception_handler(self._exception_handler)
        
        # Configure loop for high performance
        if hasattr(loop, 'set_task_factory'):
            loop.set_task_factory(self._task_factory)
        
        return loop
    
    def _exception_handler(self, loop: asyncio.AbstractEventLoop, context: Dict[str, Any]):
        """Custom exception handler for the event loop"""
        exception = context.get('exception')
        message = context.get('message', 'Unhandled exception in event loop')
        
        if exception:
            logger.error(f"Event loop exception: {message}", exc_info=exception)
        else:
            logger.error(f"Event loop error: {message}")
        
        # Update stats
        self.failed_tasks += 1
    
    def _task_factory(self, loop: asyncio.AbstractEventLoop, coro: Coroutine) -> asyncio.Task:
        """Custom task factory for tracking tasks"""
        task = asyncio.Task(coro, loop=loop)
        task_id = id(task)
        
        self.task_count += 1
        self.active_tasks[task_id] = task
        
        # Add completion callback
        task.add_done_callback(lambda t: self._task_completed(task_id, t))
        
        return task
    
    def _task_completed(self, task_id: int, task: asyncio.Task):
        """Handle task completion"""
        self.active_tasks.pop(task_id, None)
        
        if task.cancelled():
            logger.debug(f"Task {task_id} was cancelled")
        elif task.exception():
            self.failed_tasks += 1
            logger.debug(f"Task {task_id} failed: {task.exception()}")
        else:
            self.completed_tasks += 1
            logger.debug(f"Task {task_id} completed successfully")
    
    def start(self) -> None:
        """Start the event loop manager"""
        with self._lock:
            if self.is_running:
                logger.warning("Event loop manager is already running")
                return
            
            # Set up the event loop
            self.loop = self.setup_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Set up executors
            self.thread_executor = ThreadPoolExecutor(
                max_workers=self.thread_pool_size,
                thread_name_prefix="PPF-Thread"
            )
            
            self.process_executor = ProcessPoolExecutor(
                max_workers=self.process_pool_size
            )
            
            # Set default executors for the loop
            self.loop.set_default_executor(self.thread_executor)
            
            # Set up signal handlers
            self._setup_signal_handlers()
            
            self.is_running = True
            self.start_time = datetime.utcnow()
            
            logger.info(f"Event loop manager started with uvloop={self.use_uvloop}")
            
            # Run startup callbacks
            for callback in self.startup_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        self.loop.create_task(callback())
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Startup callback error: {e}")
    
    def stop(self) -> None:
        """Stop the event loop manager"""
        with self._lock:
            if not self.is_running:
                return
            
            logger.info("Stopping event loop manager...")
            
            # Run shutdown callbacks
            for callback in self.shutdown_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        if self.loop and self.loop.is_running():
                            self.loop.create_task(callback())
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Shutdown callback error: {e}")
            
            # Cancel all active tasks
            if self.active_tasks:
                logger.info(f"Cancelling {len(self.active_tasks)} active tasks...")
                for task in self.active_tasks.values():
                    if not task.done():
                        task.cancel()
            
            # Shutdown executors
            if self.thread_executor:
                self.thread_executor.shutdown(wait=True)
                self.thread_executor = None
            
            if self.process_executor:
                self.process_executor.shutdown(wait=True)
                self.process_executor = None
            
            # Restore signal handlers
            self._restore_signal_handlers()
            
            # Stop the loop
            if self.loop and self.loop.is_running():
                self.loop.stop()
            
            self.is_running = False
            self.loop = None
            
            logger.info("Event loop manager stopped")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        if sys.platform == 'win32':
            # Windows doesn't support SIGTERM
            self._original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
        else:
            self._original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
            self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _restore_signal_handlers(self):
        """Restore original signal handlers"""
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        if self.loop and self.loop.is_running():
            self.loop.create_task(self._graceful_shutdown())
    
    async def _graceful_shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Performing graceful shutdown...")
        
        # Give tasks a chance to complete
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} tasks to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_tasks.values(), return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks didn't complete within timeout")
        
        # Stop the loop
        self.stop()
    
    def run_until_complete(self, coro: Awaitable[Any]) -> Any:
        """Run a coroutine until completion"""
        if not self.is_running:
            raise RuntimeError("Event loop manager is not running")
        
        if not self.loop:
            raise RuntimeError("Event loop is not available")
        
        return self.loop.run_until_complete(coro)
    
    def create_task(self, coro: Awaitable[Any], name: Optional[str] = None) -> asyncio.Task:
        """Create a new task"""
        if not self.loop:
            raise RuntimeError("Event loop is not available")
        
        if hasattr(asyncio, 'create_task') and name:
            return self.loop.create_task(coro, name=name)
        else:
            return self.loop.create_task(coro)
    
    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run a function in the thread pool"""
        if not self.loop:
            raise RuntimeError("Event loop is not available")
        
        return await self.loop.run_in_executor(self.thread_executor, func, *args, **kwargs)
    
    async def run_in_process(self, func: Callable, *args, **kwargs) -> Any:
        """Run a function in the process pool"""
        if not self.loop:
            raise RuntimeError("Event loop is not available")
        
        return await self.loop.run_in_executor(self.process_executor, func, *args, **kwargs)
    
    async def gather(*coros: Awaitable[Any], return_exceptions: bool = False) -> List[Any]:
        """Gather multiple coroutines with enhanced error handling"""
        return await asyncio.gather(*coros, return_exceptions=return_exceptions)
    
    async def wait_for(self, coro: Awaitable[Any], timeout: float) -> Any:
        """Wait for a coroutine with timeout"""
        return await asyncio.wait_for(coro, timeout=timeout)
    
    @asynccontextmanager
    async def timeout_context(self, timeout: float):
        """Context manager for timeout operations"""
        try:
            async with asyncio.timeout(timeout):
                yield
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout} seconds")
            raise
    
    def add_startup_callback(self, callback: Callable):
        """Add a callback to run on startup"""
        self.startup_callbacks.append(callback)
    
    def add_shutdown_callback(self, callback: Callable):
        """Add a callback to run on shutdown"""
        self.shutdown_callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event loop statistics"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        loop_info = {}
        if self.loop:
            loop_info = {
                'is_running': self.loop.is_running(),
                'is_closed': self.loop.is_closed(),
                'debug': self.loop.get_debug()
            }
        
        return {
            'is_running': self.is_running,
            'use_uvloop': self.use_uvloop,
            'uptime_seconds': uptime,
            'task_count': self.task_count,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'active_tasks': len(self.active_tasks),
            'thread_pool_size': self.thread_pool_size,
            'process_pool_size': self.process_pool_size,
            'success_rate': self.completed_tasks / max(1, self.task_count),
            'loop_info': loop_info
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Check if loop is responsive
        try:
            start_time = time.time()
            await asyncio.sleep(0.001)  # Small delay to test responsiveness
            response_time = time.time() - start_time
            
            health['checks']['loop_responsive'] = {
                'status': 'healthy' if response_time < 0.1 else 'degraded',
                'response_time': response_time
            }
        except Exception as e:
            health['checks']['loop_responsive'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'unhealthy'
        
        # Check executor health
        if self.thread_executor:
            try:
                future = self.thread_executor.submit(lambda: time.time())
                result = await asyncio.wait_for(
                    asyncio.wrap_future(future), 
                    timeout=1.0
                )
                health['checks']['thread_executor'] = {'status': 'healthy'}
            except Exception as e:
                health['checks']['thread_executor'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health['status'] = 'unhealthy'
        
        # Check task queue health
        active_count = len(self.active_tasks)
        if active_count > self.max_workers * 0.9:
            health['checks']['task_queue'] = {
                'status': 'degraded',
                'active_tasks': active_count,
                'max_workers': self.max_workers
            }
            if health['status'] == 'healthy':
                health['status'] = 'degraded'
        else:
            health['checks']['task_queue'] = {
                'status': 'healthy',
                'active_tasks': active_count
            }
        
        return health


class AsyncContextManager:
    """Helper for managing async context across the framework"""
    
    def __init__(self, event_loop_manager: EventLoopManager):
        self.elm = event_loop_manager
        self.contexts: Dict[str, Any] = {}
    
    async def __aenter__(self):
        """Async context entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context exit"""
        # Clean up any resources
        for context in self.contexts.values():
            if hasattr(context, 'close'):
                try:
                    if asyncio.iscoroutinefunction(context.close):
                        await context.close()
                    else:
                        context.close()
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")
    
    def add_context(self, name: str, context: Any):
        """Add a context to manage"""
        self.contexts[name] = context
    
    def get_context(self, name: str) -> Any:
        """Get a managed context"""
        return self.contexts.get(name)


# Global event loop manager instance
_global_elm: Optional[EventLoopManager] = None


def get_event_loop_manager() -> EventLoopManager:
    """Get the global event loop manager"""
    global _global_elm
    if _global_elm is None:
        _global_elm = EventLoopManager()
    return _global_elm


def setup_event_loop_manager(**kwargs) -> EventLoopManager:
    """Set up and configure the global event loop manager"""
    global _global_elm
    _global_elm = EventLoopManager(**kwargs)
    return _global_elm


async def run_with_event_loop_manager(main_coro: Awaitable[Any], **elm_kwargs) -> Any:
    """Run a main coroutine with event loop manager"""
    elm = setup_event_loop_manager(**elm_kwargs)
    elm.start()
    
    try:
        return await elm.run_until_complete(main_coro)
    finally:
        elm.stop()