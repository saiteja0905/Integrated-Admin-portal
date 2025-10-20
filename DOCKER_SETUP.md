# 🐳 Docker Setup Guide for Shidhaan

This guide explains how to run the Shidhaan Blue-collar Marketplace using Docker and Docker Compose.

## 📋 Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- At least 4GB of free RAM
- Ports 8000, 8081, and 27017 available

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Integrated-Admin-portal
```

### 2. Configure Environment Variables (Optional)

The default configuration in `docker-compose.yml` works out of the box. For production or custom setup:

```bash
# Review and modify docker-compose.yml environment variables
nano docker-compose.yml
```

### 3. Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

### 4. Access the Application

Once all services are running:

- **Frontend & Backend**: http://localhost:8000
- **MongoDB Express** (Database UI): http://localhost:8081
  - Username: `admin`
  - Password: `admin123`

### 5. Create Demo Users (Optional)

To populate the database with test data:

```bash
# Execute the demo user creation script inside the container
docker-compose exec app python create_demo_users.py
```

Demo credentials will be displayed after running the script.

## 🛠️ Docker Services

### Service Overview

| Service | Port | Description |
|---------|------|-------------|
| **app** | 8000 | FastAPI backend + React frontend |
| **mongodb** | 27017 | MongoDB database |
| **mongo-express** | 8081 | MongoDB admin interface |

### Service Health Checks

```bash
# Check if all services are healthy
docker-compose ps

# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs app
docker-compose logs mongodb
```

## 📝 Common Commands

### Starting and Stopping

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (⚠️ deletes database data)
docker-compose down -v
```

### Building and Rebuilding

```bash
# Rebuild without cache
docker-compose build --no-cache

# Rebuild and restart
docker-compose up --build --force-recreate
```

### Viewing Logs

```bash
# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# Logs for specific service
docker-compose logs -f app
```

### Accessing Containers

```bash
# Open bash shell in app container
docker-compose exec app bash

# Open MongoDB shell
docker-compose exec mongodb mongosh -u admin -p password123

# Run Python commands in app container
docker-compose exec app python -c "print('Hello')"
```

## 🔧 Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change ports in docker-compose.yml
```

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
docker-compose ps mongodb

# View MongoDB logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb
```

### Build Failures

```bash
# Clean Docker cache
docker system prune -a

# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up --build --force-recreate
```

### Frontend Not Loading

The frontend is built into the Docker image. If you see API errors:

1. Check that `REACT_APP_BACKEND_URL` in Dockerfile is correct
2. Rebuild the image: `docker-compose up --build`
3. Clear browser cache

### Check Backend Health

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","timestamp":"2024-..."}
```

## 🔒 Production Deployment

For production deployment, update the following in `docker-compose.yml`:

### 1. Security Settings

```yaml
environment:
  - JWT_SECRET=<generate-32-character-random-string>
  - RAZORPAY_KEY_ID=<your-real-razorpay-key>
  - RAZORPAY_KEY_SECRET=<your-real-razorpay-secret>
  - MONGO_URL=mongodb://admin:<strong-password>@mongodb:27017
```

### 2. MongoDB Security

```yaml
mongodb:
  environment:
    MONGO_INITDB_ROOT_PASSWORD: <strong-password>
```

### 3. Remove Development Tools

Comment out or remove the `mongo-express` service in production.

### 4. Use Docker Secrets

For better security, use Docker secrets instead of environment variables:

```yaml
secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  
services:
  app:
    secrets:
      - jwt_secret
```

### 5. Enable HTTPS

Add a reverse proxy (nginx/traefik) with SSL certificates:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
```

## 📊 Database Management

### Backup Database

```bash
# Create backup
docker-compose exec mongodb mongodump \
  --username admin \
  --password password123 \
  --authenticationDatabase admin \
  --out /data/backup

# Copy backup to host
docker cp shidhaan-mongodb:/data/backup ./mongodb-backup
```

### Restore Database

```bash
# Copy backup to container
docker cp ./mongodb-backup shidhaan-mongodb:/data/restore

# Restore database
docker-compose exec mongodb mongorestore \
  --username admin \
  --password password123 \
  --authenticationDatabase admin \
  /data/restore
```

### Reset Database

```bash
# Stop services and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d

# Recreate demo users
docker-compose exec app python create_demo_users.py
```

## 🧪 Development vs Production

### Development Mode

For local development with hot-reload:

1. Run MongoDB in Docker:
   ```bash
   docker-compose up mongodb -d
   ```

2. Run backend locally:
   ```bash
   cd backend
   uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```

3. Run frontend locally:
   ```bash
   cd frontend
   yarn start
   ```

### Production Mode

Use the full Docker Compose setup as described in this guide.

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)

## 🆘 Getting Help

If you encounter issues:

1. Check service logs: `docker-compose logs`
2. Verify all services are healthy: `docker-compose ps`
3. Try rebuilding: `docker-compose up --build --force-recreate`
4. Check port availability: Ensure 8000, 8081, 27017 are free
5. Review environment variables in `docker-compose.yml`

## 📄 License

[Your License Here]

