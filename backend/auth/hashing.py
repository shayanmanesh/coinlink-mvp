"""
Password hashing service using BCrypt
Production-ready password security with configurable rounds
"""

import logging
from typing import Optional, Union
import secrets
import time
from passlib.context import CryptContext
from passlib.hash import bcrypt

logger = logging.getLogger(__name__)

class PasswordHashingService:
    """
    Production password hashing service using BCrypt
    Configurable rounds with performance monitoring
    """
    
    def __init__(self, rounds: int = 12):
        """
        Initialize password hashing service
        
        Args:
            rounds: BCrypt rounds (4-31). Higher = more secure but slower.
                   12 rounds ≈ 250ms, 13 rounds ≈ 500ms, 14 rounds ≈ 1000ms
        """
        self.rounds = max(4, min(31, rounds))  # Clamp to valid range
        
        # Create passlib context for secure password hashing
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=self.rounds,
            bcrypt__ident="2b"  # Use $2b$ variant (recommended)
        )
        
        logger.info(f"Password hashing service initialized with {self.rounds} BCrypt rounds")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using BCrypt
        Returns BCrypt hash string
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) > 512:
            raise ValueError("Password is too long (max 512 characters)")
        
        start_time = time.time()
        
        try:
            # Generate hash with salt
            password_hash = self.pwd_context.hash(password)
            
            # Log performance metrics
            hash_time = (time.time() - start_time) * 1000
            logger.debug(f"Password hashed in {hash_time:.2f}ms with {self.rounds} rounds")
            
            # Warn if hashing is too slow (may impact response times)
            if hash_time > 1000:  # 1 second
                logger.warning(f"Password hashing took {hash_time:.2f}ms - consider reducing rounds")
            
            return password_hash
            
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise RuntimeError(f"Failed to hash password: {str(e)}")
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        Returns True if password matches, False otherwise
        """
        if not password or not hashed_password:
            return False
        
        start_time = time.time()
        
        try:
            # Use constant-time comparison
            is_valid = self.pwd_context.verify(password, hashed_password)
            
            # Log performance metrics
            verify_time = (time.time() - start_time) * 1000
            logger.debug(f"Password verified in {verify_time:.2f}ms")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            # Return False on error to prevent bypassing authentication
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be updated
        Returns True if rehashing is recommended
        """
        try:
            return self.pwd_context.needs_update(hashed_password)
        except Exception as e:
            logger.error(f"Error checking if password needs rehash: {e}")
            return False
    
    def get_hash_info(self, hashed_password: str) -> dict:
        """
        Get information about a password hash
        Returns dict with hash details
        """
        try:
            hash_info = self.pwd_context.identify(hashed_password)
            
            # Extract BCrypt-specific information
            if hash_info == "bcrypt":
                # Parse BCrypt hash format: $2b$rounds$salt+hash
                parts = hashed_password.split('$')
                if len(parts) >= 4:
                    rounds = int(parts[2]) if parts[2].isdigit() else None
                    return {
                        "algorithm": "bcrypt",
                        "rounds": rounds,
                        "variant": parts[1] if len(parts) > 1 else None,
                        "needs_update": self.needs_rehash(hashed_password)
                    }
            
            return {
                "algorithm": hash_info or "unknown",
                "needs_update": self.needs_rehash(hashed_password)
            }
            
        except Exception as e:
            logger.error(f"Error getting hash info: {e}")
            return {"algorithm": "unknown", "error": str(e)}
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure random token
        Useful for reset tokens, API keys, etc.
        """
        if length < 1 or length > 128:
            raise ValueError("Token length must be between 1 and 128")
        
        return secrets.token_urlsafe(length)
    
    def time_hash_operation(self, password: str = "test_password_123!") -> dict:
        """
        Benchmark password hashing performance
        Returns timing statistics
        """
        times = []
        iterations = 5
        
        logger.info(f"Benchmarking password hashing with {self.rounds} rounds...")
        
        for i in range(iterations):
            start = time.time()
            test_hash = self.hash_password(password)
            hash_time = (time.time() - start) * 1000
            times.append(hash_time)
            
            # Verify the hash works
            verify_start = time.time()
            is_valid = self.verify_password(password, test_hash)
            verify_time = (time.time() - verify_start) * 1000
            
            if not is_valid:
                logger.error(f"Hash verification failed on iteration {i+1}")
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        benchmark_result = {
            "rounds": self.rounds,
            "iterations": iterations,
            "avg_hash_time_ms": round(avg_time, 2),
            "min_hash_time_ms": round(min_time, 2),
            "max_hash_time_ms": round(max_time, 2),
            "recommended": avg_time < 500,  # < 500ms is reasonable
            "performance_rating": self._get_performance_rating(avg_time)
        }
        
        logger.info(f"Hash benchmark: {avg_time:.2f}ms average ({self._get_performance_rating(avg_time)})")
        
        return benchmark_result
    
    def _get_performance_rating(self, avg_time_ms: float) -> str:
        """Get human-readable performance rating"""
        if avg_time_ms < 100:
            return "excellent"
        elif avg_time_ms < 250:
            return "good"
        elif avg_time_ms < 500:
            return "acceptable"
        elif avg_time_ms < 1000:
            return "slow"
        else:
            return "very_slow"


# Global password hashing service instance
# 12 rounds = ~250ms, good balance of security and performance
password_service = PasswordHashingService(rounds=12)


def hash_password(password: str) -> str:
    """Convenience function for hashing passwords"""
    return password_service.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Convenience function for verifying passwords"""
    return password_service.verify_password(password, hashed_password)


def needs_password_rehash(hashed_password: str) -> bool:
    """Convenience function for checking if password needs rehashing"""
    return password_service.needs_rehash(hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Convenience function for generating secure tokens"""
    return password_service.generate_secure_token(length)