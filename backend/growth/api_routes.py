"""
Growth Engine API Routes

Ultra-responsive REST API for the Growth Engine system.
Provides endpoints for sprint execution, metrics monitoring,
agent management, and real-time growth analytics.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from .growth_interface import GrowthInterface
from .growth_scheduler import GrowthScheduler, SprintType, SprintIntensity, SprintSchedule
from .growth_metrics import growth_metrics_tracker, MetricType, GrowthMetrics
from .growth_notifications import growth_notification_system, NotificationType, AlertSeverity
from .pipeline_orchestrator import PipelineOrchestrator
from .data_models import Lead, Opportunity, Campaign, Deal, GrowthEvent

# Initialize router
growth_router = APIRouter(prefix="/api/growth", tags=["Growth Engine"])

# Initialize growth components
growth_interface = GrowthInterface()
growth_scheduler = GrowthScheduler()
pipeline_orchestrator = PipelineOrchestrator()

logger = logging.getLogger(__name__)

# Pydantic models for API requests
from pydantic import BaseModel

class SprintRequest(BaseModel):
    sprint_type: str  # bd_blitz, marketing_campaign, etc.
    intensity: str = "aggressive"
    duration_minutes: int = 120
    target_agents: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None

class AgentInvocationRequest(BaseModel):
    agent_id: str
    method: str
    parameters: Dict[str, Any] = {}

class AlertRequest(BaseModel):
    alert_type: str
    severity: str
    title: str
    message: str
    source_agent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ScheduleSprintRequest(BaseModel):
    sprint_id: str
    sprint_type: str
    intensity: str
    cron_expression: str
    duration_minutes: int
    target_agents: List[str] = []
    parameters: Dict[str, Any] = {}

# Sprint execution endpoints
@growth_router.post("/sprints/execute")
async def execute_growth_sprint(request: SprintRequest, background_tasks: BackgroundTasks):
    """Execute a growth sprint immediately"""
    try:
        # Validate sprint type
        if request.sprint_type not in [st.value for st in SprintType]:
            raise HTTPException(status_code=400, detail=f"Invalid sprint type: {request.sprint_type}")
        
        # Validate intensity
        if request.intensity not in [si.value for si in SprintIntensity]:
            raise HTTPException(status_code=400, detail=f"Invalid intensity: {request.intensity}")
        
        # Create sprint schedule
        sprint_schedule = SprintSchedule(
            sprint_id=f"api_{request.sprint_type}_{int(datetime.utcnow().timestamp())}",
            sprint_type=SprintType(request.sprint_type),
            intensity=SprintIntensity(request.intensity),
            cron_expression="",  # Manual execution
            duration_minutes=request.duration_minutes,
            target_agents=request.target_agents or ["all"],
            parameters=request.parameters or {}
        )
        
        # Execute sprint in background
        background_tasks.add_task(execute_sprint_background, sprint_schedule)
        
        return {
            "status": "success",
            "message": f"Growth sprint {request.sprint_type} initiated",
            "sprint_id": sprint_schedule.sprint_id,
            "estimated_duration": request.duration_minutes,
            "intensity": request.intensity
        }
        
    except Exception as e:
        logger.error(f"Sprint execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_sprint_background(sprint_schedule: SprintSchedule):
    """Background task to execute sprint"""
    try:
        await growth_scheduler._execute_sprint(sprint_schedule)
    except Exception as e:
        logger.error(f"Background sprint execution failed: {str(e)}")

@growth_router.get("/sprints/status")
async def get_sprint_status():
    """Get current sprint execution status"""
    try:
        status = await growth_scheduler.get_sprint_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Failed to get sprint status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/sprints/history")
async def get_sprint_history(limit: int = 50):
    """Get sprint execution history"""
    try:
        history = growth_scheduler.execution_history[-limit:]
        
        return {
            "total_executions": len(growth_scheduler.execution_history),
            "recent_executions": [
                {
                    "sprint_id": execution.sprint_id,
                    "execution_id": execution.execution_id,
                    "sprint_type": execution.sprint_type.value,
                    "start_time": execution.start_time.isoformat(),
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "status": execution.status,
                    "duration_minutes": execution.duration_minutes,
                    "agents_deployed": execution.agents_deployed
                }
                for execution in history
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get sprint history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent management endpoints
@growth_router.get("/agents")
async def list_agents():
    """List all available growth agents"""
    try:
        agents = growth_interface.agents
        
        return {
            "total_agents": len(agents),
            "bd_agents": [
                {
                    "agent_id": agent_id,
                    "agent_type": agent_info["type"],
                    "available_methods": agent_info["methods"],
                    "description": agent_info.get("description", "")
                }
                for agent_id, agent_info in agents.items()
                if "bd" in agent_info["type"]
            ],
            "marketing_agents": [
                {
                    "agent_id": agent_id,
                    "agent_type": agent_info["type"], 
                    "available_methods": agent_info["methods"],
                    "description": agent_info.get("description", "")
                }
                for agent_id, agent_info in agents.items()
                if "marketing" in agent_info["type"]
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.post("/agents/invoke")
async def invoke_agent(request: AgentInvocationRequest):
    """Invoke a specific agent method"""
    try:
        result = await growth_interface.invoke_agent(
            request.agent_id,
            request.method,
            request.parameters
        )
        
        return {
            "status": "success",
            "agent_id": request.agent_id,
            "method": request.method,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent invocation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str):
    """Get performance metrics for a specific agent"""
    try:
        if agent_id not in growth_metrics_tracker.agent_performances:
            raise HTTPException(status_code=404, detail=f"Agent performance data not found: {agent_id}")
        
        performance = growth_metrics_tracker.agent_performances[agent_id]
        
        return {
            "agent_id": agent_id,
            "agent_type": performance.agent_type,
            "performance_score": performance.performance_score,
            "efficiency_rating": performance.efficiency_rating,
            "target_achievement_rate": performance.target_achievement_rate,
            "recent_metrics": [
                {
                    "metric_type": metric.metric_type.value,
                    "value": metric.value,
                    "target": metric.target,
                    "performance_ratio": metric.performance_ratio,
                    "timestamp": metric.timestamp.isoformat()
                }
                for metric in performance.daily_metrics[-10:]  # Last 10 metrics
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics and analytics endpoints
@growth_router.get("/metrics/dashboard")
async def get_growth_dashboard():
    """Get comprehensive growth performance dashboard"""
    try:
        dashboard = await growth_metrics_tracker.get_performance_dashboard()
        return JSONResponse(content=dashboard)
    except Exception as e:
        logger.error(f"Failed to get growth dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/metrics/current")
async def get_current_metrics():
    """Get current growth metrics snapshot"""
    try:
        metrics = await growth_metrics_tracker.capture_system_snapshot()
        return JSONResponse(content=metrics.to_dict())
    except Exception as e:
        logger.error(f"Failed to get current metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/metrics/history")
async def get_metrics_history(days: int = 30):
    """Get historical metrics data"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        historical_data = [
            metrics.to_dict()
            for metrics in growth_metrics_tracker.historical_metrics
            if metrics.timestamp >= cutoff_date
        ]
        
        return {
            "period_days": days,
            "data_points": len(historical_data),
            "metrics_history": historical_data
        }
    except Exception as e:
        logger.error(f"Failed to get metrics history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/metrics/performance-alerts")
