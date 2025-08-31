from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query, Depends, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import time
from pathlib import Path
import hashlib
import secrets
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import httpx
import time
from datetime import datetime, timedelta, timezone

from store import NotesStore
from storage import store_file
from tasks import enqueue_transcription, enqueue_ocr, enqueue_email, enqueue_git_sync, enqueue_iisb_processing
from auth import (
    AuthService, User, UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    Token, get_current_user, get_current_user_optional
)

# Import new APIs
from upload_api import router as upload_router
from transcription_api import router as transcription_router
from webhooks import webhook_router

# Phase 4: Production imports
from cloud_storage import storage_manager
from cache_manager import cache_manager
from monitoring import monitoring_service, monitor_endpoint
from rate_limiting import rate_limiter, quota_manager, check_rate_limit, check_user_quota
from webhooks import webhook_manager
from transcription_api import router as transcription_router
from worker_manager import worker_lifespan, get_pipeline_status

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# API Key validation on startup
def validate_api_keys():
    """Validate critical API keys on startup"""
    whisper_key = os.environ.get('WHISPER_API_KEY')
    gcv_key = os.environ.get('GCV_API_KEY')
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    
    warnings = []
    if not whisper_key or whisper_key == 'your_openai_api_key_here':
        warnings.append("⚠️  WHISPER_API_KEY is missing or invalid - audio transcription will fail")
    if not gcv_key or gcv_key == 'your_google_vision_api_key_here':
        warnings.append("⚠️  GCV_API_KEY is missing or invalid - OCR processing will fail")
    if not sendgrid_key or sendgrid_key == 'your_sendgrid_api_key_here':
        warnings.append("⚠️  SENDGRID_API_KEY is missing or invalid - email delivery will fail")
    
    if warnings:
        print("\n" + "="*80)
        print("🚨 API KEY VALIDATION WARNINGS:")
        for warning in warnings:
            print(warning)
        print("="*80 + "\n")
    else:
        print("✅ All API keys appear to be configured")

# Validate keys on startup
validate_api_keys()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AUTO-ME Productivity API", version="2.0.0", lifespan=worker_lifespan)

# 🔒 SECURITY MIDDLEWARE
# Trusted Host Middleware (prevent host header attacks)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"],  # In production: set to specific domains only
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Security headers to prevent common attacks
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Prevent directory traversal and URL manipulation
    if "../" in str(request.url) or "..\\" in str(request.url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    return response

# Input Validation and Rate Limiting
@app.middleware("http")
async def validate_and_rate_limit(request, call_next):
    # Block common malicious patterns
    malicious_patterns = [
        "<script", "javascript:", "vbscript:", "onload=", "onerror=", 
        "../../", "..\\", "%2e%2e", "..", "cmd.exe", "/etc/passwd",
        "DROP TABLE", "SELECT * FROM", "UNION SELECT", "INSERT INTO",
        "<?php", "<%", "{{", "{%", "<%=", "#{", "${", "/*", "*/", "--"
    ]
    
    # Check URL and query parameters
    url_path = str(request.url.path).lower()
    query_string = str(request.url.query).lower()
    
    for pattern in malicious_patterns:
        if pattern in url_path or pattern in query_string:
            logger.warning(f"🚨 Blocked malicious request: {pattern} in {request.url}")
            raise HTTPException(
                status_code=400, 
                detail="Request blocked for security reasons"
            )
    
    # Rate limiting by IP (basic implementation)
    client_ip = request.client.host
    current_time = time.time()
    
    # Simple in-memory rate limiting (60 requests per minute per IP)
    if not hasattr(app.state, "rate_limit"):
        app.state.rate_limit = {}
    
    if client_ip in app.state.rate_limit:
        requests, last_reset = app.state.rate_limit[client_ip]
        if current_time - last_reset > 60:  # Reset every minute
            app.state.rate_limit[client_ip] = (1, current_time)
        elif requests > 60:
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please try again later."
            )
        else:
            app.state.rate_limit[client_ip] = (requests + 1, last_reset)
    else:
        app.state.rate_limit[client_ip] = (1, current_time)
    
    return await call_next(request)

# Global exception handler for enhanced security
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Generic handler for internal server errors to prevent stack trace exposure"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler for enhanced security"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Service temporarily unavailable"}
    )

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class BatchReportRequest(BaseModel):
    note_ids: List[str]
    title: str = "Combined Analysis Report"
    format: str = "professional"  # Options: "professional", "txt", "rtf"

class NoteCreate(BaseModel):
    title: str
    kind: str  # "audio", "photo", or "text"
    text_content: Optional[str] = None

class EmailRequest(BaseModel):
    to: List[str]
    subject: str

class NoteResponse(BaseModel):
    id: str
    title: str
    kind: str
    status: str
    artifacts: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    created_at: datetime
    ready_at: Optional[datetime] = None
    user_id: Optional[str] = None

