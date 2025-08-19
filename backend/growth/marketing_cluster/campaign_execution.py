"""
Campaign Execution Agent - Real-Time Campaign Deployment & Optimization Engine

Ultra-responsive campaign execution agent that deploys, monitors, and optimizes
marketing campaigns in real-time with automated performance optimization.
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

class CampaignStatus(Enum):
    """Campaign execution statuses"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    LAUNCHING = "launching"
    ACTIVE = "active"
    OPTIMIZING = "optimizing"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OptimizationTrigger(Enum):
    """Automated optimization triggers"""
    PERFORMANCE_DECLINE = "performance_decline"
    BUDGET_PACING = "budget_pacing"
    CTR_THRESHOLD = "ctr_threshold"
    CONVERSION_RATE = "conversion_rate"
    CPL_THRESHOLD = "cpl_threshold"
    AUDIENCE_SATURATION = "audience_saturation"
    COMPETITIVE_PRESSURE = "competitive_pressure"
    SEASONAL_ADJUSTMENT = "seasonal_adjustment"

class ExecutionAction(Enum):
    """Campaign execution actions"""
    LAUNCH_CAMPAIGN = "launch_campaign"
    PAUSE_CAMPAIGN = "pause_campaign"
    ADJUST_BUDGET = "adjust_budget"
    MODIFY_TARGETING = "modify_targeting"
    UPDATE_CREATIVE = "update_creative"
    SCALE_PERFORMANCE = "scale_performance"
    SHIFT_BUDGET = "shift_budget"
    ADD_KEYWORDS = "add_keywords"

@dataclass
class CampaignExecution:
    """Campaign execution tracking and management"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str = ""
    campaign_name: str = ""
    
    # Execution details
    status: CampaignStatus = CampaignStatus.DRAFT
    channel: CampaignChannel = CampaignChannel.PAID_SEARCH
    launch_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Budget and pacing
    total_budget: float = 0.0
    daily_budget: float = 0.0
    spent_budget: float = 0.0
    remaining_budget: float = 0.0
    budget_pace: float = 0.0  # % of daily budget spent
    
    # Performance metrics
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    ctr: float = 0.0
    conversion_rate: float = 0.0
    cpc: float = 0.0
    cpl: float = 0.0
    roas: float = 0.0
    
    # Targeting and creative
    target_audience: Dict[str, Any] = field(default_factory=dict)
    active_creatives: List[Dict[str, Any]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Optimization tracking
    optimization_actions: List[Dict[str, Any]] = field(default_factory=list)
    last_optimization: Optional[datetime] = None
    optimization_frequency: int = 24  # hours between optimizations
    
    # Performance benchmarks
    target_ctr: float = 0.0
    target_conversion_rate: float = 0.0
    target_cpl: float = 0.0
    target_roas: float = 0.0
    
    # A/B testing
    ab_tests: List[Dict[str, Any]] = field(default_factory=list)
    winning_variants: List[str] = field(default_factory=list)

@dataclass
class OptimizationRule:
    """Automated optimization rule"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str = ""
    trigger: OptimizationTrigger = OptimizationTrigger.PERFORMANCE_DECLINE
    condition: str = ""  # JSON condition logic
    action: ExecutionAction = ExecutionAction.ADJUST_BUDGET
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Rule configuration
    enabled: bool = True
    priority: int = 1  # 1=highest, 5=lowest
    cooldown_hours: int = 24
    
    # Performance tracking
    triggered_count: int = 0
    success_count: int = 0
    last_triggered: Optional[datetime] = None

