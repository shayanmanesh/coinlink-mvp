"""
Innovation Pipeline
Bridge between R&D innovations and production system integration
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """Innovation pipeline stages"""
    IDEATION = "ideation"
    VALIDATION = "validation"
    PROTOTYPING = "prototyping"
    APPROVAL = "approval"
    HANDOFF = "handoff"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"

class ApprovalStatus(Enum):
    """Feature approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    ON_HOLD = "on_hold"

@dataclass
class FeatureInnovation:
    """Innovation feature in the pipeline"""
    id: str
    name: str
    description: str
    category: str  # chat_interface, prompt_feed, ai_reports, infrastructure
    source_agent: str
    created_at: datetime
    current_stage: PipelineStage
    approval_status: ApprovalStatus
    
    # Business metrics
    market_opportunity_score: int  # 1-100
    competitive_advantage_score: int  # 1-100
    user_demand_score: int  # 1-100
    implementation_complexity: str  # S, M, L, XL
    
    # Technical details
    prototype_url: Optional[str] = None
    technical_specs: Optional[Dict[str, Any]] = None
    integration_plan: Optional[Dict[str, Any]] = None
    
    # Progress tracking
    stage_history: List[Dict[str, Any]] = None
    stakeholder_feedback: List[Dict[str, Any]] = None
    approval_notes: Optional[str] = None
    
    # Pipeline metadata
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    success_metrics: Optional[Dict[str, Any]] = None

@dataclass
class PipelineMetrics:
    """Innovation pipeline performance metrics"""
    total_innovations: int
    stage_distribution: Dict[str, int]
    approval_rate: float
    average_pipeline_time: float  # days
    completion_rate: float
    success_rate: float
    roi_estimate: float

