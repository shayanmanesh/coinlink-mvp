"""
Unit and integration tests for WebSocket functionality
Tests WebSocket manager, message handling, and real-time communication
"""

import pytest
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ..websocket.manager import WebSocketManager, WebSocketMessage, Connection
from ..websocket.services import BitcoinPriceService, MarketNewsService, AlertService


@pytest.mark.websocket
@pytest.mark.unit
class TestWebSocketMessage:
    """Test WebSocket message model"""
    
    def test_message_creation(self):
        """Test WebSocket message creation"""
        message = WebSocketMessage(
            type="test",
            data={"key": "value"},
            user_id="user123"
        )
        
        assert message.type == "test"
        assert message.data == {"key": "value"}
        assert message.user_id == "user123"
        assert message.timestamp is not None
        assert message.connection_id is None
    
    def test_message_auto_timestamp(self):
        """Test automatic timestamp generation"""
        message1 = WebSocketMessage(type="test", data={})
        message2 = WebSocketMessage(type="test", data={})
        
        # Should have different timestamps
        assert message1.timestamp != message2.timestamp
    
    def test_message_serialization(self):
        """Test message dict conversion"""
        message = WebSocketMessage(
            type="chat",
            data={"message": "hello"},
            user_id="user123"
        )
        
        message_dict = message.dict()
        
        assert message_dict["type"] == "chat"
        assert message_dict["data"]["message"] == "hello"
        assert message_dict["user_id"] == "user123"
        assert "timestamp" in message_dict


