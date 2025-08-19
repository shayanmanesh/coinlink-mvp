"""
WebSocket background services for real-time data broadcasting
Bitcoin price updates, market data, and other live information
"""

import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .manager import websocket_manager, WebSocketMessage

logger = logging.getLogger(__name__)

class BitcoinPriceService:
    """
    Service for broadcasting Bitcoin price updates
    In production, this would connect to real market data APIs
    """
    
    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Mock price data for MVP
        self.current_price = 97420.15
        self.price_history = []
        self.update_interval = 5  # seconds
        
    async def start(self):
        """Start the Bitcoin price broadcasting service"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._price_update_loop())
        logger.info("Bitcoin price service started")
    
    async def stop(self):
        """Stop the Bitcoin price broadcasting service"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Bitcoin price service stopped")
    
    async def _price_update_loop(self):
        """Background loop for price updates"""
        logger.info("Bitcoin price update loop started")
        
        while self.is_running:
            try:
                # Generate mock price update
                price_update = self._generate_price_update()
                
                # Broadcast to all subscribers
                message = WebSocketMessage(
                    type="bitcoin_price",
                    data=price_update
                )
                
                subscribers_count = await websocket_manager.send_to_channel("bitcoin_prices", message)
                
                if subscribers_count > 0:
                    logger.debug(f"Bitcoin price update sent to {subscribers_count} subscribers")
                
                # Store in history
                self.price_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "price": price_update["price"],
                    "change": price_update["change_24h"]
                })
                
                # Keep only last 100 entries
                if len(self.price_history) > 100:
                    self.price_history = self.price_history[-100:]
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Bitcoin price update loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def _generate_price_update(self) -> Dict[str, Any]:
        """
        Generate mock Bitcoin price update
        In production, this would fetch from real APIs
        """
        # Simulate price volatility
        change_percent = random.uniform(-0.5, 0.5)  # ±0.5% change
        price_change = self.current_price * (change_percent / 100)
        self.current_price += price_change
        
        # Keep price in reasonable range
        self.current_price = max(80000, min(120000, self.current_price))
        
        # Calculate 24h change (mock)
        change_24h = random.uniform(-5.0, 5.0)
        
        return {
            "price": round(self.current_price, 2),
            "change_24h": round(change_24h, 2),
            "change_percent_24h": round(change_24h / self.current_price * 100, 4),
            "volume_24h": random.randint(25000000000, 35000000000),
            "market_cap": round(self.current_price * 19700000, 0),  # ~19.7M BTC in circulation
            "timestamp": datetime.now().isoformat(),
            "source": "mock_data"  # In production: "coinbase", "binance", etc.
        }
    
    def get_current_price(self) -> Dict[str, Any]:
        """Get current price data"""
        return self._generate_price_update()
    
    def get_price_history(self, limit: int = 50) -> list:
        """Get recent price history"""
        return self.price_history[-limit:] if self.price_history else []


