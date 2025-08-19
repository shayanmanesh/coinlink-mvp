"""
Global Business Development & Marketing Growth Engine

Ultra-aggressive, globally proactive growth system with autonomous BD and Marketing clusters
synchronized by an intelligent Pipeline Orchestrator for measurable growth outcomes.
"""

from .data_models import (
    Lead, Opportunity, Campaign, Deal, GrowthMetrics, GrowthEvent,
    LeadSource, LeadStage, OpportunityStage, CampaignChannel, DealStatus, Priority,
    Contact, EngagementEvent
)

__version__ = "1.0.0"
__author__ = "CoinLink Growth Engine"

# Export main classes for easy importing
__all__ = [
    'Lead', 'Opportunity', 'Campaign', 'Deal', 'GrowthMetrics', 'GrowthEvent',
    'LeadSource', 'LeadStage', 'OpportunityStage', 'CampaignChannel', 'DealStatus', 'Priority',
    'Contact', 'EngagementEvent'
]