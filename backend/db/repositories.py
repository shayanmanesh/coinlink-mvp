"""
Database repositories for CRUD operations
Async repositories with error handling and logging
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import uuid

from .models import User, UserSession, TokenBlacklist

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for User CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(self, email: str, password_hash: str, **kwargs) -> Optional[User]:
        """
        Create a new user
        Returns None if email already exists
        """
        try:
            user = User(
                email=email.lower().strip(),
                password_hash=password_hash,
                **kwargs
            )
            
            self.session.add(user)
            await self.session.flush()  # Get the ID without committing
            
            logger.info(f"Created user: {user.id} ({email})")
            return user
            
        except IntegrityError as e:
            await self.session.rollback()
            if "unique constraint" in str(e).lower() and "email" in str(e).lower():
                logger.warning(f"Attempted to create user with existing email: {email}")
                return None
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating user {email}: {e}")
            raise
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case insensitive)"""
        try:
            result = await self.session.execute(
                select(User).where(func.lower(User.email) == email.lower().strip())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def update_user(self, user_id: uuid.UUID, **kwargs) -> Optional[User]:
        """Update user fields"""
        try:
            # Remove None values
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            update_data['updated_at'] = datetime.utcnow()
            
            result = await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
                .returning(User)
            )
            
            updated_user = result.scalar_one_or_none()
            if updated_user:
                logger.info(f"Updated user: {user_id}")
            
            return updated_user
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    async def update_last_login(self, user_id: uuid.UUID) -> bool:
        """Update user's last login timestamp"""
        try:
            result = await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_login_at=datetime.utcnow(), updated_at=datetime.utcnow())
            )
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
    
    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        """Deactivate user account"""
        try:
            result = await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            
            if result.rowcount > 0:
                logger.info(f"Deactivated user: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e}")
            return False
    
    async def list_users(self, limit: int = 100, offset: int = 0, active_only: bool = True) -> List[User]:
        """List users with pagination"""
        try:
            query = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
            
            if active_only:
                query = query.where(User.is_active == True)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []


class UserSessionRepository:
    """Repository for UserSession operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_session(self, user_id: uuid.UUID, jti: str, expires_at: datetime, 
                           user_agent: str = None, ip_address: str = None) -> Optional[UserSession]:
        """Create a new user session"""
        try:
            session = UserSession(
                user_id=user_id,
                jti=jti,
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            self.session.add(session)
            await self.session.flush()
            
            logger.info(f"Created session: {session.id} for user {user_id}")
            return session
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating session for user {user_id}: {e}")
            raise
    
    async def get_session_by_jti(self, jti: str) -> Optional[UserSession]:
        """Get session by JWT ID"""
        try:
            result = await self.session.execute(
                select(UserSession).where(
                    and_(UserSession.jti == jti, UserSession.is_active == True)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting session by JTI {jti}: {e}")
            return None
    
    async def update_session_last_used(self, jti: str) -> bool:
        """Update session last used timestamp"""
        try:
            result = await self.session.execute(
                update(UserSession)
                .where(UserSession.jti == jti)
                .values(last_used_at=datetime.utcnow())
            )
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating session last used {jti}: {e}")
            return False
    
    async def deactivate_session(self, jti: str) -> bool:
        """Deactivate a session (logout)"""
        try:
            result = await self.session.execute(
                update(UserSession)
                .where(UserSession.jti == jti)
                .values(is_active=False)
            )
            
            if result.rowcount > 0:
                logger.info(f"Deactivated session: {jti}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deactivating session {jti}: {e}")
            return False
    
    async def deactivate_user_sessions(self, user_id: uuid.UUID, exclude_jti: str = None) -> int:
        """Deactivate all sessions for a user (optionally excluding one)"""
        try:
            query = update(UserSession).where(
                and_(UserSession.user_id == user_id, UserSession.is_active == True)
            )
            
            if exclude_jti:
                query = query.where(UserSession.jti != exclude_jti)
            
            result = await self.session.execute(query.values(is_active=False))
            
            deactivated_count = result.rowcount
            if deactivated_count > 0:
                logger.info(f"Deactivated {deactivated_count} sessions for user {user_id}")
            
            return deactivated_count
            
        except Exception as e:
            logger.error(f"Error deactivating sessions for user {user_id}: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            result = await self.session.execute(
                delete(UserSession).where(UserSession.expires_at < datetime.utcnow())
            )
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired sessions")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0


class TokenBlacklistRepository:
    """Repository for TokenBlacklist operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def blacklist_token(self, jti: str, token_type: str, user_id: uuid.UUID = None, 
                            reason: str = "logout", expires_at: datetime = None) -> bool:
        """Add token to blacklist"""
        try:
            if expires_at is None:
                # Default expiration based on token type
                if token_type == "access":
                    expires_at = datetime.utcnow() + timedelta(hours=1)  # Access tokens expire quickly
                else:
                    expires_at = datetime.utcnow() + timedelta(days=8)   # Refresh tokens expire later
            
            blacklist_entry = TokenBlacklist(
                jti=jti,
                token_type=token_type,
                user_id=user_id,
                reason=reason,
                expires_at=expires_at
            )
            
            self.session.add(blacklist_entry)
            await self.session.flush()
            
            logger.info(f"Blacklisted {token_type} token: {jti} (reason: {reason})")
            return True
            
        except IntegrityError:
            # Token already blacklisted
            logger.debug(f"Token {jti} already blacklisted")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error blacklisting token {jti}: {e}")
            return False
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            result = await self.session.execute(
                select(TokenBlacklist).where(
                    and_(
                        TokenBlacklist.jti == jti,
                        TokenBlacklist.expires_at > datetime.utcnow()
                    )
                )
            )
            
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking blacklist for token {jti}: {e}")
            # If we can't check, assume it's blacklisted for safety
            return True
    
    async def cleanup_expired_blacklist(self) -> int:
        """Clean up expired blacklist entries"""
        try:
            result = await self.session.execute(
                delete(TokenBlacklist).where(TokenBlacklist.expires_at < datetime.utcnow())
            )
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired blacklist entries")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired blacklist entries: {e}")
            return 0
    
    async def blacklist_user_tokens(self, user_id: uuid.UUID, reason: str = "user_deactivated") -> int:
        """Blacklist all active tokens for a user"""
        try:
            # Get all active sessions for the user
            sessions_result = await self.session.execute(
                select(UserSession).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.utcnow()
                    )
                )
            )
            
            sessions = sessions_result.scalars().all()
            blacklisted_count = 0
            
            for session in sessions:
                if await self.blacklist_token(
                    jti=session.jti,
                    token_type="refresh",
                    user_id=user_id,
                    reason=reason,
                    expires_at=session.expires_at
                ):
                    blacklisted_count += 1
            
            logger.info(f"Blacklisted {blacklisted_count} tokens for user {user_id}")
            return blacklisted_count
            
        except Exception as e:
            logger.error(f"Error blacklisting tokens for user {user_id}: {e}")
            return 0