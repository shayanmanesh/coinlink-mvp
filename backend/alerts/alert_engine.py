import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config.settings import settings

class BitcoinAlertEngine:
    def __init__(self):
        self.active_alerts = []
        self.alert_history = []
        self.max_history = 100
        self.alert_callbacks = []
        
    async def add_alert_callback(self, callback):
        """Add callback function for alert notifications"""
        self.alert_callbacks.append(callback)
    
    async def generate_price_alert(self, price_data: Dict[str, Any], previous_price: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Generate price-based alert"""
        try:
            current_price = price_data.get('price', 0)
            current_change = price_data.get('change_24h', 0)
            
            alert = {
                "id": f"price_{int(datetime.now().timestamp())}",
                "type": "price",
                "severity": "medium",
                "message": "",
                "data": {
                    "current_price": current_price,
                    "change_24h": current_change,
                    "timestamp": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            # Determine alert message based on price movement
            if abs(current_change) >= 10:
                alert["severity"] = "high"
                alert["message"] = f"🚨 Bitcoin {'surged' if current_change > 0 else 'plummeted'} {abs(current_change):.1f}% in 24h - ${current_price:,.2f}"
            elif abs(current_change) >= 5:
                alert["severity"] = "medium"
                alert["message"] = f"📈 Bitcoin {'up' if current_change > 0 else 'down'} {abs(current_change):.1f}% - ${current_price:,.2f}"
            elif abs(current_change) >= 2:
                alert["severity"] = "low"
                alert["message"] = f"📊 Bitcoin moved {abs(current_change):.1f}% - ${current_price:,.2f}"
            else:
                return None  # No alert for small movements
            
            return alert
            
        except Exception as e:
            print(f"Error generating price alert: {str(e)}")
            return None
    
    async def generate_volume_alert(self, price_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate volume-based alert"""
        try:
            volume = price_data.get('volume', 0)
            
            # Volume thresholds (in USD)
            high_volume_threshold = 5000000  # 5M
            medium_volume_threshold = 2000000  # 2M
            
            if volume >= high_volume_threshold:
                alert = {
                    "id": f"volume_{int(datetime.now().timestamp())}",
                    "type": "volume",
                    "severity": "high",
                    "message": f"🔥 Bitcoin volume explosion: ${volume:,.0f}",
                    "data": {
                        "volume": volume,
                        "threshold": high_volume_threshold,
                        "timestamp": datetime.now().isoformat()
                    },
                    "created_at": datetime.now().isoformat(),
                    "active": True
                }
                return alert
            elif volume >= medium_volume_threshold:
                alert = {
                    "id": f"volume_{int(datetime.now().timestamp())}",
                    "type": "volume",
                    "severity": "medium",
                    "message": f"📊 Bitcoin high volume: ${volume:,.0f}",
                    "data": {
                        "volume": volume,
                        "threshold": medium_volume_threshold,
                        "timestamp": datetime.now().isoformat()
                    },
                    "created_at": datetime.now().isoformat(),
                    "active": True
                }
                return alert
            
            return None
            
        except Exception as e:
            print(f"Error generating volume alert: {str(e)}")
            return None
    
    async def generate_sentiment_alert(self, sentiment_data: Dict[str, Any], previous_sentiment: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Generate sentiment-based alert"""
        try:
            current_sentiment = sentiment_data.get('overall_sentiment', 'neutral')
            sentiment_emoji = sentiment_data.get('sentiment_emoji', '⚪')
            positive_count = sentiment_data.get('positive_count', 0)
            negative_count = sentiment_data.get('negative_count', 0)
            total_articles = sentiment_data.get('total_articles', 0)
            
            alert = {
                "id": f"sentiment_{int(datetime.now().timestamp())}",
                "type": "sentiment",
                "severity": "medium",
                "message": "",
                "data": {
                    "sentiment": current_sentiment,
                    "sentiment_emoji": sentiment_emoji,
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "total_articles": total_articles,
                    "timestamp": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            # Determine alert message based on sentiment
            if current_sentiment == "positive" and positive_count >= 5:
                alert["severity"] = "high"
                alert["message"] = f"🟢 Bitcoin bullish sentiment: {positive_count} positive articles"
            elif current_sentiment == "negative" and negative_count >= 5:
                alert["severity"] = "high"
                alert["message"] = f"🔴 Bitcoin bearish sentiment: {negative_count} negative articles"
            elif current_sentiment == "positive":
                alert["severity"] = "medium"
                alert["message"] = f"🟢 Bitcoin sentiment turning positive"
            elif current_sentiment == "negative":
                alert["severity"] = "medium"
                alert["message"] = f"🔴 Bitcoin sentiment turning negative"
            else:
                alert["severity"] = "low"
                alert["message"] = f"⚪ Bitcoin sentiment neutral"
            
            return alert
            
        except Exception as e:
            print(f"Error generating sentiment alert: {str(e)}")
            return None
    
    async def generate_technical_alert(self, price_data: Dict[str, Any], technical_indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate technical analysis alert"""
        try:
            current_price = price_data.get('price', 0)
            
            # Example technical indicators (would be calculated from historical data)
            rsi = technical_indicators.get('rsi', 50)
            sma_50 = technical_indicators.get('sma_50', 0)
            sma_200 = technical_indicators.get('sma_200', 0)
            
            alert = {
                "id": f"technical_{int(datetime.now().timestamp())}",
                "type": "technical",
                "severity": "medium",
                "message": "",
                "data": {
                    "current_price": current_price,
                    "rsi": rsi,
                    "sma_50": sma_50,
                    "sma_200": sma_200,
                    "timestamp": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            # RSI-based alerts
            if rsi >= 70:
                alert["severity"] = "high"
                alert["message"] = f"⚠️ Bitcoin overbought (RSI: {rsi:.1f}) - potential reversal"
            elif rsi <= 30:
                alert["severity"] = "high"
                alert["message"] = f"💡 Bitcoin oversold (RSI: {rsi:.1f}) - potential bounce"
            
            # Moving average alerts
            elif current_price > sma_50 > sma_200:
                alert["severity"] = "medium"
                alert["message"] = f"📈 Bitcoin above 50 & 200 SMA - bullish trend"
            elif current_price < sma_50 < sma_200:
                alert["severity"] = "medium"
                alert["message"] = f"📉 Bitcoin below 50 & 200 SMA - bearish trend"
            
            else:
                return None  # No significant technical signals
            
            return alert
            
        except Exception as e:
            print(f"Error generating technical alert: {str(e)}")
            return None
    
    async def generate_combined_alert(self, price_data: Dict[str, Any], sentiment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate combined price + sentiment alert"""
        try:
            current_price = price_data.get('price', 0)
            current_change = price_data.get('change_24h', 0)
            sentiment = sentiment_data.get('overall_sentiment', 'neutral')
            sentiment_emoji = sentiment_data.get('sentiment_emoji', '⚪')
            
            # Only generate combined alert for significant movements
            if abs(current_change) >= 5:
                alert = {
                    "id": f"combined_{int(datetime.now().timestamp())}",
                    "type": "combined",
                    "severity": "high",
                    "message": f"🚨 Bitcoin {current_change:+.1f}% + {sentiment_emoji} {sentiment} sentiment - ${current_price:,.2f}",
                    "data": {
                        "price": price_data,
                        "sentiment": sentiment_data,
                        "timestamp": datetime.now().isoformat()
                    },
                    "created_at": datetime.now().isoformat(),
                    "active": True
                }
                return alert
            
            return None
            
        except Exception as e:
            print(f"Error generating combined alert: {str(e)}")
            return None
    
    async def process_alert(self, alert: Dict[str, Any]):
        """Process and broadcast alert"""
        try:
            # Add to active alerts
            self.active_alerts.append(alert)
            
            # Add to history
            self.alert_history.append(alert)
            if len(self.alert_history) > self.max_history:
                self.alert_history.pop(0)
            
            # Broadcast to all callbacks
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    print(f"Error in alert callback: {str(e)}")
            
            print(f"Alert processed: {alert['message']}")
            
        except Exception as e:
            print(f"Error processing alert: {str(e)}")
    
    async def deactivate_alert(self, alert_id: str):
        """Deactivate an alert"""
        for alert in self.active_alerts:
            if alert.get('id') == alert_id:
                alert['active'] = False
                break
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [alert for alert in self.active_alerts if alert.get('active', False)]
    
    async def get_alert_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        return self.alert_history[-limit:] if self.alert_history else []
    
    async def clear_old_alerts(self, hours: int = 24):
        """Clear alerts older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        self.active_alerts = [
            alert for alert in self.active_alerts
            if datetime.fromisoformat(alert.get('created_at', '')) > cutoff_time
        ]
        
        self.alert_history = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert.get('created_at', '')) > cutoff_time
        ]
