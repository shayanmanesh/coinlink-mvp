"""
R&D Department Backend Module
Independent research and development system for CoinLink innovation
"""

from .rd_interface import rd_agents
from .innovation_pipeline import innovation_pipeline
from .notification_system import email_notifier
from .rd_metrics import rd_metrics_tracker

# Note: rd_orchestrator is managed by the Apollo agent via rd_interface
apollo_orchestrator = "Managed by Apollo agent"

__all__ = [
    'rd_agents',
    'innovation_pipeline',
    'email_notifier',
    'rd_metrics_tracker',
    'apollo_orchestrator'
]