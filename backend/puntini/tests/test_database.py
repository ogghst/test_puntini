"""Unit tests for database models and repositories.

This module contains comprehensive unit tests for the database layer
including models, repositories, and initialization functionality.
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from puntini.database.base import init_database, get_async_session, close_database
from puntini.database.models import User, Role, UserRole, AgentSession
from puntini.database.repositories import UserRepository, SessionRepository
from puntini.database.init_db import create_default_roles, create_default_users


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_session():
    """Create a database session for testing."""
    await init_database()
    async for session in get_async_session():
        yield session
        break
    await close_database()


@pytest.fixture
async def user_repo(db_session: AsyncSession):
    """Create a user repository for testing."""
    return UserRepository(db_session)


@pytest.fixture
async def session_repo(db_session: AsyncSession):
    """Create a session repository for testing."""
    return SessionRepository(db_session)


class TestUserModel:
    """Test cases for User model."""
    
    @pytest.mark.asyncio
    async def test_user_creation(self, user_repo: UserRepository):
        """Test user creation with proper password hashing."""
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
        assert user.is_verified is False
        assert user.is_superuser is False
    
    @pytest.mark.asyncio
    async def test_user_authentication(self, user_repo: UserRepository):
        """Test user authentication."""
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
        
        # Test authentication with email
        email_auth = await user_repo.authenticate("auth@example.com", "authpass123")
        assert email_auth is not None
        assert email_auth.username == "authtest"
    
    @pytest.mark.asyncio
    async def test_user_role_assignment(self, user_repo: UserRepository, db_session: AsyncSession):
        """Test user role assignment."""
        # Create user
        user = await user_repo.create_user(
            username="roletest",
            email="role@example.com",
            password="rolepass123"
        )
        
        # Create role
        role = Role(
            name="test_role",
            display_name="Test Role",
            description="A test role",
            permissions='["test_permission"]'
        )
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        # Assign role
        success = await user_repo.assign_role(user.id, role.id)
        assert success is True
        
        # Check role assignment
        await db_session.refresh(user)
        await db_session.refresh(user, ["user_roles"])
        assert len(user.user_roles) == 1
        assert user.user_roles[0].role.name == "test_role"
        assert user.has_role("test_role") is True
    
    @pytest.mark.asyncio
    async def test_user_search(self, user_repo: UserRepository):
        """Test user search functionality."""
        # Create test users
        await user_repo.create_user(
            username="searchuser1",
            email="search1@example.com",
            password="pass123",
            full_name="Search User One"
        )
        
        await user_repo.create_user(
            username="searchuser2",
            email="search2@example.com",
            password="pass123",
            full_name="Search User Two"
        )
        
        # Test search by username
        results = await user_repo.search_users("searchuser1")
        assert len(results) == 1
        assert results[0].username == "searchuser1"
        
        # Test search by email
        results = await user_repo.search_users("search1@example.com")
        assert len(results) == 1
        assert results[0].email == "search1@example.com"
        
        # Test search by full name
        results = await user_repo.search_users("Search User")
        assert len(results) == 2


class TestRoleModel:
    """Test cases for Role model."""
    
    async def test_role_creation(self, db_session: AsyncSession):
        """Test role creation."""
        role = Role(
            name="test_role",
            display_name="Test Role",
            description="A test role for testing",
            permissions='["permission1", "permission2"]',
            is_system_role=False,
            priority=50
        )
        
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        assert role.name == "test_role"
        assert role.display_name == "Test Role"
        assert role.description == "A test role for testing"
        assert role.is_system_role is False
        assert role.priority == 50
        assert role.is_active is True
    
    async def test_role_permissions(self, db_session: AsyncSession):
        """Test role permission management."""
        role = Role(
            name="perm_test",
            display_name="Permission Test Role",
            permissions='["read", "write"]'
        )
        
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        # Test permission checking
        assert role.has_permission("read") is True
        assert role.has_permission("write") is True
        assert role.has_permission("delete") is False
        
        # Test permission list
        permissions = role.get_permissions_list()
        assert "read" in permissions
        assert "write" in permissions
        assert len(permissions) == 2
        
        # Test adding permission
        role.add_permission("delete")
        assert role.has_permission("delete") is True
        
        # Test removing permission
        role.remove_permission("read")
        assert role.has_permission("read") is False
        assert role.has_permission("write") is True


class TestAgentSessionModel:
    """Test cases for AgentSession model."""
    
    async def test_session_creation(self, session_repo: SessionRepository):
        """Test agent session creation."""
        session = await session_repo.create_session(
            session_id="test-session-123",
            user_id=1,  # Assuming user with ID 1 exists
            goal="Test goal",
            name="Test Session"
        )
        
        assert session.session_id == "test-session-123"
        assert session.user_id == 1
        assert session.goal == "Test goal"
        assert session.name == "Test Session"
        assert session.is_active is True
        assert session.is_paused is False
        assert session.retry_count == 0
    
    async def test_session_state_management(self, session_repo: SessionRepository):
        """Test session state management."""
        # Create session
        session = await session_repo.create_session(
            session_id="state-test-123",
            user_id=1,
            goal="State test goal"
        )
        
        # Update session state
        progress = ["Step 1 completed", "Step 2 in progress"]
        failures = ["Error in step 2"]
        artifacts = ["artifact1.json", "artifact2.txt"]
        
        updated_session = await session_repo.update_session_state(
            session_id="state-test-123",
            current_step="executing",
            progress=progress,
            failures=failures,
            artifacts=artifacts
        )
        
        assert updated_session is not None
        assert updated_session.current_step == "executing"
        assert updated_session.get_progress() == progress
        assert updated_session.get_failures() == failures
        assert updated_session.get_artifacts() == artifacts
    
    async def test_session_pause_resume(self, session_repo: SessionRepository):
        """Test session pause and resume functionality."""
        # Create session
        session = await session_repo.create_session(
            session_id="pause-test-123",
            user_id=1,
            goal="Pause test goal"
        )
        
        # Pause session
        paused = await session_repo.pause_session("pause-test-123")
        assert paused is True
        
        # Check session is paused
        paused_session = await session_repo.get_by_session_id("pause-test-123")
        assert paused_session.is_paused is True
        
        # Resume session
        resumed = await session_repo.resume_session("pause-test-123")
        assert resumed is True
        
        # Check session is resumed
        resumed_session = await session_repo.get_by_session_id("pause-test-123")
        assert resumed_session.is_paused is False


class TestDatabaseInitialization:
    """Test cases for database initialization."""
    
    async def test_default_roles_creation(self, db_session: AsyncSession):
        """Test default roles creation."""
        await create_default_roles(db_session)
        
        # Check that default roles were created
        admin_role = await db_session.execute(
            "SELECT * FROM roles WHERE name = 'admin'"
        )
        assert admin_role.fetchone() is not None
        
        user_role = await db_session.execute(
            "SELECT * FROM roles WHERE name = 'user'"
        )
        assert user_role.fetchone() is not None
        
        guest_role = await db_session.execute(
            "SELECT * FROM roles WHERE name = 'guest'"
        )
        assert guest_role.fetchone() is not None
    
    async def test_default_users_creation(self, db_session: AsyncSession):
        """Test default users creation."""
        # First create roles
        await create_default_roles(db_session)
        
        # Then create users
        await create_default_users(db_session)
        
        # Check that default users were created
        admin_user = await db_session.execute(
            "SELECT * FROM users WHERE username = 'admin'"
        )
        assert admin_user.fetchone() is not None
        
        user_user = await db_session.execute(
            "SELECT * FROM users WHERE username = 'user'"
        )
        assert user_user.fetchone() is not None


class TestUserRepository:
    """Test cases for UserRepository."""
    
    async def test_get_by_username(self, user_repo: UserRepository):
        """Test getting user by username."""
        # Create user
        user = await user_repo.create_user(
            username="gettest",
            email="get@example.com",
            password="getpass123"
        )
        
        # Test getting by username
        found_user = await user_repo.get_by_username("gettest")
        assert found_user is not None
        assert found_user.username == "gettest"
        
        # Test getting non-existent user
        not_found = await user_repo.get_by_username("nonexistent")
        assert not_found is None
    
    async def test_get_by_email(self, user_repo: UserRepository):
        """Test getting user by email."""
        # Create user
        user = await user_repo.create_user(
            username="emailtest",
            email="email@example.com",
            password="emailpass123"
        )
        
        # Test getting by email
        found_user = await user_repo.get_by_email("email@example.com")
        assert found_user is not None
        assert found_user.email == "email@example.com"
        
        # Test getting non-existent email
        not_found = await user_repo.get_by_email("nonexistent@example.com")
        assert not_found is None
    
    async def test_password_update(self, user_repo: UserRepository):
        """Test password update."""
        # Create user
        user = await user_repo.create_user(
            username="passtest",
            email="pass@example.com",
            password="oldpass123"
        )
        
        # Update password
        success = await user_repo.update_password(user.id, "newpass123")
        assert success is True
        
        # Test authentication with new password
        auth_user = await user_repo.authenticate("passtest", "newpass123")
        assert auth_user is not None
        
        # Test authentication with old password fails
        old_auth = await user_repo.authenticate("passtest", "oldpass123")
        assert old_auth is None


if __name__ == "__main__":
    pytest.main([__file__])
