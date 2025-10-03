#!/bin/bash

# Script to build and manage the Puntini application Docker containers
# Usage: ./docker-build.sh [build|up|down|logs|rebuild]

set -e  # Exit script on any error

# Default command
COMMAND="build"

# Parse command line arguments
if [ $# -ge 1 ]; then
    COMMAND=$1
fi

# Print script header
echo "==========================================="
echo "Puntini Application Docker Management"
echo "Command: $COMMAND"
echo "==========================================="

# Function to build images
build_images() {
    echo "Building Docker images for Puntini application..."
    docker-compose build
    echo "Docker images built successfully!"
}

# Function to start services
start_services() {
    echo "Starting Puntini application services..."
    docker-compose up -d
    echo "Services started in detached mode. Use 'docker-compose logs -f' to view logs."
}

# Function to stop services
stop_services() {
    echo "Stopping Puntini application services..."
    docker-compose down
    echo "Services stopped."
}

# Function to view logs
view_logs() {
    echo "Displaying logs for all services..."
    docker-compose logs -f
}

# Function to rebuild images and restart services
rebuild_services() {
    echo "Rebuilding Docker images and restarting services..."
    docker-compose down
    docker-compose build
    docker-compose up -d
    echo "Services rebuilt and restarted in detached mode."
}

# Function to pull latest base images
pull_base_images() {
    echo "Pulling latest base images..."
    docker-compose pull --ignore-pull-failures
}

# Execute command
case $COMMAND in
    "build")
        build_images
        ;;
    "up")
        start_services
        ;;
    "down")
        stop_services
        ;;
    "logs")
        view_logs
        ;;
    "rebuild")
        rebuild_services
        ;;
    "pull")
        pull_base_images
        ;;
    "start")
        pull_base_images
        build_images
        start_services
        ;;
    "full-rebuild")
        stop_services
        echo "Removing containers and volumes..."
        docker-compose down -v
        pull_base_images
        rebuild_services
        ;;
    *)
        echo "Invalid command: $COMMAND"
        echo ""
        echo "Available commands:"
        echo "  build      - Build Docker images"
        echo "  up         - Start services in detached mode"
        echo "  down       - Stop services"
        echo "  logs       - View logs from all services"
        echo "  rebuild    - Rebuild images and restart services"
        echo "  pull       - Pull latest base images"
        echo "  start      - Pull, build and start all services"
        echo "  full-rebuild - Stop, remove volumes, rebuild everything"
        echo ""
        echo "Example: $0 start"
        exit 1
        ;;
esac

echo "==========================================="
echo "Command completed successfully!"
echo "==========================================="