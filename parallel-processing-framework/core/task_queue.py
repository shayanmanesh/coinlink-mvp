"""
Redis-based task queue implementation with priority support
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis
import pickle
import base64

from .interfaces import ITaskQueue, Task, TaskPriority
from config.settings import settings

logger = logging.getLogger(__name__)


class RedisTaskQueue(ITaskQueue):
    """Redis-based task queue with priority support and persistence"""
    
    def __init__(self, 
                 redis_url: Optional[str] = None, 
                 queue_prefix: str = "ppf",
                 max_retries: int = 3):
        self.redis_url = redis_url or settings.redis.connection_url
        self.queue_prefix = queue_prefix
        self.max_retries = max_retries
        self.redis: Optional[aioredis.Redis] = None
        
        # Queue names for different priorities
        self.priority_queues = {
            TaskPriority.URGENT: f"{queue_prefix}:queue:urgent",
            TaskPriority.CRITICAL: f"{queue_prefix}:queue:critical", 
            TaskPriority.HIGH: f"{queue_prefix}:queue:high",
            TaskPriority.NORMAL: f"{queue_prefix}:queue:normal",
            TaskPriority.LOW: f"{queue_prefix}:queue:low"
        }
        
        # Metadata storage
        self.task_metadata_key = f"{queue_prefix}:tasks:metadata"
        self.stats_key = f"{queue_prefix}:stats"
        self.processing_key = f"{queue_prefix}:processing"
        
        self._stats = {
            'total_enqueued': 0,
            'total_dequeued': 0,
            'total_failed': 0,
            'current_size': 0
        }
    
    async def connect(self) -> None:
        """Connect to Redis"""
        if self.redis is None:
            self.redis = aioredis.from_url(
                self.redis_url,
                max_connections=settings.redis.max_connections,
                retry_on_timeout=True,
                decode_responses=False  # We handle encoding ourselves
            )
            await self.redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis")
    
    def _serialize_task(self, task: Task) -> bytes:
        """Serialize task to bytes for Redis storage"""
        task_data = {
            'id': task.id,
            'func_name': task.func.__name__ if hasattr(task.func, '__name__') else str(task.func),
            'func': base64.b64encode(pickle.dumps(task.func)).decode('utf-8'),
            'args': base64.b64encode(pickle.dumps(task.args)).decode('utf-8'),
            'kwargs': base64.b64encode(pickle.dumps(task.kwargs)).decode('utf-8'),
            'priority': task.priority.value,
            'timeout': task.timeout,
            'max_retries': task.max_retries,
            'metadata': task.metadata,
            'created_at': task.created_at.isoformat()
        }
        return json.dumps(task_data).encode('utf-8')
    
    def _deserialize_task(self, data: bytes) -> Task:
        """Deserialize task from bytes"""
        task_data = json.loads(data.decode('utf-8'))
        
        # Deserialize function and arguments
        func = pickle.loads(base64.b64decode(task_data['func']))
        args = pickle.loads(base64.b64decode(task_data['args']))
        kwargs = pickle.loads(base64.b64decode(task_data['kwargs']))
        
        task = Task(
            id=task_data['id'],
            func=func,
            args=args,
            kwargs=kwargs,
            priority=TaskPriority(task_data['priority']),
            timeout=task_data['timeout'],
            max_retries=task_data['max_retries'],
            metadata=task_data['metadata'],
            created_at=datetime.fromisoformat(task_data['created_at'])
        )
        return task
    
    async def enqueue(self, task: Task) -> bool:
        """Add a task to the appropriate priority queue"""
        await self.connect()
        
        try:
            # Serialize task
            serialized_task = self._serialize_task(task)
            
            # Get the appropriate queue for this priority
            queue_name = self.priority_queues[task.priority]
            
            # Use Redis pipeline for atomic operations
            async with self.redis.pipeline() as pipe:
                # Add task to priority queue
                await pipe.lpush(queue_name, serialized_task)
                
                # Store task metadata
                await pipe.hset(
                    self.task_metadata_key,
                    task.id,
                    json.dumps({
                        'status': 'enqueued',
                        'enqueued_at': datetime.utcnow().isoformat(),
                        'priority': task.priority.value,
                        'queue': queue_name
                    })
                )
                
                # Update stats
                await pipe.hincrby(self.stats_key, 'total_enqueued', 1)
                await pipe.hincrby(self.stats_key, 'current_size', 1)
                
                await pipe.execute()
            
            self._stats['total_enqueued'] += 1
            self._stats['current_size'] += 1
            
            logger.debug(f"Enqueued task {task.id} with priority {task.priority.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.id}: {e}")
            return False
    
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Task]:
        """Remove and return a task from the highest priority queue"""
        await self.connect()
        
        # Define queue priority order (highest to lowest)
        queue_order = [
            self.priority_queues[TaskPriority.URGENT],
            self.priority_queues[TaskPriority.CRITICAL],
            self.priority_queues[TaskPriority.HIGH],
            self.priority_queues[TaskPriority.NORMAL],
            self.priority_queues[TaskPriority.LOW]
        ]
        
        try:
            # Try to get a task from queues in priority order
            if timeout:
                # Use blocking pop with timeout
                result = await self.redis.brpop(queue_order, timeout=timeout)
            else:
                # Try each queue in priority order
                result = None
                for queue_name in queue_order:
                    data = await self.redis.rpop(queue_name)
                    if data:
                        result = (queue_name.encode(), data)
                        break
            
            if not result:
                return None
            
            queue_name, task_data = result
            task = self._deserialize_task(task_data)
            
            # Update task metadata and stats
            async with self.redis.pipeline() as pipe:
                # Update task status
                await pipe.hset(
                    self.task_metadata_key,
                    task.id,
                    json.dumps({
                        'status': 'dequeued',
                        'dequeued_at': datetime.utcnow().isoformat(),
                        'priority': task.priority.value
                    })
                )
                
                # Add to processing set
                await pipe.sadd(self.processing_key, task.id)
                
                # Update stats
                await pipe.hincrby(self.stats_key, 'total_dequeued', 1)
                await pipe.hincrby(self.stats_key, 'current_size', -1)
                
                await pipe.execute()
            
            self._stats['total_dequeued'] += 1
            self._stats['current_size'] = max(0, self._stats['current_size'] - 1)
            
            logger.debug(f"Dequeued task {task.id} from {queue_name.decode()}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to dequeue task: {e}")
            return None
    
    async def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed and remove from processing set"""
        await self.connect()
        
        try:
            async with self.redis.pipeline() as pipe:
                await pipe.srem(self.processing_key, task_id)
                await pipe.hset(
                    self.task_metadata_key,
                    task_id,
                    json.dumps({
                        'status': 'completed',
                        'completed_at': datetime.utcnow().isoformat()
                    })
                )
                await pipe.execute()
                
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as completed: {e}")
    
    async def mark_task_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed"""
        await self.connect()
        
        try:
            async with self.redis.pipeline() as pipe:
                await pipe.srem(self.processing_key, task_id)
                await pipe.hset(
                    self.task_metadata_key,
                    task_id,
                    json.dumps({
                        'status': 'failed',
                        'failed_at': datetime.utcnow().isoformat(),
                        'error': error
                    })
                )
                await pipe.hincrby(self.stats_key, 'total_failed', 1)
                await pipe.execute()
                
            self._stats['total_failed'] += 1
            
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as failed: {e}")
    
    async def size(self) -> int:
        """Get the total number of tasks in all queues"""
        await self.connect()
        
        try:
            total_size = 0
            for queue_name in self.priority_queues.values():
                size = await self.redis.llen(queue_name)
                total_size += size
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0
    
    async def size_by_priority(self) -> Dict[str, int]:
        """Get queue sizes by priority"""
        await self.connect()
        
        sizes = {}
        try:
            for priority, queue_name in self.priority_queues.items():
                size = await self.redis.llen(queue_name)
                sizes[priority.name] = size
            return sizes
            
        except Exception as e:
            logger.error(f"Failed to get queue sizes by priority: {e}")
            return {}
    
    async def clear(self) -> None:
        """Clear all tasks from all queues"""
        await self.connect()
        
        try:
            async with self.redis.pipeline() as pipe:
                # Clear all priority queues
                for queue_name in self.priority_queues.values():
                    await pipe.delete(queue_name)
                
                # Clear metadata and processing sets
                await pipe.delete(self.task_metadata_key)
                await pipe.delete(self.processing_key)
                await pipe.delete(self.stats_key)
                
                await pipe.execute()
            
            # Reset local stats
            self._stats = {
                'total_enqueued': 0,
                'total_dequeued': 0,
                'total_failed': 0,
                'current_size': 0
            }
            
            logger.info("Cleared all queues")
            
        except Exception as e:
            logger.error(f"Failed to clear queues: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        await self.connect()
        
        try:
            # Get Redis stats
            redis_stats = await self.redis.hgetall(self.stats_key)
            redis_stats = {k.decode(): int(v.decode()) for k, v in redis_stats.items()}
            
            # Get current queue sizes
            sizes_by_priority = await self.size_by_priority()
            current_size = sum(sizes_by_priority.values())
            
            # Get processing count
            processing_count = await self.redis.scard(self.processing_key)
            
            stats = {
                'total_enqueued': redis_stats.get('total_enqueued', 0),
                'total_dequeued': redis_stats.get('total_dequeued', 0),
                'total_failed': redis_stats.get('total_failed', 0),
                'current_size': current_size,
                'processing_count': processing_count,
                'sizes_by_priority': sizes_by_priority,
                'throughput_1m': await self._calculate_throughput(60),
                'throughput_5m': await self._calculate_throughput(300),
                'connection_status': 'connected' if self.redis else 'disconnected'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {'error': str(e)}
    
    async def _calculate_throughput(self, window_seconds: int) -> float:
        """Calculate tasks per second throughput over a time window"""
        # This is a simplified implementation
        # In production, you'd want to maintain time-series data
        try:
            stats = await self.redis.hgetall(self.stats_key)
            if not stats:
                return 0.0
            
            total_processed = int(stats.get(b'total_dequeued', 0))
            # For now, return average throughput since start
            # In production, implement proper time-window calculations
            return total_processed / max(window_seconds, 1)
            
        except Exception:
            return 0.0
    
    async def get_task_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific task"""
        await self.connect()
        
        try:
            metadata = await self.redis.hget(self.task_metadata_key, task_id)
            if metadata:
                return json.loads(metadata.decode())
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task metadata for {task_id}: {e}")
            return None