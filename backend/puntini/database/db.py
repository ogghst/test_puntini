"""Centralized database operations.

This module contains ALL database operations for the Puntini Agent system.
All API endpoints MUST use functions from this module - no direct ORM calls allowed.
"""

import bcrypt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from .base import get_async_session
from .models import User, Role, UserRole, Session
from ..logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# USER OPERATIONS
# ============================================================================

async def create_user(
    username: str, 
    email: str, 
    password: str, 
    is_admin: bool = False,
    full_name: Optional[str] = None,
    bio: Optional[str] = None
) -> User:
    """Create a new user.
    
    Args:
        username: Username for the user.
        email: Email address for the user.
        password: Plain text password (will be hashed).
        is_admin: Whether the user is an admin.
        full_name: Full name of the user.
        bio: Bio/description of the user.
        
    Returns:
        Created User object.
        
    Raises:
        IntegrityError: If username or email already exists.
        ValueError: If password is empty.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    async_session = get_async_session()
    async with async_session() as session:
        try:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                is_admin=is_admin,
                full_name=full_name,
                bio=bio
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created user: {username}")
            return user
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Failed to create user {username}: {e}")
            raise


async def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID.
    
    Args:
        user_id: User ID to search for.
        
    Returns:
        User object if found, None otherwise.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username.
    
    Args:
        username: Username to search for.
        
    Returns:
        User object if found, None otherwise.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()


async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email.
    
    Args:
        email: Email address to search for.
        
    Returns:
        User object if found, None otherwise.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


async def update_user(user_id: int, **updates) -> Optional[User]:
    """Update user information.
    
    Args:
        user_id: ID of user to update.
        **updates: Fields to update.
        
    Returns:
        Updated User object if found, None otherwise.
        
    Raises:
        IntegrityError: If username or email already exists.
    """
    async_session = get_async_session()
    async with async_session() as session:
        try:
            # Hash password if provided
            if 'password' in updates:
                password = updates.pop('password')
                if password:
                    updates['password_hash'] = bcrypt.hashpw(
                        password.encode('utf-8'), 
                        bcrypt.gensalt()
                    ).decode('utf-8')
            
            result = await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(**updates)
                .returning(User)
            )
            user = result.scalar_one_or_none()
            if user:
                await session.commit()
                logger.info(f"Updated user: {user.username}")
            return user
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise


async def delete_user(user_id: int) -> bool:
    """Delete a user.
    
    Args:
        user_id: ID of user to delete.
        
    Returns:
        True if user was deleted, False if not found.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            delete(User).where(User.id == user_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted user: {user_id}")
            return True
        return False


async def list_users(
    skip: int = 0, 
    limit: int = 100, 
    is_active: Optional[bool] = None
) -> List[User]:
    """List users with pagination and filtering.
    
    Args:
        skip: Number of users to skip.
        limit: Maximum number of users to return.
        is_active: Filter by active status.
        
    Returns:
        List of User objects.
    """
    async_session = get_async_session()
    async with async_session() as session:
        query = select(User)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await session.execute(query)
        return list(result.scalars().all())


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password.
    
    Args:
        username: Username to authenticate.
        password: Plain text password.
        
    Returns:
        User object if authentication successful, None otherwise.
    """
    user = await get_user_by_username(username)
    if not user or not user.is_active:
        return None
    
    if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        # Update last login
        await update_user(user.id, last_login=datetime.utcnow())
        logger.info(f"User authenticated: {username}")
        return user
    
    logger.warning(f"Failed authentication attempt for user: {username}")
    return None


async def change_user_password(user_id: int, new_password: str) -> bool:
    """Change user password.
    
    Args:
        user_id: ID of user to update.
        new_password: New plain text password.
        
    Returns:
        True if password was changed, False if user not found.
    """
    if not new_password:
        raise ValueError("Password cannot be empty")
    
    user = await update_user(user_id, password=new_password)
    return user is not None


async def activate_user(user_id: int) -> bool:
    """Activate a user.
    
    Args:
        user_id: ID of user to activate.
        
    Returns:
        True if user was activated, False if not found.
    """
    user = await update_user(user_id, is_active=True)
    return user is not None


async def deactivate_user(user_id: int) -> bool:
    """Deactivate a user.
    
    Args:
        user_id: ID of user to deactivate.
        
    Returns:
        True if user was deactivated, False if not found.
    """
    user = await update_user(user_id, is_active=False)
    return user is not None


# ============================================================================
# SESSION OPERATIONS
# ============================================================================

async def create_session(
    user_id: int, 
    session_data: Dict[str, Any],
    session_name: str = "Default Session",
    description: Optional[str] = None,
    thread_id: Optional[str] = None,
    expires_in_hours: Optional[int] = None
) -> Session:
    """Create a new session.
    
    Args:
        user_id: ID of user creating the session.
        session_data: Session state data.
        session_name: Name of the session.
        description: Description of the session.
        thread_id: LangGraph thread ID.
        expires_in_hours: Session expiration in hours.
        
    Returns:
        Created Session object.
    """
    async_session = get_async_session()
    async with async_session() as session:
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        session_obj = Session(
            user_id=user_id,
            session_name=session_name,
            description=description,
            state_data=session_data,
            thread_id=thread_id,
            expires_at=expires_at
        )
        session.add(session_obj)
        await session.commit()
        await session.refresh(session_obj)
        logger.info(f"Created session: {session_name} for user {user_id}")
        return session_obj


async def get_session_by_id(session_id: int) -> Optional[Session]:
    """Get session by ID.
    
    Args:
        session_id: Session ID to search for.
        
    Returns:
        Session object if found, None otherwise.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()


async def get_user_sessions(user_id: int) -> List[Session]:
    """Get all sessions for a user.
    
    Args:
        user_id: ID of user to get sessions for.
        
    Returns:
        List of Session objects.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.last_accessed.desc())
        )
        return list(result.scalars().all())


async def update_session(session_id: int, session_data: Dict[str, Any]) -> Optional[Session]:
    """Update session data.
    
    Args:
        session_id: ID of session to update.
        session_data: New session state data.
        
    Returns:
        Updated Session object if found, None otherwise.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(
                state_data=session_data,
                last_accessed=datetime.utcnow()
            )
            .returning(Session)
        )
        session_obj = result.scalar_one_or_none()
        if session_obj:
            await session.commit()
            logger.info(f"Updated session: {session_id}")
        return session_obj


