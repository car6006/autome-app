# 🚀 DEPLOYMENT GUIDE - Phase 1 Enhanced Features

## Overview
Comprehensive deployment guide for AUTO-ME PWA Phase 1 enhancements including new features, bug fixes, and mobile responsiveness improvements.

## 📋 PRE-DEPLOYMENT CHECKLIST

### ✅ Code Quality Verification
- [ ] All ESLint errors resolved
- [ ] TypeScript compilation successful
- [ ] No console errors in browser
- [ ] All tests passing (backend: 100%, frontend: 95%+)
- [ ] Performance Lighthouse score > 90

### ✅ Feature Verification
- [ ] Search functionality working across all note types
- [ ] Tagging system with smart suggestions operational
- [ ] Share button working on mobile and desktop
- [ ] Template system fully functional
- [ ] M4A transcription working with FFmpeg conversion
- [ ] Transcript editing save persisting correctly

### ✅ Mobile Responsiveness
- [ ] Header Profile/Help buttons visible and functional
- [ ] Bottom navigation properly positioned with safe area support
- [ ] No horizontal scrolling on mobile viewports
- [ ] Touch targets meet 44px minimum accessibility standard
- [ ] All buttons responsive across device sizes

---

## 🏗️ INFRASTRUCTURE REQUIREMENTS

### System Dependencies
```bash
# Backend Requirements
Python 3.8+
FFmpeg (latest)
MongoDB 4.4+
Redis 6.0+ (for live features)

# Frontend Requirements  
Node.js 16+
npm/yarn latest
```

### Environment Variables

**Backend** (`.env`):
```env
# Database
MONGO_URL=mongodb://localhost:27017/auto_me

# AI Services
OPENAI_API_KEY=your_openai_key
EMERGENT_LLM_KEY=your_emergent_key

# Services
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=https://your-frontend-domain.com
```

**Frontend** (`.env`):
```env
# API Configuration
REACT_APP_BACKEND_URL=https://your-api-domain.com

# Features
REACT_APP_ENABLE_TEMPLATES=true
REACT_APP_ENABLE_LIVE_TRANSCRIPTION=true
```

---

## 📦 DEPLOYMENT STEPS

### Step 1: Database Migrations
```bash
# No breaking schema changes required
# New collections will be created automatically:
# - templates (for template system)
# - tags will be added to existing notes collection

# Verify MongoDB connection
mongosh $MONGO_URL --eval "db.runCommand('ping')"
```

### Step 2: Backend Deployment
```bash
# Install dependencies
cd /app/backend
pip install -r requirements.txt

# Verify FFmpeg installation for M4A support
ffmpeg -version

# Start backend services
sudo supervisorctl restart backend

# Verify API health
curl https://your-api-domain.com/api/health
```

### Step 3: Frontend Deployment
```bash
# Install dependencies and build
cd /app/frontend
yarn install
yarn build

# Deploy to web server
sudo supervisorctl restart frontend

# Verify frontend loading
curl https://your-frontend-domain.com
```

### Step 4: Service Verification
```bash
# Check all services running
sudo supervisorctl status

# Expected output:
# backend          RUNNING   pid 1234, uptime 0:00:05
# frontend         RUNNING   pid 5678, uptime 0:00:05
```

---

## 🔧 CONFIGURATION UPDATES

### Nginx Configuration (if applicable)
```nginx
# API routes with /api prefix
location /api/ {
    proxy_pass http://localhost:8001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Increase timeout for large file processing
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;
    
    # Support for file uploads
    client_max_body_size 100M;
}

# Frontend routes
location / {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # Support for PWA
    location /manifest.json {
        add_header Cache-Control "public, max-age=86400";
    }
    
    location /service-worker.js {
        add_header Cache-Control "no-cache";
    }
}
```

### Supervisor Configuration
```ini
[program:backend]
command=/root/.venv/bin/python server.py
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=PATH="/root/.venv/bin"

[program:frontend]
command=yarn start
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
```

---

## 🧪 POST-DEPLOYMENT TESTING

### API Endpoint Testing
```bash
# Test new template endpoints
curl -X GET https://your-api-domain.com/api/templates \
  -H "Authorization: Bearer $JWT_TOKEN"

# Test tag endpoints
curl -X POST https://your-api-domain.com/api/notes/test-id/tags \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag": "test"}'

# Test note update endpoint
curl -X PUT https://your-api-domain.com/api/notes/test-id \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"artifacts": {"transcript": "Updated content"}}'
```

### Frontend Feature Testing
```bash
# Test mobile responsiveness
curl -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)" \
  https://your-frontend-domain.com

# Test PWA manifest
curl https://your-frontend-domain.com/manifest.json

# Test service worker
curl https://your-frontend-domain.com/service-worker.js
```

### M4A Transcription Testing
```bash
# Verify FFmpeg M4A support
ffmpeg -f lavfi -i "sine=frequency=1000:duration=5" -c:a aac test.m4a
curl -X POST https://your-api-domain.com/api/notes \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@test.m4a" \
  -F "title=M4A Test"
```

