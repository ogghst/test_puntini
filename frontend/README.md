# Puntini Frontend

This is the frontend application for the Puntini Agent system.

## Docker Setup

The frontend application can be built and run using Docker.

### Building the Docker Image

```bash
cd frontend
docker build -t puntini-frontend .
```

### Running the Container

```bash
docker run --rm -p 8026:8026 puntini-frontend
```

The application will be available at http://localhost:8026.

### Configuration

The Docker image is configured with the following environment variables:

- `VITE_API_BASE_URL`: http://localhost:8025 (backend API endpoint)
- `PORT`: 8026 (application port)

### Development

For development, you can run the application locally:

```bash
npm install
npm run dev
```

The development server will start on http://localhost:5173 by default.