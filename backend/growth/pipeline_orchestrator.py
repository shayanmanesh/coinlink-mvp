"""
Pipeline Orchestrator - Central Intelligence for Growth Engine

Event-driven coordination system that synchronizes Marketing and Business Development clusters,
manages pipeline flow, prevents conflicts, and optimizes for maximum growth velocity.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import uuid
from enum import Enum

from .data_models import (
    Lead, Opportunity, Campaign, Deal, GrowthEvent, GrowthMetrics,
    LeadStage, OpportunityStage, Priority, DealStatus
)

logger = logging.getLogger(__name__)

class PipelineState(Enum):
    """Pipeline entity states for state machine"""
    CREATED = "created"
    QUALIFIED = "qualified"
    ASSIGNED = "assigned"
    ENGAGED = "engaged"
    PROGRESSING = "progressing"
    CLOSING = "closing"
    CLOSED = "closed"
    LOST = "lost"
    PAUSED = "paused"

class EventType(Enum):
    """Growth event types for orchestrator routing"""
    LEAD_CREATED = "lead_created"
    LEAD_QUALIFIED = "lead_qualified"
    LEAD_DISQUALIFIED = "lead_disqualified"
    OPPORTUNITY_CREATED = "opportunity_created"
    OPPORTUNITY_PROGRESSED = "opportunity_progressed"
    DEAL_CLOSED_WON = "deal_closed_won"
    DEAL_CLOSED_LOST = "deal_closed_lost"
    CAMPAIGN_LAUNCHED = "campaign_launched"
    CAMPAIGN_COMPLETED = "campaign_completed"
    AGENT_REQUEST = "agent_request"
    CONFLICT_DETECTED = "conflict_detected"
    OPTIMIZATION_NEEDED = "optimization_needed"

@dataclass
class AgentRegistration:
    """Growth agent registration information"""
    id: str
    name: str
    cluster: str  # 'bd' or 'marketing'
    specialization: str
    capabilities: List[str]
    max_concurrent_tasks: int = 5
    current_load: int = 0
    success_rate: float = 1.0
    average_response_time: float = 60.0
    last_active: datetime = field(default_factory=datetime.now)
    status: str = "available"  # available, busy, offline

@dataclass
class PipelineConflict:
    """Detected conflicts in pipeline management"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # duplicate_outreach, resource_conflict, timing_conflict
    severity: Priority = Priority.MEDIUM
    entities: List[str] = field(default_factory=list)  # IDs of conflicting entities
    agents: List[str] = field(default_factory=list)   # Conflicting agents
    description: str = ""
    auto_resolution: Optional[str] = None
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class PipelineRule:
    """Rules for pipeline automation and routing"""
    id: str
    name: str
    condition: str  # JSON-serialized condition logic
    action: str    # JSON-serialized action to take
    priority: int
    enabled: bool = True
    success_count: int = 0
    failure_count: int = 0

