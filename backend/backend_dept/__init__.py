"""
Backend Department - Agent Management System

Ultra-comprehensive backend agent management system for the CoinLink platform.
Coordinates Athena-API, Hephaestus-Backend, and Prometheus-Backend agents
for maximum API performance, database optimization, and infrastructure reliability.
"""

from .backend_interface import backend_agents, BackendInterface
from .api_orchestrator import api_orchestrator, APIOrchestrator
from .backend_metrics import backend_metrics_tracker, BackendMetricsTracker
from .service_manager import service_manager, ServiceManager
from .infrastructure_optimizer import infrastructure_optimizer, InfrastructureOptimizer

__version__ = "1.0.0"

__all__ = [
    "backend_agents",
    "BackendInterface",
    "api_orchestrator", 
    "APIOrchestrator",
    "backend_metrics_tracker",
    "BackendMetricsTracker",
    "service_manager",
    "ServiceManager",
    "infrastructure_optimizer",
    "InfrastructureOptimizer"
]