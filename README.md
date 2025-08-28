# AUTO-ME PWA - Productivity and Transcription Platform

## 🚀 **Overview**

AUTO-ME is a comprehensive productivity platform featuring voice transcription, photo OCR, note management, and AI-powered analysis. The platform includes a robust large-file audio transcription pipeline with resumable uploads, speaker diarization, and multiple output formats.

## 📋 **Core Features**

### **🎤 Audio Transcription**
- **Large File Support**: Upload files up to 500MB with resumable uploads
- **Real-time Processing**: Live progress tracking through all pipeline stages
- **Speaker Diarization**: Multi-speaker identification and separation
- **Multiple Formats**: TXT, JSON, SRT, VTT, DOCX outputs
- **Language Detection**: Automatic language identification
- **OpenAI Whisper**: Latest `gpt-4o-mini-transcribe` model integration

### **📷 OCR Processing**
- Photo scanning with Google Cloud Vision
- Text extraction and formatting
- Multiple image format support

### **📝 Note Management**
- Real-time collaboration
- Status tracking (uploading, processing, ready)
- Archive and organization features
- Search and filtering capabilities

### **🤖 AI Features**
- Ask AI about content
- Batch report generation
- Professional meeting minutes
- Context-aware responses

### **📊 Analytics**
- Productivity metrics and time tracking
- Processing statistics
- Success rate monitoring
- User-specific dashboards

## 🏗️ **Technical Architecture**

### **Frontend (React + Tailwind CSS)**
```
/frontend/src/
├── App.js                 # Main application router
├── components/
│   ├── LargeFileTranscriptionScreen.js  # Large file processing UI
│   ├── ResumableUpload.js              # Chunked upload component
│   ├── AuthModal.js                    # Authentication UI
│   └── ProfileScreen.js                # User management
├── contexts/
│   └── AuthContext.js                  # Authentication state
└── utils/
    └── themeUtils.js                   # UI theming
```

### **Backend (FastAPI + MongoDB)**
```
/backend/
├── server.py              # Main FastAPI application
├── auth.py               # JWT authentication & user management
├── models.py             # Pydantic data models
├── enhanced_store.py     # Large file transcription storage
├── pipeline_worker.py    # Transcription processing pipeline
├── upload_api.py         # Resumable upload endpoints
├── transcription_api.py  # Job management API
├── cloud_storage.py      # Storage abstraction layer
├── cache_manager.py      # Caching system
├── monitoring.py         # Performance monitoring
├── rate_limiting.py      # API rate limiting
└── webhooks.py          # Event notifications
```

## 🔧 **Installation & Setup**

### **Prerequisites**
- Node.js 18+ and Yarn
- Python 3.9+
- MongoDB
- FFmpeg (for audio processing)

### **Environment Variables**
```bash
# Backend (.env)
MONGO_URL=mongodb://localhost:27017
DB_NAME=autome_db
JWT_SECRET_KEY=your-secure-jwt-secret-key-64-chars-minimum
WHISPER_API_KEY=sk-your-openai-api-key
OPENAI_API_KEY=sk-your-openai-api-key
GCV_API_KEY=your-google-cloud-vision-key
SENDGRID_API_KEY=your-sendgrid-key

# Frontend (.env)
REACT_APP_BACKEND_URL=https://your-backend-url
```

### **Quick Start**
```bash
# Backend
cd backend
pip install -r requirements.txt
python server.py

# Frontend
cd frontend
yarn install
yarn start
```

## 🔒 **Security Features**

### **Authentication & Authorization**
- JWT-based authentication with 24-hour expiry
- Secure password hashing with bcrypt
- Role-based access control
- User session management

### **Input Validation & Protection**
- XSS protection with content security policies
- SQL injection prevention
- Path traversal attack blocking
- Malicious pattern detection and filtering

### **Rate Limiting**
- IP-based rate limiting (60 requests/minute)
- Automatic rate limit reset
- HTTP 429 responses for exceeded limits

### **Security Headers**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` for HTTPS
- `Content-Security-Policy` for XSS prevention

### **URL Security**
- Directory traversal prevention (`../`, `..\\`)
- Malicious URL pattern blocking
- Query parameter sanitization

## 📱 **Mobile Responsiveness**

### **Responsive Design System**
- **Mobile First**: Optimized for 375px+ screens
- **Breakpoint System**: `sm:` (640px+), `md:` (768px+), `lg:` (1024px+)
- **Adaptive Components**: All screens optimized for mobile usage

### **Mobile Optimizations**
- Responsive padding: `p-2 sm:p-4` (8px mobile, 16px desktop)
- Adaptive text sizing: `text-xs sm:text-sm` (12px mobile, 14px desktop)
- Touch-friendly buttons and interactions
- Optimized tab layouts for small screens

## 🎯 **Large File Transcription Pipeline**

### **Stage Processing Flow**
1. **CREATED** → File uploaded, job initialized
2. **VALIDATING** → File format and size validation
3. **TRANSCODING** → Audio normalization (mono, 16kHz)
4. **SEGMENTING** → Smart chunking (20MB max per segment)
5. **DETECTING_LANGUAGE** → Automatic language identification
6. **TRANSCRIBING** → OpenAI Whisper processing
7. **MERGING** → Transcript consolidation with timing
8. **DIARIZING** → Speaker identification and separation
9. **GENERATING_OUTPUTS** → Multi-format generation
10. **COMPLETE** → Results transferred to main notes

