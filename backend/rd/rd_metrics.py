"""
R&D Metrics and KPI Tracking System
Comprehensive performance monitoring for innovation department
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import statistics

logger = logging.getLogger(__name__)

@dataclass
class AgentPerformanceMetrics:
    """Individual agent performance metrics"""
    agent_name: str
    specialization: str
    total_tasks: int = 0
    completed_tasks: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    innovation_contributions: int = 0
    quality_score: float = 0.0
    last_active: Optional[datetime] = None

@dataclass
class InnovationCycleMetrics:
    """Weekly innovation cycle metrics"""
    cycle_id: str
    week_start: datetime
    week_end: datetime
    
    # Intelligence metrics
    competitors_analyzed: int = 0
    research_papers_reviewed: int = 0
    user_feedback_processed: int = 0
    
    # Innovation metrics
    features_ideated: int = 0
    prototypes_created: int = 0
    validations_completed: int = 0
    
    # Pipeline metrics
    innovations_approved: int = 0
    handoffs_to_production: int = 0
    cycle_completion_rate: float = 0.0
    
    # Strategic metrics
    competitive_threats_identified: int = 0
    market_opportunities_discovered: int = 0
    strategic_recommendations: int = 0

@dataclass
class ROIMetrics:
    """Return on investment metrics for R&D"""
    features_implemented: int = 0
    user_engagement_impact: float = 0.0
    revenue_impact_estimate: float = 0.0
    cost_savings_estimate: float = 0.0
    competitive_advantages_gained: int = 0
    market_share_impact: float = 0.0

class RDMetricsTracker:
    """Comprehensive R&D performance tracking system"""
    
    def __init__(self):
        # Agent performance tracking
        self.agent_metrics: Dict[str, AgentPerformanceMetrics] = {}
        
        # Innovation cycle tracking
        self.cycle_metrics: Dict[str, InnovationCycleMetrics] = {}
        self.current_cycle_id: Optional[str] = None
        
        # Historical data
        self.metrics_history: deque = deque(maxlen=52)  # 1 year of weekly data
        self.daily_snapshots: deque = deque(maxlen=90)  # 3 months of daily data
        
        # ROI and business impact
        self.roi_metrics = ROIMetrics()
        
        # Performance targets
        self.targets = {
            "features_ideated_per_week": 10,
            "research_papers_per_week": 20,
            "competitive_insights_per_week": 5,
            "prototype_success_rate": 0.8,
            "approval_rate": 0.6,
            "innovation_cycle_completion": 0.9,
            "agent_utilization_rate": 0.75,
            "stakeholder_satisfaction": 0.85
        }
        
        # Real-time metrics
        self.real_time_metrics = {
            "active_tasks": 0,
            "completed_today": 0,
            "innovations_in_pipeline": 0,
            "critical_alerts": 0
        }
    
    def initialize_agent_metrics(self, agent_name: str, specialization: str):
        """Initialize metrics for a new agent"""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentPerformanceMetrics(
                agent_name=agent_name,
                specialization=specialization
            )
            logger.info(f"Initialized metrics for agent {agent_name}")
    
    def record_agent_task(self, agent_name: str, task_type: str, success: bool, 
                         response_time: float, quality_score: float = 0.0):
        """Record agent task completion"""
        if agent_name not in self.agent_metrics:
            self.initialize_agent_metrics(agent_name, "unknown")
        
        metrics = self.agent_metrics[agent_name]
        metrics.total_tasks += 1
        metrics.last_active = datetime.now()
        
        if success:
            metrics.completed_tasks += 1
        
        # Update success rate
        metrics.success_rate = metrics.completed_tasks / metrics.total_tasks
        
        # Update average response time (exponential moving average)
        if metrics.total_tasks == 1:
            metrics.average_response_time = response_time
        else:
            alpha = 0.1
            metrics.average_response_time = (
                alpha * response_time + 
                (1 - alpha) * metrics.average_response_time
            )
        
        # Update quality score
        if quality_score > 0:
            if metrics.total_tasks == 1:
                metrics.quality_score = quality_score
            else:
                metrics.quality_score = (
                    alpha * quality_score + 
                    (1 - alpha) * metrics.quality_score
                )
        
        # Track innovation contributions
        if task_type in ["feature_ideation", "prototype_creation", "strategic_analysis"]:
            metrics.innovation_contributions += 1
        
        logger.debug(f"Recorded task for {agent_name}: success={success}, time={response_time}")
    
    def start_innovation_cycle(self, cycle_id: str) -> InnovationCycleMetrics:
        """Start tracking a new innovation cycle"""
        week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        cycle_metrics = InnovationCycleMetrics(
            cycle_id=cycle_id,
            week_start=week_start,
            week_end=week_end
        )
        
        self.cycle_metrics[cycle_id] = cycle_metrics
        self.current_cycle_id = cycle_id
        
        logger.info(f"Started tracking innovation cycle {cycle_id}")
        return cycle_metrics
    
    def update_cycle_metrics(self, metric_type: str, value: int = 1):
        """Update current cycle metrics"""
        if not self.current_cycle_id or self.current_cycle_id not in self.cycle_metrics:
            return
        
        cycle = self.cycle_metrics[self.current_cycle_id]
        
        if hasattr(cycle, metric_type):
            current_value = getattr(cycle, metric_type)
            setattr(cycle, metric_type, current_value + value)
            logger.debug(f"Updated cycle metric {metric_type}: +{value}")
    
    def complete_innovation_cycle(self, cycle_id: str = None) -> Dict[str, Any]:
        """Complete and analyze innovation cycle"""
        cycle_id = cycle_id or self.current_cycle_id
        if not cycle_id or cycle_id not in self.cycle_metrics:
            return {"error": "Cycle not found"}
        
        cycle = self.cycle_metrics[cycle_id]
        
        # Calculate completion rate
        total_planned_activities = 10  # Base number of planned activities per cycle
        total_completed = (
            cycle.competitors_analyzed +
            cycle.research_papers_reviewed +
            cycle.features_ideated +
            cycle.prototypes_created +
            cycle.validations_completed
        )
        
        cycle.cycle_completion_rate = min(1.0, total_completed / total_planned_activities)
        
        # Archive cycle metrics
        self.metrics_history.append({
            "cycle_id": cycle_id,
            "metrics": asdict(cycle),
            "completion_date": datetime.now().isoformat()
        })
        
        # Reset current cycle
        self.current_cycle_id = None
        
        logger.info(f"Completed innovation cycle {cycle_id} with {cycle.cycle_completion_rate:.1%} completion rate")
        
        return {
            "cycle_id": cycle_id,
            "completion_rate": cycle.cycle_completion_rate,
            "total_innovations": cycle.features_ideated,
            "prototypes_created": cycle.prototypes_created,
            "approvals": cycle.innovations_approved,
            "summary": self._generate_cycle_summary(cycle)
        }
    
    def _generate_cycle_summary(self, cycle: InnovationCycleMetrics) -> str:
        """Generate human-readable cycle summary"""
        return f"""
        Innovation Cycle Summary:
        • {cycle.features_ideated} features ideated from {cycle.competitors_analyzed} competitor analyses
        • {cycle.prototypes_created} prototypes built and {cycle.validations_completed} validations completed
        • {cycle.innovations_approved} innovations approved for production
        • {cycle.competitive_threats_identified} threats identified, {cycle.market_opportunities_discovered} opportunities discovered
        • Overall completion rate: {cycle.cycle_completion_rate:.1%}
        """
    
    def get_agent_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive agent performance report"""
        agent_reports = {}
        
        for agent_name, metrics in self.agent_metrics.items():
            performance_score = self._calculate_agent_performance_score(metrics)
            
            agent_reports[agent_name] = {
                "specialization": metrics.specialization,
                "performance_score": performance_score,
                "total_tasks": metrics.total_tasks,
                "success_rate": metrics.success_rate,
                "average_response_time": metrics.average_response_time,
                "innovation_contributions": metrics.innovation_contributions,
                "quality_score": metrics.quality_score,
                "last_active": metrics.last_active.isoformat() if metrics.last_active else None,
                "performance_grade": self._get_performance_grade(performance_score)
            }
        
        # Calculate team averages
        team_metrics = self._calculate_team_averages()
        
        return {
            "individual_agents": agent_reports,
            "team_averages": team_metrics,
            "top_performers": self._get_top_performers(),
            "improvement_recommendations": self._get_improvement_recommendations()
        }
    
    def _calculate_agent_performance_score(self, metrics: AgentPerformanceMetrics) -> float:
        """Calculate composite performance score for agent"""
        if metrics.total_tasks == 0:
            return 0.0
        
        # Weighted scoring
        success_weight = 0.3
        speed_weight = 0.2
        quality_weight = 0.25
        innovation_weight = 0.25
        
        # Normalize response time (lower is better, max 300 seconds)
        speed_score = max(0, 100 - (metrics.average_response_time / 3))
        
        # Innovation contribution score (relative to total tasks)
        innovation_score = min(100, (metrics.innovation_contributions / metrics.total_tasks) * 100)
        
        composite_score = (
            metrics.success_rate * 100 * success_weight +
            speed_score * speed_weight +
            metrics.quality_score * quality_weight +
            innovation_score * innovation_weight
        )
        
        return min(100, max(0, composite_score))
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert performance score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _calculate_team_averages(self) -> Dict[str, float]:
        """Calculate team-wide performance averages"""
        if not self.agent_metrics:
            return {}
        
        total_tasks = sum(m.total_tasks for m in self.agent_metrics.values())
        completed_tasks = sum(m.completed_tasks for m in self.agent_metrics.values())
        response_times = [m.average_response_time for m in self.agent_metrics.values() if m.average_response_time > 0]
        quality_scores = [m.quality_score for m in self.agent_metrics.values() if m.quality_score > 0]
        
        return {
            "team_success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "average_response_time": statistics.mean(response_times) if response_times else 0,
            "average_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
            "total_innovation_contributions": sum(m.innovation_contributions for m in self.agent_metrics.values()),
            "agent_utilization": len([m for m in self.agent_metrics.values() if m.total_tasks > 0]) / len(self.agent_metrics)
        }
    
    def _get_top_performers(self) -> List[Dict[str, Any]]:
        """Get top performing agents"""
        performers = []
        
        for agent_name, metrics in self.agent_metrics.items():
            if metrics.total_tasks > 0:
                score = self._calculate_agent_performance_score(metrics)
                performers.append({
                    "agent_name": agent_name,
                    "specialization": metrics.specialization,
                    "performance_score": score,
                    "success_rate": metrics.success_rate,
                    "innovation_contributions": metrics.innovation_contributions
                })
        
        return sorted(performers, key=lambda x: x["performance_score"], reverse=True)[:3]
    
    def _get_improvement_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on metrics"""
        recommendations = []
        
        team_avg = self._calculate_team_averages()
        
        if team_avg.get("team_success_rate", 0) < 0.8:
            recommendations.append("Focus on improving task success rates through better training and process optimization")
        
        if team_avg.get("average_response_time", 0) > 120:
            recommendations.append("Optimize agent response times through workflow improvements and resource allocation")
        
        if team_avg.get("agent_utilization", 0) < 0.7:
            recommendations.append("Increase agent utilization through better task distribution and workload balancing")
        
        # Check cycle metrics
        if self.current_cycle_id and self.current_cycle_id in self.cycle_metrics:
            cycle = self.cycle_metrics[self.current_cycle_id]
            if cycle.features_ideated < self.targets["features_ideated_per_week"]:
                recommendations.append("Increase feature ideation through enhanced competitive intelligence and research analysis")
        
        return recommendations
    
    def get_innovation_pipeline_metrics(self) -> Dict[str, Any]:
        """Get metrics specific to innovation pipeline performance"""
        current_cycle = self.cycle_metrics.get(self.current_cycle_id) if self.current_cycle_id else None
        
        # Calculate pipeline velocity
        recent_cycles = list(self.metrics_history)[-4:]  # Last 4 weeks
        avg_features_per_week = statistics.mean([
            cycle["metrics"]["features_ideated"] for cycle in recent_cycles
        ]) if recent_cycles else 0
        
        avg_prototypes_per_week = statistics.mean([
            cycle["metrics"]["prototypes_created"] for cycle in recent_cycles
        ]) if recent_cycles else 0
        
        return {
            "current_cycle": asdict(current_cycle) if current_cycle else None,
            "pipeline_velocity": {
                "avg_features_per_week": avg_features_per_week,
                "avg_prototypes_per_week": avg_prototypes_per_week,
                "trend": self._calculate_velocity_trend()
            },
            "innovation_health": self._assess_innovation_health(),
            "bottleneck_analysis": self._identify_pipeline_bottlenecks(),
            "target_performance": self._compare_against_targets()
        }
    
    def _calculate_velocity_trend(self) -> str:
        """Calculate if innovation velocity is increasing or decreasing"""
        if len(self.metrics_history) < 2:
            return "insufficient_data"
        
        recent_features = [cycle["metrics"]["features_ideated"] for cycle in list(self.metrics_history)[-2:]]
        
        if recent_features[1] > recent_features[0]:
            return "increasing"
        elif recent_features[1] < recent_features[0]:
            return "decreasing"
        else:
            return "stable"
    
    def _assess_innovation_health(self) -> str:
        """Assess overall innovation pipeline health"""
        if not self.current_cycle_id:
            return "no_active_cycle"
        
        current_cycle = self.cycle_metrics.get(self.current_cycle_id)
        if not current_cycle:
            return "unknown"
        
        # Calculate health based on multiple factors
        health_factors = []
        
        # Feature ideation rate
        if current_cycle.features_ideated >= self.targets["features_ideated_per_week"]:
            health_factors.append(1)
        else:
            health_factors.append(current_cycle.features_ideated / self.targets["features_ideated_per_week"])
        
        # Prototype success
        if current_cycle.prototypes_created > 0:
            health_factors.append(min(1, current_cycle.validations_completed / current_cycle.prototypes_created))
        else:
            health_factors.append(0.5)  # Neutral if no prototypes
        
        # Approval rate
        if current_cycle.features_ideated > 0:
            health_factors.append(min(1, current_cycle.innovations_approved / current_cycle.features_ideated))
        else:
            health_factors.append(0.5)  # Neutral if no features
        
        overall_health = statistics.mean(health_factors)
        
        if overall_health >= 0.8:
            return "excellent"
        elif overall_health >= 0.6:
            return "good"
        elif overall_health >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _identify_pipeline_bottlenecks(self) -> List[str]:
        """Identify potential bottlenecks in innovation pipeline"""
        bottlenecks = []
        
        if not self.current_cycle_id:
            return ["No active innovation cycle"]
        
        current_cycle = self.cycle_metrics.get(self.current_cycle_id)
        if not current_cycle:
            return ["Unable to access current cycle data"]
        
        # Check various pipeline stages
        if current_cycle.competitors_analyzed < 3:
            bottlenecks.append("Insufficient competitive intelligence gathering")
        
        if current_cycle.research_papers_reviewed < 10:
            bottlenecks.append("Limited research analysis coverage")
        
        if current_cycle.features_ideated < 5:
            bottlenecks.append("Low feature ideation rate")
        
        if current_cycle.prototypes_created == 0 and current_cycle.features_ideated > 0:
            bottlenecks.append("Prototyping bottleneck - features not being prototyped")
        
        if current_cycle.innovations_approved == 0 and current_cycle.prototypes_created > 0:
            bottlenecks.append("Approval bottleneck - prototypes not getting approved")
        
        return bottlenecks
    
    def _compare_against_targets(self) -> Dict[str, Any]:
        """Compare current performance against targets"""
        if not self.current_cycle_id:
            return {}
        
        current_cycle = self.cycle_metrics.get(self.current_cycle_id)
        if not current_cycle:
            return {}
        
        comparisons = {}
        
        # Features ideated
        target_features = self.targets["features_ideated_per_week"]
        comparisons["features_ideated"] = {
            "current": current_cycle.features_ideated,
            "target": target_features,
            "performance": current_cycle.features_ideated / target_features if target_features > 0 else 0,
            "status": "on_track" if current_cycle.features_ideated >= target_features else "below_target"
        }
        
        # Research coverage
        target_research = self.targets["research_papers_per_week"]
        comparisons["research_papers"] = {
            "current": current_cycle.research_papers_reviewed,
            "target": target_research,
            "performance": current_cycle.research_papers_reviewed / target_research if target_research > 0 else 0,
            "status": "on_track" if current_cycle.research_papers_reviewed >= target_research else "below_target"
        }
        
        return comparisons
    
    def take_daily_snapshot(self):
        """Take daily snapshot of metrics for trend analysis"""
        snapshot = {
            "date": datetime.now().isoformat(),
            "agent_count": len(self.agent_metrics),
            "active_agents": len([m for m in self.agent_metrics.values() if m.last_active and 
                                (datetime.now() - m.last_active).days < 1]),
            "total_tasks_today": sum(1 for m in self.agent_metrics.values() if m.last_active and 
                                   (datetime.now() - m.last_active).days < 1),
            "innovation_cycle_active": self.current_cycle_id is not None,
            "real_time_metrics": self.real_time_metrics.copy()
        }
        
        self.daily_snapshots.append(snapshot)
        logger.debug("Took daily metrics snapshot")

# Global R&D metrics tracker instance
rd_metrics_tracker = RDMetricsTracker()