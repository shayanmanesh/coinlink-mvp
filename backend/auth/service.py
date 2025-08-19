"""
Authentication service with business logic
Orchestrates JWT, hashing, database operations, and session management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from .jwt import jwt_service
from .hashing import password_service
from ..db.repositories import UserRepository, UserSessionRepository, TokenBlacklistRepository
from ..db.schemas import UserCreate, UserLogin, AuthResponse, UserResponse, TokenPair
from ..db.models import User

logger = logging.getLogger(__name__)

class AuthenticationService:
    """
    Production authentication service
    Handles signup, login, logout, token refresh, and session management
    """
    
    def __init__(self):
        self.max_active_sessions = 5  # Max concurrent sessions per user
        self.password_reset_token_lifetime = timedelta(minutes=30)
        self.email_verification_token_lifetime = timedelta(hours=24)
    
    async def signup(self, signup_data: UserCreate, session: AsyncSession, 
                    ip_address: str = None, user_agent: str = None) -> AuthResponse:
        """
        Register a new user account
        Returns authentication response with tokens
        """
        try:
            # Initialize repositories
            user_repo = UserRepository(session)
            session_repo = UserSessionRepository(session)
            
            # Check if user already exists
            existing_user = await user_repo.get_user_by_email(signup_data.email)
            if existing_user:
                logger.warning(f"Signup attempt with existing email: {signup_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            password_hash = password_service.hash_password(signup_data.password)
            
            # Create user
            new_user = await user_repo.create_user(
                email=signup_data.email,
                password_hash=password_hash,
                first_name=signup_data.first_name,
                last_name=signup_data.last_name
            )
            
            if not new_user:
                logger.error(f"Failed to create user: {signup_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user account"
                )
            
            # Create token pair
            token_data = jwt_service.create_token_pair(str(new_user.id), new_user.email)
            
            # Create refresh token session
            await session_repo.create_session(
                user_id=new_user.id,
                jti=token_data["refresh_jti"],
                expires_at=datetime.utcnow() + timedelta(days=7),
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Commit transaction
            await session.commit()
            
            logger.info(f"User signup successful: {new_user.id} ({new_user.email})")
            
            # Prepare response
            user_response = UserResponse.from_orm(new_user)
            tokens = TokenPair(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data["token_type"],
                expires_in=token_data["expires_in"]
            )
            
            return AuthResponse(
                user=user_response,
                tokens=tokens,
                message="Account created successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Signup error for {signup_data.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during signup"
            )
    
    async def login(self, login_data: UserLogin, session: AsyncSession,
                   ip_address: str = None, user_agent: str = None) -> AuthResponse:
        """
        Authenticate user and create session
        Returns authentication response with tokens
        """
        try:
            # Initialize repositories
            user_repo = UserRepository(session)
            session_repo = UserSessionRepository(session)
            
            # Get user by email
            user = await user_repo.get_user_by_email(login_data.email)
            if not user:
                logger.warning(f"Login attempt with non-existent email: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt for deactivated user: {user.id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated"
                )
            
            # Verify password
            if not password_service.verify_password(login_data.password, user.password_hash):
                logger.warning(f"Failed login attempt for user: {user.id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if password needs rehashing
            if password_service.needs_rehash(user.password_hash):
                new_hash = password_service.hash_password(login_data.password)
                await user_repo.update_user(user.id, password_hash=new_hash)
                logger.info(f"Password rehashed for user {user.id}")
            
            # Clean up old sessions if user has too many
            await self._cleanup_old_sessions(user.id, session_repo)
            
            # Create token pair
            token_data = jwt_service.create_token_pair(str(user.id), user.email)
            
            # Create refresh token session
            await session_repo.create_session(
                user_id=user.id,
                jti=token_data["refresh_jti"],
                expires_at=datetime.utcnow() + timedelta(days=7),
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Update last login timestamp
            await user_repo.update_last_login(user.id)
            
            # Commit transaction
            await session.commit()
            
            logger.info(f"User login successful: {user.id}")
            
            # Prepare response
            user_response = UserResponse.from_orm(user)
            tokens = TokenPair(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data["token_type"],
                expires_in=token_data["expires_in"]
            )
            
            return AuthResponse(
                user=user_response,
                tokens=tokens,
                message="Login successful"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Login error for {login_data.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during login"
            )
    
    async def refresh_tokens(self, refresh_token: str, session: AsyncSession) -> TokenPair:
        """
        Refresh access token using refresh token
        Implements token rotation for security
        """
        try:
            # Validate refresh token
            payload = jwt_service.validate_token_for_type(refresh_token, "refresh")
            user_id = payload["sub"]
            refresh_jti = payload["jti"]
            user_email = payload["email"]
            
            # Initialize repositories
            user_repo = UserRepository(session)
            session_repo = UserSessionRepository(session)
            blacklist_repo = TokenBlacklistRepository(session)
            
            # Check if token is blacklisted
            if await blacklist_repo.is_token_blacklisted(refresh_jti):
                logger.warning(f"Refresh attempt with blacklisted token: {refresh_jti}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is no longer valid"
                )
            
            # Get and validate session
            user_session = await session_repo.get_session_by_jti(refresh_jti)
            if not user_session or not user_session.is_active:
                logger.warning(f"Refresh attempt with invalid session: {refresh_jti}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session is no longer valid"
                )
            
            # Get user and validate
            user = await user_repo.get_user_by_id(uuid.UUID(user_id))
            if not user or not user.is_active:
                logger.warning(f"Refresh attempt for invalid/inactive user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is no longer valid"
                )
            
            # Blacklist the old refresh token
            await blacklist_repo.blacklist_token(
                jti=refresh_jti,
                token_type="refresh",
                user_id=user.id,
                reason="refresh_rotation",
                expires_at=user_session.expires_at
            )
            
            # Deactivate old session
            await session_repo.deactivate_session(refresh_jti)
            
            # Create new token pair
            token_data = jwt_service.create_token_pair(user_id, user_email)
            
            # Create new refresh token session
            await session_repo.create_session(
                user_id=user.id,
                jti=token_data["refresh_jti"],
                expires_at=datetime.utcnow() + timedelta(days=7),
                user_agent=user_session.user_agent,
                ip_address=user_session.ip_address
            )
            
            # Update session last used
            await session_repo.update_session_last_used(token_data["refresh_jti"])
            
            # Commit transaction
            await session.commit()
            
            logger.info(f"Token refresh successful for user: {user_id}")
            
            return TokenPair(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data["token_type"],
                expires_in=token_data["expires_in"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh tokens"
            )
    
    async def logout(self, refresh_token: str, session: AsyncSession) -> str:
        """
        Logout user by invalidating refresh token and session
        """
        try:
            # Validate refresh token (allow expired tokens for logout)
            payload = jwt_service.get_token_claims(refresh_token, verify_exp=False)
            if not payload or payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid refresh token"
                )
            
            user_id = payload["sub"]
            refresh_jti = payload["jti"]
            
            # Initialize repositories
            session_repo = UserSessionRepository(session)
            blacklist_repo = TokenBlacklistRepository(session)
            
            # Get session info for blacklist expiration
            user_session = await session_repo.get_session_by_jti(refresh_jti)
            expires_at = user_session.expires_at if user_session else datetime.utcnow() + timedelta(days=7)
            
            # Blacklist the refresh token
            await blacklist_repo.blacklist_token(
                jti=refresh_jti,
                token_type="refresh", 
                user_id=uuid.UUID(user_id) if user_id else None,
                reason="logout",
                expires_at=expires_at
            )
            
            # Deactivate session
            await session_repo.deactivate_session(refresh_jti)
            
            # Commit transaction
            await session.commit()
            
            logger.info(f"User logout successful: {user_id}")
            
            return "Logout successful"
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Logout error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during logout"
            )
    
    async def verify_access_token(self, access_token: str, session: AsyncSession) -> User:
        """
        Verify access token and return user
        """
        try:
            # Validate access token
            payload = jwt_service.validate_token_for_type(access_token, "access")
            user_id = payload["sub"]
            
            # Get user
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_id(uuid.UUID(user_id))
            
            if not user or not user.is_active:
                logger.warning(f"Access token verification failed - invalid user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Access token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    async def logout_all_sessions(self, user_id: uuid.UUID, session: AsyncSession) -> int:
        """
        Logout all sessions for a user (security action)
        """
        try:
            session_repo = UserSessionRepository(session)
            blacklist_repo = TokenBlacklistRepository(session)
            
            # Deactivate all sessions
            deactivated_count = await session_repo.deactivate_user_sessions(user_id)
            
            # Blacklist all tokens
            blacklisted_count = await blacklist_repo.blacklist_user_tokens(
                user_id=user_id,
                reason="logout_all_sessions"
            )
            
            await session.commit()
            
            logger.info(f"Logged out all sessions for user {user_id}: {deactivated_count} sessions, {blacklisted_count} tokens")
            
            return deactivated_count
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error logging out all sessions for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout all sessions"
            )
    
    async def _cleanup_old_sessions(self, user_id: uuid.UUID, session_repo: UserSessionRepository):
        """
        Clean up old sessions if user has too many active
        """
        try:
            # This is a simplified version - in production you might want to
            # keep the N most recent sessions and deactivate older ones
            await session_repo.cleanup_expired_sessions()
            
            # Could implement logic here to limit concurrent sessions per user
            # For now, we'll allow unlimited sessions but clean expired ones
            
        except Exception as e:
            logger.error(f"Error cleaning up old sessions for user {user_id}: {e}")
            # Don't fail the login for session cleanup issues


# Global authentication service instance
auth_service = AuthenticationService()