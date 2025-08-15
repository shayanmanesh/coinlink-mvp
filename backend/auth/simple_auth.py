"""
Simple authentication system with fast signup and rate limiting
"""
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import re
from collections import defaultdict
import time

class SimpleAuth:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.users = {}  # {email: {password_hash, created_at}}
        self.sessions = {}  # {token: {email, created_at, expires_at}}
        self.rate_limits = defaultdict(lambda: {"prompts": 0, "reset_at": 0})
        
        # Rate limit configurations
        self.FREE_LIMIT = 5  # 5 prompts for free users
        self.FREE_RESET_TIME = 3600  # 1 hour lock
        self.AUTH_LIMIT = 50  # 50 prompts for authenticated users
        self.AUTH_RESET_TIME = 43200  # 12 hours
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def hash_password(self, password: str) -> str:
        """Simple password hashing"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def signup(self, email: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Fast signup - creates account immediately
        Returns: (success, message, token)
        """
        # Validate email
        if not self.validate_email(email):
            return False, "Invalid email format", None
        
        # Check if user exists
        if email in self.users:
            return False, "Email already registered", None
        
        # Validate password
        if len(password) < 8:
            return False, "Password must be at least 8 characters", None
        
        # Create user
        self.users[email] = {
            "password_hash": self.hash_password(password),
            "created_at": datetime.now()
        }
        
        # Generate token
        token = self.generate_token(email)
        
        return True, "Signup successful!", token
    
    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Simple login
        Returns: (success, message, token)
        """
        # Check if user exists
        if email not in self.users:
            return False, "Invalid email or password", None
        
        # Verify password
        if self.users[email]["password_hash"] != self.hash_password(password):
            return False, "Invalid email or password", None
        
        # Generate token
        token = self.generate_token(email)
        
        return True, "Login successful!", token
    
    def generate_token(self, email: str) -> str:
        """Generate JWT token"""
        expires_at = datetime.now() + timedelta(days=7)
        payload = {
            "email": email,
            "exp": expires_at.timestamp(),
            "iat": datetime.now().timestamp()
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Store session
        self.sessions[token] = {
            "email": email,
            "created_at": datetime.now(),
            "expires_at": expires_at
        }
        
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify token and return email
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            email = payload.get("email")
            
            # Check if session exists
            if token in self.sessions:
                session = self.sessions[token]
                if session["expires_at"] > datetime.now():
                    return email
            
            return email  # Token valid even if not in session cache
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def check_rate_limit(self, identifier: str, is_authenticated: bool = False) -> Tuple[bool, str, Dict]:
        """
        Check and update rate limits
        Returns: (allowed, message, info)
        """
        current_time = time.time()
        limit_data = self.rate_limits[identifier]
        
        # Determine limits based on authentication
        max_prompts = self.AUTH_LIMIT if is_authenticated else self.FREE_LIMIT
        reset_time = self.AUTH_RESET_TIME if is_authenticated else self.FREE_RESET_TIME
        
        # Reset if time window has passed
        if current_time >= limit_data["reset_at"]:
            limit_data["prompts"] = 0
            limit_data["reset_at"] = current_time + reset_time
        
        # Check if limit exceeded
        if limit_data["prompts"] >= max_prompts:
            time_left = limit_data["reset_at"] - current_time
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            if is_authenticated:
                message = f"Rate limit reached! You've used all {max_prompts} prompts. Reset in {hours}h {minutes}m."
            else:
                message = f"Free tier limit reached! You've used all {self.FREE_LIMIT} free prompts. Please sign up for more or wait {hours}h {minutes}m."
            
            return False, message, {
                "prompts_used": limit_data["prompts"],
                "prompts_max": max_prompts,
                "reset_in_seconds": int(time_left),
                "is_authenticated": is_authenticated
            }
        
        # Increment counter
        limit_data["prompts"] += 1
        
        # Prepare info
        prompts_left = max_prompts - limit_data["prompts"]
        
        return True, f"Prompts remaining: {prompts_left}/{max_prompts}", {
            "prompts_used": limit_data["prompts"],
            "prompts_max": max_prompts,
            "prompts_left": prompts_left,
            "is_authenticated": is_authenticated
        }
    
    def get_user_info(self, email: str) -> Optional[Dict]:
        """Get user information"""
        if email in self.users:
            return {
                "email": email,
                "created_at": self.users[email]["created_at"].isoformat()
            }
        return None

# Global auth instance
auth = SimpleAuth()