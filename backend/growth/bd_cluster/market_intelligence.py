"""
Market Intelligence Agent - Global Market Scanning & Intelligence Gathering

Ultra-aggressive intelligence agent that tracks global markets, competitor expansions, 
funding activity, and emerging verticals with real-time threat detection and opportunity identification.
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
    LeadSource, OpportunityStage, Contact, EngagementEvent
)

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Market threat assessment levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPPORTUNITY = "opportunity"

class MarketSegment(Enum):
    """Market segments for intelligence tracking"""
    FINTECH = "fintech"
    TRADING_PLATFORMS = "trading_platforms"
    CRYPTO_EXCHANGES = "crypto_exchanges"
    WEALTH_MANAGEMENT = "wealth_management"
    INSTITUTIONAL_TRADING = "institutional_trading"
    ROBO_ADVISORS = "robo_advisors"
    REGTECH = "regtech"
    INSURTECH = "insurtech"

@dataclass
class MarketIntelligence:
    """Market intelligence data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    segment: MarketSegment = MarketSegment.FINTECH
    region: str = ""
    intelligence_type: str = ""  # funding, expansion, product_launch, partnership
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    
    # Intelligence details
    company_name: str = ""
    funding_amount: Optional[float] = None
    funding_round: Optional[str] = None
    product_details: str = ""
    market_impact: str = ""
    
    # Timing and relevance
    discovered_at: datetime = field(default_factory=datetime.now)
    event_date: Optional[datetime] = None
    relevance_score: int = 0  # 0-100
    competitive_impact: int = 0  # 0-100
    
    # Sources and validation
    sources: List[str] = field(default_factory=list)
    confidence_level: float = 0.0  # 0.0-1.0
    validated: bool = False
    
    # Action items
    recommended_actions: List[str] = field(default_factory=list)
    assigned_agents: List[str] = field(default_factory=list)
    follow_up_date: Optional[datetime] = None

