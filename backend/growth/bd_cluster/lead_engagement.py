"""
Lead Engagement Agent - Ultra-Aggressive Multi-Touch Engagement Engine

Ultra-aggressive lead engagement agent that executes personalized, multi-channel 
engagement sequences with hyper-persistent follow-up and meeting conversion optimization.
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

class EngagementChannel(Enum):
    """Multi-channel engagement options"""
    EMAIL = "email"
    LINKEDIN_MESSAGE = "linkedin_message"
    LINKEDIN_INMAIL = "linkedin_inmail"
    COLD_CALL = "cold_call"
    VIDEO_MESSAGE = "video_message"
    DIRECT_MAIL = "direct_mail"
    SMS = "sms"
    SOCIAL_ENGAGEMENT = "social_engagement"
    REFERRAL_INTRODUCTION = "referral_introduction"

class EngagementStage(Enum):
    """Engagement sequence stages"""
    INITIAL_OUTREACH = "initial_outreach"
    VALUE_DEMONSTRATION = "value_demonstration"
    PAIN_POINT_DISCOVERY = "pain_point_discovery"
    CASE_STUDY_SHARING = "case_study_sharing"
    DEMO_INVITATION = "demo_invitation"
    URGENCY_CREATION = "urgency_creation"
    FINAL_ATTEMPT = "final_attempt"
    MEETING_SCHEDULED = "meeting_scheduled"
    DISENGAGED = "disengaged"

class MessageType(Enum):
    """Types of engagement messages"""
    PERSONALIZED_INTRO = "personalized_intro"
    VALUE_PROPOSITION = "value_proposition"
    PAIN_POINT_QUESTION = "pain_point_question"
    CASE_STUDY = "case_study"
    DEMO_REQUEST = "demo_request"
    SOCIAL_PROOF = "social_proof"
    URGENCY_DRIVER = "urgency_driver"
    BREAKUP_EMAIL = "breakup_email"
    FOLLOW_UP_QUESTION = "follow_up_question"

@dataclass
class EngagementTouch:
    """Individual engagement touch point"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    sequence_id: str = ""
    touch_number: int = 0
    
    # Touch configuration
    channel: EngagementChannel = EngagementChannel.EMAIL
    message_type: MessageType = MessageType.PERSONALIZED_INTRO
    stage: EngagementStage = EngagementStage.INITIAL_OUTREACH
    
    # Timing
    scheduled_date: datetime = field(default_factory=datetime.now)
    sent_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    
    # Content
    subject_line: str = ""
    message_content: str = ""
    call_to_action: str = ""
    personalization_elements: List[str] = field(default_factory=list)
    
    # Performance
    delivered: bool = False
    opened: bool = False
    clicked: bool = False
    responded: bool = False
    meeting_booked: bool = False
    
    # Response handling
    response_content: str = ""
    response_sentiment: str = ""  # positive, neutral, negative, objection
    next_action: str = ""

