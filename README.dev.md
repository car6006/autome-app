# AUTO-ME PWA - Development Environment

## Quick Start Options

### Option 1: GitHub Codespaces (Recommended)
1. Open this repository in GitHub Codespaces
2. Wait for the automatic setup to complete
3. Services will start automatically
4. Access the app at the forwarded ports

### Option 2: Docker Compose
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Option 3: Local Development
```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && yarn install

# Start MongoDB and Redis
sudo service mongod start
sudo service redis-server start

# Start backend
cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Start frontend (in another terminal)
cd frontend && yarn start
```

## Environment Configuration

### Backend Environment Variables (.env)
```env
MONGO_URL=mongodb://localhost:27017/autome_dev
DB_NAME=autome_dev
WHISPER_API_KEY=your_openai_api_key_here
GCV_API_KEY=your_google_vision_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
CHUNK_DURATION_SECONDS=5
ARCHIVE_DAYS=30
JWT_SECRET_KEY=your-super-secret-jwt-key
ENVIRONMENT=development
```

### Frontend Environment Variables (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_ENVIRONMENT=development
```

## Port Configuration
- **Frontend**: 3000
- **Backend**: 8001
- **MongoDB**: 27017
- **Redis**: 6379

## Key Features Working
✅ YouTube URL Processing (with cookie authentication)
✅ Voice Recording & Transcription
✅ Photo OCR Processing
✅ File Upload (up to 500MB)
✅ Live Transcription (5-second chunks)
✅ AI-Powered Analysis
✅ Multi-language Support
✅ Advanced Search & Tagging
✅ Template System
✅ Real-time Processing

## System Requirements
- **Python**: 3.11+
- **Node.js**: 18+
- **MongoDB**: 6.0+
- **Redis**: 7+
- **FFmpeg**: For audio processing
- **yt-dlp**: For YouTube processing

## Development Workflow
1. Make changes to code
2. Hot reload is enabled for both frontend and backend
3. Test changes in browser
4. Services restart automatically on crashes

## Troubleshooting

### Services Not Starting
```bash
# Check service status
sudo supervisorctl status

# Restart services
sudo supervisorctl restart all

# View logs
sudo supervisorctl tail -f backend
sudo supervisorctl tail -f frontend
```

### API Keys Missing
Add your API keys to `/app/backend/.env`:
- OpenAI API key for transcription
- Google Vision API key for OCR
- SendGrid API key for email notifications

### YouTube Processing Issues
Ensure you're logged into YouTube in your browser for cookie authentication to work properly.

## Production Deployment
See `/app/DEPLOYMENT.md` for production deployment instructions.