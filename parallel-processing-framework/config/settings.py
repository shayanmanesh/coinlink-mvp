"""
Configuration settings for the Parallel Processing Framework
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os


class RedisSettings(BaseSettings):
    """Redis configuration"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    url: Optional[str] = Field(default=None, env="REDIS_URL")
    max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    @property
    def connection_url(self) -> str:
        if self.url:
            return self.url
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class WorkerSettings(BaseSettings):
    """Worker pool configuration"""
    min_workers: int = Field(default=2, env="MIN_WORKERS")
    max_workers: int = Field(default=16, env="MAX_WORKERS")
    scale_up_threshold: float = Field(default=0.8, env="SCALE_UP_THRESHOLD")
    scale_down_threshold: float = Field(default=0.3, env="SCALE_DOWN_THRESHOLD")
    worker_timeout: int = Field(default=300, env="WORKER_TIMEOUT")
    heartbeat_interval: int = Field(default=30, env="HEARTBEAT_INTERVAL")
    max_tasks_per_worker: int = Field(default=100, env="MAX_TASKS_PER_WORKER")


class ProcessingSettings(BaseSettings):
    """Task processing configuration"""
    task_timeout: int = Field(default=600, env="TASK_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="RETRY_DELAY")
    max_concurrent_tasks: int = Field(default=1000, env="MAX_CONCURRENT_TASKS")
    result_ttl: int = Field(default=3600, env="RESULT_TTL")  # 1 hour
    
    # Queue settings
    priority_levels: int = Field(default=5, env="PRIORITY_LEVELS")
    high_priority_threshold: int = Field(default=100, env="HIGH_PRIORITY_THRESHOLD")
    
    # Circuit breaker settings
    failure_threshold: int = Field(default=5, env="FAILURE_THRESHOLD")
    recovery_timeout: int = Field(default=60, env="RECOVERY_TIMEOUT")
    half_open_max_calls: int = Field(default=3, env="HALF_OPEN_MAX_CALLS")


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration"""
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Performance thresholds
    max_memory_usage: float = Field(default=0.85, env="MAX_MEMORY_USAGE")
    max_cpu_usage: float = Field(default=0.90, env="MAX_CPU_USAGE")
    alert_on_queue_depth: int = Field(default=1000, env="ALERT_QUEUE_DEPTH")


class EventLoopSettings(BaseSettings):
    """AsyncIO event loop configuration"""
    use_uvloop: bool = Field(default=True, env="USE_UVLOOP")
    max_connections: int = Field(default=1000, env="MAX_CONNECTIONS")
    connection_timeout: float = Field(default=30.0, env="CONNECTION_TIMEOUT")
    keepalive_timeout: float = Field(default=60.0, env="KEEPALIVE_TIMEOUT")


class FrameworkSettings(BaseSettings):
    """Main framework configuration"""
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Component settings
    redis: RedisSettings = RedisSettings()
    workers: WorkerSettings = WorkerSettings()
    processing: ProcessingSettings = ProcessingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    event_loop: EventLoopSettings = EventLoopSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = FrameworkSettings()