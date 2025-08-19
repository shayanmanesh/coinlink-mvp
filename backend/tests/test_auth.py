"""
Unit tests for authentication functionality
Tests JWT service, password hashing, and auth routes
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from ..auth.jwt import jwt_service, extract_bearer_token, get_current_user_id
from ..auth.hashing import password_service, hash_password, verify_password
from ..auth.service import auth_service
from ..db.schemas import UserCreate, UserLogin


class TestJWTService:
    """Test JWT service functionality"""
    
    @pytest.mark.unit
    def test_create_access_token(self):
        """Test access token creation"""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        token = jwt_service.create_access_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        payload = jwt_service.decode_token(token)
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["type"] == "access"
        assert payload["iss"] == "coinlink-api"
    
    @pytest.mark.unit
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        token = jwt_service.create_refresh_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        payload = jwt_service.decode_token(token)
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["type"] == "refresh"
        assert payload["iss"] == "coinlink-api"
    
    @pytest.mark.unit
    def test_create_token_pair(self):
        """Test token pair creation"""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        token_pair = jwt_service.create_token_pair(user_id, email)
        
        assert "access_token" in token_pair
        assert "refresh_token" in token_pair
        assert token_pair["token_type"] == "bearer"
        assert token_pair["expires_in"] > 0
        
        # Verify both tokens decode correctly
        access_payload = jwt_service.decode_token(token_pair["access_token"])
        refresh_payload = jwt_service.decode_token(token_pair["refresh_token"])
        
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert access_payload["sub"] == user_id
        assert refresh_payload["sub"] == user_id
    
    @pytest.mark.unit
    def test_decode_token_validation(self):
        """Test token validation during decode"""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        # Valid token
        token = jwt_service.create_access_token(user_id, email)
        payload = jwt_service.decode_token(token)
        assert payload["sub"] == user_id
        
        # Invalid token
        with pytest.raises(Exception):
            jwt_service.decode_token("invalid-token")
        
        # Expired token (mock)
        with patch('jwt.decode') as mock_decode:
            from jwt.exceptions import ExpiredSignatureError
            mock_decode.side_effect = ExpiredSignatureError()
            
            with pytest.raises(ExpiredSignatureError):
                jwt_service.decode_token(token)
    
    @pytest.mark.unit
    def test_validate_token_for_type(self):
        """Test token type validation"""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        access_token = jwt_service.create_access_token(user_id, email)
        refresh_token = jwt_service.create_refresh_token(user_id, email)
        
        # Valid type validation
        payload = jwt_service.validate_token_for_type(access_token, "access")
        assert payload["type"] == "access"
        
        payload = jwt_service.validate_token_for_type(refresh_token, "refresh")
        assert payload["type"] == "refresh"
        
        # Invalid type validation
        with pytest.raises(Exception):
            jwt_service.validate_token_for_type(access_token, "refresh")
    
    @pytest.mark.unit
    def test_extract_bearer_token(self):
        """Test bearer token extraction"""
        token = "test-token-123"
        
        # Valid bearer format
        auth_header = f"Bearer {token}"
        extracted = extract_bearer_token(auth_header)
        assert extracted == token
        
        # Invalid formats
        assert extract_bearer_token("Invalid format") is None
        assert extract_bearer_token("") is None
        assert extract_bearer_token("Bearer") is None
        assert extract_bearer_token("Basic token") is None
    
    @pytest.mark.unit
    def test_get_current_user_id(self):
        """Test user ID extraction from authorization header"""
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        
        # Create valid token
        token = jwt_service.create_access_token(user_id, email)
        auth_header = f"Bearer {token}"
        
        extracted_user_id = get_current_user_id(auth_header)
        assert extracted_user_id == user_id
        
        # Invalid authorization
        assert get_current_user_id("") is None
        assert get_current_user_id("Invalid") is None


class TestPasswordService:
    """Test password hashing functionality"""
    
    @pytest.mark.unit
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        
        password_hash = password_service.hash_password(password)
        
        assert isinstance(password_hash, str)
        assert len(password_hash) > 0
        assert password_hash != password  # Should be hashed
        assert password_hash.startswith("$2b$")  # BCrypt format
    
    @pytest.mark.unit
    def test_verify_password(self):
        """Test password verification"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        
        password_hash = password_service.hash_password(password)
        
        # Correct password
        assert password_service.verify_password(password, password_hash) is True
        
        # Wrong password
        assert password_service.verify_password(wrong_password, password_hash) is False
        
        # Empty inputs
        assert password_service.verify_password("", password_hash) is False
        assert password_service.verify_password(password, "") is False
    
    @pytest.mark.unit
    def test_needs_rehash(self):
        """Test password rehash detection"""
        password = "TestPassword123!"
        password_hash = password_service.hash_password(password)
        
        # Fresh hash shouldn't need rehashing
        assert password_service.needs_rehash(password_hash) is False
    
    @pytest.mark.unit
    def test_convenience_functions(self):
        """Test convenience functions"""
        password = "TestPassword123!"
        
        # Test convenience hash function
        password_hash = hash_password(password)
        assert isinstance(password_hash, str)
        
        # Test convenience verify function
        assert verify_password(password, password_hash) is True
        assert verify_password("wrong", password_hash) is False
    
    @pytest.mark.unit
    def test_hash_validation(self):
        """Test password hash validation"""
        # Empty password
        with pytest.raises(ValueError):
            password_service.hash_password("")
        
        # Password too long
        with pytest.raises(ValueError):
            password_service.hash_password("a" * 513)
    
    @pytest.mark.unit
    def test_generate_secure_token(self):
        """Test secure token generation"""
        token = password_service.generate_secure_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Custom length
        token_custom = password_service.generate_secure_token(16)
        assert len(token_custom) > 0
        
        # Two tokens should be different
        token2 = password_service.generate_secure_token()
        assert token != token2