@pytest.mark.websocket
@pytest.mark.unit  
class TestWebSocketManager:
    """Test WebSocket manager functionality"""
    
    @pytest.fixture
    def ws_manager(self, mock_redis):
        """Create WebSocket manager with mocked Redis"""
        manager = WebSocketManager("redis://localhost:6379")
        manager.redis_client = mock_redis
        return manager
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, ws_manager):
        """Test WebSocket manager initialization"""
        await ws_manager.initialize()
        
        assert ws_manager.redis_client is not None
        assert ws_manager.connections == {}
        assert ws_manager.user_connections == {}
        assert ws_manager.channel_connections == {}
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self, ws_manager, mock_websocket):
        """Test WebSocket connection"""
        await ws_manager.initialize()
        
        connection_id = await ws_manager.connect(
            websocket=mock_websocket,
            user_id="user123",
            ip_address="127.0.0.1",
            user_agent="test"
        )
        
        assert connection_id is not None
        assert connection_id in ws_manager.connections
        assert "user123" in ws_manager.user_connections
        assert "user123" in ws_manager.user_connections
        assert len(mock_websocket.messages_sent) > 0  # Welcome message
        
        # Check connection details
        connection = ws_manager.connections[connection_id]
        assert connection.user_id == "user123"
        assert connection.authenticated is True
        assert connection.ip_address == "127.0.0.1"
    
    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, ws_manager, mock_websocket):
        """Test WebSocket disconnection"""
        await ws_manager.initialize()
        
        # Connect first
        connection_id = await ws_manager.connect(mock_websocket, "user123")
        assert connection_id in ws_manager.connections
        
        # Disconnect
        await ws_manager.disconnect(connection_id)
        
        assert connection_id not in ws_manager.connections
        assert "user123" not in ws_manager.user_connections
    
    @pytest.mark.asyncio
    async def test_join_channel(self, ws_manager, mock_websocket):
        """Test joining channels"""
        await ws_manager.initialize()
        
        connection_id = await ws_manager.connect(mock_websocket, "user123")
        
        # Join channel
        success = await ws_manager.join_channel(connection_id, "bitcoin_prices")
        
        assert success is True
        assert "bitcoin_prices" in ws_manager.channel_connections
        assert connection_id in ws_manager.channel_connections["bitcoin_prices"]
        
        # Check connection has channel
        connection = ws_manager.connections[connection_id]
        assert "bitcoin_prices" in connection.channels
    
    @pytest.mark.asyncio
    async def test_leave_channel(self, ws_manager, mock_websocket):
        """Test leaving channels"""
        await ws_manager.initialize()
        
        connection_id = await ws_manager.connect(mock_websocket, "user123")
        
        # Join then leave channel
        await ws_manager.join_channel(connection_id, "bitcoin_prices")
        success = await ws_manager.leave_channel(connection_id, "bitcoin_prices")
        
        assert success is True
        
        # Check channel removed
        connection = ws_manager.connections[connection_id]
        assert "bitcoin_prices" not in connection.channels
        
        # Channel should be removed if empty
        assert "bitcoin_prices" not in ws_manager.channel_connections
    
    @pytest.mark.asyncio
    async def test_send_to_user(self, ws_manager, mock_websocket):
        """Test sending message to specific user"""
        await ws_manager.initialize()
        
        connection_id = await ws_manager.connect(mock_websocket, "user123")
        
        message = WebSocketMessage(
            type="notification",
            data={"message": "Hello user!"}
        )
        
        sent_count = await ws_manager.send_to_user("user123", message)
        
        assert sent_count == 1
        assert len(mock_websocket.messages_sent) >= 2  # Welcome + notification
        
        # Check message content
        last_message = mock_websocket.messages_sent[-1]
        assert last_message["type"] == "notification"
        assert last_message["data"]["message"] == "Hello user!"
    
    @pytest.mark.asyncio
    async def test_send_to_channel(self, ws_manager, mock_websocket):
        """Test sending message to channel"""
        await ws_manager.initialize()
        
        connection_id = await ws_manager.connect(mock_websocket, "user123")
        await ws_manager.join_channel(connection_id, "bitcoin_prices")
        
        message = WebSocketMessage(
            type="price_update",
            data={"price": 100000}
        )
        
        sent_count = await ws_manager.send_to_channel("bitcoin_prices", message)
        
        assert sent_count == 1
        
        # Check message received
        last_message = mock_websocket.messages_sent[-1]
        assert last_message["type"] == "price_update"
        assert last_message["data"]["price"] == 100000
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, ws_manager, mock_websocket):
        """Test broadcasting message to all connections"""
        await ws_manager.initialize()
        
        # Connect multiple clients
        connection1 = await ws_manager.connect(mock_websocket, "user1")
        
        # Mock second websocket
        mock_websocket2 = MagicMock()
        mock_websocket2.send_json = AsyncMock()
        connection2 = await ws_manager.connect(mock_websocket2, "user2")
        
        message = WebSocketMessage(
            type="system_announcement",
            data={"message": "Maintenance scheduled"}
        )
        
        sent_count = await ws_manager.broadcast(message)
        
        assert sent_count == 2
    
    @pytest.mark.asyncio
    async def test_authenticate_connection(self, ws_manager, mock_websocket):
        """Test connection authentication"""
        await ws_manager.initialize()
        
        # Connect without user ID
        connection_id = await ws_manager.connect(mock_websocket)
        
        # Authenticate
        success = await ws_manager.authenticate_connection(connection_id, "user123")
        
        assert success is True
        
        # Check connection updated
        connection = ws_manager.connections[connection_id]
        assert connection.user_id == "user123"
        assert connection.authenticated is True
        
        # Check user index updated
        assert "user123" in ws_manager.user_connections
        assert connection_id in ws_manager.user_connections["user123"]
    
    def test_get_stats(self, ws_manager):
        """Test getting WebSocket manager statistics"""
        stats = ws_manager.get_stats()
        
        expected_keys = [
            "total_connections", "authenticated_connections", "anonymous_connections",
            "total_users", "total_channels", "redis_connected"
        ]
        
        for key in expected_keys:
            assert key in stats


