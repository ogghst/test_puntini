# PROJECT_PLAN.md

## Overview

This document outlines the implementation plan for adding missing features to the Puntini Agent codebase, focusing on human feedback handling, Neo4j integration, database layer abstraction, and user management system.

## Current Status Analysis

### ✅ Implemented Features
- **Interfaces**: All major component interfaces defined in `/puntini/interfaces/`
- **Factories**: Configuration-driven factories for all components
- **Base Models**: BaseEntity with UUIDv4 ID generation
- **State Management**: LangGraph state schema and orchestration skeleton
- **Observability**: Langfuse tracer implementations (noop, console, langfuse)
- **Server Configuration**: FastAPI server with settings integration
- **Graph Orchestration**: LangGraph skeleton with node placeholders
- **Context Management**: Simple context manager (progressive pending)
- **Graph Store**: In-memory and Memgraph implementations (Neo4j pending)

### ❌ Missing Features from AGENTS.md & GEMINI.md

#### 1. Human-in-the-Loop (HITL) Implementation
- **Current**: Basic escalate node with interrupt placeholder
- **Missing**: Complete human feedback handling in chat interface
- **Required**: WebSocket integration for real-time human input

#### 2. Neo4j Graph Store Implementation
- **Current**: Factory placeholder, Memgraph implementation exists
- **Missing**: Full Neo4j driver integration with MERGE semantics
- **Required**: Connection management, transaction handling, error mapping

#### 3. Database Layer Abstraction
- **Current**: No database layer for user/session management
- **Missing**: SQLAlchemy integration, user models, session persistence
- **Required**: User authentication, role management, session recovery

#### 4. Progressive Context Disclosure
- **Current**: Simple context manager only
- **Missing**: Full progressive disclosure implementation
- **Required**: Multi-level context preparation with retry logic

#### 5. Node Logic Implementation
- **Current**: Placeholder implementations in all nodes
- **Missing**: Concrete logic for parse_goal, plan_step, call_tool, evaluate, diagnose
- **Required**: LLM integration, tool execution, error classification

#### 6. Neo4j Backend Features
- **Current**: Not implemented
- **Missing**: MERGE semantics, typed errors, human-readable messages
- **Required**: Production-ready graph database operations

## Implementation Plan

### Phase 1: Database Layer & User Management (Priority: High)

#### 1.1 Database Abstraction Layer
**Libraries**: SQLAlchemy 2.0, aiosqlite, alembic

**Implementation**:
```python
# New files to create:
/puntini/database/
  ├── __init__.py
  ├── base.py              # Database base configuration
  ├── session.py           # Async session management
  ├── models/
  │   ├── __init__.py
  │   ├── user.py          # User model
  │   ├── session.py       # Session model
  │   ├── role.py          # Role model
  │   └── user_role.py     # User-Role association
  ├── repositories/
  │   ├── __init__.py
  │   ├── base.py          # Base repository
  │   ├── user.py          # User repository
  │   └── session.py       # Session repository
  └── migrations/
      └── alembic/         # Database migrations
```

**Features**:
- Async SQLAlchemy 2.0 setup with aiosqlite
- User model with authentication fields
- Session model for agent state persistence
- Role-based access control (RBAC)
- Repository pattern for data access
- Database migrations with Alembic
- Database initialization script with default users

#### 1.1.1 Database Initialization Script
**Implementation**:
```python
# New files:
/puntini/database/
  ├── init_db.py            # Database initialization script
  ├── seed_data.py          # Default data seeding
  └── scripts/
      └── create_default_users.py  # User creation script
```

**Features**:
- Database schema creation and migration
- Default admin user creation (username: admin, password: admin123)
- Default standard user creation (username: user, password: user123)
- Role assignment (admin role for admin user, user role for standard user)
- Password hashing with bcrypt
- Initial role creation (admin, user, guest)

**Default Users Created**:
```python
# Admin User
username: "admin"
email: "admin@puntini.dev"
password: "admin123"  # Must be changed on first login
role: "admin"
permissions: ["user_management", "role_management", "system_admin"]

# Standard User  
username: "user"
email: "user@puntini.dev"
password: "user123"   # Must be changed on first login
role: "user"
permissions: ["basic_access", "session_management"]
```

**Initialization Script Usage**:
```bash
# Run database initialization
python -m puntini.database.init_db

# Or via CLI command
puntini init-db --create-default-users
```

#### 1.2 User Management API
**Implementation**:
```python
# Extend existing API:
/puntini/api/
  ├── auth.py              # Enhanced authentication
  ├── users.py             # User management endpoints
  ├── roles.py             # Role management endpoints
  └── sessions.py          # Session management endpoints
```

