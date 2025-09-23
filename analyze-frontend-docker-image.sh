#!/bin/bash

# Script to analyze the frontend Docker image

echo "=== Frontend Docker Image Analysis ==="

# Navigate to frontend directory
cd /home/nicola/dev/test_puntini/frontend

# Build the Docker image if it doesn't exist
if ! sudo docker images | grep -q puntini-frontend-test; then
    echo "Building Docker image..."
    sudo docker build -t puntini-frontend-test .
fi

# Show image size
echo "Image size:"
sudo docker images puntini-frontend-test

# Show image layers
echo "Image layers:"
sudo docker history puntini-frontend-test

# Show detailed image information
echo "Detailed image information:"
sudo docker inspect puntini-frontend-test

echo "=== Analysis complete ==="