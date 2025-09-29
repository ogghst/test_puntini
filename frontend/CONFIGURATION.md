# Frontend Configuration System

This document describes the environment variable-based configuration system implemented for the frontend application.

## Overview

The frontend uses a centralized configuration system that loads settings from environment variables with fallback defaults. This approach provides maximum flexibility for different deployment environments without requiring code changes.

## Configuration Files

### 1. Environment Files

The configuration system uses environment files for different deployment scenarios:

- `.env.example` - Template for environment variables with documentation
- `.env.development` - Development environment settings
- `.env.production` - Production environment settings
- `.env.local` - Local overrides (not committed to version control)

## Environment Variables

The following environment variables control all application settings:

### API Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | API base URL | `http://localhost:8009` |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `30000` |
| `VITE_API_RETRY_ATTEMPTS` | Number of retry attempts | `3` |
| `VITE_API_RETRY_DELAY` | Delay between retries (ms) | `1000` |

### WebSocket Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_WS_BASE_URL` | WebSocket base URL | Auto-derived from API URL |
| `VITE_WS_RECONNECT_ATTEMPTS` | Reconnection attempts | `5` |
| `VITE_WS_RECONNECT_DELAY` | Delay between reconnections (ms) | `2000` |
| `VITE_WS_HEARTBEAT_INTERVAL` | Heartbeat interval (ms) | `30000` |
| `VITE_WS_CONNECTION_TIMEOUT` | Connection timeout (ms) | `10000` |

### Authentication Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_AUTH_TOKEN_STORAGE_KEY` | LocalStorage key for auth token | `authToken` |
| `VITE_AUTH_USER_STORAGE_KEY` | LocalStorage key for user data | `authUser` |
| `VITE_AUTH_TOKEN_EXPIRY_BUFFER` | Token expiry buffer (ms) | `300000` |

### UI Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_UI_THEME` | Theme (`light`, `dark`, `auto`) | `light` |
| `VITE_UI_LANGUAGE` | Language code | `en` |
| `VITE_UI_AUTO_SAVE` | Enable auto-save | `true` |
| `VITE_UI_AUTO_SAVE_INTERVAL` | Auto-save interval (ms) | `30000` |

### Feature Flags
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_FEATURES_DEBUG_MODE` | Enable debug mode | `false` |
| `VITE_FEATURES_ANALYTICS_ENABLED` | Enable analytics | `false` |
| `VITE_FEATURES_OFFLINE_MODE` | Enable offline mode | `false` |
| `VITE_FEATURES_PUSH_NOTIFICATIONS` | Enable push notifications | `false` |

### Development Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_DEV_HOT_RELOAD` | Enable hot reload | `true` |
| `VITE_DEV_SOURCE_MAPS` | Enable source maps | `true` |
| `VITE_DEV_CONSOLE_LOGGING` | Enable console logging | `false` |

### Application Environment
| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Node environment | `development` |
| `VITE_APP_ENV` | Application environment | `development` |

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

### Environment-Specific Configuration

#### Development

```bash
# Copy the example file
cp .env.example .env.local

# Edit .env.local
VITE_API_BASE_URL=http://localhost:8009
VITE_FEATURES_DEBUG_MODE=true
VITE_DEV_CONSOLE_LOGGING=true
```

#### Production

```bash
# Set environment variables
export VITE_API_BASE_URL=https://api.yourdomain.com
export VITE_WS_BASE_URL=wss://api.yourdomain.com
export VITE_FEATURES_DEBUG_MODE=false
export VITE_FEATURES_ANALYTICS_ENABLED=true
export VITE_DEV_CONSOLE_LOGGING=false
```

#### Docker

```bash
# Run container with environment variables
docker run -d --name puntini-frontend \
  -p 8026:8026 \
  -e VITE_API_BASE_URL=http://backend:8025 \
  -e VITE_FEATURES_DEBUG_MODE=false \
  -e VITE_FEATURES_ANALYTICS_ENABLED=true \
  puntini-frontend:latest
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

### 3. Environment Variable Priority

Environment variables take precedence over defaults:

```typescript
// Default: baseUrl = "http://localhost:8009"
// Environment: VITE_API_BASE_URL=https://api.production.com
// Result: baseUrl = "https://api.production.com"
```

### 4. Debug Logging

When debug mode is enabled, configuration is logged to console:

```
🔧 Application Configuration
  API Base URL: http://localhost:8009
  WebSocket URL: ws://localhost:8009
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

### 1. Configuration Updates

- Always update the JSON configuration file for new settings
- Add corresponding environment variables for overrides
- Update TypeScript interfaces when adding new configuration options

### 2. Environment Management

- Use environment files for different deployment environments
- Never commit sensitive configuration to version control
- Use environment variables for production secrets

### 3. Debug Mode

- Enable debug mode only in development
- Use debug mode for additional logging and diagnostics
- Disable debug mode in production builds

### 4. URL Configuration

- Use HTTPS/WSS in production
- Configure proper CORS settings for API endpoints
- Use proxy configuration in development for seamless local development

## Troubleshooting

### Configuration Not Loading

1. Check that environment variables are prefixed with `VITE_`
2. Verify environment variables are set correctly
3. Check browser console for configuration errors
4. Ensure `.env` files are in the project root

### Environment Variables Not Working

1. Ensure variables start with `VITE_` prefix
2. Restart the development server after adding new variables
3. Check that `.env` files are in the project root
4. Verify variable names match exactly (case-sensitive)

### WebSocket Connection Issues

1. Verify WebSocket URL configuration
2. Check that the backend supports WebSocket connections
3. Ensure proper CORS configuration on the backend
4. Verify `VITE_WS_BASE_URL` is set correctly

### Docker Configuration Issues

1. Check that environment variables are passed to the container
2. Verify the Dockerfile includes all necessary ENV declarations
3. Ensure environment variables are set before building the image
4. Check container logs for configuration errors

## Migration from JSON Configuration

If migrating from JSON-based configuration:

1. Identify all configuration values from `config.json`
2. Create corresponding environment variables with `VITE_` prefix
3. Update components to use `config.getApiUrl()` instead of hardcoded strings
4. Set up environment files for different deployment environments
5. Test configuration in different environments
6. Remove the old `config.json` file
