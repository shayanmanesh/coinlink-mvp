import re
import hashlib
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RegistrationFlow:
    def __init__(self):
        self.states = {}  # {session_id: {step, email, password, created_at}}
        self.pending_users = {}  # {email: {password_hash, token, created_at}}
        self.cleanup_interval = 3600  # 1 hour
    
    def get_step(self, session_id: str) -> str:
        """Get current registration step for a session"""
        state = self.states.get(session_id, {})
        if not state:
            return 'idle'
        
        # Clean up old sessions
        created_at = state.get('created_at')
        if created_at and (datetime.now() - created_at) > timedelta(hours=1):
            del self.states[session_id]
            return 'idle'
            
        return state.get('step', 'idle')
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> bool:
        """Basic password validation"""
        return len(password) >= 8
    
    def create_verification_token(self) -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}${hash_obj.hexdigest()}"
    
    def create_user_and_send_verification(self, email: str, password: str) -> bool:
        """Create pending user and generate verification token"""
        try:
            # Hash password
            password_hash = self.hash_password(password)
            
            # Generate verification token
            token = self.create_verification_token()
            
            # Store pending user
            self.pending_users[email] = {
                'password_hash': password_hash,
                'token': token,
                'created_at': datetime.now()
            }
            
            # TODO: Send verification email
            # For MVP, just log the verification link
            verification_url = f"http://localhost:3000/auth/verify?token={token}"
            logger.info(f"Verification link for {email}: {verification_url}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False
    
    def handle_message(self, session_id: str, message: str) -> Optional[Dict]:
        """Handle registration flow messages"""
        step = self.get_step(session_id)
        
        # Initialize registration
        if message.strip().lower() == '/register':
            self.states[session_id] = {
                'step': 'email',
                'created_at': datetime.now()
            }
            return {
                'type': 'system',
                'content': 'Welcome! Please enter your email address to register:'
            }
        
        # Cancel registration
        if message.strip().lower() == '/cancel':
            if session_id in self.states:
                del self.states[session_id]
            return {
                'type': 'system',
                'content': 'Registration cancelled. Type /register to start over.'
            }
        
        # Handle email step
        elif step == 'email':
            if self.validate_email(message):
                self.states[session_id]['email'] = message
                self.states[session_id]['step'] = 'password'
                return {
                    'type': 'system',
                    'content': 'Great! Now enter your password (minimum 8 characters):'
                }
            else:
                return {
                    'type': 'system',
                    'content': 'Invalid email format. Please enter a valid email address:'
                }
        
        # Handle password step
        elif step == 'password':
            if self.validate_password(message):
                self.states[session_id]['password'] = message
                self.states[session_id]['step'] = 'confirm'
                return {
                    'type': 'system',
                    'content': 'Please re-enter your password to confirm:'
                }
            else:
                return {
                    'type': 'system',
                    'content': 'Password must be at least 8 characters. Please try again:'
                }
        
        # Handle password confirmation
        elif step == 'confirm':
            if message == self.states[session_id]['password']:
                # Create user and send verification
                email = self.states[session_id]['email']
                if self.create_user_and_send_verification(email, message):
                    del self.states[session_id]
                    return {
                        'type': 'system',
                        'content': f'✓ Registration successful! A verification link has been sent to {email}. Please check your email and click the link to activate your account.'
                    }
                else:
                    del self.states[session_id]
                    return {
                        'type': 'system',
                        'content': 'Registration failed. Please try again or contact support.'
                    }
            else:
                del self.states[session_id]
                return {
                    'type': 'system',
                    'content': "Passwords don't match. Type /register to start over."
                }
        
        return None
    
    def cleanup_expired_sessions(self):
        """Clean up expired registration sessions and pending users"""
        now = datetime.now()
        
        # Clean up expired sessions
        expired_sessions = [
            session_id for session_id, state in self.states.items()
            if state.get('created_at') and (now - state['created_at']) > timedelta(hours=1)
        ]
        for session_id in expired_sessions:
            del self.states[session_id]
        
        # Clean up expired pending users (24 hours)
        expired_users = [
            email for email, user_data in self.pending_users.items()
            if user_data.get('created_at') and (now - user_data['created_at']) > timedelta(hours=24)
        ]
        for email in expired_users:
            del self.pending_users[email]
        
        if expired_sessions or expired_users:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions and {len(expired_users)} expired pending users")
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a token and return the associated email"""
        for email, user_data in self.pending_users.items():
            if user_data.get('token') == token:
                return email
        return None
    
    def activate_user(self, email: str) -> bool:
        """Activate a verified user"""
        if email in self.pending_users:
            # TODO: Move to actual database
            user_data = self.pending_users.pop(email)
            logger.info(f"User {email} activated successfully")
            return True
        return False
