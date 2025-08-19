"""
Backend Metrics Tracker - Performance & Infrastructure Monitoring

Ultra-comprehensive metrics tracking system for backend department.
Monitors API performance, database efficiency, infrastructure health,
agent productivity, and system reliability with real-time analytics.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import statistics

logger = logging.getLogger(__name__)

class MetricCategory(Enum):
    """Categories of backend metrics"""
    API_PERFORMANCE = "api_performance"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    RELIABILITY = "reliability"
    AGENT_PRODUCTIVITY = "agent_productivity"

class MetricSeverity(Enum):
    """Metric alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class BackendMetric:
    """Individual backend metric data point"""
    id: str
    name: str
    category: MetricCategory
    value: float
    target: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def performance_ratio(self) -> float:
        """Calculate performance ratio (actual/target)"""
        if self.target == 0:
            return 1.0
        return self.value / self.target
    
    @property
    def is_on_target(self) -> bool:
        """Check if metric meets target"""
        # For metrics where lower is better
        if self.name in ["response_time", "error_rate", "cpu_usage", "memory_usage", "query_time"]:
            return self.value <= self.target
        # For metrics where higher is better
        elif self.name in ["throughput", "uptime", "cache_hit_rate", "connection_efficiency"]:
            return self.value >= self.target
        else:
            return abs(self.performance_ratio - 1.0) <= 0.1  # Within 10%

@dataclass
class AgentProductivityMetrics:
    """Backend agent productivity tracking"""
    agent_id: str
    agent_name: str
    period_start: datetime
    period_end: datetime
    
    # Task metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_task_time: float = 0.0
    quality_score: float = 0.0
    
    # Output metrics
    apis_deployed: int = 0
    apis_optimized: int = 0
    database_optimizations: int = 0
    infrastructure_improvements: int = 0
    
    # Impact metrics
    performance_impact: float = 0.0
    reliability_impact: float = 0.0
    security_improvements: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 0.0
        return (self.tasks_completed / total_tasks) * 100
    
    @property
    def productivity_score(self) -> float:
        """Calculate overall productivity score"""
        factors = [
            self.success_rate / 100,
            min(1.0, self.quality_score / 100),
            min(1.0, self.apis_deployed / 5),  # Normalize to 5 APIs
            min(1.0, self.infrastructure_improvements / 3)  # Normalize to 3 improvements
        ]
        return (sum(factors) / len(factors)) * 100

