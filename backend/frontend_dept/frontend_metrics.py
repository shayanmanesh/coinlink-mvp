"""
Frontend Metrics Tracker - Performance & KPI Monitoring

Ultra-comprehensive metrics tracking system for frontend department.
Monitors UI/UX performance, agent productivity, user experience metrics,
and business impact of frontend optimizations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import statistics

logger = logging.getLogger(__name__)

class MetricCategory(Enum):
    """Categories of frontend metrics"""
    PERFORMANCE = "performance"
    USER_EXPERIENCE = "user_experience"
    ACCESSIBILITY = "accessibility"
    BUSINESS_IMPACT = "business_impact"
    AGENT_PRODUCTIVITY = "agent_productivity"
    TECHNICAL_QUALITY = "technical_quality"

class MetricSeverity(Enum):
    """Metric alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class FrontendMetric:
    """Individual frontend metric data point"""
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
        # For metrics where higher is better
        if self.name in ["conversion_rate", "user_satisfaction", "accessibility_score", "lighthouse_score"]:
            return self.value >= self.target
        # For metrics where lower is better  
        elif self.name in ["page_load_time", "bundle_size", "error_rate", "bounce_rate"]:
            return self.value <= self.target
        else:
            return abs(self.performance_ratio - 1.0) <= 0.1  # Within 10%

@dataclass
class AgentProductivityMetrics:
    """Agent productivity tracking"""
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
    components_created: int = 0
    components_optimized: int = 0
    performance_improvements: int = 0
    ux_enhancements: int = 0
    
    # Impact metrics
    user_satisfaction_impact: float = 0.0
    performance_impact: float = 0.0
    conversion_impact: float = 0.0
    
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
            min(1.0, self.components_created / 10),  # Normalize to 10 components
            min(1.0, self.performance_improvements / 5)  # Normalize to 5 improvements
        ]
        return (sum(factors) / len(factors)) * 100

