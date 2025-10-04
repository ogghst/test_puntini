#!/bin/bash

# Test script for building and running the backend Docker image

echo "Testing backend Docker build..."

# Build the Docker image
echo "Building Docker image..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../backend"
sudo docker build -t puntini-backend-test .

if [ $? -eq 0 ]; then
    echo "Docker build successful!"
    
    # Run the container
    echo "Running container..."
    sudo docker run --rm -p 8025:8025 puntini-backend-test
    
    if [ $? -eq 0 ]; then
        echo "Container ran successfully!"
    else
        echo "Container failed to run."
    fi
else
    echo "Docker build failed."
fi