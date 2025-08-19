"""
WebSocket routes and handlers with authentication
Production-ready WebSocket endpoints with proper error handling
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, Depends, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from .manager import websocket_manager, WebSocketMessage
from ..auth.jwt import extract_bearer_token, jwt_service
from ..auth.service import auth_service
from ..db.database import get_async_session

logger = logging.getLogger(__name__)

# WebSocket router
router = APIRouter()

async def get_client_info(websocket: WebSocket) -> tuple[str, str]:
    """Extract client IP and user agent from WebSocket"""
    # Get client IP (consider proxy headers)
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    # Get user agent from headers
    user_agent = websocket.headers.get("user-agent", "unknown")
    
    return client_ip, user_agent

async def authenticate_websocket_token(token: str, session: AsyncSession) -> Optional[str]:
    """
    Authenticate WebSocket connection using JWT token
    Returns user_id if valid, None if invalid
    """
    try:
        user = await auth_service.verify_access_token(token, session)
        return str(user.id)
    except Exception as e:
        logger.debug(f"WebSocket token authentication failed: {e}")
        return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Main WebSocket endpoint with optional authentication
    
    Authentication can happen:
    1. Via query parameter: /ws?token=<jwt_token>
    2. Via message after connection: {"type": "authenticate", "token": "<jwt_token>"}
    """
    connection_id = None
    user_id = None
    
    try:
        # Get client information
        client_ip, user_agent = get_client_info(websocket)
        
        # Try to authenticate via token parameter
        if token:
            user_id = await authenticate_websocket_token(token, session)
            if user_id:
                logger.info(f"WebSocket authenticated via query parameter: user {user_id}")
        
        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        logger.info(f"WebSocket connection established: {connection_id} (user: {user_id or 'anonymous'})")
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                raw_message = await websocket.receive_text()
                
                try:
                    message_data = json.loads(raw_message)
                except json.JSONDecodeError:
                    await _send_error(websocket, "invalid_json", "Invalid JSON format")
                    continue
                
                # Validate message structure
                if not isinstance(message_data, dict) or "type" not in message_data:
                    await _send_error(websocket, "invalid_message", "Message must have 'type' field")
                    continue
                
                message_type = message_data["type"]
                
                # Handle different message types
                if message_type == "ping":
                    await _handle_ping(websocket, connection_id)
                    
                elif message_type == "authenticate":
                    user_id = await _handle_authenticate(
                        websocket, connection_id, message_data, session
                    )
                    
                elif message_type == "join_channel":
                    await _handle_join_channel(websocket, connection_id, message_data)
                    
                elif message_type == "leave_channel":
                    await _handle_leave_channel(websocket, connection_id, message_data)
                    
                elif message_type == "chat_message":
                    await _handle_chat_message(websocket, connection_id, message_data, user_id)
                    
                elif message_type == "subscribe_bitcoin":
                    await _handle_bitcoin_subscription(websocket, connection_id)
                    
                elif message_type == "unsubscribe_bitcoin":
                    await _handle_bitcoin_unsubscription(websocket, connection_id)
                    
                else:
                    await _send_error(websocket, "unknown_message_type", f"Unknown message type: {message_type}")
                
            except WebSocketDisconnect:
                break
                
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                try:
                    await _send_error(websocket, "internal_error", "Internal server error")
                except:
                    break  # Connection is broken
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally: {connection_id}")
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id)

async def _handle_ping(websocket: WebSocket, connection_id: str):
    """Handle ping message with pong response"""
    response = WebSocketMessage(
        type="pong",
        data={"server_time": datetime.now().isoformat()}
    )
    
    try:
        await websocket.send_json(response.dict())
    except Exception as e:
        logger.error(f"Failed to send pong to {connection_id}: {e}")
        raise

async def _handle_authenticate(
    websocket: WebSocket, 
    connection_id: str, 
    message_data: Dict[str, Any],
    session: AsyncSession
) -> Optional[str]:
    """Handle authentication message"""
    token = message_data.get("token")
    if not token:
        await _send_error(websocket, "missing_token", "Token is required for authentication")
        return None
    
    # Extract bearer token if needed
    if token.startswith("Bearer "):
        token = token[7:]
    
    # Authenticate token
    user_id = await authenticate_websocket_token(token, session)
    if not user_id:
        await _send_error(websocket, "invalid_token", "Invalid or expired token")
        return None
    
    # Update connection in manager
    success = await websocket_manager.authenticate_connection(connection_id, user_id)
    if not success:
        await _send_error(websocket, "auth_failed", "Failed to authenticate connection")
        return None
    
    logger.info(f"WebSocket authenticated via message: {connection_id} -> user {user_id}")
    return user_id

