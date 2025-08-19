"""
Frontend Department - Agent Management System

Ultra-responsive frontend agent management system for the CoinLink platform.
Coordinates Athena-UX, Hephaestus-Frontend, and Prometheus-Frontend agents
for maximum UI/UX performance and user experience optimization.
"""

from .frontend_interface import frontend_agents, FrontendInterface
from .ui_orchestrator import ui_orchestrator, UIOrchestrator
from .frontend_metrics import frontend_metrics_tracker, FrontendMetricsTracker
from .component_generator import component_generator, ComponentGenerator
from .design_system_manager import design_system_manager, DesignSystemManager

__version__ = "1.0.0"

__all__ = [
    "frontend_agents",
    "FrontendInterface", 
    "ui_orchestrator",
    "UIOrchestrator",
    "frontend_metrics_tracker",
    "FrontendMetricsTracker",
    "component_generator", 
    "ComponentGenerator",
    "design_system_manager",
    "DesignSystemManager"
]