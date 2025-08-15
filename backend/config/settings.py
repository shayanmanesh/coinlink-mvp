import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
    
    # Coinbase API Configuration
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
    # Advanced Trade (CDP) API key JSON for JWT auth
    COINBASE_KEY_JSON = os.getenv("COINBASE_KEY_JSON")
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Hugging Face Configuration
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    # Additional API Keys
    COINGECKO_API_KEY = os.getenv("CoinGecko_API_key")
    REDDIT_API_SECRET = os.getenv("Reddit_API_SECRET")
    REDDIT_CLIENT_ID = os.getenv("Reddit_client_id")
    NEWSAPI_API_KEY = os.getenv("newsapi_api_key")
    MESSARI_API_KEY = os.getenv("messari_api_key")
    
    # Application Settings
    BTC_SYMBOL = "BTC-USD"
    ALERT_THRESHOLD_PERCENT = 5.0
    CACHE_TTL = 300  # 5 minutes
    MONITOR_INTERVAL = 30  # seconds
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL = 30
    
    # Sentiment Analysis
    SENTIMENT_MODEL = "ProsusAI/finbert"
    
    # Bitcoin-specific keywords for sentiment filtering
    BTC_KEYWORDS = ['bitcoin', 'btc', 'crypto', 'cryptocurrency']

settings = Settings()
