import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

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
        """Update the status of a note and trigger productivity metrics update"""
        from datetime import datetime, timezone
        
        # Update the note status
        update = {"status": status}
        if status == "ready":
            update["ready_at"] = datetime.now(timezone.utc)
        result = await db()["notes"].update_one({"id": note_id}, {"$set": update})
        
        # If status is "ready" or "completed", update user productivity metrics
        if status in ["ready", "completed"]:
            # Get the note to find the user
            note = await NotesStore.get(note_id)
            if note and note.get("user_id"):
                await NotesStore.update_user_productivity_metrics(note["user_id"])
        
        return result
    
    @staticmethod
    async def update_user_productivity_metrics(user_id: str):
        """Update productivity metrics for a user based on their completed notes"""
        try:
            # Get all completed notes for this user
            cursor = db()["notes"].find({
                "user_id": user_id,
                "status": {"$in": ["ready", "completed"]}
            })
            completed_notes = await cursor.to_list(None)
            
            # Calculate productivity metrics
            total_notes = len(completed_notes)
            audio_notes = [n for n in completed_notes if n.get("kind") == "audio"]
            photo_notes = [n for n in completed_notes if n.get("kind") == "photo"]
            text_notes = [n for n in completed_notes if n.get("kind") == "text"]
            
            # Calculate estimated time saved (realistic estimates)
            # Audio: Assume 3x time saved (15 min transcription vs 45 min manual typing)
            # Photo: Assume OCR saves 10 minutes vs manual typing
            # Text: Assume 5 minutes saved with AI analysis/formatting
            estimated_minutes_saved = (
                len(audio_notes) * 30 +  # 30 minutes saved per audio note
                len(photo_notes) * 10 +  # 10 minutes saved per photo note  
                len(text_notes) * 5      # 5 minutes saved per text note
            )
            
            # Calculate processing metrics
            processing_times = []
            for note in completed_notes:
                created_at = note.get("created_at")
                updated_at = note.get("updated_at")
                if created_at and updated_at:
                    processing_time = (updated_at - created_at).total_seconds() / 60  # in minutes
                    processing_times.append(processing_time)
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Update user's productivity metrics
            await db()["users"].update_one(
                {"id": user_id},
                {
                    "$set": {
                        "total_time_saved": estimated_minutes_saved,
                        "notes_count": total_notes,
                        "audio_notes_count": len(audio_notes),
                        "photo_notes_count": len(photo_notes),
                        "text_notes_count": len(text_notes),
                        "avg_processing_time_minutes": round(avg_processing_time, 2),
                        "last_metrics_update": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Updated productivity metrics for user {user_id}: {estimated_minutes_saved} minutes saved, {total_notes} notes completed")
            
        except Exception as e:
            logger.error(f"Failed to update productivity metrics for user {user_id}: {str(e)}")
    
    @staticmethod
    async def old_update_status(note_id: str, status: str):
        """Legacy update status method - keeping for compatibility"""
        return await db()["notes"].update_one(
            {"id": note_id}, 
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    
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