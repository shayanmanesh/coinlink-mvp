"""
Campaign Planner Agent - Campaign Planning & Budget Optimization Engine

Strategic campaign planning agent that designs multi-channel marketing campaigns,
optimizes budget allocation, and orchestrates integrated demand generation programs.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import uuid
from enum import Enum

from ..data_models import (
    Lead, Opportunity, Campaign, GrowthEvent, Priority,
    CampaignChannel, LeadSource, Contact, EngagementEvent
)

logger = logging.getLogger(__name__)

class CampaignType(Enum):
    """Types of marketing campaigns"""
    DEMAND_GENERATION = "demand_generation"
    BRAND_AWARENESS = "brand_awareness"
    PRODUCT_LAUNCH = "product_launch"
    LEAD_NURTURING = "lead_nurturing"
    ACCOUNT_BASED_MARKETING = "account_based_marketing"
    COMPETITIVE_DISPLACEMENT = "competitive_displacement"
    CUSTOMER_EXPANSION = "customer_expansion"
    EVENT_PROMOTION = "event_promotion"

class CampaignObjective(Enum):
    """Campaign primary objectives"""
    LEAD_GENERATION = "lead_generation"
    PIPELINE_ACCELERATION = "pipeline_acceleration"
    BRAND_BUILDING = "brand_building"
    THOUGHT_LEADERSHIP = "thought_leadership"
    PRODUCT_ADOPTION = "product_adoption"
    MARKET_PENETRATION = "market_penetration"
    CUSTOMER_RETENTION = "customer_retention"
    COMPETITIVE_DEFENSE = "competitive_defense"

class BudgetAllocationStrategy(Enum):
    """Budget allocation strategies"""
    PERFORMANCE_WEIGHTED = "performance_weighted"
    EQUAL_DISTRIBUTION = "equal_distribution"
    FUNNEL_OPTIMIZED = "funnel_optimized"
    CHANNEL_SPECIFIC = "channel_specific"
    TEST_AND_SCALE = "test_and_scale"
    ROI_MAXIMIZED = "roi_maximized"

@dataclass
class CampaignPlan:
    """Comprehensive campaign plan structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_name: str = ""
    campaign_type: CampaignType = CampaignType.DEMAND_GENERATION
    primary_objective: CampaignObjective = CampaignObjective.LEAD_GENERATION
    
    # Campaign scope and targeting
    target_audience: Dict[str, Any] = field(default_factory=dict)
    geographic_targeting: List[str] = field(default_factory=list)
    industry_targeting: List[str] = field(default_factory=list)
    account_targeting: List[str] = field(default_factory=list)
    
    # Channel strategy
    primary_channels: List[CampaignChannel] = field(default_factory=list)
    secondary_channels: List[CampaignChannel] = field(default_factory=list)
    channel_mix_strategy: str = ""
    
    # Budget and resource allocation
    total_budget: float = 0.0
    channel_budget_allocation: Dict[str, float] = field(default_factory=dict)
    resource_requirements: Dict[str, int] = field(default_factory=dict)
    budget_allocation_strategy: BudgetAllocationStrategy = BudgetAllocationStrategy.PERFORMANCE_WEIGHTED
    
    # Timeline and execution
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    campaign_duration_days: int = 0
    execution_phases: List[Dict[str, Any]] = field(default_factory=list)
    
    # Creative and messaging
    messaging_themes: List[str] = field(default_factory=list)
    creative_concepts: List[Dict[str, Any]] = field(default_factory=list)
    content_requirements: Dict[str, int] = field(default_factory=dict)
    
    # Success metrics and KPIs
    primary_kpis: List[str] = field(default_factory=list)
    target_metrics: Dict[str, float] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)
    
    # Optimization and testing
    ab_testing_plan: List[Dict[str, Any]] = field(default_factory=list)
    optimization_triggers: List[str] = field(default_factory=list)
    performance_benchmarks: Dict[str, float] = field(default_factory=dict)

