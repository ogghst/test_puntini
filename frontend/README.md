# Frontend Configuration System

This document describes the environment-based configuration system for the frontend application.

## Overview

The frontend uses a centralized configuration system that loads all settings exclusively from environment variables. This provides:
- Single source of truth for configuration
- Environment-specific settings without code changes
- Type-safe configuration management with validation
- Docker-friendly deployment

## Configuration Files

### 1. `.env` - Development Configuration

Used for local development. This file is gitignored and should be created from `.env.example`.

### 2. `.env.example` - Configuration Template

Template file stored in version control that documents all available configuration options with sensible defaults.

### 3. `.env.docker` - Docker Configuration

Used when building and running the frontend in Docker containers. This file is gitignored and should be customized for your Docker environment.

## Environment Variables

All configuration is managed through environment variables with the `VITE_` prefix (required by Vite for client-side access):

### API Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | API base URL | `http://localhost:8000` |
| `VITE_API_TIMEOUT` | Request timeout in ms | `30000` |
| `VITE_API_RETRY_ATTEMPTS` | Number of retry attempts | `3` |
| `VITE_API_RETRY_DELAY` | Delay between retries in ms | `1000` |

### WebSocket Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_WS_BASE_URL` | WebSocket base URL | `ws://localhost:8000` |
| `VITE_WS_RECONNECT_ATTEMPTS` | Max reconnection attempts | `5` |
| `VITE_WS_RECONNECT_DELAY` | Delay between reconnections in ms | `2000` |
| `VITE_WS_HEARTBEAT_INTERVAL` | Heartbeat interval in ms | `30000` |
| `VITE_WS_CONNECTION_TIMEOUT` | Connection timeout in ms | `10000` |

### Authentication Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_AUTH_TOKEN_KEY` | LocalStorage key for token | `puntini_access_token` |
| `VITE_AUTH_USER_KEY` | LocalStorage key for user data | `puntini_user_data` |
| `VITE_AUTH_TOKEN_EXPIRY_BUFFER` | Token expiry buffer in ms | `300000` |

### UI Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_UI_THEME` | UI theme (light/dark/auto) | `auto` |
| `VITE_UI_LANGUAGE` | UI language | `en` |
| `VITE_UI_AUTO_SAVE` | Enable auto-save | `true` |
| `VITE_UI_AUTO_SAVE_INTERVAL` | Auto-save interval in ms | `30000` |

### Feature Flags
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_DEBUG_MODE` | Enable debug mode | `false` |
| `VITE_ANALYTICS_ENABLED` | Enable analytics | `false` |
| `VITE_OFFLINE_MODE` | Enable offline mode | `false` |
| `VITE_PUSH_NOTIFICATIONS` | Enable push notifications | `false` |

### Development Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_DEV_HOT_RELOAD` | Enable hot reload | `true` |
| `VITE_DEV_SOURCE_MAPS` | Enable source maps | `true` |
| `VITE_DEV_CONSOLE_LOGGING` | Enable console logging | Matches NODE_ENV |
| `NODE_ENV` | Environment mode | `development` |

## Usage

### Basic Usage

```typescript
import { config, getApiBaseUrl, getWebSocketUrl } from '@/utils/config';

// Get API base URL
const apiUrl = getApiBaseUrl();

// Get WebSocket URL
const wsUrl = getWebSocketUrl();

// Get full API endpoint
const loginUrl = config.getApiUrl('/login');

// Get WebSocket endpoint
const chatWsUrl = config.getWebSocketEndpoint('/ws/chat');
```

### Configuration Access

```typescript
import { config } from '@/utils/config';

// Get specific configuration sections
const apiConfig = config.getApiConfig();
const wsConfig = config.getWebSocketConfig();
const authConfig = config.getAuthConfig();

// Check feature flags
if (config.isDebugMode()) {
  console.log('Debug mode enabled');
}

if (config.isAnalyticsEnabled()) {
  // Initialize analytics
}
```

### Setting Up Configuration

#### Local Development

```bash
# 1. Copy the example file
cd frontend
cp .env.example .env

# 2. Edit .env with your local settings
# The defaults are already configured for local development
# Only change what you need
```

#### Docker Deployment

```bash
# 1. Copy the example file
cd frontend
cp .env.example .env.docker

# 2. Edit .env.docker for your Docker environment
# Update URLs to match your Docker network configuration
VITE_API_BASE_URL=http://backend:8000
VITE_WS_BASE_URL=ws://backend:8000
NODE_ENV=production
```

#### Production Deployment

For production deployments without Docker, set environment variables directly:

