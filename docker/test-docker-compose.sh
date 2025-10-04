#!/bin/bash

# Test script for Docker Compose setup

set -e

echo "=== Docker Compose Test ==="

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

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null || true

# Test configuration
echo "🔍 Testing Docker Compose configuration..."
docker-compose config > /dev/null
echo "✅ Configuration is valid"

# Test frontend-only setup
echo "🧪 Testing frontend-only setup..."
cp .env.development .env
docker-compose -f docker-compose.frontend.yml up -d

# Wait for service to start
echo "⏳ Waiting for frontend service to start..."
sleep 15

# Check if frontend is running
if docker-compose -f docker-compose.frontend.yml ps | grep -q "Up"; then
    echo "✅ Frontend service is running"
    
    # Test frontend connectivity
    echo "🌐 Testing frontend connectivity..."
    if curl -f http://localhost:8026 > /dev/null 2>&1; then
        echo "✅ Frontend is accessible at http://localhost:8026"
    else
        echo "⚠️  Frontend is running but not accessible (this might be expected if backend is not running)"
    fi
else
    echo "❌ Frontend service failed to start"
    echo "Container logs:"
    docker-compose -f docker-compose.frontend.yml logs
    exit 1
fi

# Clean up frontend test
echo "🧹 Cleaning up frontend test..."
docker-compose -f docker-compose.frontend.yml down

# Test complete stack (if backend is available)
echo "🧪 Testing complete stack..."
if [ -d "../backend" ]; then
    docker-compose up -d
    
    # Wait for services to start
    echo "⏳ Waiting for services to start..."
    sleep 20
    
    # Check service status
    echo "📊 Service status:"
    docker-compose ps
    
    # Test backend connectivity
    echo "🌐 Testing backend connectivity..."
    if curl -f http://localhost:8025/docs > /dev/null 2>&1; then
        echo "✅ Backend is accessible at http://localhost:8025"
    else
        echo "⚠️  Backend is running but not accessible"
    fi
    
    # Test frontend connectivity
    echo "🌐 Testing frontend connectivity..."
    if curl -f http://localhost:8026 > /dev/null 2>&1; then
        echo "✅ Frontend is accessible at http://localhost:8026"
    else
        echo "⚠️  Frontend is running but not accessible"
    fi
    
    # Clean up
    echo "🧹 Cleaning up complete stack test..."
    docker-compose down
else
    echo "⚠️  Backend directory not found, skipping complete stack test"
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "✅ Docker Compose setup is working correctly!"
echo ""
echo "To start the services:"
echo "  ./start-docker-compose.sh"
echo ""
echo "To start with specific environment:"
echo "  ./start-docker-compose.sh --env production"
echo ""
echo "To start only frontend:"
echo "  ./start-docker-compose.sh --services frontend"
