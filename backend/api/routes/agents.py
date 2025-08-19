"""
Agent API Routes
REST API endpoints for Claude Code agent management and invocation
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from ...agents.claude_agent_interface import claude_agents
from ...agents.monitoring import agent_monitor

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Request/Response Models
class AgentInvocationRequest(BaseModel):
    agent_name: str
    task_description: str
    parameters: Optional[Dict[str, Any]] = None

class OptimizationRequest(BaseModel):
    optimization_type: str = "general"
    domain: Optional[str] = None  # "frontend", "backend", or None for both

class AgentResponse(BaseModel):
    task_id: str
    agent_name: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentStatusResponse(BaseModel):
    name: str
    description: str
    tools: List[str]
    status: str
    active_tasks: int
    last_invoked: Optional[str] = None

class SystemStatusResponse(BaseModel):
    total_agents: int
    available_agents: int
    active_tasks: int
    completed_tasks: int
    agents_directory: str
    last_discovery: str

# Agent Management Endpoints

@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all available Claude Code agents"""
    try:
        agents = claude_agents.get_available_agents()
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing agents: {str(e)}")

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get overall agent system status"""
    try:
        status = claude_agents.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

@router.get("/{agent_name}", response_model=AgentStatusResponse)
async def get_agent_status(agent_name: str):
    """Get status of a specific agent"""
    try:
        status = claude_agents.get_agent_status(agent_name)
        if not status:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agent status: {str(e)}")

# Agent Invocation Endpoints

@router.post("/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentInvocationRequest, background_tasks: BackgroundTasks):
    """Invoke a specific Claude Code agent"""
    try:
        result = await claude_agents.invoke_agent(
            agent_name=request.agent_name,
            task_description=request.task_description,
            parameters=request.parameters
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking agent: {str(e)}")

@router.post("/optimize", response_model=Dict[str, Any])
async def trigger_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """Trigger optimization cycle"""
    try:
        if request.domain == "frontend":
            result = await claude_agents.optimize_frontend(request.optimization_type)
        elif request.domain == "backend":
            result = await claude_agents.optimize_backend(request.optimization_type)
        else:
            # Full-stack optimization via Helios
            result = await claude_agents.invoke_optimization_cycle()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering optimization: {str(e)}")

@router.post("/emergency", response_model=AgentResponse)
async def trigger_emergency_response(background_tasks: BackgroundTasks):
    """Trigger emergency response via Helios orchestrator"""
    try:
        result = await claude_agents.invoke_emergency_response()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering emergency response: {str(e)}")

# Task Management Endpoints

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    try:
        task_status = claude_agents.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
        return task_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")

# Specific Agent Optimization Endpoints

@router.post("/frontend/analyze")
async def analyze_frontend():
    """Analyze frontend performance via Prometheus-Frontend"""
    try:
        result = await claude_agents.invoke_agent(
            "prometheus-frontend",
            "Comprehensive frontend performance analysis",
            {"analysis_type": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing frontend: {str(e)}")

@router.post("/frontend/optimize")
async def optimize_frontend():
    """Optimize frontend via Hephaestus-Frontend"""
    try:
        result = await claude_agents.invoke_agent(
            "hephaestus-frontend",
            "Implement frontend performance optimizations",
            {"optimization_type": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing frontend: {str(e)}")

@router.post("/frontend/verify")
async def verify_frontend():
    """Verify frontend quality via Athena-UX"""
    try:
        result = await claude_agents.invoke_agent(
            "athena-ux",
            "Verify frontend optimization quality and user experience",
            {"verification_type": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying frontend: {str(e)}")

@router.post("/backend/analyze")
async def analyze_backend():
    """Analyze backend performance via Prometheus-Backend"""
    try:
        result = await claude_agents.invoke_agent(
            "prometheus-backend",
            "Comprehensive backend performance analysis",
            {"analysis_type": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing backend: {str(e)}")

@router.post("/backend/optimize")
async def optimize_backend():
    """Optimize backend via Hephaestus-Backend"""
    try:
        result = await claude_agents.invoke_agent(
            "hephaestus-backend",
            "Implement backend infrastructure optimizations",
            {"optimization_type": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing backend: {str(e)}")

@router.post("/backend/verify")
async def verify_backend():
    """Verify backend quality via Athena-API"""
    try:
        result = await claude_agents.invoke_agent(
            "athena-api",
            "Verify backend optimization quality and API performance",
            {"verification_type": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying backend: {str(e)}")

# Orchestrator Endpoints

@router.post("/orchestrate/cycle")
async def orchestrate_optimization_cycle():
    """Execute optimization cycle via Helios orchestrator"""
    try:
        result = await claude_agents.invoke_agent(
            "helios-orchestrator",
            "Execute comprehensive optimization cycle",
            {"type": "optimization", "mode": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error orchestrating optimization cycle: {str(e)}")

@router.post("/orchestrate/emergency")
async def orchestrate_emergency_response():
    """Execute emergency response via Helios orchestrator"""
    try:
        result = await claude_agents.invoke_agent(
            "helios-orchestrator",
            "Execute emergency performance response",
            {"type": "emergency", "threshold": 0.5, "max_issues": 3}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error orchestrating emergency response: {str(e)}")

@router.post("/orchestrate/analysis")
async def orchestrate_strategic_analysis():
    """Execute strategic analysis via Helios orchestrator"""
    try:
        result = await claude_agents.invoke_agent(
            "helios-orchestrator",
            "Execute strategic performance analysis",
            {"type": "analysis", "depth": "comprehensive"}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error orchestrating strategic analysis: {str(e)}")

# Chat Interface Optimization Endpoints

@router.post("/optimize/chat")
async def optimize_chat_interface():
    """Optimize chat interface performance"""
    try:
        # Frontend chat optimization
        frontend_result = await claude_agents.invoke_agent(
            "hephaestus-frontend",
            "Optimize chat interface performance and responsiveness",
            {"optimization_type": "chat_interface_optimization"}
        )
        
        # Backend chat optimization
        backend_result = await claude_agents.invoke_agent(
            "hephaestus-backend",
            "Optimize chat backend infrastructure and message processing",
            {"optimization_type": "chat_backend_optimization"}
        )
        
        return {
            "optimization_type": "chat_interface",
            "frontend_optimization": frontend_result,
            "backend_optimization": backend_result,
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing chat interface: {str(e)}")

@router.post("/optimize/feed")
async def optimize_prompt_feed():
    """Optimize prompt feed performance and engagement"""
    try:
        # Frontend feed optimization
        frontend_result = await claude_agents.invoke_agent(
            "hephaestus-frontend",
            "Optimize prompt feed loading and user engagement",
            {"optimization_type": "prompt_feed_optimization"}
        )
        
        # Backend feed optimization
        backend_result = await claude_agents.invoke_agent(
            "hephaestus-backend",
            "Optimize prompt feed backend and content delivery",
            {"optimization_type": "prompt_feed_backend_optimization"}
        )
        
        return {
            "optimization_type": "prompt_feed",
            "frontend_optimization": frontend_result,
            "backend_optimization": backend_result,
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing prompt feed: {str(e)}")

# Monitoring Endpoints

@router.get("/monitoring/system-health")
async def get_system_health():
    """Get current system health metrics"""
    try:
        return agent_monitor.get_system_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system health: {str(e)}")

@router.get("/monitoring/agent-metrics")
async def get_agent_metrics():
    """Get performance metrics for all agents"""
    try:
        return agent_monitor.get_all_agent_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agent metrics: {str(e)}")

@router.get("/monitoring/agent-metrics/{agent_name}")
async def get_specific_agent_metrics(agent_name: str):
    """Get performance metrics for a specific agent"""
    try:
        metrics = agent_monitor.get_agent_metrics(agent_name)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Metrics for agent '{agent_name}' not found")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agent metrics: {str(e)}")

@router.get("/monitoring/alerts")
async def get_performance_alerts(alert_type: Optional[str] = None):
    """Get performance alerts"""
    try:
        return {
            "alerts": agent_monitor.get_performance_alerts(alert_type),
            "count": len(agent_monitor.get_performance_alerts(alert_type)),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

@router.get("/monitoring/history")
async def get_metrics_history(hours: int = 24):
    """Get system metrics history"""
    try:
        return {
            "metrics_history": agent_monitor.get_system_metrics_history(hours),
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics history: {str(e)}")

@router.get("/monitoring/report")
async def get_performance_report():
    """Get comprehensive performance report"""
    try:
        return agent_monitor.generate_performance_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating performance report: {str(e)}")

@router.post("/monitoring/start")
async def start_monitoring():
    """Start the monitoring system"""
    try:
        await agent_monitor.start_monitoring()
        return {
            "status": "monitoring_started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")

@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop the monitoring system"""
    try:
        await agent_monitor.stop_monitoring()
        return {
            "status": "monitoring_stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping monitoring: {str(e)}")

# Health Check
@router.get("/health")
async def agent_system_health():
    """Health check for agent system"""
    try:
        status = claude_agents.get_system_status()
        health = agent_monitor.get_system_health()
        
        return {
            "status": "healthy" if health["health_score"] > 50 else "degraded",
            "timestamp": datetime.now().isoformat(),
            "agents_available": status["available_agents"] > 0,
            "total_agents": status["total_agents"],
            "system_ready": status["total_agents"] >= 7,  # All 7 agents should be available
            "health_score": health["health_score"],
            "performance_grade": health["performance_grade"],
            "monitoring_active": agent_monitor.monitoring_active
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }