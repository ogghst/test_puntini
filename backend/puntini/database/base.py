"""Database base configuration and engine management.

This module provides the base database configuration, engine creation,
and session management for the Puntini Agent database layer.
"""

import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from ..utils.settings import Settings
from ..logging import get_logger

logger = get_logger(__name__)

# Custom naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all database models.
    
    This class provides the foundation for all database models with
    proper metadata configuration and naming conventions.
    """
    metadata = metadata


# Global engine and session maker instances
_engine: Optional[AsyncEngine] = None
_async_session: Optional[async_sessionmaker[AsyncSession]] = None


def get_database_url() -> str:
    """Get database URL from config.json or environment.
    
    Returns:
        Database URL string for SQLAlchemy engine creation.
        
    Raises:
        ValueError: If database configuration is invalid.
    """
    settings = Settings()
    db_config = settings.database
    
    # Check for environment variable override
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    
    db_type = db_config.type
    
    if db_type == "sqlite":
        location = db_config.location
        # Ensure absolute path
        if not os.path.isabs(location):
            # Get project root (assuming this file is in backend/puntini/database/)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            location = os.path.join(project_root, location)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(location), exist_ok=True)
        
        return f"sqlite+aiosqlite:///{location}"
    
    elif db_type == "postgresql":
        user = getattr(db_config, 'user', 'postgres')
        password = getattr(db_config, 'password', '')
        host = getattr(db_config, 'host', 'localhost')
        port = getattr(db_config, 'port', 5432)
        database = getattr(db_config, 'database', 'puntini')
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    
    elif db_type == "mysql":
        user = getattr(db_config, 'user', 'root')
        password = getattr(db_config, 'password', '')
        host = getattr(db_config, 'host', 'localhost')
        port = getattr(db_config, 'port', 3306)
        database = getattr(db_config, 'database', 'puntini')
        return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}"
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def create_async_engine_instance() -> AsyncEngine:
    """Create and configure async SQLAlchemy engine.
    
    Returns:
        Configured AsyncEngine instance.
        
    Raises:
        ValueError: If database configuration is invalid.
    """
    global _engine
    
    if _engine is None:
        database_url = get_database_url()
        settings = Settings()
        db_config = settings.database
        
        # Engine configuration
        engine_kwargs = {
            "echo": db_config.echo,
            "pool_size": db_config.pool_size,
            "max_overflow": db_config.max_overflow,
            "pool_timeout": db_config.pool_timeout,
            "pool_recycle": db_config.pool_recycle,
            "pool_pre_ping": db_config.pool_pre_ping,
        }
        
        _engine = create_async_engine(database_url, **engine_kwargs)
        logger.info(f"Created async engine for database: {database_url.split('://')[0]}")
    
    return _engine


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Get async session maker instance.
    
    Returns:
        Configured async_sessionmaker instance.
    """
    global _async_session
    
    if _async_session is None:
        engine = create_async_engine_instance()
        _async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("Created async session maker")
    
    return _async_session


async def close_engine():
    """Close the database engine and cleanup resources.
    
    This function should be called during application shutdown.
    """
    global _engine, _async_session
    
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")
    
    _async_session = None


# Convenience function for getting engine
def get_engine() -> AsyncEngine:
    """Get the current database engine instance.
    
    Returns:
        Current AsyncEngine instance.
    """
    return create_async_engine_instance()
