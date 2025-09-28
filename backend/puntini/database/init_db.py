"""Database initialization script.

This module provides functions to initialize the database with default
users, roles, and other essential data.
"""

import asyncio
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from .base import init_database, get_session_maker, close_database
from .models import User, Role, UserRole
from .repositories import UserRepository
from ..logging import get_logger

logger = get_logger(__name__)


async def create_default_roles(session: AsyncSession) -> None:
    """Create default roles in the database.
    
    Args:
        session: Database session.
    """
    logger.info("Creating default roles...")
    
    # Define default roles with their permissions
    default_roles = [
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Full system administrator with all permissions",
            "is_system_role": True,
            "priority": 100,
            "permissions": json.dumps([
                "user_management",
                "role_management", 
                "system_admin",
                "session_management",
                "admin_dashboard",
                "user_analytics",
                "system_monitoring"
            ])
        },
        {
            "name": "user",
            "display_name": "Standard User",
            "description": "Standard user with basic permissions",
            "is_system_role": True,
            "priority": 10,
            "permissions": json.dumps([
                "basic_access",
                "session_management",
                "profile_management"
            ])
        },
        {
            "name": "guest",
            "display_name": "Guest User",
            "description": "Guest user with limited permissions",
            "is_system_role": True,
            "priority": 1,
            "permissions": json.dumps([
                "basic_access"
            ])
        }
    ]
    
    # Create roles
    for role_data in default_roles:
        # Check if role already exists
        existing_role = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        if existing_role.scalar_one_or_none():
            logger.debug(f"Role '{role_data['name']}' already exists, skipping")
            continue
        
        # Create role
        role = Role(**role_data)
        session.add(role)
        logger.info(f"Created role: {role_data['name']}")
    
    await session.commit()
    logger.info("Default roles created successfully")


async def create_default_users(session: AsyncSession) -> None:
    """Create default users in the database.
    
    Args:
        session: Database session.
    """
    logger.info("Creating default users...")
    
    user_repo = UserRepository(session)
    
    # Default admin user
    admin_data = {
        "username": "admin",
        "email": "admin@puntini.dev",
        "password": "admin123",
        "full_name": "System Administrator",
        "first_name": "Admin",
        "last_name": "User",
        "is_active": True,
        "is_verified": True,
        "is_superuser": True
    }
    
    # Default standard user
    user_data = {
        "username": "user",
        "email": "user@puntini.dev", 
        "password": "user123",
        "full_name": "Standard User",
        "first_name": "Standard",
        "last_name": "User",
        "is_active": True,
        "is_verified": True,
        "is_superuser": False
    }
    
    # Create users
    users_to_create = [
        (admin_data, "admin"),
        (user_data, "user")
    ]
    
    for user_data_dict, role_name in users_to_create:
        try:
            # Check if user already exists
            existing_user = await user_repo.get_by_username(user_data_dict["username"])
            if existing_user:
                logger.debug(f"User '{user_data_dict['username']}' already exists, skipping")
                continue
            
            # Create user
            user = await user_repo.create_user(**user_data_dict)
            logger.info(f"Created user: {user.username}")
            
            # Assign role
            role_result = await session.execute(
                select(Role).where(Role.name == role_name)
            )
            role = role_result.scalar_one_or_none()
            if role:
                await user_repo.assign_role(user.id, role.id)
                logger.info(f"Assigned role '{role_name}' to user '{user.username}'")
            
        except Exception as e:
            logger.error(f"Failed to create user '{user_data_dict['username']}': {e}")
            raise
    
    await session.commit()
    logger.info("Default users created successfully")


async def initialize_database(create_default_users_flag: bool = True) -> None:
    """Initialize the database with tables and default data.
    
    Args:
        create_default_users_flag: Whether to create default users.
    """
    try:
        logger.info("Starting database initialization...")
        
        # Initialize database (create tables)
        await init_database()
        
        if create_default_users_flag:
            # Get session maker
            session_maker = get_session_maker()
            
            # Create default roles and users
            async with session_maker() as session:
                await create_default_roles(session)
                await create_default_users(session)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def reset_database() -> None:
    """Reset the database by dropping all tables and recreating them.
    
    WARNING: This will delete all data!
    """
    try:
        logger.warning("Resetting database - all data will be lost!")
        
        # Close existing connections
        await close_database()
        
        # Import here to avoid circular imports
        from .base import Base, create_database_engine
        
        # Create engine and drop all tables
        engine = create_database_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        await engine.dispose()
        
        logger.info("Database reset completed")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise


async def check_database_health() -> bool:
    """Check if database is healthy and accessible.
    
    Returns:
        True if database is healthy, False otherwise.
    """
    try:
        logger.info("Checking database health...")
        
        # Get session maker
        session_maker = get_session_maker()
        
        # Test database connection
        async with session_maker() as session:
            await session.execute(text("SELECT 1"))
        
        logger.info("Database health check passed")
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Puntini database")
    parser.add_argument(
        "--create-default-users",
        action="store_true",
        default=True,
        help="Create default users (admin and user)"
    )
    parser.add_argument(
        "--no-default-users",
        action="store_true",
        help="Skip creating default users"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (WARNING: deletes all data!)"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Check database health"
    )
    
    args = parser.parse_args()
    
    if args.health_check:
        result = asyncio.run(check_database_health())
        exit(0 if result else 1)
    
    if args.reset:
        asyncio.run(reset_database())
        return
    
    create_users = args.create_default_users and not args.no_default_users
    asyncio.run(initialize_database(create_users))


if __name__ == "__main__":
    main()
