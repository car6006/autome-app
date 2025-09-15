#!/bin/bash
set -e

echo "🚀 Setting up AUTO-ME PWA Development Environment..."

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y \
    ffmpeg \
    supervisor \
    redis-server \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Install yt-dlp for YouTube processing
sudo pip install yt-dlp

# Create data directories
sudo mkdir -p /data/db
sudo mkdir -p /var/log/supervisor
sudo mkdir -p /app/logs

# Set permissions
sudo chown -R vscode:vscode /app
sudo chown -R mongodb:mongodb /data/db

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd /app/backend
pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd /app/frontend
npm install -g yarn
yarn install

# Copy environment files if they don't exist
if [ ! -f /app/backend/.env ]; then
    cp /app/backend/.env.example /app/backend/.env 2>/dev/null || echo "No .env.example found, creating basic .env"
    cat > /app/backend/.env << EOF
MONGO_URL=mongodb://localhost:27017/autome_dev
DB_NAME=autome_dev
WHISPER_API_KEY=your_openai_api_key_here
GCV_API_KEY=your_google_vision_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
CHUNK_DURATION_SECONDS=5
ARCHIVE_DAYS=30
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ENVIRONMENT=development
EOF
fi

if [ ! -f /app/frontend/.env ]; then
    cp /app/frontend/.env.example /app/frontend/.env 2>/dev/null || echo "No .env.example found, creating basic .env"
    cat > /app/frontend/.env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_ENVIRONMENT=development
EOF
fi

# Update frontend .env for Codespaces if in that environment
if [ "$ENVIRONMENT" = "codespaces" ]; then
    echo "🌐 Configuring for GitHub Codespaces..."
    cat > /app/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://${CODESPACE_NAME}-8001.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}
REACT_APP_ENVIRONMENT=development
EOF
fi

# Create supervisor configuration
sudo mkdir -p /etc/supervisor/conf.d

# Backend supervisor config
sudo tee /etc/supervisor/conf.d/backend.conf > /dev/null << EOF
[program:backend]
command=/usr/local/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
directory=/app/backend
user=vscode
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=PATH="/usr/local/bin:%(ENV_PATH)s"
EOF

# Frontend supervisor config
sudo tee /etc/supervisor/conf.d/frontend.conf > /dev/null << EOF
[program:frontend]
command=/usr/local/bin/yarn start
directory=/app/frontend
user=vscode
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
environment=PATH="/usr/local/bin:%(ENV_PATH)s",PORT="3000",HOST="0.0.0.0"
EOF

# MongoDB supervisor config
sudo tee /etc/supervisor/conf.d/mongodb.conf > /dev/null << EOF
[program:mongodb]
command=/usr/bin/mongod --dbpath /data/db --nojournal --smallfiles
user=mongodb
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/mongodb.err.log
stdout_logfile=/var/log/supervisor/mongodb.out.log
EOF

# Redis supervisor config
sudo tee /etc/supervisor/conf.d/redis.conf > /dev/null << EOF
[program:redis]
command=/usr/bin/redis-server --bind 0.0.0.0 --port 6379
user=redis
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/redis.err.log
stdout_logfile=/var/log/supervisor/redis.out.log
EOF

echo "✅ Setup completed successfully!"
echo "🔧 Services will be started automatically when the container starts"
echo "📝 Don't forget to add your API keys to /app/backend/.env"