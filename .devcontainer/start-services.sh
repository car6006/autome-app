#!/bin/bash
set -e

echo "🚀 Starting AUTO-ME PWA services..."

# Wait for setup to complete
sleep 5

# Start MongoDB first
echo "📊 Starting MongoDB..."
sudo service mongod start

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
until mongosh --eval "db.adminCommand('ismaster')" >/dev/null 2>&1; do
    sleep 1
done
echo "✅ MongoDB is ready"

# Start Redis
echo "🔴 Starting Redis..."
sudo service redis-server start

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
until redis-cli ping >/dev/null 2>&1; do
    sleep 1
done
echo "✅ Redis is ready"

# Start supervisor to manage our services
echo "👨‍💼 Starting Supervisor..."
sudo service supervisor start

# Wait a moment for services to initialize
sleep 3

# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start all services
echo "🚀 Starting all application services..."
sudo supervisorctl start all

# Show status
echo "📊 Service Status:"
sudo supervisorctl status

echo ""
echo "🎉 AUTO-ME PWA is ready!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8001"
echo "📊 Backend Health: http://localhost:8001/api/health"

if [ "$ENVIRONMENT" = "codespaces" ]; then
    echo ""
    echo "🌐 GitHub Codespaces URLs:"
    echo "Frontend: https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
    echo "Backend: https://${CODESPACE_NAME}-8001.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/api/health"
fi