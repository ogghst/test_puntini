# Docker Testing Instructions

This document provides instructions for testing the Docker builds (both backend and frontend).

## Prerequisites

1. Docker must be installed and running
2. You need sudo privileges to run Docker commands

## Backend Testing Scripts

Two test scripts have been created to help with backend Docker testing:

1. `test-docker-build.sh` - Simple build and run test
2. `test-docker-comprehensive.sh` - Comprehensive test with health checks

## Frontend Testing Scripts

Three test scripts have been created to help with frontend Docker testing:

1. `test-frontend-docker-build.sh` - Simple build and run test
2. `test-frontend-docker-comprehensive.sh` - Comprehensive test with health checks
3. `analyze-frontend-docker-image.sh` - Analyze Docker image size and layers

## Running the Tests

### Backend Tests

#### Simple Test

```bash
cd /home/nicola/dev/test_puntini
./test-docker-build.sh
```

#### Comprehensive Test

```bash
cd /home/nicola/dev/test_puntini
./test-docker-comprehensive.sh
```

### Frontend Tests

#### Simple Test

```bash
cd /home/nicola/dev/test_puntini
./test-frontend-docker-build.sh
```

#### Comprehensive Test

```bash
cd /home/nicola/dev/test_puntini
./test-frontend-docker-comprehensive.sh
```

#### Image Analysis

```bash
cd /home/nicola/dev/test_puntini
./analyze-frontend-docker-image.sh
```

## Manual Testing

### Backend

1. Build the image:
   ```bash
   cd /home/nicola/dev/test_puntini/backend
   sudo docker build -t puntini-backend-test .
   ```

2. Run the container:
   ```bash
   sudo docker run --rm -p 8025:8025 puntini-backend-test
   ```

3. Test the API:
   Open your browser to http://localhost:8025/docs to see the API documentation.

### Frontend

1. Build the image:
   ```bash
   cd /home/nicola/dev/test_puntini/frontend
   sudo docker build -t puntini-frontend-test .
   ```

2. Run the container:
   ```bash
   sudo docker run --rm -p 8026:8026 puntini-frontend-test
   ```

3. Test the frontend:
   Open your browser to http://localhost:8026 to see the frontend application.

## Troubleshooting

- If you get permission denied errors, make sure you have sudo privileges for Docker
- If the container fails to start, check the logs with `sudo docker logs <container-id>`
- Make sure ports 8025 (backend) and 8026 (frontend) are not already in use on your system