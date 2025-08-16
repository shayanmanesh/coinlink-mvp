"""
Coinbase Advanced Trade WebSocket for real-time crypto data
Handles top 50 cryptocurrencies with market cap ranking
"""
import asyncio
import json
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import websockets
import httpx
from dataclasses import dataclass
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class CryptoData:
    """Data structure for cryptocurrency information"""
    symbol: str
    name: str
    price: float
    volume_24h: float
    market_cap: float
    change_24h: float
    circulating_supply: float
    rank: int
    last_updated: datetime

class CoinbaseWebSocketManager:
    """Manages Coinbase Advanced Trade WebSocket connections for top 50 cryptos"""
    
    # Top 20 tradable on Coinbase (avoid delisted/unsupported)
    TOP_50_SYMBOLS = [
        ('BTC', 'Bitcoin', 'BTC-USD'),
        ('ETH', 'Ethereum', 'ETH-USD'),
        ('SOL', 'Solana', 'SOL-USD'),
        ('USDC', 'USD Coin', 'USDC-USD'),
        ('ADA', 'Cardano', 'ADA-USD'),
        ('DOGE', 'Dogecoin', 'DOGE-USD'),
        ('AVAX', 'Avalanche', 'AVAX-USD'),
        ('DOT', 'Polkadot', 'DOT-USD'),
        ('LINK', 'Chainlink', 'LINK-USD'),
        ('BCH', 'Bitcoin Cash', 'BCH-USD'),
        ('LTC', 'Litecoin', 'LTC-USD'),
        ('MATIC', 'Polygon', 'MATIC-USD'),
        ('ATOM', 'Cosmos', 'ATOM-USD'),
        ('XLM', 'Stellar', 'XLM-USD'),
        ('ETC', 'Ethereum Classic', 'ETC-USD'),
        ('OP', 'Optimism', 'OP-USD'),
        ('ARB', 'Arbitrum', 'ARB-USD'),
        ('FIL', 'Filecoin', 'FIL-USD'),
        ('APT', 'Aptos', 'APT-USD'),
        ('ALGO', 'Algorand', 'ALGO-USD'),
    ]
    
    # Approximate circulating supplies (in millions) - would be fetched from API in production
    CIRCULATING_SUPPLY = {
        'BTC': 19_600_000,
        'ETH': 120_200_000,
        'XRP': 54_500_000_000,
        'SOL': 440_000_000,
        'BNB': 153_000_000,
        'DOGE': 142_800_000_000,
        'ADA': 35_700_000_000,
        'AVAX': 380_000_000,
        'TRX': 87_500_000_000,
        'LINK': 600_000_000,
        'DOT': 1_400_000_000,
        'MATIC': 9_300_000_000,
        'TON': 5_100_000_000,
        'SHIB': 589_000_000_000_000,
        'LTC': 73_800_000,
        'UNI': 750_000_000,
        'BCH': 19_600_000,
        'XLM': 28_800_000_000,
        'ATOM': 390_000_000,
        'NEAR': 1_100_000_000,
        'XMR': 18_400_000,
        'OP': 4_500_000_000,
        'ARB': 10_000_000_000,
        'FIL': 550_000_000,
        'APT': 1_000_000_000,
        'HBAR': 33_700_000_000,
        'CRO': 26_600_000_000,
        'VET': 72_700_000_000,
        'MKR': 920_000,
        'KAS': 24_000_000_000,
        'INJ': 100_000_000,
        'RUNE': 330_000_000,
        'GRT': 10_000_000_000,
        'THETA': 1_000_000_000,
        'FTM': 2_800_000_000,
        'ALGO': 8_100_000_000,
        'LDO': 890_000_000,
        'IMX': 2_000_000_000,
        'SUI': 10_000_000_000,
        'SEI': 10_000_000_000,
        'MANA': 1_850_000_000,
        'SAND': 2_300_000_000,
        'AXS': 140_000_000,
        'AAVE': 16_000_000,
        'EOS': 1_200_000_000,
        'QNT': 14_600_000,
        'FLOW': 1_400_000_000,
        'CHZ': 8_900_000_000,
        'RNDR': 380_000_000,
        'SNX': 320_000_000
    }
    
    def __init__(self):
        # Use public WebSocket feed for real-time data
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        self.rest_url = "https://api.exchange.coinbase.com"
        self.crypto_data: Dict[str, CryptoData] = {}
        self.ws_connection = None
        self.update_callbacks = []
        self.running = False
        self.subscribed_products = []
        
    def generate_signature(self, timestamp: str, channel: str, products: List[str]) -> str:
        """Generate JWT signature for Coinbase Advanced Trade API"""
        try:
            if not settings.COINBASE_KEY_JSON:
                return ""
                
            key_data = json.loads(settings.COINBASE_KEY_JSON)
            message = f"{timestamp}{channel}{','.join(products)}"
            signature = hmac.new(
                key_data['privateKey'].encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
            logger.error(f"Error generating signature: {e}")
            return ""
    
    async def fetch_initial_data(self):
        """Fetch initial price data via REST API"""
        async with httpx.AsyncClient() as client:
            try:
                # Fetch live market caps from Coinbase (approx via USD price * supply)
                tasks = []
                for symbol, name, product_id in self.TOP_50_SYMBOLS:
                    tasks.append(client.get(f"https://api.exchange.coinbase.com/products/{product_id}/ticker"))
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                for (symbol, name, product_id), resp in zip(self.TOP_50_SYMBOLS, responses):
                    try:
                        if isinstance(resp, Exception):
                            continue
                        data = resp.json()
                        price = float(data.get('price', 0) or 0)
                        supply = self.CIRCULATING_SUPPLY.get(symbol, 1_000_000_000)
                        market_cap = price * supply
                        self.crypto_data[symbol] = CryptoData(
                            symbol=symbol,
                            name=name,
                            price=price,
                            volume_24h=float(data.get('volume', 0) or 0),
                            market_cap=market_cap,
                            change_24h=float(data.get('change', 0) or 0),
                            circulating_supply=supply,
                            rank=0,
                            last_updated=datetime.now()
                        )
                    except Exception:
                        continue
            except Exception as e:
                logger.error(f"Error fetching initial snapshot: {e}")
        
        # Calculate initial rankings
        self._update_rankings()
    
    def _update_rankings(self):
        """Update cryptocurrency rankings based on market cap"""
        sorted_cryptos = sorted(
            self.crypto_data.values(),
            key=lambda x: x.market_cap,
            reverse=True
        )
        
        for rank, crypto in enumerate(sorted_cryptos, 1):
            crypto.rank = rank
    
    def _calculate_market_cap(self, symbol: str, price: float) -> float:
        """Calculate market cap for a cryptocurrency"""
        supply = self.CIRCULATING_SUPPLY.get(symbol, 1_000_000_000)
        return price * supply
    
    async def connect(self):
        """Establish WebSocket connection to Coinbase public feed"""
        try:
            self.ws_connection = await websockets.connect(self.ws_url)
            
            # Get product IDs for subscription
            product_ids = [product_id for _, _, product_id in self.TOP_50_SYMBOLS if product_id]
            self.subscribed_products = product_ids
            
            # Subscribe to ticker channel (public feed doesn't require auth)
            subscribe_message = {
                "type": "subscribe",
                "product_ids": product_ids[:20],  # Coinbase limits to 20 products per subscription
                "channels": ["ticker"]
            }
            
            await self.ws_connection.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to first batch of cryptocurrency feeds")
            
            # Subscribe to remaining products in batches
            for i in range(20, len(product_ids), 20):
                batch = product_ids[i:i+20]
                if batch:
                    subscribe_message = {
                        "type": "subscribe",
                        "product_ids": batch,
                        "channels": ["ticker"]
                    }
                    await self.ws_connection.send(json.dumps(subscribe_message))
                    await asyncio.sleep(0.1)  # Small delay between subscriptions
                    logger.info(f"Subscribed to batch {i//20 + 1} of cryptocurrency feeds")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
    
    def _generate_jwt_token(self) -> Optional[str]:
        """Generate JWT token for authenticated access (if credentials available)"""
        # For public data, JWT is optional
        # Implementation would go here if using private endpoints
        return None
    
    async def handle_message(self, message: Dict[str, Any]):
        """Process incoming WebSocket messages"""
        msg_type = message.get('type')
        
        if msg_type == 'ticker':
            product_id = message.get('product_id', '')
            symbol = product_id.split('-')[0] if '-' in product_id else ''
            
            if symbol in self.crypto_data:
                # Update price and calculate new market cap
                price = float(message.get('price', 0))
                volume_24h = float(message.get('volume_24_h', 0))
                
                # Calculate 24h change
                open_24h = float(message.get('open_24_h', price))
                change_24h = ((price - open_24h) / open_24h * 100) if open_24h > 0 else 0
                
                # Update crypto data
                crypto = self.crypto_data[symbol]
                crypto.price = price
                crypto.volume_24h = volume_24h
                crypto.change_24h = change_24h
                crypto.market_cap = self._calculate_market_cap(symbol, price)
                crypto.last_updated = datetime.now()
                
                # Update rankings after price change
                self._update_rankings()
                
                # Notify callbacks
                await self._notify_updates()
        
        elif msg_type == 'error':
            logger.error(f"WebSocket error: {message}")
    
    async def _notify_updates(self):
        """Notify all registered callbacks with updated data"""
        sorted_data = sorted(
            self.crypto_data.values(),
            key=lambda x: x.rank
        )
        
        # Convert to frontend-friendly format
        ticker_data = []
        for crypto in sorted_data[:50]:  # Top 50 only
            ticker_data.append({
                'symbol': crypto.symbol,
                'name': crypto.name,
                'price': crypto.price,
                'change_24h': crypto.change_24h,
                'volume_24h': crypto.volume_24h,
                'market_cap': crypto.market_cap,
                'rank': crypto.rank
            })
        
        for callback in self.update_callbacks:
            try:
                await callback(ticker_data)
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
    
    def add_update_callback(self, callback):
        """Register a callback for data updates"""
        self.update_callbacks.append(callback)
    
    async def start(self):
        """Start the WebSocket connection and message handling"""
        self.running = True
        
        # Fetch initial data
        await self.fetch_initial_data()
        
        while self.running:
            try:
                await self.connect()
                
                async for message in self.ws_connection:
                    try:
                        data = json.loads(message)
                        await self.handle_message(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON message: {message}")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the WebSocket connection"""
        self.running = False
        if self.ws_connection:
            await self.ws_connection.close()