@dataclass
class EngagementSequence:
    """Multi-touch engagement sequence"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    sequence_name: str = ""
    sequence_type: str = ""  # champion, qualified, nurture, breakup
    
    # Configuration
    touches: List[EngagementTouch] = field(default_factory=list)
    channels_used: List[EngagementChannel] = field(default_factory=list)
    cadence_days: List[int] = field(default_factory=list)
    
    # Status tracking
    status: str = "active"  # active, paused, completed, responded
    current_touch: int = 0
    total_touches: int = 0
    
    # Performance metrics
    touches_sent: int = 0
    opens: int = 0
    clicks: int = 0
    responses: int = 0
    meetings_booked: int = 0
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    last_touch_sent: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class LeadProfile:
    """Enhanced lead profile for engagement optimization"""
    lead_id: str = ""
    
    # Contact intelligence
    preferred_communication: EngagementChannel = EngagementChannel.EMAIL
    timezone: str = "UTC"
    best_contact_times: List[str] = field(default_factory=list)
    communication_style: str = ""  # formal, casual, technical, executive
    
    # Behavioral insights
    email_engagement_pattern: str = ""  # high, medium, low
    social_media_activity: str = ""
    content_preferences: List[str] = field(default_factory=list)
    
    # Business context
    current_initiatives: List[str] = field(default_factory=list)
    competitive_landscape: List[str] = field(default_factory=list)
    decision_making_process: str = ""
    influence_network: List[str] = field(default_factory=list)
    
    # Engagement history
    previous_touches: int = 0
    last_engagement_date: Optional[datetime] = None
    engagement_response_rate: float = 0.0
    preferred_meeting_types: List[str] = field(default_factory=list)

class LeadEngagementAgent:
    """Ultra-aggressive lead engagement and conversion agent"""
    
    def __init__(self):
        self.agent_id = "lead-engagement-agent"
        self.name = "Lead Engagement Agent"
        self.specialization = "ultra_aggressive_lead_engagement_conversion"
        self.capabilities = [
            "multi_touch_sequences", "personalized_outreach", "meeting_conversion",
            "objection_handling", "engagement_optimization", "follow_up_automation"
        ]
        
        # Engagement database
        self.engagement_sequences: Dict[str, EngagementSequence] = {}
        self.lead_profiles: Dict[str, LeadProfile] = {}
        self.active_touches: Dict[str, EngagementTouch] = {}
        
        # Sequence templates
        self.sequence_templates = {
            "champion_sequence": {
                "touches": 7,
                "cadence": [0, 2, 5, 8, 12, 16, 21],  # Days between touches
                "channels": [
                    EngagementChannel.EMAIL,
                    EngagementChannel.LINKEDIN_MESSAGE,
                    EngagementChannel.COLD_CALL,
                    EngagementChannel.EMAIL,
                    EngagementChannel.VIDEO_MESSAGE,
                    EngagementChannel.COLD_CALL,
                    EngagementChannel.EMAIL
                ]
            },
            "qualified_sequence": {
                "touches": 5,
                "cadence": [0, 3, 7, 14, 21],
                "channels": [
                    EngagementChannel.EMAIL,
                    EngagementChannel.LINKEDIN_MESSAGE,
                    EngagementChannel.EMAIL,
                    EngagementChannel.COLD_CALL,
                    EngagementChannel.EMAIL
                ]
            },
            "nurture_sequence": {
                "touches": 4,
                "cadence": [0, 7, 21, 45],
                "channels": [
                    EngagementChannel.EMAIL,
                    EngagementChannel.EMAIL,
                    EngagementChannel.LINKEDIN_MESSAGE,
                    EngagementChannel.EMAIL
                ]
            }
        }
        
        # Performance parameters
        self.daily_engagement_target = 200  # Touches per day
        self.response_rate_target = 0.15    # 15% response rate target
        self.meeting_booking_rate_target = 0.08  # 8% meeting booking rate
        self.follow_up_persistence_days = 21     # Ultra-persistent follow-up
        
        # Performance metrics
        self.sequences_launched_count = 0
        self.touches_sent_count = 0
        self.responses_received_count = 0
        self.meetings_scheduled_count = 0
        self.current_response_rate = 0.0
        self.current_meeting_rate = 0.0
        
        logger.info(f"Lead Engagement Agent initialized - targeting {self.daily_engagement_target} touches/day")

    async def execute_engagement_blitz(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ultra-aggressive engagement blitz across all active leads"""
        blitz_type = parameters.get('blitz_type', 'comprehensive')
        target_leads = parameters.get('lead_ids', [])
        engagement_intensity = parameters.get('intensity', 'ultra_aggressive')
        force_progression = parameters.get('force_progression', True)
        
        logger.info(f"Starting {blitz_type} engagement blitz - targeting {len(target_leads)} leads")
        
        sequences_launched = []
        touches_executed = []
        responses_handled = []
        meetings_scheduled = []
        
        # Execute parallel engagement across all leads
        engagement_tasks = [
            self._process_new_lead_assignments(target_leads),
            self._execute_scheduled_touches(),
            self._handle_responses_and_objections(),
            self._escalate_ready_prospects(),
            self._optimize_underperforming_sequences()
        ]
        
        engagement_results = await asyncio.gather(*engagement_tasks, return_exceptions=True)
        
        # Process and consolidate results
        for i, result in enumerate(engagement_results):
            if isinstance(result, Exception):
                logger.error(f"Engagement task {i} failed: {result}")
                continue
                
            sequences_launched.extend(result.get('sequences_launched', []))
            touches_executed.extend(result.get('touches_executed', []))
            responses_handled.extend(result.get('responses_handled', []))
            meetings_scheduled.extend(result.get('meetings_scheduled', []))
        
        # Launch immediate follow-up for hot responses
        hot_responses = [r for r in responses_handled if r.get('sentiment') == 'positive']
        immediate_follow_ups = await self._launch_immediate_follow_ups(hot_responses)
        
        # Update performance metrics
        self.sequences_launched_count += len(sequences_launched)
        self.touches_sent_count += len(touches_executed)
        self.responses_received_count += len(responses_handled)
        self.meetings_scheduled_count += len(meetings_scheduled)
        
        # Calculate current rates
        if self.touches_sent_count > 0:
            self.current_response_rate = self.responses_received_count / self.touches_sent_count
            self.current_meeting_rate = self.meetings_scheduled_count / self.touches_sent_count
        
        logger.info(f"Engagement blitz completed: {len(touches_executed)} touches, " +
                   f"{len(responses_handled)} responses, {len(meetings_scheduled)} meetings")
        
        return {
            "success": True,
            "blitz_type": blitz_type,
            "execution_time_minutes": 35,  # Simulated
            "engagement_summary": {
                "sequences_launched": len(sequences_launched),
                "touches_executed": len(touches_executed),
                "responses_received": len(responses_handled),
                "meetings_scheduled": len(meetings_scheduled),
                "immediate_follow_ups": len(immediate_follow_ups)
            },
            "channel_performance": {
                "email": {"touches": len(touches_executed) * 0.4, "response_rate": 0.12},
                "linkedin": {"touches": len(touches_executed) * 0.3, "response_rate": 0.18},
                "phone": {"touches": len(touches_executed) * 0.2, "response_rate": 0.25},
                "video": {"touches": len(touches_executed) * 0.1, "response_rate": 0.35}
            },
            "response_breakdown": {
                "positive": len([r for r in responses_handled if r.get('sentiment') == 'positive']),
                "neutral": len([r for r in responses_handled if r.get('sentiment') == 'neutral']),
                "objection": len([r for r in responses_handled if r.get('sentiment') == 'objection']),
                "negative": len([r for r in responses_handled if r.get('sentiment') == 'negative'])
            },
            "meeting_outcomes": {
                "discovery_calls": len([m for m in meetings_scheduled if m.get('type') == 'discovery']),
                "demos": len([m for m in meetings_scheduled if m.get('type') == 'demo']),
                "decision_maker_calls": len([m for m in meetings_scheduled if m.get('type') == 'decision_maker'])
            },
            "performance_metrics": {
                "current_response_rate": self.current_response_rate,
                "current_meeting_rate": self.current_meeting_rate,
                "response_rate_vs_target": self.current_response_rate / self.response_rate_target,
                "meeting_rate_vs_target": self.current_meeting_rate / self.meeting_booking_rate_target
            },
            "immediate_actions": [
                f"Execute immediate follow-up for {len(hot_responses)} hot responses",
                f"Escalate {len([m for m in meetings_scheduled if m.get('type') == 'decision_maker'])} decision-maker meetings",
                f"Optimize {len([s for s in sequences_launched if s.get('performance') == 'low'])} underperforming sequences"
            ],
            "next_24h_pipeline": await self._forecast_next_24h_activity()
        }

    async def _process_new_lead_assignments(self, lead_ids: List[str]) -> Dict[str, Any]:
        """Process newly assigned leads and launch engagement sequences"""
        sequences_launched = []
        
        for lead_id in lead_ids:
            # Create lead profile if not exists
            if lead_id not in self.lead_profiles:
                self.lead_profiles[lead_id] = await self._create_lead_profile(lead_id)
            
            # Determine optimal sequence based on lead characteristics
            sequence_type = await self._determine_optimal_sequence(lead_id)
            
            # Launch engagement sequence
            sequence = await self._launch_engagement_sequence(lead_id, sequence_type)
            if sequence:
                sequences_launched.append(sequence)
        
        return {
            "sequences_launched": sequences_launched,
            "touches_executed": [],
            "responses_handled": [],
            "meetings_scheduled": []
        }

    async def _create_lead_profile(self, lead_id: str) -> LeadProfile:
        """Create comprehensive lead profile for engagement optimization"""
        # Simulate lead intelligence gathering
        profile = LeadProfile(
            lead_id=lead_id,
            preferred_communication=EngagementChannel.EMAIL,
            timezone="EST",
            best_contact_times=["9:00-11:00", "14:00-16:00"],
            communication_style="professional",
            email_engagement_pattern="medium",
            current_initiatives=["Digital transformation", "Trading platform upgrade"],
            decision_making_process="Committee-based with 3-6 stakeholders",
            preferred_meeting_types=["Discovery call", "Technical demo"]
        )
        
        return profile

    async def _determine_optimal_sequence(self, lead_id: str) -> str:
        """Determine optimal engagement sequence based on lead characteristics"""
        # Simulate lead scoring and sequence selection
        lead_profile = self.lead_profiles.get(lead_id)
        
        if not lead_profile:
            return "qualified_sequence"
        
        # Determine sequence based on various factors
        # High-value enterprise leads get champion treatment
        return "champion_sequence"  # Simplified for simulation

    async def _launch_engagement_sequence(self, lead_id: str, sequence_type: str) -> Optional[Dict[str, Any]]:
        """Launch personalized engagement sequence for lead"""
        template = self.sequence_templates.get(sequence_type)
        if not template:
            return None
        
        sequence = EngagementSequence(
            lead_id=lead_id,
            sequence_name=f"{sequence_type}_{datetime.now().strftime('%Y%m%d')}",
            sequence_type=sequence_type,
            total_touches=template["touches"],
            cadence_days=template["cadence"]
        )
        
        # Create all touches in the sequence
        for i in range(template["touches"]):
            touch = EngagementTouch(
                lead_id=lead_id,
                sequence_id=sequence.id,
                touch_number=i + 1,
                channel=template["channels"][i],
                scheduled_date=datetime.now() + timedelta(days=template["cadence"][i]),
                subject_line=await self._generate_subject_line(lead_id, i + 1, template["channels"][i]),
                message_content=await self._generate_message_content(lead_id, i + 1, template["channels"][i]),
                call_to_action=await self._generate_call_to_action(i + 1)
            )
            sequence.touches.append(touch)
        
        self.engagement_sequences[sequence.id] = sequence
        
        return {
            "sequence_id": sequence.id,
            "lead_id": lead_id,
            "sequence_type": sequence_type,
            "total_touches": template["touches"],
            "first_touch_scheduled": sequence.touches[0].scheduled_date.isoformat()
        }

    async def _execute_scheduled_touches(self) -> Dict[str, Any]:
        """Execute all scheduled touches for current time window"""
        touches_executed = []
        current_time = datetime.now()
        
        # Find all touches scheduled for execution
        for sequence in self.engagement_sequences.values():
            if sequence.status != "active":
                continue
                
            for touch in sequence.touches:
                if (touch.scheduled_date <= current_time and 
                    not touch.delivered and
                    touch.touch_number == sequence.current_touch + 1):
                    
                    # Execute the touch
                    execution_result = await self._execute_touch(touch)
                    if execution_result["success"]:
                        touch.delivered = True
                        touch.sent_date = current_time
                        sequence.current_touch += 1
                        sequence.touches_sent += 1
                        sequence.last_touch_sent = current_time
                        
                        touches_executed.append({
                            "touch_id": touch.id,
                            "lead_id": touch.lead_id,
                            "channel": touch.channel.value,
                            "touch_number": touch.touch_number,
                            "execution_result": execution_result
                        })
        
        return {
            "sequences_launched": [],
            "touches_executed": touches_executed,
            "responses_handled": [],
            "meetings_scheduled": []
        }

    async def _execute_touch(self, touch: EngagementTouch) -> Dict[str, Any]:
        """Execute individual engagement touch"""
        # Simulate touch execution based on channel
        if touch.channel == EngagementChannel.EMAIL:
            return await self._send_email(touch)
        elif touch.channel == EngagementChannel.LINKEDIN_MESSAGE:
            return await self._send_linkedin_message(touch)
        elif touch.channel == EngagementChannel.COLD_CALL:
            return await self._make_cold_call(touch)
        elif touch.channel == EngagementChannel.VIDEO_MESSAGE:
            return await self._send_video_message(touch)
        else:
            return {"success": True, "method": "generic_outreach"}

    async def _send_email(self, touch: EngagementTouch) -> Dict[str, Any]:
        """Send personalized email"""
        return {
            "success": True,
            "method": "email",
            "delivered": True,
            "tracking_enabled": True,
            "personalization_score": 0.85
        }

    async def _send_linkedin_message(self, touch: EngagementTouch) -> Dict[str, Any]:
        """Send LinkedIn message"""
        return {
            "success": True,
            "method": "linkedin_message",
            "connection_required": False,
            "message_type": "inmail"
        }

    async def _make_cold_call(self, touch: EngagementTouch) -> Dict[str, Any]:
        """Make cold call with voicemail follow-up"""
        return {
            "success": True,
            "method": "cold_call",
            "answered": False,
            "voicemail_left": True,
            "call_duration_seconds": 45
        }

    async def _send_video_message(self, touch: EngagementTouch) -> Dict[str, Any]:
        """Send personalized video message"""
        return {
            "success": True,
            "method": "video_message",
            "platform": "vidyard",
            "personalization_elements": ["company_research", "recent_news"],
            "video_length_seconds": 90
        }

    async def _handle_responses_and_objections(self) -> Dict[str, Any]:
        """Handle incoming responses and objections"""
        responses_handled = []
        
        # Simulate incoming responses
        simulated_responses = [
            {
                "touch_id": "touch_123",
                "lead_id": "lead_456",
                "content": "Thanks for reaching out. Can you send me more information?",
                "sentiment": "positive",
                "response_type": "information_request"
            },
            {
                "touch_id": "touch_124",
                "lead_id": "lead_457",
                "content": "Not interested right now, maybe in 6 months",
                "sentiment": "objection",
                "response_type": "timing_objection"
            },
            {
                "touch_id": "touch_125",
                "lead_id": "lead_458",
                "content": "I'd like to schedule a quick call to learn more",
                "sentiment": "positive",
                "response_type": "meeting_request"
            }
        ]
        
        for response in simulated_responses:
            # Handle the response based on sentiment and type
            handling_result = await self._handle_individual_response(response)
            responses_handled.append({
                **response,
                "handling_result": handling_result
            })
        
        return {
            "sequences_launched": [],
            "touches_executed": [],
            "responses_handled": responses_handled,
            "meetings_scheduled": [r for r in responses_handled if r.get('response_type') == 'meeting_request']
        }

    async def _handle_individual_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle individual response with appropriate action"""
        sentiment = response.get("sentiment")
        response_type = response.get("response_type")
        
        if sentiment == "positive":
            if response_type == "meeting_request":
                return await self._schedule_meeting(response["lead_id"])
            elif response_type == "information_request":
                return await self._send_information_package(response["lead_id"])
        elif sentiment == "objection":
            return await self._handle_objection(response["lead_id"], response_type)
        
        return {"action": "continue_sequence", "notes": "Standard response handling"}

    async def _schedule_meeting(self, lead_id: str) -> Dict[str, Any]:
        """Schedule meeting with responsive lead"""
        return {
            "action": "meeting_scheduled",
            "meeting_type": "discovery_call",
            "scheduled_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "duration_minutes": 30,
            "platform": "zoom"
        }

    async def _send_information_package(self, lead_id: str) -> Dict[str, Any]:
        """Send customized information package"""
        return {
            "action": "information_sent",
            "package_type": "customized_deck",
            "follow_up_scheduled": (datetime.now() + timedelta(days=3)).isoformat()
        }

    async def _handle_objection(self, lead_id: str, objection_type: str) -> Dict[str, Any]:
        """Handle specific objection with targeted response"""
        objection_responses = {
            "timing_objection": "Set follow-up for future timing",
            "budget_objection": "Provide ROI calculator and financing options",
            "authority_objection": "Request introduction to decision maker",
            "need_objection": "Share relevant case study and industry insights"
        }
        
        response_strategy = objection_responses.get(objection_type, "General objection handling")
        
        return {
            "action": "objection_handled",
            "objection_type": objection_type,
            "response_strategy": response_strategy,
            "follow_up_sequence": "objection_specific_nurture"
        }

    async def _escalate_ready_prospects(self) -> Dict[str, Any]:
        """Escalate prospects ready for next stage"""
        return {
            "sequences_launched": [],
            "touches_executed": [],
            "responses_handled": [],
            "meetings_scheduled": []
        }

    async def _optimize_underperforming_sequences(self) -> Dict[str, Any]:
        """Optimize sequences with poor performance"""
        return {
            "sequences_launched": [],
            "touches_executed": [],
            "responses_handled": [],
            "meetings_scheduled": []
        }

    async def _launch_immediate_follow_ups(self, hot_responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Launch immediate follow-up for hot responses"""
        immediate_follow_ups = []
        
        for response in hot_responses:
            follow_up = {
                "lead_id": response["lead_id"],
                "follow_up_type": "immediate_strike_while_hot",
                "scheduled_within_hours": 2,
                "priority": "urgent"
            }
            immediate_follow_ups.append(follow_up)
        
        return immediate_follow_ups

    async def _forecast_next_24h_activity(self) -> Dict[str, Any]:
        """Forecast engagement activity for next 24 hours"""
        return {
            "scheduled_touches": 85,
            "expected_responses": 12,
            "anticipated_meetings": 6,
            "sequences_completing": 8,
            "new_sequences_launching": 15
        }

    async def _generate_subject_line(self, lead_id: str, touch_number: int, channel: EngagementChannel) -> str:
        """Generate personalized subject line"""
        subject_templates = {
            1: "Quick question about [Company]'s trading platform",
            2: "Following up: 10x faster trade execution",
            3: "5-minute call about [Company]'s growth plans?",
            4: "Case study: Similar company saved $2M annually",
            5: "[Video] Personal message for [Contact Name]",
            6: "Final attempt: Trading technology efficiency",
            7: "Breaking up: Thanks for your time"
        }
        return subject_templates.get(touch_number, "Following up on our conversation")

    async def _generate_message_content(self, lead_id: str, touch_number: int, channel: EngagementChannel) -> str:
        """Generate personalized message content"""
        # Simplified message generation
        return f"Personalized message for touch #{touch_number} via {channel.value}"

    async def _generate_call_to_action(self, touch_number: int) -> str:
        """Generate appropriate call to action"""
        cta_templates = {
            1: "Worth a quick 10-minute call to discuss?",
            2: "Can we schedule a brief demo?",
            3: "Quick call this week?",
            4: "Interested in seeing similar results?",
            5: "15-minute demo available?",
            6: "Final chance for a conversation?",
            7: "Feel free to reach out if timing changes"
        }
        return cta_templates.get(touch_number, "Worth a conversation?")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and performance metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "capabilities": self.capabilities,
            "performance_metrics": {
                "sequences_launched": self.sequences_launched_count,
                "touches_sent": self.touches_sent_count,
                "responses_received": self.responses_received_count,
                "meetings_scheduled": self.meetings_scheduled_count,
                "current_response_rate": self.current_response_rate,
                "current_meeting_rate": self.current_meeting_rate
            },
            "target_metrics": {
                "daily_engagement_target": self.daily_engagement_target,
                "response_rate_target": self.response_rate_target,
                "meeting_booking_rate_target": self.meeting_booking_rate_target,
                "follow_up_persistence_days": self.follow_up_persistence_days
            },
            "active_engagements": {
                "total_sequences": len(self.engagement_sequences),
                "active_sequences": len([s for s in self.engagement_sequences.values() if s.status == "active"]),
                "lead_profiles": len(self.lead_profiles),
                "scheduled_touches_next_24h": len([t for s in self.engagement_sequences.values() 
                                                 for t in s.touches 
                                                 if t.scheduled_date <= datetime.now() + timedelta(days=1) and not t.delivered])
            },
            "status": "active",
            "last_updated": datetime.now().isoformat()
        }

# Global agent instance
lead_engagement_agent = LeadEngagementAgent()