"""
Global Business Development & Marketing Growth Engine - Data Models
Shared data contracts for Lead, Opportunity, Campaign, Deal entities and growth metrics
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json

class LeadSource(Enum):
    """Lead acquisition channels"""
    INBOUND_ORGANIC = "inbound_organic"
    INBOUND_PAID = "inbound_paid"
    OUTBOUND_EMAIL = "outbound_email"
    OUTBOUND_LINKEDIN = "outbound_linkedin"
    OUTBOUND_PHONE = "outbound_phone"
    PARTNER_REFERRAL = "partner_referral"
    EVENT_GENERATED = "event_generated"
    CONTENT_DRIVEN = "content_driven"
    SOCIAL_MEDIA = "social_media"
    WEBINAR = "webinar"
    DEMO_REQUEST = "demo_request"

class LeadStage(Enum):
    """Lead qualification stages"""
    NEW = "new"
    RESEARCHING = "researching"
    QUALIFIED = "qualified"
    ENGAGED = "engaged"
    OPPORTUNITY = "opportunity"
    DISQUALIFIED = "disqualified"

class OpportunityStage(Enum):
    """Sales opportunity progression stages"""
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class CampaignChannel(Enum):
    """Marketing campaign channels"""
    PAID_SEARCH = "paid_search"
    PAID_SOCIAL = "paid_social"
    DISPLAY_ADS = "display_ads"
    EMAIL_MARKETING = "email_marketing"
    CONTENT_MARKETING = "content_marketing"
    SEO = "seo"
    PR = "pr"
    EVENTS = "events"
    WEBINARS = "webinars"
    PARTNERSHIPS = "partnerships"
    REFERRAL_PROGRAM = "referral_program"
    INFLUENCER = "influencer"

class DealStatus(Enum):
    """Deal completion status"""
    PENDING = "pending"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    CANCELLED = "cancelled"

class Priority(Enum):
    """Task and opportunity priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Contact:
    """Contact information for leads and opportunities"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    title: str = ""
    company: str = ""
    linkedin_url: str = ""
    timezone: str = ""
    preferred_contact: str = "email"
    
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

@dataclass
class EngagementEvent:
    """Track all interactions with leads/opportunities"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    type: str = ""  # email, call, meeting, demo, proposal, etc.
    channel: str = ""  # email, linkedin, phone, in_person, zoom
    subject: str = ""
    description: str = ""
    outcome: str = ""  # positive, neutral, negative, no_response
    next_action: str = ""
    next_action_date: Optional[datetime] = None
    agent_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Lead:
    """Core lead entity with qualification and tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: LeadSource = LeadSource.INBOUND_ORGANIC
    score: int = 0  # 0-100 lead scoring
    stage: LeadStage = LeadStage.NEW
    region: str = ""
    country: str = ""
    vertical: str = ""
    company_size: str = ""  # startup, smb, mid_market, enterprise
    annual_revenue: Optional[float] = None
    
    # Contact and company info
    contact: Contact = field(default_factory=Contact)
    company_info: Dict[str, Any] = field(default_factory=dict)
    
    # Engagement tracking
    engagement_history: List[EngagementEvent] = field(default_factory=list)
    first_contact: datetime = field(default_factory=datetime.now)
    last_contact: Optional[datetime] = None
    total_engagements: int = 0
    
    # Qualification details
    pain_points: List[str] = field(default_factory=list)
    budget_range: str = ""
    decision_timeline: str = ""
    decision_makers: List[str] = field(default_factory=list)
    
    # Assignment and tracking
    assigned_to: str = ""  # BD agent ID
    created_by: str = ""  # marketing campaign or BD agent
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Scoring and analytics
    demographic_score: int = 0
    behavioral_score: int = 0
    engagement_score: int = 0
    
    def update_score(self):
        """Calculate composite lead score"""
        self.score = min(100, self.demographic_score + self.behavioral_score + self.engagement_score)
        self.updated_at = datetime.now()

@dataclass 
class Opportunity:
    """Sales opportunity with deal progression tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    name: str = ""
    
    # Deal sizing
    value: float = 0.0
    arr_value: float = 0.0  # Annual Recurring Revenue
    probability: float = 0.0  # 0.0 to 1.0
    weighted_value: float = 0.0
    
    # Geographic and market info
    region: str = ""
    country: str = ""
    vertical: str = ""
    
    # Partnership info
    partner: Optional[str] = None
    partner_commission: float = 0.0
    
    # Sales progression
    stage: OpportunityStage = OpportunityStage.DISCOVERY
    stage_changed_at: datetime = field(default_factory=datetime.now)
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    
    # Sales process
    proposal_sent_date: Optional[datetime] = None
    demo_completed: bool = False
    pilot_program: bool = False
    contract_sent_date: Optional[datetime] = None
    
    # Stakeholders
    primary_contact_id: str = ""
    decision_makers: List[str] = field(default_factory=list)
    influencers: List[str] = field(default_factory=list)
    
    # Competition
    competitors: List[str] = field(default_factory=list)
    competitive_position: str = ""  # winning, at_risk, losing
    
    # Assignment
    assigned_bd_agent: str = ""
    assigned_ae: str = ""  # Account Executive
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    days_in_stage: int = 0
    total_sales_cycle_days: int = 0
    
    # Additional context
    notes: str = ""
    risk_factors: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    
    def calculate_weighted_value(self):
        """Update weighted pipeline value"""
        self.weighted_value = self.value * self.probability
        self.updated_at = datetime.now()
        
    def update_stage_timing(self):
        """Update stage duration tracking"""
        now = datetime.now()
        self.days_in_stage = (now - self.stage_changed_at).days
        self.total_sales_cycle_days = (now - self.created_at).days

