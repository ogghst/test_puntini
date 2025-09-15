# Puntini Agent API

This module provides the FastAPI-based REST and WebSocket API for the Puntini Agent system, implementing the messaging features described in MESSAGING.md.

## Features

- **REST API**: Authentication endpoints for user login/registration
- **WebSocket API**: Real-time communication with the Puntini Agent
- **Multi-user Support**: Session management with in-memory storage
- **JWT Authentication**: Secure token-based authentication
- **LangGraph Integration**: Streaming agent execution with real-time updates
- **Message Protocol**: Structured JSON messaging with multiple message types

## Architecture

### Components

- **`app.py`**: Main FastAPI application factory
- **`auth.py`**: JWT-based authentication management
- **`session.py`**: Multi-user session management
- **`websocket.py`**: WebSocket connection and message handling
- **`models.py`**: Message type definitions and parsing

### Message Types

The API supports the following message types as defined in MESSAGING.md:

- `init_session`: Initialize a new session
- `session_ready`: Session is ready with initial state
- `user_prompt`: User chat prompt
- `assistant_response`: Agent response
- `reasoning`: Step-by-step reasoning process
- `debug`: Debug information
- `tree_update`: Tree structure updates
- `error`: Error messages
- `ping`/`pong`: Heartbeat messages

## Usage

### Starting the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn puntini.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Authentication

1. **Register a user**:
   ```bash
   curl -X POST "http://localhost:8000/register" \
        -H "Content-Type: application/json" \
        -d '{"username": "testuser", "password": "testpass"}'
   ```

2. **Login to get token**:
   ```bash
   curl -X POST "http://localhost:8000/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "testuser", "password": "testpass"}'
   ```

### WebSocket Connection

Connect to the WebSocket endpoint with the JWT token:

```javascript
const token = "your-jwt-token";
const ws = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`);

ws.onopen = () => {
    console.log("Connected to Puntini Agent");
    
    // Initialize session
    ws.send(JSON.stringify({
        type: "init_session",
        data: {}
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log("Received:", message);
    
    // Handle different message types
    switch (message.type) {
        case "session_ready":
            console.log("Session ready:", message.data);
            break;
        case "assistant_response":
            console.log("Agent response:", message.data.text);
            break;
        case "reasoning":
            console.log("Reasoning steps:", message.data.steps);
            break;
        case "tree_update":
            console.log("Tree updated:", message.data.delta);
            break;
    }
};

// Send user prompt
ws.send(JSON.stringify({
    type: "user_prompt",
    data: {
        prompt: "Create a project management graph with tasks and dependencies"
    }
}));
```

## Configuration

The API uses the Puntini settings system for configuration. Key settings include:

- `SECRET_KEY`: JWT secret key (set via environment variable)
- Session timeout: 1 hour (configurable)
- CORS: Configured for development (adjust for production)

## Development

### Running Tests

```bash
# Run API tests
pytest puntini/api/tests/
```

### Adding New Message Types

1. Add the message type to `MessageType` enum in `models.py`
2. Create a corresponding message class
3. Add parsing logic to `parse_message()` function
4. Add handling logic to `WebSocketManager._process_message()`

### Extending the Agent Integration

The WebSocket manager integrates with the LangGraph agent through streaming. To extend this:

1. Modify `_process_with_agent()` to customize agent execution
2. Add new chunk handlers in `_handle_agent_chunk()`
3. Implement custom message types for agent-specific data

## Production Considerations

- Replace in-memory session storage with Redis or database
- Configure proper CORS settings
- Use environment variables for secrets
- Implement rate limiting
- Add monitoring and logging
- Use HTTPS for WebSocket connections
