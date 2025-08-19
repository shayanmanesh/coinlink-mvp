#!/usr/bin/env python3
"""
Growth Engine Validation and Testing System

Ultra-comprehensive validation system for the Growth Engine.
Tests all components, validates data models, checks agent connectivity,
and ensures system integrity for explosive growth operations.
"""

import asyncio
import sys
import traceback
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationResult:
    """Test validation result"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.error = None
        self.details = {}
        self.duration = 0.0
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "error": str(self.error) if self.error else None,
            "details": self.details,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat()
        }

class GrowthEngineValidator:
    """Comprehensive Growth Engine validation system"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🚀 GROWTH ENGINE ULTRA-COMPREHENSIVE VALIDATION")
        print("=" * 60)
        
        start_time = datetime.utcnow()
        
        # Test categories
        test_suites = [
            ("Data Models", self.validate_data_models),
            ("Growth Interface", self.validate_growth_interface),
            ("Pipeline Orchestrator", self.validate_pipeline_orchestrator),
            ("BD Agents", self.validate_bd_agents),
            ("Marketing Agents", self.validate_marketing_agents),
            ("Growth Metrics", self.validate_growth_metrics),
            ("Growth Scheduler", self.validate_growth_scheduler),
            ("Notification System", self.validate_notification_system),
            ("API Integration", self.validate_api_routes),
            ("System Integration", self.validate_system_integration)
        ]
        
        # Run test suites
        for suite_name, suite_func in test_suites:
            print(f"\n📊 Testing {suite_name}...")
            try:
                await suite_func()
            except Exception as e:
                logger.error(f"Test suite {suite_name} failed: {str(e)}")
                result = ValidationResult(f"{suite_name}_suite")
                result.error = e
                self.results.append(result)
                self.failed_tests += 1
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary report
        summary = self.generate_validation_summary(duration)
        
        print(f"\n{'='*60}")
        print("🏆 VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%" if self.total_tests > 0 else "0%")
        print(f"Total Duration: {duration:.2f}s")
        
        return summary
    
    async def validate_data_models(self):
        """Validate data models and structure"""
        try:
            from .data_models import Lead, Opportunity, Campaign, Deal, GrowthEvent, LeadSource, LeadStage
            
            # Test Lead model
            result = await self.run_test("Lead Model Creation", self._test_lead_model)
            
            # Test Opportunity model  
            result = await self.run_test("Opportunity Model Creation", self._test_opportunity_model)
            
            # Test Campaign model
            result = await self.run_test("Campaign Model Creation", self._test_campaign_model)
            
            # Test Deal model
            result = await self.run_test("Deal Model Creation", self._test_deal_model)
            
            # Test GrowthEvent model
            result = await self.run_test("GrowthEvent Model Creation", self._test_growth_event_model)
            
        except Exception as e:
            logger.error(f"Data models validation failed: {str(e)}")
            raise
    
    async def _test_lead_model(self) -> Dict[str, Any]:
        """Test Lead data model"""
        from .data_models import Lead, LeadSource, LeadStage
        
        lead = Lead(
            id="test_lead_001",
            source=LeadSource.WEBSITE,
            stage=LeadStage.NEW,
            score=85,
            company="Test Company",
            contact_name="John Doe",
            contact_email="john@testcompany.com",
            phone="+1-555-123-4567",
            website="https://testcompany.com"
        )
        
        # Validate field values
        assert lead.id == "test_lead_001"
        assert lead.source == LeadSource.WEBSITE
        assert lead.stage == LeadStage.NEW
        assert lead.score == 85
        assert lead.company == "Test Company"
        
        return {"lead_id": lead.id, "score": lead.score, "stage": lead.stage.value}
    
    async def _test_opportunity_model(self) -> Dict[str, Any]:
        """Test Opportunity data model"""
        from .data_models import Opportunity, OpportunityStage
        
        opportunity = Opportunity(
            id="test_opp_001",
            lead_id="test_lead_001",
            stage=OpportunityStage.QUALIFIED,
            value=750000.0,
            probability=0.75,
            company="Test Company"
        )
        
        assert opportunity.id == "test_opp_001"
        assert opportunity.value == 750000.0
        assert opportunity.probability == 0.75
        
        return {"opportunity_id": opportunity.id, "value": opportunity.value}
    
    async def _test_campaign_model(self) -> Dict[str, Any]:
        """Test Campaign data model"""
        from .data_models import Campaign, CampaignType, CampaignStatus
        
        campaign = Campaign(
            id="test_campaign_001",
            name="Test Campaign",
            campaign_type=CampaignType.PAID_SEARCH,
            status=CampaignStatus.ACTIVE,
            budget=50000.0,
            target_audience=["enterprise", "fintech"]
        )
        
        assert campaign.id == "test_campaign_001"
        assert campaign.budget == 50000.0
        assert len(campaign.target_audience) == 2
        
        return {"campaign_id": campaign.id, "budget": campaign.budget}
    
    async def _test_deal_model(self) -> Dict[str, Any]:
        """Test Deal data model"""
        from .data_models import Deal, DealStage
        
        deal = Deal(
            id="test_deal_001",
            opportunity_id="test_opp_001",
            stage=DealStage.NEGOTIATION,
            value=750000.0,
            company="Test Company"
        )
        
        assert deal.id == "test_deal_001"
        assert deal.value == 750000.0
        
        return {"deal_id": deal.id, "value": deal.value}
    
    async def _test_growth_event_model(self) -> Dict[str, Any]:
        """Test GrowthEvent data model"""
        from .data_models import GrowthEvent, EventType
        
        event = GrowthEvent(
            event_id="test_event_001",
            event_type=EventType.LEAD_CREATED,
            source_agent="opportunity_scout",
            data={"lead_id": "test_lead_001", "score": 85}
        )
        
        assert event.event_id == "test_event_001"
        assert event.source_agent == "opportunity_scout"
        assert "lead_id" in event.data
        
        return {"event_id": event.event_id, "event_type": event.event_type.value}
    
    async def validate_growth_interface(self):
        """Validate Growth Interface system"""
        try:
            from .growth_interface import GrowthInterface
            
            # Test interface initialization
            await self.run_test("Growth Interface Initialization", self._test_growth_interface_init)
            
            # Test agent registry
            await self.run_test("Agent Registry", self._test_agent_registry)
            
        except Exception as e:
            logger.error(f"Growth Interface validation failed: {str(e)}")
            raise
    
    async def _test_growth_interface_init(self) -> Dict[str, Any]:
        """Test Growth Interface initialization"""
        from .growth_interface import GrowthInterface
        
        interface = GrowthInterface()
        
        # Check that agents are registered
        assert len(interface.agents) > 0, "No agents registered"
        
        # Check for BD agents
        bd_agents = [agent_id for agent_id, info in interface.agents.items() if "bd" in info["type"]]
        assert len(bd_agents) >= 5, f"Expected 5 BD agents, found {len(bd_agents)}"
        
        # Check for Marketing agents
        marketing_agents = [agent_id for agent_id, info in interface.agents.items() if "marketing" in info["type"]]
        assert len(marketing_agents) >= 5, f"Expected 5 Marketing agents, found {len(marketing_agents)}"
        
        return {
            "total_agents": len(interface.agents),
            "bd_agents": len(bd_agents),
            "marketing_agents": len(marketing_agents)
        }
    
    async def _test_agent_registry(self) -> Dict[str, Any]:
        """Test agent registry functionality"""
        from .growth_interface import GrowthInterface
        
        interface = GrowthInterface()
        
        # Test getting agent info
        for agent_id, agent_info in interface.agents.items():
            assert "type" in agent_info
            assert "class" in agent_info
            assert "methods" in agent_info
            assert isinstance(agent_info["methods"], list)
            assert len(agent_info["methods"]) > 0
        
        return {"agents_validated": len(interface.agents)}
    
    async def validate_pipeline_orchestrator(self):
        """Validate Pipeline Orchestrator"""
        try:
            from .pipeline_orchestrator import PipelineOrchestrator
            from .data_models import GrowthEvent, EventType
            
            # Test orchestrator initialization
            await self.run_test("Pipeline Orchestrator Init", self._test_orchestrator_init)
            
            # Test event processing
            await self.run_test("Event Processing", self._test_event_processing)
            
        except Exception as e:
            logger.error(f"Pipeline Orchestrator validation failed: {str(e)}")
            raise
    
    async def _test_orchestrator_init(self) -> Dict[str, Any]:
        """Test Pipeline Orchestrator initialization"""
        from .pipeline_orchestrator import PipelineOrchestrator
        
        orchestrator = PipelineOrchestrator()
        
        assert hasattr(orchestrator, 'leads')
        assert hasattr(orchestrator, 'opportunities')
        assert hasattr(orchestrator, 'campaigns')
        assert hasattr(orchestrator, 'deals')
        
        return {"orchestrator_initialized": True}
    
    async def _test_event_processing(self) -> Dict[str, Any]:
        """Test event processing"""
        from .pipeline_orchestrator import PipelineOrchestrator
        from .data_models import GrowthEvent, EventType
        
        orchestrator = PipelineOrchestrator()
        
        # Create test event
        test_event = GrowthEvent(
            event_id="test_validation_event",
            event_type=EventType.LEAD_CREATED,
            source_agent="test_agent",
            data={"test": "data"}
        )
        
        # Process event
        result = await orchestrator.emit_event(test_event)
        assert result is True, "Event processing failed"
        
        return {"event_processed": True}
    
    async def validate_bd_agents(self):
        """Validate BD agent cluster"""
        try:
            # Test each BD agent
            bd_agents = [
                "market_intelligence",
                "opportunity_scout", 
                "lead_engagement",
                "partnership_negotiator",
                "deal_closer"
            ]
            
            for agent_id in bd_agents:
                await self.run_test(f"BD Agent: {agent_id}", self._test_bd_agent, agent_id)
                
        except Exception as e:
            logger.error(f"BD agents validation failed: {str(e)}")
            raise
    
    async def _test_bd_agent(self, agent_id: str) -> Dict[str, Any]:
        """Test individual BD agent"""
        try:
            if agent_id == "market_intelligence":
                from .bd_cluster.market_intelligence import MarketIntelligenceAgent
                agent = MarketIntelligenceAgent()
            elif agent_id == "opportunity_scout":
                from .bd_cluster.opportunity_scout import OpportunityScoutAgent
                agent = OpportunityScoutAgent()
            elif agent_id == "lead_engagement":
                from .bd_cluster.lead_engagement import LeadEngagementAgent
                agent = LeadEngagementAgent()
            elif agent_id == "partnership_negotiator":
                from .bd_cluster.partnership_negotiator import PartnershipNegotiatorAgent
                agent = PartnershipNegotiatorAgent()
            elif agent_id == "deal_closer":
                from .bd_cluster.deal_closer import DealCloserAgent
                agent = DealCloserAgent()
            else:
                raise ValueError(f"Unknown BD agent: {agent_id}")
            
            # Test agent has required methods
            required_methods = ["execute_", "_analyze_", "_generate_"]
            available_methods = [method for method in dir(agent) if any(req in method for req in required_methods)]
            
            assert len(available_methods) > 0, f"Agent {agent_id} has no required methods"
            
            return {
                "agent_id": agent_id,
                "class_name": agent.__class__.__name__,
                "available_methods": len(available_methods)
            }
            
        except Exception as e:
            logger.error(f"BD agent {agent_id} test failed: {str(e)}")
            raise
    
    async def validate_marketing_agents(self):
        """Validate Marketing agent cluster"""
        try:
            # Test each Marketing agent
            marketing_agents = [
                "marketing_strategy",
                "campaign_planner",
                "content_creation", 
                "campaign_execution",
                "marketing_analytics"
            ]
            
            for agent_id in marketing_agents:
                await self.run_test(f"Marketing Agent: {agent_id}", self._test_marketing_agent, agent_id)
                
        except Exception as e:
            logger.error(f"Marketing agents validation failed: {str(e)}")
            raise
    
    async def _test_marketing_agent(self, agent_id: str) -> Dict[str, Any]:
        """Test individual Marketing agent"""
        try:
            if agent_id == "marketing_strategy":
                from .marketing_cluster.marketing_strategy import MarketingStrategyAgent
                agent = MarketingStrategyAgent()
            elif agent_id == "campaign_planner":
                from .marketing_cluster.campaign_planner import CampaignPlannerAgent
                agent = CampaignPlannerAgent()
            elif agent_id == "content_creation":
                from .marketing_cluster.content_creation import ContentCreationAgent
                agent = ContentCreationAgent()
            elif agent_id == "campaign_execution":
                from .marketing_cluster.campaign_execution import CampaignExecutionAgent
                agent = CampaignExecutionAgent()
            elif agent_id == "marketing_analytics":
                from .marketing_cluster.marketing_analytics import MarketingAnalyticsAgent
                agent = MarketingAnalyticsAgent()
            else:
                raise ValueError(f"Unknown Marketing agent: {agent_id}")
            
            # Test agent has required methods
            required_methods = ["execute_", "_analyze_", "_generate_", "_create_"]
            available_methods = [method for method in dir(agent) if any(req in method for req in required_methods)]
            
            assert len(available_methods) > 0, f"Agent {agent_id} has no required methods"
            
            return {
                "agent_id": agent_id,
                "class_name": agent.__class__.__name__,
                "available_methods": len(available_methods)
            }
            
        except Exception as e:
            logger.error(f"Marketing agent {agent_id} test failed: {str(e)}")
            raise
    
    async def validate_growth_metrics(self):
        """Validate Growth Metrics system"""
        try:
            from .growth_metrics import GrowthMetricsTracker, MetricType, AgentPerformance
            
            # Test metrics tracker
            await self.run_test("Metrics Tracker Init", self._test_metrics_tracker)
            
            # Test performance tracking
            await self.run_test("Performance Tracking", self._test_performance_tracking)
            
        except Exception as e:
            logger.error(f"Growth Metrics validation failed: {str(e)}")
            raise
    
    async def _test_metrics_tracker(self) -> Dict[str, Any]:
        """Test metrics tracker initialization"""
        from .growth_metrics import GrowthMetricsTracker
        
        tracker = GrowthMetricsTracker()
        
        assert hasattr(tracker, 'agent_performances')
        assert hasattr(tracker, 'historical_metrics')
        assert hasattr(tracker, 'weekly_targets')
        assert len(tracker.weekly_targets) > 0
        
        return {
            "tracker_initialized": True,
            "weekly_targets": len(tracker.weekly_targets)
        }
    
    async def _test_performance_tracking(self) -> Dict[str, Any]:
        """Test performance tracking functionality"""
        from .growth_metrics import GrowthMetricsTracker, MetricType
        
        tracker = GrowthMetricsTracker()
        
        # Test agent performance tracking
        test_metrics = {
            "lead_generation": 50.0,
            "opportunity_conversion": 0.25
        }
        
        performance = await tracker.track_agent_performance(
            "test_agent",
            "bd_cluster",
            test_metrics
        )
        
        assert performance.agent_id == "test_agent"
        assert performance.agent_type == "bd_cluster"
        assert len(performance.daily_metrics) > 0
        
        return {
            "performance_tracked": True,
            "metrics_recorded": len(performance.daily_metrics)
        }
    
    async def validate_growth_scheduler(self):
        """Validate Growth Scheduler"""
        try:
            from .growth_scheduler import GrowthScheduler, SprintType, SprintIntensity
            
            # Test scheduler initialization
            await self.run_test("Scheduler Init", self._test_scheduler_init)
            
            # Test sprint schedules
            await self.run_test("Sprint Schedules", self._test_sprint_schedules)
            
        except Exception as e:
            logger.error(f"Growth Scheduler validation failed: {str(e)}")
            raise
    
    async def _test_scheduler_init(self) -> Dict[str, Any]:
        """Test scheduler initialization"""
        from .growth_scheduler import GrowthScheduler
        
        scheduler = GrowthScheduler()
        
        assert hasattr(scheduler, 'scheduled_sprints')
        assert hasattr(scheduler, 'active_executions')
        assert len(scheduler.scheduled_sprints) > 0
        
        return {
            "scheduler_initialized": True,
            "default_sprints": len(scheduler.scheduled_sprints)
        }
    
    async def _test_sprint_schedules(self) -> Dict[str, Any]:
        """Test sprint schedule validation"""
        from .growth_scheduler import GrowthScheduler
        
        scheduler = GrowthScheduler()
        
        # Validate each default sprint
        for sprint_id, sprint in scheduler.scheduled_sprints.items():
            assert sprint.sprint_id == sprint_id
            assert sprint.duration_minutes > 0
            assert len(sprint.cron_expression) > 0
            assert sprint.next_execution is not None
        
        return {
            "sprints_validated": len(scheduler.scheduled_sprints)
        }
    
    async def validate_notification_system(self):
        """Validate Notification System"""
        try:
            from .growth_notifications import GrowthNotificationSystem, NotificationType, AlertSeverity
            
            # Test notification system
            await self.run_test("Notification System Init", self._test_notifications_init)
            
            # Test alert creation
            await self.run_test("Alert Creation", self._test_alert_creation)
            
        except Exception as e:
            logger.error(f"Notification System validation failed: {str(e)}")
            raise
    
    async def _test_notifications_init(self) -> Dict[str, Any]:
        """Test notification system initialization"""
        from .growth_notifications import GrowthNotificationSystem
        
        notification_system = GrowthNotificationSystem()
        
        assert hasattr(notification_system, 'notification_channels')
        assert hasattr(notification_system, 'active_alerts')
        assert len(notification_system.notification_channels) > 0
        
        return {
            "notification_system_initialized": True,
            "channels_configured": len(notification_system.notification_channels)
        }
    
    async def _test_alert_creation(self) -> Dict[str, Any]:
        """Test alert creation"""
        from .growth_notifications import GrowthNotificationSystem, NotificationType, AlertSeverity
        
        notification_system = GrowthNotificationSystem()
        
        # Create test alert
        alert = await notification_system.create_alert(
            alert_type=NotificationType.PERFORMANCE_ALERT,
            severity=AlertSeverity.MEDIUM,
            title="Test Alert",
            message="This is a test alert for validation",
            source_agent="test_agent"
        )
        
        assert alert.alert_id is not None
        assert alert.title == "Test Alert"
        assert alert.alert_type == NotificationType.PERFORMANCE_ALERT
        
        return {
            "alert_created": True,
            "alert_id": alert.alert_id
        }
    
    async def validate_api_routes(self):
        """Validate API Routes"""
        try:
            from .api_routes import growth_router
            
            # Test router initialization  
            await self.run_test("API Router Init", self._test_api_router)
            
        except Exception as e:
            logger.error(f"API Routes validation failed: {str(e)}")
            raise
    
    async def _test_api_router(self) -> Dict[str, Any]:
        """Test API router initialization"""
        from .api_routes import growth_router
        
        # Check router configuration
        assert growth_router.prefix == "/api/growth"
        assert "Growth Engine" in growth_router.tags
        
        # Count routes
        route_count = len(growth_router.routes)
        assert route_count > 0, "No routes found in growth router"
        
        return {
            "router_initialized": True,
            "routes_count": route_count,
            "prefix": growth_router.prefix
        }
    
    async def validate_system_integration(self):
        """Validate overall system integration"""
        try:
            # Test main CLI
            await self.run_test("CLI Integration", self._test_cli_integration)
            
            # Test component interaction
            await self.run_test("Component Integration", self._test_component_integration)
            
        except Exception as e:
            logger.error(f"System Integration validation failed: {str(e)}")
            raise
    
    async def _test_cli_integration(self) -> Dict[str, Any]:
        """Test CLI integration"""
        from .main import GrowthEngineCLI
        
        cli = GrowthEngineCLI()
        
        assert hasattr(cli, 'growth_interface')
        assert hasattr(cli, 'scheduler')
        assert hasattr(cli, 'orchestrator')
        
        return {
            "cli_initialized": True,
            "components_available": True
        }
    
    async def _test_component_integration(self) -> Dict[str, Any]:
        """Test component integration"""
        from .growth_interface import GrowthInterface
        from .growth_scheduler import GrowthScheduler
        from .growth_metrics import growth_metrics_tracker
        from .growth_notifications import growth_notification_system
        
        # Test that components can be initialized together
        interface = GrowthInterface()
        scheduler = GrowthScheduler()
        
        # Test metrics tracker
        assert growth_metrics_tracker is not None
        
        # Test notification system
        assert growth_notification_system is not None
        
        return {
            "integration_successful": True,
            "components_initialized": 4
        }
    
    async def run_test(self, test_name: str, test_func, *args) -> ValidationResult:
        """Run individual test with error handling"""
        result = ValidationResult(test_name)
        start_time = datetime.utcnow()
        
        try:
            print(f"  🧪 {test_name}...", end=" ")
            
            if asyncio.iscoroutinefunction(test_func):
                result.details = await test_func(*args)
            else:
                result.details = test_func(*args)
            
            result.passed = True
            print("✅")
            self.passed_tests += 1
            
        except Exception as e:
            result.error = e
            result.passed = False
            print(f"❌ - {str(e)}")
            self.failed_tests += 1
            logger.error(f"Test {test_name} failed: {str(e)}")
            
        finally:
            end_time = datetime.utcnow()
            result.duration = (end_time - start_time).total_seconds()
            self.results.append(result)
            self.total_tests += 1
        
        return result
    
    def generate_validation_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate comprehensive validation summary"""
        
        # Categorize results
        passed_results = [r for r in self.results if r.passed]
        failed_results = [r for r in self.results if not r.passed]
        
        # Calculate statistics
        avg_test_duration = sum(r.duration for r in self.results) / len(self.results) if self.results else 0
        
        summary = {
            "validation_timestamp": datetime.utcnow().isoformat(),
            "total_duration": total_duration,
            "statistics": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                "average_test_duration": avg_test_duration
            },
            "passed_tests": [r.to_dict() for r in passed_results],
            "failed_tests": [r.to_dict() for r in failed_results],
            "system_health": {
                "overall_status": "HEALTHY" if self.failed_tests == 0 else "DEGRADED" if self.failed_tests < 5 else "CRITICAL",
                "critical_failures": len([r for r in failed_results if "critical" in r.test_name.lower()]),
                "component_status": self._analyze_component_health()
            }
        }
        
        return summary
    
    def _analyze_component_health(self) -> Dict[str, str]:
        """Analyze health of individual components"""
        components = {
            "data_models": "UNKNOWN",
            "growth_interface": "UNKNOWN", 
            "pipeline_orchestrator": "UNKNOWN",
            "bd_agents": "UNKNOWN",
            "marketing_agents": "UNKNOWN",
            "growth_metrics": "UNKNOWN",
            "growth_scheduler": "UNKNOWN",
            "notification_system": "UNKNOWN",
            "api_routes": "UNKNOWN",
            "system_integration": "UNKNOWN"
        }
        
        for result in self.results:
            for component in components.keys():
                if component.replace("_", " ").lower() in result.test_name.lower():
                    if result.passed:
                        if components[component] != "FAILED":
                            components[component] = "HEALTHY"
                    else:
                        components[component] = "FAILED"
        
        return components

async def main():
    """Main validation entry point"""
    try:
        validator = GrowthEngineValidator()
        summary = await validator.run_all_validations()
        
        # Save results to file
        with open('growth_engine_validation_report.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Validation report saved to: growth_engine_validation_report.json")
        
        # Exit with appropriate code
        if summary["statistics"]["failed_tests"] == 0:
            print("🎉 ALL VALIDATIONS PASSED! Growth Engine is ready for explosive growth!")
            sys.exit(0)
        else:
            print(f"⚠️  {summary['statistics']['failed_tests']} validations failed. Review and fix issues.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validation system failed: {str(e)}")
        logger.error(f"Validation system error: {traceback.format_exc()}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())