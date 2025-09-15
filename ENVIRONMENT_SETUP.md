# 🚀 AUTO-ME PWA - Environment Setup Guide

## 🎯 Quick Start (Choose Your Preferred Method)

### 1. GitHub Codespaces (Recommended for Cloud Development)
```bash
# Simply open this repository in GitHub Codespaces
# Everything will be set up automatically!
```

### 2. Docker Compose (Recommended for Local Development)
```bash
# Clone the repository
git clone <your-repo-url>
cd autome-pwa

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
```

### 3. Manual Setup (Full Control)
```bash
# Prerequisites
sudo apt-get update
sudo apt-get install -y python3.11 nodejs npm mongodb-server redis-server ffmpeg

# Install yt-dlp for YouTube processing
pip install yt-dlp

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd ../frontend
npm install -g yarn
yarn install
cp .env.example .env

# Start services
sudo service mongod start
sudo service redis-server start

# Start backend (terminal 1)
cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Start frontend (terminal 2)
cd frontend && yarn start
```

## 🔑 Required API Keys

### OpenAI API Key (Required for Transcription)
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `backend/.env` as `WHISPER_API_KEY=sk-...`

### Google Vision API Key (Required for OCR)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable Vision API
3. Create API key
4. Add to `backend/.env` as `GCV_API_KEY=...`

### SendGrid API Key (Optional for Email)
1. Go to [SendGrid](https://sendgrid.com)
2. Create API key
3. Add to `backend/.env` as `SENDGRID_API_KEY=SG....`

## 🌐 Environment-Specific Configurations

### GitHub Codespaces
- Ports automatically forwarded
- Environment variables configured
- Services start automatically
- Development-ready out of the box

### Local Docker
- All services containerized
- Data persistence with volumes
- Easy service management
- Production-like environment

### Manual Local Setup
- Full control over dependencies
- Direct service access
- Fastest development iteration
- Requires more setup

## 🔧 Service Management

### Using Supervisor (Recommended)
```bash
# Start all services
sudo supervisorctl start all

# Check service status
sudo supervisorctl status

# Restart specific service
sudo supervisorctl restart backend

# View logs
sudo supervisorctl tail -f backend
```

### Using Docker Compose
```bash
# Start services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## 📊 Port Configuration

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | React development server |
| Backend | 8001 | FastAPI application |
| MongoDB | 27017 | Database |
| Redis | 6379 | Caching & live transcription |

## 🧪 Verification Steps

### 1. Check Backend Health
```bash
curl http://localhost:8001/api/health
# Should return: {"status": "healthy"}
```

### 2. Check Frontend
```bash
# Navigate to http://localhost:3000
# Should show AUTO-ME PWA interface
```

### 3. Test YouTube Processing
1. Go to Features → YouTube Processing
2. Enter URL: `https://youtu.be/Lseaqxg8NaY?si=GW5dKoEcG7p_bjUk`
3. Click Preview → Should show video info
4. Click Extract Audio → Should start processing

### 4. Test Voice Recording
1. Go to Voice Capture
2. Click Record Audio
3. Allow microphone access
4. Record briefly and stop
5. Should transcribe automatically

## 🐛 Troubleshooting

### YouTube Processing Not Working
- Ensure you're logged into YouTube in your browser
- Check that yt-dlp is installed: `yt-dlp --version`
- Try different YouTube videos (educational content works better)

### Transcription Failing
- Verify OpenAI API key in `backend/.env`
- Check API key has sufficient credits
- Look at backend logs: `sudo supervisorctl tail -f backend`

### Services Not Starting
```bash
# Check if ports are available
sudo netstat -tlnp | grep :3000
sudo netstat -tlnp | grep :8001

# Restart all services
sudo supervisorctl restart all

# Check system resources
df -h  # Disk space
free -h  # Memory
```

### MongoDB Connection Issues
```bash
# Check MongoDB status
sudo service mongod status

# Start MongoDB
sudo service mongod start

# Check connection
mongosh --eval "db.adminCommand('ismaster')"
```

## 🔄 Updates and Maintenance

### Updating Dependencies
```bash
# Backend
cd backend && pip install -r requirements.txt --upgrade

# Frontend
cd frontend && yarn upgrade

# System packages
sudo apt-get update && sudo apt-get upgrade
```

### Backing Up Data
```bash
# Export MongoDB data
mongodump --db autome_dev --out backup/

# Backup uploads and logs
tar -czf backup/files.tar.gz logs/ uploads/
```

## 📈 Performance Optimization

### For Development
- Use supervisor for service management
- Enable hot reload for faster iteration
- Use Redis for caching
- Monitor logs in real-time

### For Production
- Use Docker containers
- Configure load balancing
- Set up monitoring and alerts
- Enable automatic backups

---

**Last Updated**: September 14, 2025
**Version**: 1.0 - Stable with YouTube fixes
**Environment Status**: ✅ Ready for Development and Production