"""
AsyncIO-based worker implementation for concurrent task processing
"""
import asyncio
import logging
import time
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
import psutil
import os

from core.interfaces import IWorker, Task, TaskResult, TaskStatus
from config.settings import settings

logger = logging.getLogger(__name__)


class AsyncWorker(IWorker):
    """AsyncIO-based worker for handling concurrent tasks"""
    
    def __init__(self, 
                 worker_id: Optional[str] = None,
                 max_concurrent_tasks: int = 10,
                 heartbeat_interval: int = 30):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.max_concurrent_tasks = max_concurrent_tasks
        self.heartbeat_interval = heartbeat_interval
        
        # Worker state
        self.is_running = False
        self._health_status = True
        self.start_time: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        
        # Task tracking
        self.current_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.total_execution_time = 0.0
        
        # Resource monitoring
        self.process = psutil.Process(os.getpid())
        self.max_memory_mb = 512  # Default memory limit
        
        # Internal events
        self._shutdown_event = asyncio.Event()
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the worker"""
        if self.is_running:
            logger.warning(f"Worker {self.worker_id} is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        self.last_heartbeat = self.start_time
        
        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info(f"Worker {self.worker_id} started")
    
    async def stop(self) -> None:
        """Stop the worker gracefully"""
        if not self.is_running:
            return
        
        logger.info(f"Stopping worker {self.worker_id}...")
        
        # Signal shutdown
        self._shutdown_event.set()
        self.is_running = False
        
        # Cancel heartbeat task
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Wait for current tasks to complete or timeout
        if self.current_tasks:
            logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.current_tasks.values(), return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Some tasks didn't complete within timeout, cancelling...")
                for task in self.current_tasks.values():
                    if not task.done():
                        task.cancel()
        
        self.current_tasks.clear()
        logger.info(f"Worker {self.worker_id} stopped")
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a single task"""
        if not self.is_running:
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=Exception("Worker is not running"),
                worker_id=self.worker_id
            )
        
        # Check if we have capacity
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=Exception("Worker at maximum capacity"),
                worker_id=self.worker_id
            )
        
        start_time = datetime.utcnow()
        
        try:
            # Create and track the task execution
            execution_task = asyncio.create_task(
                self._execute_task_with_timeout(task)
            )
            self.current_tasks[task.id] = execution_task
            
            # Wait for completion
            result = await execution_task
            
            # Update stats
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            self.total_execution_time += execution_time
            
            if result.status == TaskStatus.COMPLETED:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1
            
            # Update result with timing info
            result.start_time = start_time
            result.end_time = end_time
            result.execution_time = execution_time
            result.worker_id = self.worker_id
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error executing task {task.id}: {e}")
            self.failed_tasks += 1
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=e,
                start_time=start_time,
                end_time=datetime.utcnow(),
                worker_id=self.worker_id
            )
        finally:
            # Clean up task tracking
            self.current_tasks.pop(task.id, None)
    
    async def _execute_task_with_timeout(self, task: Task) -> TaskResult:
        """Execute task with timeout handling"""
        try:
            # Apply timeout if specified
            timeout = task.timeout or settings.processing.task_timeout
            
            if asyncio.iscoroutinefunction(task.func):
                # Async function
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=timeout
                )
            else:
                # Sync function - run in thread pool
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, task.func, *task.args, **task.kwargs),
                    timeout=timeout
                )
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=result
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"Task {task.id} timed out after {timeout}s")
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=Exception(f"Task timed out after {timeout}s")
            )
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            logger.debug(f"Task {task.id} traceback: {traceback.format_exc()}")
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=e
            )
    
    async def is_healthy(self) -> bool:
        """Check if worker is healthy"""
        if not self.is_running:
            return False
        
        try:
            # Check memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                logger.warning(f"Worker {self.worker_id} memory usage too high: {memory_mb:.1f}MB")
                self._health_status = False
                return False
            
            # Check heartbeat freshness
            if self.last_heartbeat:
                time_since_heartbeat = datetime.utcnow() - self.last_heartbeat
                if time_since_heartbeat > timedelta(seconds=self.heartbeat_interval * 2):
                    logger.warning(f"Worker {self.worker_id} heartbeat is stale")
                    self._health_status = False
                    return False
            
            # Check if too many tasks are hanging
            hanging_tasks = sum(
                1 for task in self.current_tasks.values()
                if not task.done()
            )
            
            if hanging_tasks > self.max_concurrent_tasks * 0.8:
                logger.warning(f"Worker {self.worker_id} has too many hanging tasks: {hanging_tasks}")
                self._health_status = False
                return False
            
            self._health_status = True
            return True
            
        except Exception as e:
            logger.error(f"Health check failed for worker {self.worker_id}: {e}")
            self._health_status = False
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        try:
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
        except:
            memory_info = None
            cpu_percent = 0.0
        
        return {
            'worker_id': self.worker_id,
            'is_running': self.is_running,
            'is_healthy': self._health_status,
            'uptime_seconds': uptime,
            'current_tasks': len(self.current_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_tasks': self.completed_tasks + self.failed_tasks,
            'success_rate': (
                self.completed_tasks / max(1, self.completed_tasks + self.failed_tasks)
            ),
            'avg_execution_time': (
                self.total_execution_time / max(1, self.completed_tasks + self.failed_tasks)
            ),
            'memory_mb': memory_info.rss / 1024 / 1024 if memory_info else 0,
            'cpu_percent': cpu_percent,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }
    
    async def _heartbeat_loop(self) -> None:
        """Internal heartbeat loop"""
        while self.is_running and not self._shutdown_event.is_set():
            try:
                self.last_heartbeat = datetime.utcnow()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error for worker {self.worker_id}: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    def can_accept_task(self) -> bool:
        """Check if worker can accept a new task"""
        return (
            self.is_running and 
            self._health_status and 
            len(self.current_tasks) < self.max_concurrent_tasks
        )
    
    async def get_current_load(self) -> float:
        """Get current load as percentage (0.0 to 1.0)"""
        if not self.is_running:
            return 1.0
        
        task_load = len(self.current_tasks) / self.max_concurrent_tasks
        
        # Factor in CPU and memory usage
        try:
            cpu_load = self.process.cpu_percent() / 100.0
            memory_info = self.process.memory_info()
            memory_load = (memory_info.rss / 1024 / 1024) / self.max_memory_mb
            
            # Weighted average: 50% task count, 30% CPU, 20% memory
            total_load = (task_load * 0.5) + (cpu_load * 0.3) + (memory_load * 0.2)
            return min(1.0, total_load)
            
        except Exception:
            return task_load