async def _handle_join_channel(websocket: WebSocket, connection_id: str, message_data: Dict[str, Any]):
    """Handle channel join request"""
    channel = message_data.get("channel")
    if not channel:
        await _send_error(websocket, "missing_channel", "Channel name is required")
        return
    
    # Validate channel name
    if not isinstance(channel, str) or not channel.strip():
        await _send_error(websocket, "invalid_channel", "Channel name must be a non-empty string")
        return
    
    channel = channel.strip().lower()
    
    # Join channel
    success = await websocket_manager.join_channel(connection_id, channel)
    if not success:
        await _send_error(websocket, "join_failed", f"Failed to join channel: {channel}")

async def _handle_leave_channel(websocket: WebSocket, connection_id: str, message_data: Dict[str, Any]):
    """Handle channel leave request"""
    channel = message_data.get("channel")
    if not channel:
        await _send_error(websocket, "missing_channel", "Channel name is required")
        return
    
    channel = channel.strip().lower()
    
    # Leave channel
    success = await websocket_manager.leave_channel(connection_id, channel)
    if not success:
        await _send_error(websocket, "leave_failed", f"Failed to leave channel: {channel}")

async def _handle_chat_message(
    websocket: WebSocket, 
    connection_id: str, 
    message_data: Dict[str, Any],
    user_id: Optional[str]
):
    """Handle chat message"""
    message = message_data.get("message", "").strip()
    channel = message_data.get("channel", "general").strip().lower()
    
    if not message:
        await _send_error(websocket, "empty_message", "Message cannot be empty")
        return
    
    if len(message) > 1000:
        await _send_error(websocket, "message_too_long", "Message exceeds maximum length (1000 characters)")
        return
    
    # For MVP, we'll implement a simple echo bot
    bot_response = _generate_bot_response(message)
    
    # Create chat response message
    chat_response = WebSocketMessage(
        type="chat_response",
        data={
            "channel": channel,
            "user_message": message,
            "bot_response": bot_response,
            "user_id": user_id,
            "authenticated": bool(user_id)
        }
    )
    
    # Send back to the user
    try:
        await websocket.send_json(chat_response.dict())
    except Exception as e:
        logger.error(f"Failed to send chat response to {connection_id}: {e}")
        raise
    
    # Also broadcast to channel if others are subscribed (for future enhancement)
    if channel != "private":
        await websocket_manager.send_to_channel(channel, chat_response)

async def _handle_bitcoin_subscription(websocket: WebSocket, connection_id: str):
    """Handle Bitcoin price subscription"""
    success = await websocket_manager.join_channel(connection_id, "bitcoin_prices")
    
    if success:
        # Send current Bitcoin price
        bitcoin_update = WebSocketMessage(
            type="bitcoin_price",
            data={
                "price": 97420.15,  # Mock price for MVP
                "change_24h": 2.34,
                "volume_24h": 28500000000,
                "status": "subscribed"
            }
        )
        
        try:
            await websocket.send_json(bitcoin_update.dict())
        except Exception as e:
            logger.error(f"Failed to send Bitcoin price to {connection_id}: {e}")
            raise

async def _handle_bitcoin_unsubscription(websocket: WebSocket, connection_id: str):
    """Handle Bitcoin price unsubscription"""
    await websocket_manager.leave_channel(connection_id, "bitcoin_prices")
    
    try:
        unsubscribe_response = WebSocketMessage(
            type="bitcoin_unsubscribed",
            data={"status": "unsubscribed"}
        )
        await websocket.send_json(unsubscribe_response.dict())
    except Exception as e:
        logger.error(f"Failed to send unsubscribe confirmation to {connection_id}: {e}")

async def _send_error(websocket: WebSocket, error_code: str, error_message: str):
    """Send error message to WebSocket client"""
    error_response = WebSocketMessage(
        type="error",
        data={
            "error_code": error_code,
            "error_message": error_message
        }
    )
    
    try:
        await websocket.send_json(error_response.dict())
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")
        raise

def _generate_bot_response(user_message: str) -> str:
    """
    Generate a simple bot response for MVP
    In production, this would connect to AI/ML services
    """
    message_lower = user_message.lower()
    
    # Simple keyword-based responses
    if any(keyword in message_lower for keyword in ["price", "bitcoin", "btc"]):
        return "Bitcoin is currently trading at $97,420.15, up 2.34% in the last 24 hours. The market is showing strong momentum!"
    
    elif any(keyword in message_lower for keyword in ["buy", "sell", "trade"]):
        return "I can't provide trading advice, but I can help you stay informed about market trends and analysis."
    
    elif any(keyword in message_lower for keyword in ["hello", "hi", "hey"]):
        return "Hello! I'm your Bitcoin analysis assistant. Ask me about Bitcoin prices, trends, or market analysis."
    
    elif any(keyword in message_lower for keyword in ["help", "what", "how"]):
        return "I can help you with Bitcoin price information, market analysis, and trading insights. Try asking about Bitcoin price or market trends!"
    
    else:
        return f"Thanks for your message: '{user_message}'. I'm analyzing Bitcoin market data and trends. What would you like to know about Bitcoin?"

# REST endpoint for WebSocket statistics (for monitoring)
@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket manager statistics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "websocket_stats": websocket_manager.get_stats()
    }