@pytest.mark.websocket
@pytest.mark.unit
class TestWebSocketServices:
    """Test WebSocket background services"""
    
    @pytest.mark.asyncio
    async def test_bitcoin_price_service(self):
        """Test Bitcoin price service"""
        service = BitcoinPriceService()
        
        # Test price generation
        price_update = service._generate_price_update()
        
        assert "price" in price_update
        assert "change_24h" in price_update
        assert "volume_24h" in price_update
        assert "timestamp" in price_update
        assert price_update["price"] > 0
        
        # Test current price
        current = service.get_current_price()
        assert current["price"] > 0
    
    @pytest.mark.asyncio
    async def test_market_news_service(self):
        """Test market news service"""
        service = MarketNewsService()
        
        # Test news generation
        news_update = service._generate_news_update()
        
        assert "id" in news_update
        assert "headline" in news_update
        assert "timestamp" in news_update
        assert "importance" in news_update
        assert news_update["importance"] in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_alert_service(self):
        """Test alert service"""
        service = AlertService()
        
        # Add price alert
        alert_id = await service.add_price_alert(
            user_id="user123",
            target_price=100000.0,
            direction="above",
            message="Bitcoin reached $100k!"
        )
        
        assert alert_id is not None
        assert "user123" in service.user_alerts
        assert len(service.user_alerts["user123"]) == 1
        
        alert = service.user_alerts["user123"][0]
        assert alert["target_price"] == 100000.0
        assert alert["direction"] == "above"
        assert alert["triggered"] is False
    
    @pytest.mark.asyncio
    async def test_alert_triggering(self):
        """Test alert triggering logic"""
        service = AlertService()
        
        # Add alerts
        await service.add_price_alert("user1", 95000.0, "above")
        await service.add_price_alert("user2", 105000.0, "below")
        
        # Mock WebSocket manager
        with patch('..websocket.services.websocket_manager') as mock_manager:
            mock_manager.send_to_user = AsyncMock()
            
            # Check alerts with price that should trigger first alert
            await service.check_alerts(96000.0)
            
            # First alert should be triggered
            alert1 = service.user_alerts["user1"][0]
            assert alert1["triggered"] is True
            
            # Second alert should not be triggered
            alert2 = service.user_alerts["user2"][0] 
            assert alert2["triggered"] is False
            
            # Check that message was sent to user1
            mock_manager.send_to_user.assert_called_once()


@pytest.mark.websocket
@pytest.mark.integration
class TestWebSocketRoutes:
    """Integration tests for WebSocket endpoints"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """Test WebSocket connection endpoint"""
        with client.websocket_connect("/ws") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            
            assert data["type"] == "connected"
            assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, client):
        """Test WebSocket ping/pong"""
        with client.websocket_connect("/ws") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_websocket_chat_message(self, client):
        """Test WebSocket chat functionality"""
        with client.websocket_connect("/ws") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send chat message
            websocket.send_json({
                "type": "chat_message",
                "message": "Hello Bitcoin!",
                "channel": "general"
            })
            
            # Receive chat response
            response = websocket.receive_json()
            assert response["type"] == "chat_response"
            assert "bot_response" in response["data"]
            assert response["data"]["user_message"] == "Hello Bitcoin!"
    
    @pytest.mark.asyncio  
    async def test_websocket_bitcoin_subscription(self, client):
        """Test Bitcoin price subscription"""
        with client.websocket_connect("/ws") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Subscribe to Bitcoin prices
            websocket.send_json({"type": "subscribe_bitcoin"})
            
            # Should receive confirmation and price update
            response = websocket.receive_json()
            
            # Could be either subscription confirmation or price update
            assert response["type"] in ["bitcoin_price", "channel_joined"]
            
            if response["type"] == "bitcoin_price":
                assert "price" in response["data"]
                assert response["data"]["status"] == "subscribed"
    
    @pytest.mark.asyncio
    async def test_websocket_authentication(self, client, auth_headers):
        """Test WebSocket authentication"""
        # Extract token from headers
        auth_header = auth_headers["Authorization"]
        token = auth_header.replace("Bearer ", "")
        
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Should receive authenticated welcome message
            data = websocket.receive_json()
            
            assert data["type"] == "connected"
            # Should indicate authentication in message data if available
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, client):
        """Test WebSocket error handling"""
        with client.websocket_connect("/ws") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send invalid message
            websocket.send_text("invalid json")
            
            # Should receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "invalid_json" in response["data"]["error_code"]
    
    @pytest.mark.asyncio
    async def test_websocket_stats_endpoint(self, async_client):
        """Test WebSocket statistics endpoint"""
        response = await async_client.get("/ws/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "websocket_stats" in data
        assert "timestamp" in data
        
        ws_stats = data["websocket_stats"]
        assert "total_connections" in ws_stats