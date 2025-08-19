"""
Database models for CoinLink MVP
SQLAlchemy 2.0 async models with strong typing
"""

from sqlalchemy import String, Text, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

from .database import Base

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    __table_args__ = (
        # Create index for fast email lookups
        Index('ix_users_email', 'email'),
        Index('ix_users_created_at', 'created_at'),
        {"schema": "public"}  # Explicitly specify schema
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Unique user identifier"
    )
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(254), 
        unique=True, 
        index=True,
        nullable=False,
        comment="User email address (unique)"
    )
    
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="BCrypt hashed password"
    )
    
    # User status and metadata
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user account is active"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user email is verified"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Account creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last account update timestamp"
    )
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )
    
    # Optional profile fields
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User first name"
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="User last name"
    )
    
    # Relationships (for future expansion)
    # sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary, optionally including sensitive fields"""
        user_dict = {
            "id": str(self.id),
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "first_name": self.first_name,
            "last_name": self.last_name
        }
        
        if include_sensitive:
            user_dict["password_hash"] = self.password_hash
            
        return user_dict


class UserSession(Base):
    """User session tracking for JWT refresh tokens"""
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index('ix_user_sessions_user_id', 'user_id'),
        Index('ix_user_sessions_jti', 'jti'),
        Index('ix_user_sessions_expires_at', 'expires_at'),
        {"schema": "public"}
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique session identifier"
    )
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # Uncomment when ready
        nullable=False,
        index=True,
        comment="Reference to user"
    )
    
    # JWT tracking
    jti: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True, 
        nullable=False,
        comment="JWT ID for refresh token"
    )
    
    # Session metadata
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether session is active"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User agent string from login"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address from login"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Session creation timestamp"
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Session expiration timestamp"
    )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time session was used"
    )
    
    # Relationships
    # user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    def to_dict(self) -> dict:
        """Convert session to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "jti": self.jti,
            "is_active": self.is_active,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class TokenBlacklist(Base):
    """Blacklisted JWT tokens (for logout and refresh rotation)"""
    __tablename__ = "token_blacklist"
    __table_args__ = (
        Index('ix_token_blacklist_jti', 'jti'),
        Index('ix_token_blacklist_expires_at', 'expires_at'),
        {"schema": "public"}
    )
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique blacklist entry identifier"
    )
    
    # JWT identifier
    jti: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        comment="JWT ID of blacklisted token"
    )
    
    # Token type for different handling
    token_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type of token: access or refresh"
    )
    
    # User reference
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who owned the token"
    )
    
    # Blacklist reason
    reason: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Reason for blacklisting: logout, refresh, revoke"
    )
    
    # Timestamps
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When token was blacklisted"
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When blacklist entry can be cleaned up"
    )
    
    def __repr__(self) -> str:
        return f"<TokenBlacklist(jti={self.jti}, type={self.token_type}, reason={self.reason})>"
    
    def to_dict(self) -> dict:
        """Convert blacklist entry to dictionary"""
        return {
            "id": str(self.id),
            "jti": self.jti,
            "token_type": self.token_type,
            "user_id": str(self.user_id) if self.user_id else None,
            "reason": self.reason,
            "blacklisted_at": self.blacklisted_at.isoformat() if self.blacklisted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }