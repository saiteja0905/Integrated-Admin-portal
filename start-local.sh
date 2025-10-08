#!/bin/bash

# Shidhaan Marketplace - Local Development Startup Script

echo "🚀 Starting Shidhaan Marketplace Local Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please update .env file with your actual values before continuing."
    echo "   Required: MONGO_URL, JWT_SECRET, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET"
    read -p "Press Enter to continue after updating .env file..."
fi

# Start the application
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."

# Check MongoDB
if docker-compose exec mongodb mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is running"
else
    echo "❌ MongoDB is not responding"
fi

# Check application
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application is running"
else
    echo "❌ Application is not responding"
fi

echo ""
echo "🎉 Shidhaan Marketplace is now running!"
echo ""
echo "📱 Application URLs:"
echo "   Main App: http://localhost:8000"
echo "   Admin Login: http://localhost:8000/admin-login"
echo "   API Docs: http://localhost:8000/docs"
echo "   MongoDB Express: http://localhost:8081 (admin/admin123)"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo ""
echo "📊 To create demo users, run:"
echo "   docker-compose exec app python create_demo_users.py"
echo ""