class TestAuthService:
    """Test authentication service functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_signup_validation(self, db_session):
        """Test user signup validation"""
        # Valid signup data
        valid_data = UserCreate(
            email="test@example.com",
            password="TestPassword123!",
            confirm_password="TestPassword123!",
            first_name="Test",
            last_name="User"
        )
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
            
            # Mock user repository
            with patch('..auth.service.UserRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo_class.return_value = mock_repo
                
                # Mock user creation
                mock_user = MagicMock()
                mock_user.id = uuid.UUID('12345678-1234-5678-9012-123456789012')
                mock_user.email = valid_data.email
                mock_repo.create_user.return_value = mock_user
                
                # Mock session repository
                with patch('..auth.service.UserSessionRepository') as mock_session_repo_class:
                    mock_session_repo = MagicMock()
                    mock_session_repo_class.return_value = mock_session_repo
                    mock_session_repo.create_session.return_value = MagicMock()
                    
                    result = await auth_service.signup(
                        signup_data=valid_data,
                        session=db_session,
                        ip_address="127.0.0.1",
                        user_agent="test"
                    )
                    
                    assert result is not None
                    assert result.user.email == valid_data.email
                    assert result.tokens.token_type == "bearer"
    
    @pytest.mark.asyncio
    @pytest.mark.unit  
    async def test_login_validation(self, db_session):
        """Test user login validation"""
        login_data = UserLogin(
            email="test@example.com",
            password="TestPassword123!"
        )
        
        # Mock user repository
        with patch('..auth.service.UserRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            
            # Mock user retrieval
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.email = login_data.email
            mock_user.is_active = True
            mock_user.password_hash = hash_password(login_data.password)
            mock_user.last_login_at = None
            mock_user.created_at = datetime.now()
            mock_repo.get_user_by_email.return_value = mock_user
            mock_repo.update_last_login.return_value = True
            
            # Mock session repository
            with patch('..auth.service.UserSessionRepository') as mock_session_repo_class:
                mock_session_repo = MagicMock()
                mock_session_repo_class.return_value = mock_session_repo
                mock_session_repo.create_session.return_value = MagicMock()
                
                # Mock password rehash check
                with patch('..auth.service.password_service.needs_rehash', return_value=False):
                    result = await auth_service.login(
                        login_data=login_data,
                        session=db_session,
                        ip_address="127.0.0.1",
                        user_agent="test"
                    )
                    
                    assert result is not None
                    assert result.user.email == login_data.email
                    assert result.tokens.token_type == "bearer"


@pytest.mark.integration
@pytest.mark.auth
class TestAuthRoutes:
    """Integration tests for auth API routes"""
    
    @pytest.mark.asyncio
    async def test_signup_endpoint(self, async_client, sample_user_data):
        """Test user signup endpoint"""
        response = await async_client.post("/api/v2/auth/signup", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert data["tokens"]["token_type"] == "bearer"
        assert len(data["tokens"]["access_token"]) > 0
        assert len(data["tokens"]["refresh_token"]) > 0
    
    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, async_client, sample_user_data):
        """Test signup with duplicate email"""
        # First signup
        response1 = await async_client.post("/api/v2/auth/signup", json=sample_user_data)
        assert response1.status_code == 201
        
        # Second signup with same email
        response2 = await async_client.post("/api/v2/auth/signup", json=sample_user_data)
        assert response2.status_code == 400
    
    @pytest.mark.asyncio
    async def test_signup_validation(self, async_client):
        """Test signup input validation"""
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",
            "confirm_password": "different",
        }
        
        response = await async_client.post("/api/v2/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_login_endpoint(self, async_client, test_user):
        """Test user login endpoint"""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        response = await async_client.post("/api/v2/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == test_user.email
        assert data["tokens"]["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client, test_user):
        """Test login with invalid credentials"""
        login_data = {
            "email": test_user.email,
            "password": "WrongPassword123!"
        }
        
        response = await async_client.post("/api/v2/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, async_client, test_user):
        """Test token refresh endpoint"""
        # First login to get refresh token
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        login_response = await async_client.post("/api/v2/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()["tokens"]
        refresh_token = tokens["refresh_token"]
        
        # Refresh tokens
        refresh_data = {"refresh_token": refresh_token}
        response = await async_client.post("/api/v2/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["access_token"] != tokens["access_token"]  # New token
    
    @pytest.mark.asyncio
    async def test_logout_endpoint(self, async_client, test_user):
        """Test logout endpoint"""
        # First login
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        
        login_response = await async_client.post("/api/v2/auth/login", json=login_data)
        tokens = login_response.json()["tokens"]
        
        # Logout
        logout_data = {"refresh_token": tokens["refresh_token"]}
        response = await async_client.post("/api/v2/auth/logout", json=logout_data)
        
        assert response.status_code == 200
        assert "message" in response.json()
    
    @pytest.mark.asyncio
    async def test_verify_token_endpoint(self, async_client, auth_headers):
        """Test token verification endpoint"""
        response = await async_client.get("/api/v2/auth/verify", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "message" in data
        assert data["message"] == "Token is valid"
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, async_client):
        """Test verification with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = await async_client.get("/api/v2/auth/verify", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_auth_health_endpoint(self, async_client):
        """Test auth service health check"""
        response = await async_client.get("/api/v2/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "checks" in data