@dataclass
class ExecutionDashboard:
    """Real-time campaign execution dashboard"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dashboard_name: str = ""
    
    # Campaign overview
    active_campaigns: List[str] = field(default_factory=list)
    total_active_budget: float = 0.0
    total_daily_spend: float = 0.0
    
    # Performance summary
    total_impressions: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    overall_ctr: float = 0.0
    overall_conversion_rate: float = 0.0
    blended_cpl: float = 0.0
    
    # Channel performance
    channel_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    top_performing_campaigns: List[str] = field(default_factory=list)
    underperforming_campaigns: List[str] = field(default_factory=list)
    
    # Optimization alerts
    active_alerts: List[Dict[str, Any]] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)
    
    # Forecasting
    daily_pace_projection: Dict[str, float] = field(default_factory=dict)
    monthly_performance_forecast: Dict[str, float] = field(default_factory=dict)

class CampaignExecutionAgent:
    """Real-time campaign execution and optimization agent"""
    
    def __init__(self):
        self.agent_id = "campaign-execution-agent"
        self.name = "Campaign Execution Agent"
        self.specialization = "real_time_campaign_deployment_optimization"
        self.capabilities = [
            "campaign_deployment", "real_time_optimization", "budget_management",
            "performance_monitoring", "automated_scaling", "multi_channel_coordination"
        ]
        
        # Execution database
        self.campaign_executions: Dict[str, CampaignExecution] = {}
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.execution_dashboards: Dict[str, ExecutionDashboard] = {}
        
        # Channel execution capabilities
        self.channel_integrations = {
            CampaignChannel.PAID_SEARCH: {
                "api_enabled": True,
                "real_time_optimization": True,
                "automated_bidding": True,
                "audience_sync": True
            },
            CampaignChannel.PAID_SOCIAL: {
                "api_enabled": True,
                "real_time_optimization": True,
                "automated_bidding": False,
                "audience_sync": True
            },
            CampaignChannel.PAID_SOCIAL: {
                "api_enabled": True,
                "real_time_optimization": True,
                "automated_bidding": True,
                "audience_sync": True
            },
            CampaignChannel.CONTENT_MARKETING: {
                "api_enabled": False,
                "real_time_optimization": False,
                "automated_bidding": False,
                "audience_sync": False
            }
        }
        
        # Performance benchmarks and thresholds
        self.performance_thresholds = {
            "min_ctr": 0.02,           # 2% minimum CTR
            "max_cpl": 200.0,          # $200 maximum CPL
            "min_conversion_rate": 0.015,  # 1.5% minimum conversion rate
            "min_roas": 2.0,           # 2:1 minimum ROAS
            "budget_pace_min": 0.8,    # 80% minimum daily budget pace
            "budget_pace_max": 1.2     # 120% maximum daily budget pace
        }
        
        # Optimization rules templates
        self.default_optimization_rules = [
            {
                "rule_name": "Low CTR Performance Alert",
                "trigger": OptimizationTrigger.CTR_THRESHOLD,
                "condition": "ctr < 0.02",
                "action": ExecutionAction.UPDATE_CREATIVE,
                "priority": 1
            },
            {
                "rule_name": "High CPL Budget Shift",
                "trigger": OptimizationTrigger.CPL_THRESHOLD,
                "condition": "cpl > 200",
                "action": ExecutionAction.SHIFT_BUDGET,
                "priority": 2
            },
            {
                "rule_name": "Budget Pacing Adjustment",
                "trigger": OptimizationTrigger.BUDGET_PACING,
                "condition": "budget_pace < 0.8 OR budget_pace > 1.2",
                "action": ExecutionAction.ADJUST_BUDGET,
                "priority": 3
            }
        ]
        
        # Execution targets
        self.execution_targets = {
            "campaign_launch_time_minutes": 30,
            "optimization_response_time_minutes": 15,
            "daily_monitoring_frequency": 12,  # Every 2 hours
            "automated_optimization_rate": 0.85,
            "target_uptime": 0.995  # 99.5% uptime
        }
        
        # Performance metrics
        self.campaigns_launched_count = 0
        self.optimizations_executed_count = 0
        self.total_budget_managed = 0.0
        self.avg_campaign_performance_lift = 0.0
        self.system_uptime = 0.995
        
        logger.info(f"Campaign Execution Agent initialized - targeting {self.execution_targets['campaign_launch_time_minutes']}min launch time")

    async def execute_campaign_deployment_blitz(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real-time campaign deployment and optimization blitz"""
        deployment_type = parameters.get('deployment_type', 'comprehensive')
        campaigns_to_launch = parameters.get('campaign_configs', [])
        optimization_intensity = parameters.get('optimization_intensity', 'high')
        budget_allocation = parameters.get('budget_allocation', {})
        real_time_monitoring = parameters.get('real_time_monitoring', True)
        
        logger.info(f"Starting {deployment_type} campaign deployment - {len(campaigns_to_launch)} campaigns")
        
        campaigns_launched = []
        optimizations_applied = []
        performance_alerts = []
        budget_adjustments = []
        
        # Execute parallel campaign deployment tasks
        deployment_tasks = [
            self._launch_multi_channel_campaigns(campaigns_to_launch, budget_allocation),
            self._apply_real_time_optimization_rules(optimization_intensity),
            self._monitor_campaign_performance_and_alerts(),
            self._execute_automated_budget_management(),
            self._coordinate_cross_channel_optimization()
        ]
        
        deployment_results = await asyncio.gather(*deployment_tasks, return_exceptions=True)
        
        # Process and consolidate results
        for i, result in enumerate(deployment_results):
            if isinstance(result, Exception):
                logger.error(f"Campaign deployment task {i} failed: {result}")
                continue
                
            campaigns_launched.extend(result.get('campaigns_launched', []))
            optimizations_applied.extend(result.get('optimizations_applied', []))
            performance_alerts.extend(result.get('performance_alerts', []))
            budget_adjustments.extend(result.get('budget_adjustments', []))
        
        # Create real-time execution dashboard
        execution_dashboard = await self._create_real_time_execution_dashboard(
            campaigns_launched, optimization_intensity
        )
        
        # Execute immediate optimization actions
        immediate_actions = await self._execute_immediate_optimization_actions(
            campaigns_launched, performance_alerts
        )
        
        # Update performance metrics
        self.campaigns_launched_count += len(campaigns_launched)
        self.optimizations_executed_count += len(optimizations_applied)
        self.total_budget_managed += sum(c.get('budget', 0) for c in campaigns_launched)
        
        logger.info(f"Campaign deployment completed: {len(campaigns_launched)} campaigns live, " +
                   f"{len(optimizations_applied)} optimizations applied, {len(immediate_actions)} immediate actions")
        
        return {
            "success": True,
            "deployment_type": deployment_type,
            "execution_time_minutes": 25,  # Simulated
            "deployment_summary": {
                "campaigns_launched": len(campaigns_launched),
                "total_budget_deployed": sum(c.get('budget', 0) for c in campaigns_launched),
                "channels_activated": len(set(c.get('channel') for c in campaigns_launched)),
                "optimizations_applied": len(optimizations_applied),
                "performance_alerts_generated": len(performance_alerts)
            },
            "campaign_performance": {
                "google_ads_campaigns": len([c for c in campaigns_launched if c.get('channel') == 'google_ads']),
                "linkedin_campaigns": len([c for c in campaigns_launched if c.get('channel') == 'linkedin_ads']),
                "facebook_campaigns": len([c for c in campaigns_launched if c.get('channel') == 'facebook_ads']),
                "average_launch_time_minutes": sum(c.get('launch_time_minutes', 30) for c in campaigns_launched) / max(len(campaigns_launched), 1)
            },
            "real_time_optimization": {
                "optimization_rules_active": len([rule for rule in self.optimization_rules.values() if rule.enabled]),
                "automated_adjustments": len([opt for opt in optimizations_applied if opt.get('automated')]),
                "performance_improvements": len([opt for opt in optimizations_applied if opt.get('performance_lift', 0) > 0]),
                "average_optimization_response_time": sum(opt.get('response_time_minutes', 15) for opt in optimizations_applied) / max(len(optimizations_applied), 1)
            },
            "budget_management": {
                "total_budget_allocated": sum(adj.get('budget_allocated', 0) for adj in budget_adjustments),
                "budget_shifts_executed": len([adj for adj in budget_adjustments if adj.get('type') == 'budget_shift']),
                "pacing_adjustments": len([adj for adj in budget_adjustments if adj.get('type') == 'pacing_adjustment']),
                "budget_utilization_rate": sum(adj.get('utilization_rate', 0.85) for adj in budget_adjustments) / max(len(budget_adjustments), 1)
            },
            "performance_monitoring": {
                "dashboard_id": execution_dashboard.get('id'),
                "active_campaigns_monitored": len(execution_dashboard.get('active_campaigns', [])),
                "performance_alerts_active": len(execution_dashboard.get('active_alerts', [])),
                "optimization_opportunities": len(execution_dashboard.get('optimization_opportunities', []))
            },
            "immediate_actions": immediate_actions,
            "next_4h_schedule": await self._forecast_next_4h_execution_activity(campaigns_launched),
            "system_health": {
                "campaign_uptime": self.system_uptime,
                "api_connection_status": "healthy",
                "optimization_engine_status": "active",
                "monitoring_frequency": f"Every {24 // self.execution_targets['daily_monitoring_frequency']} hours"
            }
        }

    async def _launch_multi_channel_campaigns(self, campaign_configs: List[Dict[str, Any]], 
                                            budget_allocation: Dict[str, float]) -> Dict[str, Any]:
        """Launch campaigns across multiple channels"""
        campaigns_launched = []
        
        # Launch campaigns based on configurations
        for config in campaign_configs:
            campaign = await self._launch_individual_campaign(config, budget_allocation)
            if campaign:
                campaigns_launched.append(campaign)
        
        return {
            "campaigns_launched": campaigns_launched,
            "optimizations_applied": [],
            "performance_alerts": [],
            "budget_adjustments": []
        }

    async def _launch_individual_campaign(self, config: Dict[str, Any], 
                                        budget_allocation: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Launch individual campaign with real-time setup"""
        channel = CampaignChannel(config.get('channel', 'google_ads'))
        campaign_name = config.get('name', f'Campaign_{datetime.now().strftime("%Y%m%d_%H%M")}')
        
        # Check channel integration capability
        integration = self.channel_integrations.get(channel, {})
        if not integration.get('api_enabled', False):
            logger.warning(f"API not enabled for channel {channel.value}")
            return None
        
        # Create campaign execution record
        execution = CampaignExecution(
            campaign_name=campaign_name,
            channel=channel,
            status=CampaignStatus.LAUNCHING,
            total_budget=config.get('budget', 10000.0),
            daily_budget=config.get('daily_budget', 500.0),
            target_audience=config.get('targeting', {}),
            active_creatives=config.get('creatives', []),
            keywords=config.get('keywords', []),
            target_ctr=self.performance_thresholds.get('min_ctr', 0.02),
            target_conversion_rate=self.performance_thresholds.get('min_conversion_rate', 0.015),
            target_cpl=self.performance_thresholds.get('max_cpl', 200.0),
            target_roas=self.performance_thresholds.get('min_roas', 2.0)
        )
        
        # Simulate campaign launch process
        launch_result = await self._execute_campaign_launch(execution, channel)
        
        if launch_result.get('success'):
            execution.status = CampaignStatus.ACTIVE
            execution.launch_date = datetime.now()
            self.campaign_executions[execution.id] = execution
            
            return {
                **execution.__dict__,
                "launch_result": launch_result,
                "launch_time_minutes": launch_result.get('launch_time_minutes', 30)
            }
        
        return None

    async def _execute_campaign_launch(self, execution: CampaignExecution, 
                                     channel: CampaignChannel) -> Dict[str, Any]:
        """Execute campaign launch on specific channel"""
        # Simulate channel-specific launch process
        if channel == CampaignChannel.PAID_SEARCH:
            return await self._launch_google_ads_campaign(execution)
        elif channel == CampaignChannel.PAID_SOCIAL:
            return await self._launch_linkedin_campaign(execution)
        elif channel == CampaignChannel.PAID_SOCIAL:
            return await self._launch_facebook_campaign(execution)
        else:
            return {"success": False, "error": "Channel not supported"}

    async def _launch_google_ads_campaign(self, execution: CampaignExecution) -> Dict[str, Any]:
        """Launch Google Ads campaign"""
        # Simulate Google Ads API integration
        return {
            "success": True,
            "campaign_id": f"gads_{execution.id}",
            "launch_time_minutes": 25,
            "initial_status": "active",
            "keywords_activated": len(execution.keywords),
            "ad_groups_created": len(execution.active_creatives),
            "targeting_applied": True
        }

    async def _launch_linkedin_campaign(self, execution: CampaignExecution) -> Dict[str, Any]:
        """Launch LinkedIn Ads campaign"""
        # Simulate LinkedIn Campaign Manager API integration
        return {
            "success": True,
            "campaign_id": f"li_{execution.id}",
            "launch_time_minutes": 35,
            "initial_status": "active",
            "audience_size": 125000,
            "targeting_criteria": execution.target_audience,
            "creative_formats": ["sponsored_content", "message_ads"]
        }

    async def _launch_facebook_campaign(self, execution: CampaignExecution) -> Dict[str, Any]:
        """Launch Facebook Ads campaign"""
        # Simulate Facebook Marketing API integration
        return {
            "success": True,
            "campaign_id": f"fb_{execution.id}",
            "launch_time_minutes": 20,
            "initial_status": "active",
            "audience_size": 250000,
            "placement_options": ["feed", "stories", "audience_network"],
            "optimization_goal": "conversions"
        }

    async def _apply_real_time_optimization_rules(self, intensity: str) -> Dict[str, Any]:
        """Apply real-time optimization rules"""
        optimizations_applied = []
        
        # Initialize default optimization rules if not exists
        if not self.optimization_rules:
            await self._initialize_optimization_rules()
        
        # Check and apply optimization rules
        for rule in self.optimization_rules.values():
            if not rule.enabled:
                continue
                
            # Check if rule should be triggered
            should_trigger = await self._evaluate_optimization_rule(rule)
            if should_trigger:
                optimization_result = await self._execute_optimization_action(rule)
                optimizations_applied.append({
                    "rule_name": rule.rule_name,
                    "trigger": rule.trigger.value,
                    "action": rule.action.value,
                    "result": optimization_result,
                    "automated": True,
                    "performance_lift": optimization_result.get('performance_lift', 0.15),
                    "response_time_minutes": optimization_result.get('response_time_minutes', 12)
                })
        
        return {
            "campaigns_launched": [],
            "optimizations_applied": optimizations_applied,
            "performance_alerts": [],
            "budget_adjustments": []
        }

    async def _initialize_optimization_rules(self):
        """Initialize default optimization rules"""
        for rule_config in self.default_optimization_rules:
            rule = OptimizationRule(
                rule_name=rule_config["rule_name"],
                trigger=rule_config["trigger"],
                condition=rule_config["condition"],
                action=rule_config["action"],
                priority=rule_config["priority"]
            )
            self.optimization_rules[rule.id] = rule

    async def _evaluate_optimization_rule(self, rule: OptimizationRule) -> bool:
        """Evaluate if optimization rule should be triggered"""
        # Check cooldown period
        if rule.last_triggered:
            time_since_last = (datetime.now() - rule.last_triggered).total_seconds() / 3600
            if time_since_last < rule.cooldown_hours:
                return False
        
        # Simulate rule condition evaluation
        if rule.trigger == OptimizationTrigger.CTR_THRESHOLD:
            # Check if any campaign has low CTR
            low_ctr_campaigns = [c for c in self.campaign_executions.values() 
                               if c.status == CampaignStatus.ACTIVE and c.ctr < 0.02]
            return len(low_ctr_campaigns) > 0
        
        elif rule.trigger == OptimizationTrigger.CPL_THRESHOLD:
            # Check if any campaign has high CPL
            high_cpl_campaigns = [c for c in self.campaign_executions.values()
                                if c.status == CampaignStatus.ACTIVE and c.cpl > 200]
            return len(high_cpl_campaigns) > 0
        
        elif rule.trigger == OptimizationTrigger.BUDGET_PACING:
            # Check budget pacing issues
            pacing_issues = [c for c in self.campaign_executions.values()
                           if c.status == CampaignStatus.ACTIVE and 
                           (c.budget_pace < 0.8 or c.budget_pace > 1.2)]
            return len(pacing_issues) > 0
        
        return False

    async def _execute_optimization_action(self, rule: OptimizationRule) -> Dict[str, Any]:
        """Execute optimization action based on rule"""
        # Update rule tracking
        rule.triggered_count += 1
        rule.last_triggered = datetime.now()
        
        # Execute action based on type
        if rule.action == ExecutionAction.UPDATE_CREATIVE:
            return await self._update_campaign_creatives(rule)
        elif rule.action == ExecutionAction.ADJUST_BUDGET:
            return await self._adjust_campaign_budgets(rule)
        elif rule.action == ExecutionAction.SHIFT_BUDGET:
            return await self._shift_budget_allocation(rule)
        elif rule.action == ExecutionAction.MODIFY_TARGETING:
            return await self._modify_campaign_targeting(rule)
        
        return {"success": False, "error": "Unknown action type"}

    async def _update_campaign_creatives(self, rule: OptimizationRule) -> Dict[str, Any]:
        """Update campaign creatives for better performance"""
        # Find campaigns with low CTR
        low_performing_campaigns = [c for c in self.campaign_executions.values() 
                                  if c.status == CampaignStatus.ACTIVE and c.ctr < 0.02]
        
        creatives_updated = 0
        for campaign in low_performing_campaigns[:3]:  # Update top 3
            # Simulate creative update
            campaign.active_creatives.append({
                "creative_id": f"creative_{datetime.now().strftime('%H%M%S')}",
                "type": "responsive_ad",
                "status": "active",
                "performance_prediction": "high"
            })
            creatives_updated += 1
        
        rule.success_count += 1 if creatives_updated > 0 else 0
        
        return {
            "success": creatives_updated > 0,
            "campaigns_updated": creatives_updated,
            "performance_lift": 0.18,  # 18% CTR improvement
            "response_time_minutes": 10
        }

    async def _adjust_campaign_budgets(self, rule: OptimizationRule) -> Dict[str, Any]:
        """Adjust campaign budgets based on pacing"""
        budget_adjustments = 0
        total_adjustment = 0.0
        
        # Find campaigns with pacing issues
        pacing_campaigns = [c for c in self.campaign_executions.values()
                          if c.status == CampaignStatus.ACTIVE and 
                          (c.budget_pace < 0.8 or c.budget_pace > 1.2)]
        
        for campaign in pacing_campaigns:
            if campaign.budget_pace < 0.8:
                # Increase budget for under-spending campaigns
                adjustment = campaign.daily_budget * 0.2  # 20% increase
                campaign.daily_budget += adjustment
                total_adjustment += adjustment
            elif campaign.budget_pace > 1.2:
                # Decrease budget for over-spending campaigns
                adjustment = campaign.daily_budget * 0.15  # 15% decrease
                campaign.daily_budget -= adjustment
                total_adjustment -= adjustment
            
            budget_adjustments += 1
        
        rule.success_count += 1 if budget_adjustments > 0 else 0
        
        return {
            "success": budget_adjustments > 0,
            "campaigns_adjusted": budget_adjustments,
            "total_budget_adjustment": total_adjustment,
            "performance_lift": 0.12,  # 12% efficiency improvement
            "response_time_minutes": 5
        }

    async def _shift_budget_allocation(self, rule: OptimizationRule) -> Dict[str, Any]:
        """Shift budget from low to high performing campaigns"""
        # Find high CPL campaigns to reduce budget
        high_cpl_campaigns = [c for c in self.campaign_executions.values()
                            if c.status == CampaignStatus.ACTIVE and c.cpl > 200]
        
        # Find low CPL campaigns to increase budget
        low_cpl_campaigns = [c for c in self.campaign_executions.values()
                           if c.status == CampaignStatus.ACTIVE and c.cpl < 100]
        
        budget_shifted = 0.0
        campaigns_affected = 0
        
        for high_campaign in high_cpl_campaigns[:2]:  # Top 2 high CPL
            for low_campaign in low_cpl_campaigns[:2]:  # Top 2 low CPL
                shift_amount = min(high_campaign.daily_budget * 0.2, 500.0)  # 20% or $500 max
                
                high_campaign.daily_budget -= shift_amount
                low_campaign.daily_budget += shift_amount
                budget_shifted += shift_amount
                campaigns_affected += 2
                break  # One shift per high campaign
        
        rule.success_count += 1 if budget_shifted > 0 else 0
        
        return {
            "success": budget_shifted > 0,
            "budget_shifted": budget_shifted,
            "campaigns_affected": campaigns_affected,
            "performance_lift": 0.25,  # 25% efficiency improvement
            "response_time_minutes": 8
        }

    async def _modify_campaign_targeting(self, rule: OptimizationRule) -> Dict[str, Any]:
        """Modify campaign targeting for better performance"""
        return {
            "success": True,
            "targeting_updates": 3,
            "audience_expansion": 0.15,  # 15% audience expansion
            "performance_lift": 0.10,
            "response_time_minutes": 15
        }

    async def _monitor_campaign_performance_and_alerts(self) -> Dict[str, Any]:
        """Monitor campaign performance and generate alerts"""
        performance_alerts = []
        
        # Check active campaigns for performance issues
        for campaign in self.campaign_executions.values():
            if campaign.status != CampaignStatus.ACTIVE:
                continue
            
            # Generate performance alerts
            alerts = await self._generate_performance_alerts(campaign)
            performance_alerts.extend(alerts)
        
        return {
            "campaigns_launched": [],
            "optimizations_applied": [],
            "performance_alerts": performance_alerts,
            "budget_adjustments": []
        }

    async def _generate_performance_alerts(self, campaign: CampaignExecution) -> List[Dict[str, Any]]:
        """Generate performance alerts for campaign"""
        alerts = []
        
        # Simulate performance data
        campaign.ctr = 0.025  # 2.5% CTR
        campaign.conversion_rate = 0.018  # 1.8% conversion rate
        campaign.cpl = 175.0  # $175 CPL
        campaign.budget_pace = 0.95  # 95% budget pace
        
        # Check CTR threshold
        if campaign.ctr < self.performance_thresholds["min_ctr"]:
            alerts.append({
                "campaign_id": campaign.id,
                "alert_type": "low_ctr",
                "severity": "medium",
                "message": f"CTR {campaign.ctr:.3f} below threshold {self.performance_thresholds['min_ctr']}",
                "recommendation": "Update creative assets or adjust targeting"
            })
        
        # Check CPL threshold
        if campaign.cpl > self.performance_thresholds["max_cpl"]:
            alerts.append({
                "campaign_id": campaign.id,
                "alert_type": "high_cpl",
                "severity": "high",
                "message": f"CPL ${campaign.cpl:.2f} exceeds threshold ${self.performance_thresholds['max_cpl']}",
                "recommendation": "Pause underperforming keywords or adjust bidding"
            })
        
        # Check budget pacing
        if campaign.budget_pace < self.performance_thresholds["budget_pace_min"]:
            alerts.append({
                "campaign_id": campaign.id,
                "alert_type": "slow_pacing",
                "severity": "low",
                "message": f"Budget pace {campaign.budget_pace:.2f} below target",
                "recommendation": "Increase bids or expand targeting"
            })
        
        return alerts

    async def _execute_automated_budget_management(self) -> Dict[str, Any]:
        """Execute automated budget management"""
        budget_adjustments = []
        
        # Calculate total spend and remaining budget
        total_daily_spend = sum(c.daily_budget for c in self.campaign_executions.values() 
                              if c.status == CampaignStatus.ACTIVE)
        
        # Execute budget management actions
        for campaign in self.campaign_executions.values():
            if campaign.status != CampaignStatus.ACTIVE:
                continue
            
            # Simulate budget utilization
            campaign.spent_budget = campaign.daily_budget * 0.85  # 85% utilization
            campaign.remaining_budget = campaign.total_budget - campaign.spent_budget
            campaign.budget_pace = campaign.spent_budget / campaign.daily_budget
            
            budget_adjustment = {
                "campaign_id": campaign.id,
                "type": "utilization_tracking",
                "budget_allocated": campaign.daily_budget,
                "utilization_rate": campaign.budget_pace,
                "remaining_budget": campaign.remaining_budget
            }
            budget_adjustments.append(budget_adjustment)
        
        return {
            "campaigns_launched": [],
            "optimizations_applied": [],
            "performance_alerts": [],
            "budget_adjustments": budget_adjustments
        }

    async def _coordinate_cross_channel_optimization(self) -> Dict[str, Any]:
        """Coordinate optimization across channels"""
        # Group campaigns by channel
        channel_groups = {}
        for campaign in self.campaign_executions.values():
            if campaign.status == CampaignStatus.ACTIVE:
                channel = campaign.channel.value
                if channel not in channel_groups:
                    channel_groups[channel] = []
                channel_groups[channel].append(campaign)
        
        # Coordinate optimization actions
        coordination_actions = []
        for channel, campaigns in channel_groups.items():
            if len(campaigns) > 1:
                # Find best and worst performing campaigns
                best_campaign = max(campaigns, key=lambda c: c.conversion_rate)
                worst_campaign = min(campaigns, key=lambda c: c.conversion_rate)
                
                # Apply learnings from best to worst
                coordination_actions.append({
                    "channel": channel,
                    "action": "apply_best_practices",
                    "source_campaign": best_campaign.id,
                    "target_campaign": worst_campaign.id,
                    "optimization_type": "cross_campaign_learning"
                })
        
        return {
            "campaigns_launched": [],
            "optimizations_applied": coordination_actions,
            "performance_alerts": [],
            "budget_adjustments": []
        }

    async def _create_real_time_execution_dashboard(self, campaigns_launched: List[Dict[str, Any]], 
                                                  optimization_intensity: str) -> Dict[str, Any]:
        """Create real-time execution dashboard"""
        active_campaigns = [c.get('id') for c in campaigns_launched]
        total_budget = sum(c.get('budget', 0) for c in campaigns_launched)
        
        dashboard = ExecutionDashboard(
            dashboard_name="Real-Time Campaign Execution Dashboard",
            active_campaigns=active_campaigns,
            total_active_budget=total_budget,
            total_daily_spend=sum(c.get('daily_budget', 0) for c in campaigns_launched),
            total_impressions=125000,  # Simulated
            total_clicks=3500,         # Simulated
            total_conversions=95,      # Simulated
            overall_ctr=0.028,
            overall_conversion_rate=0.027,
            blended_cpl=185.50,
            channel_performance={
                "google_ads": {"impressions": 75000, "clicks": 2100, "conversions": 58},
                "linkedin_ads": {"impressions": 35000, "clicks": 980, "conversions": 25},
                "facebook_ads": {"impressions": 15000, "clicks": 420, "conversions": 12}
            },
            optimization_opportunities=[
                "Increase budget for high-performing Google Ads campaigns",
                "Update LinkedIn creative assets for better engagement",
                "Expand audience targeting for Facebook campaigns"
            ]
        )
        
        self.execution_dashboards[dashboard.id] = dashboard
        return dashboard.__dict__

    async def _execute_immediate_optimization_actions(self, campaigns_launched: List[Dict[str, Any]], 
                                                    performance_alerts: List[Dict[str, Any]]) -> List[str]:
        """Execute immediate optimization actions"""
        immediate_actions = []
        
        # Process high-severity alerts
        high_severity_alerts = [alert for alert in performance_alerts if alert.get('severity') == 'high']
        for alert in high_severity_alerts:
            immediate_actions.append(f"URGENT: Address {alert.get('alert_type')} for campaign {alert.get('campaign_id')}")
        
        # Scale high-performing campaigns
        high_performers = [c for c in campaigns_launched if c.get('launch_result', {}).get('success')]
        if high_performers:
            immediate_actions.append(f"Scale budget for {len(high_performers)} high-performing campaigns")
        
        # General optimization actions
        immediate_actions.extend([
            "Monitor campaign performance every 2 hours",
            "Prepare A/B test variants for underperforming creatives",
            "Update keyword lists based on search term reports",
            "Optimize landing pages for better conversion rates"
        ])
        
        return immediate_actions

    async def _forecast_next_4h_execution_activity(self, campaigns_launched: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Forecast execution activity for next 4 hours"""
        return {
            "scheduled_optimizations": 6,
            "budget_adjustments_planned": 3,
            "creative_updates_scheduled": 2,
            "performance_reviews": 1,
            "estimated_impressions": 35000,
            "estimated_clicks": 950,
            "estimated_conversions": 28
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and performance metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "capabilities": self.capabilities,
            "performance_metrics": {
                "campaigns_launched": self.campaigns_launched_count,
                "optimizations_executed": self.optimizations_executed_count,
                "total_budget_managed": self.total_budget_managed,
                "avg_campaign_performance_lift": self.avg_campaign_performance_lift,
                "system_uptime": self.system_uptime
            },
            "execution_targets": self.execution_targets,
            "performance_thresholds": self.performance_thresholds,
            "channel_integrations": {
                channel.value: integration 
                for channel, integration in self.channel_integrations.items()
            },
            "active_execution": {
                "active_campaigns": len([c for c in self.campaign_executions.values() if c.status == CampaignStatus.ACTIVE]),
                "optimization_rules": len([r for r in self.optimization_rules.values() if r.enabled]),
                "execution_dashboards": len(self.execution_dashboards)
            },
            "optimization_engine": {
                "total_rules": len(self.optimization_rules),
                "active_rules": len([r for r in self.optimization_rules.values() if r.enabled]),
                "optimization_frequency": self.execution_targets["daily_monitoring_frequency"]
            },
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }

# Global agent instance
campaign_execution_agent = CampaignExecutionAgent()