import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Production-ready settings with strict validation"""
    
    # Core Environment
    PYTHON_ENV: str = Field(..., description="Environment: production, staging, development")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Security & CORS (REQUIRED)
    JWT_SECRET_KEY: str = Field(..., description="JWT signing secret - REQUIRED for production")
    JWT_ISSUER: str = Field(default="coinlink-api", description="JWT issuer")
    JWT_AUDIENCE: str = Field(default="coinlink-app", description="JWT audience")
    ACCESS_TOKEN_TTL_MIN: int = Field(default=15, description="Access token TTL in minutes")
    REFRESH_TOKEN_TTL_DAYS: int = Field(default=7, description="Refresh token TTL in days")
    
    ALLOWED_ORIGINS: str = Field(..., description="CSV of allowed CORS origins - REQUIRED")
    
    # Database (REQUIRED)
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL - REQUIRED")
    
    # Redis (REQUIRED) 
    REDIS_URL: str = Field(..., description="Redis connection URL - REQUIRED")
    
    # Observability
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    PROMETHEUS_ENABLED: bool = Field(default=True, description="Enable Prometheus metrics")
    
    # Rate Limiting
    RATE_LIMIT_GLOBAL: str = Field(default="100/minute", description="Global rate limit")
    RATE_LIMIT_AUTH: str = Field(default="10/minute", description="Auth endpoints rate limit")
    RATE_LIMIT_CHAT: str = Field(default="20/minute", description="Chat endpoints rate limit")
    RATE_LIMIT_PRICE: str = Field(default="60/minute", description="Price endpoints rate limit")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama API URL")
    OLLAMA_MODEL: str = Field(default="llama3:8b", description="Ollama model name")
    
    # External API Keys (Optional - graceful degradation)
    COINBASE_API_KEY: Optional[str] = None
    COINBASE_API_SECRET: Optional[str] = None
    COINBASE_KEY_JSON: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None
    REDDIT_API_SECRET: Optional[str] = None
    REDDIT_CLIENT_ID: Optional[str] = None
    NEWSAPI_API_KEY: Optional[str] = None
    MESSARI_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse CSV origins into list"""
        if not v:
            raise ValueError("ALLOWED_ORIGINS is required and cannot be empty")
        origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        if not origins:
            raise ValueError("ALLOWED_ORIGINS must contain at least one valid origin")
        return origins
    
    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret is strong enough"""
        if not v:
            raise ValueError("JWT_SECRET_KEY is required and cannot be empty")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v:
            raise ValueError("DATABASE_URL is required")
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @field_validator('REDIS_URL')
    @classmethod
    def validate_redis_url(cls, v):
        """Validate Redis URL format"""
        if not v:
            raise ValueError("REDIS_URL is required")
        if not v.startswith('redis://'):
            raise ValueError("REDIS_URL must be a Redis URL")
        return v
    
    # Application Settings
    BTC_SYMBOL: str = Field(default="BTC-USD", description="Bitcoin symbol")
    ALERT_THRESHOLD_PERCENT: float = Field(default=5.0, description="Alert threshold percentage")
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds")
    MONITOR_INTERVAL: int = Field(default=30, description="Monitor interval in seconds")
    
    # Alert pipeline and data source feature flags
    ALERT_PIPELINE: str = Field(default="rt", description="Alert pipeline: 'rt' or 'legacy'")
    WS_SOURCE: str = Field(default="advanced", description="WebSocket source: 'advanced' or 'public'")
    
    # Alert tuning
    PRICE_SIGMA_K: float = Field(default=2.5, description="k * sigma threshold for 1m returns")
    ALERT_DEDUP_WINDOW_SECONDS: int = Field(default=120, description="Alert dedup window")
    VOL_SPIKE_MULTIPLIER: float = Field(default=3.0, description="Volume spike multiplier")
    RESISTANCE_HYSTERESIS_PCT: float = Field(default=0.005, description="Resistance hysteresis %")
    SUPPORT_HYSTERESIS_PCT: float = Field(default=0.005, description="Support hysteresis %")
    ALERT_COOLDOWN_SECONDS: float = Field(default=300, description="Alert cooldown")
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, description="WebSocket heartbeat interval")
    WS_TICKER_INTERVAL: int = Field(default=5, description="Ticker update interval in seconds")
    
    # Sentiment Analysis
    SENTIMENT_MODEL: str = Field(default="ProsusAI/finbert", description="Sentiment model")
    
    # Bitcoin-specific keywords for sentiment filtering
    BTC_KEYWORDS: List[str] = Field(default=['bitcoin', 'btc', 'crypto', 'cryptocurrency'], 
                                   description="Bitcoin keywords for filtering")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    """Get validated settings instance"""
    try:
        return Settings()
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise SystemExit(f"Configuration error: {e}")

# Global settings instance
settings = get_settings()
