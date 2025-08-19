"""
Helios Master Orchestrator - Strategic coordinator for dual-agent swarms
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from queue import PriorityQueue
import time

from ..base import BaseAgent, AgentRole, AgentDomain, AgentTask, AgentSwarm
from ..kpi_tracker import kpi_tracker
from ..self_improvement import self_improvement_engine

logger = logging.getLogger(__name__)

@dataclass
class OptimizationPriority:
    """Represents optimization priorities for both swarms"""
    frontend: List[Dict[str, Any]]
    backend: List[Dict[str, Any]]
    urgency: int  # 1=critical, 2=high, 3=medium, 4=low
    expected_impact: float

class HeliosMasterOrchestrator(BaseAgent):
    """Master orchestrator coordinating frontend and backend swarms"""
    
    def __init__(self):
        super().__init__(
            name="helios-master",
            role=AgentRole.ORCHESTRATOR,
            domain=AgentDomain.FULLSTACK,
            tools=["Task", "TodoWrite", "Read", "Write", "WebSearch", "LS"]
        )
        
        self.frontend_swarm: Optional[AgentSwarm] = None
        self.backend_swarm: Optional[AgentSwarm] = None
        self.optimization_cycle_duration = 300  # 5 minutes
        self.emergency_threshold = 0.5  # Health score below which emergency mode activates
        self.optimization_queue = PriorityQueue()
        self.last_health_check = datetime.now()
        self.performance_baseline: Dict[str, float] = {}
        
        # Strategic parameters
        self.max_concurrent_optimizations = 4
        self.optimization_cooldown = 60  # seconds between optimizations of same type
        self.last_optimizations: Dict[str, datetime] = {}
        
    def set_swarms(self, frontend_swarm: AgentSwarm, backend_swarm: AgentSwarm):
        """Set the frontend and backend swarms to coordinate"""
        self.frontend_swarm = frontend_swarm
        self.backend_swarm = backend_swarm
        logger.info("Swarms assigned to Helios orchestrator")
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process orchestration tasks"""
        
        task_type = task.parameters.get("type", "optimization")
        
        if task_type == "optimization":
            return await self.orchestrate_optimization_cycle()
        elif task_type == "emergency":
            return await self.handle_emergency_situation()
        elif task_type == "analysis":
            return await self.generate_performance_analysis()
        elif task_type == "strategic_planning":
            return await self.create_strategic_plan()
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def background_work(self):
        """Continuous orchestration work"""
        # Check if it's time for a new optimization cycle
        time_since_last = (datetime.now() - self.last_health_check).total_seconds()
        
        if time_since_last >= self.optimization_cycle_duration:
            await self.orchestrate_optimization_cycle()
            self.last_health_check = datetime.now()
    
    async def orchestrate_optimization_cycle(self) -> Dict[str, Any]:
        """Main orchestration cycle"""
        logger.info("Starting optimization cycle")
        
        try:
            # 1. Collect current system metrics
            metrics = await self.collect_system_metrics()
            
            # 2. Analyze bottlenecks and priorities
            bottlenecks = await self.analyze_bottlenecks(metrics)
            
            # 3. Create optimization priorities
            priorities = await self.calculate_optimization_priorities(bottlenecks)
            
            # 4. Check for emergency situations
            health_score = kpi_tracker.calculate_overall_health_score()
            if health_score < self.emergency_threshold * 100:
                await self.handle_emergency_situation()
                return {"status": "emergency_handled", "health_score": health_score}
            
            # 5. Dispatch optimization tasks to both swarms concurrently
            optimization_results = await self.dispatch_concurrent_optimizations(priorities)
            
            # 6. Verify improvements
            improvements = await self.verify_optimizations(metrics, optimization_results)
            
            # 7. Learn from results
            await self.learn_from_results(improvements)
            
            # 8. Generate stakeholder report
            report = await self.generate_cycle_report(metrics, improvements)
            
            return {
                "status": "cycle_completed",
                "health_score": health_score,
                "optimizations_performed": len(optimization_results),
                "improvements": improvements,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Error in orchestration cycle: {e}")
            return {"status": "cycle_failed", "error": str(e)}
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        
        # Get KPI metrics
        kpi_summary = kpi_tracker.get_metrics_summary()
        
        # Get agent performance
        agent_stats = {}
        if self.frontend_swarm:
            agent_stats["frontend"] = self.frontend_swarm.get_swarm_status()
        if self.backend_swarm:
            agent_stats["backend"] = self.backend_swarm.get_swarm_status()
        
        # Get learning engine stats
        learning_stats = self_improvement_engine.get_learning_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "kpis": kpi_summary,
            "agents": agent_stats,
            "learning": learning_stats,
            "health_score": kpi_tracker.calculate_overall_health_score()
        }
    
    async def analyze_bottlenecks(self, metrics: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Analyze system bottlenecks and performance issues"""
        
        frontend_issues = []
        backend_issues = []
        
        # Analyze frontend metrics
        frontend_metrics = metrics["kpis"]["categories"].get("frontend", {})
        for metric_name, metric_data in frontend_metrics.items():
            if not metric_data["meeting_target"]:
                severity = "critical" if metric_data["priority"] == 1 else "high"
                issue = {
                    "metric": metric_name,
                    "current": metric_data["current"],
                    "target": metric_data["target"],
                    "severity": severity,
                    "trend": metric_data["trend"]
                }
                frontend_issues.append(issue)
        
        # Analyze backend metrics
        backend_metrics = metrics["kpis"]["categories"].get("backend", {})
        for metric_name, metric_data in backend_metrics.items():
            if not metric_data["meeting_target"]:
                severity = "critical" if metric_data["priority"] == 1 else "high"
                issue = {
                    "metric": metric_name,
                    "current": metric_data["current"],
                    "target": metric_data["target"],
                    "severity": severity,
                    "trend": metric_data["trend"]
                }
                backend_issues.append(issue)
        
        # Analyze business metrics for strategic direction
        business_metrics = metrics["kpis"]["categories"].get("business", {})
        business_issues = []
        for metric_name, metric_data in business_metrics.items():
            if not metric_data["meeting_target"]:
                issue = {
                    "metric": metric_name,
                    "current": metric_data["current"],
                    "target": metric_data["target"],
                    "priority": metric_data["priority"]
                }
                business_issues.append(issue)
        
        return {
            "frontend": frontend_issues,
            "backend": backend_issues,
            "business": business_issues
        }
    
    async def calculate_optimization_priorities(self, bottlenecks: Dict[str, List[Dict]]) -> OptimizationPriority:
        """Calculate optimization priorities based on bottlenecks and business impact"""
        
        frontend_priorities = []
        backend_priorities = []
        
        # Calculate urgency based on severity and trend
        urgency_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        
        # Prioritize frontend optimizations
        for issue in bottlenecks["frontend"]:
            urgency = urgency_map.get(issue["severity"], 3)
            
            # Increase urgency for declining trends
            if issue["trend"] == "declining":
                urgency = max(1, urgency - 1)
            
            priority = {
                "type": self.map_metric_to_optimization_type(issue["metric"]),
                "metric": issue["metric"],
                "urgency": urgency,
                "target_improvement": self.calculate_target_improvement(issue),
                "estimated_impact": self.estimate_optimization_impact(issue)
            }
            frontend_priorities.append(priority)
        
        # Prioritize backend optimizations
        for issue in bottlenecks["backend"]:
            urgency = urgency_map.get(issue["severity"], 3)
            
            if issue["trend"] == "declining":
                urgency = max(1, urgency - 1)
            
            priority = {
                "type": self.map_metric_to_optimization_type(issue["metric"]),
                "metric": issue["metric"],
                "urgency": urgency,
                "target_improvement": self.calculate_target_improvement(issue),
                "estimated_impact": self.estimate_optimization_impact(issue)
            }
            backend_priorities.append(priority)
        
        # Sort by urgency and impact
        frontend_priorities.sort(key=lambda x: (x["urgency"], -x["estimated_impact"]))
        backend_priorities.sort(key=lambda x: (x["urgency"], -x["estimated_impact"]))
        
        # Calculate overall urgency
        all_urgencies = [p["urgency"] for p in frontend_priorities + backend_priorities]
        overall_urgency = min(all_urgencies) if all_urgencies else 4
        
        # Calculate expected impact
        total_impact = sum(p["estimated_impact"] for p in frontend_priorities + backend_priorities)
        
        return OptimizationPriority(
            frontend=frontend_priorities[:self.max_concurrent_optimizations],
            backend=backend_priorities[:self.max_concurrent_optimizations],
            urgency=overall_urgency,
            expected_impact=total_impact
        )
    
    def map_metric_to_optimization_type(self, metric_name: str) -> str:
        """Map KPI metrics to optimization types"""
        
        optimization_map = {
            # Frontend optimizations
            "chat_response_time": "chat_interface_optimization",
            "prompt_feed_refresh": "prompt_feed_optimization",
            "ui_interaction_lag": "ui_responsiveness_optimization",
            "message_render_time": "message_rendering_optimization",
            "websocket_latency": "websocket_optimization",
            
            # Backend optimizations
            "api_response_time": "api_optimization",
            "redis_cache_hit": "cache_optimization",
            "websocket_throughput": "websocket_scaling_optimization",
            "report_generation": "report_generation_optimization",
            "sentiment_analysis": "sentiment_processing_optimization"
        }
        
        return optimization_map.get(metric_name, "general_optimization")
    
    def calculate_target_improvement(self, issue: Dict) -> float:
        """Calculate target improvement percentage"""
        current = issue["current"]
        target = issue["target"]
        
        if current <= 0:
            return 50.0  # Default 50% improvement target
        
        # For "lower is better" metrics
        if issue["metric"] in ["chat_response_time", "api_response_time", "ui_interaction_lag"]:
            return ((current - target) / current) * 100
        else:
            # For "higher is better" metrics
            return ((target - current) / current) * 100 if current > 0 else 50.0
    
    def estimate_optimization_impact(self, issue: Dict) -> float:
        """Estimate business impact of fixing this issue"""
        
        # Impact scoring based on metric type and priority
        base_impact = {
            1: 100,  # High priority metrics
            2: 60,   # Medium priority metrics
            3: 30    # Low priority metrics
        }.get(issue.get("priority", 2), 30)
        
        # Boost impact for critical user-facing metrics
        user_facing_metrics = [
            "chat_response_time", "ui_interaction_lag", "message_render_time",
            "api_response_time", "websocket_latency"
        ]
        
        if issue["metric"] in user_facing_metrics:
            base_impact *= 1.5
        
        # Boost impact for severely degraded metrics
        severity_multiplier = {
            "critical": 2.0,
            "high": 1.5,
            "medium": 1.0,
            "low": 0.7
        }.get(issue.get("severity", "medium"), 1.0)
        
        return base_impact * severity_multiplier
    
    async def dispatch_concurrent_optimizations(self, priorities: OptimizationPriority) -> List[Dict[str, Any]]:
        """Dispatch optimization tasks to both swarms concurrently"""
        
        optimization_tasks = []
        
        # Create frontend optimization tasks
        for priority in priorities.frontend:
            if self.can_perform_optimization(priority["type"]):
                task = AgentTask(
                    id=f"frontend_{priority['type']}_{int(time.time())}",
                    type=priority["type"],
                    priority=priority["urgency"],
                    description=f"Optimize {priority['metric']}",
                    parameters=priority
                )
                optimization_tasks.append(("frontend", task))
        
        # Create backend optimization tasks
        for priority in priorities.backend:
            if self.can_perform_optimization(priority["type"]):
                task = AgentTask(
                    id=f"backend_{priority['type']}_{int(time.time())}",
                    type=priority["type"],
                    priority=priority["urgency"],
                    description=f"Optimize {priority['metric']}",
                    parameters=priority
                )
                optimization_tasks.append(("backend", task))
        
        # Dispatch tasks concurrently
        results = []
        if optimization_tasks:
            dispatch_results = await asyncio.gather(
                *[self.dispatch_task_to_swarm(swarm_type, task) 
                  for swarm_type, task in optimization_tasks],
                return_exceptions=True
            )
            
            for i, result in enumerate(dispatch_results):
                swarm_type, task = optimization_tasks[i]
                if isinstance(result, Exception):
                    logger.error(f"Error dispatching {task.type} to {swarm_type}: {result}")
                    results.append({
                        "task_id": task.id,
                        "type": task.type,
                        "swarm": swarm_type,
                        "status": "failed",
                        "error": str(result)
                    })
                else:
                    results.append({
                        "task_id": task.id,
                        "type": task.type,
                        "swarm": swarm_type,
                        "status": "completed",
                        "result": result
                    })
        
        return results
    
    def can_perform_optimization(self, optimization_type: str) -> bool:
        """Check if optimization can be performed (cooldown check)"""
        
        if optimization_type in self.last_optimizations:
            time_since_last = (datetime.now() - self.last_optimizations[optimization_type]).total_seconds()
            if time_since_last < self.optimization_cooldown:
                return False
        
        return True
    
    async def dispatch_task_to_swarm(self, swarm_type: str, task: AgentTask) -> Dict[str, Any]:
        """Dispatch a task to the appropriate swarm"""
        
        # Record optimization attempt
        self.last_optimizations[task.type] = datetime.now()
        
        if swarm_type == "frontend" and self.frontend_swarm:
            # Find appropriate agent in frontend swarm
            await self.frontend_swarm.assign_task_to_role(AgentRole.BUILDER, task)
        elif swarm_type == "backend" and self.backend_swarm:
            # Find appropriate agent in backend swarm
            await self.backend_swarm.assign_task_to_role(AgentRole.BUILDER, task)
        else:
            raise ValueError(f"Cannot dispatch to {swarm_type} swarm")
        
        # Wait for task completion (with timeout)
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while task.completed_at is None and task.error is None:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task.id} timed out")
            await asyncio.sleep(1)
        
        if task.error:
            raise Exception(f"Task failed: {task.error}")
        
        return task.result
    
    async def verify_optimizations(self, 
                                 baseline_metrics: Dict[str, Any], 
                                 optimization_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify that optimizations actually improved performance"""
        
        # Wait a bit for changes to take effect
        await asyncio.sleep(30)
        
        # Collect new metrics
        new_metrics = await self.collect_system_metrics()
        
        # Compare metrics
        improvements = {}
        regressions = {}
        
        # Compare KPI metrics
        baseline_kpis = baseline_metrics["kpis"]["categories"]
        new_kpis = new_metrics["kpis"]["categories"]
        
        for category in ["frontend", "backend", "business"]:
            if category in baseline_kpis and category in new_kpis:
                for metric_name in baseline_kpis[category]:
                    if metric_name in new_kpis[category]:
                        old_value = baseline_kpis[category][metric_name]["current"]
                        new_value = new_kpis[category][metric_name]["current"]
                        
                        if old_value > 0:
                            change_percent = ((new_value - old_value) / old_value) * 100
                            
                            # For "lower is better" metrics, negative change is improvement
                            if metric_name in ["chat_response_time", "api_response_time", "ui_interaction_lag"]:
                                if change_percent < -5:  # 5% improvement threshold
                                    improvements[metric_name] = -change_percent
                                elif change_percent > 5:  # 5% regression threshold
                                    regressions[metric_name] = change_percent
                            else:
                                # For "higher is better" metrics, positive change is improvement
                                if change_percent > 5:
                                    improvements[metric_name] = change_percent
                                elif change_percent < -5:
                                    regressions[metric_name] = -change_percent
        
        # Calculate overall health score change
        old_health = baseline_metrics["health_score"]
        new_health = new_metrics["health_score"]
        health_change = new_health - old_health
        
        return {
            "improvements": improvements,
            "regressions": regressions,
            "health_score_change": health_change,
            "successful_optimizations": len([r for r in optimization_results if r["status"] == "completed"]),
            "failed_optimizations": len([r for r in optimization_results if r["status"] == "failed"])
        }
    
    async def learn_from_results(self, improvements: Dict[str, Any]):
        """Learn from optimization results"""
        
        # Record learning points for each optimization
        for optimization in improvements.get("optimization_results", []):
            outcome = "success" if optimization["status"] == "completed" else "failure"
            
            # Extract performance deltas
            performance_delta = {}
            if "improvements" in improvements:
                for metric, improvement in improvements["improvements"].items():
                    performance_delta[metric] = improvement
            
            # Record learning point
            self_improvement_engine.record_learning_point(
                agent_name=self.name,
                task_type=optimization["type"],
                parameters=optimization.get("parameters", {}),
                outcome=outcome,
                performance_delta=performance_delta,
                execution_time=1.0,  # Placeholder
                context={"swarm": optimization.get("swarm", "unknown")}
            )
    
    async def handle_emergency_situation(self) -> Dict[str, Any]:
        """Handle emergency situations with critical performance issues"""
        
        logger.critical("Emergency situation detected - initiating emergency protocols")
        
        # Get current metrics
        metrics = await self.collect_system_metrics()
        health_score = metrics["health_score"]
        
        # Identify critical issues
        critical_issues = []
        for category in ["frontend", "backend"]:
            category_metrics = metrics["kpis"]["categories"].get(category, {})
            for metric_name, metric_data in category_metrics.items():
                if metric_data["priority"] == 1 and not metric_data["meeting_target"]:
                    critical_issues.append({
                        "category": category,
                        "metric": metric_name,
                        "current": metric_data["current"],
                        "target": metric_data["target"]
                    })
        
        # Implement emergency optimizations
        emergency_tasks = []
        for issue in critical_issues[:3]:  # Limit to top 3 critical issues
            task = AgentTask(
                id=f"emergency_{issue['metric']}_{int(time.time())}",
                type="emergency_optimization",
                priority=1,
                description=f"Emergency optimization for {issue['metric']}",
                parameters={
                    "metric": issue["metric"],
                    "target": issue["target"],
                    "emergency": True
                }
            )
            emergency_tasks.append((issue["category"], task))
        
        # Execute emergency optimizations
        results = await asyncio.gather(
            *[self.dispatch_task_to_swarm(category, task) 
              for category, task in emergency_tasks],
            return_exceptions=True
        )
        
        return {
            "status": "emergency_protocols_executed",
            "initial_health_score": health_score,
            "critical_issues_addressed": len(emergency_tasks),
            "emergency_results": results
        }
    
    async def generate_cycle_report(self, 
                                  metrics: Dict[str, Any], 
                                  improvements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive cycle report for stakeholders"""
        
        return {
            "cycle_timestamp": datetime.now().isoformat(),
            "system_health": {
                "current_score": metrics["health_score"],
                "change": improvements.get("health_score_change", 0),
                "status": "healthy" if metrics["health_score"] > 70 else "needs_attention"
            },
            "optimizations_performed": {
                "successful": improvements.get("successful_optimizations", 0),
                "failed": improvements.get("failed_optimizations", 0),
                "total": improvements.get("successful_optimizations", 0) + improvements.get("failed_optimizations", 0)
            },
            "performance_improvements": improvements.get("improvements", {}),
            "performance_regressions": improvements.get("regressions", {}),
            "kpi_summary": {
                "frontend_health": self.calculate_category_health(metrics["kpis"]["categories"].get("frontend", {})),
                "backend_health": self.calculate_category_health(metrics["kpis"]["categories"].get("backend", {})),
                "business_health": self.calculate_category_health(metrics["kpis"]["categories"].get("business", {}))
            },
            "agent_performance": {
                "frontend_swarm": self.frontend_swarm.get_swarm_status() if self.frontend_swarm else None,
                "backend_swarm": self.backend_swarm.get_swarm_status() if self.backend_swarm else None
            },
            "learning_progress": self_improvement_engine.get_learning_stats(),
            "next_cycle": (datetime.now() + timedelta(seconds=self.optimization_cycle_duration)).isoformat()
        }
    
    def calculate_category_health(self, category_metrics: Dict[str, Any]) -> float:
        """Calculate health score for a metric category"""
        if not category_metrics:
            return 100.0
        
        meeting_target = sum(1 for m in category_metrics.values() if m.get("meeting_target", False))
        total = len(category_metrics)
        
        return (meeting_target / total) * 100 if total > 0 else 100.0
    
    async def create_strategic_plan(self) -> Dict[str, Any]:
        """Create strategic optimization plan based on learning"""
        
        # Get recent learning data
        learning_stats = self_improvement_engine.get_learning_stats()
        
        # Get current metrics
        metrics = await self.collect_system_metrics()
        
        # Identify strategic opportunities
        opportunities = []
        
        # Analyze patterns for strategic insights
        for agent_name, agent_stats in learning_stats["agent_stats"].items():
            if agent_stats["success_rate"] < 0.8:
                opportunities.append({
                    "type": "agent_improvement",
                    "target": agent_name,
                    "current_success_rate": agent_stats["success_rate"],
                    "recommendation": "Focus on improving agent training and task assignment"
                })
        
        # Analyze business metrics for strategic direction
        business_metrics = metrics["kpis"]["categories"].get("business", {})
        for metric_name, metric_data in business_metrics.items():
            if not metric_data["meeting_target"]:
                opportunities.append({
                    "type": "business_optimization",
                    "target": metric_name,
                    "current": metric_data["current"],
                    "target": metric_data["target"],
                    "recommendation": f"Strategic focus needed on {metric_name}"
                })
        
        return {
            "strategic_plan_created": datetime.now().isoformat(),
            "planning_horizon": "7_days",
            "opportunities": opportunities,
            "recommended_focus_areas": [
                "chat_interface_intelligence",
                "prompt_feed_optimization", 
                "ai_report_generation"
            ],
            "success_metrics": {
                "target_health_score": 85,
                "target_user_retention": 50,
                "target_engagement_increase": 100
            }
        }