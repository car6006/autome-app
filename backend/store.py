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
            
            # Calculate estimated time saved based on content length (more realistic approach)
            estimated_minutes_saved = 0
            
            for note in completed_notes:
                artifacts = note.get("artifacts", {})
                note_kind = note.get("kind", "")
                
                # Get the actual content length
                content_length = 0
                content_text = ""
                
                if note_kind == "audio":
                    # For audio notes, use transcript length
                    content_text = artifacts.get("transcript", "")
                elif note_kind == "photo":
                    # For photo notes, use OCR extracted text length
                    content_text = artifacts.get("text", "")
                elif note_kind == "text":
                    # For text notes, use the original text content
                    content_text = artifacts.get("text", "")
                
                content_length = len(content_text.strip())
                
                if content_length > 0:
                    # Calculate time saved based on content length and note type
                    if note_kind == "audio":
                        # Audio transcription saves significant time vs manual transcription
                        # Assume average person writes 15-20 words per minute by hand
                        # Average word length is ~5 characters, so ~100 characters per minute by hand
                        # Add extra time for listening and pausing audio to transcribe
                        # Also factor in the convenience of not having to manually transcribe
                        hand_writing_time = (content_length / 80) + (content_length / 400) * 5  # slower for transcription + listening time
                        time_saved = max(hand_writing_time, 15)  # minimum 15 minutes for any audio note
                        estimated_minutes_saved += min(time_saved, 480)  # cap at 8 hours per note (reasonable for full-day meetings)
                        
                    elif note_kind == "photo":
                        # OCR saves time vs manual typing from image
                        # Assume slower typing when looking at image and typing
                        # Average typing speed looking at image: ~60 characters per minute
                        hand_typing_time = content_length / 60
                        time_saved = max(hand_typing_time, 5)  # minimum 5 minutes for any photo note
                        estimated_minutes_saved += min(time_saved, 120)  # cap at 2 hours per photo (reasonable for complex documents)
                        
                    elif note_kind == "text":
                        # Text notes save time through AI analysis, formatting, and organization
                        # Assume time saved through AI processing, formatting, and insights
                        # Base calculation on content length but add value from AI features
                        base_writing_time = content_length / 100  # hand writing speed
                        ai_value_added = max(content_length / 200, 3)  # AI analysis and formatting value
                        time_saved = base_writing_time + ai_value_added
                        estimated_minutes_saved += min(time_saved, 180)  # cap at 3 hours per text note (reasonable for long documents)
                else:
                    # Fallback for notes without content (shouldn't happen, but just in case)
                    if note_kind == "audio":
                        estimated_minutes_saved += 10
                    elif note_kind == "photo":
                        estimated_minutes_saved += 3
                    elif note_kind == "text":
                        estimated_minutes_saved += 2
            
            # Round to reasonable precision
            estimated_minutes_saved = round(estimated_minutes_saved, 1)
            
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