"""
Enhanced store for large-file transcription pipeline
Extends existing NotesStore with new models
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import logging

from models import (
    UploadSession, TranscriptionJob, TranscriptionAsset, 
    TranscriptionStage, TranscriptionStatus
)

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB connection (reuse existing)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
database = client[os.environ['DB_NAME']]

class UploadSessionStore:
    """Store for managing resumable upload sessions"""
    
    collection = database["upload_sessions"]
    
    @staticmethod
    async def create_session(session: UploadSession) -> UploadSession:
        """Create new upload session"""
        await UploadSessionStore.collection.insert_one(session.dict())
        return session
    
    @staticmethod
    async def get_session(upload_id: str) -> Optional[UploadSession]:
        """Get upload session by ID"""
        doc = await UploadSessionStore.collection.find_one({"id": upload_id})
        if doc:
            return UploadSession(**doc)
        return None
    
    @staticmethod
    async def update_chunks_uploaded(upload_id: str, chunk_index: int):
        """Mark chunk as uploaded"""
        await UploadSessionStore.collection.update_one(
            {"id": upload_id},
            {"$addToSet": {"chunks_uploaded": chunk_index}}
        )
    
    @staticmethod
    async def complete_session(upload_id: str, storage_key: str, sha256: Optional[str] = None):
        """Mark session as completed"""
        update_data = {
            "status": "completed",
            "storage_key": storage_key,
            "completed_at": datetime.now(timezone.utc)
        }
        if sha256:
            update_data["sha256"] = sha256
            
        await UploadSessionStore.collection.update_one(
            {"id": upload_id},
            {"$set": update_data}
        )
    
    @staticmethod
    async def get_chunks_uploaded(upload_id: str) -> List[int]:
        """Get list of uploaded chunks"""
        session = await UploadSessionStore.get_session(upload_id)
        return session.chunks_uploaded if session else []
    
    @staticmethod
    async def cleanup_expired_sessions():
        """Clean up expired upload sessions"""
        cutoff = datetime.now(timezone.utc)
        result = await UploadSessionStore.collection.delete_many({
            "status": {"$ne": "completed"},
            "expires_at": {"$lt": cutoff}
        })
        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} expired upload sessions")
    
    @staticmethod
    async def delete_session(upload_id: str) -> bool:
        """Delete upload session"""
        result = await UploadSessionStore.collection.delete_one({"id": upload_id})
        return result.deleted_count > 0

class TranscriptionJobStore:
    """Store for managing transcription jobs and pipeline state"""
    
    collection = database["transcription_jobs"]
    
    @staticmethod
    async def create_job(job: TranscriptionJob) -> TranscriptionJob:
        """Create new transcription job"""
        await TranscriptionJobStore.collection.insert_one(job.dict())
        return job
    
    @staticmethod
    async def get_job(job_id: str) -> Optional[TranscriptionJob]:
        """Get job by ID"""
        doc = await TranscriptionJobStore.collection.find_one({"id": job_id})
        if doc:
            return TranscriptionJob(**doc)
        return None
    
    @staticmethod
    async def update_job_stage(job_id: str, stage: TranscriptionStage, progress: float = 0.0):
        """Update job stage and progress"""
        update_data = {
            "current_stage": stage.value,
            "progress": progress,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Set started_at on first progress update
        if stage != TranscriptionStage.CREATED:
            update_data["started_at"] = datetime.now(timezone.utc)
            
        # Set status based on stage
        if stage == TranscriptionStage.COMPLETE:
            update_data["status"] = TranscriptionStatus.COMPLETE.value
            update_data["completed_at"] = datetime.now(timezone.utc)
        elif stage == TranscriptionStage.FAILED:
            update_data["status"] = TranscriptionStatus.FAILED.value
        elif stage not in [TranscriptionStage.CREATED]:
            update_data["status"] = TranscriptionStatus.PROCESSING.value
        
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {"$set": update_data}
        )
    
    @staticmethod
    async def update_stage_progress(job_id: str, stage: TranscriptionStage, progress: float):
        """Update progress for specific stage and overall job progress"""
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {
                "$set": {
                    f"stage_progress.{stage.value}": progress,
                    "progress": progress,  # Also update overall progress
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    
    @staticmethod
    async def set_stage_checkpoint(job_id: str, stage: TranscriptionStage, checkpoint_data: Dict[str, Any]):
        """Save checkpoint data for resuming"""
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {
                "$set": {
                    f"stage_checkpoints.{stage.value}": checkpoint_data,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    
    @staticmethod
    async def get_stage_checkpoint(job_id: str, stage: TranscriptionStage) -> Optional[Dict[str, Any]]:
        """Get checkpoint data for stage"""
        job = await TranscriptionJobStore.get_job(job_id)
        logger.info(f"🔍 Checkpoint retrieval for {job_id}, stage {stage.value}")
        
        if job:
            logger.info(f"   Job found, stage_checkpoints type: {type(job.stage_checkpoints)}")
            logger.info(f"   Available checkpoints: {list(job.stage_checkpoints.keys()) if job.stage_checkpoints else 'None'}")
            
            if job.stage_checkpoints:
                checkpoint_data = job.stage_checkpoints.get(stage.value)
                if checkpoint_data:
                    logger.info(f"✅ Found checkpoint for {stage.value}: {list(checkpoint_data.keys())}")
                    return checkpoint_data
                else:
                    logger.warning(f"❌ No checkpoint data found for stage {stage.value}")
            else:
                logger.warning(f"❌ No stage_checkpoints field in job")
        else:
            logger.error(f"❌ Job {job_id} not found")
        return None
    
    @staticmethod
    async def record_stage_duration(job_id: str, stage: TranscriptionStage, duration_seconds: float):
        """Record how long a stage took"""
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {
                "$set": {
                    f"stage_durations.{stage.value}": duration_seconds,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    
    @staticmethod
    async def set_job_error(job_id: str, error_code: str, error_message: str):
        """Set job error state"""
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": TranscriptionStatus.FAILED.value,
                    "current_stage": TranscriptionStage.FAILED.value,
                    "error_code": error_code,
                    "error_message": error_message,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$inc": {"retry_count": 1}
            }
        )
    
    @staticmethod
    async def set_job_results(job_id: str, results: Dict[str, Any]):
        """Set job results (language, confidence, etc.)"""
        update_data = {
            "updated_at": datetime.now(timezone.utc)
        }
        update_data.update(results)
        
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {"$set": update_data}
        )
    
    @staticmethod
    async def update_job_status(job_id: str, status: TranscriptionStatus):
        """Update job status"""
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    
    @staticmethod
    async def list_jobs_for_user(user_id: str, limit: int = 50) -> List[TranscriptionJob]:
        """List jobs for user"""
        cursor = TranscriptionJobStore.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=None)
        return [TranscriptionJob(**doc) for doc in docs]
    
    @staticmethod
    async def list_jobs_by_status(status: TranscriptionStatus, limit: int = 100) -> List[TranscriptionJob]:
        """List jobs by status for worker processing"""
        cursor = TranscriptionJobStore.collection.find({"status": status.value}).sort("created_at", 1).limit(limit)
        docs = await cursor.to_list(length=None)
        return [TranscriptionJob(**doc) for doc in docs]
    
    @staticmethod
    async def get_jobs_ready_for_retry() -> List[TranscriptionJob]:
        """Get failed jobs that can be retried"""
        cursor = TranscriptionJobStore.collection.find({
            "status": TranscriptionStatus.FAILED.value,
            "retry_count": {"$lt": 3}  # max_retries
        }).sort("created_at", 1).limit(50)
        docs = await cursor.to_list(length=None)
        return [TranscriptionJob(**doc) for doc in docs]
    
    @staticmethod
    async def delete_job(job_id: str):
        """Delete job from database"""
        result = await TranscriptionJobStore.collection.delete_one({"id": job_id})
        return result.deleted_count > 0

class TranscriptionAssetStore:
    """Store for managing transcription output assets"""
    
    collection = database["transcription_assets"]
    
    @staticmethod
    async def create_asset(asset: TranscriptionAsset) -> TranscriptionAsset:
        """Create new asset record"""
        await TranscriptionAssetStore.collection.insert_one(asset.dict())
        return asset
    
    @staticmethod
    async def get_assets_for_job(job_id: str) -> List[TranscriptionAsset]:
        """Get all assets for a job"""
        cursor = TranscriptionAssetStore.collection.find({"job_id": job_id})
        docs = await cursor.to_list(length=None)
        return [TranscriptionAsset(**doc) for doc in docs]
    
    @staticmethod
    async def get_asset_by_kind(job_id: str, kind: str) -> Optional[TranscriptionAsset]:
        """Get specific asset type for job"""
        doc = await TranscriptionAssetStore.collection.find_one({
            "job_id": job_id,
            "kind": kind
        })
        if doc:
            return TranscriptionAsset(**doc)
        return None
    
    @staticmethod
    async def list_assets_by_job(job_id: str) -> List[TranscriptionAsset]:
        """List all assets for a job (alias for get_assets_for_job)"""
        return await TranscriptionAssetStore.get_assets_for_job(job_id)
    
    @staticmethod
    async def delete_assets_by_job(job_id: str) -> int:
        """Delete all assets for a job"""
        result = await TranscriptionAssetStore.collection.delete_many({"job_id": job_id})
        return result.deleted_count

# Utility functions for backward compatibility
class EnhancedNotesStore:
    """Enhanced version of NotesStore that bridges old and new systems"""
    
    @staticmethod
    async def create_from_transcription_job(job: TranscriptionJob) -> str:
        """Create a Note record from TranscriptionJob for backward compatibility"""
        from store import NotesStore
        
        # Create note in old format
        note_id = await NotesStore.create(
            title=job.filename,
            kind="audio",
            user_id=job.user_id
        )
        
        # Store job_id reference for linking
        await database["notes"].update_one(
            {"id": note_id},
            {"$set": {"transcription_job_id": job.id}}
        )
        
        return note_id
    
    @staticmethod
    async def sync_job_to_note(job_id: str):
        """Sync TranscriptionJob status to Note record"""
        from store import NotesStore
        
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            return
        
        # Find corresponding note
        note_doc = await database["notes"].find_one({"transcription_job_id": job_id})
        if not note_doc:
            return
        
        note_id = note_doc["id"]
        
        # Map job status to note status
        status_map = {
            TranscriptionStatus.CREATED: "uploading",
            TranscriptionStatus.PROCESSING: "processing", 
            TranscriptionStatus.COMPLETE: "ready",
            TranscriptionStatus.FAILED: "failed"
        }
        
        note_status = status_map.get(job.status, "processing")
        await NotesStore.update_status(note_id, note_status)
        
        # If complete, sync artifacts
        if job.status == TranscriptionStatus.COMPLETE:
            assets = await TranscriptionAssetStore.get_assets_for_job(job_id)
            
            artifacts = {}
            for asset in assets:
                if asset.kind == "txt":
                    # Load transcript content (simplified for now)
                    artifacts["transcript"] = f"[Transcript from job {job_id}]"
                elif asset.kind == "json":
                    artifacts["detailed_transcript"] = f"[Detailed JSON from job {job_id}]"
            
            if artifacts:
                await NotesStore.set_artifacts(note_id, artifacts)
        
        # Sync metrics
        metrics = {
            "transcription_job_id": job_id,
            "duration_seconds": job.total_duration,
            "confidence_score": job.confidence_score,
            "detected_language": job.detected_language,
            "stage_durations": job.stage_durations
        }
        
        await NotesStore.set_metrics(note_id, metrics)