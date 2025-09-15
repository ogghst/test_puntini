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
- `error`: Error messages
- `ping`/`pong`: Heartbeat messages

## Usage

### Starting the API Server

The server can be started using multiple methods, all of which use the centralized configuration system:

#### Method 1: Direct execution (recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment
source .venv/bin/activate

# Start the server directly
python puntini/api/app.py
```

#### Method 2: Using the example script
```bash
# Start using the example script
python run_server.py
```

#### Method 3: Traditional uvicorn (manual configuration)
```bash
# Start with uvicorn (configuration from config.json)
uvicorn puntini.api.app:app --host 127.0.0.1 --port 8000 --reload
```

#### Method 4: Programmatic startup
```python
from puntini.utils.settings import Settings
from puntini.api.app import run_server

settings = Settings()
run_server(settings)
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

The API uses the centralized Puntini settings system for configuration. All settings are managed through `config.json` and the `Settings` class.

### Server Configuration

Server settings are configured in the `server` section of `config.json`:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "reload": true,
    "workers": 1,
    "access_log": true,
    "log_level": "info",
    "root_path": "",
    "openapi_url": "/openapi.json",
    "docs_url": "/docs",
    "redoc_url": "/redoc"
  }
}
```

### Authentication Configuration

Authentication settings include:

- `SECRET_KEY`: JWT secret key (set via environment variable)
- Session timeout: 1 hour (configurable)
- CORS: Configured for development (adjust for production)

### LLM Configuration

LLM providers are configured in the `llm` section:

```json
{
  "llm": {
    "default_llm": "ollama-gemma3:4b",
    "providers": [
      {
        "name": "ollama-gemma3:4b",
        "type": "ollama",
        "model_name": "gemma3:4b",
        "temperature": 0.0,
        "enabled": true
      }
    ]
  }
}
```

## Server Configuration Features

The new server configuration system provides several benefits:

### Centralized Configuration
- All server settings managed through `config.json`
- Type-safe configuration with Pydantic dataclasses
- Environment-specific configurations supported

### Flexible Startup Options
- Multiple ways to start the server (direct, script, programmatic)
- Automatic configuration loading from settings
- Development-friendly defaults (auto-reload enabled)

### Production Ready
- Support for reverse proxy setups with `root_path`
- Configurable worker processes
- Customizable API documentation URLs
- Access logging configuration

### Development Features
- Auto-reload on code changes
- Interactive API documentation at `/docs`
- ReDoc documentation at `/redoc`
- OpenAPI schema at `/openapi.json`

## Development

### Running Tests

```bash
# Run API tests
pytest puntini/api/tests/
```

### Configuration Testing

```bash
# Test configuration loading
python -c "from puntini.utils.settings import Settings; s = Settings(); print(f'Server: {s.server_host}:{s.server_port}')"

# Test server creation
python -c "from puntini.api.app import create_app; app = create_app(); print(f'App: {app.title}')"
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

### Configuration
- Update `config.json` for production settings:
  - Set `reload: false`
  - Configure appropriate `workers` count
  - Set `host: "0.0.0.0"` for external access
  - Use `root_path` for reverse proxy setups
- Use environment variables for secrets (API keys, database credentials)
- Configure proper CORS settings in the application

### Deployment
- Replace in-memory session storage with Redis or database
- Use the `run_server.py` script for production deployment
- Configure reverse proxy (nginx, Apache) with proper `root_path`
- Implement rate limiting
- Add monitoring and logging
- Use HTTPS for WebSocket connections
- Set up proper logging with the configurable logging system

### Security
- Configure JWT secrets via environment variables
- Use secure session management
- Implement proper authentication flows
- Configure CORS for production domains only
