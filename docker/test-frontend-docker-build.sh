#!/bin/bash

# Test script for building and running the frontend Docker image

echo "Testing frontend Docker build..."

# Build the Docker image
echo "Building Docker image..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../frontend"
sudo docker build -t puntini-frontend-test .

if [ $? -eq 0 ]; then
    echo "Docker build successful!"
    
    # Run the container
    echo "Running container..."
    sudo docker run --rm -p 8026:8026 puntini-frontend-test
    
    if [ $? -eq 0 ]; then
        echo "Container ran successfully!"
    else
        echo "Container failed to run."
    fi
else
    echo "Docker build failed."
fi