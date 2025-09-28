"""Simple unit tests for database functionality.

This module contains basic unit tests for the database layer
to validate core functionality works correctly.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from puntini.database.base import init_database, get_async_session, close_database
from puntini.database.models import User, Role, UserRole, AgentSession
from puntini.database.repositories import UserRepository, SessionRepository


@pytest.mark.asyncio
async def test_database_initialization():
    """Test database initialization."""
    try:
        await init_database()
        
        # Test getting session
        async for session in get_async_session():
            assert session is not None
            break
        
        await close_database()
        assert True  # If we get here, initialization worked
    except Exception as e:
        pytest.fail(f"Database initialization failed: {e}")


@pytest.mark.asyncio
async def test_user_model_creation():
    """Test User model creation."""
    await init_database()
    
    try:
        async for session in get_async_session():
            user_repo = UserRepository(session)
            
            # Test user creation
            user = await user_repo.create_user(
                username="testuser",
                email="test@example.com",
                password="testpass123",
                full_name="Test User"
            )
            
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.full_name == "Test User"
            assert user.hashed_password != "testpass123"  # Should be hashed
            assert user.is_active is True
            
            break
    
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_user_authentication():
    """Test user authentication."""
    await init_database()
    
    try:
        async for session in get_async_session():
            user_repo = UserRepository(session)
            
            # Create user
            user = await user_repo.create_user(
                username="authtest",
                email="auth@example.com",
                password="authpass123"
            )
            
            # Test successful authentication
            auth_user = await user_repo.authenticate("authtest", "authpass123")
            assert auth_user is not None
            assert auth_user.username == "authtest"
            
            # Test failed authentication
            failed_auth = await user_repo.authenticate("authtest", "wrongpass")
            assert failed_auth is None
            
            break
    
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_role_model_creation():
    """Test Role model creation."""
    await init_database()
    
    try:
        async for session in get_async_session():
            # Create role
            role = Role(
                name="test_role",
                display_name="Test Role",
                description="A test role",
                permissions='["permission1", "permission2"]',
                is_system_role=False,
                priority=50
            )
            
            session.add(role)
            await session.commit()
            await session.refresh(role)
            
            assert role.name == "test_role"
            assert role.display_name == "Test Role"
            assert role.description == "A test role"
            assert role.is_system_role is False
            assert role.priority == 50
            assert role.is_active is True
            
            # Test permission checking
            assert role.has_permission("permission1") is True
            assert role.has_permission("permission2") is True
            assert role.has_permission("permission3") is False
            
            break
    
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_session_model_creation():
    """Test AgentSession model creation."""
    await init_database()
    
    try:
        async for session in get_async_session():
            session_repo = SessionRepository(session)
            
            # Create session
            agent_session = await session_repo.create_session(
                session_id="test-session-unique-123",
                user_id=1,  # Assuming user with ID 1 exists
                goal="Test goal",
                name="Test Session"
            )
            
            assert agent_session.session_id == "test-session-unique-123"
            assert agent_session.user_id == 1
            assert agent_session.goal == "Test goal"
            assert agent_session.name == "Test Session"
            assert agent_session.is_active is True
            assert agent_session.is_paused is False
            assert agent_session.retry_count == 0
            
            break
    
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_user_repository_methods():
    """Test UserRepository methods."""
    await init_database()
    
    try:
        async for session in get_async_session():
            user_repo = UserRepository(session)
            
            # Create user
            user = await user_repo.create_user(
                username="repotest",
                email="repo@example.com",
                password="repopass123"
            )
            
            # Test get_by_username
            found_user = await user_repo.get_by_username("repotest")
            assert found_user is not None
            assert found_user.username == "repotest"
            
            # Test get_by_email
            found_user = await user_repo.get_by_email("repo@example.com")
            assert found_user is not None
            assert found_user.email == "repo@example.com"
            
            # Test search
            results = await user_repo.search_users("repotest")
            assert len(results) == 1
            assert results[0].username == "repotest"
            
            break
    
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_session_repository_methods():
    """Test SessionRepository methods."""
    await init_database()
    
    try:
        async for session in get_async_session():
            session_repo = SessionRepository(session)
            
            # Create session
            agent_session = await session_repo.create_session(
                session_id="repo-test-123",
                user_id=1,
                goal="Repository test goal"
            )
            
            # Test get_by_session_id
            found_session = await session_repo.get_by_session_id("repo-test-123")
            assert found_session is not None
            assert found_session.session_id == "repo-test-123"
            
            # Test update_session_state
            progress = ["Step 1 completed", "Step 2 in progress"]
            updated_session = await session_repo.update_session_state(
                session_id="repo-test-123",
                current_step="executing",
                progress=progress
            )
            
            assert updated_session is not None
            assert updated_session.current_step == "executing"
            assert updated_session.get_progress() == progress
            
            break
    
    finally:
        await close_database()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
