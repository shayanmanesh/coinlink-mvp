"""
Deal Closer Agent - Revenue Closing & Deal Finalization Engine

Ultra-aggressive deal closing agent that manages final sales stages, removes obstacles, 
negotiates terms, and drives revenue recognition with relentless closing techniques.
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
    Lead, Opportunity, Campaign, Deal, GrowthEvent, Priority,
    OpportunityStage, DealStatus, Contact, EngagementEvent
)

logger = logging.getLogger(__name__)

class ClosingStage(Enum):
    """Deal closing stages"""
    OPPORTUNITY_QUALIFIED = "opportunity_qualified"
    DEMO_COMPLETED = "demo_completed" 
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION_ACTIVE = "negotiation_active"
    CONTRACTS_SENT = "contracts_sent"
    SIGNATURES_PENDING = "signatures_pending"
    DEAL_CLOSED_WON = "deal_closed_won"
    DEAL_CLOSED_LOST = "deal_closed_lost"

class ClosingTechnique(Enum):
    """Sales closing techniques"""
    ASSUMPTIVE_CLOSE = "assumptive_close"
    URGENCY_CLOSE = "urgency_close"
    SCARCITY_CLOSE = "scarcity_close"
    SUMMARY_CLOSE = "summary_close"
    ALTERNATIVE_CLOSE = "alternative_close"
    QUESTION_CLOSE = "question_close"
    TAKEAWAY_CLOSE = "takeaway_close"
    TRIAL_CLOSE = "trial_close"
    EMOTION_CLOSE = "emotion_close"
    FINANCIAL_CLOSE = "financial_close"

class ObjectionType(Enum):
    """Common sales objections"""
    PRICE_OBJECTION = "price_objection"
    BUDGET_OBJECTION = "budget_objection"
    AUTHORITY_OBJECTION = "authority_objection"
    NEED_OBJECTION = "need_objection"
    TIMING_OBJECTION = "timing_objection"
    TRUST_OBJECTION = "trust_objection"
    COMPETITOR_OBJECTION = "competitor_objection"
    FEATURE_OBJECTION = "feature_objection"

@dataclass
class DealOpportunity:
    """Deal opportunity with closing intelligence"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic opportunity information
    opportunity_name: str = ""
    account_name: str = ""
    contact_name: str = ""
    deal_value: float = 0.0
    probability: float = 0.0
    
    # Closing details
    closing_stage: ClosingStage = ClosingStage.OPPORTUNITY_QUALIFIED
    target_close_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    days_in_pipeline: int = 0
    
    # Decision-making intelligence
    decision_makers: List[Dict[str, str]] = field(default_factory=list)
    influencers: List[Dict[str, str]] = field(default_factory=list)
    budget_holder: str = ""
    technical_evaluator: str = ""
    economic_buyer: str = ""
    
    # Competitive landscape
    competitors_identified: List[str] = field(default_factory=list)
    competitive_advantages: List[str] = field(default_factory=list)
    differentiation_strategy: str = ""
    
    # Objections and obstacles
    identified_objections: List[Dict[str, str]] = field(default_factory=list)
    resolved_objections: List[str] = field(default_factory=list)
    remaining_obstacles: List[str] = field(default_factory=list)
    
    # Proposal and pricing
    proposal_sent_date: Optional[datetime] = None
    proposal_value: float = 0.0
    discount_applied: float = 0.0
    payment_terms: str = ""
    contract_length: str = ""
    
    # Closing strategy
    preferred_closing_technique: ClosingTechnique = ClosingTechnique.ASSUMPTIVE_CLOSE
    closing_calls_scheduled: int = 0
    urgency_factors: List[str] = field(default_factory=list)
    scarcity_elements: List[str] = field(default_factory=list)
    
    # Risk assessment
    closing_risk_level: str = "medium"  # low, medium, high
    risk_factors: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)