**Features**:
- User registration/login endpoints
- JWT token authentication
- Role assignment/management
- Session creation/retrieval
- User profile management
- Admin-only user management endpoints
- Admin-only role management endpoints
- Admin dashboard data endpoints

#### 1.2.1 Admin API Endpoints
**Implementation**:
```python
# New admin endpoints:
/puntini/api/admin/
  ├── __init__.py
  ├── users.py             # Admin user management
  ├── roles.py             # Admin role management
  ├── dashboard.py         # Admin dashboard data
  └── permissions.py       # Permission management
```

**Admin User Management Features**:
- List all users with pagination and filtering
- Create new users (admin-only)
- Update user profiles and roles
- Deactivate/activate users
- Reset user passwords
- View user activity logs
- Bulk user operations

**Admin Role Management Features**:
- List all roles and permissions
- Create new roles
- Update role permissions
- Delete roles (with safety checks)
- Assign/revoke roles to/from users
- Role hierarchy management

**Admin Dashboard Features**:
- System statistics (total users, active sessions, etc.)
- User activity metrics
- System health monitoring
- Recent user registrations
- Failed login attempts
- Session analytics

#### 1.3 Frontend User Management
**Implementation**:
```typescript
// New frontend components:
/frontend/app/
  ├── components/
  │   ├── auth/
  │   │   ├── LoginForm.tsx
  │   │   ├── RegisterForm.tsx
  │   │   └── UserProfile.tsx
  │   ├── admin/
  │   │   ├── UserManagement.tsx
  │   │   └── RoleManagement.tsx
  │   └── session/
  │       ├── SessionList.tsx
  │       └── SessionRecovery.tsx
  └── pages/
      ├── login/
      ├── register/
      ├── profile/
      └── admin/
```

**Features**:
- Login/register forms
- User profile management
- Admin interface for user/role management
- Session recovery interface
- Role-based UI access control
- Admin dashboard with system overview
- User activity monitoring
- Role-based navigation and permissions

#### 1.3.1 Admin Frontend Components
**Implementation**:
```typescript
// Enhanced admin components:
/frontend/app/
  ├── components/
  │   ├── admin/
  │   │   ├── AdminDashboard.tsx        # Main admin dashboard
  │   │   ├── UserManagement.tsx        # User management interface
  │   │   ├── RoleManagement.tsx        # Role management interface
  │   │   ├── UserList.tsx              # User listing with filters
  │   │   ├── UserForm.tsx              # User creation/editing form
  │   │   ├── RoleForm.tsx              # Role creation/editing form
  │   │   ├── UserActivity.tsx          # User activity logs
  │   │   ├── SystemStats.tsx           # System statistics
  │   │   └── AdminLayout.tsx           # Admin layout wrapper
  │   ├── common/
  │   │   ├── ProtectedRoute.tsx        # Role-based route protection
  │   │   ├── PermissionGuard.tsx       # Component-level permissions
  │   │   └── AdminNavbar.tsx           # Admin navigation
  └── pages/
      ├── admin/
      │   ├── dashboard/
      │   ├── users/
      │   ├── roles/
      │   └── settings/
```

**Admin Dashboard Features**:
- System overview with key metrics
- User registration trends
- Active session monitoring
- Recent user activity
- System health indicators
- Quick actions (create user, manage roles)

**User Management Interface Features**:
- Data table with sorting, filtering, and pagination
- User creation/editing modal forms
- Bulk operations (activate/deactivate users)
- User search and advanced filtering
- Export user data functionality
- User activity timeline view

**Role Management Interface Features**:
- Role hierarchy visualization
- Permission matrix interface
- Role assignment to users
- Role creation wizard
- Permission templates
- Role usage analytics

### Phase 2: Neo4j Graph Store Implementation (Priority: High)

#### 2.1 Neo4j Driver Integration
**Libraries**: neo4j (official Python driver)

**Implementation**:
```python
# New files:
/puntini/graph/
  ├── neo4j_graph.py       # Neo4j implementation
  └── neo4j_config.py      # Neo4j configuration
```

**Features**:
- Async Neo4j driver integration
- Connection pooling and management
- MERGE semantics for idempotent operations
- Transaction support
- Error mapping to domain errors
- Connection health monitoring

#### 2.2 Graph Store Factory Enhancement
**Implementation**:
```python
# Update existing:
/puntini/graph/graph_store_factory.py
```

**Features**:
- Neo4j configuration support
- Connection validation
- Graceful fallback to in-memory store
- Production-ready error handling

### Phase 3: Human-in-the-Loop Implementation (Priority: Medium)

#### 3.1 Enhanced Escalate Node
**Implementation**:
```python
# Update existing:
/puntini/nodes/escalate.py
```

**Features**:
- Complete escalation context preparation
- Human input validation
- Resume logic with human feedback
- Escalation history tracking