---

## 📊 MONITORING & HEALTH CHECKS

### Application Health Endpoints
```bash
# Backend health
GET /api/health
# Response: {"status": "healthy", "timestamp": "2025-09-11T12:00:00Z"}

# Database health
GET /api/health/db
# Response: {"status": "connected", "collections": ["notes", "templates"]}

# Service health
GET /api/health/services
# Response: {"ffmpeg": "available", "redis": "connected"}
```

### Performance Monitoring
```javascript
// Frontend performance metrics
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(`${entry.name}: ${entry.duration}ms`);
  }
});
observer.observe({entryTypes: ['navigation', 'paint']});

// Key metrics to monitor:
// - First Contentful Paint < 2.5s
// - Largest Contentful Paint < 4s
// - Time to Interactive < 3.5s
```

### Error Monitoring
```python
# Backend error tracking
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/auto-me/backend.log'),
        logging.StreamHandler()
    ]
)

# Monitor for:
# - 4xx client errors
# - 5xx server errors  
# - Database connection issues
# - FFmpeg conversion failures
```

---

## 🔄 ROLLBACK PROCEDURES

### Quick Rollback (if issues detected)
```bash
# Stop services
sudo supervisorctl stop all

# Revert to previous code version
git checkout previous-stable-commit

# Rebuild and restart
cd /app/frontend && yarn build
sudo supervisorctl start all

# Verify services
curl https://your-frontend-domain.com/api/health
```

### Database Rollback (if needed)
```bash
# Templates are new collection - can be dropped if needed
mongosh $MONGO_URL --eval "db.templates.drop()"

# Tags field is optional - existing notes unaffected
# No rollback needed for tags field
```

---

## 🚨 TROUBLESHOOTING

### Common Issues & Solutions

**Backend won't start**:
```bash
# Check logs
tail -f /var/log/supervisor/backend.err.log

# Common causes:
# - Missing dependencies: pip install -r requirements.txt
# - FFmpeg not found: apt-get install ffmpeg
# - MongoDB connection: verify MONGO_URL
```

**Frontend build fails**:
```bash
# Clear cache and rebuild
cd /app/frontend
rm -rf node_modules package-lock.json
yarn install
yarn build

# Check for memory issues
export NODE_OPTIONS="--max-old-space-size=4096"
```

**M4A files not converting**:
```bash
# Verify FFmpeg installation
ffmpeg -version
ffmpeg -encoders | grep aac

# Test manual conversion
ffmpeg -i test.m4a -acodec pcm_s16le -ar 16000 -ac 1 test.wav
```

**Mobile layout issues**:
```css
/* Add to global CSS if needed */
html {
  font-size: 16px; /* Prevent zoom on input focus */
}

@supports(padding: max(0px)) {
  .pb-safe {
    padding-bottom: max(8px, env(safe-area-inset-bottom));
  }
}
```

### Performance Issues
```bash
# Monitor resource usage
htop
df -h
free -m

# Check database performance
mongosh $MONGO_URL --eval "db.notes.getIndexes()"

# Optimize if needed
mongosh $MONGO_URL --eval "db.notes.createIndex({user_id: 1, created_at: -1})"
mongosh $MONGO_URL --eval "db.templates.createIndex({user_id: 1, usage_count: -1})"
```

---

## 📈 SCALING CONSIDERATIONS

### Horizontal Scaling
```yaml
# Docker Compose example
version: '3.8'
services:
  backend:
    build: ./backend
    replicas: 3
    environment:
      - MONGO_URL=mongodb://mongo-cluster:27017/auto_me
      - REDIS_URL=redis://redis-cluster:6379
    
  frontend:
    build: ./frontend
    replicas: 2
    depends_on:
      - backend
```

### CDN Configuration
```javascript
// Frontend asset optimization
const config = {
  // Cache static assets
  '/static/': 'public, max-age=31536000',
  
  // Cache API responses briefly
  '/api/templates': 'public, max-age=300',
  '/api/notes': 'private, max-age=60',
  
  // No cache for dynamic content
  '/api/notes/*/generate-report': 'no-cache'
};
```

---

## 📋 SUCCESS CRITERIA

### Deployment Verification Checklist
- [ ] All services running without errors
- [ ] API health checks passing
- [ ] Frontend loading correctly
- [ ] Search functionality working
- [ ] Tagging system operational
- [ ] Template creation/usage working
- [ ] M4A files transcribing successfully
- [ ] Mobile layout responsive
- [ ] Performance metrics within targets
- [ ] Error rates < 1%

### User Acceptance Testing
- [ ] New users can create and use templates
- [ ] Existing users can edit transcripts and save changes
- [ ] Mobile users can access all features
- [ ] Search returns relevant results
- [ ] Tag suggestions appear based on user profile
- [ ] Share functionality works on mobile devices

---

**Deployment Version**: 2.1.0  
**Deployment Date**: September 11, 2025  
**Rollback Time**: < 5 minutes  
**Zero Downtime**: ✅ Supported  
**Backward Compatible**: ✅ All existing features preserved