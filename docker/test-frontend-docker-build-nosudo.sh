#!/bin/bash

# Test script for building and running the frontend Docker image
# This script checks if Docker is available and can run without sudo

echo "Testing frontend Docker build..."

# Check if Docker is installed and available
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker can run without sudo (test with a simple command)
if ! docker version &> /dev/null; then
    echo "Docker requires sudo privileges. Please run with sudo or configure Docker for non-root usage."
    echo "You can run: sudo $0"
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
cd /home/nicola/dev/test_puntini/frontend
docker build -t puntini-frontend-test .

if [ $? -eq 0 ]; then
    echo "Docker build successful!"
    echo "To run the container, use:"
    echo "docker run --rm -p 8026:8026 puntini-frontend-test"
else
    echo "Docker build failed."
fi