@dataclass
class Campaign:
    """Marketing campaign with performance tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    channel: CampaignChannel = CampaignChannel.EMAIL_MARKETING
    type: str = ""  # awareness, demand_gen, nurture, retargeting
    
    # Targeting
    target_audience: str = ""
    target_regions: List[str] = field(default_factory=list)
    target_verticals: List[str] = field(default_factory=list)
    target_company_size: List[str] = field(default_factory=list)
    
    # Budget and spend
    budget: float = 0.0
    spend: float = 0.0
    remaining_budget: float = 0.0
    
    # Performance metrics
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    leads_generated: int = 0
    opportunities_created: int = 0
    deals_closed: int = 0
    
    # Calculated metrics
    ctr: float = 0.0  # Click-through rate
    conversion_rate: float = 0.0
    cpc: float = 0.0  # Cost per click
    cpl: float = 0.0  # Cost per lead
    cpa: float = 0.0  # Cost per acquisition
    roi: float = 0.0
    roas: float = 0.0  # Return on ad spend
    
    # Revenue tracking
    pipeline_generated: float = 0.0
    revenue_generated: float = 0.0
    
    # Timeline
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    duration_days: int = 0
    
    # Creative and messaging
    creative_assets: List[str] = field(default_factory=list)
    messaging_themes: List[str] = field(default_factory=list)
    
    # Status and management
    status: str = "draft"  # draft, active, paused, completed, cancelled
    assigned_to: str = ""  # marketing agent ID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # A/B testing
    variants: List[Dict[str, Any]] = field(default_factory=list)
    winning_variant: Optional[str] = None
    
    def calculate_metrics(self):
        """Recalculate all performance metrics"""
        if self.impressions > 0:
            self.ctr = self.clicks / self.impressions
        if self.clicks > 0 and self.spend > 0:
            self.cpc = self.spend / self.clicks
        if self.conversions > 0:
            self.conversion_rate = self.conversions / self.clicks if self.clicks > 0 else 0
        if self.leads_generated > 0 and self.spend > 0:
            self.cpl = self.spend / self.leads_generated
        if self.deals_closed > 0 and self.spend > 0:
            self.cpa = self.spend / self.deals_closed
        if self.spend > 0:
            self.roi = (self.revenue_generated - self.spend) / self.spend
            self.roas = self.revenue_generated / self.spend
        
        self.updated_at = datetime.now()

@dataclass
class Deal:
    """Closed deal with terms and revenue impact"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = ""
    lead_id: str = ""
    
    # Deal identification
    name: str = ""
    account_name: str = ""
    
    # Status and outcome
    status: DealStatus = DealStatus.PENDING
    win_reason: str = ""
    loss_reason: str = ""
    
    # Financial terms
    total_contract_value: float = 0.0
    annual_contract_value: float = 0.0
    monthly_recurring_revenue: float = 0.0
    one_time_revenue: float = 0.0
    
    # Contract terms
    contract_length_months: int = 12
    payment_terms: str = ""
    renewal_terms: str = ""
    discount_percentage: float = 0.0
    
    # Dates and timeline
    signed_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    
    # Assignment and attribution
    closing_agent: str = ""
    supporting_agents: List[str] = field(default_factory=list)
    originating_campaign: str = ""
    
    # Additional details
    implementation_notes: str = ""
    success_metrics: List[str] = field(default_factory=list)
    expansion_opportunities: List[str] = field(default_factory=list)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class GrowthMetrics:
    """Comprehensive growth and performance metrics"""
    
    # Time period for metrics
    period_start: datetime = field(default_factory=lambda: datetime.now() - timedelta(days=30))
    period_end: datetime = field(default_factory=datetime.now)
    
    # Pipeline metrics
    pipeline_volume: int = 0
    pipeline_value: float = 0.0
    weighted_pipeline: float = 0.0
    pipeline_velocity: float = 0.0  # days
    
    # Conversion metrics
    lead_to_opportunity_rate: float = 0.0
    opportunity_to_deal_rate: float = 0.0
    overall_conversion_rate: float = 0.0
    
    # Marketing metrics
    total_leads: int = 0
    mql_count: int = 0  # Marketing Qualified Leads
    sql_count: int = 0  # Sales Qualified Leads
    mql_to_sql_rate: float = 0.0
    
    # Cost metrics
    customer_acquisition_cost: float = 0.0
    customer_lifetime_value: float = 0.0
    ltv_cac_ratio: float = 0.0
    
    # Marketing channel performance
    marketing_spend: float = 0.0
    marketing_roi: float = 0.0
    best_performing_channel: str = ""
    worst_performing_channel: str = ""
    
    # Business development metrics
    outreach_volume: int = 0
    response_rate: float = 0.0
    meeting_conversion_rate: float = 0.0
    
    # Deal metrics
    total_deals_closed: int = 0
    total_revenue: float = 0.0
    average_deal_size: float = 0.0
    largest_deal: float = 0.0
    
    # Growth targets vs actual
    monthly_target_opportunities: int = 500
    monthly_target_revenue: float = 1000000.0
    target_conversion_rate: float = 0.15
    target_cac: float = 5000.0
    
    # Performance against targets
    opportunities_vs_target: float = 0.0
    revenue_vs_target: float = 0.0
    conversion_vs_target: float = 0.0
    
    def calculate_performance_ratios(self):
        """Calculate performance against targets"""
        if self.monthly_target_opportunities > 0:
            self.opportunities_vs_target = self.pipeline_volume / self.monthly_target_opportunities
        if self.monthly_target_revenue > 0:
            self.revenue_vs_target = self.total_revenue / self.monthly_target_revenue
        if self.target_conversion_rate > 0:
            self.conversion_vs_target = self.overall_conversion_rate / self.target_conversion_rate

@dataclass
class GrowthEvent:
    """Event for orchestrator communication between agents"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = ""
    source_agent: str = ""
    target_agent: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    
    # Event data
    entity_type: str = ""  # lead, opportunity, campaign, deal
    entity_id: str = ""
    action: str = ""  # created, updated, qualified, closed, etc.
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Processing
    processed: bool = False
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

# Export all models for easy importing
__all__ = [
    'LeadSource', 'LeadStage', 'OpportunityStage', 'CampaignChannel', 'DealStatus', 'Priority',
    'Contact', 'EngagementEvent', 'Lead', 'Opportunity', 'Campaign', 'Deal', 
    'GrowthMetrics', 'GrowthEvent'
]