@dataclass
class ChannelPlan:
    """Individual channel execution plan"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str = ""
    channel: CampaignChannel = CampaignChannel.PAID_SEARCH
    
    # Channel strategy
    channel_objective: str = ""
    target_audience_segment: str = ""
    messaging_approach: str = ""
    
    # Budget and targeting
    channel_budget: float = 0.0
    daily_budget: float = 0.0
    targeting_parameters: Dict[str, Any] = field(default_factory=dict)
    bid_strategy: str = ""
    
    # Creative requirements
    ad_formats: List[str] = field(default_factory=list)
    creative_assets_needed: List[str] = field(default_factory=list)
    landing_page_requirements: Dict[str, str] = field(default_factory=dict)
    
    # Performance expectations
    expected_impressions: int = 0
    expected_clicks: int = 0
    expected_conversions: int = 0
    target_ctr: float = 0.0
    target_conversion_rate: float = 0.0
    target_cpc: float = 0.0
    target_cpl: float = 0.0
    
    # Timeline and optimization
    launch_date: Optional[datetime] = None
    optimization_schedule: List[str] = field(default_factory=list)
    scaling_plan: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CampaignCalendar:
    """Integrated campaign calendar and scheduling"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_name: str = ""
    planning_period: str = ""  # Q1_2025, H1_2025, etc.
    
    # Campaign scheduling
    planned_campaigns: List[Dict[str, Any]] = field(default_factory=list)
    campaign_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    resource_allocation_timeline: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Budget planning
    total_period_budget: float = 0.0
    monthly_budget_distribution: Dict[str, float] = field(default_factory=dict)
    channel_budget_trends: Dict[str, List[float]] = field(default_factory=dict)
    
    # Performance projections
    projected_leads: Dict[str, int] = field(default_factory=dict)
    projected_pipeline: Dict[str, float] = field(default_factory=dict)
    projected_roi: Dict[str, float] = field(default_factory=dict)

