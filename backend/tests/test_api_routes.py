"""
Unit and integration tests for API routes
Tests market data, user management, and notifications endpoints
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.api
@pytest.mark.integration
class TestMarketDataRoutes:
    """Test market data API routes"""
    
    @pytest.mark.asyncio
    async def test_bitcoin_price_endpoint(self, async_client):
        """Test Bitcoin price endpoint"""
        response = await async_client.get("/api/v2/market/bitcoin/price")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "symbol" in data
        assert "price" in data
        assert "change_24h" in data
        assert "change_percent_24h" in data
        assert "volume_24h" in data
        assert "last_updated" in data
        
        # Check data types and values
        assert data["symbol"] == "BTC"
        assert isinstance(data["price"], (int, float))
        assert data["price"] > 0
        assert isinstance(data["volume_24h"], (int, float))
    
    @pytest.mark.asyncio
    async def test_bitcoin_history_endpoint(self, async_client):
        """Test Bitcoin price history endpoint"""
        response = await async_client.get("/api/v2/market/bitcoin/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            price_point = data[0]
            assert "timestamp" in price_point
            assert "price" in price_point
            assert isinstance(price_point["price"], (int, float))
    
    @pytest.mark.asyncio
    async def test_bitcoin_history_with_params(self, async_client):
        """Test Bitcoin history with custom parameters"""
        response = await async_client.get(
            "/api/v2/market/bitcoin/history?period=7d&interval=1h"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should return multiple data points for 7 days
        assert len(data) > 1
    
    @pytest.mark.asyncio
    async def test_crypto_ticker_endpoint(self, async_client):
        """Test crypto ticker endpoint"""
        response = await async_client.get("/api/v2/market/crypto/ticker")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check first ticker
        ticker = data[0]
        assert "symbol" in ticker
        assert "price" in ticker
        assert "change_24h" in ticker
        assert "change_percent_24h" in ticker
        assert "last_updated" in ticker
    
    @pytest.mark.asyncio
    async def test_crypto_ticker_with_symbols(self, async_client):
        """Test crypto ticker with specific symbols"""
        response = await async_client.get(
            "/api/v2/market/crypto/ticker?symbols=BTC,ETH&limit=2"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 2
        
        # Should contain requested symbols
        symbols = [ticker["symbol"] for ticker in data]
        assert "BTC" in symbols
        assert "ETH" in symbols
    
    @pytest.mark.asyncio
    async def test_market_stats_endpoint(self, async_client):
        """Test market statistics endpoint"""
        response = await async_client.get("/api/v2/market/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_market_cap" in data
        assert "total_volume_24h" in data
        assert "bitcoin_dominance" in data
        assert "active_cryptocurrencies" in data
        assert "last_updated" in data
        
        # Check data types
        assert isinstance(data["total_market_cap"], (int, float))
        assert isinstance(data["bitcoin_dominance"], (int, float))
        assert isinstance(data["active_cryptocurrencies"], int)
    
    @pytest.mark.asyncio
    async def test_trending_coins_endpoint(self, async_client):
        """Test trending coins endpoint"""
        response = await async_client.get("/api/v2/market/trending")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check first trending coin
        coin = data[0]
        assert "id" in coin
        assert "symbol" in coin
        assert "name" in coin
        assert "price" in coin
        assert "change_24h" in coin
        assert "rank" in coin
    
    @pytest.mark.asyncio
    async def test_trending_coins_with_limit(self, async_client):
        """Test trending coins with limit parameter"""
        response = await async_client.get("/api/v2/market/trending?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5
    
    @pytest.mark.asyncio
    async def test_market_data_health(self, async_client):
        """Test market data service health check"""
        response = await async_client.get("/api/v2/market/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "market_data"
        assert "endpoints" in data


@pytest.mark.api
@pytest.mark.integration
class TestUserManagementRoutes:
    """Test user management API routes"""
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, async_client, auth_headers, test_user):
        """Test get user profile endpoint"""
        response = await async_client.get("/api/v2/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user profile fields
        assert "id" in data
        assert "email" in data
        assert "is_active" in data
        assert "is_verified" in data
        assert "created_at" in data
        
        assert data["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self, async_client, auth_headers):
        """Test update user profile endpoint"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = await async_client.put(
            "/api/v2/user/profile", 
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    @pytest.mark.asyncio
    async def test_get_user_preferences(self, async_client, auth_headers):
        """Test get user preferences endpoint"""
        response = await async_client.get("/api/v2/user/preferences", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check preference fields
        assert "theme" in data
        assert "language" in data
        assert "currency" in data
        assert "notifications_enabled" in data
        assert "email_alerts" in data
    
    @pytest.mark.asyncio
    async def test_update_user_preferences(self, async_client, auth_headers):
        """Test update user preferences endpoint"""
        preferences_data = {
            "theme": "light",
            "currency": "EUR",
            "notifications_enabled": False
        }
        
        response = await async_client.put(
            "/api/v2/user/preferences",
            json=preferences_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["theme"] == "light"
        assert data["currency"] == "EUR"
        assert data["notifications_enabled"] is False
    
    @pytest.mark.asyncio
    async def test_get_user_stats(self, async_client, auth_headers):
        """Test get user statistics endpoint"""
        response = await async_client.get("/api/v2/user/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check stats fields
        assert "total_logins" in data
        assert "account_age_days" in data
        assert "active_sessions" in data
        assert "total_sessions" in data
        
        # Check data types
        assert isinstance(data["total_logins"], int)
        assert isinstance(data["account_age_days"], int)
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, async_client, auth_headers):
        """Test get user sessions endpoint"""
        response = await async_client.get("/api/v2/user/sessions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            session = data[0]
            assert "id" in session
            assert "created_at" in session
            assert "is_current" in session
    
    @pytest.mark.asyncio
    async def test_get_user_alerts(self, async_client, auth_headers):
        """Test get user alerts endpoint"""
        response = await async_client.get("/api/v2/user/alerts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Mock data should return some alerts
        if len(data) > 0:
            alert = data[0]
            assert "id" in alert
            assert "symbol" in alert
            assert "target_price" in alert
            assert "condition" in alert
            assert "is_active" in alert
    
    @pytest.mark.asyncio
    async def test_create_price_alert(self, async_client, auth_headers):
        """Test create price alert endpoint"""
        alert_data = {
            "symbol": "BTC",
            "target_price": 100000.0,
            "condition": "above"
        }
        
        response = await async_client.post(
            "/api/v2/user/alerts",
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["symbol"] == "BTC"
        assert data["target_price"] == 100000.0
        assert data["condition"] == "above"
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client):
        """Test unauthorized access to user endpoints"""
        response = await async_client.get("/api/v2/user/profile")
        assert response.status_code == 401
        
        response = await async_client.get("/api/v2/user/preferences")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_user_management_health(self, async_client):
        """Test user management service health check"""
        response = await async_client.get("/api/v2/user/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "user_management"


@pytest.mark.api
@pytest.mark.integration
class TestNotificationRoutes:
    """Test notification API routes"""
    
    @pytest.mark.asyncio
    async def test_get_notifications(self, async_client, auth_headers):
        """Test get notifications endpoint"""
        response = await async_client.get("/api/v2/notifications/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Mock should return some notifications
        if len(data) > 0:
            notification = data[0]
            assert "id" in notification
            assert "type" in notification
            assert "title" in notification
            assert "message" in notification
            assert "priority" in notification
            assert "is_read" in notification
            assert "created_at" in notification
    
    @pytest.mark.asyncio
    async def test_get_notifications_with_filter(self, async_client, auth_headers):
        """Test get notifications with type filter"""
        response = await async_client.get(
            "/api/v2/notifications/?type_filter=price_alert&unread_only=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_mark_notification_read(self, async_client, auth_headers):
        """Test mark notification as read endpoint"""
        notification_id = "test-notification-1"
        
        response = await async_client.put(
            f"/api/v2/notifications/{notification_id}/read",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_mark_all_notifications_read(self, async_client, auth_headers):
        """Test mark all notifications as read endpoint"""
        response = await async_client.put(
            "/api/v2/notifications/read-all",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_delete_notification(self, async_client, auth_headers):
        """Test delete notification endpoint"""
        notification_id = "test-notification-1"
        
        response = await async_client.delete(
            f"/api/v2/notifications/{notification_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_get_notification_settings(self, async_client, auth_headers):
        """Test get notification settings endpoint"""
        response = await async_client.get(
            "/api/v2/notifications/settings",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check settings fields
        assert "email_enabled" in data
        assert "push_enabled" in data
        assert "price_alerts" in data
        assert "news_updates" in data
        assert "system_alerts" in data
    
    @pytest.mark.asyncio
    async def test_update_notification_settings(self, async_client, auth_headers):
        """Test update notification settings endpoint"""
        settings_data = {
            "email_enabled": False,
            "price_alerts": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00"
        }
        
        response = await async_client.put(
            "/api/v2/notifications/settings",
            json=settings_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email_enabled"] is False
        assert data["price_alerts"] is True
    
    @pytest.mark.asyncio
    async def test_get_alert_rules(self, async_client, auth_headers):
        """Test get alert rules endpoint"""
        response = await async_client.get(
            "/api/v2/notifications/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            rule = data[0]
            assert "id" in rule
            assert "symbol" in rule
            assert "condition" in rule
            assert "target_value" in rule
            assert "is_active" in rule
            assert "trigger_count" in rule
    
    @pytest.mark.asyncio
    async def test_create_alert_rule(self, async_client, auth_headers):
        """Test create alert rule endpoint"""
        rule_data = {
            "symbol": "ETH",
            "condition": "below",
            "target_value": 3000.0
        }
        
        response = await async_client.post(
            "/api/v2/notifications/alerts",
            json=rule_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["symbol"] == "ETH"
        assert data["condition"] == "below"
        assert data["target_value"] == 3000.0
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_update_alert_rule(self, async_client, auth_headers):
        """Test update alert rule endpoint"""
        rule_id = "test-rule-1"
        update_data = {
            "target_value": 3500.0,
            "is_active": False
        }
        
        response = await async_client.put(
            f"/api/v2/notifications/alerts/{rule_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["target_value"] == 3500.0
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_delete_alert_rule(self, async_client, auth_headers):
        """Test delete alert rule endpoint"""
        rule_id = "test-rule-1"
        
        response = await async_client.delete(
            f"/api/v2/notifications/alerts/{rule_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, async_client, auth_headers):
        """Test get unread notification count endpoint"""
        response = await async_client.get(
            "/api/v2/notifications/unread-count",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
    
    @pytest.mark.asyncio
    async def test_notifications_health(self, async_client):
        """Test notifications service health check"""
        response = await async_client.get("/api/v2/notifications/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "notifications"


@pytest.mark.api
@pytest.mark.integration
class TestBackwardsCompatibility:
    """Test backwards compatibility endpoints"""
    
    @pytest.mark.asyncio
    async def test_old_bitcoin_price_endpoint(self, async_client):
        """Test backwards compatible Bitcoin price endpoint"""
        response = await async_client.get("/api/bitcoin/price")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have old format
        assert "data" in data
        assert "price" in data["data"]
        assert "change_24h" in data["data"]
        assert "volume_24h" in data["data"]
        assert "timestamp" in data["data"]
    
    @pytest.mark.asyncio
    async def test_old_crypto_ticker_endpoint(self, async_client):
        """Test backwards compatible crypto ticker endpoint"""
        response = await async_client.get("/api/crypto/ticker")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have old format
        assert "data" in data
        assert "timestamp" in data
        assert isinstance(data["data"], list)
        
        if len(data["data"]) > 0:
            ticker = data["data"][0]
            assert "symbol" in ticker
            assert "price" in ticker
            assert "change_24h" in ticker