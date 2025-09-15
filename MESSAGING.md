# Architecture Document for AI Assistant Application

## Overview

This document outlines the architecture for building an AI Assistant application featuring a chat interface and a structured data visualization area (e.g., an object tree) that is dynamically modified by an LLM based on chat prompts. The system supports multi-user sessions, with authentication handled via REST APIs and real-time interactions via WebSockets.

### Key Requirements
- **Backend**: FastAPI (latest version: 0.115.0 as of September 2025) for REST endpoints (authentication and session setup) and WebSocket endpoints (chat and tree updates).
- **Frontend**: React (latest: 18.3.1), with React Query (latest: 5.51.23) for managing REST data fetching and caching, React Router (latest: 6.26.2) for routing, and shadcn/ui (latest: 0.9.0) for UI components. Assume Vite and Tailwind CSS are pre-configured.
- **Session Management**: Multi-user support without Redis; use in-memory storage (e.g., Python dictionaries) for tracking active WebSocket connections and session states. This is suitable for single-instance deployments but limits horizontal scaling—consider future migration to external stores if needed.
- **WebSocket Protocol**: A scalable, flexible JSON-based messaging protocol for real-time communication, supporting types like user prompts, assistant responses, tree updates, reasoning, debug, and errors.
- **LLM Integration**: Assume an external LLM (e.g., via API like Grok or OpenAI) is integrated in the backend for processing prompts and generating tree modifications.
- **Assumptions**: Backend and frontend are already set up with basic configurations (e.g., CORS, environment variables). Focus on architectural details and protocol; minimal code snippets provided only for authentication and chat.

### High-Level Architecture
- **Backend Structure**:
  - REST API: Handles authentication, token generation, and initial session setup.
  - WebSocket Server: Manages persistent connections for chat and tree interactions per user session.
  - In-Memory Storage: Dictionaries to map user IDs to WebSocket connections and session data (e.g., current tree state).
  - LLM Processor: A module that takes prompts, queries the LLM, and generates responses/updates.

- **Frontend Structure**:
  - Routes: Login page, main dashboard with chat and tree view.
  - State Management: React Query for REST queries (e.g., login), local state (useState/useReducer) for WebSocket data.
  - UI: Split layout (chat on left, tree on right) using shadcn components like Card, Input, Button, and a tree visualization library (e.g., react-d3-tree or react-arborist).

- **Data Flow**:
  1. User authenticates via REST (/login), receives JWT token.
  2. Frontend establishes WebSocket connection with token.
  3. Backend validates token, creates/loads session in memory.
  4. User sends prompts via WebSocket; backend processes with LLM and pushes responses/updates.
  5. Multi-user: Each connection is isolated by user ID; no shared state across users unless explicitly designed.

- **Scalability Considerations**:
  - In-memory sessions limit to single server; for multi-server, future-proof by designing protocol to be stateless where possible (e.g., include session_id in messages).
  - WebSocket: Use heartbeat messages to detect disconnections and clean up sessions.
  - Protocol: JSON with extensible "type" field allows adding new message types without breaking compatibility.

## Backend Architecture

