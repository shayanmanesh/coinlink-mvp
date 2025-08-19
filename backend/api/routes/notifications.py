"""
Notifications and alerts API routes
System notifications, price alerts, and news updates
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Annotated
from enum import Enum

from fastapi import APIRouter, HTTPException, status, Header, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...auth.jwt import extract_bearer_token
from ...auth.service import auth_service
from ...db.database import get_async_session

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v2/notifications", tags=["Notifications v2"])

class NotificationType(str, Enum):
    """Notification types"""
    PRICE_ALERT = "price_alert"
    NEWS_UPDATE = "news_update"
    SYSTEM_ALERT = "system_alert"
    TRADE_UPDATE = "trade_update"
    SECURITY_ALERT = "security_alert"

class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Notification(BaseModel):
    """Notification model"""
    id: str = Field(..., description="Notification ID")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: NotificationPriority = Field(..., description="Priority level")
    is_read: bool = Field(False, description="Whether notification has been read")
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    action_url: Optional[str] = Field(None, description="Action URL")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class NotificationSettings(BaseModel):
    """User notification settings"""
    email_enabled: bool = Field(True, description="Enable email notifications")
    push_enabled: bool = Field(True, description="Enable push notifications") 
    sms_enabled: bool = Field(False, description="Enable SMS notifications")
    price_alerts: bool = Field(True, description="Enable price alerts")
    news_updates: bool = Field(True, description="Enable news updates")
    system_alerts: bool = Field(True, description="Enable system alerts")
    trade_updates: bool = Field(True, description="Enable trade updates")
    security_alerts: bool = Field(True, description="Enable security alerts")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")

class AlertRule(BaseModel):
    """Price alert rule"""
    id: str = Field(..., description="Alert rule ID")
    symbol: str = Field(..., description="Cryptocurrency symbol")
    condition: str = Field(..., description="Alert condition")
    target_value: float = Field(..., description="Target value")
    is_active: bool = Field(True, description="Whether rule is active")
    created_at: str = Field(..., description="Creation timestamp")
    last_triggered: Optional[str] = Field(None, description="Last trigger timestamp")
    trigger_count: int = Field(0, description="Number of times triggered")

async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Dependency to get current authenticated user"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    access_token = extract_bearer_token(authorization)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    user = await auth_service.verify_access_token(access_token, session)
    return user

@router.get("/",
           response_model=List[Notification],
           summary="Get user notifications",
           description="Get user's notifications with filtering and pagination")
async def get_notifications(
    current_user = Depends(get_current_user),
    type_filter: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip")
):
    """
    Get user notifications with filtering options
    
    - **type_filter**: Filter by notification type
    - **unread_only**: Show only unread notifications
    - **limit**: Maximum number of notifications (1-100)
    - **offset**: Number of notifications to skip for pagination
    
    Returns array of user notifications
    """
    try:
        # Generate mock notifications for MVP
        # In production, these would come from database
        mock_notifications = [
            Notification(
                id="notif-1",
                type=NotificationType.PRICE_ALERT,
                title="Bitcoin Price Alert",
                message="Bitcoin has reached your target price of $100,000",
                priority=NotificationPriority.HIGH,
                is_read=False,
                created_at=datetime.now().isoformat(),
                action_url="/market/bitcoin",
                metadata={"symbol": "BTC", "price": 100000, "target": 100000}
            ),
            Notification(
                id="notif-2",
                type=NotificationType.NEWS_UPDATE,
                title="Market News",
                message="Major institutional investor announces Bitcoin allocation",
                priority=NotificationPriority.MEDIUM,
                is_read=True,
                created_at=(datetime.now() - timedelta(hours=2)).isoformat(),
                action_url="/news/bitcoin-institutional-adoption"
            ),
            Notification(
                id="notif-3",
                type=NotificationType.SYSTEM_ALERT,
                title="System Maintenance",
                message="Scheduled maintenance will occur on Sunday at 2 AM UTC",
                priority=NotificationPriority.LOW,
                is_read=False,
                created_at=(datetime.now() - timedelta(hours=4)).isoformat(),
                expires_at=(datetime.now() + timedelta(days=7)).isoformat()
            ),
            Notification(
                id="notif-4",
                type=NotificationType.SECURITY_ALERT,
                title="New Login Detected",
                message="New login from Chrome on Windows (IP: 192.168.1.1)",
                priority=NotificationPriority.CRITICAL,
                is_read=False,
                created_at=(datetime.now() - timedelta(hours=6)).isoformat(),
                action_url="/security/sessions",
                metadata={"ip": "192.168.1.1", "browser": "Chrome", "os": "Windows"}
            )
        ]
        
        # Apply filters
        filtered_notifications = mock_notifications
        
        if type_filter:
            filtered_notifications = [n for n in filtered_notifications if n.type == type_filter]
        
        if unread_only:
            filtered_notifications = [n for n in filtered_notifications if not n.is_read]
        
        # Apply pagination
        paginated = filtered_notifications[offset:offset + limit]
        
        return paginated
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )

@router.put("/{notification_id}/read",
           summary="Mark notification as read",
           description="Mark a specific notification as read")
async def mark_notification_read(
    notification_id: str,
    current_user = Depends(get_current_user)
):
    """
    Mark a notification as read
    
    - **notification_id**: ID of notification to mark as read
    
    Updates the read status of the specified notification
    """
    try:
        # For MVP, just return success
        # In production, update database
        logger.info(f"Notification {notification_id} marked as read for user {current_user.id}")
        
        return {"message": "Notification marked as read"}
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.put("/read-all",
           summary="Mark all notifications as read",
           description="Mark all user notifications as read")
async def mark_all_notifications_read(
    current_user = Depends(get_current_user)
):
    """
    Mark all user notifications as read
    
    Updates read status for all unread notifications
    """
    try:
        # For MVP, just return success
        # In production, update all unread notifications in database
        logger.info(f"All notifications marked as read for user {current_user.id}")
        
        return {"message": "All notifications marked as read"}
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )

@router.delete("/{notification_id}",
              summary="Delete notification",
              description="Delete a specific notification")
async def delete_notification(
    notification_id: str,
    current_user = Depends(get_current_user)
):
    """
    Delete a notification
    
    - **notification_id**: ID of notification to delete
    
    Permanently removes the specified notification
    """
    try:
        # For MVP, just return success
        # In production, delete from database
        logger.info(f"Notification {notification_id} deleted for user {current_user.id}")
        
        return {"message": "Notification deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )

@router.get("/settings",
           response_model=NotificationSettings,
           summary="Get notification settings",
           description="Get user's notification preferences")
async def get_notification_settings(
    current_user = Depends(get_current_user)
):
    """
    Get user notification settings
    
    Returns user's notification preferences including:
    - Delivery method preferences (email, push, SMS)
    - Content type preferences (alerts, news, etc.)
    - Quiet hours configuration
    """
    try:
        # For MVP, return default settings
        # In production, these would be stored in database
        return NotificationSettings(
            email_enabled=True,
            push_enabled=True,
            sms_enabled=False,
            price_alerts=True,
            news_updates=True,
            system_alerts=True,
            trade_updates=True,
            security_alerts=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification settings"
        )

@router.put("/settings",
           response_model=NotificationSettings,
           summary="Update notification settings",
           description="Update user's notification preferences")
async def update_notification_settings(
    settings: NotificationSettings,
    current_user = Depends(get_current_user)
):
    """
    Update user notification settings
    
    - **email_enabled**: Enable/disable email notifications
    - **push_enabled**: Enable/disable push notifications
    - **sms_enabled**: Enable/disable SMS notifications
    - **price_alerts**: Enable/disable price alerts
    - **news_updates**: Enable/disable news updates
    - **system_alerts**: Enable/disable system alerts
    - **trade_updates**: Enable/disable trade updates
    - **security_alerts**: Enable/disable security alerts
    - **quiet_hours_start**: Quiet hours start time (HH:MM)
    - **quiet_hours_end**: Quiet hours end time (HH:MM)
    
    Returns updated notification settings
    """
    try:
        # For MVP, just return the provided settings
        # In production, store in database
        logger.info(f"Notification settings updated for user {current_user.id}")
        
        return settings
        
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )

@router.get("/alerts",
           response_model=List[AlertRule],
           summary="Get price alert rules",
           description="Get user's configured price alert rules")
async def get_alert_rules(
    current_user = Depends(get_current_user)
):
    """
    Get user's price alert rules
    
    Returns list of configured price alert rules with:
    - Alert conditions and target values
    - Trigger statistics
    - Active status
    """
    try:
        # Generate mock alert rules for MVP
        mock_rules = [
            AlertRule(
                id="rule-1",
                symbol="BTC",
                condition="above",
                target_value=100000.0,
                is_active=True,
                created_at=datetime.now().isoformat(),
                last_triggered=None,
                trigger_count=0
            ),
            AlertRule(
                id="rule-2", 
                symbol="ETH",
                condition="below",
                target_value=3000.0,
                is_active=True,
                created_at=datetime.now().isoformat(),
                last_triggered=(datetime.now() - timedelta(days=2)).isoformat(),
                trigger_count=3
            )
        ]
        
        return mock_rules
        
    except Exception as e:
        logger.error(f"Error getting alert rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert rules"
        )

@router.post("/alerts",
            response_model=AlertRule,
            status_code=status.HTTP_201_CREATED,
            summary="Create price alert rule",
            description="Create a new price alert rule")
async def create_alert_rule(
    rule_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """
    Create a new price alert rule
    
    - **symbol**: Cryptocurrency symbol (e.g., "BTC")
    - **condition**: Alert condition ("above", "below", "crosses_above", "crosses_below")
    - **target_value**: Target price or value
    
    Returns created alert rule
    """
    try:
        symbol = rule_data.get("symbol", "").upper()
        condition = rule_data.get("condition", "").lower()
        target_value = rule_data.get("target_value")
        
        # Validate input
        valid_conditions = ["above", "below", "crosses_above", "crosses_below"]
        if not symbol or condition not in valid_conditions or not target_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alert rule parameters"
            )
        
        # For MVP, return mock created rule
        rule_id = f"rule-{int(datetime.now().timestamp())}"
        
        new_rule = AlertRule(
            id=rule_id,
            symbol=symbol,
            condition=condition,
            target_value=float(target_value),
            is_active=True,
            created_at=datetime.now().isoformat(),
            last_triggered=None,
            trigger_count=0
        )
        
        logger.info(f"Alert rule created: {rule_id} for user {current_user.id}")
        return new_rule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert rule"
        )

@router.put("/alerts/{rule_id}",
           response_model=AlertRule,
           summary="Update price alert rule",
           description="Update an existing price alert rule")
async def update_alert_rule(
    rule_id: str,
    rule_updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """
    Update an existing price alert rule
    
    - **rule_id**: ID of rule to update
    - **is_active**: Enable/disable the rule
    - **target_value**: Update target value
    - **condition**: Update alert condition
    
    Returns updated alert rule
    """
    try:
        # For MVP, return mock updated rule
        updated_rule = AlertRule(
            id=rule_id,
            symbol="BTC", 
            condition=rule_updates.get("condition", "above"),
            target_value=rule_updates.get("target_value", 100000.0),
            is_active=rule_updates.get("is_active", True),
            created_at=datetime.now().isoformat(),
            last_triggered=None,
            trigger_count=0
        )
        
        logger.info(f"Alert rule {rule_id} updated for user {current_user.id}")
        return updated_rule
        
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert rule"
        )

@router.delete("/alerts/{rule_id}",
              summary="Delete price alert rule",
              description="Delete a price alert rule")
async def delete_alert_rule(
    rule_id: str,
    current_user = Depends(get_current_user)
):
    """
    Delete a price alert rule
    
    - **rule_id**: ID of rule to delete
    
    Permanently removes the specified alert rule
    """
    try:
        # For MVP, just return success
        logger.info(f"Alert rule {rule_id} deleted for user {current_user.id}")
        
        return {"message": "Alert rule deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert rule"
        )

@router.get("/unread-count",
           summary="Get unread notification count",
           description="Get count of unread notifications")
async def get_unread_count(
    current_user = Depends(get_current_user)
):
    """
    Get count of unread notifications
    
    Returns simple count of unread notifications for badge display
    """
    try:
        # For MVP, return mock count
        # In production, this would be a database count query
        return {"unread_count": 3}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )

@router.get("/health")
async def notifications_health():
    """Notifications service health check"""
    return {
        "status": "healthy",
        "service": "notifications",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/",
            "/settings",
            "/alerts", 
            "/unread-count"
        ]
    }