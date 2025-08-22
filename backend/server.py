from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
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
from tasks import enqueue_transcription, enqueue_ocr, enqueue_email, enqueue_git_sync

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AUTO-ME Productivity API", version="1.0.0")

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

# Core endpoints
@api_router.get("/")
async def root():
    return {"message": "AUTO-ME Productivity API", "status": "running"}

@api_router.post("/notes", response_model=Dict[str, str])
async def create_note(note: NoteCreate):
    """Create a new note"""
    note_id = await NotesStore.create(note.title, note.kind)
    return {"id": note_id, "status": "created"}

@api_router.post("/notes/{note_id}/upload")
async def upload_media(
    note_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload media file for a note"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
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

@api_router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    """Get a specific note"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(**note)

@api_router.get("/notes", response_model=List[NoteResponse])
async def list_notes(limit: int = Query(50, le=100)):
    """List recent notes"""
    notes = await NotesStore.list_recent(limit)
    return [NoteResponse(**note) for note in notes]

@api_router.post("/notes/{note_id}/email")
async def send_note_email(
    note_id: str,
    email_req: EmailRequest,
    background_tasks: BackgroundTasks
):
    """Send note content via email"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    background_tasks.add_task(enqueue_email, note_id, email_req.to, email_req.subject)
    return {"message": "Email queued for delivery"}

@api_router.post("/notes/{note_id}/git-sync")
async def sync_note_to_git(
    note_id: str,
    background_tasks: BackgroundTasks
):
    """Sync note to Git repository"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    background_tasks.add_task(enqueue_git_sync, note_id)
    return {"message": "Git sync queued"}

@api_router.get("/metrics")
async def get_metrics(days: int = Query(7, ge=1, le=90)) -> Dict[str, Any]:
    """Get productivity metrics"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get notes from the specified time window
    cursor = db["notes"].find({"created_at": {"$gte": since}})
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
    
    return {
        "window_days": days,
        "notes_total": total,
        "notes_ready": ready,
        "notes_audio": len(audio_notes),
        "notes_photo": len(photo_notes),
        "p95_latency_ms": p95,
        "estimated_minutes_saved": estimated_minutes_saved,
        "success_rate": round(ready / total * 100, 1) if total > 0 else 0
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