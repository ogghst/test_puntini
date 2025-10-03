# Configuration Summary

This document provides a comprehensive overview of all configuration files and Docker images for the Puntini application.

## Three Docker Images

| Image | Dockerfile | Base Image | Services | Ports |
|-------|-----------|------------|----------|-------|
| **Backend** | `backend/Dockerfile` | `python:3.11-slim` | Backend only | 8026 |
| **Frontend** | `frontend/Dockerfile` | `node:20-alpine` | Frontend only | 8025 |
| **Combined** | `Dockerfile.combined` | Multi-stage | Both | 8025, 8026 |

## Configuration Files

### Backend Configuration

| File | Purpose | Used By | Gitignored |
|------|---------|---------|------------|
| `backend/config.json` | Local development | Local backend | ✅ Yes |
| `backend/config.docker.json` | Docker deployments | All Docker images | ❌ No (template) |
| `backend/config.json.example` | Configuration template | Documentation | ❌ No |

**Backend Config Structure (`backend/config.docker.json`):**
```json
{
  "langfuse": { ... },
  "llm": {
    "default_llm": "deepseek",
    "providers": [ ... ]
  },
  "neo4j": { ... },
  "agent": { ... },
  "server": {
    "host": "0.0.0.0",
    "port": 8026  // Consistent across all Docker setups
  },
  "logging": { ... }
}
```

### Frontend Configuration

| File | Purpose | Used By | Gitignored |
|------|---------|---------|------------|
| `frontend/.env` | Local development | Local dev server | ✅ Yes |
| `frontend/.env.docker` | Docker deployments | All Docker images | ✅ Yes |
| `frontend/.env.example` | Configuration template | Documentation | ❌ No |

**Frontend Config (`frontend/.env.docker`):**
```bash
# API Configuration
VITE_API_BASE_URL=http://backend:8026  # Docker service name
VITE_WS_BASE_URL=ws://backend:8026

# All other settings (auth, UI, features, etc.)
# See frontend/.env.example for complete list
```

## Docker Compose Configurations

### Full Stack (`docker-compose.yml`)

| Service | Image | Internal Port | External Port | Config Source |
|---------|-------|---------------|---------------|---------------|
| backend | `backend:latest` | 8026 | 8026 | `backend/config.docker.json` |
| frontend | `frontend:latest` | 8025 | 8025 | `frontend/.env.docker` |
| neo4j | `neo4j:5-community` | 7474, 7687 | 7474, 7687 | Environment vars |
| ollama | `ollama/ollama:latest` | 11434 | 11434 | Default config |
| langfuse | `langfuse/langfuse:latest` | 3000 | 3001 | Environment vars |

**Access URLs:**
- Frontend: http://localhost:8025
- Backend: http://localhost:8026
- Backend Docs: http://localhost:8026/docs

### Minimal Setup (`docker-compose-minimal.yml`)

| Service | Image | Internal Ports | External Ports | Config Sources |
|---------|-------|----------------|----------------|----------------|
| combined | `combined:latest` | 8025, 8026 | 8025, 8026 | Both config files |

**Access URLs:**
- Frontend: http://localhost:8025
- Backend: http://localhost:8026
- Backend Docs: http://localhost:8026/docs

## Configuration Consistency Matrix

| Setting | Backend Config | Frontend Config | Value |
|---------|---------------|-----------------|-------|
| **Backend Port** | `server.port` | N/A | `8026` (consistent) |
| **Backend Host** | `server.host` | N/A | `0.0.0.0` |
| **Frontend Port** | N/A | Runtime PORT env | `8025` (consistent) |
| **API URL (Docker)** | N/A | `VITE_API_BASE_URL` | `http://backend:8026` |
| **API URL (Local)** | N/A | `VITE_API_BASE_URL` | `http://localhost:8000` |
| **WebSocket URL** | N/A | `VITE_WS_BASE_URL` | `ws://backend:8026` |
| **Default LLM** | `llm.default_llm` | N/A | `deepseek` |
| **Max Retries** | `agent.max_retries` | N/A | `3` |
| **Tracing** | `langfuse.tracing_enabled` | N/A | `false` (Docker) |

## Build Commands

### Individual Images

```bash
# Backend only
docker build -t puntini-backend -f backend/Dockerfile backend/

# Frontend only  
docker build -t puntini-frontend -f frontend/Dockerfile .

# Combined
docker build -t puntini-combined -f Dockerfile.combined .
```

### Using Docker Compose

```bash
# Full stack
docker-compose build

# Minimal combined
docker-compose -f docker-compose-minimal.yml build
```

## Configuration Flow

### Backend Docker Build
```
backend/config.docker.json
    ↓
COPY to /app/config.json
    ↓
Backend reads from /app/config.json at runtime
    ↓
Runs on port 8026
```

### Frontend Docker Build
```
frontend/.env.docker
    ↓
COPY to /app/.env during build
    ↓
Vite embeds variables at build time
    ↓
Static build with embedded config
    ↓
Runs on port 8025
```

### Combined Docker Build
```
Frontend:
  frontend/.env.docker → /app/frontend/.env
  Runs on port 8025
  
Backend:
  backend/config.docker.json → /app/config.json
  Runs on port 8026
  
Both services run in same container
```

## Port Mapping Summary

| Setup | Frontend Host | Frontend Container | Backend Host | Backend Container |
|-------|--------------|-------------------|--------------|-------------------|
| **Full Stack** | 8025 | 8025 | 8026 | 8026 |
| **Minimal** | 8025 | 8025 | 8026 | 8026 |
| **Local Dev** | 5173 (Vite) | N/A | 8000 | N/A |

## Key Principles

1. **Consistency**: Backend always uses port **8026** internally across all Docker setups
2. **Consistency**: Frontend always uses port **8025** internally across all Docker setups
3. **Service Names**: Frontend in Docker uses `http://backend:8026` (Docker service name)
4. **Gitignore**: Actual config files with secrets are gitignored; only templates are committed
5. **Single Source**: Same `config.docker.json` and `.env.docker` used by all Docker images
6. **Build-time Config**: Frontend config is embedded at build time via Vite
7. **Runtime Config**: Backend config is read at runtime from `/app/config.json`

## Verification Checklist

- ✅ All Docker images use consistent port 8026 for backend
- ✅ All Docker images use consistent port 8025 for frontend
- ✅ Frontend `.env.docker` points to `http://backend:8026`
- ✅ Backend `config.docker.json` has `server.port: 8026`
- ✅ Combined image uses same config files as standalone images
- ✅ No hardcoded service URLs (uses Docker service names)
- ✅ Configuration files are properly gitignored
- ✅ Template files (`.example`) are committed to git
- ✅ Port mappings are 1:1 (host:container) for simplicity