class MarketNewsService:
    """
    Service for broadcasting market news and alerts
    """
    
    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.news_interval = 300  # 5 minutes
        
        # Mock news data
        self.news_templates = [
            "Bitcoin shows strong resistance at ${price}, analysts remain optimistic",
            "Market volatility increases as Bitcoin trades around ${price}",
            "Institutional investors continue accumulating Bitcoin at current levels",
            "Technical analysis suggests Bitcoin may test ${price} support level",
            "Bitcoin network hash rate reaches new all-time high",
            "Regulatory clarity improves crypto market sentiment"
        ]
    
    async def start(self):
        """Start the market news service"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._news_update_loop())
        logger.info("Market news service started")
    
    async def stop(self):
        """Stop the market news service"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Market news service stopped")
    
    async def _news_update_loop(self):
        """Background loop for news updates"""
        logger.info("Market news update loop started")
        
        while self.is_running:
            try:
                # Generate mock news update
                news_update = self._generate_news_update()
                
                # Broadcast to news subscribers
                message = WebSocketMessage(
                    type="market_news",
                    data=news_update
                )
                
                subscribers_count = await websocket_manager.send_to_channel("market_news", message)
                
                if subscribers_count > 0:
                    logger.debug(f"Market news sent to {subscribers_count} subscribers")
                
                await asyncio.sleep(self.news_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in market news update loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def _generate_news_update(self) -> Dict[str, Any]:
        """Generate mock news update"""
        # Get current Bitcoin price for context
        current_price = random.uniform(95000, 100000)  # Mock price
        
        # Select random news template
        template = random.choice(self.news_templates)
        headline = template.replace("${price}", f"${current_price:,.0f}")
        
        return {
            "id": f"news_{int(datetime.now().timestamp())}",
            "headline": headline,
            "summary": f"Market analysis suggests continued interest in Bitcoin at current price levels around ${current_price:,.0f}.",
            "source": "Market Analysis",
            "category": "market_update",
            "timestamp": datetime.now().isoformat(),
            "importance": random.choice(["low", "medium", "high"])
        }


class AlertService:
    """
    Service for price alerts and notifications
    """
    
    def __init__(self):
        self.user_alerts: Dict[str, list] = {}  # user_id -> [alert_configs]
        
    async def add_price_alert(self, user_id: str, target_price: float, 
                             direction: str, message: str = None):
        """Add a price alert for a user"""
        if user_id not in self.user_alerts:
            self.user_alerts[user_id] = []
        
        alert = {
            "id": f"alert_{len(self.user_alerts[user_id])}_{int(datetime.now().timestamp())}",
            "user_id": user_id,
            "target_price": target_price,
            "direction": direction,  # "above" or "below"
            "message": message or f"Bitcoin price alert: {direction} ${target_price:,.2f}",
            "created_at": datetime.now().isoformat(),
            "triggered": False
        }
        
        self.user_alerts[user_id].append(alert)
        logger.info(f"Price alert added for user {user_id}: {direction} ${target_price}")
        
        return alert["id"]
    
    async def check_alerts(self, current_price: float):
        """Check all alerts against current price"""
        for user_id, alerts in self.user_alerts.items():
            for alert in alerts:
                if alert["triggered"]:
                    continue
                
                should_trigger = False
                
                if alert["direction"] == "above" and current_price >= alert["target_price"]:
                    should_trigger = True
                elif alert["direction"] == "below" and current_price <= alert["target_price"]:
                    should_trigger = True
                
                if should_trigger:
                    await self._trigger_alert(user_id, alert, current_price)
    
    async def _trigger_alert(self, user_id: str, alert: dict, current_price: float):
        """Trigger an alert for a user"""
        alert["triggered"] = True
        alert["triggered_at"] = datetime.now().isoformat()
        alert["triggered_price"] = current_price
        
        # Send alert message to user
        alert_message = WebSocketMessage(
            type="price_alert",
            data={
                "alert_id": alert["id"],
                "message": alert["message"],
                "target_price": alert["target_price"],
                "current_price": current_price,
                "direction": alert["direction"],
                "triggered_at": alert["triggered_at"]
            }
        )
        
        await websocket_manager.send_to_user(user_id, alert_message)
        logger.info(f"Price alert triggered for user {user_id}: ${current_price}")


# Global service instances
bitcoin_price_service = BitcoinPriceService()
market_news_service = MarketNewsService()
alert_service = AlertService()


async def start_websocket_services():
    """Start all WebSocket background services"""
    logger.info("Starting WebSocket background services...")
    
    try:
        await bitcoin_price_service.start()
        await market_news_service.start()
        logger.info("All WebSocket services started successfully")
    except Exception as e:
        logger.error(f"Failed to start WebSocket services: {e}")
        raise


async def stop_websocket_services():
    """Stop all WebSocket background services"""
    logger.info("Stopping WebSocket background services...")
    
    try:
        await bitcoin_price_service.stop()
        await market_news_service.stop()
        logger.info("All WebSocket services stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping WebSocket services: {e}")