@dataclass
class ClosingSession:
    """Deal closing session tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str = ""
    session_date: datetime = field(default_factory=datetime.now)
    session_type: str = ""  # discovery, demo, proposal, closing, contract
    
    # Participants
    attendees: List[Dict[str, str]] = field(default_factory=list)
    decision_makers_present: bool = False
    
    # Session content
    agenda_covered: List[str] = field(default_factory=list)
    objections_raised: List[Dict[str, str]] = field(default_factory=list)
    objections_handled: List[str] = field(default_factory=list)
    
    # Closing attempts
    closing_techniques_used: List[ClosingTechnique] = field(default_factory=list)
    close_attempted: bool = False
    close_successful: bool = False
    close_resistance_points: List[str] = field(default_factory=list)
    
    # Outcomes
    next_steps_agreed: List[str] = field(default_factory=list)
    commitment_level: str = ""  # high, medium, low
    follow_up_timeline: str = ""
    contract_requested: bool = False
    
    # Intelligence gathered
    new_stakeholders_identified: List[str] = field(default_factory=list)
    competitive_intel: List[str] = field(default_factory=list)
    urgency_discovered: List[str] = field(default_factory=list)

@dataclass
class ClosingPlaybook:
    """Deal-specific closing playbook and strategy"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deal_id: str = ""
    
    # Closing strategy
    primary_strategy: str = ""
    backup_strategies: List[str] = field(default_factory=list)
    closing_timeline: str = ""
    
    # Stakeholder map
    stakeholder_influence_map: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    consensus_building_plan: List[str] = field(default_factory=list)
    champion_development: List[str] = field(default_factory=list)
    
    # Value proposition
    customized_value_props: List[str] = field(default_factory=list)
    roi_calculation: Dict[str, float] = field(default_factory=dict)
    risk_mitigation_messages: List[str] = field(default_factory=list)
    
    # Closing tactics
    urgency_creation_plan: List[str] = field(default_factory=list)
    scarcity_messaging: List[str] = field(default_factory=list)
    social_proof_elements: List[str] = field(default_factory=list)
    
    # Negotiation preparation
    negotiation_ranges: Dict[str, Dict[str, float]] = field(default_factory=dict)
    concession_strategy: List[str] = field(default_factory=list)
    walk_away_points: List[str] = field(default_factory=list)

