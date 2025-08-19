"""
Authentication API routes v2
Production-ready auth endpoints with comprehensive validation
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from .service import auth_service
from .jwt import extract_bearer_token
from ..db.database import get_async_session
from ..db.schemas import (
    UserCreate, 
    UserLogin, 
    AuthResponse, 
    RefreshTokenRequest, 
    RefreshTokenResponse,
    LogoutRequest,
    LogoutResponse,
    UserVerificationResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v2/auth", tags=["Authentication v2"])

# Security scheme
security = HTTPBearer(auto_error=False)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

def get_client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and user agent from request"""
    ip_address = get_remote_address(request)
    user_agent = request.headers.get("User-Agent", "unknown")
    return ip_address, user_agent

@router.post("/signup", 
             response_model=AuthResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Register new user account",
             description="Create a new user account with email and password")
@limiter.limit("5/minute")  # Strict rate limiting for signup
async def signup(
    request: Request,
    signup_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user account
    
    - **email**: Valid email address (will be converted to lowercase)
    - **password**: Strong password (12+ chars, upper/lower/digit/special)
    - **confirm_password**: Must match password
    - **first_name**: Optional first name (max 100 chars)
    - **last_name**: Optional last name (max 100 chars)
    
    Returns user information and JWT tokens for immediate login.
    """
    try:
        ip_address, user_agent = get_client_info(request)
        
        result = await auth_service.signup(
            signup_data=signup_data,
            session=session,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"User signup successful from {ip_address}: {result.user.email}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )

@router.post("/login",
             response_model=AuthResponse,
             status_code=status.HTTP_200_OK,
             summary="Authenticate user login",
             description="Login with email and password to receive JWT tokens")
@limiter.limit("10/minute")  # Rate limiting for login attempts
async def login(
    request: Request,
    login_data: UserLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user login
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns user information and JWT tokens (access + refresh).
    Access tokens are short-lived, refresh tokens are longer-lived.
    """
    try:
        ip_address, user_agent = get_client_info(request)
        
        result = await auth_service.login(
            login_data=login_data,
            session=session,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"User login successful from {ip_address}: {result.user.email}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/refresh",
             response_model=RefreshTokenResponse,
             status_code=status.HTTP_200_OK,
             summary="Refresh access token",
             description="Use refresh token to obtain new access token")
@limiter.limit("20/minute")  # Higher limit for token refresh
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token from login/signup
    
    Implements token rotation: old refresh token is invalidated,
    new tokens are returned. This improves security.
    """
    try:
        result = await auth_service.refresh_tokens(
            refresh_token=refresh_request.refresh_token,
            session=session
        )
        
        logger.debug("Token refresh successful")
        
        return RefreshTokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            expires_in=result.expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.post("/logout",
             response_model=LogoutResponse,
             status_code=status.HTTP_200_OK,
             summary="Logout user session",
             description="Logout by invalidating refresh token and session")
async def logout(
    logout_request: LogoutRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Logout user session
    
    - **refresh_token**: Refresh token to invalidate
    
    Invalidates the refresh token and associated session.
    Access tokens remain valid until natural expiration.
    """
    try:
        message = await auth_service.logout(
            refresh_token=logout_request.refresh_token,
            session=session
        )
        
        logger.debug("User logout successful")
        
        return LogoutResponse(message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.get("/verify",
            response_model=UserVerificationResponse,
            status_code=status.HTTP_200_OK,
            summary="Verify access token",
            description="Verify access token and return user information")
async def verify_token(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Verify access token and return user information
    
    Requires Authorization header with Bearer token.
    Returns current user information if token is valid.
    """
    try:
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
        
        user = await auth_service.verify_access_token(
            access_token=access_token,
            session=session
        )
        
        from ..db.schemas import UserResponse
        user_response = UserResponse.from_orm(user)
        
        return UserVerificationResponse(
            user=user_response,
            message="Token is valid"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token verification"
        )

@router.post("/logout-all",
             response_model=LogoutResponse,
             status_code=status.HTTP_200_OK,
             summary="Logout all user sessions",
             description="Security endpoint to logout all sessions for current user")
async def logout_all_sessions(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Logout all sessions for current user
    
    Security endpoint that invalidates all refresh tokens and sessions
    for the authenticated user. Useful if account is compromised.
    """
    try:
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
        
        # Verify token and get user
        user = await auth_service.verify_access_token(
            access_token=access_token,
            session=session
        )
        
        # Logout all sessions
        count = await auth_service.logout_all_sessions(
            user_id=user.id,
            session=session
        )
        
        logger.info(f"All sessions logged out for user {user.id}: {count} sessions")
        
        return LogoutResponse(message=f"Logged out {count} sessions")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected logout-all error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout-all"
        )

@router.get("/health",
            status_code=status.HTTP_200_OK,
            summary="Auth service health check",
            description="Check if authentication service is operational")
async def auth_health_check(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authentication service health check
    
    Verifies database connectivity and service availability.
    """
    try:
        # Test database connectivity
        from ..db.database import check_db_health
        db_healthy = await check_db_health()
        
        # Test JWT service
        from .jwt import jwt_service
        test_token = jwt_service.create_access_token("test", "test@example.com")
        jwt_healthy = bool(test_token)
        
        # Test password service
        from .hashing import password_service
        test_hash = password_service.hash_password("test")
        password_healthy = bool(test_hash)
        
        overall_healthy = db_healthy and jwt_healthy and password_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "jwt_service": "healthy" if jwt_healthy else "unhealthy",
                "password_service": "healthy" if password_healthy else "unhealthy"
            }
        }
        
    except Exception as e:
        logger.error(f"Auth health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Rate limit exceeded handler
@router.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    """Handle rate limit exceeded"""
    return HTTPException(
        status_code=429,
        detail={
            "error": {
                "code": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": getattr(exc, 'retry_after', 60)
            }
        }
    )