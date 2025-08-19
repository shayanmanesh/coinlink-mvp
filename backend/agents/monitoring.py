"""
Agent Monitoring System
Real-time monitoring and performance tracking for Claude Code agents
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_name: str
    total_invocations: int = 0
    successful_invocations: int = 0
    failed_invocations: int = 0
    average_response_time: float = 0.0
    last_invocation: Optional[datetime] = None
    last_error: Optional[str] = None
    success_rate: float = 0.0

@dataclass
class SystemHealthMetrics:
    """Overall system health metrics"""
    timestamp: datetime
    total_agents: int
    active_agents: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    system_health_score: float
    performance_grade: str

class AgentMonitor:
    """Real-time agent monitoring and performance tracking"""
    
    def __init__(self, monitoring_interval: int = 60):
        self.monitoring_interval = monitoring_interval
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.system_metrics_history: deque = deque(maxlen=100)
        self.performance_alerts: List[Dict[str, Any]] = []
        self.monitoring_active = False
        
        # Performance thresholds
        self.thresholds = {
            "response_time_warning": 5.0,  # seconds
            "response_time_critical": 10.0,  # seconds
            "success_rate_warning": 0.8,  # 80%
            "success_rate_critical": 0.6,  # 60%
            "system_health_warning": 70,  # score
            "system_health_critical": 50   # score
        }
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        self.monitoring_active = True
        logger.info("Agent monitoring system started")
        
        # Start background monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        logger.info("Agent monitoring system stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_system_metrics()
                await self._check_performance_alerts()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            from .claude_agent_interface import claude_agents
            
            # Get system status
            system_status = claude_agents.get_system_status()
            
            # Calculate system health score
            health_score = self._calculate_system_health_score()
            
            # Create system health metrics
            metrics = SystemHealthMetrics(
                timestamp=datetime.now(),
                total_agents=system_status["total_agents"],
                active_agents=system_status["available_agents"],
                total_tasks=system_status["active_tasks"] + system_status["completed_tasks"],
                completed_tasks=system_status["completed_tasks"],
                failed_tasks=0,  # Would need to track this separately
                system_health_score=health_score,
                performance_grade=self._get_performance_grade(health_score)
            )
            
            # Add to history
            self.system_metrics_history.append(metrics)
            
            logger.debug(f"System health score: {health_score}")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _calculate_system_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        try:
            # Agent availability (30% weight)
            if len(self.agent_metrics) > 0:
                agent_health = sum(
                    metrics.success_rate * 100 
                    for metrics in self.agent_metrics.values()
                ) / len(self.agent_metrics)
                score = score * 0.3 + agent_health * 0.3
            
            # Response time performance (40% weight)
            avg_response_time = self._get_average_response_time()
            if avg_response_time > 0:
                response_score = max(0, 100 - (avg_response_time * 10))  # 10 points per second
                score = score * 0.6 + response_score * 0.4
            
            # System availability (30% weight)
            availability_score = 100  # Assume high availability for now
            score = score * 0.7 + availability_score * 0.3
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            score = 50.0  # Default to moderate health
        
        return min(100.0, max(0.0, score))
    
    def _get_average_response_time(self) -> float:
        """Get average response time across all agents"""
        if not self.agent_metrics:
            return 0.0
        
        total_time = sum(metrics.average_response_time for metrics in self.agent_metrics.values())
        return total_time / len(self.agent_metrics)
    
    def _get_performance_grade(self, health_score: float) -> str:
        """Convert health score to performance grade"""
        if health_score >= 90:
            return "A"
        elif health_score >= 80:
            return "B"
        elif health_score >= 70:
            return "C"
        elif health_score >= 60:
            return "D"
        else:
            return "F"
    
    async def _check_performance_alerts(self):
        """Check for performance issues and generate alerts"""
        alerts = []
        
        # Check individual agent performance
        for agent_name, metrics in self.agent_metrics.items():
            # Response time alerts
            if metrics.average_response_time > self.thresholds["response_time_critical"]:
                alerts.append({
                    "type": "critical",
                    "agent": agent_name,
                    "metric": "response_time",
                    "value": metrics.average_response_time,
                    "threshold": self.thresholds["response_time_critical"],
                    "message": f"Agent {agent_name} response time is critically high: {metrics.average_response_time:.2f}s"
                })
            elif metrics.average_response_time > self.thresholds["response_time_warning"]:
                alerts.append({
                    "type": "warning",
                    "agent": agent_name,
                    "metric": "response_time",
                    "value": metrics.average_response_time,
                    "threshold": self.thresholds["response_time_warning"],
                    "message": f"Agent {agent_name} response time is high: {metrics.average_response_time:.2f}s"
                })
            
            # Success rate alerts
            if metrics.success_rate < self.thresholds["success_rate_critical"]:
                alerts.append({
                    "type": "critical",
                    "agent": agent_name,
                    "metric": "success_rate",
                    "value": metrics.success_rate,
                    "threshold": self.thresholds["success_rate_critical"],
                    "message": f"Agent {agent_name} success rate is critically low: {metrics.success_rate:.1%}"
                })
            elif metrics.success_rate < self.thresholds["success_rate_warning"]:
                alerts.append({
                    "type": "warning",
                    "agent": agent_name,
                    "metric": "success_rate",
                    "value": metrics.success_rate,
                    "threshold": self.thresholds["success_rate_warning"],
                    "message": f"Agent {agent_name} success rate is low: {metrics.success_rate:.1%}"
                })
        
        # Check system health
        if self.system_metrics_history:
            latest_health = self.system_metrics_history[-1].system_health_score
            
            if latest_health < self.thresholds["system_health_critical"]:
                alerts.append({
                    "type": "critical",
                    "agent": "system",
                    "metric": "health_score",
                    "value": latest_health,
                    "threshold": self.thresholds["system_health_critical"],
                    "message": f"System health is critically low: {latest_health:.1f}"
                })
            elif latest_health < self.thresholds["system_health_warning"]:
                alerts.append({
                    "type": "warning",
                    "agent": "system",
                    "metric": "health_score",
                    "value": latest_health,
                    "threshold": self.thresholds["system_health_warning"],
                    "message": f"System health is low: {latest_health:.1f}"
                })
        
        # Add new alerts
        for alert in alerts:
            alert["timestamp"] = datetime.now()
            self.performance_alerts.append(alert)
            logger.warning(f"Performance alert: {alert['message']}")
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.performance_alerts = [
            alert for alert in self.performance_alerts
            if alert["timestamp"] > cutoff_time
        ]
    
    def record_agent_invocation(self, agent_name: str, success: bool, response_time: float, error: Optional[str] = None):
        """Record an agent invocation for monitoring"""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
        
        metrics = self.agent_metrics[agent_name]
        
        # Update metrics
        metrics.total_invocations += 1
        metrics.last_invocation = datetime.now()
        
        if success:
            metrics.successful_invocations += 1
        else:
            metrics.failed_invocations += 1
            metrics.last_error = error
        
        # Update success rate
        metrics.success_rate = metrics.successful_invocations / metrics.total_invocations
        
        # Update average response time (exponential moving average)
        if metrics.total_invocations == 1:
            metrics.average_response_time = response_time
        else:
            alpha = 0.1  # Smoothing factor
            metrics.average_response_time = (
                alpha * response_time + 
                (1 - alpha) * metrics.average_response_time
            )
    
    def get_agent_metrics(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific agent"""
        if agent_name not in self.agent_metrics:
            return None
        
        metrics = self.agent_metrics[agent_name]
        return asdict(metrics)
    
    def get_all_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all agents"""
        return {
            name: asdict(metrics) 
            for name, metrics in self.agent_metrics.items()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health information"""
        if not self.system_metrics_history:
            return {
                "health_score": 0,
                "performance_grade": "F",
                "status": "unknown",
                "timestamp": datetime.now().isoformat()
            }
        
        latest = self.system_metrics_history[-1]
        
        return {
            "health_score": latest.system_health_score,
            "performance_grade": latest.performance_grade,
            "total_agents": latest.total_agents,
            "active_agents": latest.active_agents,
            "total_tasks": latest.total_tasks,
            "completed_tasks": latest.completed_tasks,
            "timestamp": latest.timestamp.isoformat(),
            "status": "healthy" if latest.system_health_score > 70 else "degraded"
        }
    
    def get_performance_alerts(self, alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get performance alerts"""
        alerts = self.performance_alerts
        
        if alert_type:
            alerts = [alert for alert in alerts if alert["type"] == alert_type]
        
        # Convert datetime to ISO string for JSON serialization
        for alert in alerts:
            if isinstance(alert["timestamp"], datetime):
                alert["timestamp"] = alert["timestamp"].isoformat()
        
        return alerts
    
    def get_system_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_metrics = [
            asdict(metrics) for metrics in self.system_metrics_history
            if metrics.timestamp > cutoff_time
        ]
        
        # Convert datetime to ISO string
        for metrics in filtered_metrics:
            if isinstance(metrics["timestamp"], datetime):
                metrics["timestamp"] = metrics["timestamp"].isoformat()
        
        return filtered_metrics
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            "system_health": self.get_system_health(),
            "agent_metrics": self.get_all_agent_metrics(),
            "performance_alerts": self.get_performance_alerts(),
            "metrics_history": self.get_system_metrics_history(hours=1),  # Last hour
            "report_generated": datetime.now().isoformat()
        }

# Global monitor instance
agent_monitor = AgentMonitor()