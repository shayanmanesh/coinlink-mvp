"""
Growth Scheduler System

Ultra-aggressive automated scheduling system for growth sprints.
Coordinates BD and Marketing agents, executes timed campaigns,
and maintains relentless growth momentum through systematic sprints.
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from croniter import croniter

from .growth_interface import GrowthInterface
from .growth_metrics import growth_metrics_tracker, GrowthMetrics
from .pipeline_orchestrator import PipelineOrchestrator

class SprintType(Enum):
    BD_BLITZ = "bd_blitz"
    MARKETING_CAMPAIGN = "marketing_campaign"
    LEAD_GENERATION = "lead_generation"
    DEAL_CLOSING = "deal_closing"
    COMPREHENSIVE = "comprehensive"
    OPTIMIZATION = "optimization"

class SprintIntensity(Enum):
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    ULTRA_AGGRESSIVE = "ultra_aggressive"
    MAXIMUM = "maximum"

@dataclass
class SprintSchedule:
    """Growth sprint scheduling configuration"""
    sprint_id: str
    sprint_type: SprintType
    intensity: SprintIntensity
    cron_expression: str  # e.g., "0 9 * * 1-5" for 9am weekdays
    duration_minutes: int
    target_agents: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    
    def calculate_next_execution(self) -> datetime:
        """Calculate next execution time based on cron expression"""
        cron = croniter(self.cron_expression, datetime.utcnow())
        return cron.get_next(datetime)

@dataclass
class SprintExecution:
    """Growth sprint execution record"""
    sprint_id: str
    execution_id: str
    sprint_type: SprintType
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "RUNNING"  # RUNNING, COMPLETED, FAILED, CANCELLED
    agents_deployed: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    metrics_captured: Optional[GrowthMetrics] = None
    
    @property
    def duration_minutes(self) -> float:
        """Calculate sprint duration in minutes"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return (datetime.utcnow() - self.start_time).total_seconds() / 60

