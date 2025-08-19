"""
Opportunity Scout Agent - Ultra-Aggressive Global Prospecting & Lead Discovery

Ultra-aggressive prospecting agent that hunts for high-value opportunities across 
global markets with hyper-targeted outreach and multi-channel engagement sequences.
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
    LeadSource, LeadStage, Contact, EngagementEvent
)

logger = logging.getLogger(__name__)

class ProspectingChannel(Enum):
    """Prospecting channels for opportunity discovery"""
    LINKEDIN_SALES_NAV = "linkedin_sales_nav"
    APOLLO = "apollo"
    ZOOMINFO = "zoominfo"
    SALESFORCE_DATA = "salesforce_data"
    INDUSTRY_EVENTS = "industry_events"
    PARTNER_REFERRALS = "partner_referrals"
    COLD_EMAIL = "cold_email"
    COLD_CALLING = "cold_calling"
    SOCIAL_SELLING = "social_selling"
    CONTENT_ENGAGEMENT = "content_engagement"

class ProspectScore(Enum):
    """Prospect scoring levels"""
    CHAMPION = "champion"      # 90-100: Ideal customer profile
    QUALIFIED = "qualified"    # 75-89: Strong fit
    POTENTIAL = "potential"    # 60-74: Good fit with qualification needed  
    NURTURE = "nurture"       # 40-59: Future opportunity
    DISQUALIFIED = "disqualified"  # 0-39: Poor fit

@dataclass
class ProspectProfile:
    """Comprehensive prospect intelligence profile"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    contact_name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    
    # Company intelligence
    company_size: str = ""  # startup, smb, mid_market, enterprise
    revenue_range: str = ""
    funding_stage: str = ""
    industry_vertical: str = ""
    headquarters: str = ""
    geographic_presence: List[str] = field(default_factory=list)
    
    # Technology stack
    current_technologies: List[str] = field(default_factory=list)
    tech_stack_gaps: List[str] = field(default_factory=list)
    integration_opportunities: List[str] = field(default_factory=list)
    
    # Pain points and triggers
    identified_pain_points: List[str] = field(default_factory=list)
    buying_triggers: List[str] = field(default_factory=list)
    competitive_threats: List[str] = field(default_factory=list)
    
    # Scoring and qualification
    prospect_score: int = 0  # 0-100
    score_category: ProspectScore = ProspectScore.POTENTIAL
    qualification_notes: str = ""
    
    # Engagement tracking
    discovery_channel: ProspectingChannel = ProspectingChannel.LINKEDIN_SALES_NAV
    discovery_date: datetime = field(default_factory=datetime.now)
    first_contact_date: Optional[datetime] = None
    last_engagement_date: Optional[datetime] = None
    engagement_count: int = 0
    
    # Decision-making intelligence
    decision_makers: List[str] = field(default_factory=list)
    influencers: List[str] = field(default_factory=list)
    budget_authority: str = ""
    decision_timeline: str = ""
    approval_process: str = ""
    
    # Account research
    recent_news: List[str] = field(default_factory=list)
    hiring_patterns: List[str] = field(default_factory=list)
    expansion_indicators: List[str] = field(default_factory=list)
    financial_health: str = ""

