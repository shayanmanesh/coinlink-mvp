"""
Production WebSocket connection manager with Redis pub/sub
Supports horizontal scaling and multi-worker deployments
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Any, Optional, List
import uuid

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..config.settings import settings

logger = logging.getLogger(__name__)

class WebSocketMessage(BaseModel):
    """Standard WebSocket message format"""
    type: str
    data: Dict[str, Any]
    timestamp: str = None
    user_id: Optional[str] = None
    connection_id: Optional[str] = None
    
    def __init__(self, **data):
        if not data.get("timestamp"):
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)

class Connection(BaseModel):
    """WebSocket connection metadata"""
    id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    channels: Set[str] = set()
    authenticated: bool = False
    connected_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class WebSocketManager:
    """
    Production WebSocket manager with Redis pub/sub for scaling
    Handles authentication, channels, and message broadcasting
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub = None
        
        # Local connections (this worker instance)
        self.connections: Dict[str, Connection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.channel_connections: Dict[str, Set[str]] = {}  # channel -> connection_ids
        
        # Redis channels for pub/sub
        self.broadcast_channel = "coinlink:broadcast"
        self.user_channel_prefix = "coinlink:user:"
        self.topic_channel_prefix = "coinlink:topic:"
        
        # Heartbeat and cleanup
        self._heartbeat_task = None
        self._cleanup_task = None
        self._pubsub_task = None
        
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize Redis connection and start background tasks"""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("WebSocket manager Redis connection established")
            
            # Initialize pub/sub
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(
                self.broadcast_channel,
                f"{self.topic_channel_prefix}*",
                f"{self.user_channel_prefix}*"
            )
            
            # Start background tasks
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._pubsub_task = asyncio.create_task(self._pubsub_loop())
            
            logger.info("WebSocket manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")
            # Continue without Redis (degraded mode)
            self.redis_client = None
            logger.warning("WebSocket manager running in degraded mode (no Redis)")
    
    async def shutdown(self):
        """Shutdown WebSocket manager and cleanup resources"""
        logger.info("Shutting down WebSocket manager...")
        
        # Cancel background tasks
        for task in [self._heartbeat_task, self._cleanup_task, self._pubsub_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Disconnect all WebSocket connections
        connections_copy = list(self.connections.values())
        for connection in connections_copy:
            try:
                await connection.websocket.close()
            except:
                pass
        
        self.connections.clear()
        self.user_connections.clear()
        self.channel_connections.clear()
        
        # Close Redis connections
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("WebSocket manager shutdown complete")
    
    async def connect(self, websocket: WebSocket, user_id: str = None, 
                     ip_address: str = None, user_agent: str = None) -> str:
        """
        Accept new WebSocket connection and return connection ID
        """
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        now = datetime.now()
        
        connection = Connection(
            id=connection_id,
            websocket=websocket,
            user_id=user_id,
            authenticated=bool(user_id),
            connected_at=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store connection
        self.connections[connection_id] = connection
        
        # Index by user_id if authenticated
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # Send welcome message
        await self._send_to_connection(connection_id, WebSocketMessage(
            type="connected",
            data={
                "connection_id": connection_id,
                "authenticated": connection.authenticated,
                "user_id": user_id,
                "server_time": now.isoformat()
            }
        ))
        
        # Publish connection event to Redis
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    self.broadcast_channel,
                    json.dumps({
                        "event": "user_connected",
                        "connection_id": connection_id,
                        "user_id": user_id,
                        "timestamp": now.isoformat()
                    })
                )
            except Exception as e:
                logger.error(f"Failed to publish connection event: {e}")
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id or 'anonymous'})")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket and cleanup"""
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        # Remove from user index
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from channel indexes
        for channel in list(connection.channels):
            await self._leave_channel(connection_id, channel)
        
        # Remove connection
        del self.connections[connection_id]
        
        # Publish disconnection event
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    self.broadcast_channel,
                    json.dumps({
                        "event": "user_disconnected", 
                        "connection_id": connection_id,
                        "user_id": connection.user_id,
                        "timestamp": datetime.now().isoformat()
                    })
                )
            except Exception as e:
                logger.error(f"Failed to publish disconnection event: {e}")
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def authenticate_connection(self, connection_id: str, user_id: str):
        """Authenticate a connection with user ID"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        # Update connection
        connection.user_id = user_id
        connection.authenticated = True
        
        # Add to user index
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Send authentication confirmation
        await self._send_to_connection(connection_id, WebSocketMessage(
            type="authenticated",
            data={
                "user_id": user_id,
                "status": "authenticated"
            }
        ))
        
        logger.info(f"Connection {connection_id} authenticated as user {user_id}")
        return True
    
    async def join_channel(self, connection_id: str, channel: str):
        """Join a connection to a channel"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        # Add to connection channels
        connection.channels.add(channel)
        
        # Add to channel index
        if channel not in self.channel_connections:
            self.channel_connections[channel] = set()
        self.channel_connections[channel].add(connection_id)
        
        await self._send_to_connection(connection_id, WebSocketMessage(
            type="channel_joined",
            data={"channel": channel}
        ))
        
        logger.debug(f"Connection {connection_id} joined channel {channel}")
        return True
    
    async def leave_channel(self, connection_id: str, channel: str):
        """Leave a channel"""
        return await self._leave_channel(connection_id, channel)
    
    async def _leave_channel(self, connection_id: str, channel: str):
        """Internal method to leave channel"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        # Remove from connection channels
        connection.channels.discard(channel)
        
        # Remove from channel index
        if channel in self.channel_connections:
            self.channel_connections[channel].discard(connection_id)
            if not self.channel_connections[channel]:
                del self.channel_connections[channel]
        
        await self._send_to_connection(connection_id, WebSocketMessage(
            type="channel_left",
            data={"channel": channel}
        ))
        
        logger.debug(f"Connection {connection_id} left channel {channel}")
        return True
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send message to all connections for a specific user"""
        # Local connections
        connection_ids = self.user_connections.get(user_id, set())
        local_sent = 0
        
        for connection_id in list(connection_ids):  # Copy to avoid modification during iteration
            if await self._send_to_connection(connection_id, message):
                local_sent += 1
        
        # Publish to Redis for other workers
        if self.redis_client:
            try:
                redis_message = {
                    "target_type": "user",
                    "target_id": user_id,
                    "message": message.dict(),
                    "sender_worker": id(self)  # Avoid echo
                }
                
                await self.redis_client.publish(
                    f"{self.user_channel_prefix}{user_id}",
                    json.dumps(redis_message)
                )
            except Exception as e:
                logger.error(f"Failed to publish user message to Redis: {e}")
        
        logger.debug(f"Sent message to user {user_id}: {local_sent} local connections")
        return local_sent
    
    async def send_to_channel(self, channel: str, message: WebSocketMessage):
        """Send message to all connections in a channel"""
        # Local connections
        connection_ids = self.channel_connections.get(channel, set())
        local_sent = 0
        
        for connection_id in list(connection_ids):
            if await self._send_to_connection(connection_id, message):
                local_sent += 1
        
        # Publish to Redis for other workers
        if self.redis_client:
            try:
                redis_message = {
                    "target_type": "channel",
                    "target_id": channel,
                    "message": message.dict(),
                    "sender_worker": id(self)
                }
                
                await self.redis_client.publish(
                    f"{self.topic_channel_prefix}{channel}",
                    json.dumps(redis_message)
                )
            except Exception as e:
                logger.error(f"Failed to publish channel message to Redis: {e}")
        
        logger.debug(f"Sent message to channel {channel}: {local_sent} local connections")
        return local_sent
    
    async def broadcast(self, message: WebSocketMessage):
        """Broadcast message to all connections"""
        # Local connections
        local_sent = 0
        for connection_id in list(self.connections.keys()):
            if await self._send_to_connection(connection_id, message):
                local_sent += 1
        
        # Publish to Redis for other workers
        if self.redis_client:
            try:
                redis_message = {
                    "target_type": "broadcast",
                    "message": message.dict(),
                    "sender_worker": id(self)
                }
                
                await self.redis_client.publish(
                    self.broadcast_channel,
                    json.dumps(redis_message)
                )
            except Exception as e:
                logger.error(f"Failed to publish broadcast to Redis: {e}")
        
        logger.debug(f"Broadcast message: {local_sent} local connections")
        return local_sent
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific connection"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        try:
            # Update activity timestamp
            connection.last_activity = datetime.now()
            
            # Add connection info to message
            message.connection_id = connection_id
            message.user_id = connection.user_id
            
            await connection.websocket.send_json(message.dict())
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send message to {connection_id}: {e}")
            # Connection is likely dead, disconnect it
            await self.disconnect(connection_id)
            return False
    
    async def _pubsub_loop(self):
        """Background task to handle Redis pub/sub messages"""
        if not self.pubsub:
            return
        
        logger.info("Starting WebSocket pub/sub listener")
        
        try:
            async for redis_message in self.pubsub.listen():
                if redis_message["type"] != "message":
                    continue
                
                try:
                    data = json.loads(redis_message["data"])
                    sender_worker = data.get("sender_worker")
                    
                    # Skip messages from this worker (avoid echo)
                    if sender_worker == id(self):
                        continue
                    
                    target_type = data.get("target_type")
                    target_id = data.get("target_id")
                    message_data = data.get("message", {})
                    
                    message = WebSocketMessage(**message_data)
                    
                    # Route message based on target type
                    if target_type == "broadcast":
                        await self._handle_local_broadcast(message)
                    elif target_type == "user" and target_id:
                        await self._handle_local_user_message(target_id, message)
                    elif target_type == "channel" and target_id:
                        await self._handle_local_channel_message(target_id, message)
                    
                except Exception as e:
                    logger.error(f"Error processing pub/sub message: {e}")
                    
        except Exception as e:
            logger.error(f"Pub/sub loop error: {e}")
    
    async def _handle_local_broadcast(self, message: WebSocketMessage):
        """Handle broadcast message from Redis"""
        for connection_id in list(self.connections.keys()):
            await self._send_to_connection(connection_id, message)
    
    async def _handle_local_user_message(self, user_id: str, message: WebSocketMessage):
        """Handle user-targeted message from Redis"""
        connection_ids = self.user_connections.get(user_id, set())
        for connection_id in list(connection_ids):
            await self._send_to_connection(connection_id, message)
    
    async def _handle_local_channel_message(self, channel: str, message: WebSocketMessage):
        """Handle channel-targeted message from Redis"""
        connection_ids = self.channel_connections.get(channel, set())
        for connection_id in list(connection_ids):
            await self._send_to_connection(connection_id, message)
    
    async def _heartbeat_loop(self):
        """Background task for connection heartbeat and health monitoring"""
        logger.info("Starting WebSocket heartbeat loop")
        
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send ping to all connections
                ping_message = WebSocketMessage(
                    type="ping",
                    data={"server_time": datetime.now().isoformat()}
                )
                
                for connection_id in list(self.connections.keys()):
                    await self._send_to_connection(connection_id, ping_message)
                
                logger.debug(f"Heartbeat sent to {len(self.connections)} connections")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
    
    async def _cleanup_loop(self):
        """Background task for cleaning up stale connections"""
        logger.info("Starting WebSocket cleanup loop")
        
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.now()
                stale_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Check for stale connections
                    time_since_activity = (now - connection.last_activity).total_seconds()
                    if time_since_activity > self.connection_timeout:
                        stale_connections.append(connection_id)
                
                # Cleanup stale connections
                for connection_id in stale_connections:
                    logger.info(f"Cleaning up stale connection: {connection_id}")
                    await self.disconnect(connection_id)
                
                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale connections")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            "total_connections": len(self.connections),
            "authenticated_connections": sum(1 for c in self.connections.values() if c.authenticated),
            "anonymous_connections": sum(1 for c in self.connections.values() if not c.authenticated),
            "total_users": len(self.user_connections),
            "total_channels": len(self.channel_connections),
            "redis_connected": bool(self.redis_client),
            "background_tasks_running": sum(1 for task in [
                self._heartbeat_task, self._cleanup_task, self._pubsub_task
            ] if task and not task.done())
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()