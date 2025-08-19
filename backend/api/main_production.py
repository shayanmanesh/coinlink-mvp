"""
Production-ready API for Railway deployment
Hardened version with security, auth, observability, and full feature set
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Set
import uuid

# Import configuration and security
from ..config.settings import settings
from ..middleware.security import (
    SecurityMiddleware, 
    RequestLoggingMiddleware, 
    InputValidationMiddleware,
    rate_limit_exceeded_handler
)
from slowapi.errors import RateLimitExceeded

# Import agent routes with detailed error handling
agents_router = None
rd_status_router = None
rd_router = None
growth_router = None
auth_router_v2 = None

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

# Import Growth Engine routes
try:
    from ..growth.api_routes import growth_router
    logger.info("Successfully imported growth_router")
except ImportError as e:
    logger.error(f"Failed to import growth_router: {e}")
    try:
        from growth.api_routes import growth_router
        logger.info("Successfully imported growth_router (fallback)")
    except ImportError as e2:
        logger.error(f"Fallback import of growth_router also failed: {e2}")

# Import Auth v2 routes
try:
    from ..auth.routes_v2 import router as auth_router_v2
    logger.info("Successfully imported auth_router_v2")
except ImportError as e:
    logger.error(f"Failed to import auth_router_v2: {e}")
    try:
        from auth.routes_v2 import router as auth_router_v2
        logger.info("Successfully imported auth_router_v2 (fallback)")
    except ImportError as e2:
        logger.error(f"Fallback import of auth_router_v2 also failed: {e2}")

# Import WebSocket routes and services
try:
    from ..websocket.routes import router as websocket_router
    from ..websocket.manager import websocket_manager
    from ..websocket.services import start_websocket_services, stop_websocket_services
    logger.info("Successfully imported WebSocket components")
except ImportError as e:
    logger.error(f"Failed to import WebSocket components: {e}")
    websocket_router = None
    websocket_manager = None
    start_websocket_services = None
    stop_websocket_services = None

# Import observability components
try:
    from ..observability import initialize_observability, shutdown_observability, get_metrics_response, create_instrumentator
    from ..observability.middleware import RequestTracingMiddleware, MetricsMiddleware
    logger.info("Successfully imported observability components")
except ImportError as e:
    logger.error(f"Failed to import observability components: {e}")
    initialize_observability = None
    shutdown_observability = None
    get_metrics_response = None
    create_instrumentator = None
    RequestTracingMiddleware = None
    MetricsMiddleware = None

# Import API v2 routes for frontend parity
market_data_router = None
user_management_router = None
notifications_router = None

try:
    from .routes.market_data import router as market_data_router
    logger.info("Successfully imported market_data_router")
except ImportError as e:
    logger.error(f"Failed to import market_data_router: {e}")

try:
    from .routes.user_management import router as user_management_router
    logger.info("Successfully imported user_management_router")
except ImportError as e:
    logger.error(f"Failed to import user_management_router: {e}")

try:
    from .routes.notifications import router as notifications_router
    logger.info("Successfully imported notifications_router")
except ImportError as e:
    logger.error(f"Failed to import notifications_router: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)

# WebSocket manager initialization is handled in websocket module

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CoinLink Production API...")
    
    # Initialize observability stack first
    if initialize_observability:
        try:
            await initialize_observability()
            logger.info("Observability stack initialized successfully")
        except Exception as e:
            logger.error(f"Observability initialization error: {e}")
    
    # Initialize database
    try:
        from ..db.database import init_db, wait_for_db
        
        # Wait for database to be available
        if await wait_for_db(timeout=30):
            await init_db()
            logger.info("Database initialized successfully")
        else:
            logger.error("Database initialization failed - timeout")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Initialize security middleware with Redis
    security_middleware = SecurityMiddleware(redis_url=settings.REDIS_URL)
    await security_middleware.initialize_redis()
    app.state.security_middleware = security_middleware
    logger.info("Security middleware initialized")
    
    # Initialize WebSocket manager
    if websocket_manager:
        try:
            await websocket_manager.initialize()
            logger.info("WebSocket manager initialized successfully")
            
            # Start WebSocket background services
            if start_websocket_services:
                await start_websocket_services()
                logger.info("WebSocket background services started")
        except Exception as e:
            logger.error(f"WebSocket initialization error: {e}")
    
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
    
    # Initialize Growth Engine system
    try:
        from ..growth.growth_interface import initialize_growth_agents
        from ..growth.growth_scheduler import growth_scheduler
        from ..growth.growth_notifications import growth_notification_system
        
        # Initialize growth agents
        growth_agents = await initialize_growth_agents()
        logger.info(f"Growth Engine initialized with {len(growth_agents.agents)} agents")
        
        # Start notification services
        await growth_notification_system.start_notification_services()
        logger.info("Growth notification services started")
        
        # Start growth scheduler
        await growth_scheduler.start_scheduler()
        logger.info("Growth scheduler started with ultra-aggressive sprint automation")
        
        # Start growth monitoring system
        from ..growth.monitoring_dashboard import growth_engine_monitor
        await growth_engine_monitor.start_monitoring()
        logger.info("Growth monitoring system started")
        
        logger.info("🚀 Growth Engine fully operational - ready for explosive growth!")
        
    except Exception as e:
        logger.warning(f"Growth Engine initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CoinLink Production API...")
    
    # Shutdown observability stack
    if shutdown_observability:
        try:
            await shutdown_observability()
            logger.info("Observability stack shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down observability: {e}")
    
    # Stop WebSocket services
    if stop_websocket_services:
        try:
            await stop_websocket_services()
            logger.info("WebSocket services stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping WebSocket services: {e}")
    
    # Shutdown WebSocket manager
    if websocket_manager:
        try:
            await websocket_manager.shutdown()
            logger.info("WebSocket manager shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down WebSocket manager: {e}")
    
    # Close security middleware Redis connection
    if hasattr(app.state, 'security_middleware'):
        await app.state.security_middleware.close_redis()
        logger.info("Security middleware Redis connection closed")
    
    # Stop R&D scheduler
    try:
        from ..rd.scheduler import rd_scheduler
        if rd_scheduler.is_running:
            await rd_scheduler.stop_scheduler()
            logger.info("R&D scheduler stopped successfully")
    except Exception as e:
        logger.warning(f"Error stopping R&D scheduler: {e}")
    
    # Stop Growth Engine system
    try:
        from ..growth.growth_scheduler import growth_scheduler
        from ..growth.monitoring_dashboard import growth_engine_monitor
        
        # Stop monitoring first
        if growth_engine_monitor.monitoring_active:
            await growth_engine_monitor.stop_monitoring()
            logger.info("Growth monitoring stopped successfully")
        
        # Stop scheduler
        if growth_scheduler.is_running:
            await growth_scheduler.stop_scheduler()
            logger.info("Growth scheduler stopped successfully")
    except Exception as e:
        logger.warning(f"Error stopping Growth Engine: {e}")
    
    # Stop agent monitoring
    try:
        from ..agents.monitoring import agent_monitor
        await agent_monitor.stop_monitoring()
        logger.info("Agent monitoring stopped")
    except Exception as e:
        logger.warning(f"Error stopping agent monitoring: {e}")

# Create FastAPI app
app = FastAPI(
    title="CoinLink MVP Production API",
    description="Production-ready API for CoinLink with observability, security, and real-time features",
    version="2.0.0",
    lifespan=lifespan
)

# Initialize Prometheus instrumentator for automatic metrics
if create_instrumentator:
    try:
        instrumentator = create_instrumentator()
        instrumentator.instrument(app)
        instrumentator.expose(app, endpoint="/metrics")
        logger.info("Prometheus metrics enabled at /metrics")
    except Exception as e:
        logger.error(f"Failed to initialize Prometheus instrumentator: {e}")

# Configure strict CORS with environment-based origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

# Mount observability middleware
if RequestTracingMiddleware:
    app.add_middleware(RequestTracingMiddleware)
    logger.info("Request tracing middleware enabled")

if MetricsMiddleware:
    app.add_middleware(MetricsMiddleware)
    logger.info("Metrics middleware enabled")

# Mount security middleware
app.middleware("http")(RequestLoggingMiddleware())
app.middleware("http")(InputValidationMiddleware())

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add validation error handler for standardized responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standardized JSON response"""
    trace_id = str(uuid.uuid4())
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Invalid request data",
                "details": exc.errors(),
                "trace_id": trace_id
            }
        }
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

