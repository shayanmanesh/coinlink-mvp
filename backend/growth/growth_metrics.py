"""
Growth Metrics Tracking System

Ultra-comprehensive performance tracking for the Growth Engine.
Monitors all BD and Marketing agents, tracks KPIs, and provides
real-time growth analytics and performance optimization.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import asyncio
import json
import logging
from enum import Enum

from .data_models import GrowthEvent, Lead, Opportunity, Campaign, Deal

class MetricType(Enum):
    LEAD_GENERATION = "lead_generation"
    OPPORTUNITY_CONVERSION = "opportunity_conversion" 
    DEAL_CLOSURE = "deal_closure"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    REVENUE_RECOGNITION = "revenue_recognition"
    ROI_MEASUREMENT = "roi_measurement"

@dataclass
class MetricDataPoint:
    """Individual metric measurement"""
    metric_type: MetricType
    agent_id: str
    timestamp: datetime
    value: float
    target: float
    variance: float
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def performance_ratio(self) -> float:
        """Calculate performance vs target"""
        return self.value / self.target if self.target > 0 else 0.0
    
    @property
    def is_above_target(self) -> bool:
        return self.performance_ratio >= 1.0

@dataclass  
class AgentPerformance:
    """Comprehensive agent performance tracking"""
    agent_id: str
    agent_type: str
    daily_metrics: List[MetricDataPoint] = field(default_factory=list)
    weekly_metrics: List[MetricDataPoint] = field(default_factory=list)
    monthly_metrics: List[MetricDataPoint] = field(default_factory=list)
    performance_score: float = 0.0
    efficiency_rating: str = "PENDING"
    target_achievement_rate: float = 0.0
    
    def calculate_performance_score(self) -> float:
        """Calculate overall performance score"""
        if not self.daily_metrics:
            return 0.0
        
        total_score = sum(m.performance_ratio for m in self.daily_metrics)
        return total_score / len(self.daily_metrics)

@dataclass
class GrowthMetrics:
    """Consolidated growth metrics across all agents"""
    timestamp: datetime
    
    # BD Metrics
    leads_generated: int = 0
    opportunities_created: int = 0
    deals_closed: int = 0
    revenue_recognized: float = 0.0
    avg_deal_size: float = 0.0
    sales_cycle_days: float = 0.0
    
    # Marketing Metrics
    campaigns_launched: int = 0
    mql_generated: int = 0
    marketing_roi: float = 0.0
    campaign_conversion_rate: float = 0.0
    cost_per_lead: float = 0.0
    content_engagement_rate: float = 0.0
    
    # Overall Performance
    growth_velocity: float = 0.0
    target_achievement_rate: float = 0.0
    system_efficiency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "bd_metrics": {
                "leads_generated": self.leads_generated,
                "opportunities_created": self.opportunities_created,
                "deals_closed": self.deals_closed,
                "revenue_recognized": self.revenue_recognized,
                "avg_deal_size": self.avg_deal_size,
                "sales_cycle_days": self.sales_cycle_days
            },
            "marketing_metrics": {
                "campaigns_launched": self.campaigns_launched,
                "mql_generated": self.mql_generated,
                "marketing_roi": self.marketing_roi,
                "campaign_conversion_rate": self.campaign_conversion_rate,
                "cost_per_lead": self.cost_per_lead,
                "content_engagement_rate": self.content_engagement_rate
            },
            "performance_metrics": {
                "growth_velocity": self.growth_velocity,
                "target_achievement_rate": self.target_achievement_rate,
                "system_efficiency": self.system_efficiency
            }
        }

class GrowthMetricsTracker:
    """Ultra-comprehensive growth performance tracking system"""
    
    def __init__(self):
        self.agent_performances: Dict[str, AgentPerformance] = {}
        self.historical_metrics: List[GrowthMetrics] = []
        self.current_metrics = GrowthMetrics(timestamp=datetime.utcnow())
        self.performance_thresholds = self._initialize_thresholds()
        self.logger = logging.getLogger(__name__)
        
        # Weekly targets (ultra-aggressive)
        self.weekly_targets = {
            "new_leads": 500,
            "qualified_opportunities": 100,
            "deals_closed": 10,
            "revenue_target": 1000000.0,  # $1M weekly
            "campaigns_launched": 15,
            "mql_generated": 300,
            "marketing_roi_target": 5.0
        }
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize performance thresholds for alerts"""
        return {
            "bd_agents": {
                "leads_per_day_min": 20.0,
                "opportunity_conversion_min": 0.20,
                "deal_closure_rate_min": 0.35,
                "avg_deal_size_min": 750000.0,
                "sales_cycle_max_days": 60.0
            },
            "marketing_agents": {
                "campaign_roi_min": 5.0,
                "cost_per_lead_max": 200.0,
                "conversion_rate_min": 0.015,
                "content_engagement_min": 0.065,
                "mql_quality_score_min": 0.75
            },
            "system": {
                "growth_velocity_min": 15.0,  # 15% monthly growth
                "system_efficiency_min": 85.0,
                "target_achievement_min": 80.0
            }
        }
    
    async def track_agent_performance(self, agent_id: str, agent_type: str, 
                                    metrics: Dict[str, float]) -> AgentPerformance:
        """Track individual agent performance metrics"""
        if agent_id not in self.agent_performances:
            self.agent_performances[agent_id] = AgentPerformance(
                agent_id=agent_id,
                agent_type=agent_type
            )
        
        agent_perf = self.agent_performances[agent_id]
        timestamp = datetime.utcnow()
        
        # Create metric data points
        for metric_name, value in metrics.items():
            target = self._get_agent_target(agent_type, metric_name)
            variance = (value - target) / target if target > 0 else 0.0
            
            metric_point = MetricDataPoint(
                metric_type=MetricType(metric_name),
                agent_id=agent_id,
                timestamp=timestamp,
                value=value,
                target=target,
                variance=variance,
                context={"agent_type": agent_type}
            )
            
            agent_perf.daily_metrics.append(metric_point)
        
        # Calculate performance score
        agent_perf.performance_score = agent_perf.calculate_performance_score()
        agent_perf.efficiency_rating = self._calculate_efficiency_rating(agent_perf.performance_score)
        
        # Update target achievement rate
        above_target_count = sum(1 for m in agent_perf.daily_metrics if m.is_above_target)
        agent_perf.target_achievement_rate = above_target_count / len(agent_perf.daily_metrics) if agent_perf.daily_metrics else 0.0
        
        self.logger.info(f"Agent {agent_id} performance updated: {agent_perf.performance_score:.2f}")
        return agent_perf
    
    def _get_agent_target(self, agent_type: str, metric_name: str) -> float:
        """Get target value for specific agent metric"""
        targets = {
            "bd_agents": {
                "lead_generation": 100.0,  # leads per month
                "opportunity_conversion": 0.25,
                "deal_closure": 15.0,  # deals per month
                "revenue_recognition": 2500000.0  # $2.5M per month
            },
            "marketing_agents": {
                "campaign_performance": 5.0,  # ROI ratio
                "lead_generation": 2500.0,  # MQLs per month
                "roi_measurement": 5.0
            }
        }
        
        agent_category = "bd_agents" if "bd" in agent_type else "marketing_agents"
        return targets.get(agent_category, {}).get(metric_name, 1.0)
    
    def _calculate_efficiency_rating(self, performance_score: float) -> str:
        """Calculate efficiency rating based on performance score"""
        if performance_score >= 1.5:
            return "EXCEPTIONAL"
        elif performance_score >= 1.25:
            return "EXCELLENT"
        elif performance_score >= 1.0:
            return "GOOD"
        elif performance_score >= 0.8:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"
    
    async def capture_system_snapshot(self) -> GrowthMetrics:
        """Capture current system performance snapshot"""
        current_time = datetime.utcnow()
        metrics = GrowthMetrics(timestamp=current_time)
        
        # Aggregate BD metrics
        bd_agents = [p for p in self.agent_performances.values() if "bd" in p.agent_type]
        if bd_agents:
            metrics.leads_generated = sum(
                sum(m.value for m in agent.daily_metrics if m.metric_type == MetricType.LEAD_GENERATION)
                for agent in bd_agents
            )
            
            metrics.opportunities_created = sum(
                sum(m.value for m in agent.daily_metrics if m.metric_type == MetricType.OPPORTUNITY_CONVERSION)
                for agent in bd_agents
            )
            
            metrics.deals_closed = sum(
                sum(m.value for m in agent.daily_metrics if m.metric_type == MetricType.DEAL_CLOSURE)
                for agent in bd_agents
            )
            
            metrics.revenue_recognized = sum(
                sum(m.value for m in agent.daily_metrics if m.metric_type == MetricType.REVENUE_RECOGNITION)
                for agent in bd_agents
            )
            
            if metrics.deals_closed > 0:
                metrics.avg_deal_size = metrics.revenue_recognized / metrics.deals_closed
        
        # Aggregate Marketing metrics
        marketing_agents = [p for p in self.agent_performances.values() if "marketing" in p.agent_type]
        if marketing_agents:
            metrics.campaigns_launched = sum(
                sum(m.value for m in agent.daily_metrics if m.metric_type == MetricType.CAMPAIGN_PERFORMANCE)
                for agent in marketing_agents
            )
            
            metrics.mql_generated = sum(
                sum(m.value for m in agent.daily_metrics if m.metric_type == MetricType.LEAD_GENERATION)
                for agent in marketing_agents
            )
            
            roi_values = []
            for agent in marketing_agents:
                roi_metrics = [m.value for m in agent.daily_metrics if m.metric_type == MetricType.ROI_MEASUREMENT]
                roi_values.extend(roi_metrics)
            
            metrics.marketing_roi = sum(roi_values) / len(roi_values) if roi_values else 0.0
        
        # Calculate overall performance metrics
        all_agents = list(self.agent_performances.values())
        if all_agents:
            metrics.target_achievement_rate = sum(a.target_achievement_rate for a in all_agents) / len(all_agents)
            metrics.system_efficiency = sum(a.performance_score for a in all_agents) / len(all_agents) * 100
        
        # Calculate growth velocity (month-over-month)
        if len(self.historical_metrics) > 0:
            last_month_revenue = self.historical_metrics[-1].revenue_recognized
            if last_month_revenue > 0:
                metrics.growth_velocity = ((metrics.revenue_recognized - last_month_revenue) / last_month_revenue) * 100
        
        self.current_metrics = metrics
        self.historical_metrics.append(metrics)
        
        self.logger.info(f"System snapshot captured: {metrics.revenue_recognized:,.2f} revenue, {metrics.target_achievement_rate:.2f} achievement rate")
        return metrics
    
    async def generate_performance_alerts(self) -> List[Dict[str, Any]]:
        """Generate performance alerts for underperforming areas"""
        alerts = []
        thresholds = self.performance_thresholds
        
        # Check BD performance
        bd_agents = [p for p in self.agent_performances.values() if "bd" in p.agent_type]
        for agent in bd_agents:
            if agent.performance_score < 0.8:
                alerts.append({
                    "type": "PERFORMANCE_ALERT",
                    "severity": "HIGH",
                    "agent_id": agent.agent_id,
                    "message": f"BD agent {agent.agent_id} performance below threshold: {agent.performance_score:.2f}",
                    "recommendation": "Increase prospecting activity and improve conversion tactics",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check Marketing performance
        marketing_agents = [p for p in self.agent_performances.values() if "marketing" in p.agent_type]
        for agent in marketing_agents:
            if agent.performance_score < 0.8:
                alerts.append({
                    "type": "PERFORMANCE_ALERT", 
                    "severity": "HIGH",
                    "agent_id": agent.agent_id,
                    "message": f"Marketing agent {agent.agent_id} performance below threshold: {agent.performance_score:.2f}",
                    "recommendation": "Optimize campaigns and increase lead quality focus",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check system-wide metrics
        if self.current_metrics.target_achievement_rate < thresholds["system"]["target_achievement_min"] / 100:
            alerts.append({
                "type": "SYSTEM_ALERT",
                "severity": "CRITICAL",
                "message": f"System target achievement below threshold: {self.current_metrics.target_achievement_rate:.2f}",
                "recommendation": "Initiate comprehensive performance optimization sprint",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
    
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive performance dashboard"""
        await self.capture_system_snapshot()
        
        # Top performing agents
        top_agents = sorted(
            self.agent_performances.values(),
            key=lambda x: x.performance_score,
            reverse=True
        )[:5]
        
        # Performance trends (last 7 days)
        recent_metrics = self.historical_metrics[-7:] if len(self.historical_metrics) >= 7 else self.historical_metrics
        
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "current_metrics": self.current_metrics.to_dict(),
            "weekly_targets": self.weekly_targets,
            "target_achievement": {
                "leads": {
                    "current": self.current_metrics.leads_generated,
                    "target": self.weekly_targets["new_leads"], 
                    "achievement_rate": self.current_metrics.leads_generated / self.weekly_targets["new_leads"] if self.weekly_targets["new_leads"] > 0 else 0
                },
                "revenue": {
                    "current": self.current_metrics.revenue_recognized,
                    "target": self.weekly_targets["revenue_target"],
                    "achievement_rate": self.current_metrics.revenue_recognized / self.weekly_targets["revenue_target"] if self.weekly_targets["revenue_target"] > 0 else 0
                }
            },
            "top_performers": [
                {
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "performance_score": agent.performance_score,
                    "efficiency_rating": agent.efficiency_rating,
                    "target_achievement": agent.target_achievement_rate
                }
                for agent in top_agents
            ],
            "performance_trends": [
                {
                    "date": m.timestamp.isoformat(),
                    "revenue": m.revenue_recognized,
                    "leads": m.leads_generated,
                    "deals": m.deals_closed,
                    "growth_velocity": m.growth_velocity
                }
                for m in recent_metrics
            ],
            "system_health": {
                "overall_efficiency": self.current_metrics.system_efficiency,
                "growth_velocity": self.current_metrics.growth_velocity,
                "target_achievement_rate": self.current_metrics.target_achievement_rate,
                "active_agents": len(self.agent_performances),
                "alerts_count": len(await self.generate_performance_alerts())
            }
        }
        
        return dashboard
    
    async def optimize_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on performance analysis"""
        recommendations = []
        
        # Analyze underperforming agents
        underperformers = [
            agent for agent in self.agent_performances.values()
            if agent.performance_score < 0.8
        ]
        
        for agent in underperformers:
            if "bd" in agent.agent_type:
                recommendations.append({
                    "type": "BD_OPTIMIZATION",
                    "agent_id": agent.agent_id,
                    "priority": "HIGH",
                    "recommendation": "Increase daily prospecting volume to 100+ contacts",
                    "expected_impact": "25% improvement in lead generation",
                    "implementation_time": "immediate"
                })
            else:
                recommendations.append({
                    "type": "MARKETING_OPTIMIZATION",
                    "agent_id": agent.agent_id,
                    "priority": "HIGH", 
                    "recommendation": "Optimize campaign targeting and increase budget for high-ROI channels",
                    "expected_impact": "30% improvement in cost per lead",
                    "implementation_time": "24 hours"
                })
        
        # System-wide optimizations
        if self.current_metrics.growth_velocity < 10.0:
            recommendations.append({
                "type": "SYSTEM_OPTIMIZATION",
                "priority": "CRITICAL",
                "recommendation": "Execute comprehensive growth acceleration sprint",
                "expected_impact": "40% increase in growth velocity",
                "implementation_time": "48 hours",
                "action_items": [
                    "Increase BD prospecting by 50%",
                    "Launch 5 additional high-ROI campaigns",
                    "Optimize sales process and reduce cycle time",
                    "Implement aggressive lead nurturing sequences"
                ]
            })
        
        return recommendations

# Global metrics tracker instance
growth_metrics_tracker = GrowthMetricsTracker()