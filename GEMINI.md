refer to [Agents.md](AGENTS.md)

## Docker and GitHub Actions

The project includes comprehensive Docker support for both backend and frontend applications, along with GitHub Actions for automated testing and deployment.

### Docker Images

- **Backend**: Python 3.11-based image running the FastAPI server on port 8025
- **Frontend**: Node.js 20 Alpine-based image running the React Router application on port 8026

Both Docker images are optimized for production use with multi-stage builds.

### GitHub Actions Workflows

1. **Backend Testing** (`.github/workflows/backend-docker.yml`): Builds and tests the backend Docker image
2. **Frontend Testing** (`.github/workflows/frontend-docker.yml`): Builds and tests the frontend Docker image
3. **Docker Publishing** (`.github/workflows/docker-publish.yml`): Publishes the backend image to Docker Hub

For detailed information about Docker usage and GitHub Actions, see [AGENTS.md](AGENTS.md).