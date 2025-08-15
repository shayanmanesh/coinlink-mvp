import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from config.settings import settings
from tools.coinbase_tools import get_bitcoin_price
from sentiment.analyzer import BitcoinSentimentService

class BitcoinMonitor:
    def __init__(self):
        self.redis_client = None
        self.sentiment_service = BitcoinSentimentService()
        self.alert_threshold = settings.ALERT_THRESHOLD_PERCENT
        self.monitor_interval = settings.MONITOR_INTERVAL
        self.last_price = None
        self.last_sentiment = None
        self.alert_callbacks = []

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            await self.redis_client.ping()
            print("Bitcoin monitor initialized with Redis connection")
        except Exception as e:
            print(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None

    async def add_alert_callback(self, callback):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)

    async def get_bitcoin_price(self) -> Optional[Dict[str, Any]]:
        """Get current Bitcoin price data"""
        try:
            result = get_bitcoin_price("BTC-USD")
            if "error" not in result:
                return result
            return None
        except Exception as e:
            print(f"Error getting Bitcoin price: {str(e)}")
            return None

    async def get_bitcoin_sentiment(self) -> Optional[Dict[str, Any]]:
        """Get current Bitcoin sentiment data"""
        try:
            return await self.sentiment_service.get_bitcoin_sentiment_summary()
        except Exception as e:
            print(f"Error getting Bitcoin sentiment: {str(e)}")
            return None

    async def cache_bitcoin_data(self, data: Dict[str, Any], data_type: str):
        """Cache Bitcoin data in Redis"""
        if not self.redis_client:
            return

        try:
            cache_key = f"bitcoin:{data_type}:{int(time.time())}"
            await self.redis_client.setex(
                cache_key,
                settings.CACHE_TTL,
                json.dumps(data)
            )
        except Exception as e:
            print(f"Error caching Bitcoin data: {str(e)}")

    async def check_price_alert_conditions(self, current_price: Dict[str, Any]) -> bool:
        """Check if price alert conditions are met"""
        if not self.last_price:
            return False

        try:
            current_price_value = current_price.get('price', 0)
            last_price_value = self.last_price.get('price', 0)

            if last_price_value > 0:
                price_change_percent = abs((current_price_value - last_price_value) / last_price_value) * 100
                return price_change_percent >= self.alert_threshold

            return False
        except Exception as e:
            print(f"Error checking price alert conditions: {str(e)}")
            return False

    async def check_volume_alert_conditions(self, current_price: Dict[str, Any]) -> bool:
        """Check if volume alert conditions are met"""
        try:
            current_volume = current_price.get('volume', 0)
            # Simple volume spike detection (could be enhanced with historical data)
            return current_volume > 1000000  # 1M USD volume threshold
        except Exception as e:
            print(f"Error checking volume alert conditions: {str(e)}")
            return False

    async def check_sentiment_alert_conditions(self, current_sentiment: Dict[str, Any]) -> bool:
        """Check if sentiment alert conditions are met"""
        if not self.last_sentiment:
            return False

        try:
            current_sentiment_label = current_sentiment.get('overall_sentiment', 'neutral')
            last_sentiment_label = self.last_sentiment.get('overall_sentiment', 'neutral')

            # Alert on sentiment change
            return current_sentiment_label != last_sentiment_label
        except Exception as e:
            print(f"Error checking sentiment alert conditions: {str(e)}")
            return False

    async def generate_alert(self, alert_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alert message"""
        timestamp = datetime.now().isoformat()

        if alert_type == "price":
            current_price = data.get('price', 0)
            last_price = self.last_price.get('price', 0) if self.last_price else 0
            change_percent = ((current_price - last_price) / last_price * 100) if last_price > 0 else 0

            return {
                "type": "price_alert",
                "message": f"🚨 Bitcoin {'up' if change_percent > 0 else 'down'} {abs(change_percent):.1f}% to ${current_price:,.2f}",
                "data": {
                    "current_price": current_price,
                    "previous_price": last_price,
                    "change_percent": change_percent,
                    "timestamp": timestamp
                },
                "timestamp": timestamp
            }

        elif alert_type == "volume":
            volume = data.get('volume', 0)
            return {
                "type": "volume_alert",
                "message": f"📊 Bitcoin volume spike: ${volume:,.0f}",
                "data": {
                    "volume": volume,
                    "timestamp": timestamp
                },
                "timestamp": timestamp
            }

        elif alert_type == "sentiment":
            sentiment = data.get('overall_sentiment', 'neutral')
            emoji = data.get('sentiment_emoji', '⚪')
            return {
                "type": "sentiment_alert",
                "message": f"{emoji} Bitcoin sentiment changed to {sentiment}",
                "data": {
                    "sentiment": sentiment,
                    "sentiment_emoji": emoji,
                    "timestamp": timestamp
                },
                "timestamp": timestamp
            }

        return {
            "type": "general_alert",
            "message": "Bitcoin market update",
            "data": data,
            "timestamp": timestamp
        }

    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast alert to all registered callbacks"""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                print(f"Error broadcasting alert: {str(e)}")

    async def monitor_bitcoin(self):
        """Main monitoring loop"""
        print("Starting Bitcoin monitoring...")

        while True:
            try:
                # Get current Bitcoin data
                current_price = await self.get_bitcoin_price()
                current_sentiment = await self.get_bitcoin_sentiment()

                if current_price:
                    # Cache price data
                    await self.cache_bitcoin_data(current_price, "price")

                    # Check price alert conditions
                    if await self.check_price_alert_conditions(current_price):
                        alert = await self.generate_alert("price", current_price)
                        await self.broadcast_alert(alert)

                    # Check volume alert conditions
                    if await self.check_volume_alert_conditions(current_price):
                        alert = await self.generate_alert("volume", current_price)
                        await self.broadcast_alert(alert)

                    # Update last price
                    self.last_price = current_price

                if current_sentiment:
                    # Cache sentiment data
                    await self.cache_bitcoin_data(current_sentiment, "sentiment")

                    # Check sentiment alert conditions
                    if await self.check_sentiment_alert_conditions(current_sentiment):
                        alert = await self.generate_alert("sentiment", current_sentiment)
                        await self.broadcast_alert(alert)

                    # Update last sentiment
                    self.last_sentiment = current_sentiment

                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitor_interval)

            except Exception as e:
                print(f"Error in Bitcoin monitoring loop: {str(e)}")
                await asyncio.sleep(self.monitor_interval)

    async def get_cached_data(self, data_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cached Bitcoin data"""
        if not self.redis_client:
            return []

        try:
            pattern = f"bitcoin:{data_type}:*"
            keys = await self.redis_client.keys(pattern)
            keys.sort(reverse=True)  # Most recent first

            data = []
            for key in keys[:limit]:
                value = await self.redis_client.get(key)
                if value:
                    data.append(json.loads(value))

            return data
        except Exception as e:
            print(f"Error getting cached data: {str(e)}")
            return []

    async def get_market_summary(self) -> Dict[str, Any]:
        """Get comprehensive Bitcoin market summary"""
        try:
            current_price = await self.get_bitcoin_price()
            current_sentiment = await self.get_bitcoin_sentiment()

            return {
                "price": current_price,
                "sentiment": current_sentiment,
                "timestamp": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting market summary: {str(e)}")
            return {
                "price": None,
                "sentiment": None,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
