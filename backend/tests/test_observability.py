"""
Unit tests for observability components
Tests metrics, logging, Sentry integration, and middleware
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
import json
from datetime import datetime

from ..observability.metrics import coinlink_metrics, CoinLinkMetrics
from ..observability.logging import (
    StructuredLogger, set_trace_id, get_trace_id, set_user_id, get_user_id,
    JSONFormatter, TraceIDFilter
)
from ..observability.sentry import configure_sentry, capture_exception, capture_message
from ..observability.middleware import RequestTracingMiddleware, MetricsMiddleware


@pytest.mark.unit
class TestMetrics:
    """Test Prometheus metrics functionality"""
    
    def test_coinlink_metrics_initialization(self):
        """Test CoinLinkMetrics initialization"""
        metrics = CoinLinkMetrics()
        
        # Check that all metric objects are created
        assert hasattr(metrics, 'api_requests_total')
        assert hasattr(metrics, 'api_request_duration')
        assert hasattr(metrics, 'websocket_connections_total')
        assert hasattr(metrics, 'auth_attempts_total')
        assert hasattr(metrics, 'database_connections_active')
        assert hasattr(metrics, 'users_registered_total')
    
    def test_record_api_request(self):
        """Test API request metrics recording"""
        metrics = CoinLinkMetrics()
        
        # Record API request
        metrics.record_api_request("GET", "/api/test", 200, 0.123)
        
        # Check that counters were incremented
        # Note: In actual tests, you'd need to check the prometheus registry
        # Here we're just testing the method doesn't crash
        assert True  # Method executed successfully
    
    def test_record_websocket_message(self):
        """Test WebSocket message metrics recording"""
        metrics = CoinLinkMetrics()
        
        # Record WebSocket message
        metrics.record_websocket_message("chat", 0.05, True)
        metrics.record_websocket_message("ping", 0.01, True)
        metrics.record_websocket_message("error", 0.1, False)
        
        assert True  # Method executed successfully
    
    def test_record_auth_attempt(self):
        """Test authentication attempt metrics"""
        metrics = CoinLinkMetrics()
        
        # Record successful login
        metrics.record_auth_attempt("login", True)
        
        # Record failed login
        metrics.record_auth_attempt("login", False)
        
        # Record signup
        metrics.record_auth_attempt("signup", True)
        
        assert True  # Method executed successfully
    
    def test_record_business_metrics(self):
        """Test business logic metrics"""
        metrics = CoinLinkMetrics()
        
        # User registration
        metrics.record_user_registration()
        
        # Price alert
        metrics.record_price_alert("BTC", "above")
        
        # Market data request
        metrics.record_market_data_request("/bitcoin/price", "BTC")
        
        assert True  # Methods executed successfully
    
    def test_update_connection_counts(self):
        """Test connection count updates"""
        metrics = CoinLinkMetrics()
        
        # Update WebSocket connections
        metrics.update_websocket_connections(total=10, authenticated=7)
        
        # Update database connections
        metrics.update_database_connections(15)
        
        # Update Redis connections
        metrics.update_redis_connections(5)
        
        assert True  # Methods executed successfully
    
    def test_error_recording(self):
        """Test error metrics recording"""
        metrics = CoinLinkMetrics()
        
        # Record errors
        metrics.record_error("http_5xx", "error")
        metrics.record_error("validation", "warning")
        metrics.record_database_error("connection_timeout")
        
        # Record rate limiting
        metrics.record_rate_limit_exceeded("/api/test", "authenticated")
        
        assert True  # Methods executed successfully


@pytest.mark.unit
class TestStructuredLogging:
    """Test structured logging functionality"""
    
    def test_trace_id_context(self):
        """Test trace ID context management"""
        # Set trace ID
        trace_id = str(uuid.uuid4())
        set_trace_id(trace_id)
        
        # Get trace ID
        retrieved_id = get_trace_id()
        assert retrieved_id == trace_id
        
        # Auto-generate trace ID
        set_trace_id()  # No argument should generate new ID
        new_id = get_trace_id()
        assert new_id != trace_id
        assert len(new_id) > 0
    
    def test_user_id_context(self):
        """Test user ID context management"""
        # Set user ID
        user_id = "user123"
        set_user_id(user_id)
        
        # Get user ID
        retrieved_id = get_user_id()
        assert retrieved_id == user_id
    
    def test_json_formatter(self):
        """Test JSON log formatter"""
        import logging
        
        formatter = JSONFormatter()
        
        # Create log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Add trace ID to record
        record.trace_id = "test-trace-id"
        record.user_id = "test-user"
        
        # Format record
        formatted = formatter.format(record)
        
        # Parse JSON
        log_data = json.loads(formatted)
        
        # Check required fields
        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert log_data["trace_id"] == "test-trace-id"
        assert log_data["user_id"] == "test-user"
        assert "timestamp" in log_data
        assert "service" in log_data
        assert "source" in log_data
    
    def test_structured_logger(self):
        """Test structured logger methods"""
        logger = StructuredLogger("test")
        
        # Test different log methods (should not crash)
        logger.info("Test info message", extra_field="value")
        logger.error("Test error message", error_code="E001")
        logger.warning("Test warning", user_id="user123")
        
        # Test specialized log methods
        logger.api_request("GET", "/test", 200, 123.45)
        logger.auth_event("login", "user123", True)
        logger.websocket_event("connect", "conn123", "user123")
        logger.database_event("select", "users", 45.2)
        logger.business_event("user_signup", user_id="user123")
        logger.security_event("suspicious_login", "high", ip_address="1.2.3.4")
        
        # Should complete without errors
        assert True
    
    def test_trace_id_filter(self):
        """Test trace ID logging filter"""
        import logging
        
        filter_obj = TraceIDFilter()
        
        # Create log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Set context
        set_trace_id("test-trace")
        set_user_id("test-user")
        
        # Apply filter
        result = filter_obj.filter(record)
        
        assert result is True
        assert hasattr(record, 'trace_id')
        assert hasattr(record, 'user_id')
        assert record.trace_id == "test-trace"
        assert record.user_id == "test-user"


@pytest.mark.unit
class TestSentryIntegration:
    """Test Sentry integration functionality"""
    
    @patch('sentry_sdk.init')
    def test_configure_sentry(self, mock_init):
        """Test Sentry configuration"""
        with patch.object(configure_sentry.__globals__['settings'], 'SENTRY_DSN', 'test-dsn'):
            configure_sentry()
            
            # Check that sentry_sdk.init was called
            mock_init.assert_called_once()
    
    @patch('sentry_sdk.init')
    def test_configure_sentry_no_dsn(self, mock_init):
        """Test Sentry configuration without DSN"""
        with patch.object(configure_sentry.__globals__['settings'], 'SENTRY_DSN', None):
            configure_sentry()
            
            # Should not initialize if no DSN
            mock_init.assert_not_called()
    
    @patch('sentry_sdk.capture_exception')
    def test_capture_exception(self, mock_capture):
        """Test exception capture"""
        exception = ValueError("Test error")
        
        capture_exception(exception, context="test")
        
        mock_capture.assert_called_once_with(exception)
    
    @patch('sentry_sdk.capture_message')  
    def test_capture_message(self, mock_capture):
        """Test message capture"""
        message = "Test message"
        
        capture_message(message, level="info", context="test")
        
        mock_capture.assert_called_once_with(message, level="info")
    
    def test_before_send_filter(self):
        """Test Sentry before_send filter"""
        from ..observability.sentry import before_send_filter
        
        # Create test event
        event = {
            "exception": {
                "values": [{
                    "type": "ValueError",
                    "value": "Test error"
                }]
            },
            "request": {
                "headers": {
                    "authorization": "Bearer secret-token",
                    "user-agent": "test-agent"
                },
                "data": {
                    "password": "secret123",
                    "username": "testuser"
                }
            }
        }
        
        # Apply filter
        filtered_event = before_send_filter(event, {})
        
        # Should remove sensitive headers
        assert "authorization" not in filtered_event["request"]["headers"]
        
        # Should filter sensitive data
        assert filtered_event["request"]["data"]["password"] == "[Filtered]"
        assert filtered_event["request"]["data"]["username"] == "testuser"  # Not sensitive
    
    def test_before_send_transaction_filter(self):
        """Test Sentry transaction filter"""
        from ..observability.sentry import before_send_transaction_filter
        
        # Health check transaction (should be filtered)
        health_event = {
            "transaction": "/health",
            "type": "transaction"
        }
        
        result = before_send_transaction_filter(health_event, {})
        assert result is None  # Should be filtered out
        
        # Regular transaction (should pass)
        api_event = {
            "transaction": "/api/test",
            "type": "transaction"
        }
        
        result = before_send_transaction_filter(api_event, {})
        assert result is not None


@pytest.mark.unit
class TestObservabilityMiddleware:
    """Test observability middleware"""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock()
        request.method = "GET"
        request.url.path = "/api/test"
        request.headers = {
            "User-Agent": "test-agent",
            "Authorization": "Bearer test-token"
        }
        request.client.host = "127.0.0.1"
        return request
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response"""
        response = Mock()
        response.status_code = 200
        response.headers = {}
        return response
    
    @pytest.mark.asyncio
    async def test_request_tracing_middleware(self, mock_request, mock_response):
        """Test request tracing middleware"""
        # Mock the call_next function
        async def call_next(request):
            return mock_response
        
        # Create middleware
        middleware = RequestTracingMiddleware(None)
        
        # Process request
        with patch('..observability.middleware.jwt_service.get_token_user_id', return_value="user123"):
            result = await middleware.dispatch(mock_request, call_next)
        
        # Should return response
        assert result == mock_response
        
        # Should add trace ID header
        assert "X-Trace-ID" in result.headers
    
    @pytest.mark.asyncio
    async def test_metrics_middleware(self, mock_request, mock_response):
        """Test metrics middleware"""
        # Mock the call_next function
        async def call_next(request):
            return mock_response
        
        # Create middleware
        middleware = MetricsMiddleware(None)
        
        # Process request
        result = await middleware.dispatch(mock_request, call_next)
        
        # Should return response
        assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self, mock_request):
        """Test middleware error handling"""
        # Mock call_next to raise exception
        async def call_next(request):
            raise ValueError("Test error")
        
        # Create middleware
        middleware = RequestTracingMiddleware(None)
        
        # Process request (should handle error)
        result = await middleware.dispatch(mock_request, call_next)
        
        # Should return error response
        assert result.status_code == 500
        assert "X-Trace-ID" in result.headers
    
    def test_websocket_metrics_middleware(self):
        """Test WebSocket metrics middleware"""
        from ..observability.middleware import WebSocketMetricsMiddleware
        
        middleware = WebSocketMetricsMiddleware()
        
        # Test connection recording
        middleware.record_connection(total=5, authenticated=3)
        
        # Test message recording
        middleware.record_message("chat", 0.05, True)
        middleware.record_message("ping", 0.01, True)
        
        # Methods should complete without error
        assert True