@dataclass
class ProspectingCampaign:
    """Multi-touch prospecting campaign"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    target_profile: str = ""  # ICP description
    prospect_ids: List[str] = field(default_factory=list)
    
    # Campaign configuration
    channels: List[ProspectingChannel] = field(default_factory=list)
    touch_sequence: List[Dict[str, Any]] = field(default_factory=list)
    cadence_days: List[int] = field(default_factory=list)
    
    # Performance tracking
    prospects_contacted: int = 0
    responses_received: int = 0
    meetings_scheduled: int = 0
    opportunities_created: int = 0
    
    # Status
    status: str = "active"  # active, paused, completed
    created_at: datetime = field(default_factory=datetime.now)
    launched_at: Optional[datetime] = None

class OpportunityScoutAgent:
    """Ultra-aggressive opportunity scouting and prospecting agent"""
    
    def __init__(self):
        self.agent_id = "opportunity-scout-agent"
        self.name = "Opportunity Scout Agent"
        self.specialization = "global_prospecting_opportunity_identification"
        self.capabilities = [
            "prospect_research", "lead_discovery", "qualification", 
            "outreach_automation", "multi_touch_campaigns", "account_mapping"
        ]
        
        # Prospect database
        self.prospect_profiles: Dict[str, ProspectProfile] = {}
        self.prospecting_campaigns: Dict[str, ProspectingCampaign] = {}
        self.discovered_opportunities: List[Dict[str, Any]] = []
        
        # Target configuration  
        self.target_markets = {
            "primary": ["fintech", "trading_platforms", "wealth_management"],
            "secondary": ["banking", "insurance", "crypto_exchanges"],
            "emerging": ["regtech", "defi", "neobanks"]
        }
        
        self.geographic_focus = {
            "tier_1": ["united_states", "canada", "united_kingdom", "germany"],
            "tier_2": ["australia", "singapore", "netherlands", "switzerland"],
            "tier_3": ["brazil", "india", "japan", "france"]
        }
        
        # Prospecting parameters
        self.daily_prospecting_target = 100  # Ultra-aggressive volume
        self.weekly_outreach_target = 500
        self.response_rate_target = 0.12  # 12% response rate target
        self.meeting_booking_target = 0.05  # 5% meeting booking rate
        
        # Performance metrics
        self.prospects_discovered_count = 0
        self.campaigns_launched_count = 0
        self.meetings_scheduled_count = 0
        self.opportunities_created_count = 0
        self.current_response_rate = 0.0
        
        logger.info(f"Opportunity Scout Agent initialized - targeting {self.daily_prospecting_target} prospects/day")

    async def execute_prospecting_sprint(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ultra-aggressive prospecting sprint"""
        sprint_type = parameters.get('sprint_type', 'comprehensive')
        target_count = parameters.get('target_count', self.daily_prospecting_target)
        focus_verticals = parameters.get('verticals', self.target_markets["primary"])
        geographic_regions = parameters.get('regions', self.geographic_focus["tier_1"])
        
        logger.info(f"Starting {sprint_type} prospecting sprint - target: {target_count} prospects")
        
        prospect_results = []
        qualified_prospects = []
        campaign_launches = []
        
        # Execute parallel prospecting across channels
        prospecting_tasks = [
            self._prospect_via_linkedin_sales_nav(target_count // 4, focus_verticals, geographic_regions),
            self._prospect_via_apollo(target_count // 4, focus_verticals, geographic_regions),
            self._prospect_via_zoominfo(target_count // 4, focus_verticals, geographic_regions),
            self._prospect_via_industry_events(target_count // 4, focus_verticals, geographic_regions)
        ]
        
        prospecting_results = await asyncio.gather(*prospecting_tasks, return_exceptions=True)
        
        # Process and consolidate results
        for i, result in enumerate(prospecting_results):
            if isinstance(result, Exception):
                logger.error(f"Prospecting task {i} failed: {result}")
                continue
                
            prospect_results.extend(result.get('prospects', []))
            qualified_prospects.extend(result.get('qualified', []))
        
        # Score and prioritize prospects
        prioritized_prospects = await self._score_and_prioritize_prospects(prospect_results)
        champion_prospects = [p for p in prioritized_prospects if p.get('score_category') == 'champion']
        
        # Launch immediate engagement campaigns for top prospects
        if champion_prospects:
            campaign = await self._launch_champion_engagement_campaign(champion_prospects)
            campaign_launches.append(campaign)
        
        # Create qualified leads for qualified prospects
        leads_created = await self._create_qualified_leads(qualified_prospects)
        
        # Update metrics
        self.prospects_discovered_count += len(prospect_results)
        self.campaigns_launched_count += len(campaign_launches)
        
        logger.info(f"Prospecting sprint completed: {len(prospect_results)} prospects, " +
                   f"{len(qualified_prospects)} qualified, {len(campaign_launches)} campaigns launched")
        
        return {
            "success": True,
            "sprint_type": sprint_type,
            "execution_time_minutes": 45,  # Simulated
            "prospecting_summary": {
                "total_prospects_discovered": len(prospect_results),
                "qualified_prospects": len(qualified_prospects),
                "champion_prospects": len(champion_prospects),
                "campaigns_launched": len(campaign_launches),
                "leads_created": len(leads_created)
            },
            "channel_performance": {
                "linkedin_sales_nav": {"prospects": len(prospect_results) // 4, "response_rate": 0.14},
                "apollo": {"prospects": len(prospect_results) // 4, "response_rate": 0.11},
                "zoominfo": {"prospects": len(prospect_results) // 4, "response_rate": 0.09},
                "industry_events": {"prospects": len(prospect_results) // 4, "response_rate": 0.18}
            },
            "geographic_coverage": geographic_regions,
            "vertical_coverage": focus_verticals,
            "top_prospects": prioritized_prospects[:10],  # Top 10
            "immediate_actions": [
                f"Initiate champion engagement for {len(champion_prospects)} top prospects",
                f"Queue qualification calls for {len(qualified_prospects)} qualified prospects",
                f"Launch nurture sequences for remaining prospects"
            ],
            "performance_metrics": {
                "discovery_rate": len(prospect_results) / target_count,
                "qualification_rate": len(qualified_prospects) / max(len(prospect_results), 1),
                "champion_rate": len(champion_prospects) / max(len(prospect_results), 1)
            },
            "next_sprint_recommendations": await self._generate_next_sprint_recommendations(prospect_results)
        }

    async def _prospect_via_linkedin_sales_nav(self, target_count: int, verticals: List[str], 
                                             regions: List[str]) -> Dict[str, Any]:
        """Prospect using LinkedIn Sales Navigator with advanced filters"""
        prospects = []
        qualified = []
        
        # Simulate LinkedIn Sales Navigator prospecting
        for vertical in verticals:
            for region in regions:
                # Advanced search filters simulation
                search_results = await self._simulate_linkedin_search(vertical, region, target_count // (len(verticals) * len(regions)))
                
                for result in search_results:
                    profile = ProspectProfile(
                        company_name=result["company"],
                        contact_name=result["name"],
                        title=result["title"],
                        linkedin_url=result["linkedin_url"],
                        company_size=result["company_size"],
                        industry_vertical=vertical,
                        headquarters=region,
                        discovery_channel=ProspectingChannel.LINKEDIN_SALES_NAV,
                        prospect_score=result["score"]
                    )
                    
                    prospects.append(profile.__dict__)
                    
                    # Auto-qualify high-scoring prospects
                    if result["score"] >= 75:
                        qualified.append(profile.__dict__)
        
        return {
            "prospects": prospects,
            "qualified": qualified,
            "channel": "linkedin_sales_nav"
        }

    async def _simulate_linkedin_search(self, vertical: str, region: str, count: int) -> List[Dict[str, Any]]:
        """Simulate LinkedIn Sales Navigator search results"""
        # Mock data representing LinkedIn search results
        base_prospects = [
            {
                "company": f"TradingTech {vertical.title()}",
                "name": "Sarah Johnson",
                "title": "VP of Trading Technology",
                "linkedin_url": "https://linkedin.com/in/sarah-johnson-trading",
                "company_size": "enterprise",
                "score": 92
            },
            {
                "company": f"{vertical.title()} Solutions Inc",
                "name": "Michael Chen",
                "title": "Chief Technology Officer",
                "linkedin_url": "https://linkedin.com/in/michael-chen-cto",
                "company_size": "mid_market",
                "score": 87
            },
            {
                "company": f"Global {vertical.title()} Partners",
                "name": "Amanda Rodriguez",
                "title": "Head of Digital Transformation",
                "linkedin_url": "https://linkedin.com/in/amanda-rodriguez-digital",
                "company_size": "enterprise",
                "score": 84
            },
            {
                "company": f"{region} {vertical.title()} Hub",
                "name": "David Kim",
                "title": "Director of Trading Operations",
                "linkedin_url": "https://linkedin.com/in/david-kim-trading",
                "company_size": "mid_market",
                "score": 78
            },
            {
                "company": f"Next-Gen {vertical.title()}",
                "name": "Lisa Wang",
                "title": "VP of Product",
                "linkedin_url": "https://linkedin.com/in/lisa-wang-product",
                "company_size": "startup",
                "score": 71
            }
        ]
        
        # Return subset based on requested count
        return base_prospects[:min(count, len(base_prospects))]

    async def _prospect_via_apollo(self, target_count: int, verticals: List[str], 
                                 regions: List[str]) -> Dict[str, Any]:
        """Prospect using Apollo.io with contact enrichment"""
        prospects = []
        qualified = []
        
        # Simulate Apollo prospecting with contact enrichment
        apollo_prospects = [
            {
                "company": "QuantTrading Systems",
                "name": "Robert Martinez",
                "title": "Head of Algorithmic Trading",
                "email": "r.martinez@quanttrading.com",
                "phone": "+1-555-0198",
                "company_size": "enterprise",
                "score": 89
            },
            {
                "company": "Crypto Exchange Platform",
                "name": "Jennifer Liu",
                "title": "VP of Business Development",
                "email": "j.liu@cryptoexchange.com",
                "phone": "+1-555-0145",
                "company_size": "mid_market",
                "score": 82
            },
            {
                "company": "Digital Asset Management",
                "name": "Thomas Anderson",
                "title": "Chief Investment Officer",
                "email": "t.anderson@digitalasset.com",
                "phone": "+1-555-0167",
                "company_size": "enterprise",
                "score": 86
            }
        ]
        
        for prospect_data in apollo_prospects[:target_count]:
            profile = ProspectProfile(
                company_name=prospect_data["company"],
                contact_name=prospect_data["name"],
                title=prospect_data["title"],
                email=prospect_data["email"],
                phone=prospect_data["phone"],
                company_size=prospect_data["company_size"],
                discovery_channel=ProspectingChannel.APOLLO,
                prospect_score=prospect_data["score"]
            )
            
            prospects.append(profile.__dict__)
            
            if prospect_data["score"] >= 75:
                qualified.append(profile.__dict__)
        
        return {
            "prospects": prospects,
            "qualified": qualified,
            "channel": "apollo"
        }

    async def _prospect_via_zoominfo(self, target_count: int, verticals: List[str], 
                                   regions: List[str]) -> Dict[str, Any]:
        """Prospect using ZoomInfo with intent data"""
        prospects = []
        qualified = []
        
        # Simulate ZoomInfo prospecting with intent signals
        zoominfo_prospects = [
            {
                "company": "Institutional Trading Corp",
                "name": "Maria Gonzalez",
                "title": "Director of Technology",
                "intent_signals": ["trading platform", "API integration", "real-time data"],
                "company_size": "enterprise",
                "score": 91
            },
            {
                "company": "Wealth Management Tech",
                "name": "James Wilson",
                "title": "VP of Engineering",
                "intent_signals": ["portfolio management", "client portal", "mobile trading"],
                "company_size": "mid_market",
                "score": 79
            }
        ]
        
        for prospect_data in zoominfo_prospects[:target_count]:
            profile = ProspectProfile(
                company_name=prospect_data["company"],
                contact_name=prospect_data["name"],
                title=prospect_data["title"],
                company_size=prospect_data["company_size"],
                buying_triggers=prospect_data["intent_signals"],
                discovery_channel=ProspectingChannel.ZOOMINFO,
                prospect_score=prospect_data["score"]
            )
            
            prospects.append(profile.__dict__)
            
            if prospect_data["score"] >= 75:
                qualified.append(profile.__dict__)
        
        return {
            "prospects": prospects,
            "qualified": qualified,
            "channel": "zoominfo"
        }

    async def _prospect_via_industry_events(self, target_count: int, verticals: List[str], 
                                          regions: List[str]) -> Dict[str, Any]:
        """Prospect via industry events and conferences"""
        prospects = []
        qualified = []
        
        # Simulate event-based prospecting
        event_prospects = [
            {
                "company": "Trade Show Fintech",
                "name": "Kevin Zhang",
                "title": "Head of Trading Technology",
                "event": "FinTech World 2025",
                "company_size": "enterprise",
                "score": 88
            },
            {
                "company": "Conference Capital",
                "name": "Nicole Taylor",
                "title": "Chief Operating Officer",
                "event": "Trading Technology Summit",
                "company_size": "mid_market",
                "score": 83
            }
        ]
        
        for prospect_data in event_prospects[:target_count]:
            profile = ProspectProfile(
                company_name=prospect_data["company"],
                contact_name=prospect_data["name"],
                title=prospect_data["title"],
                company_size=prospect_data["company_size"],
                discovery_channel=ProspectingChannel.INDUSTRY_EVENTS,
                prospect_score=prospect_data["score"],
                recent_news=[f"Attended {prospect_data['event']}"]
            )
            
            prospects.append(profile.__dict__)
            
            if prospect_data["score"] >= 75:
                qualified.append(profile.__dict__)
        
        return {
            "prospects": prospects,
            "qualified": qualified,
            "channel": "industry_events"
        }

    async def _score_and_prioritize_prospects(self, prospects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score and prioritize prospects using comprehensive criteria"""
        scored_prospects = []
        
        for prospect in prospects:
            # Calculate comprehensive prospect score
            base_score = prospect.get('prospect_score', 50)
            
            # Company size bonus
            size_bonus = {
                "enterprise": 20,
                "mid_market": 15,
                "startup": 10,
                "smb": 5
            }.get(prospect.get('company_size', ''), 0)
            
            # Title relevance bonus
            title = prospect.get('title', '').lower()
            title_bonus = 0
            if any(keyword in title for keyword in ['cto', 'vp', 'director', 'head']):
                title_bonus = 15
            elif any(keyword in title for keyword in ['manager', 'senior']):
                title_bonus = 10
            
            # Intent signal bonus
            intent_bonus = len(prospect.get('buying_triggers', [])) * 5
            
            # Channel quality bonus
            channel_bonus = {
                ProspectingChannel.INDUSTRY_EVENTS.value: 10,
                ProspectingChannel.PARTNER_REFERRALS.value: 15,
                ProspectingChannel.LINKEDIN_SALES_NAV.value: 8,
                ProspectingChannel.APOLLO.value: 6,
                ProspectingChannel.ZOOMINFO.value: 7
            }.get(prospect.get('discovery_channel', ''), 0)
            
            final_score = min(100, base_score + size_bonus + title_bonus + intent_bonus + channel_bonus)
            
            # Assign score category
            if final_score >= 90:
                score_category = ProspectScore.CHAMPION.value
            elif final_score >= 75:
                score_category = ProspectScore.QUALIFIED.value
            elif final_score >= 60:
                score_category = ProspectScore.POTENTIAL.value
            elif final_score >= 40:
                score_category = ProspectScore.NURTURE.value
            else:
                score_category = ProspectScore.DISQUALIFIED.value
            
            prospect['final_score'] = final_score
            prospect['score_category'] = score_category
            prospect['score_breakdown'] = {
                'base_score': base_score,
                'size_bonus': size_bonus,
                'title_bonus': title_bonus,
                'intent_bonus': intent_bonus,
                'channel_bonus': channel_bonus
            }
            
            scored_prospects.append(prospect)
        
        # Sort by final score descending
        return sorted(scored_prospects, key=lambda p: p['final_score'], reverse=True)

    async def _launch_champion_engagement_campaign(self, champion_prospects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Launch immediate high-touch engagement for champion prospects"""
        campaign = ProspectingCampaign(
            name="Champion_Prospect_Blitz_" + datetime.now().strftime("%Y%m%d"),
            target_profile="Champion prospects (90+ score)",
            prospect_ids=[p['id'] for p in champion_prospects],
            channels=[
                ProspectingChannel.LINKEDIN_SALES_NAV,
                ProspectingChannel.COLD_EMAIL,
                ProspectingChannel.COLD_CALLING
            ],
            touch_sequence=[
                {"day": 0, "channel": "linkedin", "message_type": "personalized_connection"},
                {"day": 1, "channel": "email", "message_type": "value_proposition"},
                {"day": 3, "channel": "phone", "message_type": "discovery_call"},
                {"day": 5, "channel": "email", "message_type": "case_study_share"},
                {"day": 7, "channel": "linkedin", "message_type": "thought_leadership"},
                {"day": 10, "channel": "phone", "message_type": "follow_up_call"},
                {"day": 14, "channel": "email", "message_type": "demo_invitation"}
            ],
            status="active",
            launched_at=datetime.now()
        )
        
        self.prospecting_campaigns[campaign.id] = campaign
        
        return {
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "prospects_targeted": len(champion_prospects),
            "touch_points_planned": len(campaign.touch_sequence),
            "expected_response_rate": 0.25,  # Higher for champion prospects
            "expected_meetings": int(len(champion_prospects) * 0.15)
        }

    async def _create_qualified_leads(self, qualified_prospects: List[Dict[str, Any]]) -> List[str]:
        """Create qualified leads from qualified prospects"""
        leads_created = []
        
        for prospect in qualified_prospects:
            lead = Lead(
                id=str(uuid.uuid4()),
                source=LeadSource.OUTBOUND_PROSPECTING,
                score=prospect.get('final_score', 75),
                stage=LeadStage.QUALIFIED,
                vertical=prospect.get('industry_vertical', 'fintech'),
                company_size=prospect.get('company_size', 'mid_market'),
                contact=Contact(
                    name=prospect.get('contact_name', ''),
                    email=prospect.get('email', ''),
                    phone=prospect.get('phone', ''),
                    title=prospect.get('title', ''),
                    company=prospect.get('company_name', '')
                ),
                pain_points=prospect.get('identified_pain_points', []),
                budget_range=prospect.get('budget_authority', 'unknown'),
                decision_timeline=prospect.get('decision_timeline', 'unknown')
            )
            
            leads_created.append(lead.id)
        
        return leads_created

    async def _generate_next_sprint_recommendations(self, prospects: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for next prospecting sprint"""
        recommendations = []
        
        if not prospects:
            recommendations.append("Expand prospecting channels and target markets")
            return recommendations
        
        # Analyze performance by channel
        channel_performance = {}
        for prospect in prospects:
            channel = prospect.get('discovery_channel', 'unknown')
            if channel not in channel_performance:
                channel_performance[channel] = {'count': 0, 'avg_score': 0}
            channel_performance[channel]['count'] += 1
            channel_performance[channel]['avg_score'] += prospect.get('final_score', 0)
        
        # Calculate averages
        for channel, data in channel_performance.items():
            data['avg_score'] = data['avg_score'] / data['count'] if data['count'] > 0 else 0
        
        # Generate recommendations based on performance
        best_channel = max(channel_performance.items(), key=lambda x: x[1]['avg_score'])
        recommendations.append(f"Increase prospecting volume through {best_channel[0]} (highest scoring channel)")
        
        # Vertical recommendations
        vertical_scores = {}
        for prospect in prospects:
            vertical = prospect.get('industry_vertical', 'unknown')
            if vertical not in vertical_scores:
                vertical_scores[vertical] = []
            vertical_scores[vertical].append(prospect.get('final_score', 0))
        
        for vertical, scores in vertical_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            if avg_score > 80:
                recommendations.append(f"Double prospecting efforts in {vertical} vertical (high scoring)")
        
        # General recommendations
        recommendations.extend([
            "Implement account-based prospecting for enterprise targets",
            "Develop vertical-specific value propositions",
            "Increase multi-channel touch frequency for top prospects",
            "Launch referral prospecting program with existing customers"
        ])
        
        return recommendations

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and performance metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "capabilities": self.capabilities,
            "performance_metrics": {
                "prospects_discovered": self.prospects_discovered_count,
                "campaigns_launched": self.campaigns_launched_count,
                "meetings_scheduled": self.meetings_scheduled_count,
                "opportunities_created": self.opportunities_created_count,
                "current_response_rate": self.current_response_rate
            },
            "target_metrics": {
                "daily_prospecting_target": self.daily_prospecting_target,
                "weekly_outreach_target": self.weekly_outreach_target,
                "response_rate_target": self.response_rate_target,
                "meeting_booking_target": self.meeting_booking_target
            },
            "prospecting_scope": {
                "target_markets": self.target_markets,
                "geographic_focus": self.geographic_focus,
                "active_campaigns": len(self.prospecting_campaigns),
                "prospect_database_size": len(self.prospect_profiles)
            },
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }

# Global agent instance
opportunity_scout_agent = OpportunityScoutAgent()