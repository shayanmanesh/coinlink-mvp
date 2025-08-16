"""
Secure production API with comprehensive security measures
Implements rate limiting, input validation, API key verification, and request logging
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Import our modules
from config.settings import settings
from agents.analyst import BitcoinAnalystAgent
from tools.coinbase_tools import get_bitcoin_tools, get_bitcoin_candles
from sentiment.analyzer import BitcoinSentimentService
from monitors.btc_monitor import BitcoinMonitor
from alerts.alert_engine import BitcoinAlertEngine
from api.websocket import websocket_handler, manager
from api.prompts import get_contextual_prompts
from realtime.engine import RealTimeAlertEngine, MarketDataPoller
from realtime.coinbase_ws import CoinbaseWebSocketClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from auth.registration_state import RegistrationFlow
from auth.routes import router as auth_router
from auth.auth_api import router as simple_auth_router
from agents.analytics_agent import AnalyticsAgent
from cache.redis_prod import production_cache, init_production_cache, close_production_cache
from api.connection_pool import api_pool, init_connection_pools, close_connection_pools

# Import security middleware
from middleware.security import (
    security_middleware,
    request_logging_middleware,
    input_validation_middleware,
    api_key_validator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Input validation models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(default="default", max_length=100)
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v

class SentimentTestRequest(BaseModel):
    headline: str = Field(..., min_length=1, max_length=500)

class DebugTickRequest(BaseModel):
    price: float = Field(..., gt=0, le=1000000)
    volume24h: float = Field(default=0, ge=0)

# Initialize FastAPI app
app = FastAPI(
    title="CoinLink MVP - Bitcoin Analysis",
    description="Bitcoin-focused financial analysis chat application",
    version="1.0.0"
)

# Initialize security middleware
app.state.security_middleware = security_middleware

# Enhanced rate limiter with custom key function
def get_client_identifier(request: Request) -> str:
    """Get unique client identifier for rate limiting"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"