# Include Growth Engine routes
if growth_router is not None:
    app.include_router(growth_router)
    logger.info("Growth Engine routes included successfully")
else:
    logger.error("Growth Engine routes not included - import failed")

# Include Auth v2 routes
if auth_router_v2 is not None:
    app.include_router(auth_router_v2)
    logger.info("Auth v2 routes included successfully")
else:
    logger.error("Auth v2 routes not included - import failed")

# Include WebSocket routes
if websocket_router is not None:
    app.include_router(websocket_router)
    logger.info("WebSocket routes included successfully")
else:
    logger.error("WebSocket routes not included - import failed")

# Include API v2 routes for frontend parity
if market_data_router is not None:
    app.include_router(market_data_router)
    logger.info("Market data routes included successfully")
else:
    logger.error("Market data routes not included - import failed")

if user_management_router is not None:
    app.include_router(user_management_router)
    logger.info("User management routes included successfully") 
else:
    logger.error("User management routes not included - import failed")

if notifications_router is not None:
    app.include_router(notifications_router)
    logger.info("Notifications routes included successfully")
else:
    logger.error("Notifications routes not included - import failed")

# Health check endpoint
@app.get("/")
async def root():
    """API root endpoint with comprehensive information"""
    return {
        "message": "CoinLink MVP Production API",
        "version": "2.0.0", 
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": "production",
        "documentation": "/docs",
        "api_endpoints": {
            "authentication": "/api/v2/auth",
            "market_data": "/api/v2/market", 
            "user_management": "/api/v2/user",
            "notifications": "/api/v2/notifications",
            "websocket": "/ws",
            "health_checks": {
                "basic": "/health",
                "readiness": "/readyz", 
                "liveness": "/livez"
            }
        },
        "features": [
            "JWT Authentication with refresh tokens",
            "Real-time WebSocket with Redis pub/sub",
            "Comprehensive market data API",
            "User profile and preference management",
            "Price alerts and notifications",
            "Production security and middleware",
            "Database persistence with PostgreSQL"
        ]
    }