```bash
# Set environment variables
export VITE_API_BASE_URL=https://api.yourdomain.com
export VITE_WS_BASE_URL=wss://api.yourdomain.com
export VITE_DEBUG_MODE=false
export VITE_ANALYTICS_ENABLED=true
export NODE_ENV=production

# Then build
npm run build
```

## Configuration Features

### 1. Type Safety

All configuration options are typed with TypeScript interfaces:

```typescript
interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}
```

### 2. Validation

Configuration is validated on load:

- URLs must start with `http://` or `https://`
- Timeout values must be positive
- Reconnect attempts must be non-negative

### 3. Default Values

All configuration options have sensible defaults defined in code. If an environment variable is not set, the application uses these defaults:

```typescript
// Example: If VITE_API_BASE_URL is not set
// Result: baseUrl = "http://localhost:8000"
```

### 4. Debug Logging

When debug mode is enabled, configuration is logged to console:

```
🔧 Application Configuration
  API Base URL: http://localhost:8000
  WebSocket URL: ws://localhost:8000
  Debug Mode: true
  Analytics: false
  Development: true
```

## Integration with Components

### Session Management

The session management system automatically uses configuration:

```typescript
// session.ts automatically uses config
const wsUrl = getWebSocketEndpoint('/ws/chat');
const apiUrl = getApiUrl('/login');
```

### Authentication

Authentication context uses configuration for storage keys:

```typescript
// AuthContext automatically uses config
const authConfig = config.getAuthConfig();
localStorage.setItem(authConfig.tokenStorageKey, token);
```

## Vite Integration

The Vite configuration includes:

- Environment variable loading
- Proxy configuration for development
- Build-time environment variable injection

```typescript
// vite.config.ts
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    envPrefix: 'VITE_',
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  };
});
```

## Best Practices

### 1. Configuration Management

- **Never commit** `.env` or `.env.docker` files to version control
- Always update `.env.example` when adding new configuration options
- Document all environment variables in this README
- Update TypeScript interfaces in `app/utils/config.ts` when adding new options

### 2. Environment Files

- Use `.env` for local development
- Use `.env.docker` for Docker builds
- Keep `.env.example` up-to-date as the source of truth for available options
- Use explicit values in production rather than `.env` files

### 3. Security

- Never commit sensitive values (API keys, secrets) to version control
- Use environment variables for sensitive production configuration
- Validate all configuration values at startup

### 4. Debug Mode

- Enable debug mode only in development (`VITE_DEBUG_MODE=true`)
- Use debug mode for additional logging and diagnostics
- Always disable debug mode in production builds

### 5. URL Configuration

- Use HTTPS/WSS in production environments
- Configure proper CORS settings on the backend
- Use Docker service names (e.g., `http://backend:8000`) in `.env.docker`
- Use localhost URLs in `.env` for local development

## Troubleshooting

### Configuration Not Loading

1. Verify environment variables are prefixed with `VITE_`
2. Check browser console for configuration validation errors
3. Ensure `.env` file exists in the frontend directory
4. Restart the development server after changing `.env` files

### Environment Variables Not Working

1. Ensure all variables start with `VITE_` prefix (Vite requirement)
2. **Restart the development server** after adding/changing variables
3. Check that `.env` file is in the `frontend/` directory
4. Verify the variable name matches exactly (case-sensitive)
5. Check for syntax errors in `.env` file (no spaces around `=`)

### Docker Build Issues

1. Ensure `.env.docker` exists in the frontend directory
2. Verify Docker network service names are correct
3. Check Dockerfile copies `.env.docker` correctly
4. Rebuild the Docker image after changing `.env.docker`

### WebSocket Connection Issues

1. Verify `VITE_WS_BASE_URL` is set correctly
2. Use `ws://` for HTTP backends, `wss://` for HTTPS
3. Check that the backend supports WebSocket connections
4. Ensure proper CORS configuration on the backend

## Adding New Configuration Options

To add a new configuration option:

1. **Update TypeScript interfaces** in `app/utils/config.ts`:
   ```typescript
   export interface ApiConfig {
     baseUrl: string;
     newOption: string; // Add your new option
   }
   ```

2. **Add to ConfigManager.loadConfiguration()**:
   ```typescript
   api: {
     baseUrl: this.getEnv('VITE_API_BASE_URL', 'http://localhost:8000'),
     newOption: this.getEnv('VITE_API_NEW_OPTION', 'default-value'),
   }
   ```

3. **Update `.env.example`**:
   ```bash
   # New Option Description
   VITE_API_NEW_OPTION=default-value
   ```

4. **Update this documentation** with the new variable in the tables above

5. **Update `.env` and `.env.docker`** with appropriate values