@dataclass
class UIPerformanceSnapshot:
    """UI performance snapshot"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Core Web Vitals
    largest_contentful_paint: float = 0.0  # seconds
    first_input_delay: float = 0.0         # milliseconds
    cumulative_layout_shift: float = 0.0   # score
    first_contentful_paint: float = 0.0    # seconds
    
    # Lighthouse Scores
    lighthouse_performance: float = 0.0     # 0-100
    lighthouse_accessibility: float = 0.0   # 0-100
    lighthouse_best_practices: float = 0.0  # 0-100
    lighthouse_seo: float = 0.0             # 0-100
    
    # Bundle Analysis
    bundle_size_total: float = 0.0          # MB
    bundle_size_main: float = 0.0           # MB
    bundle_size_vendor: float = 0.0         # MB
    tree_shaking_efficiency: float = 0.0    # percentage
    
    # User Experience
    time_to_interactive: float = 0.0        # seconds
    bounce_rate: float = 0.0                # percentage
    session_duration: float = 0.0           # seconds
    page_views_per_session: float = 0.0
    
    # Business Metrics
    conversion_rate: float = 0.0            # percentage
    cart_abandonment_rate: float = 0.0      # percentage
    user_retention_rate: float = 0.0        # percentage

@dataclass
class MetricAlert:
    """Metric performance alert"""
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

class FrontendMetricsTracker:
    """Comprehensive frontend metrics tracking system"""
    
    def __init__(self):
        self.tracker_id = "frontend_metrics_tracker"
        
        # Metrics storage
        self.current_metrics: Dict[str, FrontendMetric] = {}
        self.metric_history: defaultdict = defaultdict(deque)  # metric_name -> deque of values
        self.performance_snapshots: deque = deque(maxlen=100)
        
        # Agent productivity tracking
        self.agent_productivity: Dict[str, AgentProductivityMetrics] = {}
        self.productivity_history: deque = deque(maxlen=50)
        
        # Alerting system
        self.active_alerts: Dict[str, MetricAlert] = {}
        self.alert_history: deque = deque(maxlen=200)
        
        # Tracking configuration
        self.metric_retention_days = 30
        self.snapshot_interval_minutes = 15
        self.alert_thresholds = {
            # Performance thresholds
            "page_load_time_critical": 5.0,      # seconds
            "page_load_time_warning": 3.0,       # seconds
            "bundle_size_critical": 5.0,         # MB
            "bundle_size_warning": 3.0,          # MB
            "lighthouse_performance_critical": 50.0,
            "lighthouse_performance_warning": 70.0,
            
            # UX thresholds
            "bounce_rate_critical": 70.0,        # percentage
            "bounce_rate_warning": 50.0,         # percentage
            "conversion_rate_critical": 1.0,     # percentage
            "conversion_rate_warning": 2.0,      # percentage
            
            # Agent productivity thresholds
            "agent_success_rate_critical": 60.0,  # percentage
            "agent_success_rate_warning": 80.0,   # percentage
            "agent_productivity_critical": 50.0,  # score
            "agent_productivity_warning": 70.0    # score
        }
        
        # Performance targets
        self.performance_targets = {
            # Core Web Vitals targets
            "largest_contentful_paint": 2.5,     # seconds
            "first_input_delay": 100,            # milliseconds
            "cumulative_layout_shift": 0.1,      # score
            "first_contentful_paint": 1.8,       # seconds
            
            # Lighthouse targets
            "lighthouse_performance": 90.0,      # score
            "lighthouse_accessibility": 95.0,     # score
            "lighthouse_best_practices": 90.0,    # score
            "lighthouse_seo": 85.0,              # score
            
            # Bundle targets
            "bundle_size_total": 2.0,            # MB
            "bundle_size_main": 1.0,             # MB
            "tree_shaking_efficiency": 95.0,     # percentage
            
            # UX targets
            "bounce_rate": 30.0,                 # percentage
            "session_duration": 300.0,           # seconds (5 minutes)
            "page_views_per_session": 3.0,
            
            # Business targets
            "conversion_rate": 5.0,              # percentage
            "user_retention_rate": 85.0,         # percentage
            
            # Agent productivity targets
            "agent_success_rate": 90.0,          # percentage
            "agent_productivity_score": 85.0,    # score
            "components_per_hour": 8.0,          # components
            "optimizations_per_hour": 5.0        # optimizations
        }
        
        # Initialize baseline metrics
        self._initialize_baseline_metrics()
        
        logger.info("Frontend Metrics Tracker initialized with comprehensive monitoring")

    def _initialize_baseline_metrics(self):
        """Initialize baseline metrics"""
        baseline_metrics = [
            ("page_load_time", MetricCategory.PERFORMANCE, 2.1, "seconds"),
            ("bundle_size_total", MetricCategory.PERFORMANCE, 2.8, "MB"),
            ("lighthouse_performance", MetricCategory.PERFORMANCE, 87.0, "score"),
            ("lighthouse_accessibility", MetricCategory.ACCESSIBILITY, 93.0, "score"),
            ("bounce_rate", MetricCategory.USER_EXPERIENCE, 35.0, "percentage"),
            ("conversion_rate", MetricCategory.BUSINESS_IMPACT, 4.2, "percentage"),
            ("user_satisfaction", MetricCategory.USER_EXPERIENCE, 8.5, "score"),
            ("component_reusability", MetricCategory.TECHNICAL_QUALITY, 78.0, "percentage"),
            ("code_maintainability", MetricCategory.TECHNICAL_QUALITY, 82.0, "score")
        ]
        
        for name, category, value, unit in baseline_metrics:
            target = self.performance_targets.get(name, value * 1.1)
            
            metric = FrontendMetric(
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

    async def capture_performance_snapshot(self) -> UIPerformanceSnapshot:
        """Capture comprehensive UI performance snapshot"""
        snapshot = UIPerformanceSnapshot()
        
        # Simulate performance data capture
        # In production, this would integrate with real monitoring tools
        snapshot.largest_contentful_paint = 2.1
        snapshot.first_input_delay = 85.0
        snapshot.cumulative_layout_shift = 0.08
        snapshot.first_contentful_paint = 1.4
        
        # Lighthouse scores
        snapshot.lighthouse_performance = 87.5
        snapshot.lighthouse_accessibility = 94.2
        snapshot.lighthouse_best_practices = 89.8
        snapshot.lighthouse_seo = 91.3
        
        # Bundle analysis
        snapshot.bundle_size_total = 2.3
        snapshot.bundle_size_main = 1.1
        snapshot.bundle_size_vendor = 1.2
        snapshot.tree_shaking_efficiency = 89.5
        
        # UX metrics
        snapshot.time_to_interactive = 3.2
        snapshot.bounce_rate = 32.8
        snapshot.session_duration = 285.0
        snapshot.page_views_per_session = 3.4
        
        # Business metrics
        snapshot.conversion_rate = 4.6
        snapshot.cart_abandonment_rate = 68.2
        snapshot.user_retention_rate = 76.8
        
        self.performance_snapshots.append(snapshot)
        
        # Update current metrics from snapshot
        await self._update_metrics_from_snapshot(snapshot)
        
        # Check for alerts
        await self._check_performance_alerts(snapshot)
        
        logger.debug(f"Captured performance snapshot: LCP={snapshot.largest_contentful_paint}s, Performance={snapshot.lighthouse_performance}")
        
        return snapshot

    async def _update_metrics_from_snapshot(self, snapshot: UIPerformanceSnapshot):
        """Update metrics from performance snapshot"""
        updates = [
            ("largest_contentful_paint", MetricCategory.PERFORMANCE, snapshot.largest_contentful_paint, "seconds"),
            ("first_input_delay", MetricCategory.PERFORMANCE, snapshot.first_input_delay, "milliseconds"),
            ("cumulative_layout_shift", MetricCategory.PERFORMANCE, snapshot.cumulative_layout_shift, "score"),
            ("lighthouse_performance", MetricCategory.PERFORMANCE, snapshot.lighthouse_performance, "score"),
            ("lighthouse_accessibility", MetricCategory.ACCESSIBILITY, snapshot.lighthouse_accessibility, "score"),
            ("bundle_size_total", MetricCategory.PERFORMANCE, snapshot.bundle_size_total, "MB"),
            ("bounce_rate", MetricCategory.USER_EXPERIENCE, snapshot.bounce_rate, "percentage"),
            ("conversion_rate", MetricCategory.BUSINESS_IMPACT, snapshot.conversion_rate, "percentage")
        ]
        
        for name, category, value, unit in updates:
            await self.record_metric(name, category, value, unit)

    async def record_metric(self, name: str, category: MetricCategory, value: float, 
                          unit: str, metadata: Dict[str, Any] = None) -> FrontendMetric:
        """Record a new metric data point"""
        target = self.performance_targets.get(name, value * 1.1)
        
        metric = FrontendMetric(
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
        """Track agent productivity metrics"""
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
            components_created=productivity_data.get("components_created", 0),
            components_optimized=productivity_data.get("components_optimized", 0),
            performance_improvements=productivity_data.get("performance_improvements", 0),
            ux_enhancements=productivity_data.get("ux_enhancements", 0),
            user_satisfaction_impact=productivity_data.get("user_satisfaction_impact", 0.0),
            performance_impact=productivity_data.get("performance_impact", 0.0),
            conversion_impact=productivity_data.get("conversion_impact", 0.0)
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

    async def _check_performance_alerts(self, snapshot: UIPerformanceSnapshot):
        """Check performance snapshot for alerts"""
        checks = [
            ("page_load_time", snapshot.largest_contentful_paint, "seconds"),
            ("lighthouse_performance", snapshot.lighthouse_performance, "score"),
            ("bounce_rate", snapshot.bounce_rate, "percentage"),
            ("conversion_rate", snapshot.conversion_rate, "percentage")
        ]
        
        for metric_name, value, unit in checks:
            await self._check_threshold_alerts(metric_name, value, unit)

    async def _check_metric_alert(self, metric: FrontendMetric):
        """Check individual metric for alerts"""
        await self._check_threshold_alerts(metric.name, metric.value, metric.unit)

    async def _check_threshold_alerts(self, metric_name: str, value: float, unit: str):
        """Check metric against alert thresholds"""
        critical_threshold = self.alert_thresholds.get(f"{metric_name}_critical")
        warning_threshold = self.alert_thresholds.get(f"{metric_name}_warning")
        
        if critical_threshold is not None:
            if (metric_name in ["bounce_rate", "page_load_time", "bundle_size_total"] and value > critical_threshold) or \
               (metric_name in ["lighthouse_performance", "conversion_rate"] and value < critical_threshold):
                
                await self._create_alert(
                    metric_name=metric_name,
                    severity=MetricSeverity.CRITICAL,
                    current_value=value,
                    threshold=critical_threshold,
                    unit=unit
                )
        
        elif warning_threshold is not None:
            if (metric_name in ["bounce_rate", "page_load_time", "bundle_size_total"] and value > warning_threshold) or \
               (metric_name in ["lighthouse_performance", "conversion_rate"] and value < warning_threshold):
                
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
        
        logger.warning(f"Frontend metrics alert: {alert.message}")

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
            "trend_direction": "improving" if values[-1] > values[0] else "declining",
            "percentage_change": ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
        }
        
        return trend_data

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        current_time = datetime.utcnow()
        
        # Get latest performance snapshot
        latest_snapshot = self.performance_snapshots[-1] if self.performance_snapshots else None
        
        # Calculate agent productivity summary
        agent_productivity_summary = {}
        for agent_id, productivity in self.agent_productivity.items():
            agent_productivity_summary[agent_id] = {
                "productivity_score": productivity.productivity_score,
                "success_rate": productivity.success_rate,
                "tasks_completed": productivity.tasks_completed,
                "quality_score": productivity.quality_score
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
            "performance_summary": {
                "latest_snapshot": latest_snapshot.__dict__ if latest_snapshot else None,
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
                alert for alert in self.active_alerts.values() 
                if alert.metric_name == metric_name
            ]
        }

    async def start_monitoring_loop(self, interval_minutes: int = 15):
        """Start continuous monitoring loop"""
        logger.info(f"Starting frontend metrics monitoring loop (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                await self.capture_performance_snapshot()
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in metrics monitoring loop: {e}")
                await asyncio.sleep(interval_minutes * 60)

# Global frontend metrics tracker instance
frontend_metrics_tracker = FrontendMetricsTracker()