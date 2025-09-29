# Docker Setup for Puntini Application

This document explains how to build and run the Puntini application using Docker.

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

After starting the application, the following services will be available:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Backend API Docs**: http://localhost:8000/docs
- **Neo4j Database**: http://localhost:7474 (browser), bolt://localhost:7687 (driver)
- **Ollama LLM**: http://localhost:11434
- **Langfuse Observability**: http://localhost:3001

## Minimal Setup

If you want to run just the backend and frontend without additional services like Neo4j, Ollama, and Langfuse, use the minimal compose file:

```bash
docker-compose -f docker-compose-minimal.yml up -d
```

## Environment Configuration

The backend configuration is controlled by the `backend/config.json.docker` file. You can modify this file to adjust settings like LLM providers, database connections, etc.

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

1. **Port already in use**: If you get port binding errors, make sure no other services are using the required ports (3000, 8000, 7474, 7687, 11434, 3001).

2. **Docker build fails**: Make sure you're running the script from the project root directory.

3. **Services failing to start**: Check the logs with `./docker-build.sh logs` or `docker-compose logs -f` to see error messages.

### Reset Everything

To completely reset and start fresh:

```bash
./docker-build.sh full-rebuild
```

This will stop all services, remove volumes, pull fresh base images, and rebuild everything.