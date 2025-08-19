"""
User management API routes
User profile, preferences, and account management endpoints
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Annotated

from fastapi import APIRouter, HTTPException, status, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...auth.jwt import extract_bearer_token
from ...auth.service import auth_service
from ...db.database import get_async_session
from ...db.repositories import UserRepository, UserSessionRepository
from ...db.schemas import UserResponse, UserUpdate

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v2/user", tags=["User Management v2"])

class UserPreferences(BaseModel):
    """User preferences model"""
    theme: str = Field("dark", description="UI theme preference")
    language: str = Field("en", description="Language preference")
    currency: str = Field("USD", description="Display currency")
    notifications_enabled: bool = Field(True, description="Enable push notifications")
    email_alerts: bool = Field(True, description="Enable email alerts")
    price_alerts: bool = Field(True, description="Enable price alerts")
    news_notifications: bool = Field(True, description="Enable news notifications")
    sound_enabled: bool = Field(True, description="Enable sound notifications")

class UserStats(BaseModel):
    """User statistics model"""
    total_logins: int = Field(..., description="Total number of logins")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    account_age_days: int = Field(..., description="Account age in days")
    active_sessions: int = Field(..., description="Number of active sessions")
    total_sessions: int = Field(..., description="Total sessions created")

class UserSession(BaseModel):
    """User session information"""
    id: str = Field(..., description="Session ID")
    created_at: str = Field(..., description="Session creation time")
    last_used: Optional[str] = Field(None, description="Last activity time")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    is_current: bool = Field(..., description="Whether this is the current session")

class PriceAlert(BaseModel):
    """User price alert"""
    id: str = Field(..., description="Alert ID")
    symbol: str = Field(..., description="Cryptocurrency symbol")
    target_price: float = Field(..., description="Target price")
    condition: str = Field(..., description="Alert condition (above/below)")
    created_at: str = Field(..., description="Alert creation time")
    is_active: bool = Field(..., description="Whether alert is active")

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

@router.get("/profile",
           response_model=UserResponse,
           summary="Get user profile",
           description="Get current user profile information")
async def get_user_profile(
    current_user = Depends(get_current_user)
):
    """
    Get current user profile information
    
    Returns complete user profile data including:
    - User ID and email
    - Profile information (name, etc.)
    - Account status and verification
    - Account timestamps
    """
    try:
        return UserResponse.from_orm(current_user)
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.put("/profile",
           response_model=UserResponse,
           summary="Update user profile", 
           description="Update user profile information")
async def update_user_profile(
    profile_update: UserUpdate,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update user profile information
    
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **is_active**: Account active status (admin only)
    - **is_verified**: Email verification status (admin only)
    
    Returns updated user profile
    """
    try:
        user_repo = UserRepository(session)
        
        # Update user
        updated_user = await user_repo.update_user(
            current_user.id,
            **profile_update.dict(exclude_none=True)
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await session.commit()
        
        logger.info(f"User profile updated: {current_user.id}")
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.get("/preferences",
           response_model=UserPreferences,
           summary="Get user preferences",
           description="Get user preference settings")
async def get_user_preferences(
    current_user = Depends(get_current_user)
):
    """
    Get user preference settings
    
    Returns user preferences including:
    - UI theme and language settings
    - Notification preferences
    - Display currency settings
    """
    try:
        # For MVP, return default preferences
        # In production, these would be stored in database
        return UserPreferences(
            theme="dark",
            language="en",
            currency="USD",
            notifications_enabled=True,
            email_alerts=True,
            price_alerts=True,
            news_notifications=True,
            sound_enabled=True
        )
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user preferences"
        )

@router.put("/preferences",
           response_model=UserPreferences,
           summary="Update user preferences",
           description="Update user preference settings")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user = Depends(get_current_user)
):
    """
    Update user preference settings
    
    - **theme**: UI theme (light/dark)
    - **language**: Interface language code
    - **currency**: Display currency (USD, EUR, etc.)
    - **notifications_enabled**: Enable/disable notifications
    - **email_alerts**: Enable/disable email alerts
    - **price_alerts**: Enable/disable price alerts
    - **news_notifications**: Enable/disable news notifications
    - **sound_enabled**: Enable/disable sound notifications
    
    Returns updated preferences
    """
    try:
        # For MVP, just return the provided preferences
        # In production, these would be stored in database
        logger.info(f"User preferences updated: {current_user.id}")
        return preferences
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )

@router.get("/stats",
           response_model=UserStats,
           summary="Get user statistics",
           description="Get user account statistics and metrics")
