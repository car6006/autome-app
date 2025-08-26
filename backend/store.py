import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
database = client[os.environ['DB_NAME']]

def db():
    return database

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    kind: str  # "audio", "photo", or "text"
    status: str = "uploading"  # uploading, processing, ready, failed
    media_key: Optional[str] = None
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ready_at: Optional[datetime] = None
    auto_emailed: bool = False
    auto_git: bool = False
    user_id: Optional[str] = None  # Link to user who created the note

class NotesStore:
    @staticmethod
    async def create(title: str, kind: str, user_id: Optional[str] = None) -> str:
        """Create a new note and return its ID"""
        note = Note(title=title, kind=kind, user_id=user_id)
        await db()["notes"].insert_one(note.dict())
        return note.id
    
    @staticmethod
    async def get(note_id: str) -> Optional[Dict[str, Any]]:
        """Get a note by ID"""
        return await db()["notes"].find_one({"id": note_id})
    
    @staticmethod
    async def update_media_key(note_id: str, media_key: str):
        """Update the media key for a note"""
        await db()["notes"].update_one(
            {"id": note_id}, 
            {"$set": {"media_key": media_key, "status": "processing"}}
        )
    
    @staticmethod
    async def update_status(note_id: str, status: str):
        """Update note status"""
        update = {"status": status}
        if status == "ready":
            update["ready_at"] = datetime.now(timezone.utc)
        await db()["notes"].update_one({"id": note_id}, {"$set": update})
    
    @staticmethod
    async def set_artifacts(note_id: str, artifacts: Dict[str, Any]):
        """Set processing artifacts for a note"""
        await db()["notes"].update_one(
            {"id": note_id}, 
            {"$set": {"artifacts": artifacts}}
        )
    
    @staticmethod
    async def set_metrics(note_id: str, metrics: Dict[str, Any]):
        """Set processing metrics for a note"""
        await db()["notes"].update_one(
            {"id": note_id}, 
            {"$set": {"metrics": metrics}}
        )
    
    @staticmethod
    async def list_recent(limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List recent notes (filtered by user if provided)"""
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        cursor = db()["notes"].find(query).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=None)