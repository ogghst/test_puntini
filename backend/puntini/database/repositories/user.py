"""User repository for user data access.

This module provides the UserRepository class with user-specific
database operations and business logic.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models import User, Role, UserRole
from ...logging import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for user data access operations.
    
    Provides user-specific database operations including authentication,
    role management, and user search functionality.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize user repository.
        
        Args:
            session: Async database session.
        """
        super().__init__(User, session)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username to search for.
            
        Returns:
            User instance if found, None otherwise.
        """
        try:
            query = select(User).where(User.username == username)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: Email to search for.
            
        Returns:
            User instance if found, None otherwise.
        """
        try:
            query = select(User).where(User.email == email)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password.
        
        Args:
            username: Username or email.
            password: Plain text password.
            
        Returns:
            User instance if authentication successful, None otherwise.
        """
        try:
            # Try to find user by username or email
            user = await self.get_by_username(username)
            if not user:
                user = await self.get_by_email(username)
            
            if not user:
                logger.debug(f"User not found: {username}")
                return None
            
            # Check if user is active
            if not user.is_active:
                logger.debug(f"Inactive user attempted login: {username}")
                return None
            
            # Verify password
            import bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
                logger.debug(f"Successful authentication for user: {username}")
                return user
            else:
                logger.debug(f"Invalid password for user: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication failed for user {username}: {e}")
            raise
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        **kwargs: Any
    ) -> User:
        """Create a new user with hashed password.
        
        Args:
            username: Username.
            email: Email address.
            password: Plain text password.
            full_name: Full name.
            **kwargs: Additional user fields.
            
        Returns:
            Created user instance.
            
        Raises:
            ValueError: If username or email already exists.
        """
        try:
            # Check if username already exists
            if await self.get_by_username(username):
                raise ValueError(f"Username '{username}' already exists")
            
            # Check if email already exists
            if await self.get_by_email(email):
                raise ValueError(f"Email '{email}' already exists")
            
            # Hash password
            import bcrypt
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user
            user_data = {
                'username': username,
                'email': email,
                'hashed_password': hashed_password,
                'full_name': full_name,
                **kwargs
            }
            
            user = await self.create(**user_data)
            logger.info(f"Created new user: {username}")
            return user
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            raise
    
    async def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password.
        
        Args:
            user_id: User ID.
            new_password: New plain text password.
            
        Returns:
            True if password was updated, False if user not found.
        """
        try:
            import bcrypt
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            updated = await self.update(user_id, hashed_password=hashed_password)
            if updated:
                logger.info(f"Password updated for user id {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update password for user id {user_id}: {e}")
            raise
    
    async def get_users_with_roles(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users with their roles loaded.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of users with roles loaded.
        """
        try:
            query = (
                select(User)
                .options(selectinload(User.user_roles).selectinload(UserRole.role))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get users with roles: {e}")
            raise
    
    async def assign_role(self, user_id: int, role_id: int, assigned_by: Optional[int] = None) -> bool:
        """Assign a role to a user.
        
        Args:
            user_id: User ID.
            role_id: Role ID.
            assigned_by: ID of user who assigned the role.
            
        Returns:
            True if role was assigned, False if already assigned.
        """
        try:
            # Check if assignment already exists
            existing = await self.session.execute(
                select(UserRole).where(
                    and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
                )
            )
            if existing.scalar_one_or_none():
                return False
            
            # Create new assignment
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by
            )
            self.session.add(user_role)
            await self.session.commit()
            
            logger.info(f"Assigned role {role_id} to user {user_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to assign role {role_id} to user {user_id}: {e}")
            raise
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Remove a role from a user.
        
        Args:
            user_id: User ID.
            role_id: Role ID.
            
        Returns:
            True if role was removed, False if not assigned.
        """
        try:
            result = await self.session.execute(
                select(UserRole).where(
                    and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
                )
            )
            user_role = result.scalar_one_or_none()
            
            if not user_role:
                return False
            
            await self.session.delete(user_role)
            await self.session.commit()
            
            logger.info(f"Removed role {role_id} from user {user_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to remove role {role_id} from user {user_id}: {e}")
            raise
    
    async def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Search users by username, email, or full name.
        
        Args:
            query: Search query.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of matching users.
        """
        try:
            search_term = f"%{query}%"
            sql_query = (
                select(User)
                .where(
                    or_(
                        User.username.ilike(search_term),
                        User.email.ilike(search_term),
                        User.full_name.ilike(search_term)
                    )
                )
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(sql_query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to search users with query '{query}': {e}")
            raise
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of active users.
        """
        return await self.find_by_filters(is_active=True)
    
    async def get_admin_users(self) -> List[User]:
        """Get all admin users.
        
        Returns:
            List of admin users.
        """
        try:
            query = (
                select(User)
                .options(selectinload(User.user_roles).selectinload(UserRole.role))
                .where(User.is_superuser == True)
            )
            
            # Also include users with admin role
            admin_role_query = (
                select(User)
                .join(UserRole)
                .join(Role)
                .where(Role.name == "admin")
                .options(selectinload(User.user_roles).selectinload(UserRole.role))
            )
            
            result1 = await self.session.execute(query)
            result2 = await self.session.execute(admin_role_query)
            
            admin_users = list(result1.scalars().all())
            admin_users.extend(list(result2.scalars().all()))
            
            # Remove duplicates
            return list({user.id: user for user in admin_users}.values())
            
        except Exception as e:
            logger.error(f"Failed to get admin users: {e}")
            raise
