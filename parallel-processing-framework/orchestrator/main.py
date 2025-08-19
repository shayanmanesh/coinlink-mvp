"""
Main orchestrator for the parallel processing framework
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, List, Optional, Dict, Callable
import uuid

from core.interfaces import IOrchestrator, Task, TaskResult, TaskStatus, TaskPriority
from core.task_queue import RedisTaskQueue
from core.result_store import RedisResultStore, ResultAggregator
from core.event_loop_manager import EventLoopManager, get_event_loop_manager
from core.circuit_breaker import CircuitBreakerManager
from workers.worker_pool import DynamicWorkerPool
from config.settings import settings

logger = logging.getLogger(__name__)


class ParallelProcessingOrchestrator(IOrchestrator):
    """Main orchestrator that coordinates all framework components"""
    
    def __init__(self,
                 redis_url: Optional[str] = None,
                 min_workers: int = None,
                 max_workers: int = None,
                 use_uvloop: bool = None):
        
        # Core components
        self.task_queue = RedisTaskQueue(redis_url)
        self.result_store = RedisResultStore(redis_url)
        self.result_aggregator = ResultAggregator(self.result_store)
        self.circuit_breaker_manager = CircuitBreakerManager()
        
        # Event loop manager
        self.event_loop_manager = get_event_loop_manager()
        if use_uvloop is not None:
            self.event_loop_manager.use_uvloop = use_uvloop
        
        # Worker pool
        self.worker_pool = DynamicWorkerPool(
            task_queue=self.task_queue,
            result_store=self.result_store,
            min_workers=min_workers,
            max_workers=max_workers
        )
        
        # State
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Statistics
        self.total_tasks_submitted = 0
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
    
    async def start(self) -> None:
        """Start the orchestrator and all components"""
        if self.is_running:
            logger.warning("Orchestrator is already running")
            return
        
        logger.info("Starting Parallel Processing Orchestrator...")
        
        # Start event loop manager
        if not self.event_loop_manager.is_running:
            self.event_loop_manager.start()
        
        # Connect to external services
        await self.task_queue.connect()
        await self.result_store.connect()
        
        # Start worker pool
        await self.worker_pool.start()
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        logger.info("Parallel Processing Orchestrator started successfully")
    
    async def stop(self) -> None:
        """Stop the orchestrator and all components"""
        if not self.is_running:
            return
        
        logger.info("Stopping Parallel Processing Orchestrator...")
        
        # Stop worker pool
        await self.worker_pool.stop()
        
        # Disconnect from external services
        await self.task_queue.disconnect()
        await self.result_store.disconnect()
        
        # Stop event loop manager
        self.event_loop_manager.stop()
        
        self.is_running = False
        
        logger.info("Parallel Processing Orchestrator stopped")
    
    async def submit_task(self, task: Task) -> str:
        """Submit a single task for processing"""
        if not self.is_running:
            raise RuntimeError("Orchestrator is not running")
        
        task_id = await self.worker_pool.submit_task(task)
        self.total_tasks_submitted += 1
        
        logger.debug(f"Submitted task {task_id} with priority {task.priority.name}")
        return task_id
    
    async def submit_batch(self, tasks: List[Task]) -> List[str]:
        """Submit multiple tasks for processing"""
        task_ids = []
        for task in tasks:
            task_id = await self.submit_task(task)
            task_ids.append(task_id)
        
        logger.info(f"Submitted batch of {len(tasks)} tasks")
        return task_ids
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """Get the result of a specific task"""
        if timeout:
            results = await self.result_store.wait_for_results([task_id], timeout)
            if results:
                return results[0]
            raise asyncio.TimeoutError(f"Task {task_id} did not complete within {timeout}s")
        else:
            result = await self.result_store.get_result(task_id)
            if result is None:
                raise ValueError(f"Result for task {task_id} not found")
            return result
    
    async def get_results(self, task_ids: List[str], timeout: Optional[float] = None) -> List[TaskResult]:
        """Get results for multiple tasks"""
        return await self.result_store.wait_for_results(task_ids, timeout)
    
    async def stream_results(self, task_ids: List[str]):
        """Stream results as they become available"""
        async for result in self.result_store.get_results_stream(task_ids):
            yield result
    
    async def execute_parallel_workflow(self,
                                      tasks: List[Task],
                                      aggregation_func: Optional[Callable] = None,
                                      timeout: Optional[float] = None) -> Any:
        """Execute a complete parallel workflow"""
        # Submit all tasks
        task_ids = await self.submit_batch(tasks)
        
        logger.info(f"Executing parallel workflow with {len(tasks)} tasks")
        
        # Wait for all results
        results = await self.get_results(task_ids, timeout)
        
        # Update statistics
        successful_results = [r for r in results if r.status == TaskStatus.COMPLETED]
        failed_results = [r for r in results if r.status == TaskStatus.FAILED]
        
        self.total_tasks_completed += len(successful_results)
        self.total_tasks_failed += len(failed_results)
        
        logger.info(f"Workflow completed: {len(successful_results)} successful, {len(failed_results)} failed")
        
        # Apply aggregation if provided
        if aggregation_func and successful_results:
            return aggregation_func(successful_results)
        
        return results
    
    async def create_task(self,
                         func: Callable,
                         *args,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: Optional[int] = None,
                         max_retries: int = 3,
                         metadata: Optional[Dict[str, Any]] = None,
                         **kwargs) -> Task:
        """Create a task with the given parameters"""
        return Task(
            id=str(uuid.uuid4()),
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            metadata=metadata or {}
        )
    
    async def submit_function(self,
                            func: Callable,
                            *args,
                            priority: TaskPriority = TaskPriority.NORMAL,
                            timeout: Optional[int] = None,
                            **kwargs) -> str:
        """Submit a function for execution"""
        task = await self.create_task(
            func, *args,
            priority=priority,
            timeout=timeout,
            **kwargs
        )
        return await self.submit_task(task)
    
    async def map_async(self,
                       func: Callable,
                       items: List[Any],
                       priority: TaskPriority = TaskPriority.NORMAL,
                       timeout: Optional[float] = None) -> List[TaskResult]:
        """Map a function over a list of items in parallel"""
        tasks = []
        for item in items:
            task = await self.create_task(func, item, priority=priority)
            tasks.append(task)
        
        return await self.execute_parallel_workflow(tasks, timeout=timeout)
    
    async def filter_async(self,
                          predicate: Callable,
                          items: List[Any],
                          priority: TaskPriority = TaskPriority.NORMAL,
                          timeout: Optional[float] = None) -> List[Any]:
        """Filter items using a predicate function in parallel"""
        # Create tasks that return (item, predicate_result) pairs
        async def filter_task(item):
            result = predicate(item)
            return (item, result)
        
        tasks = []
        for item in items:
            task = await self.create_task(filter_task, item, priority=priority)
            tasks.append(task)
        
        results = await self.execute_parallel_workflow(tasks, timeout=timeout)
        
        # Extract items where predicate returned True
        filtered_items = []
        for result in results:
            if result.status == TaskStatus.COMPLETED and result.result:
                item, passed = result.result
                if passed:
                    filtered_items.append(item)
        
        return filtered_items
    
    async def reduce_async(self,
                          func: Callable,
                          items: List[Any],
                          initial: Any = None,
                          chunk_size: int = 100) -> Any:
        """Reduce items using a function with parallel processing"""
        if not items:
            return initial
        
        # Process in chunks for large datasets
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        # Reduce each chunk in parallel
        async def reduce_chunk(chunk):
            result = initial
            for item in chunk:
                if result is None:
                    result = item
                else:
                    result = func(result, item)
            return result
        
        # Process chunks in parallel
        chunk_results = await self.map_async(reduce_chunk, chunks)
        
        # Final reduction of chunk results
        final_result = initial
        for result in chunk_results:
            if result.status == TaskStatus.COMPLETED:
                if final_result is None:
                    final_result = result.result
                else:
                    final_result = func(final_result, result.result)
        
        return final_result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator statistics"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Get component stats
        queue_stats = {}
        pool_stats = {}
        result_stats = {}
        elm_stats = {}
        
        if self.is_running:
            try:
                queue_stats = asyncio.create_task(self.task_queue.get_stats())
                pool_stats = self.worker_pool.get_stats()
                result_stats = asyncio.create_task(self.result_store.get_stats())
                elm_stats = self.event_loop_manager.get_stats()
            except Exception as e:
                logger.warning(f"Error collecting component stats: {e}")
        
        return {
            'orchestrator': {
                'is_running': self.is_running,
                'uptime_seconds': uptime,
                'total_tasks_submitted': self.total_tasks_submitted,
                'total_tasks_completed': self.total_tasks_completed,
                'total_tasks_failed': self.total_tasks_failed,
                'success_rate': (
                    self.total_tasks_completed / 
                    max(1, self.total_tasks_completed + self.total_tasks_failed)
                )
            },
            'task_queue': queue_stats,
            'worker_pool': pool_stats,
            'result_store': result_stats,
            'event_loop_manager': elm_stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # Check orchestrator health
        health['components']['orchestrator'] = {
            'status': 'healthy' if self.is_running else 'stopped'
        }
        
        # Check component health
        try:
            health['components']['event_loop_manager'] = await self.event_loop_manager.health_check()
        except Exception as e:
            health['components']['event_loop_manager'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'unhealthy'
        
        # Check circuit breakers
        try:
            cb_health = await self.circuit_breaker_manager.get_health_status()
            health['components']['circuit_breakers'] = cb_health
            if cb_health['health_status'] != 'healthy':
                health['status'] = 'degraded'
        except Exception as e:
            health['components']['circuit_breakers'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return health


# Global orchestrator instance
_global_orchestrator: Optional[ParallelProcessingOrchestrator] = None


def get_orchestrator(**kwargs) -> ParallelProcessingOrchestrator:
    """Get the global orchestrator instance"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = ParallelProcessingOrchestrator(**kwargs)
    return _global_orchestrator


async def run_with_orchestrator(main_func: Callable, **kwargs):
    """Run a function with the orchestrator context"""
    orchestrator = get_orchestrator(**kwargs)
    await orchestrator.start()
    
    try:
        if asyncio.iscoroutinefunction(main_func):
            return await main_func(orchestrator)
        else:
            return main_func(orchestrator)
    finally:
        await orchestrator.stop()