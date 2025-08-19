"""
Real-time KPI tracking system for monitoring performance metrics
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import json

logger = logging.getLogger(__name__)

@dataclass
class KPIMetric:
    """Represents a single KPI metric"""
    name: str
    target: float
    current: float
    unit: str
    category: str  # frontend, backend, business, agent
    priority: int = 1  # 1=high, 2=medium, 3=low
    history: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update(self, value: float):
        """Update metric value and history"""
        self.current = value
        self.last_updated = datetime.now()
        self.history.append({
            'value': value,
            'timestamp': self.last_updated.isoformat()
        })
    
    def get_trend(self, window_minutes: int = 5) -> str:
        """Get trend direction over specified window"""
        if len(self.history) < 2:
            return "stable"
        
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_values = [
            point['value'] for point in self.history
            if datetime.fromisoformat(point['timestamp']) > cutoff
        ]
        
        if len(recent_values) < 2:
            return "stable"
        
        # Simple trend calculation
        slope = (recent_values[-1] - recent_values[0]) / len(recent_values)
        threshold = abs(self.target * 0.05)  # 5% threshold
        
        if slope > threshold:
            return "improving"
        elif slope < -threshold:
            return "declining"
        else:
            return "stable"
    
    def is_meeting_target(self) -> bool:
        """Check if current value meets target"""
        # For most metrics, lower is better (response times, etc.)
        # For some metrics, higher is better (hit rates, etc.)
        if self.name in ['cache_hit_rate', 'user_retention_24h', 'messages_per_session', 'prompt_click_rate', 'report_share_rate']:
            return self.current >= self.target
        else:
            return self.current <= self.target

class KPITracker:
    """Central KPI monitoring system"""
    
    def __init__(self):
        self.metrics: Dict[str, KPIMetric] = {}
        self.collectors: Dict[str, Callable] = {}
        self.running = False
        self.collection_interval = 10  # seconds
        self.alerts: List[Dict] = []
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self):
        """Initialize default KPI metrics"""
        
        # Frontend metrics
        frontend_metrics = {
            "chat_response_time": {"target": 100, "unit": "ms", "priority": 1},
            "prompt_feed_refresh": {"target": 1000, "unit": "ms", "priority": 2},
            "ui_interaction_lag": {"target": 50, "unit": "ms", "priority": 1},
            "message_render_time": {"target": 20, "unit": "ms", "priority": 2},
            "websocket_latency": {"target": 30, "unit": "ms", "priority": 1}
        }
        
        # Backend metrics
        backend_metrics = {
            "api_response_time": {"target": 100, "unit": "ms", "priority": 1},
            "redis_cache_hit": {"target": 95, "unit": "%", "priority": 2},
            "websocket_throughput": {"target": 1000, "unit": "msg/s", "priority": 2},
            "report_generation": {"target": 500, "unit": "ms", "priority": 1},
            "sentiment_analysis": {"target": 200, "unit": "ms", "priority": 2}
        }
        
        # Business metrics
        business_metrics = {
            "user_retention_24h": {"target": 40, "unit": "%", "priority": 1},
            "messages_per_session": {"target": 5, "unit": "count", "priority": 1},
            "prompt_click_rate": {"target": 15, "unit": "%", "priority": 2},
            "report_share_rate": {"target": 10, "unit": "%", "priority": 2},
            "session_duration": {"target": 300, "unit": "seconds", "priority": 1}
        }
        
        # Agent metrics
        agent_metrics = {
            "optimizations_per_hour": {"target": 10, "unit": "count", "priority": 1},
            "optimization_success_rate": {"target": 80, "unit": "%", "priority": 1},
            "agent_response_time": {"target": 1000, "unit": "ms", "priority": 2},
            "learning_rate": {"target": 5, "unit": "%", "priority": 2}
        }
        
        # Create KPIMetric objects
        for name, config in frontend_metrics.items():
            self.metrics[name] = KPIMetric(
                name=name,
                target=config["target"],
                current=0,
                unit=config["unit"],
                category="frontend",
                priority=config["priority"]
            )
        
        for name, config in backend_metrics.items():
            self.metrics[name] = KPIMetric(
                name=name,
                target=config["target"],
                current=0,
                unit=config["unit"],
                category="backend",
                priority=config["priority"]
            )
        
        for name, config in business_metrics.items():
            self.metrics[name] = KPIMetric(
                name=name,
                target=config["target"],
                current=0,
                unit=config["unit"],
                category="business",
                priority=config["priority"]
            )
        
        for name, config in agent_metrics.items():
            self.metrics[name] = KPIMetric(
                name=name,
                target=config["target"],
                current=0,
                unit=config["unit"],
                category="agent",
                priority=config["priority"]
            )
    
    def register_collector(self, metric_name: str, collector_func: Callable):
        """Register a function to collect a specific metric"""
        self.collectors[metric_name] = collector_func
    
    async def start_monitoring(self):
        """Start continuous KPI monitoring"""
        self.running = True
        logger.info("KPI monitoring started")
        
        while self.running:
            try:
                await self.collect_all_metrics()
                await self.check_alerts()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in KPI monitoring: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def stop_monitoring(self):
        """Stop KPI monitoring"""
        self.running = False
        logger.info("KPI monitoring stopped")
    
    async def collect_all_metrics(self):
        """Collect all registered metrics"""
        tasks = []
        
        for metric_name, collector in self.collectors.items():
            if metric_name in self.metrics:
                tasks.append(self.collect_metric(metric_name, collector))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def collect_metric(self, metric_name: str, collector: Callable):
        """Collect a single metric"""
        try:
            if asyncio.iscoroutinefunction(collector):
                value = await collector()
            else:
                value = collector()
            
            if isinstance(value, (int, float)):
                self.metrics[metric_name].update(value)
        except Exception as e:
            logger.error(f"Error collecting metric {metric_name}: {e}")
    
    def update_metric(self, metric_name: str, value: float):
        """Manually update a metric value"""
        if metric_name in self.metrics:
            self.metrics[metric_name].update(value)
        else:
            logger.warning(f"Unknown metric: {metric_name}")
    
    async def check_alerts(self):
        """Check for KPI alerts"""
        new_alerts = []
        
        for metric in self.metrics.values():
            if not metric.is_meeting_target():
                # Create alert for metrics not meeting target
                alert = {
                    "type": "target_miss",
                    "metric": metric.name,
                    "current": metric.current,
                    "target": metric.target,
                    "severity": "high" if metric.priority == 1 else "medium",
                    "timestamp": datetime.now().isoformat()
                }
                new_alerts.append(alert)
            
            # Check for rapid degradation
            trend = metric.get_trend(window_minutes=2)
            if trend == "declining" and metric.priority == 1:
                alert = {
                    "type": "rapid_degradation",
                    "metric": metric.name,
                    "current": metric.current,
                    "trend": trend,
                    "severity": "critical",
                    "timestamp": datetime.now().isoformat()
                }
                new_alerts.append(alert)
        
        # Store recent alerts
        self.alerts.extend(new_alerts)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # Log critical alerts
        for alert in new_alerts:
            if alert["severity"] == "critical":
                logger.critical(f"Critical KPI alert: {alert}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_metrics": len(self.metrics),
            "metrics_meeting_target": sum(1 for m in self.metrics.values() if m.is_meeting_target()),
            "categories": {}
        }
        
        # Group by category
        for category in ["frontend", "backend", "business", "agent"]:
            category_metrics = {
                name: {
                    "current": metric.current,
                    "target": metric.target,
                    "unit": metric.unit,
                    "meeting_target": metric.is_meeting_target(),
                    "trend": metric.get_trend(),
                    "priority": metric.priority
                }
                for name, metric in self.metrics.items()
                if metric.category == category
            }
            summary["categories"][category] = category_metrics
        
        return summary
    
    def get_metric_details(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific metric"""
        if metric_name not in self.metrics:
            return None
        
        metric = self.metrics[metric_name]
        return {
            "name": metric.name,
            "current": metric.current,
            "target": metric.target,
            "unit": metric.unit,
            "category": metric.category,
            "priority": metric.priority,
            "meeting_target": metric.is_meeting_target(),
            "trend": metric.get_trend(),
            "last_updated": metric.last_updated.isoformat(),
            "history": list(metric.history)[-50:]  # Last 50 points
        }
    
    def get_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts[-limit:] if limit else self.alerts
    
    def calculate_overall_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        if not self.metrics:
            return 0
        
        total_score = 0
        total_weight = 0
        
        for metric in self.metrics.values():
            # Weight by priority (high priority = more weight)
            weight = 4 - metric.priority  # priority 1 = weight 3, priority 3 = weight 1
            
            if metric.is_meeting_target():
                score = 100
            else:
                # Calculate score based on how far from target
                if metric.name in ['cache_hit_rate', 'user_retention_24h', 'messages_per_session', 'prompt_click_rate', 'report_share_rate']:
                    # Higher is better
                    if metric.target > 0:
                        score = max(0, (metric.current / metric.target) * 100)
                    else:
                        score = 100 if metric.current > 0 else 0
                else:
                    # Lower is better
                    if metric.current > 0:
                        score = max(0, (metric.target / metric.current) * 100)
                    else:
                        score = 100
                
                score = min(100, score)  # Cap at 100
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        health_score = self.calculate_overall_health_score()
        
        # Count metrics by status
        meeting_target = sum(1 for m in self.metrics.values() if m.is_meeting_target())
        total_metrics = len(self.metrics)
        
        # Count by trend
        improving = sum(1 for m in self.metrics.values() if m.get_trend() == "improving")
        declining = sum(1 for m in self.metrics.values() if m.get_trend() == "declining")
        stable = sum(1 for m in self.metrics.values() if m.get_trend() == "stable")
        
        # Recent alerts by severity
        recent_alerts = self.get_alerts(50)
        critical_alerts = sum(1 for a in recent_alerts if a.get("severity") == "critical")
        high_alerts = sum(1 for a in recent_alerts if a.get("severity") == "high")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": round(health_score, 2),
            "metrics_status": {
                "total": total_metrics,
                "meeting_target": meeting_target,
                "missing_target": total_metrics - meeting_target,
                "target_rate": round((meeting_target / total_metrics) * 100, 2) if total_metrics > 0 else 0
            },
            "trends": {
                "improving": improving,
                "declining": declining,
                "stable": stable
            },
            "alerts": {
                "total_recent": len(recent_alerts),
                "critical": critical_alerts,
                "high": high_alerts
            },
            "categories": self.get_metrics_summary()["categories"]
        }


# Singleton instance
kpi_tracker = KPITracker()