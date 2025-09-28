"""Session repository for agent session data access.

This module provides the SessionRepository class with session-specific
database operations and business logic.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models import AgentSession, User
from ...logging import get_logger

logger = get_logger(__name__)


class SessionRepository(BaseRepository[AgentSession]):
    """Repository for agent session data access operations.
    
    Provides session-specific database operations including session
    creation, retrieval, and management functionality.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize session repository.
        
        Args:
            session: Async database session.
        """
        super().__init__(AgentSession, session)
    
    async def get_by_session_id(self, session_id: str) -> Optional[AgentSession]:
        """Get session by session ID.
        
        Args:
            session_id: Session ID to search for.
            
        Returns:
            Session instance if found, None otherwise.
        """
        try:
            query = select(AgentSession).where(AgentSession.session_id == session_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get session by session_id {session_id}: {e}")
            raise
    
    async def get_user_sessions(
        self,
        user_id: int,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[AgentSession]:
        """Get sessions for a specific user.
        
        Args:
            user_id: User ID.
            active_only: Whether to return only active sessions.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of user sessions.
        """
        try:
            query = select(AgentSession).where(AgentSession.user_id == user_id)
            
            if active_only:
                query = query.where(AgentSession.is_active == True)
            
            query = query.order_by(desc(AgentSession.updated_at)).offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            raise
    
    async def create_session(
        self,
        session_id: str,
        user_id: int,
        goal: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs: Any
    ) -> AgentSession:
        """Create a new agent session.
        
        Args:
            session_id: Unique session identifier.
            user_id: User ID.
            goal: Session goal.
            name: Session name.
            **kwargs: Additional session fields.
            
        Returns:
            Created session instance.
            
        Raises:
            ValueError: If session_id already exists.
        """
        try:
            # Check if session_id already exists
            if await self.get_by_session_id(session_id):
                raise ValueError(f"Session ID '{session_id}' already exists")
            
            # Create session
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'goal': goal,
                'name': name,
                'last_activity': datetime.utcnow(),
                **kwargs
            }
            
            session = await self.create(**session_data)
            logger.info(f"Created new session: {session_id} for user {user_id}")
            return session
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            raise
    
    async def update_session_state(
        self,
        session_id: str,
        current_step: Optional[str] = None,
        progress: Optional[List[Any]] = None,
        failures: Optional[List[Any]] = None,
        artifacts: Optional[List[Any]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        escalation_context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Optional[AgentSession]:
        """Update session state data.
        
        Args:
            session_id: Session ID.
            current_step: Current execution step.
            progress: Progress list.
            failures: Failures list.
            artifacts: Artifacts list.
            context_data: Context data dictionary.
            escalation_context: Escalation context dictionary.
            **kwargs: Additional fields to update.
            
        Returns:
            Updated session instance if found, None otherwise.
        """
        try:
            session = await self.get_by_session_id(session_id)
            if not session:
                return None
            
            # Update basic fields
            update_data = {
                'current_step': current_step,
                'last_activity': datetime.utcnow(),
                **kwargs
            }
            
            # Update JSON fields
            if progress is not None:
                session.set_progress(progress)
            if failures is not None:
                session.set_failures(failures)
            if artifacts is not None:
                session.set_artifacts(artifacts)
            if context_data is not None:
                session.set_context_data(context_data)
            if escalation_context is not None:
                session.set_escalation_context(escalation_context)
            
            # Apply other updates
            for key, value in update_data.items():
                if hasattr(session, key) and value is not None:
                    setattr(session, key, value)
            
            await self.session.commit()
            await self.session.refresh(session)
            
            logger.debug(f"Updated session state: {session_id}")
            return session
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update session state {session_id}: {e}")
            raise
    
    async def pause_session(self, session_id: str) -> bool:
        """Pause a session.
        
        Args:
            session_id: Session ID.
            
        Returns:
            True if session was paused, False if not found.
        """
        try:
            updated = await self.update(
                session_id,
                is_paused=True,
                last_activity=datetime.utcnow()
            )
            if updated:
                logger.info(f"Paused session: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to pause session {session_id}: {e}")
            raise
    
    async def resume_session(self, session_id: str) -> bool:
        """Resume a session.
        
        Args:
            session_id: Session ID.
            
        Returns:
            True if session was resumed, False if not found.
        """
        try:
            updated = await self.update(
                session_id,
                is_paused=False,
                last_activity=datetime.utcnow()
            )
            if updated:
                logger.info(f"Resumed session: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to resume session {session_id}: {e}")
            raise
    
    async def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session.
        
        Args:
            session_id: Session ID.
            
        Returns:
            True if session was deactivated, False if not found.
        """
        try:
            updated = await self.update(
                session_id,
                is_active=False,
                last_activity=datetime.utcnow()
            )
            if updated:
                logger.info(f"Deactivated session: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to deactivate session {session_id}: {e}")
            raise
    
    async def get_expired_sessions(self, timeout_hours: int = 24) -> List[AgentSession]:
        """Get expired sessions.
        
        Args:
            timeout_hours: Hours after which sessions expire.
            
        Returns:
            List of expired sessions.
        """
        try:
            expiry_time = datetime.utcnow() - timedelta(hours=timeout_hours)
            
            query = select(AgentSession).where(
                and_(
                    AgentSession.is_active == True,
                    AgentSession.last_activity < expiry_time
                )
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get expired sessions: {e}")
            raise
    
    async def cleanup_expired_sessions(self, timeout_hours: int = 24) -> int:
        """Clean up expired sessions by deactivating them.
        
        Args:
            timeout_hours: Hours after which sessions expire.
            
        Returns:
            Number of sessions cleaned up.
        """
        try:
            expired_sessions = await self.get_expired_sessions(timeout_hours)
            count = 0
            
            for session in expired_sessions:
                if await self.deactivate_session(session.session_id):
                    count += 1
            
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            raise
    
    async def get_active_sessions(self, skip: int = 0, limit: int = 100) -> List[AgentSession]:
        """Get all active sessions.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of active sessions.
        """
        return await self.find_by_filters(is_active=True)
    
    async def search_sessions(
        self,
        query: str,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AgentSession]:
        """Search sessions by name, description, or goal.
        
        Args:
            query: Search query.
            user_id: Optional user ID to filter by.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of matching sessions.
        """
        try:
            search_term = f"%{query}%"
            conditions = [
                or_(
                    AgentSession.name.ilike(search_term),
                    AgentSession.description.ilike(search_term),
                    AgentSession.goal.ilike(search_term)
                )
            ]
            
            if user_id is not None:
                conditions.append(AgentSession.user_id == user_id)
            
            sql_query = (
                select(AgentSession)
                .where(and_(*conditions))
                .order_by(desc(AgentSession.updated_at))
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(sql_query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to search sessions with query '{query}': {e}")
            raise
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics.
        
        Returns:
            Dictionary with session statistics.
        """
        try:
            # Total sessions
            total_sessions = await self.count()
            
            # Active sessions
            active_sessions = len(await self.get_active_sessions())
            
            # Paused sessions
            paused_sessions = len(await self.find_by_filters(is_paused=True))
            
            # Sessions created today
            today = datetime.utcnow().date()
            today_sessions = len(await self.find_by_filters(
                created_at__gte=datetime.combine(today, datetime.min.time())
            ))
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'paused_sessions': paused_sessions,
                'inactive_sessions': total_sessions - active_sessions,
                'sessions_created_today': today_sessions
            }
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            raise
