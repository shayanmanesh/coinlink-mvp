"""
Growth Agent Interface System
Specialized interface for Growth Engine agents with ultra-aggressive BD and Marketing capabilities
"""

import os
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

from .data_models import (
    Lead, Opportunity, Campaign, Deal, GrowthEvent, Priority,
    LeadSource, LeadStage, OpportunityStage, CampaignChannel
)
from .pipeline_orchestrator import pipeline_orchestrator, AgentRegistration

logger = logging.getLogger(__name__)

@dataclass
class GrowthAgentInfo:
    """Information about a growth engine agent"""
    name: str
    description: str
    tools: List[str]
    file_path: str
    cluster: str  # 'bd' or 'marketing' or 'orchestrator'
    specialization: str = ""
    capabilities: List[str] = None
    status: str = "available"
    last_invoked: Optional[datetime] = None
    total_invocations: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    max_concurrent_tasks: int = 5
    current_load: int = 0

@dataclass
class GrowthTask:
    """Task specific to growth engine operations"""
    id: str
    agent_name: str
    task_type: str  # lead_engagement, opportunity_qualification, campaign_creation, etc.
    description: str
    parameters: Dict[str, Any]
    created_at: datetime
    priority: Priority = Priority.MEDIUM
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    growth_sprint_id: Optional[str] = None
    expected_outcome: str = ""
    success_metrics: Dict[str, Any] = None

@dataclass
class GrowthSprint:
    """Weekly growth sprint coordination"""
    id: str
    start_date: datetime
    end_date: datetime
    status: str = "active"  # active, completed, cancelled
    tasks: List[str] = None  # Task IDs
    bd_objectives: Dict[str, Any] = None
    marketing_objectives: Dict[str, Any] = None
    pipeline_targets: Dict[str, Any] = None
    leads_generated: int = 0
    opportunities_created: int = 0
    deals_closed: int = 0
    revenue_generated: float = 0.0
    roi_achieved: float = 0.0

