"""
Authentication module for CoinLink MVP
Production-ready authentication with JWT, BCrypt, and database sessions
"""

from .jwt import jwt_service, extract_bearer_token, get_current_user_id
from .hashing import password_service, hash_password, verify_password, needs_password_rehash, generate_secure_token
from .service import auth_service
from .routes_v2 import router as auth_router_v2

__all__ = [
    # JWT service
    "jwt_service",
    "extract_bearer_token", 
    "get_current_user_id",
    
    # Password hashing service
    "password_service",
    "hash_password",
    "verify_password", 
    "needs_password_rehash",
    "generate_secure_token",
    
    # Authentication service
    "auth_service",
    
    # API routes
    "auth_router_v2",
]
