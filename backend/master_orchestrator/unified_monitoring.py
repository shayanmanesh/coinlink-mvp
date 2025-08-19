"""
Unified Monitoring Dashboard - System-Wide Observability Platform

Real-time monitoring and visualization system that provides comprehensive
insights into all departments, agents, KPIs, and system performance with
intelligent alerting and predictive analytics.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics to monitor"""
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    EFFICIENCY = "efficiency"
    PRODUCTIVITY = "productivity"
    REVENUE = "revenue"
    USER_EXPERIENCE = "user_experience"
    SYSTEM_HEALTH = "system_health"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class MonitoringMetric:
    """Individual monitoring metric"""
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    department: Optional[str] = None
    agent: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemAlert:
    """System alert/notification"""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    metric_id: Optional[str] = None
    department: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    actions_taken: List[str] = field(default_factory=list)

@dataclass
class DashboardPanel:
    """Dashboard visualization panel"""
    panel_id: str
    title: str
    panel_type: str  # chart, gauge, table, heatmap, etc.
    metrics: List[str]  # Metric IDs to display
    refresh_interval: int = 30  # seconds
    position: Dict[str, int] = field(default_factory=dict)  # x, y, width, height
    configuration: Dict[str, Any] = field(default_factory=dict)

class UnifiedMonitoringDashboard:
    """Comprehensive system monitoring dashboard"""
    
    def __init__(self):
        self.dashboard_id = "unified_monitoring"
        
        # Metrics storage
        self.current_metrics: Dict[str, MonitoringMetric] = {}
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metrics_aggregates: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Alerts
        self.active_alerts: Dict[str, SystemAlert] = {}
        self.alert_history: deque = deque(maxlen=500)
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
        # Dashboard configuration
        self.dashboard_panels: Dict[str, DashboardPanel] = {}
        self.dashboard_layouts: Dict[str, List[str]] = {  # layout_name -> panel_ids
            "executive": [],
            "operations": [],
            "technical": [],
            "growth": []
        }
        
        # Real-time tracking
        self.real_time_streams: Dict[str, Any] = {}
        self.websocket_connections: Set[str] = set()
        
        # Analytics
        self.trend_analysis: Dict[str, Dict[str, float]] = {}
        self.anomaly_detection: Dict[str, Any] = {}
        self.predictions: Dict[str, Any] = {}
        
        # Configuration
        self.alert_thresholds = self._initialize_alert_thresholds()
        self.aggregation_windows = [60, 300, 900, 3600, 86400]  # 1m, 5m, 15m, 1h, 1d
        
        # Initialize dashboard panels
        self._initialize_dashboard_panels()
        
        logger.info("Unified Monitoring Dashboard initialized")

    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize alert threshold configurations"""
        
        return {
            "system_response_time": {
                "warning": 500,
                "error": 1000,
                "critical": 2000
            },
            "error_rate": {
                "warning": 1.0,
                "error": 5.0,
                "critical": 10.0
            },
            "cpu_usage": {
                "warning": 70,
                "error": 85,
                "critical": 95
            },
            "memory_usage": {
                "warning": 75,
                "error": 85,
                "critical": 95
            },
            "revenue_daily": {
                "warning": 100000,  # Below $100k/day
                "error": 50000,     # Below $50k/day
                "critical": 10000    # Below $10k/day
            },
            "agent_productivity": {
                "warning": 80,
                "error": 60,
                "critical": 40
            }
        }

    def _initialize_dashboard_panels(self):
        """Initialize default dashboard panels"""
        
        # System Health Panel
        self.dashboard_panels["system_health"] = DashboardPanel(
            panel_id="system_health",
            title="System Health Overview",
            panel_type="multi_gauge",
            metrics=["cpu_usage", "memory_usage", "disk_usage", "network_usage"],
            position={"x": 0, "y": 0, "width": 4, "height": 2}
        )
        
        # Department Status Panel
        self.dashboard_panels["department_status"] = DashboardPanel(
            panel_id="department_status",
            title="Department Status",
            panel_type="table",
            metrics=["frontend_health", "backend_health", "rnd_health", "growth_health"],
            position={"x": 4, "y": 0, "width": 4, "height": 2}
        )
        
        # Revenue Tracker Panel
        self.dashboard_panels["revenue_tracker"] = DashboardPanel(
            panel_id="revenue_tracker",
            title="Revenue Performance",
            panel_type="line_chart",
            metrics=["revenue_hourly", "revenue_daily", "revenue_weekly"],
            refresh_interval=60,
            position={"x": 8, "y": 0, "width": 4, "height": 2}
        )
        
        # KPI Dashboard Panel
        self.dashboard_panels["kpi_dashboard"] = DashboardPanel(
            panel_id="kpi_dashboard",
            title="KPI Achievement",
            panel_type="progress_bars",
            metrics=["kpi_response_time", "kpi_availability", "kpi_conversion", "kpi_revenue"],
            position={"x": 0, "y": 2, "width": 6, "height": 2}
        )
        
        # Agent Activity Panel
        self.dashboard_panels["agent_activity"] = DashboardPanel(
            panel_id="agent_activity",
            title="Agent Activity Matrix",
            panel_type="heatmap",
            metrics=["agent_frontend_activity", "agent_backend_activity", "agent_growth_activity"],
            position={"x": 6, "y": 2, "width": 6, "height": 2}
        )
        
        # Alerts Panel
        self.dashboard_panels["alerts"] = DashboardPanel(
            panel_id="alerts",
            title="Active Alerts",
            panel_type="alert_list",
            metrics=[],  # Dynamic based on active alerts
            refresh_interval=10,
            position={"x": 0, "y": 4, "width": 12, "height": 1}
        )
        
        # Assign panels to layouts
        self.dashboard_layouts["executive"] = ["revenue_tracker", "kpi_dashboard", "department_status"]
        self.dashboard_layouts["operations"] = ["system_health", "department_status", "agent_activity", "alerts"]
        self.dashboard_layouts["technical"] = ["system_health", "agent_activity", "alerts"]
        self.dashboard_layouts["growth"] = ["revenue_tracker", "kpi_dashboard", "alerts"]

    async def record_metric(self, metric: MonitoringMetric) -> None:
        """Record a monitoring metric"""
        
        # Store current value
        self.current_metrics[metric.metric_id] = metric
        
        # Add to history
        self.metrics_history[metric.metric_id].append({
            "timestamp": metric.timestamp,
            "value": metric.value
        })
        
        # Check for alerts
        await self._check_metric_alerts(metric)
        
        # Update aggregates
        await self._update_aggregates(metric)
        
        # Stream to real-time subscribers
        await self._stream_metric(metric)
        
        # Detect anomalies
        if await self._detect_anomaly(metric):
            await self._create_anomaly_alert(metric)

    async def _check_metric_alerts(self, metric: MonitoringMetric) -> None:
        """Check if metric triggers any alerts"""
        
        if metric.name in self.alert_thresholds:
            thresholds = self.alert_thresholds[metric.name]
            
            severity = None
            threshold_value = None
            
            # Determine severity based on thresholds
            if "critical" in thresholds:
                if metric.name in ["revenue_daily"]:
                    # For metrics where lower is worse
                    if metric.value < thresholds["critical"]:
                        severity = AlertSeverity.CRITICAL
                        threshold_value = thresholds["critical"]
                else:
                    # For metrics where higher is worse
                    if metric.value > thresholds["critical"]:
                        severity = AlertSeverity.CRITICAL
                        threshold_value = thresholds["critical"]
            
            if not severity and "error" in thresholds:
                if metric.name in ["revenue_daily"]:
                    if metric.value < thresholds["error"]:
                        severity = AlertSeverity.ERROR
                        threshold_value = thresholds["error"]
                else:
                    if metric.value > thresholds["error"]:
                        severity = AlertSeverity.ERROR
                        threshold_value = thresholds["error"]
            
            if not severity and "warning" in thresholds:
                if metric.name in ["revenue_daily"]:
                    if metric.value < thresholds["warning"]:
                        severity = AlertSeverity.WARNING
                        threshold_value = thresholds["warning"]
                else:
                    if metric.value > thresholds["warning"]:
                        severity = AlertSeverity.WARNING
                        threshold_value = thresholds["warning"]
            
            if severity:
                await self._create_alert(
                    severity=severity,
                    title=f"{metric.name} Threshold Exceeded",
                    message=f"{metric.name} is {metric.value} {metric.unit} (threshold: {threshold_value})",
                    metric_id=metric.metric_id,
                    department=metric.department
                )

    async def _create_alert(self, severity: AlertSeverity, title: str, message: str,
                           metric_id: Optional[str] = None, department: Optional[str] = None) -> SystemAlert:
        """Create a system alert"""
        
        alert = SystemAlert(
            alert_id=f"alert_{datetime.utcnow().timestamp()}",
            severity=severity,
            title=title,
            message=message,
            metric_id=metric_id,
            department=department
        )
        
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Alert created: [{severity.value}] {title} - {message}")
        
        # Trigger automatic remediation for critical alerts
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            await self._trigger_auto_remediation(alert)
        
        return alert

    async def _trigger_auto_remediation(self, alert: SystemAlert) -> None:
        """Trigger automatic remediation for critical alerts"""
        
        remediation_actions = []
        
        if "response_time" in alert.title:
            remediation_actions.append("Scale up backend infrastructure")
            remediation_actions.append("Optimize database queries")
            remediation_actions.append("Clear cache and restart services")
        
        elif "revenue" in alert.title:
            remediation_actions.append("Activate all growth agents")
            remediation_actions.append("Launch emergency marketing campaigns")
            remediation_actions.append("Intensify BD outreach by 200%")
        
        elif "cpu" in alert.title or "memory" in alert.title:
            remediation_actions.append("Trigger auto-scaling")
            remediation_actions.append("Restart non-essential services")
            remediation_actions.append("Activate resource optimization")
        
        alert.actions_taken = remediation_actions
        
        logger.info(f"Auto-remediation triggered for {alert.alert_id}: {remediation_actions}")

    async def _update_aggregates(self, metric: MonitoringMetric) -> None:
        """Update metric aggregates for different time windows"""
        
        for window in self.aggregation_windows:
            window_key = f"{metric.metric_id}_{window}"
            
            # Get recent values within window
            cutoff = datetime.utcnow() - timedelta(seconds=window)
            recent_values = [
                entry["value"] for entry in self.metrics_history[metric.metric_id]
                if entry["timestamp"] >= cutoff
            ]
            
            if recent_values:
                self.metrics_aggregates[window_key] = {
                    "min": min(recent_values),
                    "max": max(recent_values),
                    "avg": statistics.mean(recent_values),
                    "median": statistics.median(recent_values),
                    "stddev": statistics.stdev(recent_values) if len(recent_values) > 1 else 0,
                    "count": len(recent_values)
                }

    async def _stream_metric(self, metric: MonitoringMetric) -> None:
        """Stream metric to real-time subscribers"""
        
        # Format for streaming
        stream_data = {
            "metric_id": metric.metric_id,
            "name": metric.name,
            "value": metric.value,
            "unit": metric.unit,
            "timestamp": metric.timestamp.isoformat(),
            "department": metric.department,
            "agent": metric.agent
        }
        
        # Add to real-time stream
        stream_key = f"stream_{metric.metric_type.value}"
        if stream_key not in self.real_time_streams:
            self.real_time_streams[stream_key] = deque(maxlen=100)
        
        self.real_time_streams[stream_key].append(stream_data)

    async def _detect_anomaly(self, metric: MonitoringMetric) -> bool:
        """Detect anomalies in metric values"""
        
        history = self.metrics_history.get(metric.metric_id, [])
        
        if len(history) < 20:
            return False  # Not enough data for anomaly detection
        
        recent_values = [entry["value"] for entry in list(history)[-20:]]
        
        # Simple statistical anomaly detection
        mean = statistics.mean(recent_values)
        stddev = statistics.stdev(recent_values)
        
        # Check if current value is outside 3 standard deviations
        if abs(metric.value - mean) > 3 * stddev:
            return True
        
        # Check for sudden changes
        if len(recent_values) >= 2:
            recent_change = abs(metric.value - recent_values[-2])
            typical_change = stddev
            
            if recent_change > 5 * typical_change:
                return True
        
        return False

    async def _create_anomaly_alert(self, metric: MonitoringMetric) -> None:
        """Create alert for detected anomaly"""
        
        await self._create_alert(
            severity=AlertSeverity.WARNING,
            title=f"Anomaly Detected: {metric.name}",
            message=f"Unusual value detected for {metric.name}: {metric.value} {metric.unit}",
            metric_id=metric.metric_id,
            department=metric.department
        )

    async def generate_dashboard_view(self, layout: str = "operations") -> Dict[str, Any]:
        """Generate dashboard view data"""
        
        if layout not in self.dashboard_layouts:
            layout = "operations"
        
        panel_ids = self.dashboard_layouts[layout]
        panels_data = []
        
        for panel_id in panel_ids:
            if panel_id not in self.dashboard_panels:
                continue
            
            panel = self.dashboard_panels[panel_id]
            panel_data = {
                "panel_id": panel.panel_id,
                "title": panel.title,
                "type": panel.panel_type,
                "position": panel.position,
                "data": await self._get_panel_data(panel)
            }
            panels_data.append(panel_data)
        
        return {
            "layout": layout,
            "timestamp": datetime.utcnow().isoformat(),
            "panels": panels_data,
            "alerts": self._get_active_alerts_summary(),
            "system_status": self._get_system_status_summary()
        }

    async def _get_panel_data(self, panel: DashboardPanel) -> Dict[str, Any]:
        """Get data for a specific panel"""
        
        panel_data = {}
        
        if panel.panel_type == "multi_gauge":
            for metric_id in panel.metrics:
                if metric_id in self.current_metrics:
                    metric = self.current_metrics[metric_id]
                    panel_data[metric_id] = {
                        "value": metric.value,
                        "unit": metric.unit,
                        "status": self._get_metric_status(metric)
                    }
        
        elif panel.panel_type == "line_chart":
            for metric_id in panel.metrics:
                if metric_id in self.metrics_history:
                    history = list(self.metrics_history[metric_id])[-50:]  # Last 50 points
                    panel_data[metric_id] = [
                        {"timestamp": entry["timestamp"].isoformat(), "value": entry["value"]}
                        for entry in history
                    ]
        
        elif panel.panel_type == "table":
            rows = []
            for metric_id in panel.metrics:
                if metric_id in self.current_metrics:
                    metric = self.current_metrics[metric_id]
                    rows.append({
                        "name": metric.name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "status": self._get_metric_status(metric),
                        "timestamp": metric.timestamp.isoformat()
                    })
            panel_data["rows"] = rows
        
        elif panel.panel_type == "alert_list":
            panel_data["alerts"] = [
                {
                    "id": alert.alert_id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged
                }
                for alert in list(self.active_alerts.values())[:10]
            ]
        
        return panel_data

    def _get_metric_status(self, metric: MonitoringMetric) -> str:
        """Determine metric status (good, warning, critical)"""
        
        if metric.name in self.alert_thresholds:
            thresholds = self.alert_thresholds[metric.name]
            
            if "critical" in thresholds:
                if metric.name in ["revenue_daily"]:
                    if metric.value < thresholds["critical"]:
                        return "critical"
                else:
                    if metric.value > thresholds["critical"]:
                        return "critical"
            
            if "warning" in thresholds:
                if metric.name in ["revenue_daily"]:
                    if metric.value < thresholds["warning"]:
                        return "warning"
                else:
                    if metric.value > thresholds["warning"]:
                        return "warning"
        
        return "good"

    def _get_active_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of active alerts"""
        
        alert_counts = defaultdict(int)
        for alert in self.active_alerts.values():
            alert_counts[alert.severity.value] += 1
        
        return {
            "total": len(self.active_alerts),
            "by_severity": dict(alert_counts),
            "unacknowledged": len([a for a in self.active_alerts.values() if not a.acknowledged])
        }

    def _get_system_status_summary(self) -> Dict[str, Any]:
        """Get system status summary"""
        
        # Calculate overall system health
        health_score = 100.0
        
        # Deduct points for active alerts
        for alert in self.active_alerts.values():
            if alert.severity == AlertSeverity.CRITICAL:
                health_score -= 20
            elif alert.severity == AlertSeverity.ERROR:
                health_score -= 10
            elif alert.severity == AlertSeverity.WARNING:
                health_score -= 5
        
        health_score = max(0, health_score)
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "critical",
            "metrics_tracked": len(self.current_metrics),
            "departments_monitored": 4  # Frontend, Backend, R&D, Growth
        }

    async def generate_report(self, period: str = "daily") -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        
        if period == "daily":
            cutoff = datetime.utcnow() - timedelta(days=1)
        elif period == "weekly":
            cutoff = datetime.utcnow() - timedelta(days=7)
        else:  # monthly
            cutoff = datetime.utcnow() - timedelta(days=30)
        
        report = {
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {},
            "metrics": {},
            "alerts": {},
            "trends": {},
            "recommendations": []
        }
        
        # Analyze metrics
        for metric_id, history in self.metrics_history.items():
            recent_data = [entry for entry in history if entry["timestamp"] >= cutoff]
            
            if recent_data:
                values = [entry["value"] for entry in recent_data]
                report["metrics"][metric_id] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "current": values[-1] if values else 0
                }
        
        # Analyze alerts
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff]
        alert_summary = defaultdict(int)
        for alert in recent_alerts:
            alert_summary[alert.severity.value] += 1
        
        report["alerts"] = {
            "total": len(recent_alerts),
            "by_severity": dict(alert_summary),
            "mean_resolution_time": self._calculate_mean_resolution_time(recent_alerts)
        }
        
        # Generate recommendations
        report["recommendations"] = await self._generate_recommendations(report)
        
        return report

    def _calculate_mean_resolution_time(self, alerts: List[SystemAlert]) -> float:
        """Calculate mean alert resolution time"""
        
        resolution_times = []
        for alert in alerts:
            if alert.resolved and alert.resolution_time:
                resolution_time = (alert.resolution_time - alert.timestamp).total_seconds() / 60  # minutes
                resolution_times.append(resolution_time)
        
        return statistics.mean(resolution_times) if resolution_times else 0.0

    async def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on report data"""
        
        recommendations = []
        
        # Check for high alert frequency
        if report["alerts"]["total"] > 50:
            recommendations.append("High alert frequency detected. Review alert thresholds and system stability.")
        
        # Check for critical alerts
        if report["alerts"]["by_severity"].get("critical", 0) > 0:
            recommendations.append("Critical alerts detected. Immediate attention required for system stability.")
        
        # Check metric trends
        for metric_id, metric_data in report["metrics"].items():
            if "response_time" in metric_id and metric_data["avg"] > 500:
                recommendations.append(f"High average response time for {metric_id}. Consider optimization.")
            
            if "error_rate" in metric_id and metric_data["max"] > 5:
                recommendations.append(f"High error rate detected in {metric_id}. Investigate root cause.")
        
        return recommendations[:5]  # Return top 5 recommendations

    def get_dashboard_status(self) -> Dict[str, Any]:
        """Get dashboard status"""
        
        return {
            "dashboard_id": self.dashboard_id,
            "status": "operational",
            "metrics_tracked": len(self.current_metrics),
            "active_alerts": len(self.active_alerts),
            "alert_rules": len(self.alert_rules),
            "dashboard_panels": len(self.dashboard_panels),
            "real_time_streams": len(self.real_time_streams),
            "available_layouts": list(self.dashboard_layouts.keys())
        }

# Global unified monitoring instance
unified_monitoring = UnifiedMonitoringDashboard()