async def delete_session(session_id: int) -> bool:
    """Delete a session.
    
    Args:
        session_id: ID of session to delete.
        
    Returns:
        True if session was deleted, False if not found.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            delete(Session).where(Session.id == session_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted session: {session_id}")
            return True
        return False


async def cleanup_expired_sessions() -> int:
    """Clean up expired sessions.
    
    Returns:
        Number of sessions cleaned up.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            delete(Session).where(
                and_(
                    Session.expires_at.isnot(None),
                    Session.expires_at < datetime.utcnow()
                )
            )
        )
        count = result.rowcount
        if count > 0:
            await session.commit()
            logger.info(f"Cleaned up {count} expired sessions")
        return count


# ============================================================================
# ROLE OPERATIONS
# ============================================================================

async def create_role(name: str, description: str = "") -> Role:
    """Create a new role.
    
    Args:
        name: Name of the role.
        description: Description of the role.
        
    Returns:
        Created Role object.
        
    Raises:
        IntegrityError: If role name already exists.
    """
    async_session = get_async_session()
    async with async_session() as session:
        try:
            role = Role(name=name, description=description)
            session.add(role)
            await session.commit()
            await session.refresh(role)
            logger.info(f"Created role: {name}")
            return role
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Failed to create role {name}: {e}")
            raise


