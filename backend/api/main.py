from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

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

# Initialize FastAPI app
app = FastAPI(
    title="CoinLink MVP - Bitcoin Analysis",
    description="Bitcoin-focused financial analysis chat application",
    version="1.0.0"
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
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

# Add tools to the analyst
bitcoin_tools = get_bitcoin_tools()
bitcoin_analyst.add_tools(bitcoin_tools)

# Include auth routes
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(simple_auth_router, prefix="/api/v2/auth", tags=["auth-v2"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("Starting CoinLink MVP...")

    # Initialize monitor
    await bitcoin_monitor.initialize()

    # Add alert callbacks (legacy pipeline guarded by feature flag)
    if settings.ALERT_PIPELINE == "legacy":
        await bitcoin_monitor.add_alert_callback(alert_engine.process_alert)
        await alert_engine.add_alert_callback(websocket_handler.send_alert)

    # Start background monitoring (legacy) only if enabled
    if settings.ALERT_PIPELINE == "legacy":
        asyncio.create_task(bitcoin_monitor.monitor_bitcoin())

    # Start Coinbase WebSocket (primary)
    asyncio.create_task(coinbase_ws.start())
    # Also keep fallback poller for RealTime engine
    asyncio.create_task(rt_poller.start())
    # Start scheduled tasks
    asyncio.create_task(rt_alert_engine.poll_sentiment())
    asyncio.create_task(rt_alert_engine.push_market_insights())
    asyncio.create_task(rt_alert_engine.monitor_correlation())
    
    # Start registration cleanup task
    asyncio.create_task(registration_cleanup_task())
    
    # Start cryptocurrency ticker feed
    # await connection_manager.start_crypto_feed()  # Commented out - not defined yet

    print("CoinLink MVP started successfully!")

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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CoinLink MVP - Bitcoin Analysis API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
async def chat_endpoint(payload: Dict[str, Any], request: Request):
    """Chat endpoint for Bitcoin analysis"""
    try:
        user_message = payload.get("message", "")
        session_id = payload.get("session_id", "default")
        
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

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
    """Get current Bitcoin price"""
    try:
        price_data = await bitcoin_monitor.get_bitcoin_price()
        if not price_data:
            raise HTTPException(status_code=404, detail="Unable to fetch Bitcoin price")

        return {
            "data": price_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Bitcoin price: {str(e)}")

@app.get("/api/bitcoin/sentiment")
async def get_bitcoin_sentiment():
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
async def get_market_summary():
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
async def get_alerts():
    """Get active alerts"""
    try:
        active_alerts = await alert_engine.get_active_alerts()
        return {
            "alerts": active_alerts,
            "count": len(active_alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@app.get("/api/alerts/history")
async def get_alert_history(limit: int = 20):
    """Get alert history"""
    try:
        history = await alert_engine.get_alert_history(limit)
        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alert history: {str(e)}")

@app.get("/api/chat/history")
async def get_chat_history():
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
async def analyze_bitcoin_text(request: Dict[str, Any]):
    """Analyze Bitcoin-related text for sentiment"""
    try:
        text = request.get("text", "")
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        sentiment = await sentiment_service.analyze_single_news(text)

        return {
            "text": text,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing text: {str(e)}")

@app.get("/api/bitcoin/news")
async def get_bitcoin_news(limit: int = 10):
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
async def get_connection_count():
    """Get number of active WebSocket connections"""
    return {
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/prompts")
async def get_prompts():
    """Get dynamic contextual prompts for UI"""
    try:
        price = await bitcoin_monitor.get_bitcoin_price()
        sentiment = await bitcoin_monitor.get_bitcoin_sentiment()
        # Pull latest technicals from real-time engine if available
        comp = rt_alert_engine.metrics.compute()
        rsi_live = rt_alert_engine.get_current_rsi()
        # Debug logging for RSI prompt
        print("[Prompts] Market compute:", comp)
        print("[Prompts] RSI live:", rsi_live)
        rsi = rsi_live if rsi_live is not None else (comp.get('rsi') if comp else None)
        # Fallback: compute RSI from hourly candles to align with chat snapshot if live RSI is unavailable or default 50
        def _compute_rsi(closes, period: int = 14):
            try:
                if not closes or len(closes) < period + 1:
                    return None
                gains = []
                losses = []
                for i in range(1, period + 1):
                    delta = float(closes[-i]) - float(closes[-(i + 1)])
                    if delta > 0:
                        gains.append(delta)
                        losses.append(0.0)
                    else:
                        gains.append(0.0)
                        losses.append(-delta)
                avg_gain = sum(gains) / period
                avg_loss = sum(losses) / period if sum(losses) > 0 else 0.0
                if avg_loss == 0:
                    return 100.0
                rs = avg_gain / avg_loss
                rsi_val = 100 - (100 / (1 + rs))
                return max(0.0, min(100.0, rsi_val))
            except Exception:
                return None

        rsi_candles = None
        try:
            candles_resp = get_bitcoin_candles("BTC-USD", granularity=3600, limit=60)
            candles = candles_resp.get("candles", []) if isinstance(candles_resp, dict) else []
            closes = [c.get("close") for c in candles if isinstance(c, dict) and c.get("close") is not None]
            rsi_candles = _compute_rsi(closes, 14)
        except Exception:
            rsi_candles = None
        # Prefer candle RSI when live RSI is missing or looks like default placeholder (50.0)
        if (rsi is None or abs(float(rsi) - 50.0) < 1e-6) and (rsi_candles is not None):
            rsi = rsi_candles
        support = comp.get('support') if comp else None
        resistance = comp.get('resistance') if comp else None
        last_price = rt_alert_engine.metrics.ticks[-1].price if rt_alert_engine.metrics.ticks else None
        near_resistance = bool(last_price and resistance and abs(last_price - resistance) / resistance < 0.005)
        near_support = bool(last_price and support and abs(last_price - support) / support < 0.005)

        # Normalize RSI to plain float for prompt generator
        rsi_val = None
        try:
            if rsi is not None:
                rsi_val = float(rsi)
        except Exception:
            rsi_val = None

        market_data = {
            'rsi': rsi_val if isinstance(rsi_val, (int, float)) else ((sentiment or {}).get('average_score', 0) * 100),
            'price_change_1h': 0,
            'price_change_24h': (price or {}).get('change_24h', 0),
            'near_resistance': near_resistance,
            'near_support': near_support,
            'sentiment': (sentiment or {}).get('overall_sentiment', 'neutral'),
            'sentiment_confidence': (sentiment or {}).get('average_score', 0),
        }
        prompts = get_contextual_prompts(market_data)
        print("[Prompts] Final market_data:", market_data)
        print("[Prompts] Returned prompts:", prompts)
        return { 'prompts': prompts, 'timestamp': datetime.now().isoformat() }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prompts: {str(e)}")

@app.get("/api/correlation")
async def get_correlation():
    try:
        snap = rt_alert_engine.get_correlation_snapshot()
        return { 'data': snap, 'timestamp': datetime.now().isoformat() }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching correlation: {str(e)}")

@app.post("/api/sentiment/test")
async def test_sentiment(payload: Dict[str, Any]):
    """Test endpoint to analyze a sample headline and broadcast sentiment shift if confidence high."""
    try:
        headline = payload.get('headline', '')
        if not headline:
            raise HTTPException(status_code=400, detail="headline is required")
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
async def debug_tick(payload: Dict[str, Any]):
    """Force a synthetic tick for alert testing.
    Body: { price: number, volume24h: number }
    """
    try:
        print("[DebugTick] Received payload:", payload)
        price = float(payload.get('price'))
        volume24h = float(payload.get('volume24h', 0))
        await rt_alert_engine.handle_tick(price, volume24h)
        comp = rt_alert_engine.metrics.compute()
        print("[DebugTick] Processed. Latest metrics:", comp)
        return {'status': 'ok', 'metrics': comp}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")

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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CoinLink MVP - Bitcoin Analysis Test</h1>
            <div id="status" class="status disconnected">Disconnected</div>
            <div class="chat-box" id="chatBox"></div>
            <input type="text" id="messageInput" class="input-box" placeholder="Ask about Bitcoin...">
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
                    addMessage('System', 'Connected to CoinLink Bitcoin Analysis');
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
