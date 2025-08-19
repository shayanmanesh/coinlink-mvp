"""
Market data API routes for frontend compatibility
Comprehensive endpoints for Bitcoin and crypto market information
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random

from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v2/market", tags=["Market Data v2"])

class PriceData(BaseModel):
    """Bitcoin price data model"""
    symbol: str = Field(..., description="Cryptocurrency symbol")
    price: float = Field(..., description="Current price in USD")
    change_24h: float = Field(..., description="24h price change in USD")
    change_percent_24h: float = Field(..., description="24h price change percentage")
    volume_24h: float = Field(..., description="24h trading volume in USD")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    last_updated: str = Field(..., description="ISO timestamp of last update")

class MarketStats(BaseModel):
    """Market statistics model"""
    total_market_cap: float = Field(..., description="Total cryptocurrency market cap")
    total_volume_24h: float = Field(..., description="Total 24h trading volume")
    bitcoin_dominance: float = Field(..., description="Bitcoin dominance percentage")
    active_cryptocurrencies: int = Field(..., description="Number of active cryptocurrencies")
    last_updated: str = Field(..., description="ISO timestamp of last update")

class PriceHistory(BaseModel):
    """Price history data point"""
    timestamp: str = Field(..., description="ISO timestamp")
    price: float = Field(..., description="Price at timestamp")
    volume: Optional[float] = Field(None, description="Volume at timestamp")

class TrendingCoin(BaseModel):
    """Trending cryptocurrency model"""
    id: str = Field(..., description="Coin ID")
    symbol: str = Field(..., description="Coin symbol")
    name: str = Field(..., description="Coin name")
    price: float = Field(..., description="Current price")
    change_24h: float = Field(..., description="24h price change percentage")
    rank: int = Field(..., description="Market cap rank")

@router.get("/bitcoin/price", 
           response_model=PriceData,
           summary="Get Bitcoin current price",
           description="Get current Bitcoin price with 24h changes and volume")
async def get_bitcoin_price():
    """
    Get current Bitcoin price information
    
    Returns comprehensive Bitcoin price data including:
    - Current USD price
    - 24h change (absolute and percentage)  
    - 24h trading volume
    - Market capitalization
    """
    try:
        # Mock data for MVP - in production, connect to real APIs
        base_price = 97420.15
        price_variation = random.uniform(-500, 500)
        current_price = base_price + price_variation
        
        change_24h = random.uniform(-2000, 2000)
        change_percent_24h = (change_24h / current_price) * 100
        
        return PriceData(
            symbol="BTC",
            price=round(current_price, 2),
            change_24h=round(change_24h, 2),
            change_percent_24h=round(change_percent_24h, 4),
            volume_24h=random.uniform(25000000000, 35000000000),
            market_cap=round(current_price * 19700000, 0),  # ~19.7M BTC circulating
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching Bitcoin price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Bitcoin price data"
        )

@router.get("/bitcoin/history",
           response_model=List[PriceHistory],
           summary="Get Bitcoin price history", 
           description="Get historical Bitcoin price data")
async def get_bitcoin_history(
    period: str = Query("24h", description="Time period: 1h, 24h, 7d, 30d, 1y"),
    interval: str = Query("1h", description="Data interval: 1m, 5m, 1h, 1d")
):
    """
    Get Bitcoin price history for specified time period
    
    - **period**: Time range (1h, 24h, 7d, 30d, 1y)
    - **interval**: Data point interval (1m, 5m, 1h, 1d)
    
    Returns array of price/timestamp data points
    """
    try:
        # Calculate number of data points
        period_hours = {
            "1h": 1,
            "24h": 24, 
            "7d": 24 * 7,
            "30d": 24 * 30,
            "1y": 24 * 365
        }
        
        interval_hours = {
            "1m": 1/60,
            "5m": 5/60,
            "1h": 1,
            "1d": 24
        }
        
        total_hours = period_hours.get(period, 24)
        step_hours = interval_hours.get(interval, 1)
        
        if step_hours > total_hours:
            step_hours = total_hours
        
        data_points = int(total_hours / step_hours)
        data_points = min(data_points, 1000)  # Limit to 1000 points max
        
        # Generate mock historical data
        history = []
        base_price = 97000.0
        current_time = datetime.now()
        
        for i in range(data_points):
            timestamp = current_time - timedelta(hours=total_hours - (i * step_hours))
            
            # Add some realistic price variation
            trend = random.uniform(-0.001, 0.001)  # Small trend
            volatility = random.uniform(-200, 200)  # Price volatility
            price = base_price + (i * trend * base_price) + volatility
            
            history.append(PriceHistory(
                timestamp=timestamp.isoformat(),
                price=round(price, 2),
                volume=random.uniform(1000000, 5000000)
            ))
        
        return history
        
    except Exception as e:
        logger.error(f"Error fetching Bitcoin history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Bitcoin price history"
        )

@router.get("/crypto/ticker",
           response_model=List[PriceData],
           summary="Get cryptocurrency ticker data",
           description="Get price data for multiple cryptocurrencies")
async def get_crypto_ticker(
    symbols: str = Query("BTC,ETH,SOL", description="Comma-separated list of symbols"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results")
):
    """
    Get ticker data for multiple cryptocurrencies
    
    - **symbols**: Comma-separated cryptocurrency symbols (e.g., "BTC,ETH,SOL")
    - **limit**: Maximum number of results to return (1-100)
    
    Returns array of price data for requested cryptocurrencies
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")][:limit]
        
        # Mock data for common cryptocurrencies
        mock_data = {
            "BTC": {"name": "Bitcoin", "base_price": 97420.15, "market_cap": 1.9e12},
            "ETH": {"name": "Ethereum", "base_price": 3250.80, "market_cap": 4e11},
            "SOL": {"name": "Solana", "base_price": 145.67, "market_cap": 7e10},
            "ADA": {"name": "Cardano", "base_price": 0.48, "market_cap": 1.7e10},
            "DOT": {"name": "Polkadot", "base_price": 6.23, "market_cap": 8e9},
            "MATIC": {"name": "Polygon", "base_price": 0.89, "market_cap": 8.5e9},
            "LINK": {"name": "Chainlink", "base_price": 14.56, "market_cap": 8.5e9},
            "UNI": {"name": "Uniswap", "base_price": 6.78, "market_cap": 5e9},
        }
        
        ticker_data = []
        
        for symbol in symbol_list:
            if symbol in mock_data:
                base_data = mock_data[symbol]
                price_variation = random.uniform(-0.05, 0.05)  # ±5% variation
                current_price = base_data["base_price"] * (1 + price_variation)
                
                change_24h = random.uniform(-0.08, 0.08)  # ±8% change
                change_24h_abs = current_price * change_24h
                
                ticker_data.append(PriceData(
                    symbol=symbol,
                    price=round(current_price, 6 if current_price < 1 else 2),
                    change_24h=round(change_24h_abs, 6 if current_price < 1 else 2),
                    change_percent_24h=round(change_24h * 100, 2),
                    volume_24h=random.uniform(100000000, 2000000000),
                    market_cap=base_data["market_cap"] * (1 + price_variation),
                    last_updated=datetime.now().isoformat()
                ))
        
        # Add unknown symbols with random data
        for symbol in symbol_list:
            if symbol not in mock_data:
                price = random.uniform(0.01, 100)
                change_pct = random.uniform(-0.15, 0.15)
                
                ticker_data.append(PriceData(
                    symbol=symbol,
                    price=round(price, 6 if price < 1 else 2),
                    change_24h=round(price * change_pct, 6 if price < 1 else 2),
                    change_percent_24h=round(change_pct * 100, 2),
                    volume_24h=random.uniform(1000000, 100000000),
                    last_updated=datetime.now().isoformat()
                ))
        
        return ticker_data[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching crypto ticker: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cryptocurrency ticker data"
        )

