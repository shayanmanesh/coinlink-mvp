"""
JWT token creation, validation, and management
Production-ready JWT service with access/refresh token pairs
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
import jwt
import uuid
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, InvalidSignatureError

from ..config.settings import settings

logger = logging.getLogger(__name__)

class JWTService:
    """Production JWT service with token rotation and blacklist support"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        
        # Token lifetimes
        self.access_token_lifetime = timedelta(minutes=15)  # Short-lived for security
        self.refresh_token_lifetime = timedelta(days=7)     # Longer-lived but rotated
        
        # Issuer for token validation
        self.issuer = "coinlink-api"
        
    def create_access_token(self, user_id: str, user_email: str, jti: str = None) -> str:
        """
        Create a short-lived access token
        JTI is optional for access tokens (usually not tracked in DB)
        """
        if jti is None:
            jti = str(uuid.uuid4())
        
        now = datetime.utcnow()
        payload = {
            # Standard JWT claims
            "iss": self.issuer,
            "sub": str(user_id),  # User ID as subject
            "jti": jti,           # JWT ID for revocation
            "iat": now,           # Issued at
            "exp": now + self.access_token_lifetime,  # Expires at
            "nbf": now,           # Not before
            
            # Custom claims
            "type": "access",
            "email": user_email,
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created access token for user {user_id} with JTI {jti}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token for user {user_id}: {e}")
            raise RuntimeError(f"Failed to create access token: {str(e)}")
    
    def create_refresh_token(self, user_id: str, user_email: str, jti: str = None) -> str:
        """
        Create a refresh token for obtaining new access tokens
        JTI is required for refresh tokens (tracked in DB for revocation)
        """
        if jti is None:
            jti = str(uuid.uuid4())
        
        now = datetime.utcnow()
        payload = {
            # Standard JWT claims  
            "iss": self.issuer,
            "sub": str(user_id),
            "jti": jti,
            "iat": now,
            "exp": now + self.refresh_token_lifetime,
            "nbf": now,
            
            # Custom claims
            "type": "refresh",
            "email": user_email,
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created refresh token for user {user_id} with JTI {jti}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating refresh token for user {user_id}: {e}")
            raise RuntimeError(f"Failed to create refresh token: {str(e)}")
    
    def create_token_pair(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """
        Create both access and refresh tokens
        Returns token pair with metadata
        """
        try:
            # Generate unique JTIs
            access_jti = str(uuid.uuid4())
            refresh_jti = str(uuid.uuid4())
            
            # Create both tokens
            access_token = self.create_access_token(user_id, user_email, access_jti)
            refresh_token = self.create_refresh_token(user_id, user_email, refresh_jti)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": int(self.access_token_lifetime.total_seconds()),
                "refresh_expires_in": int(self.refresh_token_lifetime.total_seconds()),
                "access_jti": access_jti,
                "refresh_jti": refresh_jti
            }
            
        except Exception as e:
            logger.error(f"Error creating token pair for user {user_id}: {e}")
            raise RuntimeError(f"Failed to create token pair: {str(e)}")
    
    def decode_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """
        Decode and validate a JWT token
        Returns payload if valid, raises exception if invalid
        """
        try:
            options = {
                "verify_exp": verify_exp,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_signature": True,
                "verify_iss": True
            }
            
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                options=options
            )
            
            # Validate token type
            token_type = payload.get("type")
            if token_type not in ["access", "refresh"]:
                raise InvalidTokenError(f"Invalid token type: {token_type}")
            
            # Validate required claims
            required_claims = ["sub", "jti", "email", "type"]
            missing_claims = [claim for claim in required_claims if claim not in payload]
            if missing_claims:
                raise InvalidTokenError(f"Missing required claims: {missing_claims}")
            
            logger.debug(f"Successfully decoded {token_type} token for user {payload['sub']}")
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except InvalidSignatureError:
            logger.error("Token has invalid signature")
            raise
        except InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error decoding token: {e}")
            raise InvalidTokenError(f"Token decode error: {str(e)}")
    
    def get_token_claims(self, token: str, verify_exp: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get token claims safely (returns None on any error)
        Useful for optional token validation
        """
        try:
            return self.decode_token(token, verify_exp=verify_exp)
        except Exception as e:
            logger.debug(f"Token claims extraction failed: {e}")
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without raising exceptions
        Returns True if expired, False if valid, None if can't determine
        """
        try:
            # Try to decode without exp verification first to get claims
            payload = self.decode_token(token, verify_exp=False)
            
            # Check expiration manually
            exp = payload.get("exp")
            if not exp:
                return None  # No exp claim
            
            return datetime.utcnow().timestamp() > exp
            
        except Exception:
            return None  # Can't determine
    
    def get_token_jti(self, token: str) -> Optional[str]:
        """Get JTI from token safely"""
        try:
            payload = self.decode_token(token, verify_exp=False)
            return payload.get("jti")
        except Exception:
            return None
    
    def get_token_user_id(self, token: str) -> Optional[str]:
        """Get user ID from token safely"""
        try:
            payload = self.decode_token(token, verify_exp=False)
            return payload.get("sub")
        except Exception:
            return None
    
    def get_token_type(self, token: str) -> Optional[str]:
        """Get token type (access/refresh) safely"""
        try:
            payload = self.decode_token(token, verify_exp=False)
            return payload.get("type")
        except Exception:
            return None
    
    def validate_token_for_type(self, token: str, expected_type: str) -> Dict[str, Any]:
        """
        Validate token and ensure it's the expected type
        Raises exception if invalid or wrong type
        """
        payload = self.decode_token(token)
        
        actual_type = payload.get("type")
        if actual_type != expected_type:
            raise InvalidTokenError(f"Expected {expected_type} token, got {actual_type}")
        
        return payload
    
    def create_password_reset_token(self, user_id: str, user_email: str) -> str:
        """
        Create a password reset token (short-lived, single-use)
        """
        jti = str(uuid.uuid4())
        now = datetime.utcnow()
        
        payload = {
            "iss": self.issuer,
            "sub": str(user_id),
            "jti": jti,
            "iat": now,
            "exp": now + timedelta(minutes=30),  # Very short-lived
            "nbf": now,
            "type": "password_reset",
            "email": user_email,
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Created password reset token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Error creating password reset token: {e}")
            raise RuntimeError(f"Failed to create password reset token: {str(e)}")
    
    def create_email_verification_token(self, user_id: str, user_email: str) -> str:
        """
        Create an email verification token
        """
        jti = str(uuid.uuid4())
        now = datetime.utcnow()
        
        payload = {
            "iss": self.issuer,
            "sub": str(user_id),
            "jti": jti,
            "iat": now,
            "exp": now + timedelta(hours=24),  # 24 hour expiry
            "nbf": now,
            "type": "email_verification",
            "email": user_email,
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Created email verification token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Error creating email verification token: {e}")
            raise RuntimeError(f"Failed to create email verification token: {str(e)}")


# Global JWT service instance
jwt_service = JWTService()


def extract_bearer_token(authorization: str) -> Optional[str]:
    """
    Extract bearer token from Authorization header
    Returns None if invalid format
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


def get_current_user_id(authorization: str) -> Optional[str]:
    """
    Extract current user ID from Authorization header
    Returns None if invalid token or not authenticated
    """
    token = extract_bearer_token(authorization)
    if not token:
        return None
    
    return jwt_service.get_token_user_id(token)