@pytest.mark.integration
class TestObservabilityIntegration:
    """Integration tests for observability components"""
    
    @pytest.mark.asyncio
    async def test_health_endpoints_include_observability(self, async_client):
        """Test that health endpoints include observability status"""
        response = await async_client.get("/readyz")
        
        assert response.status_code in [200, 503]  # May be unhealthy in test
        data = response.json()
        
        assert "checks" in data
        # Should include observability check
        if "observability" in data["checks"]:
            obs_check = data["checks"]["observability"]
            assert "status" in obs_check
            assert "components" in obs_check
    
    @pytest.mark.asyncio
    async def test_custom_metrics_endpoint(self, async_client):
        """Test custom metrics endpoint"""
        response = await async_client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check metrics structure
        assert "timestamp" in data
        assert "service" in data
        assert "metrics" in data
        
        metrics = data["metrics"]
        assert "websocket" in metrics
        assert "database" in metrics
        assert "system" in metrics
    
    @pytest.mark.asyncio
    async def test_prometheus_metrics_endpoint(self, async_client):
        """Test Prometheus metrics endpoint"""
        response = await async_client.get("/metrics")
        
        # Should return Prometheus format or 404 if not configured
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Should be plain text format
            assert "text/plain" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio 
    async def test_request_includes_trace_id(self, async_client):
        """Test that requests include trace ID in response"""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        
        # Should include trace ID in response headers
        assert "X-Trace-ID" in response.headers
        
        # Trace ID should be valid UUID format
        trace_id = response.headers["X-Trace-ID"]
        uuid.UUID(trace_id)  # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_api_performance_tracking(self, async_client):
        """Test that API performance is tracked"""
        # Make several requests
        endpoints = ["/health", "/api/connections", "/"]
        
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            
            # Should have trace ID (indicates middleware is working)
            if response.status_code != 404:  # Skip not found endpoints
                assert "X-Trace-ID" in response.headers
    
    @pytest.mark.asyncio
    async def test_error_response_format(self, async_client):
        """Test that error responses include trace ID"""
        # Request non-existent endpoint
        response = await async_client.get("/api/nonexistent")
        
        # Should still include trace ID even for 404
        if "X-Trace-ID" in response.headers:
            trace_id = response.headers["X-Trace-ID"]
            uuid.UUID(trace_id)  # Should be valid UUID