### **Error Handling & Recovery**
- **WAV Fallback**: Auto re-encode on 400 errors
- **Checkpoint System**: Resume from failure points  
- **Retry Logic**: 3 attempts with exponential backoff
- **Size Validation**: Prevent oversized API calls

### **Integration with Main Notes**
- Automatic transfer upon completion
- Memory optimization (cleanup duplicate storage)
- AI feature compatibility
- Batch report integration

## 🔌 **API Endpoints**

### **Authentication**
```
POST /api/auth/register     # User registration
POST /api/auth/login        # User login
GET  /api/auth/verify       # Token validation
```

### **Large File Transcription**
```
POST   /api/uploads/sessions              # Create upload session
PUT    /api/uploads/sessions/{id}/chunks/{index}  # Upload chunk
POST   /api/uploads/sessions/{id}/complete # Finalize upload
GET    /api/transcriptions/               # List jobs
POST   /api/transcriptions/{id}/transfer-to-notes  # Transfer to main notes
DELETE /api/transcriptions/{id}           # Delete job
```

### **Notes Management**
```
GET    /api/notes/          # List notes
POST   /api/notes/          # Create note
PUT    /api/notes/{id}      # Update note
DELETE /api/notes/{id}      # Delete note
```

### **Analytics**
```
GET /api/metrics           # Productivity statistics
GET /api/system-metrics    # System performance (admin)
```

## 🚀 **Performance Optimizations**

### **Caching System**
- In-memory cache with Redis fallback
- Checkpoint data caching
- API response caching

### **Storage Management**
- Object storage abstraction (Local/S3 compatible)
- Automatic cleanup after successful transfers
- Optimized file handling for large uploads

### **Processing Efficiency**
- Concurrent chunk processing with rate limiting
- Optimized audio encoding (PCM 16-bit, 16kHz)
- Smart segmentation to minimize API calls

## 📈 **Monitoring & Analytics**

### **System Metrics**
- Processing pipeline performance
- API response times and success rates
- Storage usage and optimization
- User activity patterns

### **User Metrics**
- Time saved through automation
- Content processing statistics
- Success rate tracking
- Productivity insights

## 🔄 **Recent Updates & Fixes**

### **Major Bug Fixes** ✅
- **Stage Routing Bug**: Fixed duplicate stage conditions causing pipeline failures
- **AsyncIO Conflicts**: Resolved event loop issues in `get_file_path_sync`
- **OpenAI Integration**: Updated to `gpt-4o-mini-transcribe` model with proper formats
- **Metrics Duplication**: Resolved duplicate `/metrics` endpoint conflicts

### **Feature Enhancements** ✅
- **Transfer to Notes**: Manual job transfer functionality
- **Memory Optimization**: Automatic cleanup to prevent duplication
- **Mobile UI**: Responsive design improvements across all screens
- **Security Hardening**: Enhanced input validation and rate limiting

### **Model Updates** ✅
- **OpenAI Model**: Upgraded to `gpt-4o-mini-transcribe`
- **Response Format**: Changed from `verbose_json` to `json` for compatibility
- **Size Validation**: 20MB ceiling per API request
- **WAV Fallback**: Automatic re-encoding on format errors

## 🔧 **Troubleshooting**

### **Common Issues**

**1. Jobs Stuck at 60%+ Completion** ✅ FIXED
- **Cause**: Stage routing bug with duplicate conditions
- **Solution**: Fixed pipeline stage progression logic

**2. OpenAI API 400 Errors** ✅ FIXED  
- **Cause**: Wrong model or response format
- **Solution**: Use `gpt-4o-mini-transcribe` with `json` format

**3. Stats Screen Not Loading** ✅ FIXED
- **Cause**: Duplicate `/metrics` endpoints
- **Solution**: Renamed admin endpoint to `/system-metrics`

**4. Mobile UI Issues** ✅ FIXED
- **Cause**: Fixed desktop padding and text sizes
- **Solution**: Implemented responsive design system

### **Performance Tips**
- Use WAV format for best compatibility
- Keep individual files under 2 hours for optimal processing
- Monitor rate limits during bulk uploads
- Clear browser cache if UI updates don't appear

## 📞 **Support & Contribution**

### **Error Reporting**
- Check browser console for frontend errors
- Review backend logs: `tail -f /var/log/supervisor/backend*.log`
- Include request IDs and timestamps in bug reports

### **Development**
- Follow mobile-first responsive design principles
- Implement proper error handling and logging
- Add unit tests for critical functions
- Update documentation with any API changes

---

## 🏆 **System Status: PRODUCTION READY**

✅ **Large File Transcription**: Fully operational with real OpenAI integration  
✅ **Mobile UI**: Responsive across all screen sizes  
✅ **Security**: Hardened against common attacks  
✅ **Integration**: Seamless transfer between systems  
✅ **Performance**: Optimized for large file processing  
✅ **Monitoring**: Complete analytics and metrics  

**Last Updated**: August 28, 2025  
**Version**: 2.0.0  
**Status**: Stable Production Release
