"""
FastAPI routes for simple authentication
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict
from .simple_auth import auth

router = APIRouter()

class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[Dict] = None

def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract and verify token from Authorization header"""
    if not authorization:
        return None
    
    # Expected format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    return auth.verify_token(token)

@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """
    Fast signup endpoint - creates account immediately
    """
    success, message, token = auth.signup(request.email, request.password)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    user_info = auth.get_user_info(request.email)
    
    return AuthResponse(
        success=True,
        message=message,
        token=token,
        user=user_info
    )

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login endpoint
    """
    success, message, token = auth.login(request.email, request.password)
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    user_info = auth.get_user_info(request.email)
    
    return AuthResponse(
        success=True,
        message=message,
        token=token,
        user=user_info
    )

@router.get("/verify")
async def verify_auth(current_user: Optional[str] = Depends(get_current_user)):
    """
    Verify if user is authenticated
    """
    if current_user:
        return {
            "authenticated": True,
            "email": current_user,
            "user": auth.get_user_info(current_user)
        }
    else:
        return {
            "authenticated": False,
            "email": None,
            "user": None
        }

@router.get("/rate-limit")
async def check_rate_limit(
    current_user: Optional[str] = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Check current rate limit status
    """
    # Use email as identifier for authenticated users, IP/session for anonymous
    if current_user:
        identifier = f"user:{current_user}"
        is_authenticated = True
    else:
        # In production, use IP address or session ID
        identifier = "anonymous:default"
        is_authenticated = False
    
    allowed, message, info = auth.check_rate_limit(identifier, is_authenticated)
    
    return {
        "allowed": allowed,
        "message": message,
        **info
    }