from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query, Depends, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone

from store import NotesStore
from storage import store_file
from tasks import enqueue_transcription, enqueue_ocr, enqueue_email, enqueue_git_sync, enqueue_network_diagram_processing, enqueue_iisb_processing
from auth import (
    AuthService, User, UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    Token, get_current_user, get_current_user_optional
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AUTO-ME Productivity API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class NoteCreate(BaseModel):
    title: str
    kind: str  # "audio" or "photo"

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
    return {"id": note_id, "status": "created"}

# Hidden Expeditors Network Diagram Feature
@api_router.post("/notes/network-diagram", response_model=Dict[str, str])
async def create_network_diagram_note(
    note: NoteCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create network diagram note (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    # Override note kind to network_diagram
    note_dict = note.dict()
    note_dict["kind"] = "network_diagram"
    
    user_id = current_user["id"]
    note_id = await NotesStore.create(note_dict["title"], "network_diagram", user_id)
    return {"id": note_id, "status": "created", "feature": "network_diagram"}

@api_router.post("/notes/{note_id}/process-network")
async def process_network_diagram(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """Process network diagram from voice or sketch (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    note = await NotesStore.get(note_id)
    if not note or note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if note.get("kind") != "network_diagram":
        raise HTTPException(status_code=400, detail="Invalid note type for network processing")
    
    # Store the file
    file_content = await file.read()
    media_key = store_file(file_content, file.filename)
    
    # Update note with media key
    await NotesStore.update_media_key(note_id, media_key)
    
    # Queue specialized network processing
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
    """Continue from Network Diagram to IISB analysis (HIDDEN - Expeditors only)"""
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
    
    # Extract client name from network diagram artifacts if available
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
    elif note["kind"] == "network_diagram":
        background_tasks.add_task(enqueue_network_diagram_processing, note_id)
    
    return {"message": "File uploaded successfully", "status": "processing"}

@api_router.post("/upload-file")
async def upload_file_for_scan(
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    file: UploadFile = File(...),
    title: str = Form("Uploaded Document")
):
    """Upload file directly for OCR processing (new scan feature)"""
    
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.pdf'}
    file_ext = os.path.splitext(file.filename or '')[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create note for the upload
    user_id = current_user["id"] if current_user else None
    note_id = await NotesStore.create(title, "photo", user_id)
    
    # Store the file
    file_content = await file.read()
    media_key = store_file(file_content, file.filename)
    
    # Update note with media key
    await NotesStore.update_media_key(note_id, media_key)
    
    # Queue OCR processing
    background_tasks.add_task(enqueue_ocr, note_id)
    
    return {
        "id": note_id,
        "message": "File uploaded successfully",
        "status": "processing",
        "filename": file.filename
    }

@api_router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get a specific note"""
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
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """List notes (user's notes if authenticated, public notes if not)"""
    user_id = current_user["id"] if current_user else None
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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)