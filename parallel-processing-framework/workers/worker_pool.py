"""
Dynamic worker pool with auto-scaling capabilities
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import uuid
from collections import deque

from core.interfaces import IWorkerPool, ITaskQueue, IResultStore, Task, TaskResult, TaskStatus
from .async_worker import AsyncWorker
from config.settings import settings

logger = logging.getLogger(__name__)


class DynamicWorkerPool(IWorkerPool):
    """Worker pool with dynamic scaling based on load"""
    
    def __init__(self,
                 task_queue: ITaskQueue,
                 result_store: IResultStore,
                 min_workers: int = None,
                 max_workers: int = None,
                 scale_up_threshold: float = None,
                 scale_down_threshold: float = None):
        
        self.task_queue = task_queue
        self.result_store = result_store
        
        # Scaling configuration
        self.min_workers = min_workers or settings.workers.min_workers
        self.max_workers = max_workers or settings.workers.max_workers
        self.scale_up_threshold = scale_up_threshold or settings.workers.scale_up_threshold
        self.scale_down_threshold = scale_down_threshold or settings.workers.scale_down_threshold
        
        # Worker management
        self.workers: Dict[str, AsyncWorker] = {}
        self.worker_tasks: Dict[str, asyncio.Task] = {}
        
        # Pool state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Scaling metrics
        self.load_history = deque(maxlen=60)  # 60 data points for scaling decisions
        self.last_scale_event: Optional[datetime] = None
        self.scale_cooldown = timedelta(seconds=30)  # Minimum time between scaling events
        
        # Tasks and monitoring
        self._monitor_task: Optional[asyncio.Task] = None
        self._scaling_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.total_tasks_processed = 0
        self.total_tasks_failed = 0
        self.total_scaling_events = 0
    
    async def start(self) -> None:
        """Start the worker pool"""
        if self.is_running:
            logger.warning("Worker pool is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        # Start with minimum number of workers
        await self._scale_to_target(self.min_workers)
        
        # Start monitoring and scaling tasks
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self._scaling_task = asyncio.create_task(self._scaling_loop())
        
        logger.info(f"Worker pool started with {len(self.workers)} workers")
    
    async def stop(self) -> None:
        """Stop the worker pool gracefully"""
        if not self.is_running:
            return
        
        logger.info("Stopping worker pool...")
        
        # Signal shutdown
        self._shutdown_event.set()
        self.is_running = False
        
        # Cancel monitoring tasks
        for task in [self._monitor_task, self._scaling_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop all workers
        await self._stop_all_workers()
        
        logger.info("Worker pool stopped")
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution"""
        if not self.is_running:
            raise RuntimeError("Worker pool is not running")
        
        # Add task to queue
        success = await self.task_queue.enqueue(task)
        if not success:
            raise RuntimeError(f"Failed to enqueue task {task.id}")
        
        return task.id
    
    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a completed task"""
        return await self.result_store.get_result(task_id)
    
    async def scale_workers(self, target_count: int) -> None:
        """Manually scale workers to target count"""
        target_count = max(self.min_workers, min(self.max_workers, target_count))
        await self._scale_to_target(target_count)
    
    async def _scale_to_target(self, target_count: int) -> None:
        """Scale workers to target count"""
        current_count = len(self.workers)
        
        if target_count > current_count:
            # Scale up
            for _ in range(target_count - current_count):
                await self._add_worker()
        elif target_count < current_count:
            # Scale down
            workers_to_remove = current_count - target_count
            await self._remove_workers(workers_to_remove)
        
        if target_count != current_count:
            self.total_scaling_events += 1
            self.last_scale_event = datetime.utcnow()
            logger.info(f"Scaled workers from {current_count} to {len(self.workers)}")
    
    async def _add_worker(self) -> None:
        """Add a new worker to the pool"""
        worker = AsyncWorker(
            max_concurrent_tasks=settings.workers.max_tasks_per_worker
        )
        
        await worker.start()
        self.workers[worker.worker_id] = worker
        
        # Start worker processing loop
        worker_task = asyncio.create_task(self._worker_loop(worker))
        self.worker_tasks[worker.worker_id] = worker_task
        
        logger.debug(f"Added worker {worker.worker_id}")
    
    async def _remove_workers(self, count: int) -> None:
        """Remove workers from the pool"""
        if count <= 0:
            return
        
        # Select workers to remove (prefer those with least load)
        worker_loads = []
        for worker_id, worker in self.workers.items():
            load = await worker.get_current_load()
            worker_loads.append((load, worker_id, worker))
        
        # Sort by load (ascending) and remove the least loaded workers
        worker_loads.sort(key=lambda x: x[0])
        workers_to_remove = worker_loads[:count]
        
        for load, worker_id, worker in workers_to_remove:
            await self._remove_worker(worker_id)
    
    async def _remove_worker(self, worker_id: str) -> None:
        """Remove a specific worker"""
        if worker_id not in self.workers:
            return
        
        worker = self.workers[worker_id]
        worker_task = self.worker_tasks.get(worker_id)
        
        # Stop the worker
        await worker.stop()
        
        # Cancel worker task
        if worker_task and not worker_task.done():
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        
        # Clean up
        self.workers.pop(worker_id, None)
        self.worker_tasks.pop(worker_id, None)
        
        logger.debug(f"Removed worker {worker_id}")
    
    async def _worker_loop(self, worker: AsyncWorker) -> None:
        """Main processing loop for a worker"""
        while self.is_running and worker.is_running:
            try:
                # Check if worker can accept more tasks
                if not worker.can_accept_task():
                    await asyncio.sleep(0.1)
                    continue
                
                # Get task from queue (non-blocking)
                task = await self.task_queue.dequeue(timeout=1.0)
                if not task:
                    continue
                
                # Execute task
                result = await worker.execute_task(task)
                
                # Store result
                await self.result_store.store_result(result)
                
                # Update queue metadata
                if result.status == TaskStatus.COMPLETED:
                    await self.task_queue.mark_task_completed(task.id)
                    self.total_tasks_processed += 1
                else:
                    await self.task_queue.mark_task_failed(
                        task.id, 
                        str(result.error) if result.error else "Unknown error"
                    )
                    self.total_tasks_failed += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker.worker_id} encountered error: {e}")
                await asyncio.sleep(1.0)
    
    async def _monitor_loop(self) -> None:
        """Monitor worker health and performance"""
        while self.is_running and not self._shutdown_event.is_set():
            try:
                # Check worker health
                unhealthy_workers = []
                for worker_id, worker in self.workers.items():
                    if not await worker.is_healthy():
                        unhealthy_workers.append(worker_id)
                
                # Replace unhealthy workers
                for worker_id in unhealthy_workers:
                    logger.warning(f"Replacing unhealthy worker {worker_id}")
                    await self._remove_worker(worker_id)
                    if len(self.workers) < self.min_workers:
                        await self._add_worker()
                
                # Collect load metrics for scaling decisions
                await self._collect_load_metrics()
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(10)
    
    async def _scaling_loop(self) -> None:
        """Auto-scaling loop"""
        while self.is_running and not self._shutdown_event.is_set():
            try:
                await self._evaluate_scaling()
                await asyncio.sleep(15)  # Check scaling every 15 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scaling loop error: {e}")
                await asyncio.sleep(15)
    
    async def _collect_load_metrics(self) -> None:
        """Collect load metrics for scaling decisions"""
        if not self.workers:
            return
        
        # Calculate overall load
        total_load = 0.0
        healthy_workers = 0
        
        for worker in self.workers.values():
            if await worker.is_healthy():
                load = await worker.get_current_load()
                total_load += load
                healthy_workers += 1
        
        if healthy_workers > 0:
            avg_load = total_load / healthy_workers
        else:
            avg_load = 1.0  # No healthy workers = high load
        
        # Get queue depth
        queue_size = await self.task_queue.size()
        
        # Calculate combined load metric
        queue_factor = min(1.0, queue_size / 100.0)  # Normalize queue size
        combined_load = (avg_load * 0.7) + (queue_factor * 0.3)
        
        self.load_history.append({
            'timestamp': datetime.utcnow(),
            'avg_worker_load': avg_load,
            'queue_size': queue_size,
            'combined_load': combined_load,
            'worker_count': len(self.workers),
            'healthy_workers': healthy_workers
        })
    
    async def _evaluate_scaling(self) -> None:
        """Evaluate if scaling is needed"""
        if len(self.load_history) < 3:  # Need some history
            return
        
        # Check cooldown period
        if (self.last_scale_event and 
            datetime.utcnow() - self.last_scale_event < self.scale_cooldown):
            return
        
        # Get recent load average
        recent_loads = [m['combined_load'] for m in list(self.load_history)[-3:]]
        avg_recent_load = sum(recent_loads) / len(recent_loads)
        
        current_workers = len(self.workers)
        
        # Scale up conditions
        if (avg_recent_load > self.scale_up_threshold and 
            current_workers < self.max_workers):
            
            # Calculate how many workers to add
            target_workers = min(
                self.max_workers,
                current_workers + max(1, int((avg_recent_load - self.scale_up_threshold) * 4))
            )
            
            logger.info(f"Scaling up: load={avg_recent_load:.2f}, "
                       f"current={current_workers}, target={target_workers}")
            await self._scale_to_target(target_workers)
        
        # Scale down conditions
        elif (avg_recent_load < self.scale_down_threshold and 
              current_workers > self.min_workers):
            
            # Calculate how many workers to remove
            target_workers = max(
                self.min_workers,
                current_workers - max(1, int((self.scale_down_threshold - avg_recent_load) * 2))
            )
            
            logger.info(f"Scaling down: load={avg_recent_load:.2f}, "
                       f"current={current_workers}, target={target_workers}")
            await self._scale_to_target(target_workers)
    
    async def _stop_all_workers(self) -> None:
        """Stop all workers"""
        # Cancel all worker tasks
        for worker_task in self.worker_tasks.values():
            if not worker_task.done():
                worker_task.cancel()
        
        # Wait for worker tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks.values(), return_exceptions=True)
        
        # Stop all workers
        for worker in self.workers.values():
            await worker.stop()
        
        self.workers.clear()
        self.worker_tasks.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Aggregate worker stats
        worker_stats = []
        total_current_tasks = 0
        total_completed = 0
        total_failed = 0
        healthy_workers = 0
        
        for worker in self.workers.values():
            stats = worker.get_stats()
            worker_stats.append(stats)
            total_current_tasks += stats['current_tasks']
            total_completed += stats['completed_tasks']
            total_failed += stats['failed_tasks']
            if stats['is_healthy']:
                healthy_workers += 1
        
        # Get recent load metrics
        recent_load = 0.0
        if self.load_history:
            recent_load = self.load_history[-1]['combined_load']
        
        return {
            'pool_id': id(self),
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'worker_count': len(self.workers),
            'healthy_workers': healthy_workers,
            'min_workers': self.min_workers,
            'max_workers': self.max_workers,
            'current_load': recent_load,
            'scale_up_threshold': self.scale_up_threshold,
            'scale_down_threshold': self.scale_down_threshold,
            'total_current_tasks': total_current_tasks,
            'total_tasks_processed': self.total_tasks_processed,
            'total_tasks_failed': self.total_tasks_failed,
            'total_scaling_events': self.total_scaling_events,
            'last_scale_event': self.last_scale_event.isoformat() if self.last_scale_event else None,
            'worker_stats': worker_stats,
            'load_history': list(self.load_history)[-10:]  # Last 10 data points
        }