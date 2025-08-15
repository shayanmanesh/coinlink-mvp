import json
import asyncio
from typing import Dict, Any, List
import logging
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_ids = {}
        self.logger = logging.getLogger("coinlink.ws")
        self.latest_crypto_data: List[Dict[str, Any]] = []
        self.crypto_ws_manager = None  # Will be initialized later
        
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        try:
            await websocket.accept()
            self.logger.info("WebSocket accepted")
        except Exception as e:
            # If already accepted, continue
            self.logger.error(f"WebSocket accept failed: {e}")
        connection_id = str(uuid.uuid4())
        self.active_connections.append(websocket)
        self.connection_ids[websocket] = connection_id
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "message": "Connected to CoinLink Bitcoin Analysis",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        print(f"Client connected: {connection_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            connection_id = self.connection_ids.pop(websocket, None)
            print(f"Client disconnected: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket client"""
        try:
            if websocket in self.active_connections:
                await websocket.send_text(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Error sending personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting message: {str(e)}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_bitcoin_update(self, price_data: Dict[str, Any], sentiment_data: Dict[str, Any] = None):
        """Broadcast Bitcoin price and sentiment update"""
        message = {
            "type": "bitcoin_update",
            "price": price_data,
            "sentiment": sentiment_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast Bitcoin alert"""
        message = {
            "type": "alert",
            "alert": alert,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_chat_message(self, user_message: str, bot_response: str, btc_context: Dict[str, Any] = None):
        """Broadcast chat message"""
        message = {
            "type": "chat_message",
            "user_message": user_message,
            "bot_response": bot_response,
            "btc_context": btc_context,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)

    async def broadcast_agent_chat(self, content: str):
        """Broadcast an agent-initiated chat message (alerts, system notes)."""
        message = {
            "type": "chat_agent_message",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_crypto_update(self, crypto_data: List[Dict[str, Any]]):
        """Broadcast crypto ticker updates to all clients"""
        self.latest_crypto_data = crypto_data
        message = {
            "type": "crypto_ticker_update",
            "data": crypto_data[:50],  # Top 50 only
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def start_crypto_feed(self):
        """Start the cryptocurrency WebSocket feed"""
        try:
            from realtime.crypto_websocket import CoinbaseWebSocketManager
            self.crypto_ws_manager = CoinbaseWebSocketManager()
            # Register callback for crypto updates
            self.crypto_ws_manager.add_update_callback(self.broadcast_crypto_update)
            # Start the WebSocket connection
            asyncio.create_task(self.crypto_ws_manager.start())
            self.logger.info("Started cryptocurrency WebSocket feed")
        except Exception as e:
            self.logger.error(f"Failed to start crypto feed: {e}")

class WebSocketHandler:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self.chat_history = []
        self.max_history = 50
        
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection and messages"""
        await self.manager.connect(websocket)
        
        # Start ping task for keep-alive
        ping_task = asyncio.create_task(self._send_ping_loop(websocket))
        
        try:
            while True:
                # Wait for message from client or timeout for keep-alive
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    message = json.loads(data)
                    # Handle different message types
                    await self.handle_message(message, websocket)
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await self.manager.send_personal_message({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
        except WebSocketDisconnect:
            ping_task.cancel()
            self.manager.disconnect(websocket)
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            ping_task.cancel()
            self.manager.disconnect(websocket)
    
    async def _send_ping_loop(self, websocket: WebSocket):
        """Send periodic ping messages to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(25)  # Send ping every 25 seconds
                await self.manager.send_personal_message({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
        except Exception:
            # Connection closed or error
            pass
    
    async def handle_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Handle incoming WebSocket message"""
        message_type = message.get("type", "")
        
        if message_type == "chat":
            await self.handle_chat_message(message, websocket)
        elif message_type == "ping":
            await self.handle_ping(websocket)
        elif message_type == "pong":
            # Client responded to our ping, connection is alive
            pass
        elif message_type == "get_market_data":
            await self.handle_market_data_request(websocket)
        elif message_type == "get_alerts":
            await self.handle_alerts_request(websocket)
        else:
            await self.send_error("Unknown message type", websocket)
    
    async def handle_chat_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Handle chat message from user"""
        try:
            user_message = message.get("message", "")
            if not user_message.strip():
                return
            
            # Add to chat history
            chat_entry = {
                "user_message": user_message,
                "timestamp": datetime.now().isoformat(),
                "type": "user"
            }
            self.chat_history.append(chat_entry)
            
            # Keep history size manageable
            if len(self.chat_history) > self.max_history:
                self.chat_history.pop(0)
            
            # Send acknowledgment
            await self.manager.send_personal_message({
                "type": "chat_ack",
                "message": "Message received, analyzing Bitcoin...",
                "timestamp": datetime.now().isoformat()
            }, websocket)
            
            # Note: The actual AI analysis will be handled by the main API
            # This is just for WebSocket communication
            
        except Exception as e:
            await self.send_error(f"Error handling chat message: {str(e)}", websocket)
    
    async def handle_ping(self, websocket: WebSocket):
        """Handle ping message"""
        await self.manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, websocket)
    
    async def handle_market_data_request(self, websocket: WebSocket):
        """Handle market data request"""
        try:
            # This would typically fetch from the monitor
            await self.manager.send_personal_message({
                "type": "market_data_response",
                "message": "Market data request received",
                "timestamp": datetime.now().isoformat()
            }, websocket)
        except Exception as e:
            await self.send_error(f"Error handling market data request: {str(e)}", websocket)
    
    async def handle_alerts_request(self, websocket: WebSocket):
        """Handle alerts request"""
        try:
            # This would typically fetch from the monitor
            await self.manager.send_personal_message({
                "type": "alerts_response",
                "message": "Alerts request received",
                "timestamp": datetime.now().isoformat()
            }, websocket)
        except Exception as e:
            await self.send_error(f"Error handling alerts request: {str(e)}", websocket)
    
    async def send_error(self, error_message: str, websocket: WebSocket):
        """Send error message to client"""
        await self.manager.send_personal_message({
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }, websocket)
    
    async def send_chat_response(self, user_message: str, bot_response: str, btc_context: Dict[str, Any] = None):
        """Send chat response to all clients"""
        # Add bot response to history
        chat_entry = {
            "bot_response": bot_response,
            "timestamp": datetime.now().isoformat(),
            "type": "bot"
        }
        self.chat_history.append(chat_entry)
        
        # Keep history size manageable
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)
        
        # Broadcast to all clients
        await self.manager.broadcast_chat_message(user_message, bot_response, btc_context)

    async def send_agent_message(self, content: str):
        """Send an agent-initiated chat message (e.g., alert) to all clients."""
        # Add to history
        chat_entry = {
            "agent_message": content,
            "timestamp": datetime.now().isoformat(),
            "type": "agent"
        }
        self.chat_history.append(chat_entry)
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)
        # Broadcast
        await self.manager.broadcast_agent_chat(content)
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get chat history"""
        return self.chat_history.copy()
    
    async def send_market_update(self, price_data: Dict[str, Any], sentiment_data: Dict[str, Any] = None):
        """Send market update to all clients"""
        await self.manager.broadcast_bitcoin_update(price_data, sentiment_data)
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert to all clients"""
        await self.manager.broadcast_alert(alert)

# Global instances
manager = ConnectionManager()
websocket_handler = WebSocketHandler(manager)
