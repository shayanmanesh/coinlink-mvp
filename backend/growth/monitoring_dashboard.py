"""
Growth Engine Monitoring Dashboard

Ultra-comprehensive real-time monitoring system for all Growth Engine agents.
Provides live performance tracking, health monitoring, sprint execution status,
and performance analytics with unified dashboard visualization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from .growth_interface import get_growth_agents
from .growth_metrics import growth_metrics_tracker, AgentPerformance, MetricType
from .growth_scheduler import growth_scheduler, SprintExecution
from .growth_notifications import growth_notification_system
from .pipeline_orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)

class AgentHealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

@dataclass
class AgentMonitoringData:
    """Real-time agent monitoring data"""
    agent_id: str
    agent_type: str
    health_status: AgentHealthStatus
    performance_score: float
    last_activity: Optional[datetime] = None
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    current_sprint_participation: bool = False
    alerts_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "health_status": self.health_status.value,
            "performance_score": self.performance_score,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "average_response_time": self.average_response_time,
            "current_sprint_participation": self.current_sprint_participation,
            "alerts_count": self.alerts_count
        }

@dataclass
class SystemHealthMetrics:
    """Overall system health metrics"""
    timestamp: datetime
    overall_health_score: float
    total_agents: int
    healthy_agents: int
    warning_agents: int
    critical_agents: int
    offline_agents: int
    active_sprints: int
    completed_sprints_24h: int
    total_alerts: int
    system_uptime: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "overall_health_score": self.overall_health_score,
            "agent_distribution": {
                "total": self.total_agents,
                "healthy": self.healthy_agents,
                "warning": self.warning_agents,
                "critical": self.critical_agents,
                "offline": self.offline_agents
            },
            "sprint_activity": {
                "active_sprints": self.active_sprints,
                "completed_24h": self.completed_sprints_24h
            },
            "alerts": {
                "total_active": self.total_alerts
            },
            "system_uptime": self.system_uptime
        }

@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    timestamp: datetime
    system_health: SystemHealthMetrics
    agent_monitoring: List[AgentMonitoringData]
    performance_metrics: Dict[str, Any]
    active_sprints: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]
    pipeline_status: Dict[str, Any]
    revenue_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "system_health": self.system_health.to_dict(),
            "agent_monitoring": [agent.to_dict() for agent in self.agent_monitoring],
            "performance_metrics": self.performance_metrics,
            "active_sprints": self.active_sprints,
            "recent_alerts": self.recent_alerts,
            "pipeline_status": self.pipeline_status,
            "revenue_metrics": self.revenue_metrics
        }

class GrowthEngineMonitor:
    """Ultra-comprehensive Growth Engine monitoring system"""
    
    def __init__(self, update_interval: int = 30):
        self.update_interval = update_interval  # seconds
        self.monitoring_active = False
        self.agent_monitoring_data: Dict[str, AgentMonitoringData] = {}
        self.system_start_time = datetime.utcnow()
        self.pipeline_orchestrator = PipelineOrchestrator()
        
        # Performance thresholds
        self.health_thresholds = {
            "performance_score": {
                "critical": 0.5,
                "warning": 0.7,
                "healthy": 0.8
            },
            "success_rate": {
                "critical": 0.6,
                "warning": 0.8,
                "healthy": 0.9
            },
            "response_time": {
                "critical": 10.0,  # seconds
                "warning": 5.0,
                "healthy": 2.0
            }
        }
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.system_start_time = datetime.utcnow()
        
        logger.info("Starting Growth Engine monitoring system")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        # Initialize agent monitoring
        await self._initialize_agent_monitoring()
        
        logger.info("Growth Engine monitoring system started successfully")
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        logger.info("Growth Engine monitoring system stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._update_all_monitoring_data()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.update_interval * 2)  # Wait longer on error
    
    async def _initialize_agent_monitoring(self):
        """Initialize monitoring for all growth agents"""
        try:
            growth_agents = get_growth_agents()
            await growth_agents.initialize_async()
            
            for agent_id, agent_info in growth_agents.agents.items():
                self.agent_monitoring_data[agent_id] = AgentMonitoringData(
                    agent_id=agent_id,
                    agent_type=agent_info.get("type", "unknown"),
                    health_status=AgentHealthStatus.UNKNOWN,
                    performance_score=0.0
                )
            
            logger.info(f"Initialized monitoring for {len(self.agent_monitoring_data)} growth agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent monitoring: {str(e)}")
    
    async def _update_all_monitoring_data(self):
        """Update all monitoring data"""
        try:
            await self._update_agent_health_status()
            await self._update_performance_metrics()
            await self._update_sprint_participation()
            await self._update_alert_counts()
            
        except Exception as e:
            logger.error(f"Error updating monitoring data: {str(e)}")
    
    async def _update_agent_health_status(self):
        """Update health status for all agents"""
        for agent_id, monitoring_data in self.agent_monitoring_data.items():
            try:
                # Get performance data from metrics tracker
                if agent_id in growth_metrics_tracker.agent_performances:
                    perf_data = growth_metrics_tracker.agent_performances[agent_id]
                    
                    monitoring_data.performance_score = perf_data.performance_score
                    monitoring_data.last_activity = datetime.utcnow()  # Simplified
                    monitoring_data.success_rate = perf_data.target_achievement_rate
                    
                    # Calculate health status based on performance
                    health_status = self._calculate_health_status(
                        performance_score=perf_data.performance_score,
                        success_rate=perf_data.target_achievement_rate,
                        response_time=1.0  # Placeholder
                    )
                    
                    monitoring_data.health_status = health_status
                else:
                    # No performance data available
                    monitoring_data.health_status = AgentHealthStatus.UNKNOWN
                    
            except Exception as e:
                logger.error(f"Error updating health for agent {agent_id}: {str(e)}")
                monitoring_data.health_status = AgentHealthStatus.CRITICAL
    
    def _calculate_health_status(self, performance_score: float, success_rate: float, 
                               response_time: float) -> AgentHealthStatus:
        """Calculate overall health status based on metrics"""
        
        # Check critical thresholds
        if (performance_score < self.health_thresholds["performance_score"]["critical"] or
            success_rate < self.health_thresholds["success_rate"]["critical"] or
            response_time > self.health_thresholds["response_time"]["critical"]):
            return AgentHealthStatus.CRITICAL
        
        # Check warning thresholds
        if (performance_score < self.health_thresholds["performance_score"]["warning"] or
            success_rate < self.health_thresholds["success_rate"]["warning"] or
            response_time > self.health_thresholds["response_time"]["warning"]):
            return AgentHealthStatus.WARNING
        
        # Check healthy thresholds
        if (performance_score >= self.health_thresholds["performance_score"]["healthy"] and
            success_rate >= self.health_thresholds["success_rate"]["healthy"] and
            response_time <= self.health_thresholds["response_time"]["healthy"]):
            return AgentHealthStatus.HEALTHY
        
        return AgentHealthStatus.WARNING
    
    async def _update_performance_metrics(self):
        """Update performance metrics for all agents"""
        for agent_id, monitoring_data in self.agent_monitoring_data.items():
            try:
                if agent_id in growth_metrics_tracker.agent_performances:
                    perf = growth_metrics_tracker.agent_performances[agent_id]
                    
                    # Count tasks (simplified - would get from actual task tracking)
                    monitoring_data.completed_tasks = len(perf.daily_metrics)
                    monitoring_data.failed_tasks = max(0, len(perf.daily_metrics) - int(perf.target_achievement_rate * len(perf.daily_metrics)))
                    monitoring_data.success_rate = perf.target_achievement_rate
                    
            except Exception as e:
                logger.error(f"Error updating performance metrics for {agent_id}: {str(e)}")
    
    async def _update_sprint_participation(self):
        """Update sprint participation status"""
        try:
            # Check active sprint executions
            active_sprints = growth_scheduler.active_executions
            
            for agent_id, monitoring_data in self.agent_monitoring_data.items():
                monitoring_data.current_sprint_participation = False
                
                # Check if agent is in any active sprint
                for execution in active_sprints.values():
                    if agent_id in execution.agents_deployed:
                        monitoring_data.current_sprint_participation = True
                        break
                        
        except Exception as e:
            logger.error(f"Error updating sprint participation: {str(e)}")
    
    async def _update_alert_counts(self):
        """Update alert counts for agents"""
        try:
            active_alerts = await growth_notification_system.get_active_alerts()
            
            # Reset all alert counts
            for monitoring_data in self.agent_monitoring_data.values():
                monitoring_data.alerts_count = 0
            
            # Count alerts by source agent
            for alert in active_alerts:
                source_agent = alert.get('source_agent')
                if source_agent and source_agent in self.agent_monitoring_data:
                    self.agent_monitoring_data[source_agent].alerts_count += 1
                    
        except Exception as e:
            logger.error(f"Error updating alert counts: {str(e)}")
    
    async def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data"""
        try:
            current_time = datetime.utcnow()
            
            # Calculate system health metrics
            system_health = await self._calculate_system_health_metrics(current_time)
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics()
            
            # Get active sprints
            active_sprints = await self._get_active_sprints()
            
            # Get recent alerts
            recent_alerts = await self._get_recent_alerts()
            
            # Get pipeline status
            pipeline_status = await self._get_pipeline_status()
            
            # Get revenue metrics
            revenue_metrics = await self._get_revenue_metrics()
            
            dashboard_data = DashboardData(
                timestamp=current_time,
                system_health=system_health,
                agent_monitoring=list(self.agent_monitoring_data.values()),
                performance_metrics=performance_metrics,
                active_sprints=active_sprints,
                recent_alerts=recent_alerts,
                pipeline_status=pipeline_status,
                revenue_metrics=revenue_metrics
            )
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            raise
    
    async def _calculate_system_health_metrics(self, timestamp: datetime) -> SystemHealthMetrics:
        """Calculate overall system health metrics"""
        try:
            agent_statuses = [data.health_status for data in self.agent_monitoring_data.values()]
            
            healthy_count = sum(1 for status in agent_statuses if status == AgentHealthStatus.HEALTHY)
            warning_count = sum(1 for status in agent_statuses if status == AgentHealthStatus.WARNING)
            critical_count = sum(1 for status in agent_statuses if status == AgentHealthStatus.CRITICAL)
            offline_count = sum(1 for status in agent_statuses if status == AgentHealthStatus.OFFLINE)
            
            total_agents = len(agent_statuses)
            
            # Calculate overall health score
            if total_agents > 0:
                health_score = (
                    (healthy_count * 1.0 + warning_count * 0.7 + critical_count * 0.3) / total_agents
                ) * 100
            else:
                health_score = 0.0
            
            # Get sprint activity
            active_sprints = len(growth_scheduler.active_executions)
            
            # Count completed sprints in last 24h
            cutoff_time = timestamp - timedelta(days=1)
            completed_24h = sum(
                1 for execution in growth_scheduler.execution_history
                if execution.end_time and execution.end_time >= cutoff_time
            )
            
            # Get alert count
            active_alerts = await growth_notification_system.get_active_alerts()
            total_alerts = len(active_alerts)
            
            # Calculate uptime
            uptime_seconds = (timestamp - self.system_start_time).total_seconds()
            uptime_hours = uptime_seconds / 3600
            
            return SystemHealthMetrics(
                timestamp=timestamp,
                overall_health_score=health_score,
                total_agents=total_agents,
                healthy_agents=healthy_count,
                warning_agents=warning_count,
                critical_agents=critical_count,
                offline_agents=offline_count,
                active_sprints=active_sprints,
                completed_sprints_24h=completed_24h,
                total_alerts=total_alerts,
                system_uptime=uptime_hours
            )
            
        except Exception as e:
            logger.error(f"Error calculating system health metrics: {str(e)}")
            raise
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        try:
            dashboard = await growth_metrics_tracker.get_performance_dashboard()
            return {
                "current_metrics": dashboard.get("current_metrics", {}),
                "target_achievement": dashboard.get("target_achievement", {}),
                "system_health": dashboard.get("system_health", {})
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    async def _get_active_sprints(self) -> List[Dict[str, Any]]:
        """Get active sprint information"""
        try:
            active_sprints = []
            for execution_id, execution in growth_scheduler.active_executions.items():
                active_sprints.append({
                    "execution_id": execution_id,
                    "sprint_id": execution.sprint_id,
                    "sprint_type": execution.sprint_type.value,
                    "start_time": execution.start_time.isoformat(),
                    "duration_minutes": execution.duration_minutes,
                    "status": execution.status,
                    "agents_deployed": execution.agents_deployed
                })
            return active_sprints
        except Exception as e:
            logger.error(f"Error getting active sprints: {str(e)}")
            return []
    
    async def _get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            active_alerts = await growth_notification_system.get_active_alerts()
            # Return most recent alerts
            return sorted(
                active_alerts,
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )[:limit]
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    async def _get_pipeline_status(self) -> Dict[str, Any]:
        """Get pipeline status information"""
        try:
            return {
                "active_leads": len([
                    lead for lead in self.pipeline_orchestrator.leads.values()
                    if lead.stage.name != "CLOSED"
                ]),
                "active_opportunities": len([
                    opp for opp in self.pipeline_orchestrator.opportunities.values()
                    if opp.stage.name != "CLOSED"
                ]),
                "active_campaigns": len([
                    camp for camp in self.pipeline_orchestrator.campaigns.values()
                    if camp.status.name == "ACTIVE"
                ]),
                "events_processed": self.pipeline_orchestrator.events_processed
            }
        except Exception as e:
            logger.error(f"Error getting pipeline status: {str(e)}")
            return {}
    
    async def _get_revenue_metrics(self) -> Dict[str, Any]:
        """Get revenue metrics"""
        try:
            current_metrics = await growth_metrics_tracker.capture_system_snapshot()
            
            return {
                "current_revenue": current_metrics.revenue_recognized,
                "deals_closed": current_metrics.deals_closed,
                "avg_deal_size": current_metrics.avg_deal_size,
                "leads_generated": current_metrics.leads_generated,
                "opportunities_created": current_metrics.opportunities_created,
                "growth_velocity": current_metrics.growth_velocity,
                "marketing_roi": current_metrics.marketing_roi
            }
        except Exception as e:
            logger.error(f"Error getting revenue metrics: {str(e)}")
            return {}
    
    async def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific agent"""
        if agent_id not in self.agent_monitoring_data:
            return None
        
        try:
            monitoring_data = self.agent_monitoring_data[agent_id]
            
            # Get performance history if available
            performance_history = []
            if agent_id in growth_metrics_tracker.agent_performances:
                perf = growth_metrics_tracker.agent_performances[agent_id]
                performance_history = [
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "metric_type": metric.metric_type.value,
                        "value": metric.value,
                        "target": metric.target,
                        "performance_ratio": metric.performance_ratio
                    }
                    for metric in perf.daily_metrics[-20:]  # Last 20 metrics
                ]
            
            return {
                "monitoring_data": monitoring_data.to_dict(),
                "performance_history": performance_history,
                "health_thresholds": self.health_thresholds
            }
            
        except Exception as e:
            logger.error(f"Error getting agent details for {agent_id}: {str(e)}")
            return None

# Global monitoring instance
growth_engine_monitor = GrowthEngineMonitor()