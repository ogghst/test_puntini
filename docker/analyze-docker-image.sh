#!/bin/bash

# Script to analyze the Docker image

echo "=== Docker Image Analysis ==="

# Navigate to backend directory
cd /home/nicola/dev/test_puntini/backend

# Build the Docker image if it doesn't exist
if ! sudo docker images | grep -q puntini-backend-test; then
    echo "Building Docker image..."
    sudo docker build -t puntini-backend-test .
fi

# Show image size
echo "Image size:"
sudo docker images puntini-backend-test

# Show image layers
echo "Image layers:"
sudo docker history puntini-backend-test

# Show detailed image information
echo "Detailed image information:"
sudo docker inspect puntini-backend-test

echo "=== Analysis complete ==="