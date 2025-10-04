# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy the docker-specific configuration file to the default config.json
# This file should exist as backend/config.docker.json in the repository
COPY config.docker.json config.json

# Expose the port the app runs on
<<<<<<< HEAD
EXPOSE 8026
=======
EXPOSE 8025
>>>>>>> 4204b32f4cfdabb5d42e18cd506c75762a75a455

# Define the command to run the application
CMD ["python", "run_server.py"]
