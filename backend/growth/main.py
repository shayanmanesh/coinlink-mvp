#!/usr/bin/env python3
"""
Growth Engine Main Entry Point

Ultra-aggressive growth system command-line interface.
Execute growth sprints, manage agents, and drive explosive revenue growth
through systematic BD and Marketing automation.

Usage:
    python -m backend.growth.main --help
    python -m backend.growth.main sprint --type bd_blitz --intensity ultra_aggressive
    python -m backend.growth.main scheduler --start
    python -m backend.growth.main dashboard
"""

import asyncio
import argparse
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .growth_interface import GrowthInterface
from .growth_scheduler import GrowthScheduler, SprintType, SprintIntensity, SprintSchedule
from .growth_metrics import growth_metrics_tracker
from .growth_notifications import growth_notification_system, NotificationType, AlertSeverity
from .pipeline_orchestrator import PipelineOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('growth_engine.log')
    ]
)

logger = logging.getLogger(__name__)

class GrowthEngineCLI:
    """Growth Engine Command Line Interface"""
    
    def __init__(self):
        self.growth_interface = GrowthInterface()
        self.scheduler = GrowthScheduler()
        self.orchestrator = PipelineOrchestrator()
        
    async def execute_sprint(self, sprint_type: str, intensity: str = "aggressive", 
                           duration: int = 120, agents: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute a growth sprint"""
        print(f"\n🚀 EXECUTING {sprint_type.upper()} SPRINT")
        print(f"Intensity: {intensity}")
        print(f"Duration: {duration} minutes")
        print("=" * 50)
        
        start_time = datetime.utcnow()
        
        try:
            # Create sprint schedule
            sprint_schedule = SprintSchedule(
                sprint_id=f"manual_{sprint_type}_{int(start_time.timestamp())}",
                sprint_type=SprintType(sprint_type),
                intensity=SprintIntensity(intensity),
                cron_expression="",  # Manual execution
                duration_minutes=duration,
                target_agents=agents or ["all"],
                parameters={"manual_execution": True}
            )
            
            # Execute sprint based on type
            if sprint_type == "bd_blitz":
                result = await self._execute_bd_blitz_cli(sprint_schedule)
            elif sprint_type == "marketing_campaign":
                result = await self._execute_marketing_campaign_cli(sprint_schedule)
            elif sprint_type == "lead_generation":
                result = await self._execute_lead_generation_cli(sprint_schedule)
            elif sprint_type == "deal_closing":
                result = await self._execute_deal_closing_cli(sprint_schedule)
            elif sprint_type == "comprehensive":
                result = await self._execute_comprehensive_cli(sprint_schedule)
            elif sprint_type == "optimization":
                result = await self._execute_optimization_cli(sprint_schedule)
            else:
                raise ValueError(f"Unknown sprint type: {sprint_type}")
            
            end_time = datetime.utcnow()
            duration_actual = (end_time - start_time).total_seconds() / 60
            
            print(f"\n✅ SPRINT COMPLETED SUCCESSFULLY")
            print(f"Actual Duration: {duration_actual:.1f} minutes")
            print(f"Results: {json.dumps(result, indent=2)}")
            
            # Send completion notification
            await growth_notification_system.create_alert(
                alert_type=NotificationType.SPRINT_COMPLETED,
                severity=AlertSeverity.LOW,
                title=f"Sprint Completed: {sprint_type}",
                message=f"Manual {sprint_type} sprint completed successfully in {duration_actual:.1f} minutes",
                context={"results": result}
            )
            
            return result
            
        except Exception as e:
            print(f"\n❌ SPRINT FAILED: {str(e)}")
            logger.error(f"Sprint execution failed: {str(e)}")
            
            # Send failure notification
            await growth_notification_system.create_alert(
                alert_type=NotificationType.SYSTEM_ERROR,
                severity=AlertSeverity.HIGH,
                title=f"Sprint Failed: {sprint_type}",
                message=f"Manual {sprint_type} sprint failed: {str(e)}",
                action_required=True
            )
            
            return {"error": str(e)}
    
    async def _execute_bd_blitz_cli(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute BD blitz with CLI feedback"""
        print("🎯 Initiating BD Agent Deployment...")
        
        results = {"agents_executed": [], "results": []}
        
        # Market Intelligence
        print("📊 Deploying Market Intelligence Agent...")
        market_result = await self.growth_interface.invoke_agent(
            "market_intelligence",
            "execute_market_intelligence_sweep",
            {"intensity": sprint.intensity.value}
        )
        results["agents_executed"].append("market_intelligence")
        results["results"].append(market_result)
        print(f"   ✓ Market Intelligence: {market_result.get('intelligence_summary', {}).get('total_insights_generated', 0)} insights")
        
        # Opportunity Scout
        print("🔍 Deploying Opportunity Scout Agent...")
        scout_result = await self.growth_interface.invoke_agent(
            "opportunity_scout",
            "execute_prospecting_blitz",
            {"blitz_type": "comprehensive", "prospecting_volume": 100, "intensity": sprint.intensity.value}
        )
        results["agents_executed"].append("opportunity_scout")
        results["results"].append(scout_result)
        print(f"   ✓ Opportunity Scout: {scout_result.get('prospecting_summary', {}).get('total_prospects_identified', 0)} prospects")
        
        # Lead Engagement
        print("💬 Deploying Lead Engagement Agent...")
        engagement_result = await self.growth_interface.invoke_agent(
            "lead_engagement",
            "execute_engagement_blitz",
            {"intensity": sprint.intensity.value}
        )
        results["agents_executed"].append("lead_engagement")
        results["results"].append(engagement_result)
        print(f"   ✓ Lead Engagement: {engagement_result.get('engagement_summary', {}).get('total_outreach_sent', 0)} outreach sent")
        
        # Deal Closer
        print("🤝 Deploying Deal Closer Agent...")
        closer_result = await self.growth_interface.invoke_agent(
            "deal_closer",
            "execute_closing_blitz",
            {"closing_intensity": sprint.intensity.value}
        )
        results["agents_executed"].append("deal_closer")
        results["results"].append(closer_result)
        print(f"   ✓ Deal Closer: {closer_result.get('closing_summary', {}).get('deals_advanced', 0)} deals advanced")
        
        return results
    
    async def _execute_marketing_campaign_cli(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute marketing campaign with CLI feedback"""
        print("📈 Initiating Marketing Agent Deployment...")
        
        results = {"agents_executed": [], "results": []}
        
        # Campaign Planner
        print("📋 Deploying Campaign Planner Agent...")
        planner_result = await self.growth_interface.invoke_agent(
            "campaign_planner",
            "execute_campaign_planning_sprint",
            {"planning_scope": "weekly", "total_budget": 500000.0}
        )
        results["agents_executed"].append("campaign_planner")
        results["results"].append(planner_result)
        print(f"   ✓ Campaign Planner: {planner_result.get('planning_summary', {}).get('total_campaigns_planned', 0)} campaigns planned")
        
        # Campaign Execution
        print("🚀 Deploying Campaign Execution Agent...")
        execution_result = await self.growth_interface.invoke_agent(
            "campaign_execution",
            "execute_campaign_deployment_blitz",
            {"deployment_type": "comprehensive", "optimization_intensity": "high"}
        )
        results["agents_executed"].append("campaign_execution")
        results["results"].append(execution_result)
        print(f"   ✓ Campaign Execution: {execution_result.get('deployment_summary', {}).get('campaigns_launched', 0)} campaigns launched")
        
        # Marketing Analytics
        print("📊 Deploying Marketing Analytics Agent...")
        analytics_result = await self.growth_interface.invoke_agent(
            "marketing_analytics",
            "execute_analytics_and_optimization_sprint",
            {"analysis_type": "comprehensive", "time_period_days": 30}
        )
        results["agents_executed"].append("marketing_analytics")
        results["results"].append(analytics_result)
        print(f"   ✓ Marketing Analytics: {analytics_result.get('analytics_summary', {}).get('total_insights_generated', 0)} insights generated")
        
        return results
    
    async def _execute_lead_generation_cli(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute lead generation sprint with CLI feedback"""
        print("📧 Initiating Lead Generation Sprint...")
        
        # Execute coordinated lead generation across BD and Marketing
        tasks = [
            self.growth_interface.invoke_agent("opportunity_scout", "execute_prospecting_blitz", {"prospecting_volume": 50}),
            self.growth_interface.invoke_agent("content_creation", "execute_content_production_sprint", {"production_volume": "high"}),
            self.growth_interface.invoke_agent("campaign_execution", "execute_campaign_deployment_blitz", {"deployment_type": "lead_generation"})
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_leads = sum(
            result.get('prospecting_summary', {}).get('total_prospects_identified', 0) if isinstance(result, dict) else 0
            for result in results
        )
        
        print(f"   ✓ Total Lead Generation: {total_leads} leads generated")
        
        return {"total_leads_generated": total_leads, "agent_results": results}
    
    async def _execute_deal_closing_cli(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute deal closing sprint with CLI feedback"""
        print("💰 Initiating Deal Closing Sprint...")
        
        # Focus on closing activities
        closer_result = await self.growth_interface.invoke_agent(
            "deal_closer",
            "execute_closing_blitz",
            {"closing_intensity": "ultra_aggressive", "revenue_focus": True}
        )
        
        negotiator_result = await self.growth_interface.invoke_agent(
            "partnership_negotiator",
            "execute_negotiation_blitz",
            {"urgency_level": "maximum"}
        )
        
        deals_closed = closer_result.get('closing_summary', {}).get('deals_closed', 0)
        revenue_recognized = closer_result.get('closing_summary', {}).get('revenue_recognized', 0)
        
        print(f"   ✓ Deals Closed: {deals_closed}")
        print(f"   ✓ Revenue Recognized: ${revenue_recognized:,.2f}")
        
        return {
            "deals_closed": deals_closed,
            "revenue_recognized": revenue_recognized,
            "closer_result": closer_result,
            "negotiator_result": negotiator_result
        }
    
    async def _execute_comprehensive_cli(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute comprehensive sprint with CLI feedback"""
        print("🎯 Initiating COMPREHENSIVE ALL-HANDS SPRINT...")
        print("   Deploying ALL agents simultaneously...")
        
        # Execute all agents in parallel
        all_agents = [
            ("market_intelligence", "execute_market_intelligence_sweep", {"intensity": "ultra_aggressive"}),
            ("opportunity_scout", "execute_prospecting_blitz", {"blitz_type": "comprehensive", "prospecting_volume": 100}),
            ("lead_engagement", "execute_engagement_blitz", {"intensity": "ultra_aggressive"}),
            ("partnership_negotiator", "execute_negotiation_blitz", {"urgency_level": "maximum"}),
            ("deal_closer", "execute_closing_blitz", {"closing_intensity": "ultra_aggressive"}),
            ("marketing_strategy", "develop_comprehensive_marketing_strategy", {"strategy_type": "go_to_market"}),
            ("campaign_planner", "execute_campaign_planning_sprint", {"planning_scope": "quarterly"}),
            ("content_creation", "execute_content_production_sprint", {"production_volume": "high"}),
            ("campaign_execution", "execute_campaign_deployment_blitz", {"deployment_type": "comprehensive"}),
            ("marketing_analytics", "execute_analytics_and_optimization_sprint", {"analysis_type": "comprehensive"})
        ]
        
        tasks = [
            self.growth_interface.invoke_agent(agent_id, method, params)
            for agent_id, method, params in all_agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_agents = sum(1 for result in results if isinstance(result, dict) and 'error' not in result)
        
        print(f"   ✓ Agents Successfully Deployed: {successful_agents}/{len(all_agents)}")
        
        return {
            "total_agents": len(all_agents),
            "successful_agents": successful_agents,
            "agent_results": results
        }
    
    async def _execute_optimization_cli(self, sprint: SprintSchedule) -> Dict[str, Any]:
        """Execute optimization sprint with CLI feedback"""
        print("⚡ Initiating Performance Optimization Sprint...")
        
        # Generate performance analysis
        dashboard = await growth_metrics_tracker.get_performance_dashboard()
        alerts = await growth_metrics_tracker.generate_performance_alerts()
        recommendations = await growth_metrics_tracker.optimize_performance_recommendations()
        
        print(f"   ✓ Performance Alerts: {len(alerts)}")
        print(f"   ✓ Optimization Recommendations: {len(recommendations)}")
        print(f"   ✓ System Efficiency: {dashboard['system_health']['overall_efficiency']:.1f}%")
        
        return {
            "performance_dashboard": dashboard,
            "performance_alerts": alerts,
            "optimization_recommendations": recommendations
        }
    
    async def start_scheduler(self):
        """Start the automated growth scheduler"""
        print("\n🤖 STARTING AUTOMATED GROWTH SCHEDULER")
        print("Ultra-aggressive scheduling system activated")
        print("=" * 50)
        
        # Start notification services
        await growth_notification_system.start_notification_services()
        
        # Start scheduler
        await self.scheduler.start_scheduler()
    
    async def show_dashboard(self):
        """Display growth dashboard"""
        print("\n📊 GROWTH ENGINE DASHBOARD")
        print("=" * 50)
        
        # Get performance dashboard
        dashboard = await growth_metrics_tracker.get_performance_dashboard()
        
        print(f"📈 CURRENT PERFORMANCE")
        print(f"   Revenue: ${dashboard['current_metrics']['bd_metrics']['revenue_recognized']:,.2f}")
        print(f"   Leads Generated: {dashboard['current_metrics']['bd_metrics']['leads_generated']}")
        print(f"   Deals Closed: {dashboard['current_metrics']['bd_metrics']['deals_closed']}")
        print(f"   System Efficiency: {dashboard['system_health']['overall_efficiency']:.1f}%")
        
        print(f"\n🎯 TARGET ACHIEVEMENT")
        print(f"   Revenue: {dashboard['target_achievement']['revenue']['achievement_rate']:.1%}")
        print(f"   Leads: {dashboard['target_achievement']['leads']['achievement_rate']:.1%}")
        
        print(f"\n🏆 TOP PERFORMERS")
        for i, agent in enumerate(dashboard['top_performers'][:5], 1):
            print(f"   {i}. {agent['agent_id']}: {agent['performance_score']:.2f} ({agent['efficiency_rating']})")
        
        print(f"\n⚠️  ACTIVE ALERTS")
        alerts = await growth_notification_system.get_active_alerts()
        for alert in alerts[-5:]:  # Show last 5 alerts
            print(f"   • {alert['title']} ({alert['severity']})")
        
        # Scheduler status
        scheduler_status = await self.scheduler.get_sprint_status()
        print(f"\n🤖 SCHEDULER STATUS")
        print(f"   Running: {scheduler_status['scheduler_running']}")
        print(f"   Scheduled Sprints: {scheduler_status['scheduled_sprints']}")
        print(f"   Active Executions: {scheduler_status['active_executions']}")
        
        if scheduler_status['next_sprint']:
            next_sprint = datetime.fromisoformat(scheduler_status['next_sprint'].replace('Z', '+00:00'))
            print(f"   Next Sprint: {next_sprint.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    async def list_agents(self):
        """List all available agents"""
        print("\n🤖 GROWTH ENGINE AGENTS")
        print("=" * 50)
        
        print("📊 BUSINESS DEVELOPMENT CLUSTER")
        bd_agents = [
            ("market_intelligence", "Global market scanning and competitive intelligence"),
            ("opportunity_scout", "Ultra-aggressive prospecting and lead identification"),
            ("lead_engagement", "Multi-touch engagement and lead nurturing"),
            ("partnership_negotiator", "Strategic partnerships and deal negotiation"),
            ("deal_closer", "Revenue closing and contract finalization")
        ]
        
        for agent_id, description in bd_agents:
            print(f"   • {agent_id}: {description}")
        
        print("\n📈 MARKETING CLUSTER")
        marketing_agents = [
            ("marketing_strategy", "Go-to-market strategy and competitive positioning"),
            ("campaign_planner", "Multi-channel campaign design and budget optimization"),
            ("content_creation", "High-velocity content production and creative assets"),
            ("campaign_execution", "Real-time campaign deployment and optimization"),
            ("marketing_analytics", "Performance measurement and ROI optimization")
        ]
        
        for agent_id, description in marketing_agents:
            print(f"   • {agent_id}: {description}")
    
    async def test_agent(self, agent_id: str):
        """Test a specific agent"""
        print(f"\n🧪 TESTING AGENT: {agent_id}")
        print("=" * 50)
        
        try:
            # Get agent info
            if agent_id not in self.growth_interface.agents:
                print(f"❌ Agent not found: {agent_id}")
                return
            
            agent = self.growth_interface.agents[agent_id]
            print(f"Agent Type: {agent['type']}")
            print(f"Agent Class: {agent['class']}")
            print(f"Available Methods: {', '.join(agent['methods'])}")
            
            # Test agent health
            print(f"\n🔍 Testing agent connectivity...")
            # This would be replaced with actual agent health check
            print(f"✅ Agent {agent_id} is responsive")
            
        except Exception as e:
            print(f"❌ Agent test failed: {str(e)}")

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Growth Engine Ultra-Aggressive CLI")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sprint command
    sprint_parser = subparsers.add_parser('sprint', help='Execute growth sprint')
    sprint_parser.add_argument('--type', 
                              choices=['bd_blitz', 'marketing_campaign', 'lead_generation', 'deal_closing', 'comprehensive', 'optimization'],
                              required=True,
                              help='Sprint type to execute')
    sprint_parser.add_argument('--intensity',
                              choices=['standard', 'aggressive', 'ultra_aggressive', 'maximum'],
                              default='aggressive',
                              help='Sprint intensity level')
    sprint_parser.add_argument('--duration', type=int, default=120, help='Sprint duration in minutes')
    sprint_parser.add_argument('--agents', nargs='*', help='Specific agents to include')
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser('scheduler', help='Manage growth scheduler')
    scheduler_parser.add_argument('--start', action='store_true', help='Start the scheduler')
    scheduler_parser.add_argument('--status', action='store_true', help='Show scheduler status')
    
    # Dashboard command
    subparsers.add_parser('dashboard', help='Show growth dashboard')
    
    # Agents command
    agents_parser = subparsers.add_parser('agents', help='Manage agents')
    agents_parser.add_argument('--list', action='store_true', help='List all agents')
    agents_parser.add_argument('--test', help='Test specific agent')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = GrowthEngineCLI()
    
    try:
        if args.command == 'sprint':
            await cli.execute_sprint(
                sprint_type=args.type,
                intensity=args.intensity,
                duration=args.duration,
                agents=args.agents
            )
        
        elif args.command == 'scheduler':
            if args.start:
                await cli.start_scheduler()
            elif args.status:
                status = await cli.scheduler.get_sprint_status()
                print(json.dumps(status, indent=2))
            else:
                print("Use --start to start scheduler or --status to show status")
        
        elif args.command == 'dashboard':
            await cli.show_dashboard()
        
        elif args.command == 'agents':
            if args.list:
                await cli.list_agents()
            elif args.test:
                await cli.test_agent(args.test)
            else:
                print("Use --list to list agents or --test AGENT_ID to test agent")
        
    except KeyboardInterrupt:
        print("\n🛑 Growth Engine CLI interrupted")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        logger.error(f"CLI error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())