async def get_role_by_name(name: str) -> Optional[Role]:
    """Get role by name.
    
    Args:
        name: Role name to search for.
        
    Returns:
        Role object if found, None otherwise.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()


async def assign_role_to_user(user_id: int, role_name: str) -> bool:
    """Assign a role to a user.
    
    Args:
        user_id: ID of user to assign role to.
        role_name: Name of role to assign.
        
    Returns:
        True if role was assigned, False if user or role not found.
    """
    async_session = get_async_session()
    async with async_session() as session:
        try:
            # Check if user exists
            user = await get_user_by_id(user_id)
            if not user:
                return False
            
            # Check if role exists
            role = await get_role_by_name(role_name)
            if not role:
                return False
            
            # Check if already assigned
            existing = await session.execute(
                select(UserRole).where(
                    and_(UserRole.user_id == user_id, UserRole.role_id == role.id)
                )
            )
            if existing.scalar_one_or_none():
                return True  # Already assigned
            
            # Assign role
            user_role = UserRole(user_id=user_id, role_id=role.id)
            session.add(user_role)
            await session.commit()
            logger.info(f"Assigned role {role_name} to user {user_id}")
            return True
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Failed to assign role {role_name} to user {user_id}: {e}")
            return False


async def revoke_role_from_user(user_id: int, role_name: str) -> bool:
    """Revoke a role from a user.
    
    Args:
        user_id: ID of user to revoke role from.
        role_name: Name of role to revoke.
        
    Returns:
        True if role was revoked, False if not found.
    """
    async_session = get_async_session()
    async with async_session() as session:
        # Get role
        role = await get_role_by_name(role_name)
        if not role:
            return False
        
        # Remove assignment
        result = await session.execute(
            delete(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role.id)
            )
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Revoked role {role_name} from user {user_id}")
            return True
        return False


async def get_user_roles(user_id: int) -> List[Role]:
    """Get all roles for a user.
    
    Args:
        user_id: ID of user to get roles for.
        
    Returns:
        List of Role objects.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(Role)
            .join(UserRole)
            .where(UserRole.user_id == user_id)
        )
        return list(result.scalars().all())


# ============================================================================
# ADMIN OPERATIONS
# ============================================================================

async def get_admin_users() -> List[User]:
    """Get all admin users.
    
    Returns:
        List of admin User objects.
    """
    async_session = get_async_session()
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_admin == True)
        )
        return list(result.scalars().all())


async def get_system_stats() -> Dict[str, Any]:
    """Get system statistics.
    
    Returns:
        Dictionary with system statistics.
    """
    async_session = get_async_session()
    async with async_session() as session:
        # Count users
        user_count_result = await session.execute(
            select(func.count(User.id))
        )
        total_users = user_count_result.scalar()
        
        # Count active users
        active_users_result = await session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar()
        
        # Count sessions
        session_count_result = await session.execute(
            select(func.count(Session.id))
        )
        total_sessions = session_count_result.scalar()
        
        # Count active sessions
        active_sessions_result = await session.execute(
            select(func.count(Session.id)).where(Session.is_active == True)
        )
        active_sessions = active_sessions_result.scalar()
        
        # Count roles
        role_count_result = await session.execute(
            select(func.count(Role.id))
        )
        total_roles = role_count_result.scalar()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_roles": total_roles,
            "timestamp": datetime.utcnow().isoformat()
        }


async def get_user_activity_stats() -> Dict[str, Any]:
    """Get user activity statistics.
    
    Returns:
        Dictionary with user activity statistics.
    """
    async_session = get_async_session()
    async with async_session() as session:
        # Recent registrations (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations_result = await session.execute(
            select(func.count(User.id)).where(User.created_at >= week_ago)
        )
        recent_registrations = recent_registrations_result.scalar()
        
        # Recent logins (last 24 hours)
        day_ago = datetime.utcnow() - timedelta(days=1)
        recent_logins_result = await session.execute(
            select(func.count(User.id)).where(User.last_login >= day_ago)
        )
        recent_logins = recent_logins_result.scalar()
        
        return {
            "recent_registrations_7d": recent_registrations,
            "recent_logins_24h": recent_logins,
            "timestamp": datetime.utcnow().isoformat()
        }


async def bulk_update_users(user_ids: List[int], **updates) -> int:
    """Bulk update users.
    
    Args:
        user_ids: List of user IDs to update.
        **updates: Fields to update.
        
    Returns:
        Number of users updated.
    """
    if not user_ids:
        return 0
    
    async_session = get_async_session()
    async with async_session() as session:
        try:
            # Hash password if provided
            if 'password' in updates:
                password = updates.pop('password')
                if password:
                    updates['password_hash'] = bcrypt.hashpw(
                        password.encode('utf-8'), 
                        bcrypt.gensalt()
                    ).decode('utf-8')
            
            result = await session.execute(
                update(User)
                .where(User.id.in_(user_ids))
                .values(**updates)
            )
            count = result.rowcount
            await session.commit()
            logger.info(f"Bulk updated {count} users")
            return count
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Failed to bulk update users: {e}")
            raise
