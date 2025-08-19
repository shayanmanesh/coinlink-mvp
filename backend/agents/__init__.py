"""
CoinLink Agent Framework
Self-improving agent system for concurrent frontend and backend optimization
"""

from .base import BaseAgent, AgentRole, AgentSwarm
from .orchestrator.helios import HeliosMasterOrchestrator
from .kpi_tracker import KPITracker
from .self_improvement import SelfImprovementEngine

__all__ = [
    'BaseAgent',
    'AgentRole', 
    'AgentSwarm',
    'HeliosMasterOrchestrator',
    'KPITracker',
    'SelfImprovementEngine'
]