async def get_performance_alerts():
    """Get current performance alerts and recommendations"""
    try:
        alerts = await growth_metrics_tracker.generate_performance_alerts()
        recommendations = await growth_metrics_tracker.optimize_performance_recommendations()
        
        return {
            "alerts_count": len(alerts),
            "recommendations_count": len(recommendations),
            "performance_alerts": alerts,
            "optimization_recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Scheduler management endpoints  
@growth_router.post("/scheduler/start")
async def start_scheduler(background_tasks: BackgroundTasks):
    """Start the automated growth scheduler"""
    try:
        # Start scheduler in background
        background_tasks.add_task(start_scheduler_background)
        
        return {
            "status": "success",
            "message": "Growth scheduler started",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def start_scheduler_background():
    """Background task to start scheduler"""
    try:
        await growth_notification_system.start_notification_services()
        await growth_scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"Background scheduler start failed: {str(e)}")

@growth_router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the automated growth scheduler"""
    try:
        await growth_scheduler.stop_scheduler()
        
        return {
            "status": "success",
            "message": "Growth scheduler stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.post("/scheduler/sprints")
async def schedule_sprint(request: ScheduleSprintRequest):
    """Schedule a recurring growth sprint"""
    try:
        # Validate sprint type and intensity
        if request.sprint_type not in [st.value for st in SprintType]:
            raise HTTPException(status_code=400, detail=f"Invalid sprint type: {request.sprint_type}")
        
        if request.intensity not in [si.value for si in SprintIntensity]:
            raise HTTPException(status_code=400, detail=f"Invalid intensity: {request.intensity}")
        
        # Create sprint schedule
        sprint_schedule = SprintSchedule(
            sprint_id=request.sprint_id,
            sprint_type=SprintType(request.sprint_type),
            intensity=SprintIntensity(request.intensity),
            cron_expression=request.cron_expression,
            duration_minutes=request.duration_minutes,
            target_agents=request.target_agents,
            parameters=request.parameters
        )
        
        # Add to scheduler
        await growth_scheduler.add_custom_sprint(sprint_schedule)
        
        return {
            "status": "success",
            "message": f"Sprint {request.sprint_id} scheduled successfully",
            "sprint_id": request.sprint_id,
            "next_execution": sprint_schedule.next_execution.isoformat() if sprint_schedule.next_execution else None
        }
    except Exception as e:
        logger.error(f"Failed to schedule sprint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.delete("/scheduler/sprints/{sprint_id}")
async def remove_scheduled_sprint(sprint_id: str):
    """Remove a scheduled sprint"""
    try:
        success = await growth_scheduler.remove_sprint(sprint_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Sprint not found: {sprint_id}")
        
        return {
            "status": "success",
            "message": f"Sprint {sprint_id} removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove sprint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Notifications and alerts endpoints
@growth_router.get("/alerts")
async def get_active_alerts():
    """Get all active growth alerts"""
    try:
        alerts = await growth_notification_system.get_active_alerts()
        
        return {
            "alerts_count": len(alerts),
            "active_alerts": alerts,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.post("/alerts")
async def create_alert(request: AlertRequest):
    """Create a new growth alert"""
    try:
        alert = await growth_notification_system.create_alert(
            alert_type=NotificationType(request.alert_type),
            severity=AlertSeverity(request.severity),
            title=request.title,
            message=request.message,
            source_agent=request.source_agent,
            context=request.context
        )
        
        return {
            "status": "success",
            "alert_id": alert.alert_id,
            "message": "Alert created successfully",
            "notification_sent": alert.notification_sent
        }
    except Exception as e:
        logger.error(f"Failed to create alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    try:
        success = await growth_notification_system.acknowledge_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")
        
        return {
            "status": "success",
            "message": f"Alert {alert_id} acknowledged"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Pipeline management endpoints
@growth_router.get("/pipeline/status")
async def get_pipeline_status():
    """Get pipeline orchestrator status"""
    try:
        # Get pipeline statistics
        return {
            "pipeline_active": True,
            "events_processed": pipeline_orchestrator.events_processed,
            "active_leads": len([lead for lead in pipeline_orchestrator.leads.values() if lead.stage.name != "CLOSED"]),
            "active_opportunities": len([opp for opp in pipeline_orchestrator.opportunities.values() if opp.stage.name != "CLOSED"]),
            "active_campaigns": len([camp for camp in pipeline_orchestrator.campaigns.values() if camp.status.name == "ACTIVE"]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/pipeline/leads")
async def get_pipeline_leads(stage: Optional[str] = None, limit: int = 50):
    """Get pipeline leads"""
    try:
        leads = list(pipeline_orchestrator.leads.values())
        
        if stage:
            leads = [lead for lead in leads if lead.stage.name.lower() == stage.lower()]
        
        leads = leads[-limit:]  # Get most recent
        
        return {
            "leads_count": len(leads),
            "leads": [
                {
                    "id": lead.id,
                    "source": lead.source.value,
                    "stage": lead.stage.value,
                    "score": lead.score,
                    "company": lead.company,
                    "contact_email": lead.contact_email,
                    "created_at": lead.created_at.isoformat(),
                    "last_activity": lead.last_activity.isoformat() if lead.last_activity else None
                }
                for lead in leads
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get pipeline leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/pipeline/opportunities")
async def get_pipeline_opportunities(stage: Optional[str] = None, limit: int = 50):
    """Get pipeline opportunities"""
    try:
        opportunities = list(pipeline_orchestrator.opportunities.values())
        
        if stage:
            opportunities = [opp for opp in opportunities if opp.stage.name.lower() == stage.lower()]
        
        opportunities = opportunities[-limit:]  # Get most recent
        
        return {
            "opportunities_count": len(opportunities),
            "opportunities": [
                {
                    "id": opp.id,
                    "lead_id": opp.lead_id,
                    "stage": opp.stage.value,
                    "value": opp.value,
                    "probability": opp.probability,
                    "company": opp.company,
                    "created_at": opp.created_at.isoformat(),
                    "last_activity": opp.last_activity.isoformat() if opp.last_activity else None
                }
                for opp in opportunities
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get pipeline opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@growth_router.get("/health")
async def growth_engine_health():
    """Growth Engine health check"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "growth_interface": len(growth_interface.agents) > 0,
                "scheduler": True,  # Would check actual scheduler health
                "metrics_tracker": True,
                "notification_system": True,
                "pipeline_orchestrator": True
            },
            "agents_available": len(growth_interface.agents),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Import monitoring dashboard