# Authentication endpoints
@api_router.post("/auth/verify-user")
async def verify_user(request: dict):
    """Verify if user exists for password reset"""
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Clean and normalize email (trim whitespace and convert to lowercase)
    email = email.strip().lower()
    
    # Find user by email
    user = await AuthService.get_user_by_email(email)
    
    if user:
        return {"exists": True, "message": "User found"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@api_router.post("/auth/reset-password")
async def reset_password(request: dict):
    """Reset user password"""
    email = request.get("email")
    new_password = request.get("newPassword")
    
    if not email or not new_password:
        raise HTTPException(status_code=400, detail="Email and new password are required")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    # Find user by email
    user = await AuthService.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    success = await AuthService.update_user_password(user["id"], new_password)
    
    if success:
        return {"message": "Password updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update password")

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    user_id = await AuthService.create_user(user_data)
    user = await AuthService.get_user_by_id(user_id)
    
    # Create access token
    access_token = AuthService.create_access_token(data={"sub": user_id})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user"""
    user = await AuthService.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = AuthService.create_access_token(data={"sub": user["id"]})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)

@api_router.put("/auth/me", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    success = await AuthService.update_user_profile(current_user["id"], profile_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )
    
    # Get updated user
    updated_user = await AuthService.get_user_by_id(current_user["id"])
    return UserResponse(**updated_user)

# Core endpoints (updated to work with authentication)
@api_router.get("/")
async def root():
    return {"message": "AUTO-ME Productivity API v2.0", "status": "running"}

@api_router.post("/notes", response_model=Dict[str, str])
async def create_note(
    note: NoteCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Create a new note (authenticated or anonymous)"""
    user_id = current_user["id"] if current_user else None
    note_id = await NotesStore.create(note.title, note.kind, user_id)
    
    # For text notes, immediately set the content and mark as ready
    if note.kind == "text" and note.text_content:
        artifacts = {"text": note.text_content}
        await NotesStore.set_artifacts(note_id, artifacts)
        await NotesStore.update_status(note_id, "ready")
        return {"id": note_id, "status": "ready"}
    
    return {"id": note_id, "status": "created"}


# Hidden IISB Analysis Feature (Expeditors only)
@api_router.post("/iisb/analyze", response_model=Dict[str, Any])
async def analyze_client_issues(
    request: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """Analyze client supply chain issues using IISB framework (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    client_name = request.get("client_name", "")
    issues_text = request.get("issues_text", "")
    
    if not client_name or not issues_text:
        raise HTTPException(
            status_code=400,
            detail="Client name and issues text are required"
        )
    
    # Process IISB analysis
    from iisb_processor import iisb_processor
    result = await iisb_processor.process_iisb_input(client_name, issues_text)
    
    return result

@api_router.post("/notes/{note_id}/continue-to-iisb")
async def continue_to_iisb_analysis(
    note_id: str,
    request: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """IISB analysis (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    # Verify note exists and belongs to user
    note = await NotesStore.get(note_id)
    if not note or note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Extract client name from note if available
    client_name = request.get("client_name", "")
    if not client_name and note.get("artifacts"):
        # Try to extract client name from note title or artifacts
        client_name = note.get("title", "").split("-")[0].strip() or "Client"
    
    return {
        "note_id": note_id,
        "client_name": client_name,
        "network_completed": note.get("status") == "ready",
        "ready_for_iisb": True,
        "message": "Ready to proceed with IISB analysis"
    }

@api_router.post("/notes/{note_id}/upload")
async def upload_media(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    file: UploadFile = File(...)
):
    """Upload media file for a note"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    # Store the file
    file_content = await file.read()
    media_key = store_file(file_content, file.filename)
    
    # Update note with media key
    await NotesStore.update_media_key(note_id, media_key)
    
    # Queue processing based on note kind
    if note["kind"] == "audio":
        background_tasks.add_task(enqueue_transcription, note_id)
    elif note["kind"] == "photo":
        background_tasks.add_task(enqueue_ocr, note_id)

    
    return {"message": "File uploaded successfully", "status": "processing"}

@api_router.post("/upload-file")
async def upload_file_for_scan(
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    file: UploadFile = File(...),
    title: str = Form("Uploaded Document")
):
    """Upload file directly for processing (scan or audio)"""
    
    # Validate file type
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.pdf'}
    audio_extensions = {'.mp3', '.wav', '.m4a', '.webm', '.ogg', '.mpeg'}
    allowed_extensions = image_extensions | audio_extensions
    
    file_ext = os.path.splitext(file.filename or '')[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: Images ({', '.join(image_extensions)}), Audio ({', '.join(audio_extensions)})"
        )
    
    # Determine note kind based on file type
    if file_ext in audio_extensions or file.content_type.startswith('audio/'):
        note_kind = "audio"
    else:
        note_kind = "photo"
    
    # Create note for the upload
    user_id = current_user["id"] if current_user else None
    note_id = await NotesStore.create(title, note_kind, user_id)
    
    # Store the file
    file_content = await file.read()
    media_key = store_file(file_content, file.filename)
    
    # Update note with media key
    await NotesStore.update_media_key(note_id, media_key)
    
    # Queue appropriate processing
    if note_kind == "audio":
        background_tasks.add_task(enqueue_transcription, note_id)
    else:
        background_tasks.add_task(enqueue_ocr, note_id)
    
    return {
        "id": note_id,
        "message": f"{'Audio' if note_kind == 'audio' else 'File'} uploaded successfully",
        "status": "processing",
        "filename": file.filename,
        "kind": note_kind
    }

@api_router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific note (authentication required)"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    return NoteResponse(**note)

@api_router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_user)
):
    """List user's notes (authentication required)"""
    user_id = current_user["id"]
    notes = await NotesStore.list_recent(limit, user_id)
    return [NoteResponse(**note) for note in notes]

@api_router.post("/notes/{note_id}/email")
async def send_note_email(
    note_id: str,
    email_req: EmailRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Send note content via email"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    background_tasks.add_task(enqueue_email, note_id, email_req.to, email_req.subject)
    return {"message": "Email queued for delivery"}

@api_router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific note (authentication required)"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this note")
    
    # Delete from database
    await db["notes"].delete_one({"id": note_id})
    
    return {"message": "Note deleted successfully"}


@api_router.post("/user/professional-context")
async def update_professional_context(
    context_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user's professional context for personalized AI responses"""
    user_id = current_user["id"]
    
    # Extract professional context fields
    professional_updates = {
        "primary_industry": context_data.get("primary_industry", ""),
        "job_role": context_data.get("job_role", ""),
        "work_environment": context_data.get("work_environment", ""),
        "key_focus_areas": context_data.get("key_focus_areas", []),
        "content_types": context_data.get("content_types", []),
        "analysis_preferences": context_data.get("analysis_preferences", [])
    }
    
    # Update user profile
    await db["users"].update_one(
        {"id": user_id},
        {"$set": {f"profile.{key}": value for key, value in professional_updates.items()}}
    )
    
    return {"message": "Professional context updated successfully", "context": professional_updates}

@api_router.get("/health")
@monitor_endpoint("health_check")
async def health_check():
    """Enhanced health check endpoint with Phase 4 monitoring"""
    try:
        # Check database connection
        await db["users"].find_one({})
        database_health = "healthy"
        
        # Check pipeline status
        try:
            from worker_manager import get_pipeline_status
            pipeline_status = await get_pipeline_status()
            pipeline_health = "healthy" if pipeline_status.get("worker", {}).get("running") else "degraded"
        except Exception as e:
            pipeline_health = "unknown"
            pipeline_status = {"error": str(e)}
        
        # Phase 4: Check production services
        services_health = {
            "database": database_health,
            "api": "running",
            "pipeline": pipeline_health
        }
        
        # Check cache status
        try:
            cache_stats = await cache_manager.get_cache_stats()
            services_health["cache"] = "healthy" if cache_stats.get("enabled") else "disabled"
        except Exception as e:
            services_health["cache"] = "error"
        
        # Check storage status
        try:
            storage_stats = storage_manager.get_usage_stats()
            services_health["storage"] = "healthy"
        except Exception as e:
            services_health["storage"] = "error"
        
        # Check webhook manager
        try:
            webhook_stats = await webhook_manager.get_delivery_stats()
            services_health["webhooks"] = "healthy" if webhook_stats.get("enabled") else "disabled"
        except Exception as e:
            services_health["webhooks"] = "error"
        
        # Get comprehensive metrics
        try:
            metrics = await monitoring_service.get_comprehensive_metrics()
        except Exception as e:
            logger.warning(f"Failed to get comprehensive metrics: {e}")
            metrics = {"error": "metrics_unavailable"}
        
        # Determine overall health
        critical_services = ["database", "api", "pipeline"]
        unhealthy_critical = [s for s in critical_services if services_health.get(s) not in ["healthy", "running"]]
        
        if unhealthy_critical:
            overall_status = "unhealthy"
        elif any(status == "degraded" for status in services_health.values()):
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": services_health,
            "pipeline": pipeline_status,
            "metrics": metrics,
            "version": "Phase 4 Production",
            "uptime_hours": (datetime.now(timezone.utc) - datetime.fromtimestamp(time.time() - 3600, timezone.utc)).total_seconds() / 3600
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy", 
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Health check failed",
                "details": str(e)
            }
        )

@api_router.get("/system-metrics")
@monitor_endpoint("system_metrics")
async def get_system_metrics(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get comprehensive system metrics (Phase 4)"""
    
    # Check if user has access to metrics (admin only in production)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # In production, restrict to admin users
    user_role = current_user.get("role", "user")
    if user_role not in ["admin", "enterprise"]:
        # Return limited metrics for regular users
        try:
            cache_stats = await cache_manager.get_cache_stats()
            storage_stats = storage_manager.get_usage_stats()
            
            return {
                "user_metrics": {
                    "user_id": current_user["id"],
                    "cache_enabled": cache_stats.get("enabled", False),
                    "storage_usage_bytes": storage_stats.get("bytes_stored", 0),
                    "files_stored": storage_stats.get("files_stored", 0)
                },
                "access_level": "limited",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to retrieve user metrics")
    
    # Full metrics for admin users
    try:
        comprehensive_metrics = await monitoring_service.get_comprehensive_metrics()
        
        # Add Phase 4 service metrics
        phase4_metrics = {
            "cache": await cache_manager.get_cache_stats(),
            "storage": storage_manager.get_usage_stats(),
            "rate_limiting": rate_limiter.get_limits_status("system"),
            "webhooks": await webhook_manager.get_delivery_stats()
        }
        
        return {
            **comprehensive_metrics,
            "phase4_services": phase4_metrics,
            "access_level": "full",
            "generated_for": current_user["id"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve system metrics",
                "details": str(e)
            }
        )

@api_router.get("/user/professional-context")
async def get_professional_context(
    current_user: dict = Depends(get_current_user)
):
    """Get user's current professional context"""
    user_id = current_user["id"]
    user = await db["users"].find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = user.get("profile", {})
    
    return {
        "primary_industry": profile.get("primary_industry", ""),
        "job_role": profile.get("job_role", ""),
        "work_environment": profile.get("work_environment", ""),
        "key_focus_areas": profile.get("key_focus_areas", []),
        "content_types": profile.get("content_types", []),
        "analysis_preferences": profile.get("analysis_preferences", [])
    }

from ai_context_processor import ai_context_processor

@api_router.post("/notes/{note_id}/ai-chat")
async def ai_chat_with_note(
    note_id: str,
    request: dict,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """AI conversational agent for note content analysis with dynamic profession-based context"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    content = artifacts.get("transcript") or artifacts.get("text", "")
    
    if not content:
        raise HTTPException(status_code=400, detail="No content available for analysis")
    
    user_question = request.get("question", "").strip()
    if not user_question:
        raise HTTPException(status_code=400, detail="Please provide a question")
    
    try:
        # Use OpenAI with dynamic profession-based context
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Get user profile for context
        user_profile = current_user.get("profile", {}) if current_user else {}
        
        # Generate dynamic prompt based on user's profession and question
        if "meeting" in user_question.lower() or "minutes" in user_question.lower():
            analysis_type = "meeting_minutes"
        elif "insight" in user_question.lower() or "analysis" in user_question.lower():
            analysis_type = "insights"
        elif "summary" in user_question.lower() or "summarize" in user_question.lower():
            analysis_type = "summary"
        else:
            analysis_type = "general"
        
        # Create dynamic prompt with profession context
        base_prompt = ai_context_processor.generate_dynamic_prompt(
            content=content,
            user_profile=user_profile,
            analysis_type=analysis_type
        )
        
        # Add the specific user question
        full_prompt = f"""
        {base_prompt}
        
        User's specific question: {user_question}
        
        Provide a comprehensive, profession-specific response that directly addresses their question.
        """
        
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": 1200,
                    "temperature": 0.3
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            ai_analysis = response.json()
            ai_response = ai_analysis["choices"][0]["message"]["content"]
            
            # Store the conversation in artifacts for reference
            conversations = artifacts.get("ai_conversations", [])
            conversations.append({
                "question": user_question,
                "response": ai_response,
                "context_used": ai_context_processor.get_context_summary(user_profile),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            updated_artifacts = {**artifacts, "ai_conversations": conversations}
            await NotesStore.set_artifacts(note_id, updated_artifacts)
            
            return {
                "response": ai_response,
                "question": user_question,
                "note_title": note["title"],
                "context_summary": ai_context_processor.get_context_summary(user_profile),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        logger.error(f"AI chat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI chat service temporarily unavailable")

@api_router.post("/notes/{note_id}/generate-meeting-minutes")
async def generate_meeting_minutes(
    note_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Generate structured meeting minutes from AI conversations"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    conversations = artifacts.get("ai_conversations", [])
    transcript = artifacts.get("transcript", "")
    
    if not conversations and not transcript:
        raise HTTPException(status_code=400, detail="No content available for meeting minutes generation")
    
    try:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Service not configured")
        
        # Check if user is from Expeditors
        is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
        
        # Combine all available content
        all_content = []
        if transcript:
            all_content.append(transcript)
        
        for conv in conversations:
            response = conv.get("response", "")
            if response:
                all_content.append(response)
        
        combined_content = "\n\n".join(all_content)
        
        # Get user profile for professional context
        user_profile = current_user.get("profile", {}) if current_user else {}
        
        # Generate professional context-aware meeting minutes prompt
        meeting_minutes_prompt = ai_context_processor.generate_dynamic_prompt(
            content=combined_content,
            user_profile=user_profile,
            analysis_type="meeting_minutes"
        )
        
        # Enhanced meeting minutes prompt with professional context
        company_context = "Expeditors International (a global logistics and freight forwarding company)" if is_expeditors_user else "the organization"
        
        prompt = f"""
        {meeting_minutes_prompt}

        ADDITIONAL CONTEXT: You are creating formal meeting minutes for {company_context}.

        FORMATTING INSTRUCTIONS:
        Create comprehensive meeting minutes following this EXACT professional format with NO bold, NO markdown symbols:

        Date: [Extract or use current date]
        Meeting Type: [Determine meeting type from context]

        EXECUTIVE SUMMARY
        Write a brief paragraph summarizing the meeting's purpose, key topics discussed, and overall focus. Emphasize collaborative decision-making and strategic planning.

        OPENING REMARKS AND OBJECTIVES
        Describe how the meeting commenced, welcoming remarks, agenda setting, and primary objectives. Focus on the meeting's purpose and expected outcomes.

        KEY DISCUSSION TOPICS

        [Create appropriate section headers based on content, such as:]
        Performance Review and Analysis
        Strategic Planning and Resource Allocation  
        Customer Engagement and Service Delivery
        Operational Efficiency and Process Improvement
        Team Development and Communication
        Financial Performance Review
        [Add other relevant sections based on actual content]

        For each section, provide detailed narrative explaining:
        - What was discussed
        - Key points raised by participants  
        - Concerns or challenges identified
        - Solutions proposed
        - Decisions made

        DECISIONS AND RESOLUTIONS
        Summarize key decisions made during the meeting and any formal resolutions agreed upon.

        ACTION ITEMS AND NEXT STEPS
        Clearly defined action items with responsibilities assigned. Format as numbered list with specific, actionable descriptions.

        CONCLUSION  
        Professional summary emphasizing successful outcomes, renewed commitments, and next steps for implementation.

        IMPORTANT: 
        - Use professional business language appropriate for corporate meetings
        - Write in narrative form with detailed explanations
        - Include specific details mentioned in the transcript
        - Structure content logically with clear section divisions
        - NO bullet points in main content (only in action items)
        - Focus on business outcomes and strategic initiatives
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            ai_analysis = response.json()
            meeting_minutes = ai_analysis["choices"][0]["message"]["content"]
            
            # Store the meeting minutes in artifacts
            updated_artifacts = {**artifacts, "meeting_minutes": meeting_minutes}
            await NotesStore.set_artifacts(note_id, updated_artifacts)
            
            return {
                "meeting_minutes": meeting_minutes,
                "note_title": note["title"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "note_id": note_id,
                "is_expeditors": is_expeditors_user
            }
    
    except Exception as e:
        logger.error(f"Meeting minutes generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Meeting minutes generation temporarily unavailable")

@api_router.post("/notes/{note_id}/generate-action-items")
async def generate_action_items(
    note_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Generate structured action items table from meeting content"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    transcript = artifacts.get("transcript", "")
    
    if not transcript:
        raise HTTPException(status_code=400, detail="No content available for action items generation")
    
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=503, detail="AI service configuration error")
        
        # Generate action items in table format
        prompt = f"""
        Based on the following meeting transcript, extract and create a comprehensive action items table.

        TRANSCRIPT:
        {transcript}

        INSTRUCTIONS:
        Create a structured action items table with the following format:

        Consolidated Action Items

        No. | Action Item | Start Date | End Date | Status | Responsible Person
        1   | [Detailed action description] | | | |
        2   | [Detailed action description] | | | |
        [etc.]

        REQUIREMENTS:
        - Extract ALL actionable items, decisions, and commitments mentioned
        - Write clear, specific action descriptions
        - Number each item sequentially
        - Leave Start Date, End Date, Status, and Responsible Person columns empty for manual completion
        - Focus on concrete, measurable actions
        - Include both explicit action items and implied commitments from discussions
        - Use professional business language
        - NO markdown formatting, just clean text

        Format the response as a simple table that can be easily copied into a document.
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.2
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            ai_analysis = response.json()
            action_items_table = ai_analysis["choices"][0]["message"]["content"]
            
            # Store the action items in artifacts
            updated_artifacts = {**artifacts, "action_items": action_items_table}
            await NotesStore.set_artifacts(note_id, updated_artifacts)
            
            return {
                "action_items": action_items_table,
                "note_title": note["title"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "note_id": note_id
            }
    
    except Exception as e:
        logger.error(f"Action items generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Action items generation temporarily unavailable")

@api_router.get("/notes/{note_id}/ai-conversations/export")
async def export_ai_conversations(
    note_id: str,
    format: str = Query("pdf", regex="^(pdf|docx|txt|rtf)$"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Export AI conversations/analysis to PDF, Word DOC, TXT, or RTF format"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    
    # Try to get AI conversations first, then fall back to meeting minutes
    ai_conversations = artifacts.get("ai_conversations", [])
    meeting_minutes = artifacts.get("meeting_minutes", "")
    
    if not ai_conversations and not meeting_minutes:
        raise HTTPException(status_code=400, detail="No AI analysis or meeting minutes found. Please generate AI analysis first.")
    
    # Check if user is from Expeditors for branding
    is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
    
    # Clean content function to remove all AI formatting
    def clean_content(text):
        if not text:
            return text
        # Remove markdown formatting
        cleaned = text.replace("**", "").replace("***", "").replace("###", "").replace("##", "").replace("#", "").replace("*", "").replace("_", "")
        # Remove bullet points and section formatting
        lines = cleaned.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line:
                line = line.lstrip('•-*1234567890. ')
                # Remove common AI section headers but keep content
                if not any(header in line.upper() for header in ['ATTENDEES:', 'APOLOGIES:', 'MEETING MINUTES:', 'ACTION ITEMS:', 'KEY INSIGHTS:', 'ASSESSMENTS:', 'RISK ASSESSMENT:', 'NEXT STEPS:']):
                    if line:
                        clean_lines.append(line)
        return '\n'.join(clean_lines)
    
    # Prepare content based on what's available
    content_title = note['title']
    export_content = ""
    
    if ai_conversations:
        export_content = f"AI Content Analysis for: {content_title}\n\n"
        for i, conv in enumerate(ai_conversations, 1):
            question = conv.get("question", "")
            response = conv.get("response", "")
            timestamp = conv.get("timestamp", "")
            
            export_content += f"Question {i}: {question}\n\n"
            export_content += f"AI Analysis:\n{clean_content(response)}\n\n"
            if i < len(ai_conversations):
                export_content += "=" * 50 + "\n\n"
    elif meeting_minutes:
        export_content = f"Meeting Minutes for: {content_title}\n\n{clean_content(meeting_minutes)}"
    
    if format == "txt":
        # Plain text format
        clean_title = note['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"AI_Analysis_{clean_title}.txt"
        
        return Response(
            content=export_content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    elif format == "rtf":
        # RTF format
        clean_title = note['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"AI_Analysis_{clean_title}.rtf"
        
        # RTF header
        rtf_content = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 "
        
        # Convert content to RTF
        rtf_body = export_content.replace("\\", "\\\\").replace("\n", "\\par ")
        rtf_content += rtf_body + "}"
        
        return Response(
            content=rtf_content,
            media_type="application/rtf",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    elif format == "pdf":
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import Color, black
        from io import BytesIO
        import os
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        # Create custom styles
        styles = getSampleStyleSheet()
        
        # Custom styles for professional AI analysis
        title_style = ParagraphStyle(
            'AnalysisTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=1,  # Center
            textColor=Color(234/255, 10/255, 42/255) if is_expeditors_user else black
        )
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=Color(234/255, 10/255, 42/255) if is_expeditors_user else Color(0.2, 0.2, 0.2)
        )
        
        body_style = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=11,
            spaceBefore=6,
            spaceAfter=6,
            leftIndent=0,
            rightIndent=0
        )
        
        story = []
        
        # Add logo if Expeditors user
        if is_expeditors_user:
            logo_path = "/app/backend/expeditors-logo.png"
            if os.path.exists(logo_path):
                try:
                    img = Image(logo_path, width=3*inch, height=1*inch)
                    img.hAlign = 'CENTER'
                    story.append(img)
                    story.append(Spacer(1, 20))
                except Exception as e:
                    print(f"Logo loading error: {e}")
        
        # Title
        title_text = f"AI Content Analysis: {content_title}"
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 20))
        
        # Content
        if ai_conversations:
            for i, conv in enumerate(ai_conversations, 1):
                question = conv.get("question", "")
                response = conv.get("response", "")
                
                # Question
                story.append(Paragraph(f"Question {i}:", heading_style))
                story.append(Paragraph(question, body_style))
                story.append(Spacer(1, 12))
                
                # Response
                story.append(Paragraph("AI Analysis:", heading_style))
                # Clean and process response
                clean_response = clean_content(response)
                story.append(Paragraph(clean_response, body_style))
                
                if i < len(ai_conversations):
                    story.append(Spacer(1, 20))
        elif meeting_minutes:
            clean_minutes = clean_content(meeting_minutes)
            story.append(Paragraph(clean_minutes, body_style))
        
        # Footer
        if is_expeditors_user:
            story.append(Spacer(1, 30))
            story.append(Paragraph("Confidential - Expeditors International", 
                                 ParagraphStyle('Footer', parent=styles['Normal'], 
                                               fontSize=8, alignment=1, textColor=Color(0.5, 0.5, 0.5))))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Create filename
        filename_base = note['title'][:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"AI_Analysis_{filename_base}.pdf"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    elif format == "docx":
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.shared import OxmlElement, qn
        from io import BytesIO
        import os
        
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Add logo if Expeditors user
        if is_expeditors_user:
            logo_path = "/app/backend/expeditors-logo.png"
            if os.path.exists(logo_path):
                try:
                    logo_para = doc.add_paragraph()
                    logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = logo_para.runs[0] if logo_para.runs else logo_para.add_run()
                    run.add_picture(logo_path, width=Inches(3))
                    doc.add_paragraph()  # Spacer
                except Exception as e:
                    print(f"Logo loading error: {e}")
        
        # Title
        if is_expeditors_user:
            title = doc.add_heading('EXPEDITORS INTERNATIONAL', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            subtitle = doc.add_heading(f'AI Content Analysis: {content_title}', level=1)
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            title = doc.add_heading(f'AI Content Analysis: {content_title}', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Content
        if ai_conversations:
            for i, conv in enumerate(ai_conversations, 1):
                question = conv.get("question", "")
                response = conv.get("response", "")
                
                # Question
                doc.add_heading(f'Question {i}:', level=2)
                doc.add_paragraph(question)
                
                # Response
                doc.add_heading('AI Analysis:', level=2)
                clean_response = clean_content(response)
                doc.add_paragraph(clean_response)
                
                if i < len(ai_conversations):
                    doc.add_paragraph()  # Spacer
        elif meeting_minutes:
            clean_minutes = clean_content(meeting_minutes)
            doc.add_paragraph(clean_minutes)
        
        # Footer
        if is_expeditors_user:
            footer_para = doc.add_paragraph()
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_run = footer_para.add_run("Confidential - Expeditors International")
            footer_run.font.size = Pt(8)
        
        # Save to buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        # Create filename
        filename_base = note['title'][:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"AI_Analysis_{filename_base}.docx"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    if format == "pdf":
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import Color, black
        from io import BytesIO
        import os
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        # Create custom styles
        styles = getSampleStyleSheet()
        
        # Custom styles for professional meeting minutes
        title_style = ParagraphStyle(
            'MeetingTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=1,  # Center
            textColor=Color(234/255, 10/255, 42/255) if is_expeditors_user else black
        )
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=Color(234/255, 10/255, 42/255) if is_expeditors_user else black
        )
        
        body_style = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leftIndent=0,
            rightIndent=0
        )
        
        bullet_style = ParagraphStyle(
            'BulletPoint',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leftIndent=20,
            bulletIndent=10
        )
        
        story = []
        
        # Add logo if Expeditors user
        if is_expeditors_user:
            logo_path = "/app/backend/expeditors-logo.png"
            if os.path.exists(logo_path):
                try:
                    logo = Image(logo_path, width=2*inch, height=0.8*inch)
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 20))
                except Exception as e:
                    print(f"Logo loading error: {e}")
        
        # Title
        if is_expeditors_user:
            story.append(Paragraph("EXPEDITORS INTERNATIONAL", title_style))
            story.append(Paragraph("Meeting Minutes", heading_style))
        else:
            story.append(Paragraph("Meeting Minutes", title_style))
        
        story.append(Spacer(1, 20))
        
        # Document info
        story.append(Paragraph(f"<b>Meeting:</b> {note['title']}", body_style))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now(timezone.utc).strftime('%B %d, %Y')}", body_style))
        story.append(Spacer(1, 20))
        
        # Process meeting minutes content
        lines = meeting_minutes.split('\n')
        current_paragraph = ""
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    story.append(Paragraph(current_paragraph, body_style))
                    current_paragraph = ""
                continue
            
            # Check if line is a section header
            section_headers = ['ATTENDEES', 'APOLOGIES', 'MEETING MINUTES', 'ACTION ITEMS', 
                             'KEY INSIGHTS', 'ASSESSMENTS', 'RISK ASSESSMENT', 'NEXT STEPS']
            
            if any(header in line.upper() for header in section_headers):
                if current_paragraph:
                    story.append(Paragraph(current_paragraph, body_style))
                    current_paragraph = ""
                
                story.append(Paragraph(line, heading_style))
                current_section = line.upper()
            
            # Handle bullet points
            elif line.startswith(('•', '-', '*')):
                if current_paragraph:
                    story.append(Paragraph(current_paragraph, body_style))
                    current_paragraph = ""
                
                bullet_text = line[1:].strip()
                story.append(Paragraph(f"• {bullet_text}", bullet_style))
            
            # Regular text
            else:
                if current_paragraph:
                    current_paragraph += " " + line
                else:
                    current_paragraph = line
        
        # Add remaining paragraph
        if current_paragraph:
            story.append(Paragraph(current_paragraph, body_style))
        
        # Footer
        if is_expeditors_user:
            story.append(Spacer(1, 30))
            story.append(Paragraph("Confidential - Expeditors International", 
                                 ParagraphStyle('Footer', parent=styles['Normal'], 
                                               fontSize=8, alignment=1, textColor=Color(0.5, 0.5, 0.5))))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Create filename
        filename_base = note['title'][:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"Meeting_Minutes_{filename_base}.pdf"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    elif format == "docx":
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.shared import OxmlElement, qn
        from io import BytesIO
        import os
        
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Add logo if Expeditors user
        if is_expeditors_user:
            logo_path = "/app/backend/expeditors-logo.png"
            if os.path.exists(logo_path):
                try:
                    logo_para = doc.add_paragraph()
                    logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = logo_para.runs[0] if logo_para.runs else logo_para.add_run()
                    run.add_picture(logo_path, width=Inches(3))
                    doc.add_paragraph()  # Spacer
                except Exception as e:
                    print(f"Logo loading error: {e}")
        
        # Title
        if is_expeditors_user:
            title = doc.add_heading('EXPEDITORS INTERNATIONAL', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            subtitle = doc.add_heading('Meeting Minutes', level=1)
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            title = doc.add_heading('Meeting Minutes', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Document info
        info_para = doc.add_paragraph()
        info_para.add_run("Meeting: ").bold = True
        info_para.add_run(f"{note['title']}")
        info_para.add_run("\nDate: ").bold = True
        info_para.add_run(f"{datetime.now(timezone.utc).strftime('%B %d, %Y')}")
        
        doc.add_paragraph()  # Spacer
        
        # Process meeting minutes content
        lines = meeting_minutes.split('\n')
        current_paragraph = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    doc.add_paragraph(current_paragraph)
                    current_paragraph = ""
                continue
            
            # Check if line is a section header
            section_headers = ['ATTENDEES', 'APOLOGIES', 'MEETING MINUTES', 'ACTION ITEMS', 
                             'KEY INSIGHTS', 'ASSESSMENTS', 'RISK ASSESSMENT', 'NEXT STEPS']
            
            if any(header in line.upper() for header in section_headers):
                if current_paragraph:
                    doc.add_paragraph(current_paragraph)
                    current_paragraph = ""
                
                doc.add_heading(line, level=2)
            
            # Handle bullet points
            elif line.startswith(('•', '-', '*')):
                if current_paragraph:
                    doc.add_paragraph(current_paragraph)
                    current_paragraph = ""
                
                bullet_text = line[1:].strip()
                doc.add_paragraph(bullet_text, style='List Bullet')
            
            # Regular text
            else:
                if current_paragraph:
                    current_paragraph += " " + line
                else:
                    current_paragraph = line
        
        # Add remaining paragraph
        if current_paragraph:
            doc.add_paragraph(current_paragraph)
        
        # Footer
        if is_expeditors_user:
            doc.add_paragraph()
            footer_para = doc.add_paragraph("Confidential - Expeditors International")
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_run = footer_para.runs[0]
            footer_run.font.size = Pt(8)
        
        # Save to buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        # Create filename
        filename_base = note['title'][:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"Meeting_Minutes_{filename_base}.docx"
        
        # Mark note as completed since file was generated
        await NotesStore.update_status(note_id, "completed")
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    else:  # txt format
        content = ""
        
        # Header
        if is_expeditors_user:
            content += "EXPEDITORS INTERNATIONAL\n"
            content += "MEETING MINUTES\n"
            content += "=" * 50 + "\n\n"
        else:
            content += "MEETING MINUTES\n"
            content += "=" * 30 + "\n\n"
        
        content += f"Meeting: {note['title']}\n"
        content += f"Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}\n\n"
        
        # Add meeting minutes content
        content += meeting_minutes
        
        # Footer
        if is_expeditors_user:
            content += "\n\n" + "=" * 50 + "\n"
            content += "Confidential - Expeditors International\n"
        
        # Create filename
        filename_base = note['title'][:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"Meeting_Minutes_{filename_base}.txt"
        
        # Mark note as completed since file was generated
        await NotesStore.update_status(note_id, "completed")
        
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )

@api_router.post("/notes/{note_id}/generate-report")
async def generate_professional_report(
    note_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Generate a professional report with insights and action items"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    content = artifacts.get("transcript") or artifacts.get("text", "")
    
    if not content:
        raise HTTPException(status_code=400, detail="No content available to generate report")
    
    try:
        # Use OpenAI to generate professional insights
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Check if user is from Expeditors
        is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
        
        # Add logo header for Expeditors users
        logo_header = ""
        if is_expeditors_user:
            logo_header = """
==================================================
           EXPEDITORS INTERNATIONAL
           Professional Business Report
==================================================

"""
        
        prompt = f"""
        You are a senior executive assistant creating a professional business report{" for Expeditors International" if is_expeditors_user else ""}. Based on the following content, create a clean, well-formatted business analysis.

        Content to analyze:
        {content}

        Create a comprehensive professional report with these sections. Use clean formatting with clear headings and bullet points - NO MARKDOWN SYMBOLS like ### or **. Format as clean text with proper structure:

        EXECUTIVE SUMMARY
        Write 2-3 sentences highlighting the main points and overall situation

        KEY INSIGHTS  
        List 4-6 important findings as bullet points starting with •

        STRATEGIC RECOMMENDATIONS
        List 3-5 high-impact recommendations as bullet points starting with •

        ACTION ITEMS
        List specific, actionable next steps as bullet points starting with •
        - Include timeframes where appropriate (immediate, 1-3 months, etc.)
        - Be specific about who should be responsible

        PRIORITIES
        Categorize the action items:
        HIGH PRIORITY (next 2 weeks):
        • [list items]
        
        MEDIUM PRIORITY (next 1-3 months):
        • [list items]

        FOLLOW-UP & MONITORING
        List key metrics to track and review schedule as bullet points starting with •

        Use professional business language. Make it executive-ready. Use clear section headings in CAPS, bullet points with •, and write in complete sentences. Do NOT use markdown formatting symbols.
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            ai_analysis = response.json()
            report_content = ai_analysis["choices"][0]["message"]["content"]
            
            # Add logo header for Expeditors users
            if is_expeditors_user:
                report_content = logo_header + report_content
            
            # Store the report in artifacts
            updated_artifacts = {**artifacts, "professional_report": report_content}
            await NotesStore.set_artifacts(note_id, updated_artifacts)
            
            # Mark note as completed since report was generated
            await NotesStore.update_status(note_id, "completed")
            
            return {
                "report": report_content,
                "note_title": note["title"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "note_id": note_id,
                "is_expeditors": is_expeditors_user
            }
    
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Report generation temporarily unavailable")

@api_router.post("/notes/comprehensive-batch-report")
async def generate_comprehensive_batch_report(
    request: BatchReportRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Generate a comprehensive batch report including Meeting Minutes and Action Items"""
    note_ids = request.note_ids
    title = request.title
    format = request.format
    
    if not note_ids:
        raise HTTPException(status_code=400, detail="No notes provided")
    
    try:
        # Collect all content from notes
        all_transcripts = []
        all_meeting_minutes = []
        all_action_items = []
        note_titles = []
        report_date = datetime.now().strftime("%d %B %Y")
        
        for note_id in note_ids:
            note = await NotesStore.get(note_id)
            if not note:
                continue
                
            # Check user permissions
            if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
                continue
                
            artifacts = note.get("artifacts", {})
            transcript = artifacts.get("transcript") or artifacts.get("text", "")
            
            if transcript:
                note_titles.append(note["title"])
                all_transcripts.append({
                    "title": note["title"],
                    "content": transcript,
                    "created_at": note.get("created_at", "")
                })
        
        if not all_transcripts:
            raise HTTPException(status_code=400, detail="No valid content found in selected notes")
        
        # Generate Meeting Minutes for the entire batch
        session_list = "\n\n".join([f"SESSION: {item['title']}\n{item['content']}" for item in all_transcripts])
        combined_transcript = session_list
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=503, detail="AI service configuration error")
        
        # Generate comprehensive meeting minutes matching user's preferred format
        meeting_minutes_prompt = f"""
        Based on the following multi-session meeting transcripts, create meeting minutes following this EXACT format structure (NO markdown, NO bold formatting):

        MEETING SUMMARY

        Date: {report_date}
        Meeting Type: Multi-Session Team Meeting Summary

        EXECUTIVE SUMMARY

        This comprehensive meeting summary covers {len(all_transcripts)} sessions focused on reviewing performance, addressing operational challenges, and planning strategic initiatives. The meetings emphasized open communication, collaborative problem-solving, and clear action planning to achieve organizational objectives.

        OPENING REMARKS AND OBJECTIVES

        The sessions commenced with welcoming remarks from the chairperson, setting clear agendas and expectations for productive discussions. The primary objectives included reviewing current performance metrics, identifying areas for improvement, and establishing clear action plans for upcoming initiatives.

        KEY DISCUSSION TOPICS

        Performance Review and Analysis
        [Extract and summarize performance-related discussions from all sessions]

        Strategic Planning and Resource Allocation
        [Extract and summarize strategic planning discussions from all sessions]

        Customer Engagement and Service Delivery
        [Extract and summarize customer-related discussions from all sessions]

        Operational Efficiency and Process Improvement
        [Extract and summarize operational discussions from all sessions]

        Team Development and Communication
        [Extract and summarize team development discussions from all sessions]

        DECISIONS AND RESOLUTIONS

        [Extract key decisions made across all sessions and their collective impact]

        ACTION ITEMS AND NEXT STEPS

        [Extract action items from all sessions in narrative form, mentioning which session they came from]

        CONCLUSION

        The sessions successfully addressed key operational and strategic topics, resulting in clear action plans and renewed commitment to organizational objectives. All participants agreed to maintain open communication and collaborative approach to achieving established goals.

        TRANSCRIPTS:
        {combined_transcript}
        
        Use professional business language. Structure content logically with clear section divisions. Write in narrative form with detailed explanations. NO bullet points in main content. Focus on business outcomes and strategic initiatives.
        """
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": meeting_minutes_prompt}],
                    "max_tokens": 2500,
                    "temperature": 0.2
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            meeting_minutes_result = response.json()["choices"][0]["message"]["content"]
        
        # Generate consolidated action items table
        action_items_prompt = f"""
        Based on these multi-session meeting transcripts, create a comprehensive action items table:

        TRANSCRIPTS:
        {combined_transcript}

        Create a consolidated action items table with this format:

        CONSOLIDATED ACTION ITEMS - MULTI-SESSION REPORT

        No. | Action Item | Session Source | Start Date | End Date | Priority | Responsible Person
        1   | [Detailed action description] | [Session name] | | | | |
        2   | [Detailed action description] | [Session name] | | | | |
        [etc.]

        Extract ALL actionable items from ALL sessions. Include:
        - Cross-session dependencies and connections
        - Strategic priorities that span multiple sessions  
        - Follow-up items from previous sessions
        - New commitments and deliverables
        - Resource allocation and planning items

        Leave Date, Priority, and Responsible Person columns empty for manual completion.
        Use professional language. NO markdown formatting.
        """
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": action_items_prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.2
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            action_items_result = response.json()["choices"][0]["message"]["content"]
        
        # Combine everything into comprehensive report
        if format == "ai":
            # Full AI-enhanced format
            session_appendix = "\n".join([f"\nSESSION: {item['title']}\n{'-' * 50}\n{item['content']}" for item in all_transcripts])
            final_content = f"""COMPREHENSIVE MULTI-SESSION REPORT
{title}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sessions: {len(all_transcripts)}

{meeting_minutes_result}

---

{action_items_result}

---

APPENDIX: SESSION TRANSCRIPTS
{session_appendix}
"""
        
        else:
            # Clean format for TXT/RTF - Simple notes without speaker confusion
            clean_content = f"""{title}
Multi-Session Report
Generated: {report_date}
Sessions: {len(all_transcripts)}

"""
            # Just include the actual content without complex formatting
            for item in all_transcripts:
                clean_content += f"""
SESSION: {item['title']}
{'-' * 50}
{item['content']}

"""
            
            final_content = clean_content
        
        # Handle RTF format
        if format == "rtf":
            title_escaped = title.replace('&', '\\&')
            content_escaped = final_content.replace('&', '\\&').replace('\n', '\\par ')
            rtf_content = f"""{{\\rtf1\\ansi\\deff0 {{\\fonttbl {{\\f0 Times New Roman;}}}}
\\f0\\fs24 
\\b {title_escaped}\\b0\\par
\\par
{content_escaped}
}}"""
            final_content = rtf_content
        
        filename = f"{title.replace(' ', '_')}_Comprehensive_Report.{format if format != 'ai' else 'txt'}"
        
        return {
            "content": final_content,
            "filename": filename,
            "note_count": len(all_transcripts),
            "title": title,
            "format": format,
            "sessions": note_titles,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Comprehensive batch report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Comprehensive report generation temporarily unavailable")

@api_router.post("/notes/batch-report")
async def generate_batch_report(
    request: BatchReportRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Generate a combined report from multiple notes in multiple formats"""
    note_ids = request.note_ids
    title = request.title
    format = request.format
    
    if not note_ids:
        raise HTTPException(status_code=400, detail="No notes provided")
    
    try:
        combined_content = []
        note_titles = []
        
        # Collect content from all notes
        for note_id in note_ids:
            note = await NotesStore.get(note_id)
            if not note:
                continue
                
            # Check user permissions
            if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
                continue
                
            artifacts = note.get("artifacts", {})
            content = artifacts.get("transcript") or artifacts.get("text", "")
            
            if content:
                note_titles.append(note["title"])
                if format in ["txt", "rtf"]:
                    # Clean content for raw formats
                    clean_content = content.replace("**", "").replace("###", "").replace("##", "").replace("#", "").replace("*", "").replace("_", "")
                    lines = clean_content.split('\n')
                    clean_lines = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            line = line.lstrip('•-*1234567890. ')
                            if not any(header in line.upper() for header in ['ATTENDEES:', 'APOLOGIES:', 'MEETING MINUTES:', 'ACTION ITEMS:', 'KEY INSIGHTS:', 'ASSESSMENTS:', 'RISK ASSESSMENT:', 'NEXT STEPS:']):
                                if line:
                                    clean_lines.append(line)
                    combined_content.append(f"{note['title']}\n{chr(61)*len(note['title'])}\n\n{chr(10).join(clean_lines)}")
                else:
                    combined_content.append(f"## {note['title']}\n{content}")
        
        if not combined_content:
            raise HTTPException(status_code=400, detail="You can only create batch reports with your own notes. Please select notes you created.")
        
        # Handle different export formats
        if format == "txt":
            # Plain text format - completely clean
            content_text = f"{title}\n{'='*len(title)}\n\n"
            content_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content_text += f"Notes included: {len(note_titles)}\n\n"
            content_text += "\n\n".join(combined_content)
            
            # Mark all accessible notes as completed
            for note_id in note_ids:
                note = await NotesStore.get(note_id)
                if note and (not current_user or not note.get("user_id") or note.get("user_id") == current_user["id"]):
                    await NotesStore.update_status(note_id, "completed")
            
            return {
                "format": "txt",
                "content": content_text,
                "filename": f"{title.replace(' ', '_')}.txt",
                "note_count": len(note_titles),
                "source_notes": note_titles
            }
        
        elif format == "rtf":
            # RTF format - clean and professional
            content_text = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 "
            content_text += f"\\b\\fs32 {title}\\b0\\fs24\\par\\par "
            content_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\par "
            content_text += f"Notes included: {len(note_titles)}\\par\\par "
            
            for section in combined_content:
                # Convert to RTF format
                rtf_section = section.replace("\\", "\\\\").replace("\n", "\\par ")
                content_text += rtf_section + "\\par\\par "
            
            content_text += "}"
            
            # Mark all accessible notes as completed
            for note_id in note_ids:
                note = await NotesStore.get(note_id)
                if note and (not current_user or not note.get("user_id") or note.get("user_id") == current_user["id"]):
                    await NotesStore.update_status(note_id, "completed")
            
            return {
                "format": "rtf", 
                "content": content_text,
                "filename": f"{title.replace(' ', '_')}.rtf",
                "note_count": len(note_titles),
                "source_notes": note_titles
            }
        
        else:  # Professional AI report format (default)
            # Generate comprehensive AI report
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="AI service not configured")
            
            full_content = "\n\n".join(combined_content)
            
            # Get user profile for professional context
            user_profile = current_user.get("profile", {}) if current_user else {}
            
            # Check if user is from Expeditors
            is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
            
            # Add logo header for Expeditors users
            logo_header = ""
            if is_expeditors_user:
                logo_header = """
==================================================
           EXPEDITORS INTERNATIONAL
        Comprehensive Business Analysis Report
==================================================

"""
            
            # Generate professional context-aware prompt for batch report
            batch_prompt = ai_context_processor.generate_dynamic_prompt(
                content=full_content,
                user_profile=user_profile,
                analysis_type="strategic_planning"
            )
            
            prompt = f"""
            {logo_header}
            You are a senior business analyst creating a comprehensive strategic report from multiple business documents.
            
            ANALYSIS REQUIREMENTS:
            - Synthesize information across ALL provided documents
            - Identify cross-cutting themes, patterns, and strategic insights
            - Provide executive-level recommendations with clear rationale
            - Structure the analysis professionally for C-level stakeholders
            - Focus on actionable insights that drive business value
            
            DOCUMENTS TO ANALYZE:
            {full_content}
            
            {batch_prompt}
            
            Provide a comprehensive business analysis that executives can immediately act upon. Structure with clear sections and actionable recommendations.
            """
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": "You are a senior business analyst and strategic advisor."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 4000,
                        "temperature": 0.3
                    },
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                response.raise_for_status()
                
                ai_response = response.json()
                report_content = ai_response["choices"][0]["message"]["content"]
                
                # Add Expeditors branding if applicable
                if is_expeditors_user:
                    report_content = logo_header + report_content
                
                # Mark all accessible notes as completed
                for note_id in note_ids:
                    note = await NotesStore.get(note_id)
                    if note and (not current_user or not note.get("user_id") or note.get("user_id") == current_user["id"]):
                        await NotesStore.update_status(note_id, "completed")
                
                return {
                    "format": "professional",
                    "report": report_content,
                    "title": title,
                    "generated_at": datetime.now().isoformat(),
                    "note_count": len(note_titles),
                    "source_notes": note_titles,
                    "user_profile": user_profile
                }
        
    except Exception as e:
        logger.error(f"Batch report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch report generation temporarily unavailable")

@api_router.get("/notes/{note_id}/export")
async def export_note(
    note_id: str,
    format: str = Query("txt", regex="^(txt|md|json|rtf)$"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Export note in various formats (txt, md, json, rtf)"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    
    if format == "json":
        # Convert datetime to string for JSON serialization
        export_data = {
            "id": note["id"],
            "title": note["title"],
            "kind": note["kind"],
            "created_at": note["created_at"].isoformat() if hasattr(note["created_at"], 'isoformat') else str(note["created_at"]),
            "artifacts": artifacts
        }
        # Mark note as completed since file was exported
        if current_user:  # Only update status for authenticated users
            await NotesStore.update_status(note_id, "completed")
        
        # Use note title for filename
        clean_title = note['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{clean_title}.json"
        
        return JSONResponse(
            content=export_data,
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    elif format == "md":
        content = f"# {note['title']}\n\n"
        content += f"**Created:** {note['created_at']}\n"
        content += f"**Type:** {note['kind']}\n\n"
        
        if artifacts.get("transcript"):
            content += "## Transcript\n\n"
            content += artifacts["transcript"] + "\n\n"
        
        if artifacts.get("text"):
            content += "## OCR Text\n\n"
            content += artifacts["text"] + "\n\n"
        
        if artifacts.get("summary"):
            content += "## Summary\n\n"
            content += artifacts["summary"] + "\n\n"
        
        if artifacts.get("actions"):
            content += "## Action Items\n\n"
            for action in artifacts["actions"]:
                content += f"- {action}\n"
        
        # Mark note as completed since file was exported
        if current_user:  # Only update status for authenticated users
            await NotesStore.update_status(note_id, "completed")
        
        # Use note title for filename
        clean_title = note['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{clean_title}.md"
        
        return Response(
            content=content, 
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    elif format == "rtf":
        # Clean RTF format - completely raw transcript without any AI formatting
        clean_title = note['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{clean_title}.rtf"
        
        # RTF Header
        content = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}\\f0\\fs24 "
        
        # Title (minimal formatting)
        content += f"\\b\\fs28 {note['title']}\\b0\\fs24\\par\\par "
        
        # Metadata  
        content += f"Created: {note['created_at']}\\par "
        content += f"Type: {note['kind']}\\par\\par "
        
        # Raw transcript content - completely clean
        if artifacts.get("transcript"):
            # Remove ALL AI formatting: markdown, bullets, headers, etc.
            raw_transcript = artifacts["transcript"]
            
            # Remove markdown formatting
            raw_transcript = raw_transcript.replace("**", "")
            raw_transcript = raw_transcript.replace("###", "")
            raw_transcript = raw_transcript.replace("##", "")
            raw_transcript = raw_transcript.replace("#", "")
            raw_transcript = raw_transcript.replace("*", "")
            raw_transcript = raw_transcript.replace("_", "")
            
            # Remove bullet points and list formatting
            lines = raw_transcript.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    # Remove bullet points, dashes, numbers
                    line = line.lstrip('•-*1234567890. ')
                    if line:  # Only add non-empty lines
                        clean_lines.append(line)
            
            # Join with simple line breaks
            clean_content = ' '.join(clean_lines)
            
            # Convert to RTF format
            content += clean_content.replace("\n", " ").replace("\\", "\\\\") + "\\par\\par "
        
        # Raw OCR text if available
        if artifacts.get("text"):
            raw_text = artifacts["text"]
            # Clean text completely
            raw_text = raw_text.replace("**", "").replace("###", "").replace("##", "").replace("#", "").replace("*", "").replace("_", "")
            content += raw_text.replace("\n", " ").replace("\\", "\\\\") + "\\par\\par "
        
        # RTF Footer
        content += "}"
        
        # Mark note as completed since file was exported
        if current_user:
            await NotesStore.update_status(note_id, "completed")
        
        return Response(
            content=content, 
            media_type="application/rtf",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    else:  # txt format - completely clean raw content
        content = f"{note['title']}\n"
        content += "=" * len(note['title']) + "\n\n"
        content += f"Created: {note['created_at']}\n"
        content += f"Type: {note['kind']}\n\n"
        
        # Raw transcript - completely clean without any AI formatting
        if artifacts.get("transcript"):
            raw_transcript = artifacts["transcript"]
            
            # Remove ALL formatting markers
            raw_transcript = raw_transcript.replace("**", "")
            raw_transcript = raw_transcript.replace("###", "") 
            raw_transcript = raw_transcript.replace("##", "")
            raw_transcript = raw_transcript.replace("#", "")
            raw_transcript = raw_transcript.replace("*", "")
            raw_transcript = raw_transcript.replace("_", "")
            
            # Remove bullet points and list formatting
            lines = raw_transcript.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    # Remove bullet points, dashes, numbers, section headers
                    line = line.lstrip('•-*1234567890. ')
                    # Remove common AI section headers
                    if not any(header in line.upper() for header in ['ATTENDEES:', 'APOLOGIES:', 'MEETING MINUTES:', 'ACTION ITEMS:', 'KEY INSIGHTS:', 'ASSESSMENTS:', 'RISK ASSESSMENT:', 'NEXT STEPS:']):
                        if line:  # Only add non-empty meaningful lines
                            clean_lines.append(line)
            
            # Join as continuous text with natural breaks
            content += '\n'.join(clean_lines) + "\n\n"
        
        # Raw OCR text if available
        if artifacts.get("text"):
            raw_text = artifacts["text"]
            # Clean completely - no AI formatting
            raw_text = raw_text.replace("**", "").replace("###", "").replace("##", "").replace("#", "").replace("*", "").replace("_", "")
            content += raw_text + "\n\n"
        
        # Mark note as completed since file was exported
        if current_user:
            await NotesStore.update_status(note_id, "completed")
        
        # Use note title for filename
        clean_title = note['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{clean_title}.txt"
        
        return Response(
            content=content, 
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )

@api_router.post("/notes/{note_id}/git-sync")
async def sync_note_to_git(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Sync note to Git repository"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    background_tasks.add_task(enqueue_git_sync, note_id)
    return {"message": "Git sync queued"}

@api_router.get("/metrics")
async def get_metrics(
    days: int = Query(7, ge=1, le=90),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get productivity metrics (user-specific if authenticated)"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Build query based on authentication
    query = {"created_at": {"$gte": since}}
    if current_user:
        query["user_id"] = current_user["id"]
    
    # Get notes from the specified time window
    cursor = db["notes"].find(query)
    notes = await cursor.to_list(None)
    
    total = len(notes)
    ready = sum(1 for n in notes if n.get("status") == "ready")
    latencies = [n.get("metrics", {}).get("latency_ms") for n in notes if n.get("metrics", {}).get("latency_ms")]
    
    p95 = None
    if latencies:
        sorted_latencies = sorted(latencies)
        idx = int(0.95 * len(sorted_latencies)) - 1
        if idx >= 0:
            p95 = sorted_latencies[idx]
    
    # Calculate estimated time saved (rough estimates)
    audio_notes = [n for n in notes if n.get("kind") == "audio" and n.get("status") == "ready"]
    photo_notes = [n for n in notes if n.get("kind") == "photo" and n.get("status") == "ready"]
    
    # Rough time savings estimates
    estimated_minutes_saved = len(audio_notes) * 15 + len(photo_notes) * 10
    
    # Update user's total time saved if authenticated
    if current_user:
        await db["users"].update_one(
            {"id": current_user["id"]},
            {"$set": {"total_time_saved": estimated_minutes_saved, "notes_count": total}}
        )
    
    return {
        "window_days": days,
        "notes_total": total,
        "notes_ready": ready,
        "notes_audio": len(audio_notes),
        "notes_photo": len(photo_notes),
        "p95_latency_ms": p95,
        "estimated_minutes_saved": estimated_minutes_saved,
        "success_rate": round(ready / total * 100, 1) if total > 0 else 0,
        "user_authenticated": current_user is not None
    }

# Include the router in the main app
app.include_router(api_router)
app.include_router(upload_router, prefix="/api")  # New resumable upload API
app.include_router(transcription_router, prefix="/api")  # New transcription job API
app.include_router(webhook_router, prefix="/api")  # Phase 4: Webhook management API

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Start pipeline worker and Phase 4 services on server startup"""
    from worker_manager import start_pipeline_worker
    
    # Start pipeline worker
    logger.info("🚀 Starting pipeline worker...")
    try:
        await start_pipeline_worker()
        logger.info("✅ Pipeline worker started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start pipeline worker: {e}")
    
    # Phase 4: Start production services
    logger.info("🚀 Starting Phase 4 production services...")
    
    # Start monitoring service
    try:
        await monitoring_service.start_monitoring()
        logger.info("✅ Monitoring service started")
    except Exception as e:
        logger.error(f"❌ Failed to start monitoring service: {e}")
    
    # Start webhook manager
    try:
        await webhook_manager.start()
        logger.info("✅ Webhook manager started")
    except Exception as e:
        logger.error(f"❌ Failed to start webhook manager: {e}")
    
    logger.info("🎉 All Phase 4 services started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Shutdown database, pipeline worker, and Phase 4 services"""
    from worker_manager import stop_pipeline_worker
    
    # Stop pipeline worker
    logger.info("🛑 Stopping pipeline worker...")
    try:
        await stop_pipeline_worker()
        logger.info("✅ Pipeline worker stopped successfully")
    except Exception as e:
        logger.error(f"❌ Error stopping pipeline worker: {e}")
    
    # Phase 4: Stop production services
    logger.info("🛑 Stopping Phase 4 production services...")
    
    # Stop webhook manager
    try:
        await webhook_manager.stop()
        logger.info("✅ Webhook manager stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping webhook manager: {e}")
    
    # Stop monitoring service
    try:
        await monitoring_service.stop_monitoring()
        logger.info("✅ Monitoring service stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping monitoring service: {e}")
    
    client.close()
    logger.info("🎉 All services stopped successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)