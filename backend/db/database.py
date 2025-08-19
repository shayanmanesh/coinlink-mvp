"""
Database configuration and connection management
Async PostgreSQL setup with SQLAlchemy 2.0
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio

from ..config.settings import settings

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

# Create async engine with production settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL logging in development
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections every hour
    pool_pre_ping=True,  # Verify connections before use
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,  # Use NullPool for SQLite
    connect_args={
        "command_timeout": 30,  # 30 second timeout for commands
        "server_settings": {
            "application_name": "coinlink_api",
        }
    } if "postgresql" in settings.DATABASE_URL else {}
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    Automatically handles session lifecycle
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions
    Use this for manual session management
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from .models import User
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def check_db_health() -> bool:
    """
    Check database health for readiness probes
    Returns True if database is accessible, False otherwise
    """
    try:
        async with engine.begin() as conn:
            # Simple query to test connection
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            return row is not None and row[0] == 1
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def get_db_stats() -> dict:
    """
    Get database connection and performance statistics
    """
    try:
        pool = engine.pool
        
        async with engine.begin() as conn:
            # Get database-specific stats
            if "postgresql" in settings.DATABASE_URL:
                result = await conn.execute(text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """))
                db_stats = result.fetchone()
                
                # Get database size
                size_result = await conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """))
                size_info = size_result.fetchone()
                
                return {
                    "pool_size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalidated": pool.invalidated(),
                    "db_total_connections": db_stats.total_connections if db_stats else 0,
                    "db_active_connections": db_stats.active_connections if db_stats else 0,
                    "db_idle_connections": db_stats.idle_connections if db_stats else 0,
                    "database_size": size_info.db_size if size_info else "unknown"
                }
            else:
                # Fallback for other databases
                return {
                    "pool_size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalidated": pool.invalidated(),
                    "db_total_connections": "unknown",
                    "db_active_connections": "unknown", 
                    "db_idle_connections": "unknown",
                    "database_size": "unknown"
                }
                
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {
            "error": str(e),
            "pool_size": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalidated": 0
        }

async def close_db():
    """Close database engine and all connections"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

# Health check with retry logic
async def wait_for_db(timeout: int = 30, retry_interval: int = 1) -> bool:
    """
    Wait for database to become available
    Used during startup to ensure DB is ready
    """
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        if await check_db_health():
            logger.info("Database is ready")
            return True
            
        logger.info(f"Waiting for database... ({int(asyncio.get_event_loop().time() - start_time)}s)")
        await asyncio.sleep(retry_interval)
    
    logger.error(f"Database not ready after {timeout} seconds")
    return False