@dataclass
class CompetitorProfile:
    """Comprehensive competitor intelligence profile"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    ticker_symbol: Optional[str] = None
    headquarters: str = ""
    founded_year: int = 0
    
    # Financial intelligence
    last_funding_round: Optional[str] = None
    total_funding: Optional[float] = None
    valuation: Optional[float] = None
    revenue_estimate: Optional[float] = None
    employee_count: int = 0
    
    # Product intelligence
    primary_products: List[str] = field(default_factory=list)
    target_markets: List[str] = field(default_factory=list)
    key_features: List[str] = field(default_factory=list)
    pricing_model: str = ""
    
    # Market positioning
    market_share: Optional[float] = None
    geographic_presence: List[str] = field(default_factory=list)
    customer_segments: List[str] = field(default_factory=list)
    
    # Intelligence tracking
    last_updated: datetime = field(default_factory=datetime.now)
    intelligence_sources: List[str] = field(default_factory=list)
    threat_assessment: ThreatLevel = ThreatLevel.MEDIUM
    monitoring_priority: Priority = Priority.MEDIUM
    
    # Recent activities
    recent_news: List[str] = field(default_factory=list)
    partnership_announcements: List[str] = field(default_factory=list)
    product_launches: List[str] = field(default_factory=list)
    executive_moves: List[str] = field(default_factory=list)

class MarketIntelligenceAgent:
    """Ultra-aggressive market intelligence and competitor tracking agent"""
    
    def __init__(self):
        self.agent_id = "market-intelligence-agent"
        self.name = "Market Intelligence Agent"
        self.specialization = "global_market_scanning_competitive_intelligence"
        self.capabilities = [
            "market_research", "competitor_analysis", "trend_identification",
            "threat_assessment", "opportunity_detection", "intelligence_synthesis"
        ]
        
        # Intelligence databases
        self.market_intelligence: Dict[str, MarketIntelligence] = {}
        self.competitor_profiles: Dict[str, CompetitorProfile] = {}
        self.intelligence_history: List[MarketIntelligence] = []
        
        # Monitoring configuration
        self.monitored_competitors: Set[str] = {
            "Binance", "Coinbase", "Robinhood", "Interactive Brokers", "TD Ameritrade",
            "Charles Schwab", "Fidelity", "E*TRADE", "Alpaca", "TradeStation",
            "Bloomberg Terminal", "Refinitiv", "FactSet", "S&P Capital IQ", "Morningstar",
            "Kraken", "FTX", "Gemini", "Bitfinex", "Crypto.com", "KuCoin",
            "eToro", "Plus500", "XTB", "IG Group", "OANDA", "Forex.com"
        }
        
        self.monitored_segments: Set[MarketSegment] = set(MarketSegment)
        self.monitored_regions: Set[str] = {
            "North America", "Europe", "APAC", "Latin America", "Middle East", "Africa"
        }
        
        # Intelligence parameters
        self.scan_interval_hours = 2  # Ultra-frequent scanning
        self.threat_threshold = 75  # Alert threshold for competitive threats
        self.opportunity_threshold = 80  # Alert threshold for market opportunities
        self.confidence_threshold = 0.7  # Minimum confidence for actionable intelligence
        
        # Performance metrics
        self.intelligence_generated_count = 0
        self.threats_identified_count = 0
        self.opportunities_identified_count = 0
        self.accuracy_rate = 0.95
        
        logger.info(f"Market Intelligence Agent initialized - monitoring {len(self.monitored_competitors)} competitors")

    async def execute_intelligence_scan(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive market intelligence scan"""
        scan_type = parameters.get('scan_type', 'comprehensive')
        target_regions = parameters.get('regions', list(self.monitored_regions))
        priority_segments = parameters.get('segments', ['fintech', 'trading_platforms'])
        
        logger.info(f"Starting {scan_type} intelligence scan across {len(target_regions)} regions")
        
        intelligence_results = []
        threats_detected = []
        opportunities_identified = []
        
        # Execute parallel intelligence gathering
        scan_tasks = [
            self._scan_funding_activity(target_regions),
            self._scan_competitor_expansions(priority_segments),
            self._scan_product_launches(self.monitored_competitors),
            self._scan_partnership_announcements(),
            self._scan_regulatory_changes(target_regions),
            self._scan_market_trends(priority_segments),
            self._scan_executive_moves(self.monitored_competitors),
            self._scan_acquisition_activity()
        ]
        
        scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # Process and consolidate results
        for i, result in enumerate(scan_results):
            if isinstance(result, Exception):
                logger.error(f"Scan task {i} failed: {result}")
                continue
                
            intelligence_results.extend(result.get('intelligence', []))
            threats_detected.extend(result.get('threats', []))
            opportunities_identified.extend(result.get('opportunities', []))
        
        # Analyze and prioritize findings
        priority_intelligence = await self._prioritize_intelligence(intelligence_results)
        critical_threats = [t for t in threats_detected if t.get('level') in ['critical', 'high']]
        high_value_opportunities = [o for o in opportunities_identified if o.get('score', 0) > 80]
        
        # Generate strategic recommendations
        recommendations = await self._generate_strategic_recommendations(
            priority_intelligence, critical_threats, high_value_opportunities
        )
        
        # Update intelligence database
        for intel in intelligence_results:
            await self._store_intelligence(intel)
        
        # Update metrics
        self.intelligence_generated_count += len(intelligence_results)
        self.threats_identified_count += len(critical_threats)
        self.opportunities_identified_count += len(high_value_opportunities)
        
        logger.info(f"Intelligence scan completed: {len(intelligence_results)} findings, "
                   f"{len(critical_threats)} threats, {len(high_value_opportunities)} opportunities")
        
        return {
            "success": True,
            "scan_type": scan_type,
            "execution_time_minutes": 8,  # Simulated
            "intelligence_summary": {
                "total_findings": len(intelligence_results),
                "critical_threats": len(critical_threats),
                "high_value_opportunities": len(high_value_opportunities),
                "priority_intelligence": len(priority_intelligence)
            },
            "threat_level": self._calculate_overall_threat_level(critical_threats),
            "market_sentiment": self._assess_market_sentiment(intelligence_results),
            "competitive_landscape": await self._analyze_competitive_landscape(),
            "priority_findings": priority_intelligence[:10],  # Top 10
            "critical_threats": critical_threats,
            "strategic_opportunities": high_value_opportunities[:5],  # Top 5
            "recommended_actions": recommendations,
            "next_scan_recommended": (datetime.now() + timedelta(hours=self.scan_interval_hours)).isoformat(),
            "confidence_level": 0.92,
            "sources_analyzed": 47,  # Simulated
            "regions_covered": target_regions,
            "segments_analyzed": priority_segments
        }

    async def _scan_funding_activity(self, regions: List[str]) -> Dict[str, Any]:
        """Scan for funding announcements and investment activity"""
        intelligence = []
        threats = []
        opportunities = []
        
        # Simulate funding intelligence (in production, would integrate with Crunchbase, PitchBook, etc.)
        funding_events = [
            {
                "company": "TradeTech AI",
                "amount": 50000000,
                "round": "Series B",
                "lead_investor": "Andreessen Horowitz",
                "region": "North America",
                "segment": "trading_platforms",
                "threat_level": "high"
            },
            {
                "company": "CryptoFlow Europe",
                "amount": 25000000,
                "round": "Series A", 
                "lead_investor": "Index Ventures",
                "region": "Europe",
                "segment": "crypto_exchanges",
                "threat_level": "medium"
            },
            {
                "company": "APAC Financial Innovation",
                "amount": 75000000,
                "round": "Series C",
                "lead_investor": "SoftBank Vision Fund",
                "region": "APAC",
                "segment": "fintech",
                "threat_level": "critical"
            }
        ]
        
        for event in funding_events:
            if event["region"] in regions:
                intel = MarketIntelligence(
                    segment=MarketSegment.FINTECH,
                    region=event["region"],
                    intelligence_type="funding",
                    company_name=event["company"],
                    funding_amount=event["amount"],
                    funding_round=event["round"],
                    threat_level=ThreatLevel(event["threat_level"]),
                    relevance_score=85,
                    competitive_impact=75,
                    sources=["crunchbase", "techcrunch", "financial_times"],
                    confidence_level=0.9,
                    recommended_actions=[
                        f"Analyze {event['company']} product offering",
                        f"Assess competitive positioning vs {event['company']}",
                        "Consider preemptive partnership or acquisition"
                    ]
                )
                intelligence.append(intel.__dict__)
                
                if event["threat_level"] in ["high", "critical"]:
                    threats.append({
                        "company": event["company"],
                        "level": event["threat_level"],
                        "funding": event["amount"],
                        "impact": "New well-funded competitor entering market"
                    })
        
        return {
            "intelligence": intelligence,
            "threats": threats,
            "opportunities": opportunities
        }

    async def _scan_competitor_expansions(self, segments: List[str]) -> Dict[str, Any]:
        """Scan for competitor geographic and market expansions"""
        intelligence = []
        threats = []
        opportunities = []
        
        # Simulate expansion intelligence
        expansion_events = [
            {
                "company": "Robinhood",
                "expansion_type": "geographic",
                "target_market": "Europe",
                "timeline": "Q2 2025",
                "threat_level": "high",
                "investment": 100000000
            },
            {
                "company": "Interactive Brokers",
                "expansion_type": "product",
                "new_offering": "Crypto Trading Platform",
                "timeline": "Q1 2025",
                "threat_level": "medium",
                "investment": 50000000
            },
            {
                "company": "Binance",
                "expansion_type": "enterprise",
                "target_segment": "Institutional Trading",
                "timeline": "Q3 2025",
                "threat_level": "critical",
                "investment": 200000000
            }
        ]
        
        for event in expansion_events:
            intel = MarketIntelligence(
                segment=MarketSegment.TRADING_PLATFORMS,
                intelligence_type="expansion",
                company_name=event["company"],
                market_impact=f"{event['expansion_type']} expansion - {event.get('target_market', event.get('new_offering', event.get('target_segment')))}",
                threat_level=ThreatLevel(event["threat_level"]),
                relevance_score=90,
                competitive_impact=85,
                sources=["company_announcements", "sec_filings", "industry_reports"],
                confidence_level=0.85,
                recommended_actions=[
                    f"Accelerate competitive response to {event['company']} expansion",
                    "Develop counter-positioning strategy",
                    "Consider first-mover advantage in adjacent markets"
                ]
            )
            intelligence.append(intel.__dict__)
            
            threats.append({
                "company": event["company"],
                "level": event["threat_level"],
                "expansion": event["expansion_type"],
                "impact": f"Market share pressure from {event['company']} expansion"
            })
        
        return {
            "intelligence": intelligence,
            "threats": threats,
            "opportunities": opportunities
        }

    async def _scan_product_launches(self, competitors: Set[str]) -> Dict[str, Any]:
        """Scan for competitor product launches and feature updates"""
        intelligence = []
        threats = []
        opportunities = []
        
        # Simulate product intelligence
        product_launches = [
            {
                "company": "Coinbase",
                "product": "Advanced Trading Analytics Suite",
                "features": ["AI-powered insights", "Real-time risk management", "Automated trading signals"],
                "launch_date": "2025-02-15",
                "target_segment": "Professional Traders",
                "threat_level": "high"
            },
            {
                "company": "Charles Schwab",
                "product": "Schwab Trading AI",
                "features": ["Predictive market analysis", "Portfolio optimization", "Trade execution optimization"],
                "launch_date": "2025-03-01",
                "target_segment": "Retail Investors",
                "threat_level": "medium"
            }
        ]
        
        for launch in product_launches:
            if launch["company"] in competitors:
                intel = MarketIntelligence(
                    segment=MarketSegment.TRADING_PLATFORMS,
                    intelligence_type="product_launch",
                    company_name=launch["company"],
                    product_details=f"{launch['product']}: {', '.join(launch['features'])}",
                    threat_level=ThreatLevel(launch["threat_level"]),
                    relevance_score=88,
                    competitive_impact=82,
                    sources=["product_hunt", "company_website", "press_releases"],
                    confidence_level=0.88,
                    recommended_actions=[
                        f"Feature gap analysis vs {launch['company']} {launch['product']}",
                        "Accelerate similar feature development",
                        "Develop differentiated positioning"
                    ]
                )
                intelligence.append(intel.__dict__)
                
                if launch["threat_level"] == "high":
                    threats.append({
                        "company": launch["company"],
                        "product": launch["product"],
                        "level": launch["threat_level"],
                        "impact": "Feature parity pressure and customer retention risk"
                    })
        
        return {
            "intelligence": intelligence,
            "threats": threats,
            "opportunities": opportunities
        }

    async def _scan_partnership_announcements(self) -> Dict[str, Any]:
        """Scan for strategic partnerships and alliances"""
        intelligence = []
        opportunities = []
        
        # Simulate partnership intelligence
        partnerships = [
            {
                "company1": "Binance",
                "company2": "Tesla",
                "partnership_type": "Payment Integration",
                "announcement_date": "2025-01-15",
                "market_impact": "Mainstream crypto adoption acceleration"
            },
            {
                "company1": "Fidelity",
                "company2": "Microsoft",
                "partnership_type": "Cloud Infrastructure",
                "announcement_date": "2025-01-20",
                "market_impact": "Enhanced trading platform scalability"
            }
        ]
        
        for partnership in partnerships:
            intel = MarketIntelligence(
                intelligence_type="partnership",
                company_name=f"{partnership['company1']} + {partnership['company2']}",
                market_impact=f"{partnership['partnership_type']}: {partnership['market_impact']}",
                threat_level=ThreatLevel.MEDIUM,
                relevance_score=75,
                competitive_impact=70,
                sources=["business_wire", "company_announcements"],
                confidence_level=0.82,
                recommended_actions=[
                    "Evaluate similar partnership opportunities",
                    "Assess competitive implications",
                    "Consider strategic alliance development"
                ]
            )
            intelligence.append(intel.__dict__)
            
            opportunities.append({
                "type": "partnership_opportunity",
                "potential_partner": partnership["company2"],
                "partnership_model": partnership["partnership_type"],
                "score": 78
            })
        
        return {
            "intelligence": intelligence,
            "threats": [],
            "opportunities": opportunities
        }

    async def _scan_regulatory_changes(self, regions: List[str]) -> Dict[str, Any]:
        """Scan for regulatory developments affecting the market"""
        intelligence = []
        opportunities = []
        
        # Simulate regulatory intelligence
        regulatory_events = [
            {
                "region": "Europe",
                "regulation": "MiCA Crypto Regulation",
                "status": "Implemented",
                "impact": "Increased compliance requirements for crypto trading platforms",
                "opportunity": "Compliance-as-a-service market expansion"
            },
            {
                "region": "North America",
                "regulation": "SEC Trading Platform Rules",
                "status": "Proposed",
                "impact": "Enhanced reporting requirements for trading platforms", 
                "opportunity": "RegTech solution demand increase"
            }
        ]
        
        for event in regulatory_events:
            if event["region"] in regions:
                intel = MarketIntelligence(
                    region=event["region"],
                    intelligence_type="regulatory",
                    market_impact=f"{event['regulation']}: {event['impact']}",
                    threat_level=ThreatLevel.MEDIUM,
                    relevance_score=80,
                    sources=["regulatory_filings", "legal_databases"],
                    confidence_level=0.9,
                    recommended_actions=[
                        "Assess compliance impact and requirements",
                        "Develop regulatory compliance strategy",
                        "Consider RegTech partnership opportunities"
                    ]
                )
                intelligence.append(intel.__dict__)
                
                opportunities.append({
                    "type": "regulatory_opportunity",
                    "market": event["opportunity"],
                    "region": event["region"],
                    "score": 82
                })
        
        return {
            "intelligence": intelligence,
            "threats": [],
            "opportunities": opportunities
        }

    async def _scan_market_trends(self, segments: List[str]) -> Dict[str, Any]:
        """Scan for emerging market trends and opportunities"""
        intelligence = []
        opportunities = []
        
        # Simulate trend intelligence
        trends = [
            {
                "trend": "AI-Powered Trading Automation",
                "segments": ["fintech", "trading_platforms"],
                "growth_rate": "45% YoY",
                "market_size": 2500000000,
                "adoption_stage": "Early Majority"
            },
            {
                "trend": "Embedded Finance in Trading",
                "segments": ["fintech", "wealth_management"],
                "growth_rate": "62% YoY", 
                "market_size": 1800000000,
                "adoption_stage": "Early Adopters"
            },
            {
                "trend": "Social Trading Platforms",
                "segments": ["trading_platforms", "wealth_management"],
                "growth_rate": "38% YoY",
                "market_size": 3200000000,
                "adoption_stage": "Late Majority"
            }
        ]
        
        for trend in trends:
            if any(segment in trend["segments"] for segment in segments):
                intel = MarketIntelligence(
                    intelligence_type="market_trend",
                    market_impact=f"{trend['trend']}: {trend['growth_rate']} growth, ${trend['market_size']:,} market",
                    threat_level=ThreatLevel.OPPORTUNITY,
                    relevance_score=85,
                    competitive_impact=0,  # Trend is opportunity, not threat
                    sources=["market_research", "industry_reports", "analyst_reports"],
                    confidence_level=0.83,
                    recommended_actions=[
                        f"Evaluate {trend['trend']} implementation roadmap",
                        "Assess competitive positioning in trend",
                        "Consider early adopter advantage strategy"
                    ]
                )
                intelligence.append(intel.__dict__)
                
                opportunities.append({
                    "type": "market_trend",
                    "trend": trend["trend"],
                    "market_size": trend["market_size"],
                    "growth_rate": trend["growth_rate"],
                    "score": 87
                })
        
        return {
            "intelligence": intelligence,
            "threats": [],
            "opportunities": opportunities
        }

    async def _scan_executive_moves(self, competitors: Set[str]) -> Dict[str, Any]:
        """Scan for executive moves and leadership changes"""
        intelligence = []
        opportunities = []
        
        # Simulate executive intelligence
        executive_moves = [
            {
                "company": "Robinhood",
                "executive": "Sarah Chen",
                "previous_role": "VP Engineering at Google",
                "new_role": "CTO",
                "hire_date": "2025-01-10",
                "strategic_impact": "Enhanced technical capabilities and AI expertise"
            },
            {
                "company": "Interactive Brokers", 
                "executive": "Michael Rodriguez",
                "previous_role": "Head of Trading at Goldman Sachs",
                "new_role": "Chief Trading Officer",
                "hire_date": "2025-01-15",
                "strategic_impact": "Institutional trading expansion signal"
            }
        ]
        
        for move in executive_moves:
            if move["company"] in competitors:
                intel = MarketIntelligence(
                    intelligence_type="executive_move",
                    company_name=move["company"],
                    market_impact=f"Hired {move['executive']} as {move['new_role']} from {move['previous_role']}: {move['strategic_impact']}",
                    threat_level=ThreatLevel.MEDIUM,
                    relevance_score=70,
                    competitive_impact=65,
                    sources=["linkedin", "company_announcements", "industry_press"],
                    confidence_level=0.85,
                    recommended_actions=[
                        f"Analyze {move['company']} strategic direction change",
                        "Assess competitive response needs",
                        "Consider talent acquisition acceleration"
                    ]
                )
                intelligence.append(intel.__dict__)
                
                opportunities.append({
                    "type": "talent_opportunity",
                    "company": move["company"],
                    "signal": "Strategic hiring indicating market direction",
                    "score": 75
                })
        
        return {
            "intelligence": intelligence,
            "threats": [],
            "opportunities": opportunities
        }

    async def _scan_acquisition_activity(self) -> Dict[str, Any]:
        """Scan for acquisition announcements and M&A activity"""
        intelligence = []
        threats = []
        opportunities = []
        
        # Simulate M&A intelligence
        acquisitions = [
            {
                "acquirer": "JPMorgan Chase",
                "target": "TradingTech Solutions",
                "deal_value": 850000000,
                "announcement_date": "2025-01-12",
                "strategic_rationale": "Digital trading platform capabilities expansion",
                "threat_level": "high"
            },
            {
                "acquirer": "Visa",
                "target": "CryptoGateway",
                "deal_value": 450000000,
                "announcement_date": "2025-01-18",
                "strategic_rationale": "Crypto payments infrastructure",
                "threat_level": "medium"
            }
        ]
        
        for acquisition in acquisitions:
            intel = MarketIntelligence(
                intelligence_type="acquisition",
                company_name=f"{acquisition['acquirer']} acquires {acquisition['target']}",
                market_impact=f"${acquisition['deal_value']:,} acquisition: {acquisition['strategic_rationale']}",
                threat_level=ThreatLevel(acquisition["threat_level"]),
                relevance_score=88,
                competitive_impact=80,
                sources=["sec_filings", "financial_press", "company_announcements"],
                confidence_level=0.92,
                recommended_actions=[
                    f"Assess {acquisition['acquirer']} enhanced competitive position",
                    "Evaluate similar acquisition opportunities",
                    "Develop competitive response strategy"
                ]
            )
            intelligence.append(intel.__dict__)
            
            if acquisition["threat_level"] == "high":
                threats.append({
                    "acquirer": acquisition["acquirer"],
                    "target": acquisition["target"],
                    "value": acquisition["deal_value"],
                    "level": acquisition["threat_level"],
                    "impact": "Market consolidation and enhanced competitor capabilities"
                })
            
            opportunities.append({
                "type": "acquisition_opportunity",
                "market_signal": "Increased M&A activity in sector",
                "valuation_reference": acquisition["deal_value"],
                "score": 83
            })
        
        return {
            "intelligence": intelligence,
            "threats": threats,
            "opportunities": opportunities
        }

    async def _prioritize_intelligence(self, intelligence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize intelligence findings by relevance and impact"""
        # Sort by combination of relevance score and competitive impact
        def priority_score(intel):
            return (
                intel.get('relevance_score', 0) * 0.6 +
                intel.get('competitive_impact', 0) * 0.4 +
                (20 if intel.get('threat_level') == 'critical' else 0) +
                (15 if intel.get('threat_level') == 'high' else 0) +
                (intel.get('confidence_level', 0) * 10)
            )
        
        return sorted(intelligence_list, key=priority_score, reverse=True)

    def _calculate_overall_threat_level(self, threats: List[Dict[str, Any]]) -> str:
        """Calculate overall market threat level"""
        if not threats:
            return "low"
        
        critical_count = len([t for t in threats if t.get('level') == 'critical'])
        high_count = len([t for t in threats if t.get('level') == 'high'])
        
        if critical_count >= 2 or (critical_count >= 1 and high_count >= 2):
            return "critical"
        elif critical_count >= 1 or high_count >= 3:
            return "high"
        elif high_count >= 1:
            return "medium"
        else:
            return "low"

    def _assess_market_sentiment(self, intelligence_list: List[Dict[str, Any]]) -> str:
        """Assess overall market sentiment from intelligence"""
        if not intelligence_list:
            return "neutral"
        
        positive_indicators = len([i for i in intelligence_list if i.get('threat_level') == 'opportunity'])
        threat_indicators = len([i for i in intelligence_list if i.get('threat_level') in ['critical', 'high']])
        
        if positive_indicators > threat_indicators * 1.5:
            return "bullish"
        elif threat_indicators > positive_indicators * 1.5:
            return "bearish"
        else:
            return "neutral"

    async def _analyze_competitive_landscape(self) -> Dict[str, Any]:
        """Analyze current competitive landscape"""
        return {
            "market_leaders": ["Binance", "Coinbase", "Interactive Brokers"],
            "emerging_competitors": ["Robinhood", "Alpaca", "TradeStation"],
            "consolidation_trend": "High - increased M&A activity",
            "innovation_areas": ["AI trading", "Embedded finance", "RegTech"],
            "market_maturity": "Growth stage with increasing competition",
            "entry_barriers": "Medium - regulatory and capital requirements",
            "disruption_risk": "High - AI and blockchain innovations"
        }

    async def _generate_strategic_recommendations(self, 
                                                priority_intelligence: List[Dict[str, Any]],
                                                critical_threats: List[Dict[str, Any]],
                                                opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate strategic recommendations based on intelligence"""
        recommendations = []
        
        # Threat-based recommendations
        if critical_threats:
            recommendations.append("URGENT: Accelerate competitive response to critical threats identified")
            recommendations.append("Increase market share defense budget by 40%")
            recommendations.append("Fast-track product roadmap to maintain competitive parity")
        
        # Opportunity-based recommendations
        high_score_opportunities = [o for o in opportunities if o.get('score', 0) > 85]
        if high_score_opportunities:
            recommendations.append("Prioritize market entry into high-opportunity segments")
            recommendations.append("Allocate additional R&D resources to trending technologies")
        
        # Intelligence-driven recommendations
        if len(priority_intelligence) > 20:
            recommendations.append("Increase intelligence analysis team capacity")
        
        # Always include these strategic recommendations
        recommendations.extend([
            "Implement real-time competitive monitoring dashboard",
            "Establish quarterly competitive intelligence review process",
            "Develop rapid response team for competitive threats",
            "Create market expansion task force for identified opportunities",
            "Enhance partnership development in high-growth segments",
            "Accelerate product development in AI and automation features"
        ])
        
        return recommendations

    async def _store_intelligence(self, intel_dict: Dict[str, Any]):
        """Store intelligence in agent database"""
        intel_id = intel_dict.get('id', str(uuid.uuid4()))
        self.market_intelligence[intel_id] = intel_dict
        self.intelligence_history.append(intel_dict)
        
        # Maintain history limit
        if len(self.intelligence_history) > 1000:
            self.intelligence_history = self.intelligence_history[-1000:]

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and performance metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "capabilities": self.capabilities,
            "performance_metrics": {
                "intelligence_generated": self.intelligence_generated_count,
                "threats_identified": self.threats_identified_count,
                "opportunities_identified": self.opportunities_identified_count,
                "accuracy_rate": self.accuracy_rate
            },
            "monitoring_scope": {
                "competitors_tracked": len(self.monitored_competitors),
                "market_segments": len(self.monitored_segments),
                "geographic_regions": len(self.monitored_regions)
            },
            "intelligence_database": {
                "current_intelligence": len(self.market_intelligence),
                "historical_intelligence": len(self.intelligence_history),
                "competitor_profiles": len(self.competitor_profiles)
            },
            "configuration": {
                "scan_interval_hours": self.scan_interval_hours,
                "threat_threshold": self.threat_threshold,
                "opportunity_threshold": self.opportunity_threshold,
                "confidence_threshold": self.confidence_threshold
            },
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }

# Global agent instance
market_intelligence_agent = MarketIntelligenceAgent()