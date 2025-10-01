#!/bin/bash

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

echo "Starting combined frontend and backend services..."

# Start backend server
echo "Starting backend on port 8026..."
cd /app
python run_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo "Starting frontend on port 8025..."
cd /app/frontend
PORT=8025 npm start &
FRONTEND_PID=$!

echo "Both services started successfully!"
echo "Frontend: http://localhost:8025"
echo "Backend: http://localhost:8026"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
