"""
Test configuration and fixtures for CoinLink MVP
Production-ready test setup with database, Redis, and authentication mocking
"""

import asyncio
import os
import uuid
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Test imports
from ..api.main_production import app
from ..db.database import Base, get_async_session
from ..db.models import User
from ..auth.jwt import jwt_service
from ..auth.hashing import hash_password
from ..config.settings import settings

# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

# Create test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the database dependency"""
    async def _override():
        yield db_session
    return _override

@pytest.fixture
def client(override_get_db) -> TestClient:
    """
    Create a test client with database override
    """
    app.dependency_overrides[get_async_session] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client
    """
    app.dependency_overrides[get_async_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create a test user in the database
    """
    from ..db.repositories import UserRepository
    
    user_repo = UserRepository(db_session)
    
    user_data = {
        "email": "test@example.com",
        "password_hash": hash_password("TestPassword123!"),
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_verified": True
    }
    
    user = await user_repo.create_user(**user_data)
    await db_session.commit()
    
    return user

@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    """
    Create authentication headers for test user
    """
    token_data = jwt_service.create_token_pair(str(test_user.id), test_user.email)
    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    class MockRedis:
        def __init__(self):
            self.data = {}
            self.pubsub_data = []
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
        
        async def delete(self, key):
            return self.data.pop(key, None)
        
        async def ping(self):
            return True
        
        async def publish(self, channel, message):
            self.pubsub_data.append({"channel": channel, "message": message})
        
        def pubsub(self):
            return self
        
        async def subscribe(self, *channels):
            pass
        
        async def listen(self):
            return iter([])
    
    return MockRedis()

@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing"""
    class MockWebSocket:
        def __init__(self):
            self.messages_sent = []
            self.messages_received = []
            self.closed = False
        
        async def accept(self):
            pass
        
        async def send_json(self, data):
            self.messages_sent.append(data)
        
        async def receive_json(self):
            if self.messages_received:
                return self.messages_received.pop(0)
            raise Exception("No more messages")
        
        async def close(self):
            self.closed = True
        
        def add_message(self, message):
            self.messages_received.append(message)
    
    return MockWebSocket()

@pytest.fixture
def sample_bitcoin_data() -> Dict[str, Any]:
    """Sample Bitcoin market data for testing"""
    return {
        "symbol": "BTC",
        "price": 97420.15,
        "change_24h": 1234.56,
        "change_percent_24h": 1.28,
        "volume_24h": 28500000000,
        "market_cap": 1900000000000,
        "last_updated": datetime.now().isoformat()
    }

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing"""
    return {
        "email": f"test-{uuid.uuid4()}@example.com",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def sample_notification_data() -> Dict[str, Any]:
    """Sample notification data for testing"""
    return {
        "id": str(uuid.uuid4()),
        "type": "price_alert",
        "title": "Bitcoin Price Alert",
        "message": "Bitcoin has reached your target price of $100,000",
        "priority": "high",
        "is_read": False,
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    # Set test environment variables
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-do-not-use-in-production"
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce log noise in tests
    
    yield
    
    # Clean up environment variables
    test_vars = [
        "JWT_SECRET_KEY", "ALLOWED_ORIGINS", "DATABASE_URL", 
        "REDIS_URL", "LOG_LEVEL", "SENTRY_DSN"
    ]
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]

@pytest.fixture
def disable_sentry():
    """Disable Sentry for tests"""
    import sentry_sdk
    sentry_sdk.init()  # Initialize with no DSN to disable

# Async test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test to run with asyncio"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "websocket: mark test as websocket related"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API related"
    )

# Test utilities
class TestUtils:
    """Utility functions for tests"""
    
    @staticmethod
    def assert_response_structure(response_data: dict, expected_keys: list):
        """Assert that response has expected structure"""
        for key in expected_keys:
            assert key in response_data, f"Expected key '{key}' not found in response"
    
    @staticmethod
    def assert_error_response(response_data: dict):
        """Assert that response is a standard error response"""
        assert "error" in response_data
        error = response_data["error"]
        assert "code" in error
        assert "message" in error
    
    @staticmethod
    def assert_success_response(response_data: dict, expected_status: str = None):
        """Assert that response indicates success"""
        if expected_status:
            assert response_data.get("status") == expected_status
        assert "error" not in response_data

@pytest.fixture
def test_utils():
    """Provide test utilities"""
    return TestUtils()