class CampaignPlannerAgent:
    """Strategic campaign planning and budget optimization agent"""
    
    def __init__(self):
        self.agent_id = "campaign-planner-agent"
        self.name = "Campaign Planner Agent"
        self.specialization = "campaign_planning_budget_optimization"
        self.capabilities = [
            "campaign_design", "budget_optimization", "channel_planning",
            "audience_segmentation", "performance_forecasting", "calendar_management"
        ]
        
        # Campaign database
        self.campaign_plans: Dict[str, CampaignPlan] = {}
        self.channel_plans: Dict[str, ChannelPlan] = {}
        self.campaign_calendars: Dict[str, CampaignCalendar] = {}
        
        # Channel performance benchmarks (historical data)
        self.channel_benchmarks = {
            CampaignChannel.PAID_SEARCH: {
                "avg_ctr": 0.035,
                "avg_conversion_rate": 0.028,
                "avg_cpc": 12.50,
                "avg_cpl": 145.00,
                "lead_quality_score": 0.82
            },
            CampaignChannel.PAID_SOCIAL: {
                "avg_ctr": 0.045,
                "avg_conversion_rate": 0.035,
                "avg_cpc": 18.75,
                "avg_cpl": 185.00,
                "lead_quality_score": 0.89
            },
            CampaignChannel.PAID_SOCIAL: {
                "avg_ctr": 0.025,
                "avg_conversion_rate": 0.022,
                "avg_cpc": 8.25,
                "avg_cpl": 95.00,
                "lead_quality_score": 0.65
            },
            CampaignChannel.CONTENT_MARKETING: {
                "avg_engagement_rate": 0.065,
                "avg_conversion_rate": 0.042,
                "avg_cpl": 75.00,
                "lead_quality_score": 0.78,
                "long_term_multiplier": 2.5
            }
        }
        
        # Budget allocation templates
        self.budget_templates = {
            "aggressive_growth": {
                "paid_search": 0.35,
                "social_advertising": 0.25,
                "content_marketing": 0.20,
                "events": 0.15,
                "other": 0.05
            },
            "balanced_mix": {
                "paid_search": 0.30,
                "social_advertising": 0.25,
                "content_marketing": 0.25,
                "events": 0.15,
                "other": 0.05
            },
            "brand_focused": {
                "content_marketing": 0.35,
                "social_advertising": 0.25,
                "events": 0.20,
                "paid_search": 0.15,
                "other": 0.05
            }
        }
        
        # Planning parameters
        self.planning_targets = {
            "quarterly_lead_target": 7500,
            "monthly_pipeline_target": 5000000.0,
            "target_marketing_roi": 5.0,
            "max_cpl_threshold": 200.00,
            "min_lead_quality_score": 0.75
        }
        
        # Performance metrics
        self.campaigns_planned_count = 0
        self.total_budget_optimized = 0.0
        self.avg_campaign_roi = 0.0
        self.planning_accuracy_rate = 0.0
        
        logger.info(f"Campaign Planner Agent initialized - targeting {self.planning_targets['quarterly_lead_target']} leads/quarter")

    async def execute_campaign_planning_sprint(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive campaign planning and optimization sprint"""
        planning_scope = parameters.get('planning_scope', 'quarterly')
        total_budget = parameters.get('total_budget', 2000000.0)
        campaign_objectives = parameters.get('objectives', ['lead_generation', 'brand_awareness'])
        target_segments = parameters.get('target_segments', ['enterprise', 'mid_market'])
        planning_timeline = parameters.get('timeline_months', 3)
        
        logger.info(f"Starting {planning_scope} campaign planning sprint - budget: ${total_budget:,.0f}")
        
        campaign_plans_created = []
        channel_plans_optimized = []
        budget_allocations = []
        performance_forecasts = []
        
        # Execute parallel campaign planning tasks
        planning_tasks = [
            self._design_integrated_campaign_portfolio(campaign_objectives, target_segments, total_budget),
            self._optimize_multi_channel_budget_allocation(total_budget, campaign_objectives),
            self._create_detailed_channel_execution_plans(target_segments),
            self._develop_campaign_calendar_and_sequencing(planning_timeline),
            self._forecast_campaign_performance_and_roi(total_budget, campaign_objectives)
        ]
        
        planning_results = await asyncio.gather(*planning_tasks, return_exceptions=True)
        
        # Process and consolidate results
        for i, result in enumerate(planning_results):
            if isinstance(result, Exception):
                logger.error(f"Campaign planning task {i} failed: {result}")
                continue
                
            campaign_plans_created.extend(result.get('campaign_plans', []))
            channel_plans_optimized.extend(result.get('channel_plans', []))
            budget_allocations.extend(result.get('budget_allocations', []))
            performance_forecasts.extend(result.get('performance_forecasts', []))
        
        # Create integrated campaign calendar
        campaign_calendar = await self._create_integrated_campaign_calendar(
            campaign_plans_created, planning_timeline, total_budget
        )
        
        # Optimize budget allocation across campaigns
        optimized_budget = await self._optimize_cross_campaign_budget_allocation(
            campaign_plans_created, total_budget
        )
        
        # Update performance metrics
        self.campaigns_planned_count += len(campaign_plans_created)
        self.total_budget_optimized += total_budget
        
        logger.info(f"Campaign planning completed: {len(campaign_plans_created)} campaigns, " +
                   f"${total_budget:,.0f} optimized across {len(channel_plans_optimized)} channels")
        
        return {
            "success": True,
            "planning_scope": planning_scope,
            "execution_time_minutes": 50,  # Simulated
            "planning_summary": {
                "total_campaigns_planned": len(campaign_plans_created),
                "total_budget_allocated": total_budget,
                "channels_optimized": len(set(cp.get('channel') for cp in channel_plans_optimized)),
                "target_segments_covered": len(target_segments),
                "planning_timeline_months": planning_timeline
            },
            "campaign_portfolio": {
                "demand_generation_campaigns": len([c for c in campaign_plans_created if c.get('type') == 'demand_generation']),
                "brand_awareness_campaigns": len([c for c in campaign_plans_created if c.get('type') == 'brand_awareness']),
                "product_launch_campaigns": len([c for c in campaign_plans_created if c.get('type') == 'product_launch']),
                "account_based_campaigns": len([c for c in campaign_plans_created if c.get('type') == 'account_based_marketing'])
            },
            "budget_optimization": {
                "primary_channel_allocation": optimized_budget.get('primary_channels', {}),
                "secondary_channel_allocation": optimized_budget.get('secondary_channels', {}),
                "monthly_budget_distribution": optimized_budget.get('monthly_distribution', {}),
                "roi_optimization_score": optimized_budget.get('optimization_score', 0.85)
            },
            "channel_strategy": {
                "google_ads_investment": sum(cp.get('budget', 0) for cp in channel_plans_optimized if cp.get('channel') == 'google_ads'),
                "linkedin_ads_investment": sum(cp.get('budget', 0) for cp in channel_plans_optimized if cp.get('channel') == 'linkedin_ads'),
                "content_marketing_investment": sum(cp.get('budget', 0) for cp in channel_plans_optimized if cp.get('channel') == 'content_marketing'),
                "events_investment": sum(cp.get('budget', 0) for cp in channel_plans_optimized if cp.get('channel') == 'events')
            },
            "performance_projections": {
                "projected_leads": sum(pf.get('leads', 0) for pf in performance_forecasts),
                "projected_pipeline_value": sum(pf.get('pipeline_value', 0) for pf in performance_forecasts),
                "projected_marketing_roi": sum(pf.get('roi', 0) for pf in performance_forecasts) / max(len(performance_forecasts), 1),
                "projected_customer_acquisition_cost": sum(pf.get('cac', 0) for pf in performance_forecasts) / max(len(performance_forecasts), 1)
            },
            "campaign_calendar": {
                "calendar_id": campaign_calendar.get('id'),
                "campaign_sequence": campaign_calendar.get('campaign_sequence', []),
                "resource_utilization": campaign_calendar.get('resource_utilization', {}),
                "peak_activity_periods": campaign_calendar.get('peak_periods', [])
            },
            "optimization_recommendations": await self._generate_campaign_optimization_recommendations(campaign_plans_created, optimized_budget),
            "risk_analysis": {
                "budget_concentration_risk": self._assess_budget_concentration_risk(optimized_budget),
                "performance_dependency_risk": self._assess_performance_risk(performance_forecasts),
                "timeline_execution_risk": self._assess_timeline_risk(campaign_calendar)
            }
        }

    async def _design_integrated_campaign_portfolio(self, objectives: List[str], 
                                                  target_segments: List[str], 
                                                  total_budget: float) -> Dict[str, Any]:
        """Design integrated portfolio of campaigns"""
        campaign_plans = []
        
        # Create campaign plans for each objective-segment combination
        for objective in objectives:
            for segment in target_segments:
                campaign_plan = await self._create_campaign_plan(objective, segment, total_budget / (len(objectives) * len(target_segments)))
                campaign_plans.append(campaign_plan)
        
        return {
            "campaign_plans": campaign_plans,
            "channel_plans": [],
            "budget_allocations": [],
            "performance_forecasts": []
        }

    async def _create_campaign_plan(self, objective: str, segment: str, budget: float) -> Dict[str, Any]:
        """Create detailed campaign plan for specific objective and segment"""
        campaign_plan = CampaignPlan(
            campaign_name=f"{objective.title()} - {segment.title()} Q1 2025",
            campaign_type=CampaignType.DEMAND_GENERATION if objective == 'lead_generation' else CampaignType.BRAND_AWARENESS,
            primary_objective=CampaignObjective(objective.upper()),
            target_audience={
                "segment": segment,
                "company_size": "enterprise" if segment == "enterprise" else "mid_market",
                "decision_makers": ["CTO", "VP Engineering", "Head of Trading"],
                "geographic_focus": ["North America", "Europe"]
            },
            total_budget=budget,
            campaign_duration_days=90,
            primary_channels=[
                CampaignChannel.PAID_SOCIAL,
                CampaignChannel.PAID_SEARCH,
                CampaignChannel.CONTENT_MARKETING
            ],
            messaging_themes=[
                "Trading platform modernization",
                "Performance and reliability",
                "Cost optimization",
                "Regulatory compliance"
            ],
            target_metrics={
                "leads": budget / 150,  # $150 target CPL
                "pipeline_value": (budget / 150) * 25000,  # $25k average opportunity
                "roi": 4.5,
                "conversion_rate": 0.03
            }
        )
        
        return campaign_plan.__dict__

    async def _optimize_multi_channel_budget_allocation(self, total_budget: float, 
                                                      objectives: List[str]) -> Dict[str, Any]:
        """Optimize budget allocation across multiple channels"""
        # Determine allocation strategy based on objectives
        if 'lead_generation' in objectives:
            allocation_template = self.budget_templates["aggressive_growth"]
        elif 'brand_awareness' in objectives:
            allocation_template = self.budget_templates["brand_focused"]
        else:
            allocation_template = self.budget_templates["balanced_mix"]
        
        # Apply budget allocation
        budget_allocation = {}
        for channel, percentage in allocation_template.items():
            budget_allocation[channel] = total_budget * percentage
        
        # Optimize based on expected ROI
        optimized_allocation = await self._apply_roi_optimization(budget_allocation)
        
        return {
            "campaign_plans": [],
            "channel_plans": [],
            "budget_allocations": [optimized_allocation],
            "performance_forecasts": []
        }

    async def _apply_roi_optimization(self, base_allocation: Dict[str, float]) -> Dict[str, Any]:
        """Apply ROI-based optimization to budget allocation"""
        # Simulate ROI optimization algorithm
        channel_roi_scores = {
            "paid_search": 4.8,
            "social_advertising": 4.2,
            "content_marketing": 5.5,
            "events": 3.9,
            "other": 3.2
        }
        
        # Reallocate budget based on ROI scores
        total_roi_weight = sum(channel_roi_scores.values())
        optimized_allocation = {}
        
        total_budget = sum(base_allocation.values())
        for channel, base_budget in base_allocation.items():
            roi_weight = channel_roi_scores.get(channel, 3.0)
            optimization_factor = roi_weight / (total_roi_weight / len(channel_roi_scores))
            optimized_allocation[channel] = base_budget * optimization_factor
        
        # Normalize to maintain total budget
        allocation_sum = sum(optimized_allocation.values())
        for channel in optimized_allocation:
            optimized_allocation[channel] = (optimized_allocation[channel] / allocation_sum) * total_budget
        
        return {
            "primary_channels": optimized_allocation,
            "optimization_score": 0.87,
            "roi_improvement": 0.15
        }

    async def _create_detailed_channel_execution_plans(self, target_segments: List[str]) -> Dict[str, Any]:
        """Create detailed execution plans for each channel"""
        channel_plans = []
        
        # Create channel plans for primary channels
        primary_channels = [
            CampaignChannel.GOOGLE_ADS,
            CampaignChannel.LINKEDIN_ADS,
            CampaignChannel.CONTENT_MARKETING
        ]
        
        for channel in primary_channels:
            for segment in target_segments:
                channel_plan = await self._create_channel_execution_plan(channel, segment)
                channel_plans.append(channel_plan)
        
        return {
            "campaign_plans": [],
            "channel_plans": channel_plans,
            "budget_allocations": [],
            "performance_forecasts": []
        }

    async def _create_channel_execution_plan(self, channel: CampaignChannel, segment: str) -> Dict[str, Any]:
        """Create detailed execution plan for specific channel"""
        benchmark = self.channel_benchmarks.get(channel, {})
        
        # Calculate budget and performance expectations
        if channel == CampaignChannel.PAID_SEARCH:
            daily_budget = 2500.0
            expected_clicks = int(daily_budget / benchmark.get('avg_cpc', 12.50))
            expected_conversions = int(expected_clicks * benchmark.get('avg_conversion_rate', 0.028))
        elif channel == CampaignChannel.PAID_SOCIAL:
            daily_budget = 2000.0
            expected_clicks = int(daily_budget / benchmark.get('avg_cpc', 18.75))
            expected_conversions = int(expected_clicks * benchmark.get('avg_conversion_rate', 0.035))
        else:  # Content Marketing
            daily_budget = 1500.0
            expected_conversions = int(daily_budget / benchmark.get('avg_cpl', 75.00))
            expected_clicks = expected_conversions * 25  # Estimated content engagement
        
        channel_plan = ChannelPlan(
            channel=channel,
            channel_objective=f"Generate qualified leads from {segment} segment",
            target_audience_segment=segment,
            daily_budget=daily_budget,
            expected_clicks=expected_clicks,
            expected_conversions=expected_conversions,
            target_ctr=benchmark.get('avg_ctr', 0.03),
            target_conversion_rate=benchmark.get('avg_conversion_rate', 0.03),
            target_cpc=benchmark.get('avg_cpc', 12.0),
            target_cpl=benchmark.get('avg_cpl', 150.0),
            ad_formats=await self._get_channel_ad_formats(channel),
            targeting_parameters=await self._get_targeting_parameters(channel, segment)
        )
        
        return channel_plan.__dict__

    async def _get_channel_ad_formats(self, channel: CampaignChannel) -> List[str]:
        """Get recommended ad formats for channel"""
        format_map = {
            CampaignChannel.GOOGLE_ADS: ["Search ads", "Display ads", "YouTube ads"],
            CampaignChannel.LINKEDIN_ADS: ["Sponsored content", "Message ads", "Dynamic ads"],
            CampaignChannel.CONTENT_MARKETING: ["Blog posts", "Whitepapers", "Webinars"]
        }
        return format_map.get(channel, ["Standard ads"])

    async def _get_targeting_parameters(self, channel: CampaignChannel, segment: str) -> Dict[str, Any]:
        """Get targeting parameters for channel and segment"""
        base_targeting = {
            "geographic": ["United States", "Canada", "United Kingdom", "Germany"],
            "industries": ["Financial Services", "Technology", "Investment Management"],
            "company_size": "1000+" if segment == "enterprise" else "100-1000"
        }
        
        if channel == CampaignChannel.LINKEDIN_ADS:
            base_targeting.update({
                "job_titles": ["CTO", "VP Engineering", "Head of Trading", "Technology Director"],
                "skills": ["Trading Systems", "Financial Technology", "Risk Management"]
            })
        elif channel == CampaignChannel.PAID_SEARCH:
            base_targeting.update({
                "keywords": ["trading platform", "financial technology", "trading software"],
                "audiences": ["In-market for business software", "Technology decision makers"]
            })
        
        return base_targeting

    async def _develop_campaign_calendar_and_sequencing(self, timeline_months: int) -> Dict[str, Any]:
        """Develop integrated campaign calendar"""
        campaign_sequence = []
        
        # Create phased campaign launches
        for month in range(timeline_months):
            month_campaigns = {
                "month": month + 1,
                "campaigns": [
                    f"Demand Generation Wave {month + 1}",
                    f"Brand Awareness Push {month + 1}" if month % 2 == 0 else None,
                    f"Product Feature Campaign {month + 1}" if month == 1 else None
                ],
                "budget_allocation": {
                    "google_ads": 35000 + (month * 5000),
                    "linkedin_ads": 30000 + (month * 4000),
                    "content_marketing": 25000 + (month * 3000)
                }
            }
            campaign_sequence.append({k: v for k, v in month_campaigns.items() if v is not None})
        
        return {
            "campaign_plans": [],
            "channel_plans": [],
            "budget_allocations": [],
            "performance_forecasts": [],
            "campaign_calendar": {
                "campaign_sequence": campaign_sequence,
                "peak_periods": ["Month 2", "Month 3"],
                "resource_utilization": {"content_team": 0.85, "ad_ops": 0.75, "design": 0.80}
            }
        }

    async def _forecast_campaign_performance_and_roi(self, total_budget: float, 
                                                   objectives: List[str]) -> Dict[str, Any]:
        """Forecast campaign performance and ROI"""
        performance_forecasts = []
        
        # Forecast performance for each objective
        for objective in objectives:
            if objective == 'lead_generation':
                # Lead generation forecast
                forecast = {
                    "objective": objective,
                    "leads": int(total_budget / 175),  # $175 blended CPL
                    "pipeline_value": (total_budget / 175) * 28000,  # $28k avg opportunity
                    "roi": 4.8,
                    "cac": 185.00,
                    "conversion_rate": 0.032
                }
            else:  # Brand awareness
                forecast = {
                    "objective": objective,
                    "brand_lift": 0.25,
                    "reach": int(total_budget * 45),  # 45 reach per dollar
                    "engagement_rate": 0.045,
                    "share_of_voice_increase": 0.15,
                    "roi": 3.2  # Lower direct ROI, higher long-term value
                }
            
            performance_forecasts.append(forecast)
        
        return {
            "campaign_plans": [],
            "channel_plans": [],
            "budget_allocations": [],
            "performance_forecasts": performance_forecasts
        }

    async def _create_integrated_campaign_calendar(self, campaign_plans: List[Dict[str, Any]], 
                                                 timeline_months: int, total_budget: float) -> Dict[str, Any]:
        """Create integrated campaign calendar"""
        calendar = CampaignCalendar(
            calendar_name=f"Q1 2025 Integrated Campaign Calendar",
            planning_period="Q1_2025",
            total_period_budget=total_budget,
            planned_campaigns=[
                {
                    "campaign_id": plan.get('id'),
                    "campaign_name": plan.get('campaign_name'),
                    "start_month": 1,
                    "duration_months": timeline_months,
                    "budget": plan.get('total_budget', 0)
                }
                for plan in campaign_plans
            ],
            monthly_budget_distribution={
                f"month_{i+1}": total_budget / timeline_months
                for i in range(timeline_months)
            },
            projected_leads={
                f"month_{i+1}": int((total_budget / timeline_months) / 150)
                for i in range(timeline_months)
            }
        )
        
        return calendar.__dict__

    async def _optimize_cross_campaign_budget_allocation(self, campaign_plans: List[Dict[str, Any]], 
                                                       total_budget: float) -> Dict[str, Any]:
        """Optimize budget allocation across campaigns"""
        # Performance-weighted allocation
        campaign_scores = []
        for plan in campaign_plans:
            # Calculate performance score based on expected ROI and lead quality
            roi_score = plan.get('target_metrics', {}).get('roi', 4.0)
            conversion_score = plan.get('target_metrics', {}).get('conversion_rate', 0.03) * 100
            performance_score = (roi_score * 0.7) + (conversion_score * 0.3)
            campaign_scores.append(performance_score)
        
        # Allocate budget based on performance scores
        total_score = sum(campaign_scores)
        optimized_allocation = {}
        
        for i, plan in enumerate(campaign_plans):
            score_weight = campaign_scores[i] / total_score
            optimized_budget = total_budget * score_weight
            plan_id = plan.get('id', f'plan_{i}')
            optimized_allocation[plan_id] = optimized_budget
        
        return {
            "primary_channels": optimized_allocation,
            "optimization_score": 0.89,
            "performance_improvement": 0.18
        }

    async def _generate_campaign_optimization_recommendations(self, campaign_plans: List[Dict[str, Any]], 
                                                           optimized_budget: Dict[str, Any]) -> List[str]:
        """Generate campaign optimization recommendations"""
        recommendations = []
        
        # Budget optimization recommendations
        if optimized_budget.get('optimization_score', 0) > 0.85:
            recommendations.append("Budget allocation is well-optimized for maximum ROI")
        else:
            recommendations.append("Consider reallocating 15% budget from low-performing to high-ROI channels")
        
        # Campaign mix recommendations
        demand_gen_campaigns = len([c for c in campaign_plans if c.get('campaign_type') == 'demand_generation'])
        if demand_gen_campaigns > len(campaign_plans) * 0.7:
            recommendations.append("Balance campaign portfolio with more brand awareness and nurturing campaigns")
        
        # Channel recommendations
        recommendations.extend([
            "Increase LinkedIn advertising for enterprise segment targeting",
            "Implement progressive budget shifting based on 2-week performance cycles",
            "Add retargeting campaigns for website visitors who didn't convert",
            "Launch account-based marketing campaigns for top 100 target accounts",
            "Develop seasonal campaign adjustments for Q2 planning"
        ])
        
        return recommendations

    def _assess_budget_concentration_risk(self, budget_allocation: Dict[str, Any]) -> str:
        """Assess risk from budget concentration"""
        primary_channels = budget_allocation.get('primary_channels', {})
        if not primary_channels:
            return "low"
        
        max_allocation = max(primary_channels.values())
        total_allocation = sum(primary_channels.values())
        concentration_ratio = max_allocation / total_allocation
        
        if concentration_ratio > 0.5:
            return "high"
        elif concentration_ratio > 0.35:
            return "medium" 
        else:
            return "low"

    def _assess_performance_risk(self, performance_forecasts: List[Dict[str, Any]]) -> str:
        """Assess performance dependency risk"""
        if not performance_forecasts:
            return "medium"
        
        roi_variance = max([pf.get('roi', 3.0) for pf in performance_forecasts]) - min([pf.get('roi', 3.0) for pf in performance_forecasts])
        
        if roi_variance > 2.0:
            return "high"
        elif roi_variance > 1.0:
            return "medium"
        else:
            return "low"

    def _assess_timeline_risk(self, campaign_calendar: Dict[str, Any]) -> str:
        """Assess timeline execution risk"""
        peak_periods = len(campaign_calendar.get('peak_periods', []))
        resource_utilization = campaign_calendar.get('resource_utilization', {})
        
        if peak_periods > 2 or any(util > 0.9 for util in resource_utilization.values()):
            return "high"
        elif peak_periods > 1 or any(util > 0.8 for util in resource_utilization.values()):
            return "medium"
        else:
            return "low"

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and performance metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "capabilities": self.capabilities,
            "performance_metrics": {
                "campaigns_planned": self.campaigns_planned_count,
                "total_budget_optimized": self.total_budget_optimized,
                "average_campaign_roi": self.avg_campaign_roi,
                "planning_accuracy_rate": self.planning_accuracy_rate
            },
            "planning_targets": self.planning_targets,
            "channel_benchmarks": {
                channel.value: benchmarks 
                for channel, benchmarks in self.channel_benchmarks.items()
            },
            "active_planning": {
                "total_campaign_plans": len(self.campaign_plans),
                "total_channel_plans": len(self.channel_plans),
                "active_calendars": len(self.campaign_calendars)
            },
            "budget_templates": list(self.budget_templates.keys()),
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }

# Global agent instance
campaign_planner_agent = CampaignPlannerAgent()