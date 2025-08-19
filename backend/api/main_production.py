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

# Import agent routes with detailed error handling
agents_router = None
rd_status_router = None
rd_router = None

logger = logging.getLogger(__name__)

try:
    from .routes.agents import router as agents_router
    logger.info("Successfully imported agents_router")
except ImportError as e:
    logger.error(f"Failed to import agents_router: {e}")
    # Fallback for development
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    try:
        from api.routes.agents import router as agents_router
        logger.info("Successfully imported agents_router (fallback)")
    except ImportError as e2:
        logger.error(f"Fallback import of agents_router also failed: {e2}")

try:
    from .routes.rd_status import router as rd_status_router  
    logger.info("Successfully imported rd_status_router")
except ImportError as e:
    logger.error(f"Failed to import rd_status_router: {e}")
    try:
        from api.routes.rd_status import router as rd_status_router
        logger.info("Successfully imported rd_status_router (fallback)")
    except ImportError as e2:
        logger.error(f"Fallback import of rd_status_router also failed: {e2}")

try:
    from .routes.rd_routes import router as rd_router
    logger.info("Successfully imported rd_router")
except ImportError as e:
    logger.warning(f"Failed to import rd_router (expected): {e}")
    try:
        from api.routes.rd_routes import router as rd_router
        logger.info("Successfully imported rd_router (fallback)")
    except ImportError as e2:
        logger.warning(f"Fallback import of rd_router also failed (expected): {e2}")

# Configure logging
logging.basicConfig(level=logging.INFO)

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
    
    # Initialize agent system
    try:
        from ..agents.claude_agent_interface import claude_agents
        from ..agents.monitoring import agent_monitor
        
        logger.info(f"Agent system initialized with {len(claude_agents.agents)} agents")
        
        # Start agent monitoring
        await agent_monitor.start_monitoring()
        logger.info("Agent monitoring system started")
        
    except Exception as e:
        logger.warning(f"Agent system initialization failed: {e}")
    
    # Initialize R&D system
    try:
        from ..rd.rd_interface import rd_agents
        from ..rd.rd_metrics import rd_metrics_tracker
        from ..rd.innovation_pipeline import innovation_pipeline
        
        logger.info(f"R&D system initialized with {len(rd_agents.agents)} R&D agents")
        
        # Initialize agent metrics
        for agent_name, agent_info in rd_agents.agents.items():
            rd_metrics_tracker.initialize_agent_metrics(agent_name, agent_info.specialization)
        
        # Start innovation cycle if none active
        if not rd_agents.current_cycle_id:
            cycle_id = rd_agents.start_innovation_cycle()
            rd_metrics_tracker.start_innovation_cycle(cycle_id)
            logger.info(f"Started initial R&D innovation cycle: {cycle_id}")
        
        logger.info("R&D department system initialized successfully")
        
    except Exception as e:
        logger.warning(f"R&D system initialization failed: {e}")
    
    # Initialize R&D scheduler for 30-minute reporting
    try:
        from ..rd.scheduler import rd_scheduler
        
        await rd_scheduler.start_scheduler()
        logger.info("R&D 30-minute reporting scheduler started successfully")
        
    except Exception as e:
        logger.warning(f"R&D scheduler initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CoinLink Production API...")
    
    # Stop R&D scheduler
    try:
        from ..rd.scheduler import rd_scheduler
        if rd_scheduler.is_running:
            await rd_scheduler.stop_scheduler()
            logger.info("R&D scheduler stopped successfully")
    except Exception as e:
        logger.warning(f"Error stopping R&D scheduler: {e}")
    
    # Stop agent monitoring
    try:
        from ..agents.monitoring import agent_monitor
        await agent_monitor.stop_monitoring()
        logger.info("Agent monitoring stopped")
    except Exception as e:
        logger.warning(f"Error stopping agent monitoring: {e}")

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

# Include agent routes
if agents_router is not None:
    app.include_router(agents_router)
    logger.info("Agent routes included successfully")
else:
    logger.error("Agent routes not included - import failed")

if rd_status_router is not None:
    app.include_router(rd_status_router)
    logger.info("R&D status routes included successfully")
else:
    logger.error("R&D status routes not included - import failed")

if rd_router is not None:
    app.include_router(rd_router)
    logger.info("R&D routes included successfully")
else:
    logger.warning("R&D routes not included - import issues (expected)")

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
        "connections": len(manager.active_connections),
        "routes_loaded": {
            "agents": agents_router is not None,
            "rd_status": rd_status_router is not None, 
            "rd_full": rd_router is not None
        }
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

# Alert endpoints
@app.get("/api/alerts")
async def get_alerts():
    """Get active alerts"""
    try:
        # Simple mock alerts for MVP
        return {
            "alerts": [],
            "count": 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/history")
async def get_alert_history(limit: int = 20):
    """Get alert history"""
    try:
        return {
            "history": [],
            "count": 0,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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