### FastAPI Setup
- Use FastAPI's built-in support for OAuth2/JWT for authentication.
- WebSocket endpoints: One for chat (/ws/chat) and one for tree updates (/ws/tree), or a unified /ws/session for flexibility.
- Dependencies: Install via pip: `fastapi[standard]`, `python-jose[cryptography]`, `passlib[bcrypt]` for secure passwords.
- In-Memory Session Management:
  - `connected_users: dict[str, WebSocket]` – Maps user_id to active WebSocket.
  - `sessions: dict[str, dict]` – Maps user_id to session data (e.g., {"tree": json_tree, "chat_history": []}).
  - Cleanup: On disconnect, remove from dicts; use periodic tasks (e.g., via FastAPI's lifespan) for expired sessions.

### Authentication (REST)
Authentication generates a JWT token used for WebSocket handshake. Use query param for token in WebSocket URL (e.g., ws://backend-url/ws/chat?token=ey...).

Minimal Snippet (FastAPI):
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI()
SECRET_KEY = "your-secret-key"  # Use env var in production
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class User(BaseModel):
    username: str

fake_users_db = {}  # Replace with real DB

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate credentials (e.g., from DB)
    if form_data.username not in fake_users_db:
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": form_data.username})
    return {"access_token": token}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

### WebSocket Handling
- Validate token on connect.
- Route messages based on "type" field.
- For multi-user: Ensure messages are sent only to the correct connection via user_id lookup.

Minimal Snippet for Chat WebSocket:
```python
from fastapi import WebSocket, WebSocketDisconnect

connected_users = {}  # user_id: WebSocket

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str):
    user_id = await get_current_user(token)  # Reuse dependency
    if not user_id:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    connected_users[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            # Process based on type (e.g., user_prompt -> LLM -> send response)
            if data["type"] == "user_prompt":
                response = llm_process(data["data"]["prompt"])  # Integrate LLM
                await websocket.send_json({"type": "assistant_response", "data": {"text": response}})
    except WebSocketDisconnect:
        del connected_users[user_id]
```

### LLM Integration
- A separate module (e.g., llm.py) that calls an external API.
- For tree modifications: Parse LLM output to generate JSON deltas (e.g., {"action": "add", "node": {...}}).
- Store updated tree in sessions[user_id]["tree"].

## Frontend Architecture

### React Setup
- Use React Router for routes: /login, /dashboard (with chat and tree).
- React Query: For login mutation and initial data fetch (e.g., load initial tree via REST if needed).
- shadcn/ui: Components like Tabs for switching views, Textarea for chat input, TreeView for object tree.
- WebSocket: Native WebSocket API with hooks; handle reconnects with exponential backoff.
- Layout: Responsive grid (Tailwind): Chat column (40%), Tree column (60%).

### State Management
- Global: Use Context for auth token and user_id.
- Local: useReducer for chat history and tree state.
- React Query: Mutations for login; queries for any REST data.

### WebSocket Integration
- Hook: Custom useWebSocket that connects with token, listens for messages, and dispatches to reducers based on type.

## WebSocket Protocol

### Message Structure
All messages are JSON objects with a scalable structure:
- **type** (string, required): Defines the message purpose (e.g., "user_prompt", "assistant_response").
- **data** (object, required): Payload specific to the type.
- **session_id** (string, optional): Unique session identifier (generated on connect; allows resuming across disconnects).
- **timestamp** (string, optional): ISO timestamp for logging.
- **error** (object, optional): If present, { "code": int, "message": string } for errors.

This structure is flexible: New types can be added without breaking existing clients. Backend validates type and data schema.

### Protocol Flow
1. Client connects: Sends initial {"type": "init_session", "data": {}} after connect.
2. Server responds: {"type": "session_ready", "data": {"session_id": "uuid", "initial_tree": {...}}}.
3. Client sends prompts/updates.
4. Server pushes responses, updates, reasoning, etc.
5. Heartbeat: Every 30s, client sends {"type": "ping"}; server responds {"type": "pong"}.

### Examples of Messages
- **User Chat Prompt**: Sent from client to server.
  ```json
  {
    "type": "user_prompt",
    "data": {
      "prompt": "Add a new node with value 'Task 1' under root"
    },
    "session_id": "abc-123"
  }
  ```

- **Assistant Response**: Pushed from server to client (e.g., LLM output).
  ```json
  {
    "type": "assistant_response",
    "data": {
      "text": "Node 'Task 1' added successfully under root.",
      "chunk": true  // For streaming; false for complete
    },
    "session_id": "abc-123"
  }
  ```

- **Reasoning**: Pushed during LLM processing (e.g., step-by-step thoughts).
  ```json
  {
    "type": "reasoning",
    "data": {
      "steps": [
        "Parsing prompt: Identify action 'add' and target 'root'.",
        "Querying LLM for validation.",
        "Generating tree delta."
      ]
    },
    "session_id": "abc-123"
  }
  ```

- **Debug**: For development/logging (e.g., errors or info).
  ```json
  {
    "type": "debug",
    "data": {
      "message": "LLM API latency: 250ms",
      "level": "info"
    },
    "session_id": "abc-123"
  }
  ```

- **Tree Update**: Pushed after LLM modifies the tree (use deltas for efficiency).
  ```json
  {
    "type": "tree_update",
    "data": {
      "delta": {
        "action": "add",
        "path": "/root/children",
        "node": {
          "id": "node-1",
          "value": "Task 1",
          "children": []
        }
      }
    },
    "session_id": "abc-123"
  }
  ```

- **Error**: Generic error response.
  ```json
  {
    "type": "error",
    "data": {},
    "error": {
      "code": 400,
      "message": "Invalid prompt format"
    },
    "session_id": "abc-123"
  }
  ```

- **Other Typical Examples**:
  - **Init Session**: Client: {"type": "init_session", "data": {}}; Server: {"type": "session_ready", "data": {"initial_tree": {...}}}.
  - **Logout/Close**: Client: {"type": "close_session", "data": {}}; Server closes connection and cleans session.
  - **History Sync**: Server: {"type": "chat_history", "data": {"messages": [{"role": "user", "content": "..."}, ...]}} for loading past chats.

## Session Management (Multi-User)

- **Creation**: On successful WebSocket connect and init_session, generate session_id (UUID) and store in sessions[user_id] = {"session_id": "...", "tree": {}, "history": []}.
- **Isolation**: All operations keyed by user_id from JWT. No cross-user data leakage.
- **Persistence**: In-memory only; on disconnect, persist to DB if needed (e.g., via SQLAlchemy integration).
- **Cleanup**: On WebSocketDisconnect, remove from connected_users; use a timer to expire inactive sessions (e.g., 1 hour).
- **Multi-Session per User**: Support multiple tabs by associating session_id per connection; merge states if conflicting.

## Implementation Guidelines for Development Team

- **Backend**:
  - Use Pydantic for message validation (e.g., models for each type).
  - Integrate LLM asynchronously (e.g., with httpx for API calls).
  - Logging: Use FastAPI's logger for all WebSocket events.
  - Testing: Use pytest for REST; websocket-client for WS.

- **Frontend**:
  - Auth Context: Provider to store token after login.
  - WebSocket Hook: Handle onmessage by dispatching to reducers (e.g., update chat with assistant_response, apply delta with tree_update).
  - UI: Use shadcn's ScrollArea for chat, Tree for object view.
  - Error Handling: Display toasts (shadcn Toast) for errors; auto-reconnect WebSocket.

- **Security**:
  - Validate all inputs (e.g., prevent injection in prompts).
  - Rate limiting: On WebSocket messages to prevent abuse.
  - HTTPS: Enforce for production.

- **Deployment**:
  - Run FastAPI with uvicorn/gunicorn.
  - Frontend: Build with Vite, serve via Nginx (proxy WebSockets).

This architecture provides a solid foundation; iterate based on performance metrics.
