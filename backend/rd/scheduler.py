"""
R&D Automated Scheduler
30-minute interval reporting and automated R&D operations
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)

class RDScheduler:
    """Automated scheduler for R&D operations and reporting"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.report_interval_minutes = 30
        self.quiet_hours_start = 22  # 10 PM
        self.quiet_hours_end = 7    # 7 AM
        self.enable_quiet_hours = True
        
        # Scheduling configuration
        self.schedule_config = {
            "thirty_minute_reports": True,
            "competitive_monitoring": True,
            "innovation_cycle_tracking": True,
            "metrics_collection": True,
            "priority_threshold": "medium"
        }
        
        # Tracking for delta reporting
        self.last_report_data = {}
        self.report_count = 0
        
        # Add event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
    
    def _job_executed(self, event):
        """Handle successful job execution"""
        logger.info(f"Job {event.job_id} executed successfully")
    
    def _job_error(self, event):
        """Handle job execution errors"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    
    async def start_scheduler(self):
        """Start the automated scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Add 30-minute reporting job
            self.scheduler.add_job(
                self._run_thirty_minute_report,
                IntervalTrigger(minutes=self.report_interval_minutes),
                id="thirty_minute_reports",
                name="30-Minute R&D Reports",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5 minutes grace period
            )
            
            # Add continuous competitive monitoring (every 10 minutes)
            self.scheduler.add_job(
                self._run_competitive_monitoring,
                IntervalTrigger(minutes=10),
                id="competitive_monitoring",
                name="Competitive Intelligence Monitoring",
                max_instances=1,
                coalesce=True
            )
            
            # Add metrics collection (every 5 minutes)
            self.scheduler.add_job(
                self._collect_metrics,
                IntervalTrigger(minutes=5),
                id="metrics_collection",
                name="R&D Metrics Collection",
                max_instances=1,
                coalesce=True
            )
            
            # Add daily innovation cycle review (9 AM daily)
            self.scheduler.add_job(
                self._daily_innovation_review,
                CronTrigger(hour=9, minute=0),
                id="daily_innovation_review",
                name="Daily Innovation Cycle Review",
                max_instances=1
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("R&D Scheduler started successfully")
            logger.info(f"30-minute reports will be sent to shayan.bozorgmanesh@gmail.com")
            
            # Send initial status report
            await self._send_scheduler_status_report("started")
            
        except Exception as e:
            logger.error(f"Failed to start R&D scheduler: {e}")
            raise
    
    async def stop_scheduler(self):
        """Stop the automated scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("R&D Scheduler stopped successfully")
            
            # Send shutdown notification
            await self._send_scheduler_status_report("stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop R&D scheduler: {e}")
            raise
    
    async def trigger_immediate_report(self):
        """Trigger an immediate 30-minute report"""
        logger.info("Triggering immediate 30-minute report")
        await self._run_thirty_minute_report()
    
    def update_schedule_config(self, new_config: Dict[str, Any]):
        """Update scheduler configuration"""
        self.schedule_config.update(new_config)
        
        # Update report interval if changed
        if "report_interval_minutes" in new_config:
            self.report_interval_minutes = new_config["report_interval_minutes"]
            
            # Reschedule 30-minute reports with new interval
            if self.is_running:
                try:
                    self.scheduler.remove_job("thirty_minute_reports")
                    self.scheduler.add_job(
                        self._run_thirty_minute_report,
                        IntervalTrigger(minutes=self.report_interval_minutes),
                        id="thirty_minute_reports",
                        name="30-Minute R&D Reports",
                        max_instances=1,
                        coalesce=True
                    )
                    logger.info(f"Updated report interval to {self.report_interval_minutes} minutes")
                except Exception as e:
                    logger.error(f"Failed to update report interval: {e}")
        
        logger.info(f"Scheduler configuration updated: {new_config}")
    
    async def _run_thirty_minute_report(self):
        """Execute 30-minute reporting cycle"""
        try:
            # Check quiet hours
            if self.enable_quiet_hours and self._is_quiet_hours():
                logger.info("Skipping 30-minute report due to quiet hours")
                return
            
            logger.info("Starting 30-minute R&D report generation")
            self.report_count += 1
            
            # Import required modules
            from .rd_orchestrator import rd_orchestrator
            from .notification_system import email_notifier
            
            # Generate comprehensive 30-minute report
            report_data = await rd_orchestrator.generate_thirty_minute_report(
                include_delta=True,
                last_report_data=self.last_report_data
            )
            
            # Send email report if there's meaningful content
            if self._has_meaningful_content(report_data):
                success = await email_notifier.send_thirty_minute_report(report_data)
                
                if success:
                    logger.info(f"30-minute report #{self.report_count} sent successfully")
                    self.last_report_data = report_data.copy()
                else:
                    logger.error("Failed to send 30-minute report")
            else:
                logger.info("No significant changes detected, skipping report")
                
        except Exception as e:
            logger.error(f"Error in 30-minute report cycle: {e}")
            
            # Send error notification
            try:
                from .notification_system import email_notifier
                await email_notifier.send_urgent_competitive_alert({
                    "title": "R&D Scheduler Error",
                    "competitor": "System",
                    "description": f"30-minute report generation failed: {str(e)}",
                    "threat_level": "High",
                    "recommendations": ["Check R&D system logs", "Restart scheduler if needed"]
                })
            except Exception as notification_error:
                logger.error(f"Failed to send error notification: {notification_error}")
    
    async def _run_competitive_monitoring(self):
        """Execute competitive intelligence monitoring"""
        try:
            logger.debug("Running competitive intelligence monitoring")
            
            from .rd_interface import rd_agents
            
            # Run Argus competitive analysis
            result = await rd_agents.invoke_rd_agent(
                "argus-competitor",
                "continuous_monitoring",
                "10-minute competitive intelligence scan",
                {"priority_threshold": self.schedule_config.get("priority_threshold", "medium")}
            )
            
            # Check for critical competitive threats
            if result.get("status") == "completed" and result.get("result"):
                threat_level = result["result"].get("threat_level", "low")
                if threat_level in ["high", "critical"]:
                    # Send immediate alert
                    from .notification_system import email_notifier
                    await email_notifier.send_urgent_competitive_alert({
                        "title": "Critical Competitive Threat Detected",
                        "competitor": result["result"].get("competitor", "Unknown"),
                        "description": result["result"].get("intelligence_summary", ""),
                        "threat_level": threat_level.title(),
                        "recommendations": result["result"].get("recommendations", [])
                    })
                    
        except Exception as e:
            logger.error(f"Error in competitive monitoring: {e}")
    
    async def _collect_metrics(self):
        """Collect R&D metrics for tracking"""
        try:
            logger.debug("Collecting R&D metrics")
            
            from .rd_metrics import rd_metrics_tracker
            
            # Take daily snapshot
            rd_metrics_tracker.take_daily_snapshot()
            
            # Update real-time metrics
            rd_metrics_tracker.real_time_metrics["last_collection"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def _daily_innovation_review(self):
        """Execute daily innovation cycle review"""
        try:
            logger.info("Running daily innovation cycle review")
            
            from .rd_interface import rd_agents
            from .notification_system import email_notifier
            
            # Run Apollo daily review
            result = await rd_agents.invoke_rd_agent(
                "apollo-rd-orchestrator",
                "daily_review",
                "Daily innovation cycle review and planning",
                {"review_type": "comprehensive", "planning": True}
            )
            
            # Generate and send daily summary report
            if result.get("status") == "completed":
                daily_summary = {
                    "executive_summary": f"Daily innovation review completed. {result['result'].get('summary', '')}",
                    "competitive_updates": result["result"].get("competitive_updates", []),
                    "research_highlights": result["result"].get("research_highlights", []),
                    "feature_recommendations": result["result"].get("feature_recommendations", []),
                    "action_items": result["result"].get("action_items", []),
                    "metrics_dashboard": result["result"].get("metrics", {})
                }
                
                await email_notifier.send_weekly_innovation_report(daily_summary)
                logger.info("Daily innovation summary sent")
                
        except Exception as e:
            logger.error(f"Error in daily innovation review: {e}")
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        if not self.enable_quiet_hours:
            return False
        
        current_hour = datetime.now().hour
        
        if self.quiet_hours_start < self.quiet_hours_end:
            # Normal case: quiet hours within same day (e.g., 22-7)
            return self.quiet_hours_start <= current_hour <= self.quiet_hours_end
        else:
            # Spanning midnight: quiet hours across day boundary
            return current_hour >= self.quiet_hours_start or current_hour <= self.quiet_hours_end
    
    def _has_meaningful_content(self, report_data: Dict[str, Any]) -> bool:
        """Check if report contains meaningful content worth sending"""
        # Check for new competitive updates
        if report_data.get("competitive_updates") and len(report_data["competitive_updates"]) > 0:
            return True
        
        # Check for new research highlights
        if report_data.get("research_highlights") and len(report_data["research_highlights"]) > 0:
            return True
        
        # Check for new feature recommendations
        if report_data.get("feature_recommendations") and len(report_data["feature_recommendations"]) > 0:
            return True
        
        # Check for urgent action items
        if report_data.get("action_items") and len(report_data["action_items"]) > 0:
            return True
        
        # Check for significant metric changes
        metrics = report_data.get("metrics_dashboard", {})
        if metrics.get("significant_changes", False):
            return True
        
        # Check for pipeline movement
        if report_data.get("pipeline_changes") and len(report_data["pipeline_changes"]) > 0:
            return True
        
        return False
    
    async def _send_scheduler_status_report(self, status: str):
        """Send scheduler status notification"""
        try:
            from .notification_system import email_notifier
            
            status_data = {
                "title": f"R&D Scheduler {status.title()}",
                "competitor": "System",
                "description": f"R&D automated scheduler has been {status}. " +
                             f"30-minute reports {'are now active' if status == 'started' else 'have been paused'}.",
                "threat_level": "Medium",
                "recommendations": [
                    f"30-minute reports will be sent to shayan.bozorgmanesh@gmail.com",
                    f"Competitive monitoring is {'active' if status == 'started' else 'inactive'}",
                    f"Next scheduled report: {(datetime.now() + timedelta(minutes=self.report_interval_minutes)).strftime('%H:%M')}"
                ]
            }
            
            await email_notifier.send_urgent_competitive_alert(status_data)
            
        except Exception as e:
            logger.error(f"Failed to send scheduler status report: {e}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        
        return {
            "is_running": self.is_running,
            "report_interval_minutes": self.report_interval_minutes,
            "reports_sent": self.report_count,
            "quiet_hours_enabled": self.enable_quiet_hours,
            "quiet_hours": f"{self.quiet_hours_start:02d}:00 - {self.quiet_hours_end:02d}:00",
            "current_time": datetime.now().isoformat(),
            "in_quiet_hours": self._is_quiet_hours(),
            "scheduled_jobs": jobs,
            "configuration": self.schedule_config
        }

# Global scheduler instance
rd_scheduler = RDScheduler()