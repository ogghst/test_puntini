# Docker Setup for Puntini Application

This document explains how to build and run the Puntini application using Docker.

## Quick Reference

### Full Stack (All Services)
```bash
docker-compose up -d
# Frontend: http://localhost:8025
# Backend: http://localhost:8026
# Backend Docs: http://localhost:8026/docs
```

### Minimal Combined (Single Container)
```bash
docker-compose -f docker-compose-minimal.yml up -d
# Frontend: http://localhost:8025
# Backend: http://localhost:8026
# Backend Docs: http://localhost:8026/docs
```

## Three Docker Images

The application can be deployed using three different Docker images:

### 1. **Backend Image** (`backend/Dockerfile`)
- Standalone Python backend service
- Based on `python:3.11-slim`
- Uses `backend/config.docker.json` for configuration
- Runs on port 8026

### 2. **Frontend Image** (`frontend/Dockerfile`)
- Standalone React frontend service
- Based on `node:20-alpine`
- Uses `frontend/.env.docker` for configuration
- Runs on port 8025
- Points to backend service via Docker network

### 3. **Combined Image** (`Dockerfile.combined`)
- Single container with both frontend and backend
- Multi-stage build combining both services
- Uses same configuration files as standalone images
- Runs both services in a single container
- Backend: port 8026, Frontend: port 8025

## Prerequisites

- Docker Engine (version 20.10 or higher)
- Docker Compose (v2 or higher)

## Building and Running the Application

### Quick Start

To build and start the complete application stack with all services:

```bash
./docker-build.sh start
```

This will:
1. Pull the latest base images
2. Build the backend and frontend Docker images
3. Start all services in detached mode

### Using Docker Compose Directly

You can also use docker-compose commands directly:

#### Build the images:
```bash
docker-compose build
```

#### Start the services:
```bash
docker-compose up -d
```

#### View logs:
```bash
docker-compose logs -f
```

#### Stop the services:
```bash
docker-compose down
```

## Available Services

### Full Stack (docker-compose.yml)

After starting the full stack, the following services will be available:

- **Frontend**: http://localhost:8025
- **Backend API**: http://localhost:8026
- **Backend API Docs**: http://localhost:8026/docs
- **Neo4j Database**: http://localhost:7474 (browser), bolt://localhost:7687 (driver)
- **Ollama LLM**: http://localhost:11434
- **Langfuse Observability**: http://localhost:3001

### Minimal Setup (docker-compose-minimal.yml)

- **Frontend**: http://localhost:8025
- **Backend API**: http://localhost:8026
- **Backend API Docs**: http://localhost:8026/docs

## Minimal Setup

If you want to run just the backend and frontend without additional services like Neo4j, Ollama, and Langfuse, use the minimal compose file:

### Combined Single-Container Setup

The minimal setup uses a single Docker image that combines both frontend and backend applications:

```bash
docker-compose -f docker-compose-minimal.yml up -d
```

This creates a single container with both services:
- **Frontend**: http://localhost:8025
- **Backend API**: http://localhost:8026
- **Backend API Docs**: http://localhost:8026/docs

Both services run in the same container, sharing the same network namespace.

### Build the Combined Image

To build the combined image:

```bash
docker-compose -f docker-compose-minimal.yml build
```

### Combined Configuration

The combined setup uses:
- `Dockerfile.combined` - Multi-stage build combining frontend and backend
- `backend/config.docker.json` - Backend configuration (port 8026)
- `frontend/.env.docker` - Frontend environment configuration
- `start_combined.sh` - Startup script that runs both services in parallel

The backend is configured with:
- DeepSeek LLM as the default provider
- Tracing disabled for minimal overhead
- Port 8026 for the API server

### Full Stack Setup (Alternative)

If you need all supporting services (Neo4j, Ollama, Langfuse), use the full stack:

```bash
docker-compose up -d
```

This starts separate containers for:
- Backend (port 8026)
- Frontend (port 8025)
- Neo4j, Ollama, Langfuse

## Environment Configuration

### Configuration Files

All Docker setups use the same configuration files:

#### Backend Configuration (`backend/config.docker.json`)
- LLM providers (OpenAI, Anthropic, Ollama, DeepSeek)
- Neo4j database connection settings
- Server settings (host, port, logging)
- Agent settings (retries, checkpointer, tracer)
- Langfuse observability settings

Default settings:
- Server port: **8026** (consistent across all Docker setups)
- Default LLM: DeepSeek
- Tracing: Disabled for production

#### Frontend Configuration (`frontend/.env.docker`)
- API base URL: `http://backend:8026` (uses Docker service name)
- WebSocket URL: `ws://backend:8026`
- Feature flags (debug mode, analytics, etc.)
- UI settings (theme, language, auto-save)
- Authentication storage keys

Both configuration files are:
- Gitignored (not committed to version control)
- Copied during Docker build
- Consistent across all three Docker images

## Build Script Commands

The `docker-build.sh` script provides convenient commands:

- `./docker-build.sh build` - Build Docker images
- `./docker-build.sh up` - Start services in detached mode
- `./docker-build.sh down` - Stop services
- `./docker-build.sh logs` - View logs from all services
- `./docker-build.sh rebuild` - Rebuild images and restart services
- `./docker-build.sh pull` - Pull latest base images
- `./docker-build.sh start` - Pull, build and start all services
- `./docker-build.sh full-rebuild` - Complete rebuild including volumes

## Troubleshooting

### Common Issues

1. **Port already in use**: If you get port binding errors, make sure no other services are using the required ports:
   - Full stack: 8025, 8026, 7474, 7687, 11434, 3001
   - Combined setup: 8025, 8026

2. **Docker build fails**: Make sure you're running the script from the project root directory.

3. **Services failing to start**: Check the logs with `./docker-build.sh logs` or `docker-compose logs -f` to see error messages.

### Reset Everything

To completely reset and start fresh:

```bash
./docker-build.sh full-rebuild
```

This will stop all services, remove volumes, pull fresh base images, and rebuild everything.