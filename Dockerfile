# Multi-stage Dockerfile for Shidhaan Blue-collar Marketplace
# Stage 1: Build React Frontend
FROM node:22-alpine3.21 AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/yarn.lock* ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy frontend source code
COPY frontend/ ./

# Build argument for backend URL (empty = relative URLs, same origin)
ARG REACT_APP_BACKEND_URL=""
ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}

# Build the React app
RUN yarn build

# Stage 2: Python Backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for health checks, gosu to drop privileges
# after preparing the mounted uploads volume)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./static

# Create non-root user (and the uploads dir it owns, so a mounted volume is writable)
RUN mkdir -p /app/uploads && \
    useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# The entrypoint runs as root only long enough to take ownership of the mounted
# uploads volume, then hands the server over to the app user.
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start the application
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