class GrowthScheduler:
    """Ultra-aggressive automated growth sprint scheduler"""
    
    def __init__(self):
        self.growth_interface = GrowthInterface()
        self.orchestrator = PipelineOrchestrator()
        self.scheduled_sprints: Dict[str, SprintSchedule] = {}
        self.active_executions: Dict[str, SprintExecution] = {}
        self.execution_history: List[SprintExecution] = []
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
        # Initialize default sprint schedules
        self._initialize_default_schedules()
    
    def _initialize_default_schedules(self):
        """Initialize default ultra-aggressive sprint schedules"""
        
        # Daily BD Blitz - Every weekday at 9am
        self.scheduled_sprints["daily_bd_blitz"] = SprintSchedule(
            sprint_id="daily_bd_blitz",
            sprint_type=SprintType.BD_BLITZ,
            intensity=SprintIntensity.ULTRA_AGGRESSIVE,
            cron_expression="0 9 * * 1-5",  # 9am weekdays
            duration_minutes=240,  # 4 hours
            target_agents=["opportunity_scout", "lead_engagement", "deal_closer"],
            parameters={
                "prospecting_volume": 100,
                "engagement_intensity": "ultra_aggressive",
                "closing_focus": True
            }
        )
        
        # Marketing Campaign Blitz - 3x per week
        self.scheduled_sprints["marketing_blitz"] = SprintSchedule(
            sprint_id="marketing_blitz",
            sprint_type=SprintType.MARKETING_CAMPAIGN,
            intensity=SprintIntensity.AGGRESSIVE,
            cron_expression="0 10 * * 1,3,5",  # 10am Mon/Wed/Fri
            duration_minutes=180,  # 3 hours
            target_agents=["campaign_planner", "campaign_execution", "marketing_analytics"],
            parameters={
                "campaign_count": 5,
                "budget_acceleration": True,
                "optimization_intensity": "high"
            }
        )
        
        # Lead Generation Sprint - Daily at 8am
        self.scheduled_sprints["lead_generation_sprint"] = SprintSchedule(
            sprint_id="lead_generation_sprint", 
            sprint_type=SprintType.LEAD_GENERATION,
            intensity=SprintIntensity.ULTRA_AGGRESSIVE,
            cron_expression="0 8 * * *",  # 8am daily
            duration_minutes=120,  # 2 hours
            target_agents=["opportunity_scout", "content_creation", "campaign_execution"],
            parameters={
                "lead_target": 50,
                "content_volume": "high",
                "multi_channel": True
            }
        )
        
        # Deal Closing Power Hour - Twice daily
        self.scheduled_sprints["closing_power_hour"] = SprintSchedule(
            sprint_id="closing_power_hour",
            sprint_type=SprintType.DEAL_CLOSING,
            intensity=SprintIntensity.MAXIMUM,
            cron_expression="0 11,15 * * 1-5",  # 11am and 3pm weekdays
            duration_minutes=60,
            target_agents=["deal_closer", "partnership_negotiator"],
            parameters={
                "closing_techniques": "all",
                "urgency_level": "maximum",
                "revenue_focus": True
            }
        )
        
        # Comprehensive Weekly Sprint - Mondays
        self.scheduled_sprints["weekly_comprehensive"] = SprintSchedule(
            sprint_id="weekly_comprehensive",
            sprint_type=SprintType.COMPREHENSIVE,
            intensity=SprintIntensity.ULTRA_AGGRESSIVE,
            cron_expression="0 7 * * 1",  # 7am Mondays
            duration_minutes=480,  # 8 hours
            target_agents=["all"],
            parameters={
                "full_engagement": True,
                "weekly_targets": True,
                "comprehensive_optimization": True
            }
        )
        
        # Performance Optimization - Daily evening
        self.scheduled_sprints["optimization_sprint"] = SprintSchedule(
            sprint_id="optimization_sprint",
            sprint_type=SprintType.OPTIMIZATION,
            intensity=SprintIntensity.STANDARD,
            cron_expression="0 18 * * *",  # 6pm daily
            duration_minutes=30,
            target_agents=["marketing_analytics", "pipeline_orchestrator"],
            parameters={
                "metrics_analysis": True,
                "performance_optimization": True,
                "alert_generation": True
            }
        )
        
        # Calculate initial next execution times
        for sprint in self.scheduled_sprints.values():
            sprint.next_execution = sprint.calculate_next_execution()
    
    async def start_scheduler(self):
        """Start the automated growth scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self.logger.info("Starting ultra-aggressive growth scheduler")
        
        # Start the main scheduling loop
        await self._scheduler_loop()
    
    async def stop_scheduler(self):
        """Stop the automated growth scheduler"""
        self.is_running = False
        self.logger.info("Growth scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler event loop"""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Check for sprints ready to execute
                ready_sprints = [
                    sprint for sprint in self.scheduled_sprints.values()
                    if (sprint.is_active and 
                        sprint.next_execution and 
                        sprint.next_execution <= current_time)
                ]
                
                # Execute ready sprints
                for sprint in ready_sprints:
                    await self._execute_sprint(sprint)
                
                # Clean up completed executions
                await self._cleanup_completed_executions()
                
                # Sleep for 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _execute_sprint(self, sprint: SprintSchedule):
        """Execute a scheduled growth sprint"""
        execution_id = f"{sprint.sprint_id}_{int(datetime.utcnow().timestamp())}"
        
        execution = SprintExecution(
            sprint_id=sprint.sprint_id,
            execution_id=execution_id,
            sprint_type=sprint.sprint_type,
            start_time=datetime.utcnow()
        )
        
        self.active_executions[execution_id] = execution
        self.logger.info(f"Executing sprint: {sprint.sprint_id} with intensity {sprint.intensity.value}")
        
        try:
            # Execute sprint based on type
            if sprint.sprint_type == SprintType.BD_BLITZ:
                result = await self._execute_bd_blitz(sprint)
            elif sprint.sprint_type == SprintType.MARKETING_CAMPAIGN:
                result = await self._execute_marketing_campaign(sprint)
            elif sprint.sprint_type == SprintType.LEAD_GENERATION:
                result = await self._execute_lead_generation_sprint(sprint)
            elif sprint.sprint_type == SprintType.DEAL_CLOSING:
                result = await self._execute_deal_closing_sprint(sprint)
            elif sprint.sprint_type == SprintType.COMPREHENSIVE:
                result = await self._execute_comprehensive_sprint(sprint)
            elif sprint.sprint_type == SprintType.OPTIMIZATION:
                result = await self._execute_optimization_sprint(sprint)
            else:
                result = {"error": "Unknown sprint type"}
            
            execution.results = result
            execution.status = "COMPLETED"
            execution.end_time = datetime.utcnow()
            
            # Capture performance metrics
            execution.metrics_captured = await growth_metrics_tracker.capture_system_snapshot()
            
            self.logger.info(f"Sprint {sprint.sprint_id} completed successfully in {execution.duration_minutes:.1f} minutes")
            
        except Exception as e:
            execution.status = "FAILED"
            execution.end_time = datetime.utcnow()
            execution.results = {"error": str(e)}
            self.logger.error(f"Sprint {sprint.sprint_id} failed: {str(e)}")
        
        # Update sprint schedule
        sprint.last_execution = execution.start_time
        sprint.next_execution = sprint.calculate_next_execution()
        sprint.execution_count += 1
        
        # Move to history
        self.execution_history.append(execution)
        if execution_id in self.active_executions:
            del self.active_executions[execution_id]
    
    async def _execute_bd_blitz(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute BD blitz sprint"""
        results = {"sprint_type": "BD_BLITZ", "agents_executed": []}
        
        # Execute BD agents in parallel
        tasks = []
        
        # Market Intelligence
        if "all" in sprint.target_agents or "market_intelligence" in sprint.target_agents:
            tasks.append(self.growth_interface.invoke_agent(
                "market_intelligence",
                "execute_market_intelligence_sweep",
                {"intensity": sprint.intensity.value}
            ))
            results["agents_executed"].append("market_intelligence")
        
        # Opportunity Scout
        if "all" in sprint.target_agents or "opportunity_scout" in sprint.target_agents:
            tasks.append(self.growth_interface.invoke_agent(
                "opportunity_scout", 
                "execute_prospecting_blitz",
                {
                    "blitz_type": "comprehensive",
                    "prospecting_volume": sprint.parameters.get("prospecting_volume", 100),
                    "intensity": sprint.intensity.value
                }
            ))
            results["agents_executed"].append("opportunity_scout")
        
        # Lead Engagement
        if "all" in sprint.target_agents or "lead_engagement" in sprint.target_agents:
            tasks.append(self.growth_interface.invoke_agent(
                "lead_engagement",
                "execute_engagement_blitz", 
                {"intensity": sprint.parameters.get("engagement_intensity", "aggressive")}
            ))
            results["agents_executed"].append("lead_engagement")
        
        # Deal Closer
        if "all" in sprint.target_agents or "deal_closer" in sprint.target_agents:
            tasks.append(self.growth_interface.invoke_agent(
                "deal_closer",
                "execute_closing_blitz",
                {"closing_intensity": sprint.intensity.value}
            ))
            results["agents_executed"].append("deal_closer")
        
        # Execute all BD tasks in parallel
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            results["task_results"] = [
                result if not isinstance(result, Exception) else {"error": str(result)}
                for result in task_results
            ]
        
        return results
    
    async def _execute_marketing_campaign(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute marketing campaign sprint"""
        results = {"sprint_type": "MARKETING_CAMPAIGN", "agents_executed": []}
        
        tasks = []
        
        # Campaign Planner
        if "all" in sprint.target_agents or "campaign_planner" in sprint.target_agents:
            tasks.append(self.growth_interface.invoke_agent(
                "campaign_planner",
                "execute_campaign_planning_sprint",
                {"planning_intensity": sprint.intensity.value}
            ))
            results["agents_executed"].append("campaign_planner")
        
        # Campaign Execution
        if "all" in sprint.target_agents or "campaign_execution" in sprint.target_agents:
            tasks.append(self.growth_interface.invoke_agent(
                "campaign_execution",
                "execute_campaign_deployment_blitz",
                {
                    "deployment_type": "comprehensive",
                    "optimization_intensity": sprint.parameters.get("optimization_intensity", "high")
                }
            ))
            results["agents_executed"].append("campaign_execution")
        
        # Marketing Analytics
        if "all" in sprint.target_agents or "marketing_analytics" in sprint.target_agents:
            tasks.append(self.growth_interface.invoke_agent(
                "marketing_analytics",
                "execute_analytics_and_optimization_sprint",
                {"analysis_type": "comprehensive"}
            ))
            results["agents_executed"].append("marketing_analytics")
        
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            results["task_results"] = [
                result if not isinstance(result, Exception) else {"error": str(result)}
                for result in task_results
            ]
        
        return results
    
    async def _execute_lead_generation_sprint(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute lead generation focused sprint"""
        results = {"sprint_type": "LEAD_GENERATION", "lead_target": sprint.parameters.get("lead_target", 50)}
        
        # Coordinate BD and Marketing for lead generation
        tasks = [
            self.growth_interface.invoke_agent(
                "opportunity_scout",
                "execute_prospecting_blitz",
                {"prospecting_volume": sprint.parameters.get("lead_target", 50)}
            ),
            self.growth_interface.invoke_agent(
                "content_creation", 
                "execute_content_production_sprint",
                {"production_volume": sprint.parameters.get("content_volume", "high")}
            ),
            self.growth_interface.invoke_agent(
                "campaign_execution",
                "execute_campaign_deployment_blitz",
                {"deployment_type": "lead_generation"}
            )
        ]
        
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        results["task_results"] = task_results
        
        return results
    
    async def _execute_deal_closing_sprint(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute deal closing focused sprint"""
        results = {"sprint_type": "DEAL_CLOSING", "urgency_level": sprint.parameters.get("urgency_level", "maximum")}
        
        # Focus on closing activities
        tasks = [
            self.growth_interface.invoke_agent(
                "deal_closer",
                "execute_closing_blitz", 
                {
                    "closing_intensity": sprint.intensity.value,
                    "revenue_focus": sprint.parameters.get("revenue_focus", True)
                }
            ),
            self.growth_interface.invoke_agent(
                "partnership_negotiator",
                "execute_negotiation_blitz",
                {"urgency_level": sprint.parameters.get("urgency_level", "high")}
            )
        ]
        
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        results["task_results"] = task_results
        
        return results
    
    async def _execute_comprehensive_sprint(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute comprehensive all-hands growth sprint"""
        results = {"sprint_type": "COMPREHENSIVE", "full_system_engagement": True}
        
        # Execute all agents simultaneously
        all_agent_tasks = []
        
        # BD Cluster
        bd_agents = ["market_intelligence", "opportunity_scout", "lead_engagement", "partnership_negotiator", "deal_closer"]
        for agent in bd_agents:
            all_agent_tasks.append(self.growth_interface.invoke_agent(
                agent,
                f"execute_{agent.replace('_', '_').split('_')[-1]}_blitz",
                {"intensity": "ultra_aggressive"}
            ))
        
        # Marketing Cluster  
        marketing_agents = ["marketing_strategy", "campaign_planner", "content_creation", "campaign_execution", "marketing_analytics"]
        for agent in marketing_agents:
            method_name = f"execute_{agent.replace('_', '_').split('_')[-1]}_sprint"
            if agent == "marketing_strategy":
                method_name = "develop_comprehensive_marketing_strategy"
            elif agent == "content_creation":
                method_name = "execute_content_production_sprint"
            elif agent == "campaign_execution":
                method_name = "execute_campaign_deployment_blitz"
            elif agent == "marketing_analytics":
                method_name = "execute_analytics_and_optimization_sprint"
            
            all_agent_tasks.append(self.growth_interface.invoke_agent(
                agent,
                method_name,
                {"intensity": "comprehensive"}
            ))
        
        # Execute all agents in parallel
        task_results = await asyncio.gather(*all_agent_tasks, return_exceptions=True)
        results["task_results"] = task_results
        results["agents_deployed"] = bd_agents + marketing_agents
        
        return results
    
    async def _execute_optimization_sprint(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute performance optimization sprint"""
        results = {"sprint_type": "OPTIMIZATION"}
        
        # Generate performance analysis and recommendations
        dashboard = await growth_metrics_tracker.get_performance_dashboard()
        alerts = await growth_metrics_tracker.generate_performance_alerts()
        recommendations = await growth_metrics_tracker.optimize_performance_recommendations()
        
        results.update({
            "performance_dashboard": dashboard,
            "performance_alerts": alerts,
            "optimization_recommendations": recommendations,
            "metrics_snapshot": await growth_metrics_tracker.capture_system_snapshot()
        })
        
        return results
    
    async def _cleanup_completed_executions(self):
        """Clean up old completed executions"""
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    async def add_custom_sprint(self, sprint_schedule: SprintSchedule):
        """Add a custom sprint schedule"""
        sprint_schedule.next_execution = sprint_schedule.calculate_next_execution()
        self.scheduled_sprints[sprint_schedule.sprint_id] = sprint_schedule
        self.logger.info(f"Added custom sprint: {sprint_schedule.sprint_id}")
    
    async def remove_sprint(self, sprint_id: str) -> bool:
        """Remove a sprint schedule"""
        if sprint_id in self.scheduled_sprints:
            del self.scheduled_sprints[sprint_id]
            self.logger.info(f"Removed sprint: {sprint_id}")
            return True
        return False
    
    async def get_sprint_status(self) -> Dict[str, Any]:
        """Get comprehensive sprint scheduler status"""
        return {
            "scheduler_running": self.is_running,
            "scheduled_sprints": len(self.scheduled_sprints),
            "active_executions": len(self.active_executions),
            "total_executions": len(self.execution_history),
            "next_sprint": min(
                (sprint.next_execution for sprint in self.scheduled_sprints.values() if sprint.next_execution),
                default=None
            ),
            "sprint_schedules": [
                {
                    "sprint_id": sprint.sprint_id,
                    "sprint_type": sprint.sprint_type.value,
                    "intensity": sprint.intensity.value,
                    "next_execution": sprint.next_execution.isoformat() if sprint.next_execution else None,
                    "execution_count": sprint.execution_count,
                    "is_active": sprint.is_active
                }
                for sprint in self.scheduled_sprints.values()
            ]
        }

# Global scheduler instance
growth_scheduler = GrowthScheduler()