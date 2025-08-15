"""
Simplified production API for Railway deployment
MVP version with core features only
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CoinLink Production API...")
    yield
    # Shutdown
    logger.info("Shutting down CoinLink Production API...")

# Create FastAPI app
app = FastAPI(
    title="CoinLink MVP API",
    description="Simplified production API for CoinLink",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-oyhz3vvwf-shayans-projects-ede8d66b.vercel.app",
        "https://*.vercel.app",
        "https://coin.link",
        "https://www.coin.link",
        "http://localhost:3000"  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "CoinLink MVP API",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connections": len(manager.active_connections)
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to CoinLink",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle different message types
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "chat":
                    # Simple echo for MVP
                    response = {
                        "type": "chat_response",
                        "user_message": data.get("message", ""),
                        "bot_response": f"Bitcoin is currently showing strong momentum. Your message: {data.get('message', '')}",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_json(response)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        manager.disconnect(websocket)

# Chat endpoint (REST fallback)
@app.post("/api/chat")
async def chat_endpoint(payload: Dict[str, Any]):
    """REST API endpoint for chat (fallback if WebSocket fails)"""
    try:
        user_message = payload.get("message", "")
        
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Simple response for MVP
        return {
            "type": "chat",
            "user_message": user_message,
            "bot_response": f"Bitcoin analysis: The market is showing interesting patterns. Your query: {user_message}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bitcoin price endpoint (mock for MVP)
@app.get("/api/bitcoin/price")
async def get_bitcoin_price():
    """Get current Bitcoin price (mock data for MVP)"""
    return {
        "data": {
            "price": 97420.15,
            "change_24h": 2.34,
            "volume_24h": 28500000000,
            "timestamp": datetime.now().isoformat()
        }
    }

# Active connections count
@app.get("/api/connections")
async def get_connections():
    return {
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

# Crypto ticker endpoint (mock for MVP)
@app.get("/api/crypto/ticker")
async def get_crypto_ticker():
    """Get crypto ticker data (simplified for MVP)"""
    return {
        "data": [
            {"symbol": "BTC", "price": 97420.15, "change_24h": 2.34},
            {"symbol": "ETH", "price": 3250.80, "change_24h": 1.89},
            {"symbol": "SOL", "price": 145.67, "change_24h": 5.12},
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)