"""
Growth Notifications System

Ultra-responsive notification system for growth alerts, performance monitoring,
and real-time updates. Supports email, webhooks, and real-time dashboard alerts
for critical growth metrics and opportunities.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import aiohttp
import os

from .growth_metrics import growth_metrics_tracker, MetricType, AgentPerformance
from .data_models import GrowthEvent, Lead, Opportunity, Deal

class NotificationType(Enum):
    PERFORMANCE_ALERT = "performance_alert"
    OPPORTUNITY_CREATED = "opportunity_created"
    DEAL_CLOSED = "deal_closed"
    TARGET_ACHIEVED = "target_achieved" 
    TARGET_MISSED = "target_missed"
    SYSTEM_ERROR = "system_error"
    SPRINT_COMPLETED = "sprint_completed"
    MILESTONE_REACHED = "milestone_reached"
    CRITICAL_ALERT = "critical_alert"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"

@dataclass
class NotificationChannel:
    """Notification delivery channel configuration"""
    channel_id: str
    channel_type: str  # email, webhook, slack, discord
    config: Dict[str, Any]
    is_active: bool = True
    alert_types: List[NotificationType] = field(default_factory=list)
    min_severity: AlertSeverity = AlertSeverity.LOW

@dataclass
class GrowthAlert:
    """Growth system alert"""
    alert_id: str
    alert_type: NotificationType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source_agent: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    action_required: bool = False
    notification_sent: bool = False
    acknowledgement_required: bool = False
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "source_agent": self.source_agent,
            "context": self.context,
            "action_required": self.action_required,
            "notification_sent": self.notification_sent
        }

class GrowthNotificationSystem:
    """Ultra-responsive growth notification and alert system"""
    
    def __init__(self):
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.active_alerts: Dict[str, GrowthAlert] = {}
        self.alert_history: List[GrowthAlert] = []
        self.email_queue: asyncio.Queue = asyncio.Queue()
        self.webhook_queue: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger(__name__)
        
        # Initialize default channels
        self._initialize_default_channels()
        
        # Email configuration
        self.email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "email_user": os.getenv("EMAIL_USER", ""),
            "email_password": os.getenv("EMAIL_PASSWORD", ""),
            "from_email": os.getenv("FROM_EMAIL", "growth@coinlink.com")
        }
        
        # Webhook configuration
        self.webhook_config = {
            "slack_webhook": os.getenv("SLACK_WEBHOOK_URL", ""),
            "discord_webhook": os.getenv("DISCORD_WEBHOOK_URL", ""),
            "general_webhook": os.getenv("GROWTH_WEBHOOK_URL", "")
        }
    
    def _initialize_default_channels(self):
        """Initialize default notification channels"""
        
        # Email channel for critical alerts
        self.notification_channels["email_critical"] = NotificationChannel(
            channel_id="email_critical",
            channel_type="email",
            config={
                "recipients": ["shayan.bozorgmanesh@gmail.com"],
                "subject_prefix": "🚨 CRITICAL GROWTH ALERT",
                "template": "critical_alert"
            },
            alert_types=[NotificationType.CRITICAL_ALERT, NotificationType.SYSTEM_ERROR],
            min_severity=AlertSeverity.CRITICAL
        )
        
        # Email channel for performance alerts
        self.notification_channels["email_performance"] = NotificationChannel(
            channel_id="email_performance", 
            channel_type="email",
            config={
                "recipients": ["shayan.bozorgmanesh@gmail.com"],
                "subject_prefix": "📊 Growth Performance Update",
                "template": "performance_report"
            },
            alert_types=[NotificationType.PERFORMANCE_ALERT, NotificationType.TARGET_MISSED, NotificationType.TARGET_ACHIEVED],
            min_severity=AlertSeverity.MEDIUM
        )
        
        # Email channel for opportunities and deals
        self.notification_channels["email_revenue"] = NotificationChannel(
            channel_id="email_revenue",
            channel_type="email", 
            config={
                "recipients": ["shayan.bozorgmanesh@gmail.com"],
                "subject_prefix": "💰 Revenue Update",
                "template": "revenue_alert"
            },
            alert_types=[NotificationType.OPPORTUNITY_CREATED, NotificationType.DEAL_CLOSED, NotificationType.MILESTONE_REACHED],
            min_severity=AlertSeverity.LOW
        )
        
        # Webhook channel for real-time updates
        if self.webhook_config.get("general_webhook"):
            self.notification_channels["webhook_general"] = NotificationChannel(
                channel_id="webhook_general",
                channel_type="webhook",
                config={
                    "url": self.webhook_config["general_webhook"],
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"}
                },
                alert_types=list(NotificationType),
                min_severity=AlertSeverity.LOW
            )
    
    async def create_alert(self, alert_type: NotificationType, severity: AlertSeverity,
                          title: str, message: str, source_agent: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None,
                          action_required: bool = False) -> GrowthAlert:
        """Create and process a growth alert"""
        
        alert_id = f"{alert_type.value}_{int(datetime.utcnow().timestamp())}"
        
        alert = GrowthAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            source_agent=source_agent,
            context=context or {},
            action_required=action_required,
            acknowledgement_required=severity in [AlertSeverity.CRITICAL, AlertSeverity.URGENT]
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        await self._send_alert_notifications(alert)
        
        self.logger.info(f"Created alert: {alert_id} - {title}")
        return alert
    
    async def _send_alert_notifications(self, alert: GrowthAlert):
        """Send alert notifications to all applicable channels"""
        for channel in self.notification_channels.values():
            if not channel.is_active:
                continue
            
            # Check if channel handles this alert type
            if alert.alert_type not in channel.alert_types:
                continue
            
            # Check severity threshold
            if alert.severity.value < channel.min_severity.value:
                continue
            
            try:
                if channel.channel_type == "email":
                    await self._send_email_notification(alert, channel)
                elif channel.channel_type == "webhook":
                    await self._send_webhook_notification(alert, channel)
                elif channel.channel_type == "slack":
                    await self._send_slack_notification(alert, channel)
            except Exception as e:
                self.logger.error(f"Failed to send notification via {channel.channel_id}: {str(e)}")
    
    async def _send_email_notification(self, alert: GrowthAlert, channel: NotificationChannel):
        """Send email notification"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"{channel.config['subject_prefix']} - {alert.title}"
            msg['From'] = self.email_config['from_email']
            msg['To'] = ", ".join(channel.config['recipients'])
            
            # Generate email content based on template
            if channel.config.get('template') == 'critical_alert':
                content = self._generate_critical_alert_email(alert)
            elif channel.config.get('template') == 'performance_report':
                content = await self._generate_performance_report_email(alert)
            elif channel.config.get('template') == 'revenue_alert':
                content = self._generate_revenue_alert_email(alert)
            else:
                content = self._generate_basic_alert_email(alert)
            
            msg.attach(MIMEText(content, 'html'))
            
            # Add to email queue for async processing
            await self.email_queue.put({
                'msg': msg,
                'recipients': channel.config['recipients']
            })
            
            alert.notification_sent = True
            self.logger.info(f"Email notification queued for alert: {alert.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to prepare email notification: {str(e)}")
    
    async def _send_webhook_notification(self, alert: GrowthAlert, channel: NotificationChannel):
        """Send webhook notification"""
        try:
            payload = {
                "timestamp": alert.timestamp.isoformat(),
                "alert": alert.to_dict(),
                "system": "growth_engine"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    channel.config['url'],
                    json=payload,
                    headers=channel.config.get('headers', {})
                ) as response:
                    if response.status == 200:
                        alert.notification_sent = True
                        self.logger.info(f"Webhook notification sent for alert: {alert.alert_id}")
                    else:
                        self.logger.error(f"Webhook notification failed with status: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {str(e)}")
    
    async def _send_slack_notification(self, alert: GrowthAlert, channel: NotificationChannel):
        """Send Slack notification"""
        try:
            # Format Slack message
            emoji = self._get_alert_emoji(alert.severity)
            color = self._get_alert_color(alert.severity)
            
            payload = {
                "text": f"{emoji} Growth Alert: {alert.title}",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Source",
                                "value": alert.source_agent or "System",
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            }
                        ],
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    channel.config['url'],
                    json=payload
                ) as response:
                    if response.status == 200:
                        alert.notification_sent = True
                        self.logger.info(f"Slack notification sent for alert: {alert.alert_id}")
                        
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
    
    def _get_alert_emoji(self, severity: AlertSeverity) -> str:
        """Get emoji for alert severity"""
        emoji_map = {
            AlertSeverity.LOW: "ℹ️",
            AlertSeverity.MEDIUM: "⚠️", 
            AlertSeverity.HIGH: "🚨",
            AlertSeverity.CRITICAL: "🔥",
            AlertSeverity.URGENT: "💥"
        }
        return emoji_map.get(severity, "📢")
    
    def _get_alert_color(self, severity: AlertSeverity) -> str:
        """Get color for alert severity"""
        color_map = {
            AlertSeverity.LOW: "good",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.HIGH: "danger", 
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.URGENT: "#ff0000"
        }
        return color_map.get(severity, "#cccccc")
    
    def _generate_critical_alert_email(self, alert: GrowthAlert) -> str:
        """Generate critical alert email content"""
        return f"""
        <html>
        <body>
            <div style="background: #ff4444; color: white; padding: 20px; text-align: center;">
                <h1>🚨 CRITICAL GROWTH ENGINE ALERT 🚨</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2>{alert.title}</h2>
                
                <p><strong>Severity:</strong> <span style="color: #ff4444; font-weight: bold;">{alert.severity.value.upper()}</span></p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Source:</strong> {alert.source_agent or 'System'}</p>
                
                <div style="background: #f8f8f8; padding: 15px; border-left: 4px solid #ff4444;">
                    <p><strong>Alert Message:</strong></p>
                    <p>{alert.message}</p>
                </div>
                
                {self._format_alert_context(alert.context)}
                
                <div style="background: #ffe6e6; padding: 15px; margin-top: 20px;">
                    <p><strong>⚡ IMMEDIATE ACTION REQUIRED ⚡</strong></p>
                    <p>This critical alert requires immediate attention to prevent impact on growth performance.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def _generate_performance_report_email(self, alert: GrowthAlert) -> str:
        """Generate performance report email content"""
        # Get current performance dashboard
        dashboard = await growth_metrics_tracker.get_performance_dashboard()
        
        return f"""
        <html>
        <body>
            <div style="background: #4CAF50; color: white; padding: 20px; text-align: center;">
                <h1>📊 Growth Performance Update</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2>{alert.title}</h2>
                
                <p><strong>Alert Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                
                <h3>📈 Current Performance Metrics</h3>
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background: #f2f2f2;">
                        <th style="padding: 10px; border: 1px solid #ddd;">Metric</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Current</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Target</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Achievement</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Revenue</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${dashboard['current_metrics']['bd_metrics']['revenue_recognized']:,.2f}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${dashboard['weekly_targets']['revenue_target']:,.2f}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{dashboard['target_achievement']['revenue']['achievement_rate']:.1%}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Leads</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{dashboard['current_metrics']['bd_metrics']['leads_generated']}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{dashboard['weekly_targets']['new_leads']}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{dashboard['target_achievement']['leads']['achievement_rate']:.1%}</td>
                    </tr>
                </table>
                
                <h3>🏆 Top Performers</h3>
                <ul>
                    {' '.join([f"<li><strong>{agent['agent_id']}</strong>: {agent['performance_score']:.2f} ({agent['efficiency_rating']})</li>" for agent in dashboard['top_performers'][:3]])}
                </ul>
            </div>
        </body>
        </html>
        """
    
    def _generate_revenue_alert_email(self, alert: GrowthAlert) -> str:
        """Generate revenue alert email content"""
        return f"""
        <html>
        <body>
            <div style="background: #2E7D32; color: white; padding: 20px; text-align: center;">
                <h1>💰 Revenue Update</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2>{alert.title}</h2>
                
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Source:</strong> {alert.source_agent or 'System'}</p>
                
                <div style="background: #e8f5e8; padding: 15px; border-left: 4px solid #4CAF50;">
                    <p>{alert.message}</p>
                </div>
                
                {self._format_alert_context(alert.context)}
            </div>
        </body>
        </html>
        """
    
    def _generate_basic_alert_email(self, alert: GrowthAlert) -> str:
        """Generate basic alert email content"""
        return f"""
        <html>
        <body>
            <div style="background: #333; color: white; padding: 20px; text-align: center;">
                <h1>📢 Growth Engine Alert</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2>{alert.title}</h2>
                
                <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Source:</strong> {alert.source_agent or 'System'}</p>
                
                <div style="background: #f8f8f8; padding: 15px; border-left: 4px solid #333;">
                    <p>{alert.message}</p>
                </div>
                
                {self._format_alert_context(alert.context)}
            </div>
        </body>
        </html>
        """
    
    def _format_alert_context(self, context: Dict[str, Any]) -> str:
        """Format alert context for email"""
        if not context:
            return ""
        
        context_html = "<h3>📋 Additional Context</h3><ul>"
        for key, value in context.items():
            context_html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        context_html += "</ul>"
        
        return context_html
    
    async def process_email_queue(self):
        """Process email notification queue"""
        while True:
            try:
                email_item = await self.email_queue.get()
                await self._send_email(email_item['msg'], email_item['recipients'])
                self.email_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error processing email queue: {str(e)}")
                await asyncio.sleep(5)
    
    async def _send_email(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP"""
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['email_user'], self.email_config['email_password'])
                server.send_message(msg, to_addrs=recipients)
            
            self.logger.info(f"Email sent successfully to {', '.join(recipients)}")
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
    
    async def monitor_performance_and_alert(self):
        """Monitor system performance and generate alerts"""
        while True:
            try:
                # Get current performance metrics
                dashboard = await growth_metrics_tracker.get_performance_dashboard()
                alerts = await growth_metrics_tracker.generate_performance_alerts()
                
                # Process performance alerts
                for perf_alert in alerts:
                    await self.create_alert(
                        alert_type=NotificationType.PERFORMANCE_ALERT,
                        severity=AlertSeverity.HIGH if perf_alert['severity'] == 'HIGH' else AlertSeverity.MEDIUM,
                        title=f"Performance Alert: {perf_alert['agent_id']}",
                        message=perf_alert['message'],
                        source_agent=perf_alert.get('agent_id'),
                        context={
                            'recommendation': perf_alert['recommendation'],
                            'alert_type': perf_alert['type']
                        }
                    )
                
                # Check for milestone achievements
                revenue_achievement = dashboard['target_achievement']['revenue']['achievement_rate']
                if revenue_achievement >= 1.0:
                    await self.create_alert(
                        alert_type=NotificationType.TARGET_ACHIEVED,
                        severity=AlertSeverity.LOW,
                        title="🎯 Revenue Target Achieved!",
                        message=f"Weekly revenue target achieved at {revenue_achievement:.1%}",
                        context={'current_revenue': dashboard['current_metrics']['bd_metrics']['revenue_recognized']}
                    )
                elif revenue_achievement < 0.5:  # Less than 50% of target
                    await self.create_alert(
                        alert_type=NotificationType.TARGET_MISSED,
                        severity=AlertSeverity.HIGH,
                        title="⚠️ Revenue Target At Risk",
                        message=f"Revenue achievement at only {revenue_achievement:.1%} of target",
                        context={'current_revenue': dashboard['current_metrics']['bd_metrics']['revenue_recognized']},
                        action_required=True
                    )
                
                # Sleep for 1 hour before next check
                await asyncio.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    async def start_notification_services(self):
        """Start all notification services"""
        self.logger.info("Starting growth notification services")
        
        # Start email queue processor
        asyncio.create_task(self.process_email_queue())
        
        # Start performance monitoring
        asyncio.create_task(self.monitor_performance_and_alert())
        
        self.logger.info("Growth notification services started")

# Global notification system instance
growth_notification_system = GrowthNotificationSystem()