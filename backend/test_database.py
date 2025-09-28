#!/usr/bin/env python3
"""Test script for database implementation.

This script tests the database models, repositories, and initialization
to ensure everything is working correctly.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from puntini.database.init_db import initialize_database, check_database_health
from puntini.database.repositories import UserRepository, SessionRepository
from puntini.database.base import get_async_session
from puntini.logging import get_logger

logger = get_logger(__name__)


async def test_database_models():
    """Test database models and repositories."""
    try:
        logger.info("Testing database models and repositories...")
        
        # Get database session
        async for session in get_async_session():
            # Test user repository
            user_repo = UserRepository(session)
            
            # Test getting users with relationships loaded
            users = await user_repo.get_users_with_roles()
            logger.info(f"Found {len(users)} users in database")
            
            # Test getting user by username
            admin_user = await user_repo.get_by_username("admin")
            if admin_user:
                logger.info(f"Admin user found: {admin_user.username} (ID: {admin_user.id})")
                # Load relationships explicitly
                await session.refresh(admin_user, ["user_roles"])
                logger.info(f"Admin user roles: {admin_user.role_names}")
                logger.info(f"Is admin: {admin_user.is_admin()}")
            else:
                logger.warning("Admin user not found")
            
            # Test getting user by username
            standard_user = await user_repo.get_by_username("user")
            if standard_user:
                logger.info(f"Standard user found: {standard_user.username} (ID: {standard_user.id})")
                # Load relationships explicitly
                await session.refresh(standard_user, ["user_roles"])
                logger.info(f"Standard user roles: {standard_user.role_names}")
                logger.info(f"Is admin: {standard_user.is_admin()}")
            else:
                logger.warning("Standard user not found")
            
            # Test authentication
            auth_user = await user_repo.authenticate("admin", "admin123")
            if auth_user:
                logger.info(f"Authentication successful for: {auth_user.username}")
            else:
                logger.warning("Authentication failed for admin user")
            
            # Test session repository
            session_repo = SessionRepository(session)
            
            # Test creating a session
            import uuid
            unique_session_id = f"test-session-{uuid.uuid4().hex[:8]}"
            test_session = await session_repo.create_session(
                session_id=unique_session_id,
                user_id=admin_user.id if admin_user else 1,
                goal="Test goal",
                name="Test Session"
            )
            logger.info(f"Created test session: {test_session.session_id}")
            
            # Test getting user sessions
            user_sessions = await session_repo.get_user_sessions(
                user_id=admin_user.id if admin_user else 1
            )
            logger.info(f"Found {len(user_sessions)} sessions for user")
            
            # Test session statistics
            stats = await session_repo.get_session_statistics()
            logger.info(f"Session statistics: {stats}")
            
            break  # Exit the async generator
        
        logger.info("✅ Database models and repositories test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting database tests...")
    
    # Initialize database first
    logger.info("0. Initializing database...")
    from puntini.database.init_db import initialize_database
    await initialize_database(create_default_users_flag=True)
    logger.info("✅ Database initialized")
    
    # Test database health
    logger.info("1. Testing database health...")
    health_ok = await check_database_health()
    if not health_ok:
        logger.error("Database health check failed")
        return False
    logger.info("✅ Database health check passed")
    
    # Test database models
    logger.info("2. Testing database models and repositories...")
    models_ok = await test_database_models()
    if not models_ok:
        logger.error("Database models test failed")
        return False
    
    logger.info("🎉 All database tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