from .monitoring_dashboard import growth_engine_monitor

# Growth Engine Monitoring Endpoints
@growth_router.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """Get comprehensive Growth Engine monitoring dashboard"""
    try:
        dashboard_data = await growth_engine_monitor.get_dashboard_data()
        return JSONResponse(content=dashboard_data.to_dict())
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/monitoring/agents/{agent_id}")
async def get_agent_monitoring_details(agent_id: str):
    """Get detailed monitoring information for a specific agent"""
    try:
        agent_details = await growth_engine_monitor.get_agent_details(agent_id)
        
        if not agent_details:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        return JSONResponse(content=agent_details)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent monitoring details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/monitoring/health")
async def get_system_health():
    """Get Growth Engine system health summary"""
    try:
        dashboard_data = await growth_engine_monitor.get_dashboard_data()
        
        return {
            "timestamp": dashboard_data.timestamp.isoformat(),
            "system_health": dashboard_data.system_health.to_dict(),
            "agent_summary": {
                "total_agents": len(dashboard_data.agent_monitoring),
                "healthy": len([a for a in dashboard_data.agent_monitoring if a.health_status.value == "healthy"]),
                "warning": len([a for a in dashboard_data.agent_monitoring if a.health_status.value == "warning"]),
                "critical": len([a for a in dashboard_data.agent_monitoring if a.health_status.value == "critical"]),
                "offline": len([a for a in dashboard_data.agent_monitoring if a.health_status.value == "offline"])
            },
            "system_status": "operational" if dashboard_data.system_health.overall_health_score > 70 else "degraded" if dashboard_data.system_health.overall_health_score > 30 else "critical"
        }
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.get("/monitoring/agents")
async def list_monitored_agents():
    """List all monitored Growth Engine agents with basic status"""
    try:
        dashboard_data = await growth_engine_monitor.get_dashboard_data()
        
        return {
            "timestamp": dashboard_data.timestamp.isoformat(),
            "total_agents": len(dashboard_data.agent_monitoring),
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "health_status": agent.health_status.value,
                    "performance_score": agent.performance_score,
                    "success_rate": agent.success_rate,
                    "last_activity": agent.last_activity.isoformat() if agent.last_activity else None,
                    "alerts_count": agent.alerts_count,
                    "current_sprint_participation": agent.current_sprint_participation
                }
                for agent in dashboard_data.agent_monitoring
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list monitored agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@growth_router.post("/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start the Growth Engine monitoring system"""
    try:
        background_tasks.add_task(start_monitoring_background)
        
        return {
            "status": "success",
            "message": "Growth Engine monitoring system started",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def start_monitoring_background():
    """Background task to start monitoring"""
    try:
        await growth_engine_monitor.start_monitoring()
    except Exception as e:
        logger.error(f"Background monitoring start failed: {str(e)}")

@growth_router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop the Growth Engine monitoring system"""
    try:
        await growth_engine_monitor.stop_monitoring()
        
        return {
            "status": "success",
            "message": "Growth Engine monitoring system stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router for integration with main FastAPI app
__all__ = ["growth_router"]