class InnovationPipeline:
    """Innovation pipeline management system"""
    
    def __init__(self):
        self.innovations: Dict[str, FeatureInnovation] = {}
        self.pipeline_config = {
            "auto_approval_threshold": 85,  # Score above which features auto-advance
            "critical_review_threshold": 95,  # Score requiring executive review
            "pipeline_timeout_days": 30,  # Max days in pipeline before review
            "batch_handoff_size": 5  # Number of features to handoff at once
        }
        
        # Integration with production system
        self.production_integration_queue = []
        self.helios_coordination_active = False
        
    def add_innovation(self, innovation_data: Dict[str, Any]) -> str:
        """Add new innovation to pipeline"""
        innovation_id = str(uuid.uuid4())
        
        innovation = FeatureInnovation(
            id=innovation_id,
            name=innovation_data["name"],
            description=innovation_data["description"],
            category=innovation_data.get("category", "general"),
            source_agent=innovation_data["source_agent"],
            created_at=datetime.now(),
            current_stage=PipelineStage.IDEATION,
            approval_status=ApprovalStatus.PENDING,
            market_opportunity_score=innovation_data.get("market_opportunity_score", 50),
            competitive_advantage_score=innovation_data.get("competitive_advantage_score", 50),
            user_demand_score=innovation_data.get("user_demand_score", 50),
            implementation_complexity=innovation_data.get("implementation_complexity", "M"),
            stage_history=[],
            stakeholder_feedback=[]
        )
        
        # Initialize stage history
        innovation.stage_history.append({
            "stage": PipelineStage.IDEATION.value,
            "timestamp": datetime.now().isoformat(),
            "notes": "Innovation created and entered pipeline"
        })
        
        self.innovations[innovation_id] = innovation
        logger.info(f"Added innovation {innovation.name} to pipeline with ID {innovation_id}")
        
        return innovation_id
    
    def advance_innovation_stage(self, innovation_id: str, notes: Optional[str] = None) -> bool:
        """Advance innovation to next pipeline stage"""
        if innovation_id not in self.innovations:
            return False
        
        innovation = self.innovations[innovation_id]
        current_stage = innovation.current_stage
        
        # Define stage progression
        stage_flow = [
            PipelineStage.IDEATION,
            PipelineStage.VALIDATION,
            PipelineStage.PROTOTYPING,
            PipelineStage.APPROVAL,
            PipelineStage.HANDOFF,
            PipelineStage.INTEGRATION,
            PipelineStage.DEPLOYMENT,
            PipelineStage.MONITORING
        ]
        
        try:
            current_index = stage_flow.index(current_stage)
            if current_index < len(stage_flow) - 1:
                next_stage = stage_flow[current_index + 1]
                innovation.current_stage = next_stage
                
                # Record stage transition
                innovation.stage_history.append({
                    "stage": next_stage.value,
                    "timestamp": datetime.now().isoformat(),
                    "notes": notes or f"Advanced from {current_stage.value}"
                })
                
                logger.info(f"Advanced innovation {innovation.name} to {next_stage.value}")
                return True
            else:
                logger.warning(f"Innovation {innovation.name} already at final stage")
                return False
                
        except ValueError:
            logger.error(f"Invalid current stage for innovation {innovation_id}")
            return False
    
    def evaluate_innovation_approval(self, innovation_id: str) -> Dict[str, Any]:
        """Evaluate innovation for approval based on scores and criteria"""
        if innovation_id not in self.innovations:
            return {"error": "Innovation not found"}
        
        innovation = self.innovations[innovation_id]
        
        # Calculate composite score
        composite_score = (
            innovation.market_opportunity_score * 0.4 +
            innovation.competitive_advantage_score * 0.3 +
            innovation.user_demand_score * 0.3
        )
        
        # Determine approval recommendation
        if composite_score >= self.pipeline_config["critical_review_threshold"]:
            recommendation = "critical_executive_review"
        elif composite_score >= self.pipeline_config["auto_approval_threshold"]:
            recommendation = "auto_approve"
        elif composite_score >= 70:
            recommendation = "standard_review"
        else:
            recommendation = "needs_improvement"
        
        # Consider implementation complexity
        complexity_impact = {
            "S": 1.0,  # No impact
            "M": 0.95,  # 5% score reduction
            "L": 0.85,  # 15% score reduction
            "XL": 0.75  # 25% score reduction
        }
        
        adjusted_score = composite_score * complexity_impact.get(innovation.implementation_complexity, 0.9)
        
        return {
            "innovation_id": innovation_id,
            "composite_score": composite_score,
            "adjusted_score": adjusted_score,
            "recommendation": recommendation,
            "market_opportunity": innovation.market_opportunity_score,
            "competitive_advantage": innovation.competitive_advantage_score,
            "user_demand": innovation.user_demand_score,
            "implementation_complexity": innovation.implementation_complexity,
            "evaluation_timestamp": datetime.now().isoformat()
        }
    
    def set_approval_status(self, innovation_id: str, status: ApprovalStatus, notes: Optional[str] = None) -> bool:
        """Set approval status for innovation"""
        if innovation_id not in self.innovations:
            return False
        
        innovation = self.innovations[innovation_id]
        innovation.approval_status = status
        innovation.approval_notes = notes
        
        # Record approval decision
        innovation.stakeholder_feedback.append({
            "type": "approval_decision",
            "status": status.value,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        })
        
        # Auto-advance to next stage if approved
        if status == ApprovalStatus.APPROVED:
            self.advance_innovation_stage(innovation_id, "Approved for production handoff")
        
        logger.info(f"Set approval status for {innovation.name}: {status.value}")
        return True
    
    def prepare_production_handoff(self, innovation_id: str) -> Dict[str, Any]:
        """Prepare innovation for handoff to production system"""
        if innovation_id not in self.innovations:
            return {"error": "Innovation not found"}
        
        innovation = self.innovations[innovation_id]
        
        if innovation.approval_status != ApprovalStatus.APPROVED:
            return {"error": "Innovation not approved for production"}
        
        # Create handoff package
        handoff_package = {
            "innovation_id": innovation.id,
            "feature_name": innovation.name,
            "description": innovation.description,
            "category": innovation.category,
            "priority": self._calculate_priority(innovation),
            "business_case": {
                "market_opportunity": innovation.market_opportunity_score,
                "competitive_advantage": innovation.competitive_advantage_score,
                "user_demand": innovation.user_demand_score,
                "implementation_complexity": innovation.implementation_complexity
            },
            "technical_specifications": innovation.technical_specs or {},
            "integration_plan": innovation.integration_plan or {},
            "prototype_url": innovation.prototype_url,
            "success_metrics": innovation.success_metrics or {},
            "timeline_estimate": self._estimate_implementation_timeline(innovation),
            "handoff_timestamp": datetime.now().isoformat(),
            "source_agent": innovation.source_agent,
            "rd_contact": "apollo-rd-orchestrator"
        }
        
        # Add to production integration queue
        self.production_integration_queue.append(handoff_package)
        
        # Advance innovation stage
        self.advance_innovation_stage(innovation_id, "Prepared for production handoff")
        
        logger.info(f"Prepared innovation {innovation.name} for production handoff")
        return handoff_package
    
    def _calculate_priority(self, innovation: FeatureInnovation) -> str:
        """Calculate implementation priority based on scores"""
        composite_score = (
            innovation.market_opportunity_score * 0.4 +
            innovation.competitive_advantage_score * 0.3 +
            innovation.user_demand_score * 0.3
        )
        
        if composite_score >= 90:
            return "critical"
        elif composite_score >= 80:
            return "high"
        elif composite_score >= 70:
            return "medium"
        else:
            return "low"
    
    def _estimate_implementation_timeline(self, innovation: FeatureInnovation) -> Dict[str, Any]:
        """Estimate implementation timeline based on complexity"""
        complexity_timelines = {
            "S": {"weeks": 1, "description": "Simple feature, minimal integration"},
            "M": {"weeks": 3, "description": "Moderate feature, standard integration"},
            "L": {"weeks": 6, "description": "Complex feature, significant integration"},
            "XL": {"weeks": 10, "description": "Major feature, extensive integration"}
        }
        
        timeline = complexity_timelines.get(innovation.implementation_complexity, {"weeks": 3})
        
        return {
            "estimated_weeks": timeline["weeks"],
            "description": timeline["description"],
            "start_date_estimate": datetime.now().isoformat(),
            "completion_estimate": (datetime.now() + timedelta(weeks=timeline["weeks"])).isoformat()
        }
    
    async def coordinate_with_helios(self, handoff_package: Dict[str, Any]) -> bool:
        """Coordinate with Helios production orchestrator for feature integration"""
        try:
            # In production, this would integrate with the main agent system
            # For now, we'll simulate the coordination
            
            logger.info(f"Coordinating with Helios for feature: {handoff_package['feature_name']}")
            
            # Simulate handoff to production system
            coordination_result = {
                "handoff_accepted": True,
                "assigned_agents": ["hephaestus-frontend", "hephaestus-backend"],
                "integration_timeline": handoff_package["timeline_estimate"],
                "production_task_id": str(uuid.uuid4()),
                "coordinator": "helios-orchestrator"
            }
            
            # Update innovation status
            innovation_id = handoff_package["innovation_id"]
            if innovation_id in self.innovations:
                innovation = self.innovations[innovation_id]
                innovation.stakeholder_feedback.append({
                    "type": "production_handoff",
                    "result": coordination_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                self.advance_innovation_stage(innovation_id, "Handed off to production system")
            
            return True
            
        except Exception as e:
            logger.error(f"Error coordinating with Helios: {e}")
            return False
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        stage_counts = {}
        approval_counts = {}
        
        for innovation in self.innovations.values():
            stage = innovation.current_stage.value
            approval = innovation.approval_status.value
            
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            approval_counts[approval] = approval_counts.get(approval, 0) + 1
        
        # Calculate metrics
        total_innovations = len(self.innovations)
        approved_count = approval_counts.get("approved", 0)
        
        return {
            "total_innovations": total_innovations,
            "stage_distribution": stage_counts,
            "approval_distribution": approval_counts,
            "approval_rate": approved_count / total_innovations if total_innovations > 0 else 0,
            "production_queue_size": len(self.production_integration_queue),
            "helios_coordination_active": self.helios_coordination_active,
            "pipeline_health": self._assess_pipeline_health(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _assess_pipeline_health(self) -> str:
        """Assess overall pipeline health"""
        if not self.innovations:
            return "empty"
        
        # Check for stalled innovations
        stalled_count = 0
        for innovation in self.innovations.values():
            days_in_current_stage = (datetime.now() - innovation.created_at).days
            if days_in_current_stage > self.pipeline_config["pipeline_timeout_days"]:
                stalled_count += 1
        
        stall_rate = stalled_count / len(self.innovations)
        
        if stall_rate > 0.3:
            return "poor"
        elif stall_rate > 0.1:
            return "fair"
        else:
            return "good"
    
    def get_innovations_by_stage(self, stage: PipelineStage) -> List[Dict[str, Any]]:
        """Get innovations at specific pipeline stage"""
        innovations = [
            asdict(innovation) for innovation in self.innovations.values()
            if innovation.current_stage == stage
        ]
        
        # Convert datetime objects to ISO strings for JSON serialization
        for innovation in innovations:
            innovation["created_at"] = innovation["created_at"].isoformat() if isinstance(innovation["created_at"], datetime) else innovation["created_at"]
            if innovation.get("estimated_completion"):
                innovation["estimated_completion"] = innovation["estimated_completion"].isoformat() if isinstance(innovation["estimated_completion"], datetime) else innovation["estimated_completion"]
            if innovation.get("actual_completion"):
                innovation["actual_completion"] = innovation["actual_completion"].isoformat() if isinstance(innovation["actual_completion"], datetime) else innovation["actual_completion"]
        
        return innovations
    
    def get_ready_for_approval(self) -> List[Dict[str, Any]]:
        """Get innovations ready for stakeholder approval"""
        ready_innovations = []
        
        for innovation in self.innovations.values():
            if (innovation.current_stage == PipelineStage.APPROVAL and 
                innovation.approval_status == ApprovalStatus.PENDING):
                
                evaluation = self.evaluate_innovation_approval(innovation.id)
                innovation_data = asdict(innovation)
                innovation_data["evaluation"] = evaluation
                innovation_data["created_at"] = innovation.created_at.isoformat()
                
                ready_innovations.append(innovation_data)
        
        return ready_innovations
    
    def process_batch_handoffs(self) -> List[Dict[str, Any]]:
        """Process batch of innovations ready for production handoff"""
        handoff_results = []
        
        # Get approved innovations ready for handoff
        ready_for_handoff = [
            innovation for innovation in self.innovations.values()
            if (innovation.approval_status == ApprovalStatus.APPROVED and
                innovation.current_stage == PipelineStage.HANDOFF)
        ]
        
        # Process up to batch size
        batch_size = min(len(ready_for_handoff), self.pipeline_config["batch_handoff_size"])
        
        for i in range(batch_size):
            innovation = ready_for_handoff[i]
            handoff_package = self.prepare_production_handoff(innovation.id)
            handoff_results.append(handoff_package)
        
        return handoff_results

# Global innovation pipeline instance
innovation_pipeline = InnovationPipeline()