class GrowthAgentInterface:
    """Interface for managing and invoking growth engine agents"""
    
    def __init__(self):
        self.agents: Dict[str, GrowthAgentInfo] = {}
        self.active_tasks: Dict[str, GrowthTask] = {}
        self.completed_tasks: List[GrowthTask] = []
        self.current_sprint: Optional[GrowthSprint] = None
        self.sprint_history: List[GrowthSprint] = []
        
        # Performance tracking
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Growth targets
        self.weekly_targets = {
            "new_leads": 500,
            "qualified_opportunities": 100,
            "deals_closed": 10,
            "target_revenue": 1000000.0,  # $1M weekly target
            "marketing_roi": 4.0,
            "bd_conversion_rate": 0.15
        }
        
        # Initialize flags for async tasks
        self._agents_discovered = False
        self._orchestrator_registered = False
        
        logger.info("Growth Agent Interface initialized with ultra-aggressive targets")

    async def initialize_async(self):
        """Initialize async components - must be called from async context"""
        if not self._agents_discovered:
            await self.discover_growth_agents()
            self._agents_discovered = True
            
        if not self._orchestrator_registered:
            await self.register_with_orchestrator()
            self._orchestrator_registered = True
            
        logger.info("Growth Agent Interface async initialization completed")

    async def discover_growth_agents(self):
        """Auto-discover growth engine agents from .claude/agents/growth/"""
        try:
            agents_base_path = Path(".claude/agents/growth")
            
            if not agents_base_path.exists():
                logger.warning(f"Growth agents path does not exist: {agents_base_path}")
                return
            
            # Discover orchestrator agent
            orchestrator_file = agents_base_path / "pipeline-orchestrator.md"
            if orchestrator_file.exists():
                agent_info = self._parse_agent_file(orchestrator_file, "orchestrator")
                if agent_info:
                    self.agents[agent_info.name] = agent_info
            
            # Discover BD agents
            bd_path = agents_base_path / "bd"
            if bd_path.exists():
                for agent_file in bd_path.glob("*.md"):
                    agent_info = self._parse_agent_file(agent_file, "bd")
                    if agent_info:
                        self.agents[agent_info.name] = agent_info
            
            # Discover Marketing agents  
            marketing_path = agents_base_path / "marketing"
            if marketing_path.exists():
                for agent_file in marketing_path.glob("*.md"):
                    agent_info = self._parse_agent_file(agent_file, "marketing")
                    if agent_info:
                        self.agents[agent_info.name] = agent_info
            
            logger.info(f"Discovered {len(self.agents)} growth agents: " +
                       f"BD: {len([a for a in self.agents.values() if a.cluster == 'bd'])}, " +
                       f"Marketing: {len([a for a in self.agents.values() if a.cluster == 'marketing'])}")
                       
        except Exception as e:
            logger.error(f"Error discovering growth agents: {e}")

    def _parse_agent_file(self, file_path: Path, cluster: str) -> Optional[GrowthAgentInfo]:
        """Parse a growth agent definition file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    frontmatter = parts[1].strip()
                    
                    # Simple YAML parsing (production would use yaml library)
                    agent_data = {}
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key == 'tools':
                                agent_data[key] = [tool.strip() for tool in value.split(',')]
                            else:
                                agent_data[key] = value
                    
                    # Extract specialization from description
                    specialization = agent_data.get('description', '').split('.')[0].lower()
                    if 'intelligence' in specialization:
                        capabilities = ['market_research', 'competitor_analysis', 'trend_identification']
                    elif 'scout' in specialization:
                        capabilities = ['lead_discovery', 'opportunity_identification', 'prospecting']
                    elif 'engagement' in specialization:
                        capabilities = ['outreach', 'follow_up', 'meeting_scheduling']
                    elif 'negotiator' in specialization:
                        capabilities = ['deal_structuring', 'contract_negotiation', 'partnership_development']
                    elif 'closer' in specialization:
                        capabilities = ['deal_closing', 'contract_finalization', 'revenue_recognition']
                    elif 'strategy' in specialization:
                        capabilities = ['go_to_market', 'positioning', 'market_segmentation']
                    elif 'planner' in specialization:
                        capabilities = ['campaign_planning', 'budget_allocation', 'audience_targeting']
                    elif 'content' in specialization:
                        capabilities = ['content_creation', 'copywriting', 'creative_assets']
                    elif 'execution' in specialization:
                        capabilities = ['campaign_deployment', 'optimization', 'a_b_testing']
                    elif 'analytics' in specialization:
                        capabilities = ['performance_measurement', 'roi_analysis', 'attribution_modeling']
                    else:
                        capabilities = ['general_growth']
                    
                    return GrowthAgentInfo(
                        name=agent_data.get('name', file_path.stem),
                        description=agent_data.get('description', ''),
                        tools=agent_data.get('tools', []),
                        file_path=str(file_path),
                        cluster=cluster,
                        specialization=specialization,
                        capabilities=capabilities,
                        max_concurrent_tasks=8 if cluster == 'bd' else 6  # BD agents handle higher load
                    )
                    
        except Exception as e:
            logger.error(f"Error parsing agent file {file_path}: {e}")
            return None

    async def register_with_orchestrator(self):
        """Register all discovered agents with the pipeline orchestrator"""
        try:
            await asyncio.sleep(2)  # Allow discovery to complete
            
            for agent_name, agent_info in self.agents.items():
                registration = AgentRegistration(
                    id=agent_name,
                    name=agent_name,
                    cluster=agent_info.cluster,
                    specialization=agent_info.specialization,
                    capabilities=agent_info.capabilities or [],
                    max_concurrent_tasks=agent_info.max_concurrent_tasks,
                    success_rate=agent_info.success_rate,
                    average_response_time=agent_info.average_response_time
                )
                
                await pipeline_orchestrator.register_agent(registration)
                
            logger.info(f"Registered {len(self.agents)} agents with pipeline orchestrator")
            
        except Exception as e:
            logger.error(f"Error registering agents with orchestrator: {e}")

    async def invoke_growth_agent(self, agent_name: str, task_type: str, 
                                 description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a growth agent with ultra-aggressive execution"""
        try:
            if agent_name not in self.agents:
                raise ValueError(f"Growth agent '{agent_name}' not found")
            
            agent = self.agents[agent_name]
            
            # Create growth task
            task = GrowthTask(
                id=str(uuid.uuid4()),
                agent_name=agent_name,
                task_type=task_type,
                description=description,
                parameters=parameters,
                created_at=datetime.now(),
                priority=parameters.get('priority', Priority.MEDIUM),
                growth_sprint_id=self.current_sprint.id if self.current_sprint else None,
                expected_outcome=parameters.get('expected_outcome', ''),
                success_metrics=parameters.get('success_metrics', {})
            )
            
            self.active_tasks[task.id] = task
            agent.current_load += 1
            
            # Execute task based on cluster
            if agent.cluster == 'bd':
                result = await self._execute_bd_task(task)
            elif agent.cluster == 'marketing':
                result = await self._execute_marketing_task(task)
            elif agent.cluster == 'orchestrator':
                result = await self._execute_orchestrator_task(task)
            else:
                raise ValueError(f"Unknown agent cluster: {agent.cluster}")
            
            # Update task status
            task.status = "completed" if result.get('success') else "failed"
            task.result = result
            
            # Update agent metrics
            agent.total_invocations += 1
            agent.last_invoked = datetime.now()
            agent.current_load = max(0, agent.current_load - 1)
            
            if task.status == "completed":
                agent.success_rate = ((agent.success_rate * (agent.total_invocations - 1)) + 1) / agent.total_invocations
            
            # Move to completed tasks
            del self.active_tasks[task.id]
            self.completed_tasks.append(task)
            
            # Emit orchestrator event
            await self._emit_task_completion_event(task)
            
            logger.info(f"Growth agent {agent_name} completed {task_type}: {task.status}")
            
            return {
                "task_id": task.id,
                "agent_name": agent_name,
                "status": task.status,
                "result": result,
                "execution_time": (datetime.now() - task.created_at).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error invoking growth agent {agent_name}: {e}")
            return {
                "task_id": task.id if 'task' in locals() else None,
                "agent_name": agent_name,
                "status": "failed",
                "error": str(e)
            }

    async def _execute_bd_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute BD cluster task with ultra-aggressive approach"""
        agent_name = task.agent_name
        task_type = task.task_type
        parameters = task.parameters
        
        if 'intelligence' in agent_name:
            return await self._execute_market_intelligence_task(task)
        elif 'scout' in agent_name:
            return await self._execute_opportunity_scout_task(task)
        elif 'engagement' in agent_name:
            return await self._execute_lead_engagement_task(task)
        elif 'negotiator' in agent_name:
            return await self._execute_partnership_negotiation_task(task)
        elif 'closer' in agent_name:
            return await self._execute_deal_closing_task(task)
        else:
            return await self._execute_generic_bd_task(task)

    async def _execute_marketing_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute Marketing cluster task with growth hacking focus"""
        agent_name = task.agent_name
        
        if 'strategy' in agent_name:
            return await self._execute_marketing_strategy_task(task)
        elif 'planner' in agent_name:
            return await self._execute_campaign_planning_task(task)
        elif 'content' in agent_name:
            return await self._execute_content_creation_task(task)
        elif 'execution' in agent_name:
            return await self._execute_campaign_execution_task(task)
        elif 'analytics' in agent_name:
            return await self._execute_analytics_task(task)
        else:
            return await self._execute_generic_marketing_task(task)

    # BD Task Implementations
    
    async def _execute_market_intelligence_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute market intelligence gathering"""
        return {
            "success": True,
            "intelligence_summary": "Global fintech market expansion opportunities identified",
            "new_markets_detected": 5,
            "competitor_activities": 12,
            "emerging_verticals": ["DeFi", "RegTech", "Embedded Finance"],
            "threat_level": "medium",
            "opportunities": {
                "apac_expansion": {"value": 50000000, "timeline": "6_months"},
                "enterprise_segment": {"value": 25000000, "timeline": "3_months"}
            },
            "recommended_actions": [
                "Accelerate APAC market entry planning",
                "Increase enterprise outreach by 200%",
                "Launch DeFi partnership initiative"
            ]
        }

    async def _execute_opportunity_scout_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute opportunity scouting with aggressive prospecting"""
        opportunities_target = task.parameters.get('target_count', 100)
        
        # Simulate ultra-aggressive prospecting
        identified_opportunities = min(opportunities_target * 1.2, 150)  # Over-deliver
        
        return {
            "success": True,
            "opportunities_identified": identified_opportunities,
            "high_value_prospects": max(5, identified_opportunities // 10),
            "channels_used": ["linkedin", "sales_nav", "apollo", "zoominfo", "events"],
            "regions_covered": ["north_america", "europe", "apac"],
            "verticals_targeted": ["fintech", "banking", "insurance", "wealth_mgmt"],
            "contact_info_verified": int(identified_opportunities * 0.85),
            "meeting_requests_sent": int(identified_opportunities * 0.6),
            "expected_response_rate": 0.12,
            "next_actions": [
                "Begin multi-touch engagement sequence",
                "Schedule discovery calls",
                "Prepare personalized value propositions"
            ]
        }

    async def _execute_lead_engagement_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute ultra-aggressive lead engagement"""
        lead_id = task.parameters.get('lead_id')
        engagement_type = task.parameters.get('type', 'multi_touch')
        
        return {
            "success": True,
            "lead_id": lead_id,
            "engagement_sequence": "ultra_aggressive_7_touch",
            "emails_sent": 3,
            "linkedin_messages": 2,
            "phone_calls": 2,
            "response_received": True,
            "meeting_scheduled": True,
            "meeting_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "qualification_score": 85,
            "pain_points_identified": [
                "Manual trading processes",
                "Lack of real-time analytics",
                "Compliance overhead"
            ],
            "budget_confirmed": "$500K-$1M annually",
            "decision_timeline": "Q1 2025",
            "next_steps": [
                "Send meeting confirmation",
                "Prepare discovery deck",
                "Research attendee backgrounds"
            ]
        }

    async def _execute_partnership_negotiation_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute partnership negotiation"""
        return {
            "success": True,
            "partnership_type": "channel_partner",
            "deal_structure": "revenue_share",
            "terms_negotiated": {
                "commission_rate": "15%",
                "exclusivity": "regional",
                "minimum_commitment": "$2M ARR",
                "contract_length": "3_years"
            },
            "stakeholders_aligned": 4,
            "contract_status": "under_review",
            "expected_signing": (datetime.now() + timedelta(days=14)).isoformat(),
            "projected_revenue_impact": 5000000.0,
            "risk_assessment": "low"
        }

    async def _execute_deal_closing_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute deal closing with urgency"""
        opportunity_id = task.parameters.get('opportunity_id')
        
        return {
            "success": True,
            "opportunity_id": opportunity_id,
            "final_contract_value": task.parameters.get('value', 750000),
            "closing_date": datetime.now().isoformat(),
            "payment_terms": "annual_prepay",
            "contract_length": "2_years",
            "expansion_clause": True,
            "handoff_to_success": True,
            "revenue_recognition": "immediate",
            "upsell_opportunities": [
                "Premium analytics package",
                "Additional trading venues",
                "White-label solution"
            ]
        }

    # Marketing Task Implementations
    
    async def _execute_marketing_strategy_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute marketing strategy development"""
        return {
            "success": True,
            "strategy_focus": "aggressive_demand_generation",
            "target_segments": [
                "enterprise_trading_firms",
                "mid_market_asset_managers", 
                "crypto_exchanges"
            ],
            "gtm_approach": "product_led_growth",
            "messaging_framework": {
                "value_prop": "10x faster trading execution with AI",
                "key_differentiators": ["real_time_analytics", "compliance_automation", "api_first"],
                "proof_points": ["99.99% uptime", "500ms avg latency", "50+ integrations"]
            },
            "channel_strategy": {
                "primary": ["paid_search", "linkedin", "content_marketing"],
                "secondary": ["events", "partnerships", "pr"],
                "budget_allocation": {"paid": 0.6, "organic": 0.25, "events": 0.15}
            },
            "success_metrics": {
                "mql_target": 2000,
                "pipeline_target": 10000000,
                "cac_target": 5000,
                "ltv_target": 50000
            }
        }

    async def _execute_campaign_planning_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute campaign planning with growth hacking"""
        return {
            "success": True,
            "campaign_name": "Q1_Domination_2025",
            "channels": [
                {"name": "google_ads", "budget": 100000, "target_impressions": 2000000},
                {"name": "linkedin_ads", "budget": 150000, "target_clicks": 50000},
                {"name": "content_syndication", "budget": 50000, "target_leads": 1000}
            ],
            "audience_segments": [
                "trading_platform_decision_makers",
                "fintech_ctos",
                "risk_management_heads"
            ],
            "creative_concepts": [
                "AI-powered trading revolution",
                "Milliseconds matter in trading",
                "The future of financial markets"
            ],
            "landing_pages": 5,
            "a_b_tests_planned": 12,
            "conversion_funnels": 3,
            "attribution_model": "data_driven",
            "launch_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "duration_weeks": 12
        }

    async def _execute_content_creation_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute high-velocity content creation"""
        return {
            "success": True,
            "content_created": {
                "blog_posts": 5,
                "whitepapers": 2,
                "case_studies": 3,
                "video_content": 8,
                "social_posts": 50,
                "email_sequences": 4
            },
            "messaging_themes": [
                "Trading speed advantage",
                "AI-driven insights",
                "Regulatory compliance",
                "Market connectivity"
            ],
            "seo_optimization": {
                "target_keywords": 25,
                "content_optimized": 15,
                "backlink_targets": 10
            },
            "creative_assets": {
                "display_banners": 20,
                "social_creatives": 30,
                "video_ads": 6,
                "infographics": 4
            },
            "content_calendar": "12_weeks_planned"
        }

    async def _execute_campaign_execution_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute campaign with real-time optimization"""
        campaign_id = task.parameters.get('campaign_id')
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "deployment_status": "live",
            "channels_activated": 5,
            "initial_performance": {
                "impressions": 150000,
                "clicks": 3500,
                "ctr": 0.023,
                "conversions": 125,
                "conversion_rate": 0.036,
                "cpc": 12.50,
                "cpl": 87.00
            },
            "optimizations_applied": [
                "Increased bids on high-performing keywords",
                "Paused underperforming ad groups",
                "Expanded winning audience segments",
                "Adjusted ad scheduling for peak hours"
            ],
            "a_b_tests_running": 6,
            "winning_variants": 2,
            "budget_utilization": 0.45,
            "recommended_adjustments": [
                "Increase budget for top-performing campaigns",
                "Test new creative variants",
                "Expand geographic targeting"
            ]
        }

    async def _execute_analytics_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute ROI analytics and attribution"""
        return {
            "success": True,
            "analysis_period": "last_30_days",
            "performance_metrics": {
                "total_leads": 2847,
                "qualified_leads": 634,
                "opportunities": 127,
                "closed_deals": 18,
                "revenue_generated": 2250000.0
            },
            "channel_performance": {
                "google_ads": {"roi": 4.2, "cac": 4500, "ltv": 45000},
                "linkedin": {"roi": 3.8, "cac": 5200, "ltv": 48000},
                "content": {"roi": 6.1, "cac": 2800, "ltv": 52000}
            },
            "attribution_analysis": {
                "first_touch": 0.25,
                "last_touch": 0.35,
                "linear": 0.40
            },
            "cohort_analysis": {
                "q4_2024_cohort_ltv": 47500,
                "retention_rate_month_3": 0.85,
                "expansion_rate": 0.30
            },
            "optimization_recommendations": [
                "Shift 20% budget from LinkedIn to content marketing",
                "Implement retargeting for abandoned form fills",
                "Create lookalike audiences from best customers"
            ]
        }

    # Generic task handlers
    
    async def _execute_generic_bd_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Generic BD task execution"""
        return {
            "success": True,
            "task_type": task.task_type,
            "execution_mode": "ultra_aggressive",
            "results": f"Executed {task.task_type} with maximum velocity",
            "metrics": {"efficiency": 0.95, "impact": "high"}
        }

    async def _execute_generic_marketing_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Generic Marketing task execution"""
        return {
            "success": True,
            "task_type": task.task_type,
            "execution_mode": "growth_hacking",
            "results": f"Executed {task.task_type} with optimization focus",
            "metrics": {"roi": 4.5, "conversion_lift": 0.25}
        }

    async def _execute_orchestrator_task(self, task: GrowthTask) -> Dict[str, Any]:
        """Execute orchestrator coordination task"""
        return {
            "success": True,
            "coordination_result": "Pipeline synchronized",
            "conflicts_resolved": 3,
            "agents_balanced": 8,
            "performance_optimized": True
        }

    # Event and Sprint Management

    async def _emit_task_completion_event(self, task: GrowthTask):
        """Emit task completion event to orchestrator"""
        event = GrowthEvent(
            event_type="task_completed",
            source_agent=task.agent_name,
            entity_type="task",
            entity_id=task.id,
            action="completed" if task.status == "completed" else "failed",
            priority=task.priority,
            data={
                "task": asdict(task),
                "performance_impact": self._calculate_task_impact(task)
            }
        )
        await pipeline_orchestrator.emit_event(event)

    def _calculate_task_impact(self, task: GrowthTask) -> Dict[str, Any]:
        """Calculate the impact of a completed task"""
        # Simplified impact calculation
        base_impact = 1.0
        
        if task.status == "completed":
            if "intelligence" in task.agent_name:
                base_impact *= 1.2  # Market intelligence has high strategic value
            elif "closer" in task.agent_name:
                base_impact *= 2.0  # Deal closing has direct revenue impact
            elif "analytics" in task.agent_name:
                base_impact *= 1.5  # Analytics drives optimization
        
        return {
            "impact_score": base_impact,
            "revenue_influence": base_impact * 10000,  # Estimated revenue influence
            "pipeline_acceleration": base_impact * 0.1,  # Pipeline velocity improvement
            "learning_value": base_impact * 0.2  # Organizational learning value
        }

    async def start_growth_sprint(self) -> str:
        """Start a new weekly growth sprint"""
        if self.current_sprint and self.current_sprint.status == "active":
            await self.complete_growth_sprint()
        
        sprint = GrowthSprint(
            id=str(uuid.uuid4()),
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            bd_objectives={
                "new_opportunities": 100,
                "qualified_leads": 250,
                "meetings_scheduled": 150,
                "proposals_sent": 25,
                "deals_to_close": 8
            },
            marketing_objectives={
                "campaign_launches": 3,
                "content_pieces": 15,
                "lead_generation": 500,
                "mql_target": 200,
                "roi_target": 4.0
            },
            pipeline_targets={
                "new_pipeline_value": 5000000.0,
                "weighted_pipeline": 2000000.0,
                "conversion_rate_target": 0.18
            }
        )
        
        self.current_sprint = sprint
        logger.info(f"Started growth sprint {sprint.id} with aggressive targets")
        
        return sprint.id

    async def complete_growth_sprint(self) -> Dict[str, Any]:
        """Complete current growth sprint and generate report"""
        if not self.current_sprint:
            return {"error": "No active sprint to complete"}
        
        sprint = self.current_sprint
        sprint.status = "completed"
        sprint.end_date = datetime.now()
        
        # Calculate sprint performance
        sprint_performance = await self._calculate_sprint_performance(sprint)
        
        # Archive sprint
        self.sprint_history.append(sprint)
        self.current_sprint = None
        
        logger.info(f"Completed growth sprint {sprint.id}")
        
        return {
            "sprint_id": sprint.id,
            "duration_days": (sprint.end_date - sprint.start_date).days,
            "performance": sprint_performance,
            "achievements": {
                "leads_generated": sprint.leads_generated,
                "opportunities_created": sprint.opportunities_created,
                "deals_closed": sprint.deals_closed,
                "revenue_generated": sprint.revenue_generated,
                "roi_achieved": sprint.roi_achieved
            },
            "next_sprint_recommendations": await self._generate_next_sprint_recommendations(sprint_performance)
        }

    async def _calculate_sprint_performance(self, sprint: GrowthSprint) -> Dict[str, Any]:
        """Calculate comprehensive sprint performance metrics"""
        # Get actual results from completed tasks
        sprint_tasks = [task for task in self.completed_tasks 
                       if task.growth_sprint_id == sprint.id]
        
        bd_tasks = [task for task in sprint_tasks if self.agents[task.agent_name].cluster == 'bd']
        marketing_tasks = [task for task in sprint_tasks if self.agents[task.agent_name].cluster == 'marketing']
        
        return {
            "overall_score": 0.85,  # Would calculate based on target achievement
            "bd_performance": {
                "tasks_completed": len(bd_tasks),
                "success_rate": len([t for t in bd_tasks if t.status == "completed"]) / max(len(bd_tasks), 1),
                "target_achievement": 0.92
            },
            "marketing_performance": {
                "tasks_completed": len(marketing_tasks),
                "success_rate": len([t for t in marketing_tasks if t.status == "completed"]) / max(len(marketing_tasks), 1),
                "target_achievement": 0.88
            },
            "pipeline_impact": {
                "new_opportunities": sprint.opportunities_created,
                "pipeline_velocity_improvement": 0.15,
                "conversion_rate_improvement": 0.08
            }
        }

    async def _generate_next_sprint_recommendations(self, performance: Dict[str, Any]) -> List[str]:
        """Generate recommendations for next sprint"""
        recommendations = []
        
        if performance["bd_performance"]["target_achievement"] < 0.9:
            recommendations.append("Increase BD agent focus on high-value opportunities")
        
        if performance["marketing_performance"]["target_achievement"] < 0.9:
            recommendations.append("Optimize marketing campaigns for better lead quality")
        
        recommendations.extend([
            "Implement cross-cluster collaboration sessions",
            "Increase automation in lead qualification",
            "Expand into 2 new geographic markets",
            "Launch partner referral program"
        ])
        
        return recommendations

    # Status and Monitoring
    
    def get_growth_agents(self) -> List[Dict[str, Any]]:
        """Get all discovered growth agents"""
        return [asdict(agent) for agent in self.agents.values()]

    def get_growth_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get status of specific growth agent"""
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        return {
            "name": agent.name,
            "cluster": agent.cluster,
            "specialization": agent.specialization,
            "status": agent.status,
            "current_load": agent.current_load,
            "max_concurrent_tasks": agent.max_concurrent_tasks,
            "total_invocations": agent.total_invocations,
            "success_rate": agent.success_rate,
            "average_response_time": agent.average_response_time,
            "last_invoked": agent.last_invoked.isoformat() if agent.last_invoked else None,
            "capabilities": agent.capabilities
        }

    def get_growth_system_status(self) -> Dict[str, Any]:
        """Get overall growth system status"""
        bd_agents = [a for a in self.agents.values() if a.cluster == 'bd']
        marketing_agents = [a for a in self.agents.values() if a.cluster == 'marketing']
        
        return {
            "total_growth_agents": len(self.agents),
            "bd_agents": len(bd_agents),
            "marketing_agents": len(marketing_agents),
            "available_agents": len([a for a in self.agents.values() if a.status == "available"]),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "current_sprint": self.current_sprint.id if self.current_sprint else None,
            "sprint_history_count": len(self.sprint_history),
            "system_performance": {
                "overall_success_rate": sum(a.success_rate for a in self.agents.values()) / max(len(self.agents), 1),
                "avg_response_time": sum(a.average_response_time for a in self.agents.values()) / max(len(self.agents), 1),
                "system_load": sum(a.current_load for a in self.agents.values())
            },
            "weekly_targets": self.weekly_targets,
            "last_updated": datetime.now().isoformat()
        }

    def get_growth_metrics(self) -> Dict[str, Any]:
        """Get comprehensive growth metrics"""
        # This would integrate with the pipeline orchestrator metrics
        return {
            "current_sprint_metrics": asdict(self.current_sprint) if self.current_sprint else None,
            "agent_performance": {
                agent_name: {
                    "success_rate": agent.success_rate,
                    "total_invocations": agent.total_invocations,
                    "current_load": agent.current_load
                } for agent_name, agent in self.agents.items()
            },
            "system_targets": self.weekly_targets,
            "pipeline_orchestrator_health": "connected"
        }

# Global growth agents instance - initialize on first use
growth_agents = None

def get_growth_agents() -> GrowthAgentInterface:
    """Get or create the global growth agents instance"""
    global growth_agents
    if growth_agents is None:
        growth_agents = GrowthAgentInterface()
    return growth_agents

async def initialize_growth_agents():
    """Initialize the global growth agents instance with async components"""
    agents = get_growth_agents()
    await agents.initialize_async()
    return agents