#### 3.2 WebSocket Integration
**Implementation**:
```python
# New files:
/puntini/api/
  ├── websocket_hitl.py    # HITL WebSocket handler
  └── escalation_manager.py # Escalation state management
```

**Features**:
- Real-time escalation notifications
- Human input collection via WebSocket
- Escalation state persistence
- Timeout handling for human input

#### 3.3 Frontend HITL Interface
**Implementation**:
```typescript
// New components:
/frontend/app/
  ├── components/
  │   └── escalation/
  │       ├── EscalationDialog.tsx
  │       ├── HumanFeedbackForm.tsx
  │       └── EscalationHistory.tsx
  └── hooks/
      └── useEscalation.tsx
```

**Features**:
- Real-time escalation notifications
- Human feedback forms
- Escalation history display
- WebSocket connection management

### Phase 4: Progressive Context Disclosure (Priority: Medium)

#### 4.1 Enhanced Context Manager
**Implementation**:
```python
# Update existing:
/puntini/context/context_manager.py
```

**Features**:
- Multi-level context preparation
- Retry logic with context expansion
- Context size management
- LLM token optimization

#### 4.2 Context Strategies
**Implementation**:
```python
# New files:
/puntini/context/
  ├── strategies/
  │   ├── __init__.py
  │   ├── minimal.py       # Minimal context strategy
  │   ├── error_aware.py   # Error-aware context strategy
  │   └── historical.py    # Historical context strategy
  └── context_builder.py   # Context building orchestration
```

**Features**:
- Configurable context strategies
- Context size optimization
- Progressive disclosure policies
- Context relevance scoring

### Phase 5: Node Logic Implementation (Priority: Medium)

#### 5.1 Parse Goal Node
**Implementation**:
```python
# Update existing:
/puntini/nodes/parse_goal.py
```

**Features**:
- LLM integration for goal parsing
- Structured output validation
- Goal complexity assessment
- Domain hint extraction

#### 5.2 Plan Step Node
**Implementation**:
```python
# Update existing:
/puntini/nodes/plan_step.py
```

**Features**:
- Step planning with LLM
- Tool selection logic
- Plan validation
- Step dependency management

#### 5.3 Call Tool Node
**Implementation**:
```python
# Update existing:
/puntini/nodes/call_tool.py
```

**Features**:
- Tool execution with validation
- Error handling and normalization
- Tool result processing
- Execution timing and metrics

#### 5.4 Evaluate Node
**Implementation**:
```python
# Update existing:
/puntini/nodes/evaluate.py
```

**Features**:
- Step result evaluation
- Progress assessment
- Routing decision logic
- Retry policy enforcement

#### 5.5 Diagnose Node
**Implementation**:
```python
# Update existing:
/puntini/nodes/diagnose.py
```

**Features**:
- Error classification (identical/random/systematic)
- Failure pattern analysis
- Remediation strategy selection
- Error context preparation

### Phase 6: Production Features (Priority: Low)

#### 6.1 Monitoring & Observability
**Implementation**:
- Enhanced Langfuse integration
- Custom metrics collection
- Performance monitoring
- Error tracking and alerting

#### 6.2 Security Enhancements
**Implementation**:
- Input validation and sanitization
- Rate limiting
- Audit logging
- Security headers

#### 6.3 Performance Optimization
**Implementation**:
- Connection pooling optimization
- Query caching
- Async operation optimization
- Resource management

## Implementation Dependencies

### Critical Path Dependencies
1. **Database Layer** → **User Management** → **Session Persistence**
2. **Neo4j Implementation** → **Graph Operations** → **Node Logic**
3. **HITL Infrastructure** → **Escalate Node** → **Frontend Integration**

### Feature Interactions

#### User Management ↔ Session Persistence
- User authentication enables session recovery
- Role-based access controls session visibility
- User preferences influence agent behavior

#### Neo4j ↔ Graph Operations
- Neo4j implementation enables real graph operations
- MERGE semantics ensures idempotent operations
- Graph store factory provides abstraction layer

#### HITL ↔ Node Logic
- Escalate node requires complete node implementations
- Human feedback influences planning and execution
- Escalation history improves future decisions

#### Database ↔ API ↔ Frontend
- Database models drive API schemas
- API endpoints enable frontend functionality
- Frontend state management requires backend persistence

## Technology Stack Decisions

### Database Layer
- **SQLAlchemy 2.0**: Modern async ORM with excellent type hints
- **aiosqlite**: Async SQLite driver for development
- **Alembic**: Database migration management
- **PostgreSQL**: Production database (future consideration)

### Neo4j Integration
- **neo4j Python Driver**: Official driver with async support
- **Connection pooling**: Built-in driver pooling
- **MERGE semantics**: Native Neo4j idempotent operations

