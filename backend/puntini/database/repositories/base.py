"""Base repository for data access layer abstraction.

This module provides a base repository class with common CRUD operations
and query utilities for all database repositories.
"""

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from ..base import Base
from ...logging import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations.
    
    Provides a foundation for all repository classes with standard
    database operations and query utilities.
    
    Args:
        model: SQLAlchemy model class.
        session: Async database session.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """Initialize repository.
        
        Args:
            model: SQLAlchemy model class.
            session: Async database session.
        """
        self.model = model
        self.session = session
    
    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.
        
        Args:
            **kwargs: Field values for the new record.
            
        Returns:
            Created model instance.
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            logger.debug(f"Created {self.model.__name__} with id {instance.id}")
            return instance
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise
    
    async def get_by_id(self, id: int, load_relationships: bool = False) -> Optional[ModelType]:
        """Get record by ID.
        
        Args:
            id: Record ID.
            load_relationships: Whether to eager load relationships.
            
        Returns:
            Model instance if found, None otherwise.
        """
        try:
            query = select(self.model).where(self.model.id == id)
            
            if load_relationships:
                # Load common relationships if they exist
                if hasattr(self.model, 'user_roles'):
                    query = query.options(selectinload(self.model.user_roles))
                if hasattr(self.model, 'sessions'):
                    query = query.options(selectinload(self.model.sessions))
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} by id {id}: {e}")
            raise
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        load_relationships: bool = False
    ) -> List[ModelType]:
        """Get all records with pagination.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            load_relationships: Whether to eager load relationships.
            
        Returns:
            List of model instances.
        """
        try:
            query = select(self.model).offset(skip).limit(limit)
            
            if load_relationships:
                # Load common relationships if they exist
                if hasattr(self.model, 'user_roles'):
                    query = query.options(selectinload(self.model.user_roles))
                if hasattr(self.model, 'sessions'):
                    query = query.options(selectinload(self.model.sessions))
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get all {self.model.__name__}s: {e}")
            raise
    
    async def update(self, id: int, **kwargs: Any) -> Optional[ModelType]:
        """Update record by ID.
        
        Args:
            id: Record ID.
            **kwargs: Field values to update.
            
        Returns:
            Updated model instance if found, None otherwise.
        """
        try:
            # First check if record exists
            instance = await self.get_by_id(id)
            if not instance:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            await self.session.commit()
            await self.session.refresh(instance)
            logger.debug(f"Updated {self.model.__name__} with id {id}")
            return instance
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update {self.model.__name__} with id {id}: {e}")
            raise
    
    async def delete(self, id: int) -> bool:
        """Delete record by ID.
        
        Args:
            id: Record ID.
            
        Returns:
            True if record was deleted, False if not found.
        """
        try:
            # First check if record exists
            instance = await self.get_by_id(id)
            if not instance:
                return False
            
            await self.session.delete(instance)
            await self.session.commit()
            logger.debug(f"Deleted {self.model.__name__} with id {id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete {self.model.__name__} with id {id}: {e}")
            raise
    
    async def count(self) -> int:
        """Count total number of records.
        
        Returns:
            Total number of records.
        """
        try:
            from sqlalchemy import func
            query = select(func.count(self.model.id))
            result = await self.session.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Failed to count {self.model.__name__}s: {e}")
            raise
    
    async def exists(self, id: int) -> bool:
        """Check if record exists by ID.
        
        Args:
            id: Record ID.
            
        Returns:
            True if record exists, False otherwise.
        """
        try:
            instance = await self.get_by_id(id)
            return instance is not None
        except Exception as e:
            logger.error(f"Failed to check existence of {self.model.__name__} with id {id}: {e}")
            raise
    
    def build_query(self, **filters: Any) -> Select:
        """Build a query with filters.
        
        Args:
            **filters: Filter conditions.
            
        Returns:
            SQLAlchemy select query.
        """
        query = select(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                if value is not None:
                    if isinstance(value, list):
                        query = query.where(getattr(self.model, key).in_(value))
                    else:
                        query = query.where(getattr(self.model, key) == value)
        
        return query
    
    async def find_by_filters(self, **filters: Any) -> List[ModelType]:
        """Find records by filters.
        
        Args:
            **filters: Filter conditions.
            
        Returns:
            List of matching model instances.
        """
        try:
            query = self.build_query(**filters)
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to find {self.model.__name__}s by filters: {e}")
            raise
    
    async def find_one_by_filters(self, **filters: Any) -> Optional[ModelType]:
        """Find one record by filters.
        
        Args:
            **filters: Filter conditions.
            
        Returns:
            Matching model instance if found, None otherwise.
        """
        try:
            query = self.build_query(**filters)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to find one {self.model.__name__} by filters: {e}")
            raise
