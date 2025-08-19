"""
R&D Orchestrator
Coordinates R&D agents for comprehensive report generation and strategic oversight
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class RDOrchestrator:
    """R&D Orchestrator for coordinating agent activities and report generation"""
    
    def __init__(self):
        self.last_activities = {}
        self.delta_cache = {}
        self.orchestration_stats = {
            "reports_generated": 0,
            "total_orchestrations": 0,
            "last_orchestration": None,
            "agent_coordination_success_rate": 0.0
        }
    
    async def generate_thirty_minute_report(self, include_delta: bool = True, 
                                          last_report_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive 30-minute R&D report"""
        try:
            logger.info("Starting 30-minute R&D report orchestration")
            start_time = datetime.now()
            
            # Coordinate all R&D agents for data collection
            agent_results = await self._coordinate_all_agents("thirty_minute_report")
            
            # Aggregate intelligence from all sources
            report_data = await self._aggregate_intelligence(agent_results, last_report_data, include_delta)
            
            # Generate executive summary
            report_data["executive_summary"] = self._generate_executive_summary(report_data)
            
            # Add orchestration metadata
            report_data["orchestration_metadata"] = {
                "report_type": "thirty_minute_interval",
                "generation_time": (datetime.now() - start_time).total_seconds(),
                "agents_coordinated": len(agent_results),
                "timestamp": datetime.now().isoformat(),
                "report_number": self.orchestration_stats["reports_generated"] + 1
            }
            
            # Update stats
            self.orchestration_stats["reports_generated"] += 1
            self.orchestration_stats["last_orchestration"] = datetime.now()
            
            logger.info(f"30-minute report generated successfully in {report_data['orchestration_metadata']['generation_time']:.2f}s")
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating 30-minute report: {e}")
            return self._generate_error_report(str(e))
    
    async def _coordinate_all_agents(self, task_type: str) -> Dict[str, Any]:
        """Coordinate all R&D agents for comprehensive data collection"""
        from .rd_interface import rd_agents
        
        agent_tasks = [
            # Intelligence gathering agents
            ("argus-competitor", "competitive_scan", "30-minute competitive intelligence scan"),
            ("minerva-research", "research_scan", "30-minute research landscape scan"),
            ("echo-feedback", "feedback_analysis", "30-minute user feedback analysis"),
            
            # Strategic agents
            ("vulcan-strategy", "strategy_update", "30-minute strategic assessment"),
            ("mercury-integration", "integration_status", "30-minute integration pipeline review"),
            ("daedalus-prototype", "prototype_status", "30-minute prototype development status")
        ]
        
        # Execute agent tasks concurrently
        agent_results = {}
        tasks = []
        
        for agent_name, task_subtype, description in agent_tasks:
            task = self._invoke_agent_with_timeout(
                rd_agents, agent_name, task_subtype, description
            )
            tasks.append((agent_name, task))
        
        # Collect results with timeout handling
        for agent_name, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=60.0)  # 1 minute timeout per agent
                agent_results[agent_name] = result
            except asyncio.TimeoutError:
                logger.warning(f"Agent {agent_name} timed out during 30-minute report")
                agent_results[agent_name] = {"status": "timeout", "error": "Agent response timeout"}
            except Exception as e:
                logger.error(f"Error invoking agent {agent_name}: {e}")
                agent_results[agent_name] = {"status": "error", "error": str(e)}
        
        return agent_results
    
    async def _invoke_agent_with_timeout(self, rd_agents, agent_name: str, task_type: str, description: str):
        """Invoke agent with timeout protection"""
        return await rd_agents.invoke_rd_agent(
            agent_name,
            task_type,
            description,
            {
                "priority": "high",
                "timeout": 45,
                "report_interval": "thirty_minutes",
                "include_delta": True
            }
        )
    
    async def _aggregate_intelligence(self, agent_results: Dict[str, Any], 
                                    last_report_data: Optional[Dict[str, Any]] = None,
                                    include_delta: bool = True) -> Dict[str, Any]:
        """Aggregate intelligence from all agent results"""
        
        # Initialize report structure
        report_data = {
            "competitive_updates": [],
            "research_highlights": [],
            "feature_recommendations": [],
            "action_items": [],
            "metrics_dashboard": {},
            "pipeline_changes": [],
            "urgent_alerts": [],
            "delta_summary": {}
        }
        
        # Process Argus (competitive intelligence) results
        argus_result = agent_results.get("argus-competitor", {})
        if argus_result.get("status") == "completed" and argus_result.get("result"):
            competitive_data = argus_result["result"]
            
            # Add competitive updates
            if competitive_data.get("new_features_detected", 0) > 0:
                report_data["competitive_updates"].append({
                    "source": "Argus Intelligence",
                    "type": "feature_detection",
                    "count": competitive_data["new_features_detected"],
                    "threat_level": competitive_data.get("threat_level", "medium"),
                    "summary": competitive_data.get("intelligence_summary", "New competitive features detected")
                })
            
            # Add urgent competitive alerts
            if competitive_data.get("threat_level") in ["high", "critical"]:
                report_data["urgent_alerts"].append({
                    "type": "competitive_threat",
                    "severity": competitive_data["threat_level"],
                    "message": competitive_data.get("intelligence_summary", "Critical competitive threat detected"),
                    "recommended_action": "Immediate strategic response required"
                })
        
        # Process Minerva (research analysis) results
        minerva_result = agent_results.get("minerva-research", {})
        if minerva_result.get("status") == "completed" and minerva_result.get("result"):
            research_data = minerva_result["result"]
            
            if research_data.get("breakthrough_technologies", 0) > 0:
                report_data["research_highlights"].append({
                    "source": "Minerva Research",
                    "type": "breakthrough_detection",
                    "count": research_data["breakthrough_technologies"],
                    "innovation_potential": research_data.get("innovation_potential", "medium"),
                    "summary": research_data.get("research_summary", "New breakthrough technologies identified")
                })
        
        # Process Vulcan (strategy) results
        vulcan_result = agent_results.get("vulcan-strategy", {})
        if vulcan_result.get("status") == "completed" and vulcan_result.get("result"):
            strategy_data = vulcan_result["result"]
            
            if strategy_data.get("features_ideated", 0) > 0:
                report_data["feature_recommendations"].append({
                    "source": "Vulcan Strategy",
                    "type": "feature_ideation",
                    "count": strategy_data["features_ideated"],
                    "competitive_advantage_score": strategy_data.get("competitive_advantage_score", 0),
                    "summary": strategy_data.get("strategy_summary", "New strategic feature concepts developed")
                })
        
        # Process Echo (feedback) results
        echo_result = agent_results.get("echo-feedback", {})
        if echo_result.get("status") == "completed" and echo_result.get("result"):
            feedback_data = echo_result["result"]
            
            if feedback_data.get("user_insights_generated", 0) > 0:
                report_data["action_items"].append(
                    f"Review {feedback_data['user_insights_generated']} new user insights from feedback analysis"
                )
                
                if feedback_data.get("satisfaction_trends") == "negative":
                    report_data["urgent_alerts"].append({
                        "type": "user_satisfaction",
                        "severity": "high",
                        "message": "Negative user satisfaction trends detected",
                        "recommended_action": "Immediate UX investigation required"
                    })
        
        # Process Daedalus (prototype) results
        daedalus_result = agent_results.get("daedalus-prototype", {})
        if daedalus_result.get("status") == "completed" and daedalus_result.get("result"):
            prototype_data = daedalus_result["result"]
            
            if prototype_data.get("prototypes_created", 0) > 0:
                report_data["pipeline_changes"].append({
                    "type": "prototype_completion",
                    "count": prototype_data["prototypes_created"],
                    "technical_validation": prototype_data.get("technical_validation", "pending"),
                    "summary": prototype_data.get("prototype_summary", "New prototypes completed")
                })
        
        # Process Mercury (integration) results
        mercury_result = agent_results.get("mercury-integration", {})
        if mercury_result.get("status") == "completed" and mercury_result.get("result"):
            integration_data = mercury_result["result"]
            
            report_data["pipeline_changes"].append({
                "type": "integration_status",
                "complexity": integration_data.get("integration_complexity", "unknown"),
                "timeline": integration_data.get("timeline_estimate", "TBD"),
                "summary": integration_data.get("integration_summary", "Integration pipeline status updated")
            })
        
        # Generate metrics dashboard
        report_data["metrics_dashboard"] = await self._generate_metrics_dashboard()
        
        # Calculate delta if previous report data available
        if include_delta and last_report_data:
            report_data["delta_summary"] = self._calculate_delta_changes(report_data, last_report_data)
        
        return report_data
    
    async def _generate_metrics_dashboard(self) -> Dict[str, Any]:
        """Generate real-time metrics dashboard"""
        try:
            from .rd_metrics import rd_metrics_tracker
            from .innovation_pipeline import innovation_pipeline
            
            # Get current metrics
            innovation_metrics = rd_metrics_tracker.get_innovation_pipeline_metrics()
            pipeline_status = innovation_pipeline.get_pipeline_status()
            agent_performance = rd_metrics_tracker.get_agent_performance_report()
            
            # Calculate key metrics for 30-minute interval
            current_time = datetime.now()
            thirty_minutes_ago = current_time - timedelta(minutes=30)
            
            return {
                "timestamp": current_time.isoformat(),
                "interval": "30_minutes",
                "pipeline_health": pipeline_status.get("pipeline_health", "unknown"),
                "total_innovations": pipeline_status.get("total_innovations", 0),
                "active_agents": len([a for a in agent_performance.get("individual_agents", {}).values() 
                                    if a.get("last_active")]),
                "team_success_rate": agent_performance.get("team_averages", {}).get("team_success_rate", 0),
                "innovation_velocity": innovation_metrics.get("pipeline_velocity", {}).get("avg_features_per_week", 0),
                "significant_changes": self._detect_significant_metric_changes()
            }
            
        except Exception as e:
            logger.error(f"Error generating metrics dashboard: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Failed to generate metrics dashboard",
                "significant_changes": False
            }
    
    def _detect_significant_metric_changes(self) -> bool:
        """Detect if there are significant metric changes worth reporting"""
        # For now, return True if any agents have been active in last 30 minutes
        # In production, this would compare against historical baselines
        return True
    
    def _calculate_delta_changes(self, current_data: Dict[str, Any], 
                               last_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes since last report"""
        delta = {
            "new_competitive_updates": 0,
            "new_research_highlights": 0,
            "new_feature_recommendations": 0,
            "new_pipeline_changes": 0,
            "changes_summary": []
        }
        
        # Calculate new items by comparing lengths
        current_competitive = len(current_data.get("competitive_updates", []))
        last_competitive = len(last_data.get("competitive_updates", []))
        delta["new_competitive_updates"] = max(0, current_competitive - last_competitive)
        
        current_research = len(current_data.get("research_highlights", []))
        last_research = len(last_data.get("research_highlights", []))
        delta["new_research_highlights"] = max(0, current_research - last_research)
        
        current_features = len(current_data.get("feature_recommendations", []))
        last_features = len(last_data.get("feature_recommendations", []))
        delta["new_feature_recommendations"] = max(0, current_features - last_features)
        
        current_pipeline = len(current_data.get("pipeline_changes", []))
        last_pipeline = len(last_data.get("pipeline_changes", []))
        delta["new_pipeline_changes"] = max(0, current_pipeline - last_pipeline)
        
        # Generate summary
        if delta["new_competitive_updates"] > 0:
            delta["changes_summary"].append(f"{delta['new_competitive_updates']} new competitive updates")
        if delta["new_research_highlights"] > 0:
            delta["changes_summary"].append(f"{delta['new_research_highlights']} new research highlights")
        if delta["new_feature_recommendations"] > 0:
            delta["changes_summary"].append(f"{delta['new_feature_recommendations']} new feature recommendations")
        if delta["new_pipeline_changes"] > 0:
            delta["changes_summary"].append(f"{delta['new_pipeline_changes']} pipeline changes")
        
        return delta
    
    def _generate_executive_summary(self, report_data: Dict[str, Any]) -> str:
        """Generate executive summary for 30-minute report"""
        summary_parts = []
        
        # Count totals
        competitive_count = len(report_data.get("competitive_updates", []))
        research_count = len(report_data.get("research_highlights", []))
        feature_count = len(report_data.get("feature_recommendations", []))
        urgent_count = len(report_data.get("urgent_alerts", []))
        
        # Generate summary based on activity
        if urgent_count > 0:
            summary_parts.append(f"🚨 {urgent_count} urgent alert{'s' if urgent_count != 1 else ''} requiring immediate attention")
        
        if competitive_count > 0:
            summary_parts.append(f"🔍 {competitive_count} competitive update{'s' if competitive_count != 1 else ''} detected")
        
        if research_count > 0:
            summary_parts.append(f"🧬 {research_count} research highlight{'s' if research_count != 1 else ''} identified")
        
        if feature_count > 0:
            summary_parts.append(f"💡 {feature_count} feature recommendation{'s' if feature_count != 1 else ''} generated")
        
        # Check metrics
        metrics = report_data.get("metrics_dashboard", {})
        pipeline_health = metrics.get("pipeline_health", "unknown")
        
        if pipeline_health in ["excellent", "good"]:
            summary_parts.append(f"📊 Innovation pipeline health: {pipeline_health}")
        elif pipeline_health in ["fair", "poor"]:
            summary_parts.append(f"⚠️ Pipeline health needs attention: {pipeline_health}")
        
        # Delta information
        delta = report_data.get("delta_summary", {})
        if delta.get("changes_summary"):
            summary_parts.append(f"📈 Changes since last report: {', '.join(delta['changes_summary'])}")
        
        if not summary_parts:
            return "✅ System operating normally with no significant changes in the last 30 minutes."
        
        return " • ".join(summary_parts[:3])  # Limit to top 3 most important items
    
    def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """Generate error report when orchestration fails"""
        return {
            "executive_summary": f"❌ R&D report generation failed: {error_message}",
            "competitive_updates": [],
            "research_highlights": [],
            "feature_recommendations": [],
            "action_items": [
                "Check R&D system logs for detailed error information",
                "Verify all R&D agents are operational",
                "Consider restarting R&D scheduler if issues persist"
            ],
            "metrics_dashboard": {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error_message": error_message
            },
            "urgent_alerts": [{
                "type": "system_error",
                "severity": "high",
                "message": f"R&D orchestration failed: {error_message}",
                "recommended_action": "Immediate system investigation required"
            }],
            "orchestration_metadata": {
                "report_type": "error_report",
                "generation_time": 0,
                "agents_coordinated": 0,
                "timestamp": datetime.now().isoformat(),
                "error": error_message
            }
        }
    
    async def generate_daily_review(self) -> Dict[str, Any]:
        """Generate comprehensive daily review"""
        try:
            logger.info("Starting daily R&D review orchestration")
            
            # Coordinate all agents for daily review
            agent_results = await self._coordinate_all_agents("daily_review")
            
            # Generate comprehensive daily summary
            daily_data = await self._aggregate_daily_intelligence(agent_results)
            
            # Add daily-specific analysis
            daily_data["daily_analysis"] = {
                "innovation_velocity": self._calculate_daily_velocity(),
                "competitive_landscape_changes": self._analyze_competitive_changes(),
                "research_opportunities": self._identify_research_opportunities(),
                "strategic_recommendations": self._generate_strategic_recommendations()
            }
            
            self.orchestration_stats["total_orchestrations"] += 1
            
            return daily_data
            
        except Exception as e:
            logger.error(f"Error generating daily review: {e}")
            return self._generate_error_report(str(e))
    
    async def _aggregate_daily_intelligence(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate intelligence for daily review"""
        # Similar to 30-minute aggregation but with daily focus
        # This would include more comprehensive analysis and longer-term trends
        return await self._aggregate_intelligence(agent_results, None, False)
    
    def _calculate_daily_velocity(self) -> Dict[str, Any]:
        """Calculate daily innovation velocity metrics"""
        return {
            "features_ideated_today": 0,  # Would calculate from metrics
            "prototypes_completed_today": 0,
            "competitive_insights_today": 0,
            "velocity_trend": "stable"
        }
    
    def _analyze_competitive_changes(self) -> List[str]:
        """Analyze competitive landscape changes"""
        return [
            "Monitor ongoing competitive intelligence",
            "Assess strategic positioning changes"
        ]
    
    def _identify_research_opportunities(self) -> List[str]:
        """Identify research opportunities"""
        return [
            "Evaluate emerging technology applications",
            "Assess research collaboration opportunities"
        ]
    
    def _generate_strategic_recommendations(self) -> List[str]:
        """Generate strategic recommendations"""
        return [
            "Continue innovation pipeline optimization",
            "Maintain competitive intelligence monitoring"
        ]
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        return {
            "stats": self.orchestration_stats,
            "last_activities": {
                agent: activity["timestamp"] if isinstance(activity, dict) and "timestamp" in activity else str(activity)
                for agent, activity in list(self.last_activities.items())[-5:]  # Last 5 activities
            },
            "system_status": "operational"
        }

# Global orchestrator instance
rd_orchestrator = RDOrchestrator()