"""Database package for Puntini Agent.

This package provides database abstraction layer with SQLAlchemy 2.0,
centralized ORM operations, and configuration management.
"""

from .base import Base, get_database_url, create_async_engine, get_async_session
from .db import (
    # User operations
    create_user,
    get_user_by_id,
    get_user_by_username,
    get_user_by_email,
    update_user,
    delete_user,
    list_users,
    authenticate_user,
    change_user_password,
    activate_user,
    deactivate_user,
    # Session operations
    create_session,
    get_session_by_id,
    get_user_sessions,
    update_session,
    delete_session,
    cleanup_expired_sessions,
    # Role operations
    create_role,
    get_role_by_name,
    assign_role_to_user,
    revoke_role_from_user,
    get_user_roles,
    # Admin operations
    get_admin_users,
    get_system_stats,
    get_user_activity_stats,
    bulk_update_users,
)

__all__ = [
    "Base",
    "get_database_url",
    "create_async_engine", 
    "get_async_session",
    # User operations
    "create_user",
    "get_user_by_id",
    "get_user_by_username",
    "get_user_by_email",
    "update_user",
    "delete_user",
    "list_users",
    "authenticate_user",
    "change_user_password",
    "activate_user",
    "deactivate_user",
    # Session operations
    "create_session",
    "get_session_by_id",
    "get_user_sessions",
    "update_session",
    "delete_session",
    "cleanup_expired_sessions",
    # Role operations
    "create_role",
    "get_role_by_name",
    "assign_role_to_user",
    "revoke_role_from_user",
    "get_user_roles",
    # Admin operations
    "get_admin_users",
    "get_system_stats",
    "get_user_activity_stats",
    "bulk_update_users",
]


