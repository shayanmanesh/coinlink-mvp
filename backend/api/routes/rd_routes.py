"""
R&D Department API Routes
REST API endpoints for R&D agent management, innovation pipeline, and metrics
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

# Import R&D modules with error handling for different deployment contexts
try:
    from ...rd.rd_interface import rd_agents
    from ...rd.innovation_pipeline import innovation_pipeline, PipelineStage, ApprovalStatus
    from ...rd.rd_metrics import rd_metrics_tracker
    from ...rd.notification_system import email_notifier
    from ...rd.scheduler import rd_scheduler
    from ...rd.rd_orchestrator import rd_orchestrator
except ImportError:
    # Fallback for production deployment
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'rd'))
    try:
        from rd.rd_interface import rd_agents
        from rd.innovation_pipeline import innovation_pipeline, PipelineStage, ApprovalStatus
        from rd.rd_metrics import rd_metrics_tracker
        from rd.notification_system import email_notifier
        from rd.scheduler import rd_scheduler
        from rd.rd_orchestrator import rd_orchestrator
    except ImportError:
        # Final fallback - disable R&D routes if modules not available
        rd_agents = None

router = APIRouter(prefix="/api/rd", tags=["rd"])

# Request/Response Models

class RDAgentInvocationRequest(BaseModel):
    agent_name: str
    task_type: str
    description: str
    parameters: Optional[Dict[str, Any]] = None

class InnovationSubmissionRequest(BaseModel):
    name: str
    description: str
    category: str = "general"
    source_agent: str
    market_opportunity_score: int = 50
    competitive_advantage_score: int = 50
    user_demand_score: int = 50
    implementation_complexity: str = "M"

class ApprovalDecisionRequest(BaseModel):
    innovation_id: str
    decision: str  # approved, rejected, needs_review, on_hold
    notes: Optional[str] = None

class EmailReportRequest(BaseModel):
    report_type: str  # weekly_innovation, competitive_alert, feature_approval
    data: Dict[str, Any]

class SchedulerConfigRequest(BaseModel):
    report_interval_minutes: Optional[int] = None
    thirty_minute_reports: Optional[bool] = None
    competitive_monitoring: Optional[bool] = None
    priority_threshold: Optional[str] = None
    enable_quiet_hours: Optional[bool] = None

# R&D System Availability Check
def check_rd_system():
    if rd_agents is None:
        raise HTTPException(status_code=503, detail="R&D system not available - modules failed to load")

# R&D System Status Endpoints

@router.get("/status")
async def rd_system_status():
    """Check R&D system availability and status"""
    if rd_agents is None:
        return {
            "status": "unavailable",
            "message": "R&D modules failed to load",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        check_rd_system()
        return {
            "status": "available", 
            "message": "R&D system is operational",
            "scheduler_loaded": rd_scheduler is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

# R&D Agent Management Endpoints

@router.get("/agents")
async def list_rd_agents():
    """List all R&D department agents"""
    check_rd_system()
    try:
        agents = rd_agents.get_rd_agents()
        return {
            "agents": agents,
            "total_agents": len(agents),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing R&D agents: {str(e)}")

@router.get("/agents/status")
async def get_rd_system_status():
    """Get overall R&D system status"""
    try:
        status = rd_agents.get_rd_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting R&D system status: {str(e)}")

@router.get("/agents/{agent_name}")
async def get_rd_agent_status(agent_name: str):
    """Get status of specific R&D agent"""
    try:
        status = rd_agents.get_rd_agent_status(agent_name)
        if not status:
            raise HTTPException(status_code=404, detail=f"R&D agent '{agent_name}' not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting R&D agent status: {str(e)}")

@router.post("/agents/invoke")
async def invoke_rd_agent(request: RDAgentInvocationRequest, background_tasks: BackgroundTasks):
    """Invoke specific R&D agent"""
    try:
        result = await rd_agents.invoke_rd_agent(
            agent_name=request.agent_name,
            task_type=request.task_type,
            description=request.description,
            parameters=request.parameters
        )
        
        # Record metrics in background
        background_tasks.add_task(
            rd_metrics_tracker.record_agent_task,
            request.agent_name,
            request.task_type,
            result.get("status") == "completed",
            1.0,  # Mock response time
            85.0  # Mock quality score
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking R&D agent: {str(e)}")

# Innovation Cycle Management

@router.post("/cycles/start")
async def start_innovation_cycle():
    """Start new weekly innovation cycle"""
    try:
        cycle_id = rd_agents.start_innovation_cycle()
        
        # Initialize metrics tracking
        rd_metrics_tracker.start_innovation_cycle(cycle_id)
        
        return {
            "cycle_id": cycle_id,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting innovation cycle: {str(e)}")

@router.get("/cycles/current")
async def get_current_cycle_status():
    """Get current innovation cycle status"""
    try:
        cycle_status = rd_agents.get_innovation_cycle_status()
        if not cycle_status:
            raise HTTPException(status_code=404, detail="No active innovation cycle")
        return cycle_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cycle status: {str(e)}")

@router.get("/cycles/{cycle_id}")
async def get_cycle_status(cycle_id: str):
    """Get specific innovation cycle status"""
    try:
        cycle_status = rd_agents.get_innovation_cycle_status(cycle_id)
        if not cycle_status:
            raise HTTPException(status_code=404, detail=f"Innovation cycle '{cycle_id}' not found")
        return cycle_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cycle status: {str(e)}")

# Innovation Pipeline Endpoints

@router.post("/innovations/submit")
async def submit_innovation(request: InnovationSubmissionRequest):
    """Submit new innovation to pipeline"""
    try:
        innovation_data = request.dict()
        innovation_id = innovation_pipeline.add_innovation(innovation_data)
        
        # Update cycle metrics
        rd_metrics_tracker.update_cycle_metrics("features_ideated", 1)
        
        return {
            "innovation_id": innovation_id,
            "status": "submitted",
            "pipeline_stage": "ideation",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting innovation: {str(e)}")

@router.get("/innovations/pipeline")
async def get_pipeline_status():
    """Get innovation pipeline status"""
    try:
        status = innovation_pipeline.get_pipeline_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pipeline status: {str(e)}")

@router.get("/innovations/stage/{stage}")
async def get_innovations_by_stage(stage: str):
    """Get innovations at specific pipeline stage"""
    try:
        # Validate stage
        try:
            pipeline_stage = PipelineStage(stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid pipeline stage: {stage}")
        
        innovations = innovation_pipeline.get_innovations_by_stage(pipeline_stage)
        return {
            "stage": stage,
            "innovations": innovations,
            "count": len(innovations)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting innovations by stage: {str(e)}")

@router.get("/innovations/approval-queue")
async def get_approval_queue():
    """Get innovations ready for approval"""
    try:
        ready_innovations = innovation_pipeline.get_ready_for_approval()
        return {
            "innovations": ready_innovations,
            "count": len(ready_innovations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting approval queue: {str(e)}")

@router.post("/innovations/approve")
async def approve_innovation(request: ApprovalDecisionRequest, background_tasks: BackgroundTasks):
    """Make approval decision for innovation"""
    try:
        # Validate decision
        try:
            approval_status = ApprovalStatus(request.decision)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid approval decision: {request.decision}")
        
        success = innovation_pipeline.set_approval_status(
            request.innovation_id,
            approval_status,
            request.notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Innovation '{request.innovation_id}' not found")
        
        # Send email notification if approved
        if approval_status == ApprovalStatus.APPROVED:
            background_tasks.add_task(
                _send_approval_notification,
                request.innovation_id,
                request.notes
            )
            
            # Update metrics
            rd_metrics_tracker.update_cycle_metrics("innovations_approved", 1)
        
        return {
            "innovation_id": request.innovation_id,
            "decision": request.decision,
            "status": "processed",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing approval: {str(e)}")

@router.post("/innovations/{innovation_id}/advance")
async def advance_innovation_stage(innovation_id: str, notes: Optional[str] = None):
    """Advance innovation to next pipeline stage"""
    try:
        success = innovation_pipeline.advance_innovation_stage(innovation_id, notes)
        if not success:
            raise HTTPException(status_code=404, detail=f"Innovation '{innovation_id}' not found or cannot advance")
        
        return {
            "innovation_id": innovation_id,
            "status": "advanced",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error advancing innovation stage: {str(e)}")

@router.get("/innovations/{innovation_id}/evaluation")
async def evaluate_innovation(innovation_id: str):
    """Get innovation evaluation and recommendation"""
    try:
        evaluation = innovation_pipeline.evaluate_innovation_approval(innovation_id)
        if "error" in evaluation:
            raise HTTPException(status_code=404, detail=evaluation["error"])
        return evaluation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating innovation: {str(e)}")

# Production Handoff Endpoints

@router.post("/handoff/prepare/{innovation_id}")
async def prepare_production_handoff(innovation_id: str):
    """Prepare innovation for production handoff"""
    try:
        handoff_package = innovation_pipeline.prepare_production_handoff(innovation_id)
        if "error" in handoff_package:
            raise HTTPException(status_code=400, detail=handoff_package["error"])
        
        # Update metrics
        rd_metrics_tracker.update_cycle_metrics("handoffs_to_production", 1)
        
        return handoff_package
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preparing handoff: {str(e)}")

@router.post("/handoff/batch")
async def process_batch_handoffs():
    """Process batch of innovations for production handoff"""
    try:
        handoff_results = innovation_pipeline.process_batch_handoffs()
        return {
            "handoffs_processed": len(handoff_results),
            "handoff_packages": handoff_results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch handoffs: {str(e)}")

@router.post("/handoff/coordinate/{innovation_id}")
async def coordinate_with_helios(innovation_id: str):
    """Coordinate with Helios for production integration"""
    try:
        # Get handoff package
        handoff_package = innovation_pipeline.prepare_production_handoff(innovation_id)
        if "error" in handoff_package:
            raise HTTPException(status_code=400, detail=handoff_package["error"])
        
        # Coordinate with Helios
        success = await innovation_pipeline.coordinate_with_helios(handoff_package)
        
        return {
            "innovation_id": innovation_id,
            "coordination_status": "success" if success else "failed",
            "handoff_package": handoff_package,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error coordinating with Helios: {str(e)}")

# Metrics and Analytics Endpoints

@router.get("/metrics/agents")
async def get_agent_performance_metrics():
    """Get agent performance metrics"""
    try:
        metrics = rd_metrics_tracker.get_agent_performance_report()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agent metrics: {str(e)}")

@router.get("/metrics/innovation")
async def get_innovation_metrics():
    """Get innovation pipeline metrics"""
    try:
        metrics = rd_metrics_tracker.get_innovation_pipeline_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting innovation metrics: {str(e)}")

@router.get("/metrics/overview")
async def get_metrics_overview():
    """Get comprehensive R&D metrics overview"""
    try:
        innovation_metrics = rd_agents.get_innovation_metrics()
        pipeline_status = innovation_pipeline.get_pipeline_status()
        agent_performance = rd_metrics_tracker.get_agent_performance_report()
        
        return {
            "innovation_metrics": innovation_metrics,
            "pipeline_status": pipeline_status,
            "agent_performance": agent_performance["team_averages"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics overview: {str(e)}")

# Email Notification Endpoints

@router.post("/notifications/weekly-report")
async def send_weekly_report(background_tasks: BackgroundTasks):
    """Send weekly innovation report"""
    try:
        # Generate sample report data
        report_data = email_notifier.generate_sample_weekly_report()
        
        # Send email in background
        background_tasks.add_task(
            email_notifier.send_weekly_innovation_report,
            report_data
        )
        
        return {
            "status": "report_scheduled",
            "message": "Weekly innovation report will be sent shortly",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending weekly report: {str(e)}")

@router.post("/notifications/competitive-alert")
async def send_competitive_alert(alert_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Send urgent competitive alert"""
    try:
        # Send alert in background
        background_tasks.add_task(
            email_notifier.send_urgent_competitive_alert,
            alert_data
        )
        
        return {
            "status": "alert_scheduled",
            "message": "Competitive alert will be sent immediately",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending competitive alert: {str(e)}")

@router.post("/notifications/feature-approval")
async def send_feature_approval_request(feature_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Send feature approval request"""
    try:
        # Send approval request in background
        background_tasks.add_task(
            email_notifier.send_feature_approval_request,
            feature_data
        )
        
        return {
            "status": "approval_request_scheduled",
            "message": "Feature approval request will be sent shortly",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending approval request: {str(e)}")

# Scheduler Management Endpoints

@router.post("/scheduler/start")
async def start_rd_scheduler():
    """Start the R&D automated scheduler"""
    try:
        if rd_scheduler.is_running:
            return {
                "status": "already_running",
                "message": "R&D scheduler is already active",
                "timestamp": datetime.now().isoformat()
            }
        
        await rd_scheduler.start_scheduler()
        
        return {
            "status": "started",
            "message": "R&D scheduler started successfully",
            "report_interval_minutes": rd_scheduler.report_interval_minutes,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")

@router.post("/scheduler/stop")
async def stop_rd_scheduler():
    """Stop the R&D automated scheduler"""
    try:
        if not rd_scheduler.is_running:
            return {
                "status": "already_stopped",
                "message": "R&D scheduler is not running",
                "timestamp": datetime.now().isoformat()
            }
        
        await rd_scheduler.stop_scheduler()
        
        return {
            "status": "stopped",
            "message": "R&D scheduler stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get current scheduler status and configuration"""
    try:
        status = rd_scheduler.get_scheduler_status()
        orchestrator_status = rd_orchestrator.get_orchestration_status()
        
        return {
            "scheduler": status,
            "orchestrator": orchestrator_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")

@router.post("/scheduler/configure")
async def update_scheduler_config(request: SchedulerConfigRequest):
    """Update scheduler configuration"""
    try:
        # Build config dict from non-None values
        config_updates = {}
        if request.report_interval_minutes is not None:
            config_updates["report_interval_minutes"] = request.report_interval_minutes
        if request.thirty_minute_reports is not None:
            config_updates["thirty_minute_reports"] = request.thirty_minute_reports
        if request.competitive_monitoring is not None:
            config_updates["competitive_monitoring"] = request.competitive_monitoring
        if request.priority_threshold is not None:
            config_updates["priority_threshold"] = request.priority_threshold
        if request.enable_quiet_hours is not None:
            rd_scheduler.enable_quiet_hours = request.enable_quiet_hours
        
        if config_updates:
            rd_scheduler.update_schedule_config(config_updates)
        
        return {
            "status": "updated",
            "message": "Scheduler configuration updated successfully",
            "updated_config": config_updates,
            "current_config": rd_scheduler.schedule_config,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating scheduler config: {str(e)}")

@router.post("/scheduler/report/immediate")
async def trigger_immediate_report(background_tasks: BackgroundTasks):
    """Trigger an immediate 30-minute report"""
    try:
        # Run report generation in background
        background_tasks.add_task(rd_scheduler.trigger_immediate_report)
        
        return {
            "status": "triggered",
            "message": "Immediate 30-minute report generation triggered",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering immediate report: {str(e)}")

@router.post("/reports/thirty-minute")
async def generate_thirty_minute_report(background_tasks: BackgroundTasks):
    """Generate and send 30-minute R&D report"""
    try:
        # Generate report data
        report_data = await rd_orchestrator.generate_thirty_minute_report(
            include_delta=True,
            last_report_data=rd_scheduler.last_report_data
        )
        
        # Send email in background
        background_tasks.add_task(
            email_notifier.send_thirty_minute_report,
            report_data
        )
        
        return {
            "status": "generated",
            "message": "30-minute report generated and will be sent shortly",
            "report_metadata": report_data.get("orchestration_metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating 30-minute report: {str(e)}")

@router.get("/reports/thirty-minute/preview")
async def preview_thirty_minute_report():
    """Preview 30-minute report without sending email"""
    try:
        report_data = await rd_orchestrator.generate_thirty_minute_report(
            include_delta=True,
            last_report_data=rd_scheduler.last_report_data
        )
        
        return {
            "status": "preview_generated",
            "report_data": report_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report preview: {str(e)}")

# Specialized R&D Workflows

@router.post("/workflows/competitive-intelligence")
async def run_competitive_intelligence():
    """Run competitive intelligence workflow"""
    try:
        # Invoke Argus for competitive analysis
        result = await rd_agents.invoke_rd_agent(
            "argus-competitor",
            "competitive_analysis",
            "Weekly competitive intelligence scan",
            {"comprehensive": True}
        )
        
        # Update metrics
        rd_metrics_tracker.update_cycle_metrics("competitors_analyzed", 5)
        
        return {
            "workflow": "competitive_intelligence",
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running competitive intelligence: {str(e)}")

@router.post("/workflows/research-analysis")
async def run_research_analysis():
    """Run research analysis workflow"""
    try:
        # Invoke Minerva for research analysis
        result = await rd_agents.invoke_rd_agent(
            "minerva-research",
            "research_analysis",
            "Weekly research landscape analysis",
            {"comprehensive": True}
        )
        
        # Update metrics
        rd_metrics_tracker.update_cycle_metrics("research_papers_reviewed", 8)
        
        return {
            "workflow": "research_analysis",
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running research analysis: {str(e)}")

@router.post("/workflows/feature-strategy")
async def run_feature_strategy():
    """Run feature strategy development workflow"""
    try:
        # Invoke Vulcan for strategic planning
        result = await rd_agents.invoke_rd_agent(
            "vulcan-strategy",
            "strategic_planning",
            "Weekly feature strategy development",
            {"intelligence_integration": True}
        )
        
        # Update metrics
        rd_metrics_tracker.update_cycle_metrics("strategic_recommendations", 3)
        
        return {
            "workflow": "feature_strategy",
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running feature strategy: {str(e)}")

@router.post("/workflows/prototyping/{innovation_id}")
async def run_prototyping_workflow(innovation_id: str):
    """Run prototyping workflow for specific innovation"""
    try:
        # Invoke Daedalus for prototyping
        result = await rd_agents.invoke_rd_agent(
            "daedalus-prototype",
            "prototype_development",
            f"Prototype development for innovation {innovation_id}",
            {"innovation_id": innovation_id}
        )
        
        # Update metrics
        rd_metrics_tracker.update_cycle_metrics("prototypes_created", 1)
        
        return {
            "workflow": "prototyping",
            "innovation_id": innovation_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running prototyping workflow: {str(e)}")

# Apollo Orchestration Endpoints

@router.post("/apollo/orchestrate")
async def run_apollo_orchestration():
    """Run complete R&D orchestration cycle via Apollo"""
    try:
        # Invoke Apollo for full cycle orchestration
        result = await rd_agents.invoke_rd_agent(
            "apollo-rd-orchestrator",
            "full_cycle_orchestration",
            "Complete R&D innovation cycle orchestration",
            {"cycle_type": "weekly", "comprehensive": True}
        )
        
        return {
            "orchestrator": "apollo",
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running Apollo orchestration: {str(e)}")

@router.get("/apollo/status")
async def get_apollo_status():
    """Get Apollo orchestrator status"""
    try:
        status = rd_agents.get_rd_agent_status("apollo-rd-orchestrator")
        if not status:
            raise HTTPException(status_code=404, detail="Apollo orchestrator not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Apollo status: {str(e)}")

# Health Check

@router.get("/health")
async def rd_health_check():
    """Health check for R&D system"""
    try:
        system_status = rd_agents.get_rd_system_status()
        pipeline_status = innovation_pipeline.get_pipeline_status()
        
        # Determine overall health
        health_indicators = [
            system_status["total_rd_agents"] >= 7,  # All agents available
            system_status["available_agents"] > 0,  # At least some agents working
            pipeline_status["pipeline_health"] in ["good", "excellent"],  # Pipeline healthy
        ]
        
        overall_health = "healthy" if all(health_indicators) else "degraded"
        
        return {
            "status": overall_health,
            "timestamp": datetime.now().isoformat(),
            "rd_agents_available": system_status["available_agents"] > 0,
            "total_rd_agents": system_status["total_rd_agents"],
            "innovation_pipeline_health": pipeline_status["pipeline_health"],
            "active_innovation_cycle": system_status["current_innovation_cycle"] is not None,
            "system_ready": system_status["total_rd_agents"] >= 7
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Helper Functions

async def _send_approval_notification(innovation_id: str, notes: Optional[str]):
    """Send approval notification email"""
    try:
        # In production, this would get actual innovation data
        feature_data = {
            "id": innovation_id,
            "name": f"Innovation {innovation_id[:8]}",
            "description": "Innovation approved for production development",
            "approval_notes": notes,
            "prototype_status": "Available"
        }
        
        await email_notifier.send_feature_approval_request(feature_data)
    except Exception as e:
        logger.error(f"Error sending approval notification: {e}")