"""
WebSocket module for real-time communication
Production WebSocket implementation with Redis pub/sub scaling
"""

from .manager import websocket_manager, WebSocketMessage
from .routes import router as websocket_router

__all__ = [
    "websocket_manager",
    "WebSocketMessage", 
    "websocket_router"
]