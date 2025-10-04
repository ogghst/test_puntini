#!/bin/bash

# Docker Compose startup script for Puntini

set -e

echo "=== Puntini Docker Compose Startup ==="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Parse command line arguments
ENVIRONMENT="development"
SERVICES="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--services)
            SERVICES="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --env ENVIRONMENT    Set environment (development|production) [default: development]"
            echo "  -s, --services SERVICES  Set services to start (all|frontend|backend) [default: all]"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "Environment: $ENVIRONMENT"
echo "Services: $SERVICES"

# Set up environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ "$ENVIRONMENT" = "production" ]; then
        cp .env.production .env
        echo "✅ Created .env from production template"
    else
        cp .env.development .env
        echo "✅ Created .env from development template"
    fi
    echo "⚠️  Please edit .env file with your specific configuration"
    echo "   Press Enter to continue or Ctrl+C to exit and edit .env first"
    read -r
else
    echo "✅ Using existing .env file"
fi

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null || true

# Start services based on selection
case $SERVICES in
    "frontend")
        echo "🚀 Starting frontend service..."
        docker-compose -f docker-compose.frontend.yml up -d
        echo "✅ Frontend service started"
        echo "🌐 Frontend available at: http://localhost:8026"
        ;;
    "backend")
        echo "🚀 Starting backend service..."
        docker-compose up -d puntini-backend
        echo "✅ Backend service started"
        echo "🌐 Backend API available at: http://localhost:8025"
        echo "📚 API documentation at: http://localhost:8025/docs"
        ;;
    "all")
        echo "🚀 Starting all services..."
        docker-compose up -d
        echo "✅ All services started"
        echo "🌐 Frontend available at: http://localhost:8026"
        echo "🌐 Backend API available at: http://localhost:8025"
        echo "📚 API documentation at: http://localhost:8025/docs"
        ;;
    *)
        echo "❌ Invalid services option: $SERVICES"
        echo "Valid options: all, frontend, backend"
        exit 1
        ;;
esac

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo "📊 Service status:"
docker-compose ps

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=20

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Useful commands:"
echo "  View logs:           docker-compose logs -f"
echo "  Stop services:       docker-compose down"
echo "  Restart services:    docker-compose restart"
echo "  View status:         docker-compose ps"
echo ""
echo "For more information, see README.md"
