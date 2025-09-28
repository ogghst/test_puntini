# Docker Compose Configuration

This directory contains Docker Compose configurations for running the Puntini application with environment variable-based configuration.

## Files Overview

- `docker-compose.yml` - Complete stack (frontend + backend)
- `.env.example` - Environment variables template
- `.env.development` - Development environment variables
- `.env.production` - Production environment variables

## Quick Start

### 1. Complete Stack (Frontend + Backend)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Start the complete stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the stack
docker-compose down
```

### 2. Frontend Only

```bash
# Copy environment template
cp .env.example .env

# Start only the frontend
docker-compose -f docker-compose.frontend.yml up -d

# View logs
docker-compose -f docker-compose.frontend.yml logs -f

# Stop
docker-compose -f docker-compose.frontend.yml down
```

## Environment Variables

All frontend configuration is controlled through environment variables. The Docker Compose files use the following pattern:

```yaml
environment:
  - VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8025}
```

This means:
- Use the value from `.env` file if set
- Fall back to the default value (`http://localhost:8025`) if not set

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8025` |
| `VITE_WS_BASE_URL` | WebSocket URL | `ws://localhost:8025` |
| `VITE_FEATURES_DEBUG_MODE` | Enable debug mode | `false` |
| `VITE_FEATURES_ANALYTICS_ENABLED` | Enable analytics | `false` |

## Environment-Specific Configurations

### Development

```bash
# Use development environment
cp .env.development .env
docker-compose up -d
```

Development settings:
- Debug mode enabled
- Console logging enabled
- Hot reload enabled
- Source maps enabled

### Production

```bash
# Use production environment
cp .env.production .env
# Edit .env with your production URLs
docker-compose up -d
```

Production settings:
- Debug mode disabled
- Analytics enabled
- Push notifications enabled
- Optimized for performance

## Custom Configuration

### Override Specific Variables

```bash
# Override specific variables without editing .env
VITE_API_BASE_URL=https://api.example.com docker-compose up -d
```

### Custom Environment File

```bash
# Use a custom environment file
docker-compose --env-file .env.custom up -d
```

## Service Configuration

### Frontend Service

- **Port**: 8026
- **Health Check**: HTTP check on port 8026
- **Dependencies**: Waits for backend to be healthy
- **Restart Policy**: `unless-stopped`

### Backend Service

- **Port**: 8025
- **Health Check**: HTTP check on `/docs` endpoint
- **Restart Policy**: `unless-stopped`

## Networking

Both services are connected via a custom bridge network (`puntini-network`) allowing them to communicate using service names:

- Frontend can reach backend at `http://puntini-backend:8025`
- Backend can reach frontend at `http://puntini-frontend:8026`

## Health Checks

Both services include health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8026"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   netstat -tulpn | grep :8025
   netstat -tulpn | grep :8026
   ```

2. **Environment Variables Not Loading**
   ```bash
   # Check environment variables
   docker-compose config
   ```

3. **Services Not Starting**
   ```bash
   # Check logs
   docker-compose logs puntini-frontend
   docker-compose logs puntini-backend
   ```

4. **Health Check Failures**
   ```bash
   # Check health status
   docker-compose ps
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Add to .env
VITE_FEATURES_DEBUG_MODE=true
VITE_DEV_CONSOLE_LOGGING=true

# Restart services
docker-compose restart puntini-frontend
```

## Scaling

### Scale Frontend Service

```bash
# Scale frontend to 3 instances
docker-compose up -d --scale puntini-frontend=3
```

### Load Balancer

For production deployments, consider adding a load balancer:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - puntini-frontend
```

## Monitoring

### View Service Status

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats
```

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs puntini-frontend
docker-compose logs puntini-backend

# Follow logs in real-time
docker-compose logs -f
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files with sensitive data
2. **Network**: Services communicate over internal network
3. **Ports**: Only necessary ports are exposed
4. **Health Checks**: Regular health monitoring

## Production Deployment

For production deployment:

1. Copy `.env.production` to `.env`
2. Update URLs to production endpoints
3. Set `NODE_ENV=production`
4. Disable debug features
5. Enable analytics and monitoring
6. Use HTTPS/WSS URLs
7. Set up proper logging and monitoring

```bash
# Production deployment
cp .env.production .env
# Edit .env with production URLs
docker-compose up -d
```