@router.get("/stats",
           response_model=MarketStats,
           summary="Get overall market statistics",
           description="Get global cryptocurrency market statistics")
async def get_market_stats():
    """
    Get global cryptocurrency market statistics
    
    Returns overall market metrics including:
    - Total market capitalization
    - Total 24h trading volume
    - Bitcoin dominance percentage
    - Number of active cryptocurrencies
    """
    try:
        # Mock global market data
        total_market_cap = random.uniform(2.3e12, 2.7e12)  # $2.3-2.7 trillion
        total_volume_24h = random.uniform(50e9, 120e9)     # $50-120 billion
        btc_dominance = random.uniform(48, 52)              # 48-52%
        
        return MarketStats(
            total_market_cap=total_market_cap,
            total_volume_24h=total_volume_24h,
            bitcoin_dominance=round(btc_dominance, 1),
            active_cryptocurrencies=random.randint(8000, 12000),
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching market stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch market statistics"
        )

@router.get("/trending",
           response_model=List[TrendingCoin],
           summary="Get trending cryptocurrencies",
           description="Get currently trending cryptocurrencies")
async def get_trending_coins(
    limit: int = Query(10, ge=1, le=50, description="Number of trending coins to return")
):
    """
    Get currently trending cryptocurrencies
    
    - **limit**: Number of trending coins to return (1-50)
    
    Returns array of trending cryptocurrency data
    """
    try:
        trending_coins = [
            {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "base_price": 97420},
            {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "base_price": 3250},
            {"id": "solana", "symbol": "SOL", "name": "Solana", "base_price": 145},
            {"id": "cardano", "symbol": "ADA", "name": "Cardano", "base_price": 0.48},
            {"id": "polkadot", "symbol": "DOT", "name": "Polkadot", "base_price": 6.23},
            {"id": "polygon", "symbol": "MATIC", "name": "Polygon", "base_price": 0.89},
            {"id": "chainlink", "symbol": "LINK", "name": "Chainlink", "base_price": 14.56},
            {"id": "avalanche", "symbol": "AVAX", "name": "Avalanche", "base_price": 38.45},
            {"id": "cosmos", "symbol": "ATOM", "name": "Cosmos", "base_price": 10.23},
            {"id": "near", "symbol": "NEAR", "name": "NEAR Protocol", "base_price": 2.34},
        ]
        
        # Randomize order and add price variations
        random.shuffle(trending_coins)
        
        result = []
        for i, coin in enumerate(trending_coins[:limit]):
            price_variation = random.uniform(-0.03, 0.03)
            current_price = coin["base_price"] * (1 + price_variation)
            change_24h = random.uniform(-0.15, 0.15) * 100
            
            result.append(TrendingCoin(
                id=coin["id"],
                symbol=coin["symbol"], 
                name=coin["name"],
                price=round(current_price, 6 if current_price < 1 else 2),
                change_24h=round(change_24h, 2),
                rank=i + 1
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching trending coins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trending cryptocurrencies"
        )

@router.get("/health")
async def market_data_health():
    """Market data service health check"""
    return {
        "status": "healthy",
        "service": "market_data",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/bitcoin/price",
            "/bitcoin/history", 
            "/crypto/ticker",
            "/stats",
            "/trending"
        ]
    }