class PipelineOrchestrator:
    """Central pipeline orchestrator coordinating BD and Marketing clusters"""
    
    def __init__(self):
        self.agent_registry: Dict[str, AgentRegistration] = {}
        self.event_queue: deque = deque()
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        
        # Pipeline state tracking
        self.leads: Dict[str, Lead] = {}
        self.opportunities: Dict[str, Opportunity] = {}
        self.campaigns: Dict[str, Campaign] = {}
        self.deals: Dict[str, Deal] = {}
        
        # State machines
        self.pipeline_states: Dict[str, PipelineState] = {}
        self.state_transitions: Dict[str, datetime] = {}
        
        # Conflict detection and resolution
        self.active_conflicts: Dict[str, PipelineConflict] = {}
        self.conflict_rules: List[PipelineRule] = []
        
        # Performance tracking
        self.metrics: GrowthMetrics = GrowthMetrics()
        self.performance_history: List[GrowthMetrics] = []
        
        # Orchestration parameters
        self.max_concurrent_events = 50
        self.event_processing_interval = 5  # seconds
        self.health_check_interval = 300   # 5 minutes
        self.optimization_threshold = 0.8  # Trigger optimization when metrics drop below
        
        # Agent load balancing
        self.assignment_strategies = {
            'round_robin': self._round_robin_assignment,
            'lowest_load': self._lowest_load_assignment,
            'best_success_rate': self._best_performance_assignment,
            'specialized': self._specialized_assignment
        }
        self.default_strategy = 'specialized'
        
        # Initialize event handlers
        self._setup_event_handlers()
        
        logger.info("Pipeline Orchestrator initialized with event-driven coordination")

    def _setup_event_handlers(self):
        """Setup event handlers for different event types"""
        self.event_handlers[EventType.LEAD_CREATED].append(self._handle_new_lead)
        self.event_handlers[EventType.LEAD_QUALIFIED].append(self._handle_qualified_lead)
        self.event_handlers[EventType.OPPORTUNITY_CREATED].append(self._handle_new_opportunity)
        self.event_handlers[EventType.DEAL_CLOSED_WON].append(self._handle_closed_deal)
        self.event_handlers[EventType.CAMPAIGN_LAUNCHED].append(self._handle_campaign_launch)
        self.event_handlers[EventType.CONFLICT_DETECTED].append(self._handle_conflict)
        
    async def register_agent(self, agent_info: AgentRegistration) -> bool:
        """Register a growth agent with the orchestrator"""
        try:
            self.agent_registry[agent_info.id] = agent_info
            logger.info(f"Registered {agent_info.cluster} agent: {agent_info.name} ({agent_info.specialization})")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent {agent_info.name}: {e}")
            return False

    async def emit_event(self, event: GrowthEvent) -> bool:
        """Emit an event into the orchestrator pipeline"""
        try:
            self.event_queue.append(event)
            logger.debug(f"Emitted {event.event_type} event from {event.source_agent}")
            
            # Process high-priority events immediately
            if event.priority == Priority.CRITICAL:
                await self._process_event(event)
            
            return True
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
            return False

    async def process_events(self):
        """Main event processing loop"""
        while True:
            try:
                processed_count = 0
                
                # Process events up to max concurrent limit
                while self.event_queue and processed_count < self.max_concurrent_events:
                    event = self.event_queue.popleft()
                    await self._process_event(event)
                    processed_count += 1
                
                # Wait before next processing cycle
                await asyncio.sleep(self.event_processing_interval)
                
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(self.event_processing_interval)

    async def _process_event(self, event: GrowthEvent):
        """Process a single event through registered handlers"""
        try:
            event_type = EventType(event.event_type)
            handlers = self.event_handlers.get(event_type, [])
            
            for handler in handlers:
                await handler(event)
                
            event.processed = True
            event.processed_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Error processing event {event.id}: {e}")

    # Event Handlers
    
    async def _handle_new_lead(self, event: GrowthEvent):
        """Handle new lead creation events"""
        lead_data = event.data.get('lead')
        if lead_data:
            lead = Lead(**lead_data)
            self.leads[lead.id] = lead
            self.pipeline_states[lead.id] = PipelineState.CREATED
            
            # Auto-qualify if meets criteria
            if await self._should_auto_qualify_lead(lead):
                await self._qualify_lead(lead.id)
            
            logger.info(f"New lead added to pipeline: {lead.contact.company} ({lead.vertical})")

    async def _handle_qualified_lead(self, event: GrowthEvent):
        """Handle lead qualification events"""
        lead_id = event.entity_id
        if lead_id in self.leads:
            lead = self.leads[lead_id]
            lead.stage = LeadStage.QUALIFIED
            self.pipeline_states[lead_id] = PipelineState.QUALIFIED
            
            # Assign to best BD agent
            bd_agent = await self._assign_to_bd_agent(lead)
            if bd_agent:
                lead.assigned_to = bd_agent.id
                self.pipeline_states[lead_id] = PipelineState.ASSIGNED
                
                # Emit assignment event
                assignment_event = GrowthEvent(
                    event_type=EventType.AGENT_REQUEST.value,
                    source_agent="pipeline-orchestrator",
                    target_agent=bd_agent.id,
                    entity_type="lead",
                    entity_id=lead_id,
                    action="engage",
                    data={"lead": lead.__dict__, "priority": "high"}
                )
                await self.emit_event(assignment_event)
                
            logger.info(f"Qualified lead assigned to BD agent: {lead.contact.company}")

    async def _handle_new_opportunity(self, event: GrowthEvent):
        """Handle new opportunity creation"""
        opportunity_data = event.data.get('opportunity')
        if opportunity_data:
            opportunity = Opportunity(**opportunity_data)
            self.opportunities[opportunity.id] = opportunity
            self.pipeline_states[opportunity.id] = PipelineState.CREATED
            
            # Check for conflicts with existing opportunities
            conflicts = await self._detect_opportunity_conflicts(opportunity)
            if conflicts:
                for conflict in conflicts:
                    self.active_conflicts[conflict.id] = conflict
                    await self._emit_conflict_event(conflict)
                    
            logger.info(f"New opportunity created: {opportunity.name} (${opportunity.value:,.2f})")

    async def _handle_closed_deal(self, event: GrowthEvent):
        """Handle closed deal events"""
        deal_data = event.data.get('deal')
        if deal_data:
            deal = Deal(**deal_data)
            self.deals[deal.id] = deal
            
            # Update metrics
            await self._update_deal_metrics(deal)
            
            # Check for expansion opportunities
            if deal.status == DealStatus.CLOSED_WON:
                expansion_tasks = await self._identify_expansion_opportunities(deal)
                for task in expansion_tasks:
                    await self.emit_event(task)
                    
            logger.info(f"Deal closed: {deal.account_name} - ${deal.total_contract_value:,.2f}")

    async def _handle_campaign_launch(self, event: GrowthEvent):
        """Handle campaign launch events"""
        campaign_data = event.data.get('campaign')
        if campaign_data:
            campaign = Campaign(**campaign_data)
            self.campaigns[campaign.id] = campaign
            
            # Coordinate with BD agents about campaign target accounts
            await self._coordinate_campaign_with_bd(campaign)
            
            logger.info(f"Campaign launched: {campaign.name} ({campaign.channel.value})")

    async def _handle_conflict(self, event: GrowthEvent):
        """Handle pipeline conflicts"""
        conflict_data = event.data.get('conflict')
        if conflict_data:
            conflict = PipelineConflict(**conflict_data)
            
            # Attempt auto-resolution
            resolution = await self._attempt_conflict_resolution(conflict)
            if resolution:
                conflict.auto_resolution = resolution
                conflict.resolved = True
                logger.info(f"Auto-resolved conflict: {conflict.type}")
            else:
                # Escalate to human intervention
                await self._escalate_conflict(conflict)
                logger.warning(f"Conflict requires manual intervention: {conflict.type}")

    # Lead Management
    
    async def _should_auto_qualify_lead(self, lead: Lead) -> bool:
        """Determine if a lead should be auto-qualified"""
        score_threshold = 75
        
        # Auto-qualify based on score and attributes
        if lead.score >= score_threshold:
            return True
            
        # Auto-qualify enterprise leads with known pain points
        if (lead.company_size == "enterprise" and 
            len(lead.pain_points) >= 2 and
            lead.budget_range in ["$50k-$100k", "$100k+"]):
            return True
            
        return False

    async def _qualify_lead(self, lead_id: str):
        """Qualify a lead and emit qualification event"""
        qualification_event = GrowthEvent(
            event_type=EventType.LEAD_QUALIFIED.value,
            source_agent="pipeline-orchestrator",
            entity_type="lead",
            entity_id=lead_id,
            action="qualified",
            priority=Priority.HIGH
        )
        await self.emit_event(qualification_event)

    # Agent Assignment
    
    async def _assign_to_bd_agent(self, lead: Lead) -> Optional[AgentRegistration]:
        """Assign lead to best available BD agent"""
        bd_agents = [agent for agent in self.agent_registry.values() 
                    if agent.cluster == 'bd' and agent.status == 'available']
        
        if not bd_agents:
            logger.warning("No BD agents available for lead assignment")
            return None
            
        # Use specialized assignment strategy
        return await self.assignment_strategies[self.default_strategy](bd_agents, lead)

    async def _round_robin_assignment(self, agents: List[AgentRegistration], entity: Any) -> AgentRegistration:
        """Round-robin assignment strategy"""
        # Simple implementation - in production would track last assigned
        return min(agents, key=lambda a: a.current_load)

    async def _lowest_load_assignment(self, agents: List[AgentRegistration], entity: Any) -> AgentRegistration:
        """Assign to agent with lowest current load"""
        return min(agents, key=lambda a: a.current_load)

    async def _best_performance_assignment(self, agents: List[AgentRegistration], entity: Any) -> AgentRegistration:
        """Assign to agent with best success rate"""
        return max(agents, key=lambda a: a.success_rate)

    async def _specialized_assignment(self, agents: List[AgentRegistration], entity: Any) -> AgentRegistration:
        """Assign based on agent specialization and entity attributes"""
        # Match agent specialization with lead/opportunity characteristics
        if isinstance(entity, Lead):
            if entity.vertical == "fintech":
                fintech_agents = [a for a in agents if "fintech" in a.specialization.lower()]
                if fintech_agents:
                    return max(fintech_agents, key=lambda a: a.success_rate)
            
            if entity.company_size == "enterprise":
                enterprise_agents = [a for a in agents if "enterprise" in a.specialization.lower()]
                if enterprise_agents:
                    return max(enterprise_agents, key=lambda a: a.success_rate)
        
        # Fallback to best performance
        return await self._best_performance_assignment(agents, entity)

    # Conflict Detection and Resolution
    
    async def _detect_opportunity_conflicts(self, opportunity: Opportunity) -> List[PipelineConflict]:
        """Detect conflicts with existing opportunities"""
        conflicts = []
        
        # Check for duplicate opportunities from same company
        for existing_opp in self.opportunities.values():
            if (existing_opp.id != opportunity.id and
                existing_opp.lead_id == opportunity.lead_id and
                existing_opp.stage not in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]):
                
                conflict = PipelineConflict(
                    type="duplicate_opportunity",
                    severity=Priority.HIGH,
                    entities=[opportunity.id, existing_opp.id],
                    description=f"Duplicate opportunity detected for lead {opportunity.lead_id}"
                )
                conflicts.append(conflict)
        
        return conflicts

    async def _attempt_conflict_resolution(self, conflict: PipelineConflict) -> Optional[str]:
        """Attempt automatic conflict resolution"""
        if conflict.type == "duplicate_opportunity":
            # Merge opportunities or keep the higher value one
            opportunities = [self.opportunities.get(eid) for eid in conflict.entities 
                           if eid in self.opportunities]
            
            if len(opportunities) == 2:
                higher_value = max(opportunities, key=lambda o: o.value)
                lower_value = min(opportunities, key=lambda o: o.value)
                
                # Merge lower value opportunity into higher value one
                higher_value.value += lower_value.value
                higher_value.updated_at = datetime.now()
                
                # Remove lower value opportunity
                del self.opportunities[lower_value.id]
                
                return f"Merged opportunities: kept {higher_value.id}, removed {lower_value.id}"
        
        return None

    async def _emit_conflict_event(self, conflict: PipelineConflict):
        """Emit conflict detection event"""
        conflict_event = GrowthEvent(
            event_type=EventType.CONFLICT_DETECTED.value,
            source_agent="pipeline-orchestrator",
            priority=conflict.severity,
            entity_type="conflict",
            entity_id=conflict.id,
            action="detected",
            data={"conflict": conflict.__dict__}
        )
        await self.emit_event(conflict_event)

    async def _escalate_conflict(self, conflict: PipelineConflict):
        """Escalate conflict for human intervention"""
        # In production, this would notify admins/managers
        logger.critical(f"Pipeline conflict requires manual resolution: {conflict.description}")

    # Metrics and Performance
    
    async def _update_deal_metrics(self, deal: Deal):
        """Update metrics based on closed deal"""
        if deal.status == DealStatus.CLOSED_WON:
            self.metrics.total_deals_closed += 1
            self.metrics.total_revenue += deal.total_contract_value
            
            # Update average deal size
            if self.metrics.total_deals_closed > 0:
                self.metrics.average_deal_size = self.metrics.total_revenue / self.metrics.total_deals_closed
                
            # Update largest deal
            if deal.total_contract_value > self.metrics.largest_deal:
                self.metrics.largest_deal = deal.total_contract_value

    async def _calculate_pipeline_metrics(self) -> GrowthMetrics:
        """Calculate comprehensive pipeline metrics"""
        metrics = GrowthMetrics()
        current_time = datetime.now()
        
        # Pipeline volume and value
        active_opportunities = [opp for opp in self.opportunities.values() 
                              if opp.stage not in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]]
        
        metrics.pipeline_volume = len(active_opportunities)
        metrics.pipeline_value = sum(opp.value for opp in active_opportunities)
        metrics.weighted_pipeline = sum(opp.value * opp.probability for opp in active_opportunities)
        
        # Conversion rates
        total_leads = len(self.leads)
        if total_leads > 0:
            opportunities_count = len(self.opportunities)
            deals_count = len([d for d in self.deals.values() if d.status == DealStatus.CLOSED_WON])
            
            metrics.lead_to_opportunity_rate = opportunities_count / total_leads
            if opportunities_count > 0:
                metrics.opportunity_to_deal_rate = deals_count / opportunities_count
            metrics.overall_conversion_rate = deals_count / total_leads if total_leads > 0 else 0
        
        # Calculate pipeline velocity
        closed_deals = [d for d in self.deals.values() if d.status == DealStatus.CLOSED_WON]
        if closed_deals:
            avg_cycle_time = sum((d.signed_date - self.opportunities[d.opportunity_id].created_at).days 
                               for d in closed_deals if d.signed_date and d.opportunity_id in self.opportunities)
            metrics.pipeline_velocity = avg_cycle_time / len(closed_deals) if closed_deals else 0
        
        # Calculate performance vs targets
        metrics.calculate_performance_ratios()
        
        return metrics

    # Campaign Coordination
    
    async def _coordinate_campaign_with_bd(self, campaign: Campaign):
        """Coordinate campaign launch with BD agents"""
        # Identify target accounts that overlap with BD prospecting
        # Prevent BD outreach to accounts being targeted by paid campaigns
        
        bd_agents = [agent for agent in self.agent_registry.values() 
                    if agent.cluster == 'bd']
        
        coordination_event = GrowthEvent(
            event_type=EventType.CAMPAIGN_LAUNCHED.value,
            source_agent="pipeline-orchestrator",
            entity_type="campaign",
            entity_id=campaign.id,
            action="coordinate",
            data={
                "campaign": campaign.__dict__,
                "target_regions": campaign.target_regions,
                "target_verticals": campaign.target_verticals,
                "instruction": "avoid_outreach_to_campaign_targets"
            }
        )
        
        for agent in bd_agents:
            coordination_event.target_agent = agent.id
            await self.emit_event(coordination_event)

    # Expansion Opportunities
    
    async def _identify_expansion_opportunities(self, deal: Deal) -> List[GrowthEvent]:
        """Identify expansion opportunities from closed deals"""
        expansion_events = []
        
        if deal.status == DealStatus.CLOSED_WON:
            # Create upsell opportunity
            upsell_event = GrowthEvent(
                event_type=EventType.OPPORTUNITY_CREATED.value,
                source_agent="pipeline-orchestrator",
                entity_type="opportunity",
                entity_id=str(uuid.uuid4()),
                action="create_upsell",
                priority=Priority.MEDIUM,
                data={
                    "type": "upsell",
                    "parent_deal_id": deal.id,
                    "account_name": deal.account_name,
                    "estimated_value": deal.total_contract_value * 0.3,  # 30% upsell
                    "timeline": "6_months"
                }
            )
            expansion_events.append(upsell_event)
            
            # Create referral opportunity
            referral_event = GrowthEvent(
                event_type=EventType.AGENT_REQUEST.value,
                source_agent="pipeline-orchestrator",
                entity_type="lead",
                entity_id=str(uuid.uuid4()),
                action="request_referral",
                priority=Priority.LOW,
                data={
                    "type": "referral_request",
                    "source_account": deal.account_name,
                    "contact_id": deal.id,
                    "timeline": "3_months"
                }
            )
            expansion_events.append(referral_event)
        
        return expansion_events

    # Health and Monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of orchestrator"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agents": {
                "total": len(self.agent_registry),
                "available": len([a for a in self.agent_registry.values() if a.status == "available"]),
                "busy": len([a for a in self.agent_registry.values() if a.status == "busy"]),
                "offline": len([a for a in self.agent_registry.values() if a.status == "offline"])
            },
            "pipeline": {
                "leads": len(self.leads),
                "opportunities": len(self.opportunities),
                "campaigns": len(self.campaigns),
                "deals": len(self.deals),
                "active_conflicts": len(self.active_conflicts)
            },
            "events": {
                "queue_size": len(self.event_queue),
                "processing_rate": self.max_concurrent_events / self.event_processing_interval
            },
            "performance": {
                "total_revenue": self.metrics.total_revenue,
                "conversion_rate": self.metrics.overall_conversion_rate,
                "pipeline_value": self.metrics.pipeline_value
            }
        }
        
        # Determine overall health status
        if (self.metrics.overall_conversion_rate < self.optimization_threshold or
            len(self.active_conflicts) > 10 or
            len(self.event_queue) > self.max_concurrent_events * 2):
            health["status"] = "degraded"
            
        return health

    async def generate_growth_report(self) -> Dict[str, Any]:
        """Generate comprehensive growth performance report"""
        current_metrics = await self._calculate_pipeline_metrics()
        
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": current_metrics.period_start.isoformat(),
                "end": current_metrics.period_end.isoformat()
            },
            "pipeline_overview": {
                "volume": current_metrics.pipeline_volume,
                "value": current_metrics.pipeline_value,
                "weighted_value": current_metrics.weighted_pipeline,
                "velocity": current_metrics.pipeline_velocity
            },
            "conversions": {
                "lead_to_opportunity": current_metrics.lead_to_opportunity_rate,
                "opportunity_to_deal": current_metrics.opportunity_to_deal_rate,
                "overall": current_metrics.overall_conversion_rate
            },
            "performance_vs_targets": {
                "opportunities": current_metrics.opportunities_vs_target,
                "revenue": current_metrics.revenue_vs_target,
                "conversion": current_metrics.conversion_vs_target
            },
            "agent_performance": {
                agent.name: {
                    "success_rate": agent.success_rate,
                    "current_load": agent.current_load,
                    "response_time": agent.average_response_time
                } for agent in self.agent_registry.values()
            },
            "conflicts": {
                "total": len(self.active_conflicts),
                "by_type": self._group_conflicts_by_type(),
                "resolution_rate": self._calculate_conflict_resolution_rate()
            },
            "recommendations": await self._generate_optimization_recommendations()
        }
        
        return report

    def _group_conflicts_by_type(self) -> Dict[str, int]:
        """Group active conflicts by type"""
        conflict_types = defaultdict(int)
        for conflict in self.active_conflicts.values():
            conflict_types[conflict.type] += 1
        return dict(conflict_types)

    def _calculate_conflict_resolution_rate(self) -> float:
        """Calculate conflict resolution rate"""
        # Would need to track historical conflicts for accurate rate
        return 0.85  # Placeholder

    async def _generate_optimization_recommendations(self) -> List[str]:
        """Generate AI-powered optimization recommendations"""
        recommendations = []
        
        # Analyze conversion bottlenecks
        if self.metrics.lead_to_opportunity_rate < 0.20:
            recommendations.append("Improve lead qualification criteria - current conversion rate is below 20%")
        
        if self.metrics.opportunity_to_deal_rate < 0.25:
            recommendations.append("Focus on deal closing training and process optimization")
            
        # Analyze pipeline velocity
        if self.metrics.pipeline_velocity > 90:  # More than 90 days
            recommendations.append("Accelerate sales cycle - current velocity exceeds 90 days")
            
        # Agent load balancing
        agent_loads = [agent.current_load for agent in self.agent_registry.values()]
        if agent_loads and max(agent_loads) - min(agent_loads) > 3:
            recommendations.append("Rebalance agent workloads - significant load disparity detected")
            
        # Campaign performance
        active_campaigns = [c for c in self.campaigns.values() if c.status == "active"]
        low_roi_campaigns = [c for c in active_campaigns if c.roi < 2.0]
        if low_roi_campaigns:
            recommendations.append(f"Optimize or pause {len(low_roi_campaigns)} underperforming campaigns")
            
        return recommendations

    async def trigger_optimization_cycle(self):
        """Trigger orchestrator optimization cycle"""
        logger.info("Starting orchestrator optimization cycle")
        
        # Recalculate metrics
        self.metrics = await self._calculate_pipeline_metrics()
        
        # Check for optimization triggers
        if self.metrics.overall_conversion_rate < self.optimization_threshold:
            optimization_event = GrowthEvent(
                event_type=EventType.OPTIMIZATION_NEEDED.value,
                source_agent="pipeline-orchestrator",
                priority=Priority.HIGH,
                entity_type="system",
                entity_id="orchestrator",
                action="optimize",
                data={
                    "trigger": "low_conversion_rate",
                    "current_rate": self.metrics.overall_conversion_rate,
                    "threshold": self.optimization_threshold,
                    "recommendations": await self._generate_optimization_recommendations()
                }
            )
            await self.emit_event(optimization_event)
        
        logger.info("Optimization cycle completed")

# Global orchestrator instance
pipeline_orchestrator = PipelineOrchestrator()