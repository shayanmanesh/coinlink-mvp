"""
Core interfaces and abstract base classes for the parallel processing framework
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 3
    HIGH = 5
    CRITICAL = 7
    URGENT = 9


@dataclass
class Task:
    """Represents a task to be executed"""
    id: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[int] = None
    max_retries: int = 3
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.kwargs is None:
            self.kwargs = {}
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class TaskResult:
    """Represents the result of a task execution"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    worker_id: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.start_time and self.end_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()


class ITaskQueue(ABC):
    """Interface for task queue implementations"""
    
    @abstractmethod
    async def enqueue(self, task: Task) -> bool:
        """Add a task to the queue"""
        pass
    
    @abstractmethod
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Task]:
        """Remove and return a task from the queue"""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get the current queue size"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all tasks from the queue"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        pass


class IWorker(ABC):
    """Interface for worker implementations"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the worker"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the worker"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task and return the result"""
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if the worker is healthy"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        pass


class IWorkerPool(ABC):
    """Interface for worker pool implementations"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the worker pool"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the worker pool"""
        pass
    
    @abstractmethod
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution"""
        pass
    
    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a completed task"""
        pass
    
    @abstractmethod
    async def scale_workers(self, target_count: int) -> None:
        """Scale the number of workers"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        pass


class IResultStore(ABC):
    """Interface for result storage implementations"""
    
    @abstractmethod
    async def store_result(self, result: TaskResult) -> bool:
        """Store a task result"""
        pass
    
    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Retrieve a task result"""
        pass
    
    @abstractmethod
    async def delete_result(self, task_id: str) -> bool:
        """Delete a task result"""
        pass
    
    @abstractmethod
    async def get_results_stream(self, task_ids: List[str]) -> AsyncGenerator[TaskResult, None]:
        """Stream results for multiple tasks"""
        pass


class ICircuitBreaker(ABC):
    """Interface for circuit breaker implementations"""
    
    @abstractmethod
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection"""
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """Get the current circuit breaker state"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        pass


class IMonitor(ABC):
    """Interface for monitoring implementations"""
    
    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        pass
    
    @abstractmethod
    async def alert(self, message: str, severity: str = "info") -> None:
        """Send an alert"""
        pass


class IOrchestrator(ABC):
    """Interface for task orchestration implementations"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the orchestrator"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the orchestrator"""
        pass
    
    @abstractmethod
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution"""
        pass
    
    @abstractmethod
    async def submit_batch(self, tasks: List[Task]) -> List[str]:
        """Submit multiple tasks for execution"""
        pass
    
    @abstractmethod
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """Get the result of a task"""
        pass
    
    @abstractmethod
    async def get_results(self, task_ids: List[str], timeout: Optional[float] = None) -> List[TaskResult]:
        """Get results for multiple tasks"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        pass