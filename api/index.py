"""
Vercel serverless function for CoinLink backend
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json

app = FastAPI(
    title="CoinLink API",
    description="CoinLink backend as Vercel serverless function",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-3qc7kuq2w-shayans-projects-ede8d66b.vercel.app",
        "https://www.coin.link",
        "https://coin.link",
        "*"  # Allow all for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "CoinLink API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "platform": "Vercel Functions"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": {"status": "healthy"},
            "platform": "vercel"
        }
    }

@app.get("/api/bitcoin/price")
async def get_bitcoin_price():
    # Mock Bitcoin price for now
    return {
        "symbol": "BTC-USD",
        "price": 67500.00,
        "change_24h": 2.5,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/alerts")
async def get_alerts():
    return {
        "alerts": [],
        "count": 0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/alerts/history")
async def get_alert_history():
    return {
        "history": [],
        "count": 0,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/chat")
async def chat_endpoint(payload: dict):
    user_message = payload.get("message", "")
    return {
        "type": "chat",
        "user_message": user_message,
        "bot_response": f"Bitcoin analysis: Your message '{user_message}' received. Bitcoin is showing strong momentum.",
        "timestamp": datetime.now().isoformat()
    }

# Vercel serverless function handler
from mangum import Mangum
handler = Mangum(app)