"""Database initialization script.

This script creates the database schema and initializes default users
as specified in the PROJECT_PLAN.md.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from puntini.database.base import create_async_engine_instance, Base, close_engine
from puntini.database.db import create_user, create_role, assign_role_to_user
from puntini.logging import get_logger

logger = get_logger(__name__)


async def create_tables():
    """Create all database tables."""
    engine = create_async_engine_instance()
    
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from puntini.database.models import User, Role, UserRole, Session
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def create_default_roles():
    """Create default roles."""
    try:
        # Create admin role
        admin_role = await create_role("admin", "Administrator role with full system access")
        logger.info("Created admin role")
        
        # Create user role
        user_role = await create_role("user", "Standard user role with basic access")
        logger.info("Created user role")
        
        return admin_role, user_role
    except Exception as e:
        logger.error(f"Failed to create default roles: {e}")
        raise


async def create_default_users():
    """Create default users as specified in PROJECT_PLAN.md."""
    try:
        # Create admin user
        admin_user = await create_user(
            username="admin",
            email="admin@puntini.dev",
            password="admin",  # Must be changed on first login
            is_admin=True,
            full_name="System Administrator",
            bio="Default system administrator account"
        )
        logger.info("Created admin user")
        
        # Create standard user
        standard_user = await create_user(
            username="user",
            email="user@puntini.dev",
            password="user",  # Must be changed on first login
            is_admin=False,
            full_name="Standard User",
            bio="Default standard user account"
        )
        logger.info("Created standard user")
        
        return admin_user, standard_user
    except Exception as e:
        logger.error(f"Failed to create default users: {e}")
        raise


async def assign_default_roles(admin_user, standard_user):
    """Assign default roles to users."""
    try:
        # Assign admin role to admin user
        await assign_role_to_user(admin_user.id, "admin")
        logger.info("Assigned admin role to admin user")
        
        # Assign user role to standard user
        await assign_role_to_user(standard_user.id, "user")
        logger.info("Assigned user role to standard user")
        
    except Exception as e:
        logger.error(f"Failed to assign default roles: {e}")
        raise


async def init_database():
    """Initialize the database with schema and default data."""
    logger.info("Starting database initialization...")
    
    try:
        # Create tables
        await create_tables()
        
        # Create default roles
        admin_role, user_role = await create_default_roles()
        
        # Create default users
        admin_user, standard_user = await create_default_users()
        
        # Assign default roles
        await assign_default_roles(admin_user, standard_user)
        
        logger.info("Database initialization completed successfully!")
        logger.info("Default users created:")
        logger.info("  Admin: username='admin', password='admin' (CHANGE ON FIRST LOGIN)")
        logger.info("  User:  username='user', password='user' (CHANGE ON FIRST LOGIN)")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        # Clean up
        await close_engine()


def main():
    """Main entry point for database initialization."""
    print("Puntini Agent Database Initialization")
    print("=====================================")
    
    try:
        asyncio.run(init_database())
        print("\n✅ Database initialization completed successfully!")
        print("\nDefault users created:")
        print("  Admin: username='admin', password='admin' (CHANGE ON FIRST LOGIN)")
        print("  User:  username='user', password='user' (CHANGE ON FIRST LOGIN)")
        print("\n⚠️  IMPORTANT: Change default passwords on first login!")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


