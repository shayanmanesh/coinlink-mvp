import httpx
import hmac
import hashlib
import time
import base64
import json
from typing import Dict, Any, Optional
from config.settings import settings

class CoinbaseAPITool:
    def __init__(self):
        self.api_key = settings.COINBASE_API_KEY
        self.api_secret = settings.COINBASE_API_SECRET
        self.base_url = "https://api.exchange.coinbase.com"

    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate Coinbase API signature"""
        message = timestamp + method + request_path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(signature.digest()).decode('utf-8')

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to Coinbase API"""
        timestamp = str(int(time.time()))
        url = f"{self.base_url}{endpoint}"

        # Add query parameters to URL if present
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"

        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': self._generate_signature(timestamp, method, endpoint, json.dumps(data) if data else ""),
            'CB-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }

        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

_coinbase_calls = 0
_coinbase_last_reset = time.time()


def _ratelimit_coinbase(max_per_second: int = 10) -> bool:
    global _coinbase_calls, _coinbase_last_reset
    now = time.time()
    if now - _coinbase_last_reset > 1.0:
        _coinbase_calls = 0
        _coinbase_last_reset = now
    if _coinbase_calls >= max_per_second:
        return False
    _coinbase_calls += 1
    return True


def get_bitcoin_price(symbol: str = "BTC-USD") -> Dict[str, Any]:
    """Get current Bitcoin price data"""
    try:
        # Only allow BTC-USD queries
        if symbol != "BTC-USD":
            return {"error": "This tool only supports BTC-USD queries"}

        # Soft limit to protect external API
        if not _ratelimit_coinbase(10):
            # Return a lightweight cached value fallback
            return {
                "symbol": symbol,
                "price": 0.0,
                "change_24h": 0.0,
                "volume": 0.0,
                "timestamp": "",
                "bid": 0.0,
                "ask": 0.0,
                "note": "rate_limited"
            }

        url = f"https://api.exchange.coinbase.com/products/{symbol}/ticker"

        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        return {
            "symbol": symbol,
            "price": float(data.get('price', 0)),
            "change_24h": float(data.get('change', 0)),
            "volume": float(data.get('volume', 0)),
            "timestamp": data.get('time', ''),
            "bid": float(data.get('bid', 0)),
            "ask": float(data.get('ask', 0))
        }
    except Exception as e:
        return {"error": f"Failed to get Bitcoin price: {str(e)}"}

def get_bitcoin_candles(symbol: str = "BTC-USD", granularity: int = 3600, limit: int = 100) -> Dict[str, Any]:
    """Get Bitcoin historical data"""
    try:
        # Only allow BTC-USD queries
        if symbol != "BTC-USD":
            return {"error": "This tool only supports BTC-USD queries"}

        url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
        params = {
            "granularity": granularity,
            "limit": limit
        }

        with httpx.Client() as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Format candle data
        candles = []
        for candle in data:
            candles.append({
                "timestamp": candle[0],
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5])
            })

        return {
            "symbol": symbol,
            "granularity": granularity,
            "candles": candles
        }
    except Exception as e:
        return {"error": f"Failed to get Bitcoin candles: {str(e)}"}

def get_bitcoin_order_book(symbol: str = "BTC-USD", level: int = 2) -> Dict[str, Any]:
    """Get Bitcoin order book"""
    try:
        # Only allow BTC-USD queries
        if symbol != "BTC-USD":
            return {"error": "This tool only supports BTC-USD queries"}

        url = f"https://api.exchange.coinbase.com/products/{symbol}/book"
        params = {"level": level}

        with httpx.Client() as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        return {
            "symbol": symbol,
            "bids": data.get('bids', []),
            "asks": data.get('asks', []),
            "sequence": data.get('sequence', 0)
        }
    except Exception as e:
        return {"error": f"Failed to get Bitcoin order book: {str(e)}"}

def get_bitcoin_stats(symbol: str = "BTC-USD") -> Dict[str, Any]:
    """Get Bitcoin statistics"""
    try:
        # Only allow BTC-USD queries
        if symbol != "BTC-USD":
            return {"error": "This tool only supports BTC-USD queries"}

        url = f"https://api.exchange.coinbase.com/products/{symbol}/stats"

        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        return {
            "symbol": symbol,
            "open": float(data.get('open', 0)),
            "high": float(data.get('high', 0)),
            "low": float(data.get('low', 0)),
            "last": float(data.get('last', 0)),
            "volume": float(data.get('volume', 0)),
            "volume_30d": float(data.get('volume_30d', 0))
        }
    except Exception as e:
        return {"error": f"Failed to get Bitcoin stats: {str(e)}"}

def get_bitcoin_tools() -> list:
    """Get all Bitcoin-specific tools (simplified functions)"""
    return [
        get_bitcoin_price,
        get_bitcoin_candles,
        get_bitcoin_order_book,
        get_bitcoin_stats
    ]