@dataclass
class SystemHealthSnapshot:
    """System health and performance snapshot"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # API Performance
    api_response_time: float = 0.0          # milliseconds
    api_throughput: float = 0.0             # requests per second
    api_error_rate: float = 0.0             # percentage
    api_uptime: float = 0.0                 # percentage
    
    # Database Performance
    db_query_time: float = 0.0              # milliseconds
    db_connection_pool_usage: float = 0.0   # percentage
    db_cache_hit_rate: float = 0.0          # percentage
    db_slow_queries: int = 0                # count
    
    # Infrastructure Metrics
    cpu_usage: float = 0.0                  # percentage
    memory_usage: float = 0.0               # percentage
    disk_usage: float = 0.0                 # percentage
    network_io: float = 0.0                 # MB/s
    disk_io: float = 0.0                    # MB/s
    
    # System Resources
    active_connections: int = 0
    queue_depth: int = 0
    background_tasks: int = 0
    cache_memory_usage: float = 0.0         # MB
    
    # Security Metrics
    failed_auth_attempts: int = 0
    blocked_ips: int = 0
    security_violations: int = 0
    ssl_certificate_validity: float = 0.0   # days remaining

@dataclass
class MetricAlert:
    """System performance alert"""
    id: str = field(default_factory=lambda: f"alert_{int(datetime.utcnow().timestamp())}")
    metric_name: str = ""
    severity: MetricSeverity = MetricSeverity.INFO
    message: str = ""
    current_value: float = 0.0
    target_value: float = 0.0
    deviation_percentage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

class BackendMetricsTracker:
    """Comprehensive backend metrics tracking system"""
    
    def __init__(self):
        self.tracker_id = "backend_metrics_tracker"
        
        # Metrics storage
        self.current_metrics: Dict[str, BackendMetric] = {}
        self.metric_history: defaultdict = defaultdict(deque)  # metric_name -> deque of values
        self.system_snapshots: deque = deque(maxlen=100)
        
        # Agent productivity tracking
        self.agent_productivity: Dict[str, AgentProductivityMetrics] = {}
        self.productivity_history: deque = deque(maxlen=50)
        
        # Alerting system
        self.active_alerts: Dict[str, MetricAlert] = {}
        self.alert_history: deque = deque(maxlen=200)
        
        # Tracking configuration
        self.metric_retention_days = 30
        self.snapshot_interval_minutes = 10
        self.alert_thresholds = {
            # API Performance thresholds
            "api_response_time_critical": 1000.0,    # milliseconds
            "api_response_time_warning": 500.0,      # milliseconds
            "api_error_rate_critical": 5.0,          # percentage
            "api_error_rate_warning": 1.0,           # percentage
            "api_throughput_critical": 100.0,        # requests/second
            "api_throughput_warning": 500.0,         # requests/second
            
            # Database thresholds
            "db_query_time_critical": 1000.0,        # milliseconds
            "db_query_time_warning": 500.0,          # milliseconds
            "db_connection_usage_critical": 95.0,    # percentage
            "db_connection_usage_warning": 80.0,     # percentage
            
            # Infrastructure thresholds
            "cpu_usage_critical": 90.0,              # percentage
            "cpu_usage_warning": 75.0,               # percentage
            "memory_usage_critical": 90.0,           # percentage
            "memory_usage_warning": 80.0,            # percentage
            "disk_usage_critical": 90.0,             # percentage
            "disk_usage_warning": 80.0,              # percentage
            
            # Agent productivity thresholds
            "agent_success_rate_critical": 60.0,     # percentage
            "agent_success_rate_warning": 80.0,      # percentage
        }
        
        # Performance targets
        self.performance_targets = {
            # API Performance targets
            "api_response_time": 200.0,              # milliseconds
            "api_throughput": 1000.0,                # requests per second
            "api_error_rate": 0.1,                   # percentage
            "api_uptime": 99.9,                      # percentage
            
            # Database targets
            "db_query_time": 50.0,                   # milliseconds
            "db_connection_pool_usage": 70.0,        # percentage
            "db_cache_hit_rate": 85.0,               # percentage
            "db_slow_queries": 5,                    # count per minute
            
            # Infrastructure targets
            "cpu_usage": 70.0,                       # percentage
            "memory_usage": 80.0,                    # percentage
            "disk_usage": 70.0,                      # percentage
            "network_io": 100.0,                     # MB/s
            
            # System targets
            "active_connections": 500,               # count
            "background_tasks": 10,                  # count
            "cache_memory_usage": 512.0,             # MB
            
            # Agent productivity targets
            "agent_success_rate": 90.0,              # percentage
            "agent_productivity_score": 85.0,        # score
            "apis_per_day": 3.0,                     # APIs deployed
            "optimizations_per_day": 5.0             # optimizations
        }
        
        # Initialize baseline metrics
        self._initialize_baseline_metrics()
        
        logger.info("Backend Metrics Tracker initialized with comprehensive monitoring")

    def _initialize_baseline_metrics(self):
        """Initialize baseline metrics"""
        baseline_metrics = [
            ("api_response_time", MetricCategory.API_PERFORMANCE, 185.0, "milliseconds"),
            ("api_throughput", MetricCategory.API_PERFORMANCE, 850.0, "requests/second"),
            ("api_error_rate", MetricCategory.API_PERFORMANCE, 0.08, "percentage"),
            ("api_uptime", MetricCategory.API_PERFORMANCE, 99.94, "percentage"),
            ("db_query_time", MetricCategory.DATABASE, 42.0, "milliseconds"),
            ("db_cache_hit_rate", MetricCategory.DATABASE, 82.5, "percentage"),
            ("cpu_usage", MetricCategory.INFRASTRUCTURE, 65.0, "percentage"),
            ("memory_usage", MetricCategory.INFRASTRUCTURE, 72.0, "percentage"),
            ("system_reliability", MetricCategory.RELIABILITY, 98.5, "percentage")
        ]
        
        for name, category, value, unit in baseline_metrics:
            target = self.performance_targets.get(name, value * 0.9)  # 10% better target
            
            metric = BackendMetric(
                id=f"baseline_{name}",
                name=name,
                category=category,
                value=value,
                target=target,
                unit=unit,
                metadata={"source": "baseline_initialization"}
            )
            
            self.current_metrics[name] = metric
            self.metric_history[name].append((datetime.utcnow(), value))

    async def capture_system_snapshot(self) -> SystemHealthSnapshot:
        """Capture comprehensive system health snapshot"""
        snapshot = SystemHealthSnapshot()
        
        try:
            # Capture real system metrics where possible using psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # System resource metrics
            snapshot.cpu_usage = cpu_percent
            snapshot.memory_usage = memory.percent
            snapshot.disk_usage = disk.percent
            
            # Network I/O (convert to MB/s - simplified calculation)
            if hasattr(self, '_last_network_bytes'):
                bytes_diff = network.bytes_sent + network.bytes_recv - self._last_network_bytes
                snapshot.network_io = bytes_diff / (1024 * 1024)  # MB
            self._last_network_bytes = network.bytes_sent + network.bytes_recv
            
        except Exception as e:
            logger.warning(f"Could not capture real system metrics: {e}")
            # Fallback to simulated metrics
            snapshot.cpu_usage = 68.5
            snapshot.memory_usage = 74.2
            snapshot.disk_usage = 45.8
            snapshot.network_io = 12.3
        
        # API Performance metrics (simulated - would come from real monitoring)
        snapshot.api_response_time = 185.0
        snapshot.api_throughput = 850.0
        snapshot.api_error_rate = 0.08
        snapshot.api_uptime = 99.94
        
        # Database metrics (simulated)
        snapshot.db_query_time = 42.0
        snapshot.db_connection_pool_usage = 68.0
        snapshot.db_cache_hit_rate = 82.5
        snapshot.db_slow_queries = 3
        
        # System activity metrics (simulated)
        snapshot.active_connections = 245
        snapshot.queue_depth = 12
        snapshot.background_tasks = 8
        snapshot.cache_memory_usage = 384.0
        
        # Security metrics (simulated)
        snapshot.failed_auth_attempts = 2
        snapshot.blocked_ips = 0
        snapshot.security_violations = 0
        snapshot.ssl_certificate_validity = 45.0  # days
        
        self.system_snapshots.append(snapshot)
        
        # Update current metrics from snapshot
        await self._update_metrics_from_snapshot(snapshot)
        
        # Check for alerts
        await self._check_system_alerts(snapshot)
        
        logger.debug(f"Captured system snapshot: CPU={snapshot.cpu_usage}%, API={snapshot.api_response_time}ms")
        
        return snapshot

    async def _update_metrics_from_snapshot(self, snapshot: SystemHealthSnapshot):
        """Update metrics from system snapshot"""
        updates = [
            ("api_response_time", MetricCategory.API_PERFORMANCE, snapshot.api_response_time, "milliseconds"),
            ("api_throughput", MetricCategory.API_PERFORMANCE, snapshot.api_throughput, "requests/second"),
            ("api_error_rate", MetricCategory.API_PERFORMANCE, snapshot.api_error_rate, "percentage"),
            ("db_query_time", MetricCategory.DATABASE, snapshot.db_query_time, "milliseconds"),
            ("db_cache_hit_rate", MetricCategory.DATABASE, snapshot.db_cache_hit_rate, "percentage"),
            ("cpu_usage", MetricCategory.INFRASTRUCTURE, snapshot.cpu_usage, "percentage"),
            ("memory_usage", MetricCategory.INFRASTRUCTURE, snapshot.memory_usage, "percentage"),
            ("disk_usage", MetricCategory.INFRASTRUCTURE, snapshot.disk_usage, "percentage")
        ]
        
        for name, category, value, unit in updates:
            await self.record_metric(name, category, value, unit)

    async def record_metric(self, name: str, category: MetricCategory, value: float,
                          unit: str, metadata: Dict[str, Any] = None) -> BackendMetric:
        """Record a new metric data point"""
        target = self.performance_targets.get(name, value * 0.9)
        
        metric = BackendMetric(
            id=f"{name}_{int(datetime.utcnow().timestamp())}",
            name=name,
            category=category,
            value=value,
            target=target,
            unit=unit,
            metadata=metadata or {}
        )
        
        # Update current metrics
        self.current_metrics[name] = metric
        
        # Add to history
        self.metric_history[name].append((datetime.utcnow(), value))
        
        # Trim history if needed
        if len(self.metric_history[name]) > 1000:
            self.metric_history[name].popleft()
        
        # Check for alerts
        await self._check_metric_alert(metric)
        
        return metric

    async def track_agent_productivity(self, agent_id: str, agent_name: str,
                                     productivity_data: Dict[str, Any]) -> AgentProductivityMetrics:
        """Track backend agent productivity metrics"""
        period_start = productivity_data.get("period_start", datetime.utcnow() - timedelta(hours=1))
        period_end = productivity_data.get("period_end", datetime.utcnow())
        
        metrics = AgentProductivityMetrics(
            agent_id=agent_id,
            agent_name=agent_name,
            period_start=period_start,
            period_end=period_end,
            tasks_completed=productivity_data.get("tasks_completed", 0),
            tasks_failed=productivity_data.get("tasks_failed", 0),
            average_task_time=productivity_data.get("average_task_time", 0.0),
            quality_score=productivity_data.get("quality_score", 0.0),
            apis_deployed=productivity_data.get("apis_deployed", 0),
            apis_optimized=productivity_data.get("apis_optimized", 0),
            database_optimizations=productivity_data.get("database_optimizations", 0),
            infrastructure_improvements=productivity_data.get("infrastructure_improvements", 0),
            performance_impact=productivity_data.get("performance_impact", 0.0),
            reliability_impact=productivity_data.get("reliability_impact", 0.0),
            security_improvements=productivity_data.get("security_improvements", 0)
        )
        
        self.agent_productivity[agent_id] = metrics
        self.productivity_history.append(metrics)
        
        # Record agent productivity metrics
        await self.record_metric(
            f"agent_success_rate_{agent_id}",
            MetricCategory.AGENT_PRODUCTIVITY,
            metrics.success_rate,
            "percentage",
            {"agent_name": agent_name}
        )
        
        await self.record_metric(
            f"agent_productivity_score_{agent_id}",
            MetricCategory.AGENT_PRODUCTIVITY,
            metrics.productivity_score,
            "score",
            {"agent_name": agent_name}
        )
        
        logger.info(f"Tracked productivity for {agent_name}: {metrics.productivity_score:.1f} score, {metrics.success_rate:.1f}% success rate")
        
        return metrics

    async def _check_system_alerts(self, snapshot: SystemHealthSnapshot):
        """Check system snapshot for alerts"""
        checks = [
            ("api_response_time", snapshot.api_response_time, "milliseconds"),
            ("api_error_rate", snapshot.api_error_rate, "percentage"),
            ("cpu_usage", snapshot.cpu_usage, "percentage"),
            ("memory_usage", snapshot.memory_usage, "percentage"),
            ("db_query_time", snapshot.db_query_time, "milliseconds")
        ]
        
        for metric_name, value, unit in checks:
            await self._check_threshold_alerts(metric_name, value, unit)

    async def _check_metric_alert(self, metric: BackendMetric):
        """Check individual metric for alerts"""
        await self._check_threshold_alerts(metric.name, metric.value, metric.unit)

    async def _check_threshold_alerts(self, metric_name: str, value: float, unit: str):
        """Check metric against alert thresholds"""
        critical_threshold = self.alert_thresholds.get(f"{metric_name}_critical")
        warning_threshold = self.alert_thresholds.get(f"{metric_name}_warning")
        
        if critical_threshold is not None:
            # For metrics where higher values indicate problems
            if metric_name in ["api_response_time", "api_error_rate", "cpu_usage", "memory_usage", "db_query_time"]:
                if value > critical_threshold:
                    await self._create_alert(
                        metric_name=metric_name,
                        severity=MetricSeverity.CRITICAL,
                        current_value=value,
                        threshold=critical_threshold,
                        unit=unit
                    )
            # For metrics where lower values indicate problems
            elif metric_name in ["api_throughput", "db_cache_hit_rate"]:
                if value < critical_threshold:
                    await self._create_alert(
                        metric_name=metric_name,
                        severity=MetricSeverity.CRITICAL,
                        current_value=value,
                        threshold=critical_threshold,
                        unit=unit
                    )
        
        if warning_threshold is not None:
            # Similar logic for warning thresholds
            if metric_name in ["api_response_time", "api_error_rate", "cpu_usage", "memory_usage", "db_query_time"]:
                if value > warning_threshold and (critical_threshold is None or value <= critical_threshold):
                    await self._create_alert(
                        metric_name=metric_name,
                        severity=MetricSeverity.WARNING,
                        current_value=value,
                        threshold=warning_threshold,
                        unit=unit
                    )
            elif metric_name in ["api_throughput", "db_cache_hit_rate"]:
                if value < warning_threshold and (critical_threshold is None or value >= critical_threshold):
                    await self._create_alert(
                        metric_name=metric_name,
                        severity=MetricSeverity.WARNING,
                        current_value=value,
                        threshold=warning_threshold,
                        unit=unit
                    )

    async def _create_alert(self, metric_name: str, severity: MetricSeverity, current_value: float,
                          threshold: float, unit: str):
        """Create a metric alert"""
        alert_id = f"{metric_name}_{severity.value}_{int(datetime.utcnow().timestamp())}"
        
        if alert_id in self.active_alerts:
            return  # Alert already exists
        
        deviation = abs((current_value - threshold) / threshold) * 100
        
        alert = MetricAlert(
            id=alert_id,
            metric_name=metric_name,
            severity=severity,
            message=f"{metric_name} is {severity.value}: {current_value} {unit} (threshold: {threshold} {unit})",
            current_value=current_value,
            target_value=threshold,
            deviation_percentage=deviation
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Backend metrics alert: {alert.message}")

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_timestamp = datetime.utcnow()
            
            del self.active_alerts[alert_id]
            
            logger.info(f"Resolved alert: {alert.message}")
            return True
        
        return False

    def calculate_metric_trends(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Calculate metric trends over specified period"""
        if metric_name not in self.metric_history:
            return {"error": f"Metric {metric_name} not found"}
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_data = [
            (timestamp, value) for timestamp, value in self.metric_history[metric_name]
            if timestamp >= cutoff
        ]
        
        if len(recent_data) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        values = [value for _, value in recent_data]
        
        # Calculate trend statistics
        trend_data = {
            "metric_name": metric_name,
            "period_days": days,
            "data_points": len(values),
            "current_value": values[-1],
            "average_value": statistics.mean(values),
            "median_value": statistics.median(values),
            "min_value": min(values),
            "max_value": max(values),
            "standard_deviation": statistics.stdev(values) if len(values) > 1 else 0,
            "trend_direction": "improving" if values[-1] < values[0] else "declining" if "time" in metric_name or "error" in metric_name else "improving" if values[-1] > values[0] else "stable",
            "percentage_change": ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
        }
        
        return trend_data

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        current_time = datetime.utcnow()
        
        # Get latest system snapshot
        latest_snapshot = self.system_snapshots[-1] if self.system_snapshots else None
        
        # Calculate agent productivity summary
        agent_productivity_summary = {}
        for agent_id, productivity in self.agent_productivity.items():
            agent_productivity_summary[agent_id] = {
                "productivity_score": productivity.productivity_score,
                "success_rate": productivity.success_rate,
                "tasks_completed": productivity.tasks_completed,
                "apis_deployed": productivity.apis_deployed,
                "infrastructure_improvements": productivity.infrastructure_improvements
            }
        
        # Calculate overall system health score
        health_factors = []
        for metric in self.current_metrics.values():
            if metric.is_on_target:
                health_factors.append(1.0)
            else:
                health_factors.append(max(0.0, 1.0 - abs(1.0 - metric.performance_ratio)))
        
        system_health_score = (sum(health_factors) / len(health_factors)) * 100 if health_factors else 0
        
        return {
            "timestamp": current_time.isoformat(),
            "system_health_score": system_health_score,
            "system_snapshot": latest_snapshot.__dict__ if latest_snapshot else None,
            "performance_summary": {
                "metrics_on_target": len([m for m in self.current_metrics.values() if m.is_on_target]),
                "total_metrics": len(self.current_metrics),
                "target_achievement_rate": (len([m for m in self.current_metrics.values() if m.is_on_target]) / max(1, len(self.current_metrics))) * 100
            },
            "agent_productivity": agent_productivity_summary,
            "alerts": {
                "active_alerts": len(self.active_alerts),
                "critical_alerts": len([a for a in self.active_alerts.values() if a.severity == MetricSeverity.CRITICAL]),
                "warning_alerts": len([a for a in self.active_alerts.values() if a.severity == MetricSeverity.WARNING]),
                "recent_alerts": [
                    {
                        "id": alert.id,
                        "metric": alert.metric_name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in list(self.active_alerts.values())[-5:]
                ]
            },
            "current_metrics": {
                name: {
                    "value": metric.value,
                    "target": metric.target,
                    "unit": metric.unit,
                    "on_target": metric.is_on_target,
                    "performance_ratio": metric.performance_ratio
                }
                for name, metric in self.current_metrics.items()
            },
            "performance_targets": self.performance_targets
        }

    def get_metric_details(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific metric"""
        if metric_name not in self.current_metrics:
            return None
        
        metric = self.current_metrics[metric_name]
        trend_data = self.calculate_metric_trends(metric_name, 7)
        
        return {
            "metric": {
                "name": metric.name,
                "category": metric.category.value,
                "current_value": metric.value,
                "target": metric.target,
                "unit": metric.unit,
                "performance_ratio": metric.performance_ratio,
                "on_target": metric.is_on_target,
                "last_updated": metric.timestamp.isoformat()
            },
            "trend_analysis": trend_data,
            "history_points": len(self.metric_history[metric_name]),
            "related_alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved
                }
                for alert in self.active_alerts.values()
                if alert.metric_name == metric_name
            ]
        }

    async def start_monitoring_loop(self, interval_minutes: int = 10):
        """Start continuous monitoring loop"""
        logger.info(f"Starting backend metrics monitoring loop (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                await self.capture_system_snapshot()
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in metrics monitoring loop: {e}")
                await asyncio.sleep(interval_minutes * 60)

# Global backend metrics tracker instance
backend_metrics_tracker = BackendMetricsTracker()