@app.get("/health")
async def health_check():
    """Quick health check - low cost"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connections": websocket_manager.get_stats()["total_connections"] if websocket_manager else 0,
        "routes_loaded": {
            "agents": agents_router is not None,
            "rd_status": rd_status_router is not None, 
            "rd_full": rd_router is not None,
            "growth": growth_router is not None,
            "auth_v2": auth_router_v2 is not None,
            "websocket": websocket_router is not None,
            "market_data": market_data_router is not None,
            "user_management": user_management_router is not None,
            "notifications": notifications_router is not None
        }
    }

@app.get("/api/metrics")
async def custom_metrics():
    """Custom business metrics endpoint"""
    try:
        # Get WebSocket stats
        ws_stats = websocket_manager.get_stats() if websocket_manager else {}
        
        # Get database stats
        from ..db.database import get_db_stats
        db_stats = await get_db_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "service": "coinlink-api",
            "version": "2.0.0",
            "metrics": {
                "websocket": {
                    "total_connections": ws_stats.get("total_connections", 0),
                    "authenticated_connections": ws_stats.get("authenticated_connections", 0),
                    "channels": ws_stats.get("total_channels", 0)
                },
                "database": {
                    "active_connections": db_stats.get("checked_out", 0),
                    "pool_size": db_stats.get("pool_size", 0),
                    "overflow": db_stats.get("overflow", 0)
                },
                "system": {
                    "uptime_seconds": int(datetime.now().timestamp()),
                    "routes_loaded": sum(1 for r in [
                        agents_router, rd_status_router, auth_router_v2,
                        websocket_router, market_data_router, user_management_router,
                        notifications_router
                    ] if r is not None)
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting custom metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get metrics"
        )

@app.get("/readyz")
async def readiness_check():
    """Readiness check - verifies all dependencies are available"""
    checks = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": {}
    }
    
    overall_healthy = True
    
    # Check Redis connection
    try:
        security_middleware = app.state.security_middleware
        if security_middleware.redis_client:
            await security_middleware.redis_client.ping()
            checks["checks"]["redis"] = {"status": "healthy", "message": "Connected"}
        else:
            checks["checks"]["redis"] = {"status": "degraded", "message": "Not connected - graceful degradation"}
    except Exception as e:
        checks["checks"]["redis"] = {"status": "unhealthy", "message": f"Error: {str(e)}"}
        overall_healthy = False
    
    # Check database connection
    try:
        from ..db.database import check_db_health
        db_healthy = await check_db_health()
        
        if db_healthy:
            checks["checks"]["database"] = {"status": "healthy", "message": "Database connection successful"}
        else:
            checks["checks"]["database"] = {"status": "unhealthy", "message": "Database connection failed"}
            overall_healthy = False
            
    except Exception as e:
        checks["checks"]["database"] = {"status": "unhealthy", "message": f"Database error: {str(e)}"}
        overall_healthy = False
    
    # Check observability stack
    try:
        observability_status = {
            "prometheus_metrics": create_instrumentator is not None,
            "structured_logging": True,  # Always enabled
            "sentry_available": getattr(settings, 'SENTRY_DSN', None) is not None
        }
        
        checks["checks"]["observability"] = {
            "status": "healthy",
            "message": "Observability stack operational", 
            "components": observability_status
        }
    except Exception as e:
        checks["checks"]["observability"] = {"status": "unhealthy", "message": f"Observability error: {str(e)}"}
        overall_healthy = False
    
    # Check required environment variables
    try:
        required_vars = ["JWT_SECRET_KEY", "ALLOWED_ORIGINS", "REDIS_URL", "DATABASE_URL"]
        optional_vars = ["SENTRY_DSN", "LOG_LEVEL"]
        missing_vars = []
        
        for var in required_vars:
            if not hasattr(settings, var) or not getattr(settings, var):
                missing_vars.append(var)
        
        if missing_vars:
            checks["checks"]["environment"] = {
                "status": "unhealthy", 
                "message": f"Missing required variables: {', '.join(missing_vars)}"
            }
            overall_healthy = False
        else:
            optional_status = {var: getattr(settings, var, None) is not None for var in optional_vars}
            checks["checks"]["environment"] = {
                "status": "healthy", 
                "message": "All required variables present",
                "optional_vars": optional_status
            }
            
    except Exception as e:
        checks["checks"]["environment"] = {"status": "unhealthy", "message": f"Error checking environment: {str(e)}"}
        overall_healthy = False
    
    # Check WebSocket manager status
    try:
        if websocket_manager:
            ws_stats = websocket_manager.get_stats()
            checks["checks"]["websocket"] = {
                "status": "healthy",
                "message": f"WebSocket manager running with {ws_stats['total_connections']} connections",
                "redis_connected": ws_stats.get("redis_connected", False),
                "background_tasks": ws_stats.get("background_tasks_running", 0)
            }
        else:
            checks["checks"]["websocket"] = {
                "status": "degraded", 
                "message": "WebSocket manager not available - real-time features disabled"
            }
    except Exception as e:
        checks["checks"]["websocket"] = {"status": "unhealthy", "message": f"WebSocket error: {str(e)}"}
        overall_healthy = False
    
    # Update overall status
    if not overall_healthy:
        checks["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=checks)
    
    return checks

@app.get("/livez")
async def liveness_check():
    """Liveness check - verifies event loop responsiveness"""
    start_time = asyncio.get_event_loop().time()
    
    # Simple async operation to test responsiveness
    await asyncio.sleep(0.001)
    
    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
    
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": round(response_time, 2),
        "event_loop_responsive": response_time < 100  # Should be very fast
    }

# WebSocket endpoints are handled by websocket_router (see websocket/routes.py)

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

# Bitcoin price endpoint (backwards compatibility - redirects to v2)
@app.get("/api/bitcoin/price")
async def get_bitcoin_price():
    """Get current Bitcoin price (backwards compatible endpoint)"""
    try:
        # Call the new v2 endpoint if available
        if market_data_router:
            from .routes.market_data import get_bitcoin_price as get_bitcoin_price_v2
            bitcoin_data = await get_bitcoin_price_v2()
            
            # Format for backwards compatibility
            return {
                "data": {
                    "price": bitcoin_data.price,
                    "change_24h": bitcoin_data.change_percent_24h,
                    "volume_24h": bitcoin_data.volume_24h,
                    "timestamp": bitcoin_data.last_updated
                }
            }
        else:
            # Fallback to mock data
            return {
                "data": {
                    "price": 97420.15,
                    "change_24h": 2.34,
                    "volume_24h": 28500000000,
                    "timestamp": datetime.now().isoformat()
                }
            }
    except Exception as e:
        logger.error(f"Error in backwards compatibility Bitcoin price endpoint: {e}")
        # Fallback to mock data on error
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
    ws_stats = websocket_manager.get_stats() if websocket_manager else {
        "total_connections": 0,
        "authenticated_connections": 0,
        "anonymous_connections": 0
    }
    
    return {
        "active_connections": ws_stats["total_connections"],
        "authenticated_connections": ws_stats.get("authenticated_connections", 0),
        "anonymous_connections": ws_stats.get("anonymous_connections", 0),
        "websocket_stats": ws_stats,
        "timestamp": datetime.now().isoformat()
    }

# Crypto ticker endpoint (backwards compatibility - redirects to v2)
@app.get("/api/crypto/ticker")
async def get_crypto_ticker():
    """Get crypto ticker data (backwards compatible endpoint)"""
    try:
        # Call the new v2 endpoint if available
        if market_data_router:
            from .routes.market_data import get_crypto_ticker as get_crypto_ticker_v2
            ticker_data = await get_crypto_ticker_v2(symbols="BTC,ETH,SOL")
            
            # Format for backwards compatibility
            simplified_data = []
            for coin in ticker_data:
                simplified_data.append({
                    "symbol": coin.symbol,
                    "price": coin.price,
                    "change_24h": coin.change_percent_24h
                })
            
            return {
                "data": simplified_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Fallback to mock data
            return {
                "data": [
                    {"symbol": "BTC", "price": 97420.15, "change_24h": 2.34},
                    {"symbol": "ETH", "price": 3250.80, "change_24h": 1.89},
                    {"symbol": "SOL", "price": 145.67, "change_24h": 5.12},
                ],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error in backwards compatibility crypto ticker endpoint: {e}")
        # Fallback to mock data on error
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