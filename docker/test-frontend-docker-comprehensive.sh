#!/bin/bash

# Comprehensive test script for building and running the frontend Docker image

set -e  # Exit on any error

echo "=== Puntini Frontend Docker Test ==="

# Navigate to frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../frontend"

# Clean up any existing test containers
echo "Cleaning up existing containers..."
sudo docker stop puntini-frontend-test 2>/dev/null || true
sudo docker rm puntini-frontend-test 2>/dev/null || true

# Build the Docker image
echo "Building Docker image..."
sudo docker build -t puntini-frontend-test .

if [ $? -eq 0 ]; then
    echo "✓ Docker build successful!"
else
    echo "✗ Docker build failed."
    exit 1
fi

# Run the container in detached mode
echo "Starting container..."
sudo docker run -d --name puntini-frontend-test -p 8026:8026 puntini-frontend-test

# Wait a bit for the server to start
echo "Waiting for server to start..."
sleep 10

# Check if container is running
if sudo docker ps | grep -q puntini-frontend-test; then
    echo "✓ Container is running!"
else
    echo "✗ Container failed to start."
    echo "Container logs:"
    sudo docker logs puntini-frontend-test
    exit 1
fi

# Test if we can access the frontend (basic connectivity test)
echo "Testing frontend connectivity..."
curl -f http://localhost:8026 2>/dev/null || echo "Frontend not available or curl failed"

# Show container logs
echo "Container logs:"
sudo docker logs puntini-frontend-test

# Clean up
echo "Cleaning up..."
sudo docker stop puntini-frontend-test
sudo docker rm puntini-frontend-test

echo "=== Test completed ==="