class DealCloserAgent:
    """Ultra-aggressive deal closing and revenue recognition agent"""
    
    def __init__(self):
        self.agent_id = "deal-closer-agent"
        self.name = "Deal Closer Agent"
        self.specialization = "revenue_closing_deal_finalization"
        self.capabilities = [
            "deal_closing", "objection_handling", "negotiation", "contract_acceleration",
            "stakeholder_alignment", "urgency_creation", "revenue_recognition"
        ]
        
        # Deal database
        self.deal_opportunities: Dict[str, DealOpportunity] = {}
        self.closing_sessions: Dict[str, ClosingSession] = {}
        self.closing_playbooks: Dict[str, ClosingPlaybook] = {}
        
        # Closing parameters
        self.closing_targets = {
            "monthly_deal_count": 15,
            "monthly_revenue_target": 2500000.0,
            "average_deal_size": 750000.0,
            "close_rate_target": 0.35,
            "average_sales_cycle_days": 60
        }
        
        # Closing technique success rates (historical data)
        self.technique_success_rates = {
            ClosingTechnique.ASSUMPTIVE_CLOSE: 0.42,
            ClosingTechnique.URGENCY_CLOSE: 0.38,
            ClosingTechnique.SCARCITY_CLOSE: 0.35,
            ClosingTechnique.SUMMARY_CLOSE: 0.40,
            ClosingTechnique.ALTERNATIVE_CLOSE: 0.33,
            ClosingTechnique.QUESTION_CLOSE: 0.36,
            ClosingTechnique.TAKEAWAY_CLOSE: 0.31,
            ClosingTechnique.TRIAL_CLOSE: 0.28,
            ClosingTechnique.EMOTION_CLOSE: 0.39,
            ClosingTechnique.FINANCIAL_CLOSE: 0.45
        }
        
        # Objection handling scripts
        self.objection_responses = {
            ObjectionType.PRICE_OBJECTION: [
                "What's the cost of not solving this problem?",
                "Let's look at the ROI calculation together",
                "This investment pays for itself in 6 months"
            ],
            ObjectionType.BUDGET_OBJECTION: [
                "What budget cycle works better for you?",
                "We have flexible payment terms available",
                "What if we could phase the implementation?"
            ],
            ObjectionType.TIMING_OBJECTION: [
                "What would need to change for this to be the right time?",
                "The cost of waiting is higher than acting now",
                "We can start with a pilot program immediately"
            ]
        }
        
        # Performance metrics
        self.deals_closed_count = 0
        self.total_revenue_closed = 0.0
        self.current_close_rate = 0.0
        self.average_deal_cycle_days = 0
        self.objections_handled_count = 0
        
        logger.info(f"Deal Closer Agent initialized - targeting {self.closing_targets['monthly_deal_count']} deals/month")

    async def execute_closing_blitz(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ultra-aggressive deal closing blitz across pipeline"""
        blitz_type = parameters.get('blitz_type', 'comprehensive')
        target_deals = parameters.get('deal_ids', [])
        closing_intensity = parameters.get('intensity', 'ultra_aggressive')
        revenue_focus = parameters.get('revenue_focus', True)
        
        logger.info(f"Starting {blitz_type} closing blitz - targeting {len(target_deals)} deals")
        
        deals_advanced = []
        objections_handled = []
        contracts_sent = []
        deals_closed = []
        revenue_recognized = []
        
        # Execute parallel closing activities
        closing_tasks = [
            self._advance_hot_deals(target_deals, closing_intensity),
            self._handle_pipeline_objections(),
            self._accelerate_contract_process(),
            self._execute_closing_calls(),
            self._recognize_closed_revenue()
        ]
        
        closing_results = await asyncio.gather(*closing_tasks, return_exceptions=True)
        
        # Process and consolidate results
        for i, result in enumerate(closing_results):
            if isinstance(result, Exception):
                logger.error(f"Closing task {i} failed: {result}")
                continue
                
            deals_advanced.extend(result.get('deals_advanced', []))
            objections_handled.extend(result.get('objections_handled', []))
            contracts_sent.extend(result.get('contracts_sent', []))
            deals_closed.extend(result.get('deals_closed', []))
            revenue_recognized.extend(result.get('revenue_recognized', []))
        
        # Calculate immediate follow-up actions for hot deals
        immediate_actions = await self._identify_immediate_closing_actions(deals_advanced)
        
        # Update performance metrics
        self.deals_closed_count += len(deals_closed)
        self.total_revenue_closed += sum(d.get('deal_value', 0) for d in deals_closed)
        self.objections_handled_count += len(objections_handled)
        
        # Calculate current performance rates
        if len(target_deals) > 0:
            self.current_close_rate = len(deals_closed) / len(target_deals)
        
        logger.info(f"Closing blitz completed: {len(deals_advanced)} deals advanced, " +
                   f"{len(deals_closed)} deals closed, ${sum(d.get('deal_value', 0) for d in deals_closed):,.0f} revenue")
        
        return {
            "success": True,
            "blitz_type": blitz_type,
            "execution_time_minutes": 90,  # Simulated
            "closing_summary": {
                "deals_advanced": len(deals_advanced),
                "objections_handled": len(objections_handled),
                "contracts_sent": len(contracts_sent),
                "deals_closed": len(deals_closed),
                "revenue_recognized": sum(r.get('amount', 0) for r in revenue_recognized)
            },
            "closing_stage_progression": {
                "proposal_to_negotiation": len([d for d in deals_advanced if d.get('stage_change') == 'proposal_to_negotiation']),
                "negotiation_to_contract": len([d for d in deals_advanced if d.get('stage_change') == 'negotiation_to_contract']),
                "contract_to_signature": len([d for d in deals_advanced if d.get('stage_change') == 'contract_to_signature']),
                "signature_to_closed": len(deals_closed)
            },
            "objection_resolution": {
                "price_objections": len([o for o in objections_handled if o.get('type') == 'price_objection']),
                "timing_objections": len([o for o in objections_handled if o.get('type') == 'timing_objection']),
                "authority_objections": len([o for o in objections_handled if o.get('type') == 'authority_objection']),
                "budget_objections": len([o for o in objections_handled if o.get('type') == 'budget_objection'])
            },
            "revenue_impact": {
                "total_closed_value": sum(d.get('deal_value', 0) for d in deals_closed),
                "average_deal_size": sum(d.get('deal_value', 0) for d in deals_closed) / max(len(deals_closed), 1),
                "largest_deal_closed": max([d.get('deal_value', 0) for d in deals_closed], default=0),
                "q1_revenue_impact": sum(d.get('deal_value', 0) for d in deals_closed if d.get('close_date', '').startswith('2025-01'))
            },
            "closing_performance": {
                "close_rate_this_blitz": len(deals_closed) / max(len(target_deals), 1),
                "avg_closing_technique_success": sum(self.technique_success_rates.values()) / len(self.technique_success_rates),
                "objection_resolution_rate": len(objections_handled) / max(len([d for d in deals_advanced if d.get('objections_count', 0) > 0]), 1)
            },
            "immediate_actions": immediate_actions,
            "next_48h_pipeline": await self._forecast_next_48h_closing_activity(deals_advanced)
        }

    async def _advance_hot_deals(self, deal_ids: List[str], intensity: str) -> Dict[str, Any]:
        """Advance hot deals through closing stages"""
        deals_advanced = []
        
        # Simulate hot deals in pipeline
        hot_deals = [
            {
                "deal_id": "deal_001",
                "account_name": "Enterprise Trading Corp",
                "deal_value": 1250000.0,
                "current_stage": "negotiation_active",
                "probability": 0.85,
                "days_to_close": 7
            },
            {
                "deal_id": "deal_002",
                "account_name": "Global Fintech Solutions",
                "deal_value": 850000.0,
                "current_stage": "contracts_sent",
                "probability": 0.90,
                "days_to_close": 3
            },
            {
                "deal_id": "deal_003",
                "account_name": "Regional Investment Platform",
                "deal_value": 650000.0,
                "current_stage": "proposal_sent",
                "probability": 0.70,
                "days_to_close": 14
            }
        ]
        
        for deal in hot_deals:
            advancement_result = await self._advance_individual_deal(deal, intensity)
            deals_advanced.append({
                **deal,
                "advancement_result": advancement_result
            })
        
        return {
            "deals_advanced": deals_advanced,
            "objections_handled": [],
            "contracts_sent": [],
            "deals_closed": [],
            "revenue_recognized": []
        }

    async def _advance_individual_deal(self, deal: Dict[str, Any], intensity: str) -> Dict[str, Any]:
        """Advance individual deal based on current stage"""
        current_stage = deal["current_stage"]
        deal_value = deal["deal_value"]
        
        if current_stage == "proposal_sent":
            return await self._follow_up_on_proposal(deal, intensity)
        elif current_stage == "negotiation_active":
            return await self._close_negotiation(deal, intensity)
        elif current_stage == "contracts_sent":
            return await self._accelerate_signature(deal, intensity)
        
        return {"action": "standard_follow_up", "stage_change": None}

    async def _follow_up_on_proposal(self, deal: Dict[str, Any], intensity: str) -> Dict[str, Any]:
        """Follow up aggressively on sent proposal"""
        follow_up_actions = [
            "Scheduled proposal review call",
            "Sent ROI calculator with proposal",
            "Identified decision timeline",
            "Addressed initial questions"
        ]
        
        return {
            "action": "proposal_follow_up",
            "stage_change": "proposal_to_negotiation",
            "actions_taken": follow_up_actions,
            "next_meeting_scheduled": (datetime.now() + timedelta(days=2)).isoformat(),
            "closing_technique_used": ClosingTechnique.QUESTION_CLOSE.value
        }

    async def _close_negotiation(self, deal: Dict[str, Any], intensity: str) -> Dict[str, Any]:
        """Close active negotiation with urgency"""
        negotiation_tactics = [
            "Created end-of-quarter urgency",
            "Offered limited-time discount",
            "Scheduled decision-maker call",
            "Prepared contract with negotiated terms"
        ]
        
        return {
            "action": "negotiation_closing",
            "stage_change": "negotiation_to_contract",
            "tactics_used": negotiation_tactics,
            "urgency_factors": ["Q1 budget deadline", "Implementation timeline"],
            "concessions_offered": ["5% discount", "Extended payment terms"],
            "closing_technique_used": ClosingTechnique.URGENCY_CLOSE.value
        }

    async def _accelerate_signature(self, deal: Dict[str, Any], intensity: str) -> Dict[str, Any]:
        """Accelerate contract signature process"""
        acceleration_actions = [
            "Daily signature status check",
            "Expedited legal review",
            "Direct CEO outreach",
            "Implementation team introduction"
        ]
        
        return {
            "action": "signature_acceleration",
            "stage_change": "contract_to_signature",
            "acceleration_tactics": acceleration_actions,
            "estimated_signature_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "closing_technique_used": ClosingTechnique.ASSUMPTIVE_CLOSE.value
        }

    async def _handle_pipeline_objections(self) -> Dict[str, Any]:
        """Handle objections across pipeline deals"""
        objections_handled = []
        
        # Simulate common objections in pipeline
        pipeline_objections = [
            {
                "deal_id": "deal_001",
                "objection_type": "price_objection",
                "objection_content": "The price seems high compared to competitors",
                "stakeholder": "CFO"
            },
            {
                "deal_id": "deal_002",
                "objection_type": "timing_objection", 
                "objection_content": "We want to wait until Q2 to implement",
                "stakeholder": "IT Director"
            },
            {
                "deal_id": "deal_003",
                "objection_type": "authority_objection",
                "objection_content": "I need to discuss with the board",
                "stakeholder": "CEO"
            }
        ]
        
        for objection in pipeline_objections:
            handling_result = await self._handle_specific_objection(objection)
            objections_handled.append({
                **objection,
                "handling_result": handling_result
            })
        
        return {
            "deals_advanced": [],
            "objections_handled": objections_handled,
            "contracts_sent": [],
            "deals_closed": [],
            "revenue_recognized": []
        }

    async def _handle_specific_objection(self, objection: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific objection with targeted response"""
        objection_type = ObjectionType(objection["objection_type"])
        stakeholder = objection["stakeholder"]
        
        # Select appropriate response based on objection type
        responses = self.objection_responses.get(objection_type, ["Let's discuss this further"])
        selected_response = responses[0]  # Use first response for simulation
        
        # Simulate objection handling
        if objection_type == ObjectionType.PRICE_OBJECTION:
            return await self._handle_price_objection(objection, selected_response)
        elif objection_type == ObjectionType.TIMING_OBJECTION:
            return await self._handle_timing_objection(objection, selected_response)
        elif objection_type == ObjectionType.AUTHORITY_OBJECTION:
            return await self._handle_authority_objection(objection, selected_response)
        
        return {"response": selected_response, "objection_resolved": True}

    async def _handle_price_objection(self, objection: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Handle price objection with ROI focus"""
        return {
            "response_strategy": "roi_demonstration",
            "response": response,
            "supporting_materials": ["ROI calculator", "Case study", "Cost comparison"],
            "follow_up_action": "Schedule CFO call to review financial impact",
            "objection_resolved": True,
            "next_step": "proposal_revision_with_roi"
        }

    async def _handle_timing_objection(self, objection: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Handle timing objection with urgency creation"""
        return {
            "response_strategy": "urgency_creation",
            "response": response,
            "urgency_factors": ["Market conditions", "Competitive advantage", "Budget cycles"],
            "follow_up_action": "Demonstrate cost of waiting",
            "objection_resolved": True,
            "next_step": "phased_implementation_proposal"
        }

    async def _handle_authority_objection(self, objection: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Handle authority objection with stakeholder engagement"""
        return {
            "response_strategy": "stakeholder_engagement",
            "response": response,
            "action_plan": ["Request board presentation", "Prepare executive summary", "Identify champion"],
            "follow_up_action": "Schedule board presentation",
            "objection_resolved": False,  # Requires further engagement
            "next_step": "executive_stakeholder_meeting"
        }

    async def _accelerate_contract_process(self) -> Dict[str, Any]:
        """Accelerate contract and signature process"""
        contracts_sent = []
        
        # Simulate contracts ready to send
        ready_contracts = [
            {
                "deal_id": "deal_004",
                "account_name": "New Enterprise Client",
                "contract_value": 950000.0,
                "terms_agreed": True
            }
        ]
        
        for contract in ready_contracts:
            send_result = await self._send_expedited_contract(contract)
            contracts_sent.append({
                **contract,
                "send_result": send_result
            })
        
        return {
            "deals_advanced": [],
            "objections_handled": [],
            "contracts_sent": contracts_sent,
            "deals_closed": [],
            "revenue_recognized": []
        }

    async def _send_expedited_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Send contract with expedited processing"""
        return {
            "contract_sent": True,
            "expedited_processing": True,
            "legal_review_expedited": True,
            "signature_deadline": (datetime.now() + timedelta(days=5)).isoformat(),
            "follow_up_schedule": "Daily until signed"
        }

    async def _execute_closing_calls(self) -> Dict[str, Any]:
        """Execute scheduled closing calls"""
        return {
            "deals_advanced": [],
            "objections_handled": [],
            "contracts_sent": [],
            "deals_closed": [],
            "revenue_recognized": []
        }

    async def _recognize_closed_revenue(self) -> Dict[str, Any]:
        """Process and recognize closed revenue"""
        deals_closed = []
        revenue_recognized = []
        
        # Simulate recently closed deals
        closed_deals = [
            {
                "deal_id": "deal_002",
                "account_name": "Global Fintech Solutions",
                "deal_value": 850000.0,
                "close_date": datetime.now().isoformat(),
                "contract_length": "24_months"
            }
        ]
        
        for deal in closed_deals:
            recognition_result = await self._process_revenue_recognition(deal)
            deals_closed.append(deal)
            revenue_recognized.append(recognition_result)
        
        return {
            "deals_advanced": [],
            "objections_handled": [],
            "contracts_sent": [],
            "deals_closed": deals_closed,
            "revenue_recognized": revenue_recognized
        }

    async def _process_revenue_recognition(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Process revenue recognition for closed deal"""
        return {
            "deal_id": deal["deal_id"],
            "amount": deal["deal_value"],
            "recognition_date": deal["close_date"],
            "payment_schedule": "Annual prepay",
            "revenue_type": "new_business",
            "booking_confirmed": True
        }

    async def _identify_immediate_closing_actions(self, deals_advanced: List[Dict[str, Any]]) -> List[str]:
        """Identify immediate actions needed for deal advancement"""
        actions = []
        
        high_probability_deals = [d for d in deals_advanced if d.get('probability', 0) > 0.8]
        if high_probability_deals:
            actions.append(f"Execute signature acceleration for {len(high_probability_deals)} high-probability deals")
        
        negotiation_deals = [d for d in deals_advanced if d.get('current_stage') == 'negotiation_active']
        if negotiation_deals:
            actions.append(f"Close negotiations for {len(negotiation_deals)} active deals")
        
        contract_deals = [d for d in deals_advanced if d.get('current_stage') == 'contracts_sent']
        if contract_deals:
            actions.append(f"Follow up daily on {len(contract_deals)} pending signatures")
        
        actions.extend([
            "Conduct end-of-quarter urgency campaign",
            "Schedule decision-maker calls for stalled deals",
            "Prepare discount approvals for price-sensitive deals"
        ])
        
        return actions

    async def _forecast_next_48h_closing_activity(self, deals_advanced: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Forecast closing activity for next 48 hours"""
        return {
            "scheduled_closing_calls": 8,
            "contract_signatures_expected": 3,
            "objection_handling_sessions": 5,
            "proposal_follow_ups": 12,
            "potential_revenue_at_risk": 2100000.0,
            "deals_likely_to_close": 4
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and performance metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "capabilities": self.capabilities,
            "performance_metrics": {
                "deals_closed": self.deals_closed_count,
                "total_revenue_closed": self.total_revenue_closed,
                "current_close_rate": self.current_close_rate,
                "average_deal_cycle_days": self.average_deal_cycle_days,
                "objections_handled": self.objections_handled_count
            },
            "closing_targets": self.closing_targets,
            "closing_techniques": {
                technique.value: success_rate 
                for technique, success_rate in self.technique_success_rates.items()
            },
            "active_deals": {
                "total_opportunities": len(self.deal_opportunities),
                "hot_deals": len([d for d in self.deal_opportunities.values() 
                               if d.probability > 0.75]),
                "closing_sessions_this_week": len([s for s in self.closing_sessions.values()
                                                 if s.session_date >= datetime.now() - timedelta(days=7)]),
                "pipeline_value": sum(d.deal_value for d in self.deal_opportunities.values())
            },
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }

# Global agent instance
deal_closer_agent = DealCloserAgent()