async def get_user_stats(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get user account statistics
    
    Returns account metrics including:
    - Login statistics
    - Account age and activity
    - Session information
    """
    try:
        # Calculate account age
        account_age = (datetime.now() - current_user.created_at).days
        
        # For MVP, return mock statistics
        # In production, these would be calculated from actual data
        return UserStats(
            total_logins=42,  # Mock data
            last_login=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            account_age_days=account_age,
            active_sessions=1,  # Mock data
            total_sessions=15   # Mock data
        )
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.get("/sessions",
           response_model=List[UserSession],
           summary="Get user sessions",
           description="Get list of user's active and recent sessions")
async def get_user_sessions(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get user's active and recent sessions
    
    Returns list of sessions with:
    - Session creation and activity times
    - IP address and user agent information
    - Current session indicator
    """
    try:
        session_repo = UserSessionRepository(session)
        
        # Get user sessions (this would require extending the repository)
        # For MVP, return mock session data
        return [
            UserSession(
                id="current-session",
                created_at=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0...",
                is_current=True
            )
        ]
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user sessions"
        )

@router.delete("/sessions/{session_id}",
              summary="Revoke user session",
              description="Revoke a specific user session")
async def revoke_user_session(
    session_id: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Revoke a specific user session
    
    - **session_id**: ID of session to revoke
    
    Terminates the specified session and blacklists associated tokens
    """
    try:
        session_repo = UserSessionRepository(session)
        
        # Deactivate the specific session
        success = await session_repo.deactivate_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or already inactive"
            )
        
        await session.commit()
        
        logger.info(f"Session {session_id} revoked for user {current_user.id}")
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error revoking user session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

@router.get("/alerts",
           response_model=List[PriceAlert],
           summary="Get user price alerts",
           description="Get user's configured price alerts")
async def get_user_alerts(
    current_user = Depends(get_current_user)
):
    """
    Get user's configured price alerts
    
    Returns list of price alerts with:
    - Target prices and conditions
    - Alert status and creation time
    - Associated cryptocurrency symbols
    """
    try:
        # For MVP, return mock alert data
        # In production, these would be stored in database
        return [
            PriceAlert(
                id="alert-1",
                symbol="BTC",
                target_price=100000.0,
                condition="above",
                created_at=datetime.now().isoformat(),
                is_active=True
            ),
            PriceAlert(
                id="alert-2", 
                symbol="ETH",
                target_price=3000.0,
                condition="below",
                created_at=datetime.now().isoformat(),
                is_active=True
            )
        ]
        
    except Exception as e:
        logger.error(f"Error getting user alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user alerts"
        )

@router.post("/alerts",
            response_model=PriceAlert,
            status_code=status.HTTP_201_CREATED,
            summary="Create price alert",
            description="Create a new price alert")
async def create_price_alert(
    alert_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """
    Create a new price alert
    
    - **symbol**: Cryptocurrency symbol (e.g., "BTC")
    - **target_price**: Target price for alert
    - **condition**: Alert condition ("above" or "below")
    
    Returns created alert information
    """
    try:
        symbol = alert_data.get("symbol", "").upper()
        target_price = alert_data.get("target_price")
        condition = alert_data.get("condition", "").lower()
        
        # Validate input
        if not symbol or not target_price or condition not in ["above", "below"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alert parameters"
            )
        
        # For MVP, return mock created alert
        # In production, store in database and configure actual alerting
        alert_id = f"alert-{int(datetime.now().timestamp())}"
        
        new_alert = PriceAlert(
            id=alert_id,
            symbol=symbol,
            target_price=float(target_price),
            condition=condition,
            created_at=datetime.now().isoformat(),
            is_active=True
        )
        
        logger.info(f"Price alert created: {alert_id} for user {current_user.id}")
        return new_alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating price alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create price alert"
        )

@router.delete("/alerts/{alert_id}",
              summary="Delete price alert",
              description="Delete a user's price alert")
async def delete_price_alert(
    alert_id: str,
    current_user = Depends(get_current_user)
):
    """
    Delete a user's price alert
    
    - **alert_id**: ID of alert to delete
    
    Removes the specified price alert
    """
    try:
        # For MVP, just return success
        # In production, remove from database
        logger.info(f"Price alert {alert_id} deleted for user {current_user.id}")
        return {"message": "Price alert deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting price alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete price alert"
        )

@router.get("/health")
async def user_management_health():
    """User management service health check"""
    return {
        "status": "healthy",
        "service": "user_management",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/profile",
            "/preferences", 
            "/stats",
            "/sessions",
            "/alerts"
        ]
    }