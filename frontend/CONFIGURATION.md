# Frontend Configuration System

This document describes the robust configuration system implemented for the frontend application.

## Overview

The frontend uses a centralized configuration system that combines:
- JSON configuration file (`config.json`) as the base configuration
- Environment variables for environment-specific overrides
- Type-safe configuration management with validation

## Configuration Files

### 1. Base Configuration (`config.json`)

The main configuration file containing default settings:

```json
{
  "api": {
    "baseUrl": "http://localhost:8000",
    "timeout": 30000,
    "retryAttempts": 3,
    "retryDelay": 1000
  },
  "websocket": {
    "reconnectAttempts": 5,
    "reconnectDelay": 2000,
    "heartbeatInterval": 30000,
    "connectionTimeout": 10000
  },
  "auth": {
    "tokenStorageKey": "authToken",
    "userStorageKey": "authUser",
    "tokenExpiryBuffer": 300000
  },
  "ui": {
    "theme": "light",
    "language": "en",
    "autoSave": true,
    "autoSaveInterval": 30000
  },
  "features": {
    "enableDebugMode": false,
    "enableAnalytics": false,
    "enableOfflineMode": false,
    "enablePushNotifications": false
  },
  "development": {
    "enableHotReload": true,
    "enableSourceMaps": true,
    "enableConsoleLogging": true
  }
}
```

### 2. Environment Files

- `env.example` - Template for environment variables
- `env.development` - Development environment settings
- `env.production` - Production environment settings

## Environment Variables

The following environment variables can override configuration settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | API base URL | `http://localhost:8000` |
| `VITE_WS_BASE_URL` | WebSocket base URL | `ws://localhost:8000` |
| `VITE_DEBUG_MODE` | Enable debug mode | `false` |
| `VITE_ANALYTICS_ENABLED` | Enable analytics | `false` |
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

### Environment-Specific Configuration

#### Development

```bash
# Copy the example file
cp env.example .env.local

# Edit .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG_MODE=true
```

#### Production

```bash
# Set environment variables
export VITE_API_BASE_URL=https://api.yourdomain.com
export VITE_WS_BASE_URL=wss://api.yourdomain.com
export VITE_DEBUG_MODE=false
export VITE_ANALYTICS_ENABLED=true
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

### 3. Environment Variable Overrides

Environment variables automatically override JSON configuration:

```typescript
// JSON config: "baseUrl": "http://localhost:8000"
// Environment: VITE_API_BASE_URL=https://api.production.com
// Result: baseUrl = "https://api.production.com"
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

1. Check that `config.json` exists and is valid JSON
2. Verify environment variables are prefixed with `VITE_`
3. Check browser console for configuration errors

### Environment Variables Not Working

1. Ensure variables start with `VITE_` prefix
2. Restart the development server after adding new variables
3. Check that `.env` files are in the project root

### WebSocket Connection Issues

1. Verify WebSocket URL configuration
2. Check that the backend supports WebSocket connections
3. Ensure proper CORS configuration on the backend

## Migration from Hardcoded Values

If migrating from hardcoded configuration:

1. Identify all hardcoded URLs and settings
2. Add them to `config.json`
3. Update components to use `config.getApiUrl()` instead of hardcoded strings
4. Add environment variable support for deployment flexibility
5. Test configuration in different environments
