"""Database base configuration and session management.

This module provides the core database setup using SQLAlchemy 2.0
with async support and proper session management.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

from ..utils.settings import Settings
from ..logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models.
    
    Provides common functionality for all database models including
    automatic timestamp management and common metadata.
    """
    pass


# Global database engine and session maker
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL from settings.
    
    Returns:
        Database connection URL.
        
    Raises:
        ValueError: If database URL is not configured.
    """
    settings = Settings()
    
    # For development, use SQLite
    if settings.langfuse.environment == "development":
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "database", "puntini.db")
        return f"sqlite+aiosqlite:///{db_path}"
    
    # For production, use configured database
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return db_url


def create_database_engine() -> AsyncEngine:
    """Create async database engine.
    
    Returns:
        Configured async database engine.
    """
    database_url = get_database_url()
    
    # SQLite-specific configuration
    if database_url.startswith("sqlite"):
        engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
            },
        )
        
        # Enable foreign key constraints for SQLite
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            
    else:
        # PostgreSQL or other databases
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
        )
    
    return engine


async def init_database() -> None:
    """Initialize database connection and create tables.
    
    This function should be called once at application startup.
    It creates the database engine, session maker, and all tables.
    """
    global _engine, _async_session_maker
    
    try:
        logger.info("Initializing database connection...")
        
        # Create engine
        _engine = create_database_engine()
        
        # Create session maker
        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create all tables
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database() -> None:
    """Close database connections.
    
    This function should be called when shutting down the application.
    """
    global _engine
    
    if _engine:
        logger.info("Closing database connections...")
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.
    
    Yields:
        AsyncSession: Database session for use in dependency injection.
        
    Raises:
        RuntimeError: If database is not initialized.
    """
    if not _async_session_maker:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with _async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get the session maker for manual session management.
    
    Returns:
        Session maker instance.
        
    Raises:
        RuntimeError: If database is not initialized.
    """
    if not _async_session_maker:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return _async_session_maker