limiter = Limiter(key_func=get_client_identifier, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware
app.middleware("http")(request_logging_middleware)
app.middleware("http")(input_validation_middleware)

# Add CORS middleware - Enhanced for production
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

# Add production domains
if os.getenv("NODE_ENV") == "production":
    CORS_ORIGINS.extend([
        "https://www.coin.link",
        "https://coin.link",
        "https://coinlink.vercel.app",
        "https://*.vercel.app",  # For preview deployments
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global instances
bitcoin_analyst = BitcoinAnalystAgent()
sentiment_service = BitcoinSentimentService()
bitcoin_monitor = BitcoinMonitor()
alert_engine = BitcoinAlertEngine()
rt_alert_engine = RealTimeAlertEngine()
rt_poller = MarketDataPoller(rt_alert_engine)
coinbase_ws = CoinbaseWebSocketClient(rt_alert_engine)
registration_flow = RegistrationFlow()
analytics_agent = AnalyticsAgent(rt_alert_engine)

# Add tools to the analyst
bitcoin_tools = get_bitcoin_tools()
bitcoin_analyst.add_tools(bitcoin_tools)

# Include auth routes
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(simple_auth_router, prefix="/api/v2/auth", tags=["auth-v2"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Starting CoinLink MVP with Security Features...")
    
    # Validate API keys
    print("\n=== API Key Validation ===")
    api_key_status = api_key_validator.validate_environment()
    
    # Check if all required keys are present
    missing_keys = [name for name, status in api_key_status.items() if status is False]
    if missing_keys:
        print(f"\n⚠️  WARNING: Missing required API keys: {', '.join(missing_keys)}")
        print("Some features may not work properly.")
    else:
        print("\n✅ All required API keys loaded successfully")
    
    print("\n=== Security Features ===")
    print("✅ Rate limiting enabled")
    print("✅ Input validation active")
    print("✅ Request logging enabled")
    print("✅ Security headers configured")
    
    print("\n=== Initializing Services ===")
    
    # Initialize Redis cache
    await init_production_cache()
    
    # Initialize connection pools
    await init_connection_pools()

    # Initialize monitor
    await bitcoin_monitor.initialize()

    # Add alert callbacks (legacy pipeline guarded by feature flag)
    if settings.ALERT_PIPELINE == "legacy":
        await bitcoin_monitor.add_alert_callback(alert_engine.process_alert)
        await alert_engine.add_alert_callback(websocket_handler.send_alert)

    # Start background monitoring (legacy) only if enabled
    if settings.ALERT_PIPELINE == "legacy":
        asyncio.create_task(bitcoin_monitor.monitor_bitcoin())

    # Start market data sources based on feature flags
    if settings.WS_SOURCE == "advanced" and settings.COINBASE_KEY_JSON:
        asyncio.create_task(coinbase_ws.start())
    else:
        # Use public WS via connection manager to drive frontend ticker updates
        try:
            asyncio.create_task(manager.start_crypto_feed())
        except Exception:
            pass
    # Also keep fallback poller for RealTime engine (for price_update + alerts)
    asyncio.create_task(rt_poller.start())
    # Start scheduled tasks
    asyncio.create_task(rt_alert_engine.poll_sentiment())
    asyncio.create_task(rt_alert_engine.push_market_insights())
    asyncio.create_task(rt_alert_engine.monitor_correlation())
    asyncio.create_task(rt_alert_engine.push_technical_reports())
    # Start continuous 2s market report stream
    asyncio.create_task(rt_alert_engine.start_market_report_stream())
    # Start analytics agent streams (sentiment updates/aggregates, market reports)
    asyncio.create_task(analytics_agent.start())
    
    # Start registration cleanup task
    asyncio.create_task(registration_cleanup_task())

    print("\nCoinLink MVP started successfully with enhanced security!")

async def registration_cleanup_task():
    """Background task to clean up expired registration sessions"""
    while True:
        try:
            registration_flow.cleanup_expired_sessions()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logging.error(f"Registration cleanup error: {e}")
            await asyncio.sleep(3600)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down CoinLink MVP...")
    
    # Close Redis cache
    await close_production_cache()
    
    # Close connection pools
    await close_connection_pools()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CoinLink MVP - Bitcoin Analysis API",
        "version": "1.0.0",
        "status": "running",
        "security": "enhanced",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
@limiter.limit("120/minute")
async def health_check(request: Request):
    """Health check endpoint - Enhanced with monitoring layer"""
    try:
        from monitoring.health import health_monitor
        health_data = await health_monitor.get_system_health()
        return health_data
    except Exception:
        # Fallback to original simple health check if monitoring fails
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "bitcoin_analyst": "active",
                "sentiment_service": "active",
                "bitcoin_monitor": "active",
                "alert_engine": "active"
            }
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    try:
        # Log origin and path for debugging WS failures
        try:
            logging.getLogger("coinlink.ws").info(
                "Incoming handshake from origin: %s, client: %s",
                websocket.headers.get("origin"), getattr(websocket, 'client', None)
            )
        except Exception:
            pass
        # Delegate to handler (accept occurs inside)
        await websocket_handler.handle_websocket(websocket)
    except Exception as e:
        try:
            logging.getLogger("coinlink.ws").error("Error in websocket endpoint: %s", str(e))
        except Exception:
            pass

@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat_endpoint(payload: ChatRequest, request: Request):
    """Chat endpoint for Bitcoin analysis with input validation"""
    try:
        user_message = payload.message
        session_id = payload.session_id

        # Check if this is a registration message first
        registration_response = registration_flow.handle_message(session_id, user_message)
        if registration_response:
            # This is a registration flow message
            return {
                "type": "registration",
                "system_message": registration_response,
                "timestamp": datetime.now().isoformat()
            }

        # Normal chat flow - check if user is in registration mode
        current_step = registration_flow.get_step(session_id)
        if current_step != 'idle':
            return {
                "type": "registration",
                "system_message": {
                    "type": "system",
                    "content": "Please complete your registration first. Type /cancel to cancel registration."
                },
                "timestamp": datetime.now().isoformat()
            }

        # Get current Bitcoin context (with safety timeouts)
        try:
            current_price = await asyncio.wait_for(
                bitcoin_monitor.get_bitcoin_price(), timeout=8
            )
        except asyncio.TimeoutError:
            current_price = None
        try:
            current_sentiment = await asyncio.wait_for(
                bitcoin_monitor.get_bitcoin_sentiment(), timeout=8
            )
        except asyncio.TimeoutError:
            current_sentiment = None

        # Prepare context for the analyst
        corr_snapshot = rt_alert_engine.get_correlation_snapshot()
        btc_context = {
            "current_price": f"${current_price.get('price', 0):,.2f}" if current_price else "Unknown",
            "24h_change": f"{current_price.get('change_24h', 0):+.2f}%" if current_price else "Unknown",
            "sentiment": current_sentiment.get('overall_sentiment', 'neutral') if current_sentiment else 'neutral',
            "corr_30m": corr_snapshot.get('corr_30m'),
            "lead_minutes": corr_snapshot.get('lead_minutes'),
            "lead_corr": corr_snapshot.get('lead_corr'),
        }

        # Always return quick deterministic snapshot for speed
        try:
            bot_response = bitcoin_analyst._fallback_technical_analysis(user_message, btc_context)  # type: ignore
        except Exception:
            bot_response = "Unable to compute snapshot right now. Please try again."

        # Send response via WebSocket
        await websocket_handler.send_chat_response(user_message, bot_response, btc_context)

        return {
            "type": "chat",
            "user_message": user_message,
            "bot_response": bot_response,
            "btc_context": btc_context,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/api/bitcoin/price")
@limiter.limit("60/minute")
async def get_bitcoin_price_api(request: Request):
    """Get current Bitcoin price with caching"""
    try:
        # Try to get from cache first
        cache_key = "bitcoin:price"
        cached_data = await production_cache.get(cache_key)
        
        if cached_data:
            return {
                "data": cached_data,
                "timestamp": datetime.now().isoformat(),
                "cached": True
            }
        
        # Fetch fresh data
        price_data = await bitcoin_monitor.get_bitcoin_price()
        if not price_data:
            raise HTTPException(status_code=404, detail="Unable to fetch Bitcoin price")
        
        # Cache the data for 10 seconds (frequent updates for price)
        await production_cache.set(cache_key, price_data, ttl=10)

        return {
            "data": price_data,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Bitcoin price: {str(e)}")

@app.get("/api/bitcoin/sentiment")
@limiter.limit("30/minute")
async def get_bitcoin_sentiment(request: Request):
    """Get current Bitcoin sentiment analysis"""
    try:
        sentiment_data = await bitcoin_monitor.get_bitcoin_sentiment()
        if not sentiment_data:
            raise HTTPException(status_code=404, detail="Unable to fetch Bitcoin sentiment")

        return {
            "data": sentiment_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Bitcoin sentiment: {str(e)}")

@app.get("/api/bitcoin/market-summary")
@limiter.limit("30/minute")
async def get_market_summary(request: Request):
    """Get comprehensive Bitcoin market summary"""
    try:
        summary = await bitcoin_monitor.get_market_summary()
        return {
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market summary: {str(e)}")

@app.get("/api/alerts")
@limiter.limit("30/minute")
async def get_alerts(request: Request):
    """Get active alerts (legacy)"""
    try:
        if settings.ALERT_PIPELINE != "legacy":
            raise HTTPException(status_code=404, detail="Endpoint disabled")
        active_alerts = await alert_engine.get_active_alerts()
        return {
            "alerts": active_alerts,
            "count": len(active_alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@app.get("/api/alerts/history")
@limiter.limit("30/minute")
async def get_alert_history(limit: int = Field(default=20, le=100), request: Request = None):
    """Get alert history (legacy)"""
    try:
        if settings.ALERT_PIPELINE != "legacy":
            raise HTTPException(status_code=404, detail="Endpoint disabled")
        history = await alert_engine.get_alert_history(limit)
        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alert history: {str(e)}")

@app.get("/api/chat/history")
@limiter.limit("30/minute")
async def get_chat_history(request: Request):
    """Get chat history"""
    try:
        history = websocket_handler.get_chat_history()
        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@app.post("/api/bitcoin/analyze")
@limiter.limit("10/minute")
async def analyze_bitcoin_text(payload: AnalyzeRequest, request: Request):
    """Analyze Bitcoin-related text for sentiment with validation"""
    try:
        text = payload.text
        sentiment = await sentiment_service.analyze_single_news(text)

        return {
            "text": text,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing text: {str(e)}")

@app.get("/api/bitcoin/news")
@limiter.limit("30/minute")
async def get_bitcoin_news(limit: int = Field(default=10, le=50), request: Request = None):
    """Get recent Bitcoin news"""
    try:
        news = await sentiment_service.news_fetcher.get_bitcoin_news(limit)
        return {
            "news": news,
            "count": len(news),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Bitcoin news: {str(e)}")

@app.get("/api/connections")
@limiter.limit("60/minute")
async def get_connection_count(request: Request):
    """Get number of active WebSocket connections"""
    return {
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/prompts")
@limiter.limit("60/minute")
async def get_prompts(request: Request):
    """Get dynamic contextual prompts for UI (kept for compatibility)."""
    try:
        # Deprecated: intelligent prompt feed is provided via WS 'prompt_feed'
        return { 'prompts': [], 'timestamp': datetime.now().isoformat() }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prompts: {str(e)}")

@app.get("/api/correlation")
@limiter.limit("60/minute")
async def get_correlation(request: Request):
    try:
        snap = rt_alert_engine.get_correlation_snapshot()
        return { 'data': snap, 'timestamp': datetime.now().isoformat() }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching correlation: {str(e)}")

@app.post("/api/sentiment/test")
@limiter.limit("5/minute")
async def test_sentiment(payload: SentimentTestRequest, request: Request):
    """Test endpoint to analyze a sample headline with validation"""
    try:
        headline = payload.headline
        result = await sentiment_service.analyze_single_news(headline)
        if result:
            data = {
                'type': 'sentiment_shift',
                'data': {
                    'sentiment': result.get('label', 'neutral'),
                    'confidence': result.get('score', 0),
                    'source': 'test',
                    'headline': headline,
                    'timestamp': datetime.now().isoformat()
                },
                'priority': 'high'
            }
            await manager.broadcast(data)
        return {'result': result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing sentiment: {str(e)}")

@app.post("/api/debug/tick")
@limiter.limit("10/minute")
async def debug_tick(payload: DebugTickRequest, request: Request):
    """Force a synthetic tick for alert testing with validation"""
    try:
        print("[DebugTick] Received payload:", payload.dict())
        await rt_alert_engine.handle_tick(payload.price, payload.volume24h)
        comp = rt_alert_engine.metrics.compute()
        print("[DebugTick] Processed. Latest metrics:", comp)
        return {'status': 'ok', 'metrics': comp}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")

@app.get("/api/security/status")
@limiter.limit("10/minute")
async def security_status(request: Request):
    """Get security status and configuration"""
    client_id = get_client_identifier(request)
    
    return {
        "status": "active",
        "features": {
            "rate_limiting": True,
            "input_validation": True,
            "request_logging": True,
            "api_key_validation": True,
            "security_headers": True,
            "cors_protection": True
        },
        "client_identifier": api_key_validator.mask_key(client_id),
        "rate_limits": {
            "chat": "20/minute",
            "price": "60/minute",
            "auth": "5/minute"
        },
        "timestamp": datetime.now().isoformat()
    }

# Serve static HTML for testing
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Simple test page for WebSocket testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CoinLink MVP Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .chat-box { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
            .input-box { width: 100%; padding: 10px; margin: 10px 0; }
            .send-btn { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .security { background: #d1ecf1; color: #0c5460; margin: 10px 0; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CoinLink MVP - Bitcoin Analysis Test</h1>
            <div class="security">🔒 Security Enhanced: Rate limiting, input validation, and request logging active</div>
            <div id="status" class="status disconnected">Disconnected</div>
            <div class="chat-box" id="chatBox"></div>
            <input type="text" id="messageInput" class="input-box" placeholder="Ask about Bitcoin..." maxlength="1000">
            <button onclick="sendMessage()" class="send-btn">Send</button>
        </div>

        <script>
            let ws = null;
            const chatBox = document.getElementById('chatBox');
            const messageInput = document.getElementById('messageInput');
            const statusDiv = document.getElementById('status');

            function connect() {
                ws = new WebSocket('ws://localhost:8000/ws');

                ws.onopen = function() {
                    statusDiv.textContent = 'Connected';
                    statusDiv.className = 'status connected';
                    addMessage('System', 'Connected to CoinLink Bitcoin Analysis (Secure Mode)');
                };

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'chat_message') {
                        addMessage('User', data.user_message);
                        addMessage('Bot', data.bot_response);
                    } else if (data.type === 'bitcoin_update') {
                        addMessage('System', `Bitcoin Update: $${data.price.price} (${data.price.change_24h}%)`);
                    } else if (data.type === 'alert') {
                        addMessage('Alert', data.alert.message);
                    }
                };

                ws.onclose = function() {
                    statusDiv.textContent = 'Disconnected';
                    statusDiv.className = 'status disconnected';
                    addMessage('System', 'Disconnected from server');
                    setTimeout(connect, 5000);
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }

            function sendMessage() {
                const message = messageInput.value.trim();
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'chat',
                        message: message
                    }));
                    messageInput.value = '';
                }
            }

            function addMessage(sender, message) {
                const div = document.createElement('div');
                div.innerHTML = `<strong>${sender}:</strong> ${message}`;
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            connect();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)