### WebSocket & Real-time
- **FastAPI WebSockets**: Native WebSocket support
- **Async context managers**: Proper connection lifecycle
- **Message queuing**: Redis for production (future)

### Frontend Enhancements
- **React Query**: Server state management
- **WebSocket hooks**: Real-time communication
- **Form validation**: Zod for type-safe forms
- **State management**: Zustand for client state

## Quality Assurance

### Testing Strategy
1. **Unit Tests**: All new components and functions
2. **Integration Tests**: Database operations and API endpoints
3. **E2E Tests**: Complete user workflows
4. **Performance Tests**: Database and graph operations
5. **Security Tests**: Authentication and authorization

### Code Quality
- **Type Hints**: Complete type coverage
- **Docstrings**: Google-style documentation
- **Error Handling**: Comprehensive error mapping
- **Logging**: Structured logging with context
- **Monitoring**: Metrics and health checks

### Deployment Considerations
- **Database Migrations**: Automated migration deployment
- **Configuration Management**: Environment-specific configs
- **Health Checks**: Database and external service monitoring
- **Rollback Strategy**: Safe deployment rollback procedures

## Timeline Estimate

### Phase 1: Database Layer & User Management (3-4 weeks)
- Week 1: Database abstraction, models, and initialization script
- Week 2: User management API, authentication, and admin endpoints
- Week 3: Frontend user management and admin components
- Week 4: Admin dashboard, role management, and testing

### Phase 2: Neo4j Implementation (1-2 weeks)
- Week 1: Neo4j driver integration and basic operations
- Week 2: Production-ready features and error handling

### Phase 3: Human-in-the-Loop (2-3 weeks)
- Week 1: Enhanced escalate node and WebSocket infrastructure
- Week 2: Frontend HITL interface and real-time communication
- Week 3: Integration testing and refinement

### Phase 4: Progressive Context Disclosure (1-2 weeks)
- Week 1: Enhanced context manager implementation
- Week 2: Context strategies and optimization

### Phase 5: Node Logic Implementation (3-4 weeks)
- Week 1: Parse goal and plan step nodes
- Week 2: Call tool and evaluate nodes
- Week 3: Diagnose node and error classification
- Week 4: Integration testing and refinement

### Phase 6: Production Features (2-3 weeks)
- Week 1: Monitoring and observability enhancements
- Week 2: Security and performance optimizations
- Week 3: Final testing and documentation

**Total Estimated Timeline: 12-18 weeks**

## Risk Mitigation

### Technical Risks
1. **Neo4j Integration Complexity**: Start with simple operations, iterate
2. **WebSocket Reliability**: Implement robust reconnection logic
3. **Database Performance**: Use connection pooling and query optimization
4. **Frontend-Backend Sync**: Implement proper state synchronization

### Project Risks
1. **Scope Creep**: Stick to defined phases, document changes
2. **Timeline Delays**: Build in buffer time, prioritize critical features
3. **Resource Constraints**: Focus on core functionality first
4. **Integration Issues**: Comprehensive testing at each phase

## Success Criteria

### Functional Requirements
- [ ] Users can register, login, and manage profiles
- [ ] Sessions persist across browser refreshes
- [ ] Default admin and user accounts are created on initialization
- [ ] Admin users can manage other users and roles
- [ ] Role-based access control prevents unauthorized access
- [ ] Admin dashboard provides system overview and analytics
- [ ] Neo4j graph operations work with MERGE semantics
- [ ] Human-in-the-loop escalation functions correctly
- [ ] Progressive context disclosure improves performance
- [ ] All nodes execute with proper LLM integration

### Non-Functional Requirements
- [ ] Database operations complete within 100ms
- [ ] WebSocket connections maintain 99.9% uptime
- [ ] Graph operations scale to 10,000+ nodes
- [ ] User interface responds within 200ms
- [ ] System handles 100+ concurrent users
- [ ] Code coverage exceeds 80%

### Quality Gates
- [ ] All tests pass in CI/CD pipeline
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks met
- [ ] Documentation complete and up-to-date
- [ ] Code review approval from team
- [ ] Production deployment successful

## Next Steps

1. **Immediate Actions**:
   - Set up development database (SQLite)
   - Install required dependencies (SQLAlchemy, neo4j driver, bcrypt)
   - Create database models and migrations
   - Implement database initialization script with default users
   - Begin Phase 1 implementation

2. **Parallel Work**:
   - Start Neo4j driver research and testing
   - Design frontend component architecture
   - Plan WebSocket communication protocol
   - Prepare testing infrastructure

3. **Review & Approval**:
   - Present plan to stakeholders
   - Gather feedback and refine timeline
   - Secure necessary resources
   - Begin implementation

This implementation plan provides a comprehensive roadmap for enhancing the Puntini Agent with production-ready features while maintaining code quality and system reliability.
