# Frontend Docker Testing Instructions

This document provides instructions for testing the frontend Docker build.

## Prerequisites

1. Docker must be installed and running
2. You need sudo privileges to run Docker commands

## Testing Scripts

Three test scripts have been created to help with Docker testing:

1. `test-frontend-docker-build.sh` - Simple build and run test
2. `test-frontend-docker-comprehensive.sh` - Comprehensive test with health checks
3. `analyze-frontend-docker-image.sh` - Analyze Docker image size and layers

## Running the Tests

### Simple Test

```bash
cd /home/nicola/dev/test_puntini
./test-frontend-docker-build.sh
```

### Comprehensive Test

```bash
cd /home/nicola/dev/test_puntini
./test-frontend-docker-comprehensive.sh
```

### Image Analysis

```bash
cd /home/nicola/dev/test_puntini
./analyze-frontend-docker-image.sh
```

## Manual Testing

If you prefer to run the commands manually:

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

## Configuration

The frontend Docker image is configured to:

- Connect to the backend API at http://localhost:8025
- Run on port 8026
- Use production dependencies only

Environment variables:
- `VITE_API_BASE_URL`: Set to http://localhost:8025 for backend connection
- `PORT`: Set to 8026 for the application port

## Troubleshooting

- If you get permission denied errors, make sure you have sudo privileges for Docker
- If the container fails to start, check the logs with `sudo docker logs <container-id>`
- Make sure port 8026 is not already in use on your system
- Ensure the backend is running on port 8025 for proper API connectivity