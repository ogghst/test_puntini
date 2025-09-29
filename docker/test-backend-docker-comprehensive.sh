#!/bin/bash

# Comprehensive test script for building and running the backend Docker image

set -e  # Exit on any error

echo "=== Puntini Backend Docker Test ==="

# Navigate to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../backend"

# Clean up any existing test containers
echo "Cleaning up existing containers..."
sudo docker stop puntini-test 2>/dev/null || true
sudo docker rm puntini-test 2>/dev/null || true

# Build the Docker image
echo "Building Docker image..."
sudo docker build -t puntini-backend-test .

if [ $? -eq 0 ]; then
    echo "✓ Docker build successful!"
else
    echo "✗ Docker build failed."
    exit 1
fi

# Run the container in detached mode
echo "Starting container..."
sudo docker run -d --name puntini-test -p 8025:8025 puntini-backend-test

# Wait a bit for the server to start
echo "Waiting for server to start..."
sleep 10

# Check if container is running
if sudo docker ps | grep -q puntini-test; then
    echo "✓ Container is running!"
else
    echo "✗ Container failed to start."
    echo "Container logs:"
    sudo docker logs puntini-test
    exit 1
fi

# Test the health endpoint (if available)
echo "Testing API endpoints..."
curl -f http://localhost:8025/docs 2>/dev/null || echo "API docs endpoint not available or curl failed"

# Show container logs
echo "Container logs:"
sudo docker logs puntini-test

# Clean up
echo "Cleaning up..."
sudo docker stop puntini-test
sudo docker rm puntini-test

echo "=== Test completed ==="