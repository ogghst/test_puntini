# Database Package

This package provides the database abstraction layer for the Puntini Agent system using SQLAlchemy 2.0 with async support.

## Features

- **Async SQLAlchemy 2.0** setup with proper session management
- **User authentication** with bcrypt password hashing
- **Role-based access control (RBAC)** with flexible permissions
- **Session persistence** for agent state recovery
- **Database migrations** with Alembic
- **Repository pattern** for clean data access
- **Default users** and roles creation

## Models

### User Model
- User authentication and profile management
- Password hashing with bcrypt
- Role assignments and permission checking
- Account status and verification

### Role Model
- Role-based access control
- Permission management with JSON storage
- Role hierarchy and priority
- System vs. custom roles

### UserRole Model
- Many-to-many relationship between users and roles
- Role assignment tracking
- Active/inactive role assignments

### AgentSession Model
- Agent session persistence
- State recovery across browser sessions
- Progress, failures, and artifacts tracking
- Context and escalation data storage

## Usage

### Initialize Database

```python
from puntini.database.init_db import initialize_database

# Initialize with default users
await initialize_database(create_default_users_flag=True)

# Initialize without default users
await initialize_database(create_default_users_flag=False)
```

### CLI Commands

```bash
# Initialize database with default users
python -m puntini.cli init-db

# Initialize without default users
python -m puntini.cli init-db --no-default-users

# Check database health
python -m puntini.cli init-db --health-check

# Reset database (WARNING: deletes all data!)
python -m puntini.cli init-db --reset
```

### Using Repositories

```python
from puntini.database.repositories import UserRepository, SessionRepository
from puntini.database.base import get_async_session

# Get async session
async for session in get_async_session():
    # User operations
    user_repo = UserRepository(session)
    
    # Authenticate user
    user = await user_repo.authenticate("admin", "admin123")
    
    # Create new user
    new_user = await user_repo.create_user(
        username="newuser",
        email="newuser@example.com",
        password="password123",
        full_name="New User"
    )
    
    # Assign role
    await user_repo.assign_role(new_user.id, role_id=1)
    
    # Session operations
    session_repo = SessionRepository(session)
    
    # Create session
    agent_session = await session_repo.create_session(
        session_id="unique-session-id",
        user_id=user.id,
        goal="User's goal",
        name="Session Name"
    )
    
    # Update session state
    await session_repo.update_session_state(
        session_id="unique-session-id",
        current_step="planning",
        progress=["Step 1 completed", "Step 2 in progress"]
    )
    
    break  # Exit async generator
```

### Database Migrations

```bash
# Create new migration
cd puntini/database/migrations
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Default Users

The initialization script creates two default users:

### Admin User
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@puntini.dev`
- **Roles**: `admin` (with full permissions)
- **Permissions**: user_management, role_management, system_admin, etc.

### Standard User
- **Username**: `user`
- **Password**: `user123`
- **Email**: `user@puntini.dev`
- **Roles**: `user` (with basic permissions)
- **Permissions**: basic_access, session_management, profile_management

## Default Roles

### Admin Role
- Full system administrator privileges
- Can manage users and roles
- Access to admin dashboard
- System monitoring capabilities

### User Role
- Standard user privileges
- Session management
- Profile management
- Basic system access

### Guest Role
- Limited access
- Basic system access only

## Configuration

The database configuration is managed through environment variables:

```bash
# For development (SQLite)
DATABASE_URL=sqlite+aiosqlite:///./puntini.db

# For production (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/puntini
```

## Testing

Run the database test script to verify everything is working:

```bash
python test_database.py
```

## Security Considerations

1. **Password Hashing**: All passwords are hashed using bcrypt
2. **Default Passwords**: Default users must change passwords on first login
3. **Role-based Access**: All operations check user permissions
4. **Session Security**: Sessions have expiration and activity tracking
5. **SQL Injection Protection**: All queries use parameterized statements

## Dependencies

- `sqlalchemy>=2.0.0` - Modern async ORM
- `alembic>=1.13.0` - Database migrations
- `aiosqlite>=0.20.0` - Async SQLite driver
- `bcrypt>=4.2.1` - Password hashing

## File Structure

```
puntini/database/
├── __init__.py                 # Package exports
├── base.py                     # Database configuration and session management
├── init_db.py                  # Database initialization script
├── models/                     # Database models
│   ├── __init__.py
│   ├── user.py                 # User model
│   ├── role.py                 # Role model
│   ├── user_role.py            # User-Role association
│   └── session.py              # Agent session model
├── repositories/               # Data access layer
│   ├── __init__.py
│   ├── base.py                 # Base repository
│   ├── user.py                 # User repository
│   └── session.py              # Session repository
├── migrations/                 # Database migrations
│   ├── __init__.py
│   ├── alembic.ini             # Alembic configuration
│   └── alembic/                # Migration files
│       ├── env.py              # Migration environment
│       ├── script.py.mako      # Migration template
│       └── versions/           # Migration versions
└── scripts/                    # Utility scripts
    └── create_default_users.py # Default user creation script
```
