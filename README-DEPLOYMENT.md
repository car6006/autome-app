# AUTO-ME Application - Deployment Guide

## Overview
AUTO-ME is a comprehensive voice & document capture application with AI-powered analysis capabilities.

## Tech Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Features**: Voice transcription, OCR, AI analysis, file uploads, authentication

## Project Structure
```
/
├── frontend/          # React application
├── backend/           # FastAPI server
├── docs/             # Documentation
├── scripts/          # Deployment scripts
└── README.md         # This file
```

## Prerequisites for Self-Hosting
- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)
- MongoDB database
- OpenAI API key (for AI features)

## Environment Variables Needed

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://your-api-domain.com
```

### Backend (.env)
```
MONGO_URL=mongodb://your-mongodb-connection
OPENAI_API_KEY=your-openai-api-key
JWT_SECRET=your-jwt-secret
DB_NAME=autome_production
```

## Recommended Hosting Providers

### Option 1: Vercel + Railway + MongoDB Atlas
- **Frontend**: Vercel (Free tier)
- **Backend**: Railway (~$5/month)
- **Database**: MongoDB Atlas (Free tier)
- **Total Cost**: ~$5/month

### Option 2: Netlify + Render + MongoDB Atlas  
- **Frontend**: Netlify (Free tier)
- **Backend**: Render (~$7/month)
- **Database**: MongoDB Atlas (Free tier)
- **Total Cost**: ~$7/month

### Option 3: DigitalOcean Droplet
- **Full Stack**: DigitalOcean droplet (~$12/month)
- **Database**: MongoDB Atlas or self-hosted
- **Total Cost**: ~$12-20/month

## Quick Start Commands

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development  
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload
```

## Production Deployment Steps
1. Clone this repository
2. Set up environment variables
3. Deploy frontend to hosting provider
4. Deploy backend to hosting provider
5. Configure MongoDB database
6. Point domain to deployments

## Features Included
- ✅ Voice recording and transcription (OpenAI Whisper)
- ✅ Document OCR scanning
- ✅ AI-powered content analysis
- ✅ File upload and management
- ✅ User authentication (JWT)
- ✅ Professional report generation
- ✅ Batch processing capabilities
- ✅ Mobile-responsive design
- ✅ Analytics and productivity tracking

## Support
This application was developed using the Emergent platform and is now ready for independent deployment.

For technical questions about deployment, refer to the documentation in the `/docs` folder.