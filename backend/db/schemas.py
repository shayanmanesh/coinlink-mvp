"""
Pydantic schemas for database models
Request/response models with validation
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid
import re

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=100, description="User first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User last name")

class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=12, max_length=512, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        
        if len(v) > 512:
            raise ValueError('Password cannot exceed 512 characters')
        
        # Check for required character types
        has_upper = bool(re.search(r'[A-Z]', v))
        has_lower = bool(re.search(r'[a-z]', v))
        has_digit = bool(re.search(r'\d', v))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))
        
        if not has_upper:
            raise ValueError('Password must contain at least one uppercase letter')
        if not has_lower:
            raise ValueError('Password must contain at least one lowercase letter')
        if not has_digit:
            raise ValueError('Password must contain at least one digit')
        if not has_special:
            raise ValueError('Password must contain at least one special character')
        
        # Check for control characters and other dangerous patterns
        if re.search(r'[\x00-\x1F\x7F]', v):
            raise ValueError('Password contains invalid characters')
        
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Ensure password and confirm_password match"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Additional email validation beyond EmailStr"""
        if len(v) > 254:
            raise ValueError('Email address is too long')
        
        # Basic sanity checks
        if v.count('@') != 1:
            raise ValueError('Invalid email format')
        
        local, domain = v.split('@')
        if len(local) == 0 or len(domain) == 0:
            raise ValueError('Invalid email format')
        
        # Check for dangerous characters
        if re.search(r'[<>"\\\x00-\x1F]', v):
            raise ValueError('Email contains invalid characters')
        
        return v.lower().strip()

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=512, description="User password")
    
    @field_validator('email')
    @classmethod
    def normalize_email(cls, v):
        """Normalize email for consistent login"""
        return v.lower().strip()

class UserResponse(UserBase):
    """Schema for user response (public fields only)"""
    id: uuid.UUID = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for user updates"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class TokenPair(BaseModel):
    """Schema for JWT token pair"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

class AuthResponse(BaseModel):
    """Schema for authentication response"""
    user: UserResponse = Field(..., description="User information")
    tokens: TokenPair = Field(..., description="JWT tokens")
    message: str = Field(..., description="Success message")

class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., description="JWT refresh token")

class RefreshTokenResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

class LogoutRequest(BaseModel):
    """Schema for logout request"""
    refresh_token: str = Field(..., description="JWT refresh token to invalidate")

class LogoutResponse(BaseModel):
    """Schema for logout response"""
    message: str = Field(..., description="Logout confirmation message")

class UserVerificationResponse(BaseModel):
    """Schema for user verification response"""
    user: UserResponse = Field(..., description="Verified user information")
    message: str = Field(..., description="Verification message")

class RateLimitInfo(BaseModel):
    """Schema for rate limit information"""
    endpoint: str = Field(..., description="API endpoint")
    limit: int = Field(..., description="Rate limit (requests per window)")
    window_seconds: int = Field(..., description="Rate limit window in seconds")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset_at: datetime = Field(..., description="When the window resets")

class RateLimitResponse(BaseModel):
    """Schema for rate limit check response"""
    user_limits: List[RateLimitInfo] = Field(..., description="User-specific rate limits")
    ip_limits: List[RateLimitInfo] = Field(..., description="IP-based rate limits")
    global_limit: RateLimitInfo = Field(..., description="Global rate limit")

class ErrorDetail(BaseModel):
    """Schema for error details"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")

class ErrorResponse(BaseModel):
    """Standardized error response schema"""
    error: dict = Field(..., description="Error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "validation_error",
                    "message": "Invalid request data",
                    "details": [
                        {
                            "field": "email",
                            "message": "Invalid email format",
                            "code": "invalid_format"
                        }
                    ],
                    "trace_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }

class UserSessionResponse(BaseModel):
    """Schema for user session information"""
    id: uuid.UUID = Field(..., description="Session ID")
    user_id: uuid.UUID = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether session is active")
    user_agent: Optional[str] = Field(None, description="User agent from login")
    ip_address: Optional[str] = Field(None, description="IP address from login")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last session usage")
    
    class Config:
        from_attributes = True

class UserSessionsList(BaseModel):
    """Schema for user sessions list"""
    sessions: List[UserSessionResponse] = Field(..., description="User sessions")
    total: int = Field(..., description="Total number of sessions")
    active: int = Field(..., description="Number of active sessions")

# Password reset schemas (for future implementation)
class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr = Field(..., description="User email for password reset")

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=12, max_length=512, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Reuse password validation from UserCreate"""
        return UserCreate.validate_password_strength(v)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Ensure passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=12, max_length=512, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Reuse password validation from UserCreate"""
        return UserCreate.validate_password_strength(v)
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Ensure passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v