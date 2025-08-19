"""
Result storage and aggregation with streaming support
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, AsyncGenerator, Set, Callable
import redis.asyncio as aioredis
import pickle
import base64
from collections import defaultdict

from .interfaces import IResultStore, TaskResult, TaskStatus
from config.settings import settings

logger = logging.getLogger(__name__)


class RedisResultStore(IResultStore):
    """Redis-based result store with streaming capabilities"""
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 key_prefix: str = "ppf",
                 result_ttl: int = None):
        self.redis_url = redis_url or settings.redis.connection_url
        self.key_prefix = key_prefix
        self.result_ttl = result_ttl or settings.processing.result_ttl
        
        self.redis: Optional[aioredis.Redis] = None
        
        # Keys for different data types
        self.results_key = f"{key_prefix}:results"
        self.notifications_key = f"{key_prefix}:notifications"
        self.streams_key = f"{key_prefix}:streams"
        
        # Active result streams
        self.active_streams: Dict[str, Set[str]] = defaultdict(set)
        self.stream_callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    async def connect(self) -> None:
        """Connect to Redis"""
        if self.redis is None:
            self.redis = aioredis.from_url(
                self.redis_url,
                max_connections=settings.redis.max_connections,
                retry_on_timeout=True,
                decode_responses=False
            )
            await self.redis.ping()
            logger.info(f"Result store connected to Redis at {self.redis_url}")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Result store disconnected from Redis")
    
    def _serialize_result(self, result: TaskResult) -> bytes:
        """Serialize result to bytes for Redis storage"""
        result_data = {
            'task_id': result.task_id,
            'status': result.status.value,
            'result': base64.b64encode(pickle.dumps(result.result)).decode('utf-8') if result.result is not None else None,
            'error': str(result.error) if result.error else None,
            'start_time': result.start_time.isoformat() if result.start_time else None,
            'end_time': result.end_time.isoformat() if result.end_time else None,
            'execution_time': result.execution_time,
            'worker_id': result.worker_id,
            'retry_count': result.retry_count,
            'metadata': result.metadata
        }
        return json.dumps(result_data).encode('utf-8')
    
    def _deserialize_result(self, data: bytes) -> TaskResult:
        """Deserialize result from bytes"""
        result_data = json.loads(data.decode('utf-8'))
        
        # Deserialize the actual result
        result_value = None
        if result_data['result']:
            try:
                result_value = pickle.loads(base64.b64decode(result_data['result']))
            except Exception as e:
                logger.warning(f"Failed to deserialize result: {e}")
        
        return TaskResult(
            task_id=result_data['task_id'],
            status=TaskStatus(result_data['status']),
            result=result_value,
            error=Exception(result_data['error']) if result_data['error'] else None,
            start_time=datetime.fromisoformat(result_data['start_time']) if result_data['start_time'] else None,
            end_time=datetime.fromisoformat(result_data['end_time']) if result_data['end_time'] else None,
            execution_time=result_data['execution_time'],
            worker_id=result_data['worker_id'],
            retry_count=result_data['retry_count'],
            metadata=result_data['metadata'] or {}
        )
    
    async def store_result(self, result: TaskResult) -> bool:
        """Store a task result"""
        await self.connect()
        
        try:
            serialized_result = self._serialize_result(result)
            
            # Store result with TTL
            async with self.redis.pipeline() as pipe:
                await pipe.hset(self.results_key, result.task_id, serialized_result)
                await pipe.expire(f"{self.results_key}:{result.task_id}", self.result_ttl)
                
                # Publish notification for streaming
                notification = {
                    'task_id': result.task_id,
                    'status': result.status.value,
                    'timestamp': datetime.utcnow().isoformat()
                }
                await pipe.publish(self.notifications_key, json.dumps(notification))
                
                await pipe.execute()
            
            logger.debug(f"Stored result for task {result.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store result for task {result.task_id}: {e}")
            return False
    
    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Retrieve a task result"""
        await self.connect()
        
        try:
            data = await self.redis.hget(self.results_key, task_id)
            if data:
                return self._deserialize_result(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get result for task {task_id}: {e}")
            return None
    
    async def delete_result(self, task_id: str) -> bool:
        """Delete a task result"""
        await self.connect()
        
        try:
            deleted = await self.redis.hdel(self.results_key, task_id)
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Failed to delete result for task {task_id}: {e}")
            return False
    
    async def get_results_stream(self, task_ids: List[str]) -> AsyncGenerator[TaskResult, None]:
        """Stream results for multiple tasks as they become available"""
        await self.connect()
        
        remaining_tasks = set(task_ids)
        yielded_tasks = set()
        
        # First, yield any results that are already available
        for task_id in task_ids:
            if task_id in yielded_tasks:
                continue
                
            result = await self.get_result(task_id)
            if result:
                yielded_tasks.add(task_id)
                remaining_tasks.discard(task_id)
                yield result
        
        if not remaining_tasks:
            return
        
        # Subscribe to notifications for remaining tasks
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.notifications_key)
        
        try:
            while remaining_tasks:
                try:
                    # Wait for notification with timeout
                    message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=30.0)
                    
                    if message and message['type'] == 'message':
                        notification = json.loads(message['data'].decode('utf-8'))
                        task_id = notification['task_id']
                        
                        if task_id in remaining_tasks:
                            result = await self.get_result(task_id)
                            if result:
                                yielded_tasks.add(task_id)
                                remaining_tasks.discard(task_id)
                                yield result
                
                except asyncio.TimeoutError:
                    # Check for any new results that might have been missed
                    for task_id in list(remaining_tasks):
                        if task_id not in yielded_tasks:
                            result = await self.get_result(task_id)
                            if result:
                                yielded_tasks.add(task_id)
                                remaining_tasks.discard(task_id)
                                yield result
                    
                    if remaining_tasks:
                        logger.debug(f"Still waiting for {len(remaining_tasks)} results")
                
        finally:
            await pubsub.unsubscribe(self.notifications_key)
            await pubsub.close()
    
    async def get_results_batch(self, task_ids: List[str], timeout: Optional[float] = None) -> List[TaskResult]:
        """Get results for multiple tasks, waiting up to timeout seconds"""
        results = []
        
        if timeout is None:
            # Get all available results immediately
            for task_id in task_ids:
                result = await self.get_result(task_id)
                if result:
                    results.append(result)
        else:
            # Stream results with timeout
            start_time = asyncio.get_event_loop().time()
            async for result in self.get_results_stream(task_ids):
                results.append(result)
                
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    break
        
        return results
    
    async def wait_for_results(self, task_ids: List[str], timeout: Optional[float] = None) -> List[TaskResult]:
        """Wait for all specified task results to be available"""
        results = []
        completed_tasks = set()
        
        start_time = asyncio.get_event_loop().time()
        
        async for result in self.get_results_stream(task_ids):
            results.append(result)
            completed_tasks.add(result.task_id)
            
            # Check if all tasks are completed
            if len(completed_tasks) >= len(task_ids):
                break
            
            # Check timeout
            if timeout and (asyncio.get_event_loop().time() - start_time > timeout):
                logger.warning(f"Timeout waiting for results. Got {len(results)}/{len(task_ids)} results")
                break
        
        return results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get result store statistics"""
        await self.connect()
        
        try:
            # Get total stored results
            total_results = await self.redis.hlen(self.results_key)
            
            # Get status distribution
            status_counts = defaultdict(int)
            cursor = 0
            while True:
                cursor, results = await self.redis.hscan(self.results_key, cursor, count=100)
                
                for task_id, data in results.items():
                    try:
                        result_data = json.loads(data.decode('utf-8'))
                        status = result_data['status']
                        status_counts[status] += 1
                    except Exception:
                        continue
                
                if cursor == 0:
                    break
            
            return {
                'total_results': total_results,
                'status_distribution': dict(status_counts),
                'active_streams': len(self.active_streams),
                'result_ttl': self.result_ttl
            }
            
        except Exception as e:
            logger.error(f"Failed to get result store stats: {e}")
            return {'error': str(e)}
    
    async def cleanup_expired_results(self) -> int:
        """Clean up expired results (manual cleanup)"""
        await self.connect()
        
        try:
            expired_count = 0
            cursor = 0
            current_time = datetime.utcnow()
            
            while True:
                cursor, results = await self.redis.hscan(self.results_key, cursor, count=100)
                
                for task_id, data in results.items():
                    try:
                        result_data = json.loads(data.decode('utf-8'))
                        if result_data.get('end_time'):
                            end_time = datetime.fromisoformat(result_data['end_time'])
                            if current_time - end_time > timedelta(seconds=self.result_ttl):
                                await self.redis.hdel(self.results_key, task_id.decode())
                                expired_count += 1
                    except Exception:
                        continue
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleaned up {expired_count} expired results")
            return expired_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired results: {e}")
            return 0


class ResultAggregator:
    """High-level result aggregation with advanced features"""
    
    def __init__(self, result_store: IResultStore):
        self.result_store = result_store
    
    async def aggregate_results(self, 
                              task_ids: List[str],
                              aggregation_func: Callable[[List[TaskResult]], Any],
                              timeout: Optional[float] = None) -> Any:
        """Aggregate results using a custom function"""
        results = await self.result_store.wait_for_results(task_ids, timeout)
        
        # Filter only successful results
        successful_results = [r for r in results if r.status == TaskStatus.COMPLETED]
        
        if not successful_results:
            raise RuntimeError("No successful results to aggregate")
        
        return aggregation_func(successful_results)
    
    async def collect_streaming_results(self,
                                      task_ids: List[str],
                                      callback: Callable[[TaskResult], None],
                                      timeout: Optional[float] = None) -> None:
        """Collect results with streaming callback"""
        start_time = asyncio.get_event_loop().time()
        
        async for result in self.result_store.get_results_stream(task_ids):
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Callback error for task {result.task_id}: {e}")
            
            # Check timeout
            if timeout and (asyncio.get_event_loop().time() - start_time > timeout):
                break
    
    async def batch_process_results(self,
                                  task_ids: List[str],
                                  batch_size: int = 10,
                                  processor: Callable[[List[TaskResult]], Any] = None) -> List[Any]:
        """Process results in batches as they arrive"""
        results = []
        batch = []
        processed_results = []
        
        async for result in self.result_store.get_results_stream(task_ids):
            batch.append(result)
            
            if len(batch) >= batch_size:
                if processor:
                    try:
                        processed = processor(batch)
                        processed_results.append(processed)
                    except Exception as e:
                        logger.error(f"Batch processor error: {e}")
                
                results.extend(batch)
                batch = []
        
        # Process remaining results
        if batch:
            if processor:
                try:
                    processed = processor(batch)
                    processed_results.append(processed)
                except Exception as e:
                    logger.error(f"Final batch processor error: {e}")
            
            results.extend(batch)
        
        return processed_results if processor else results