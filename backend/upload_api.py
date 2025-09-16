"""
Resumable upload API endpoints for large-file transcription pipeline
"""
import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse

from models import (
    UploadSessionRequest, UploadSessionResponse, ChunkUploadResponse,
    FinalizeUploadRequest, FinalizeUploadResponse, UploadSession, 
    TranscriptionJob, PipelineConfig
)
from enhanced_store import UploadSessionStore, TranscriptionJobStore, EnhancedNotesStore
from auth import get_current_user_optional
from storage import store_file
import logging

logger = logging.getLogger(__name__)

# Configuration
config = PipelineConfig()
router = APIRouter(prefix="/uploads", tags=["uploads"])

# Storage directory for chunked uploads
CHUNK_STORAGE = Path("/tmp/upload_chunks")
CHUNK_STORAGE.mkdir(exist_ok=True)

@router.post("/sessions", response_model=UploadSessionResponse)
async def create_upload_session(
    request: UploadSessionRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Create a resumable upload session for large audio files
    Returns upload session with chunk configuration
    """
    try:
        # Validate file size
        if request.total_size > config.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {config.max_file_size / (1024*1024):.1f} MB"
            )
        
        # Validate MIME type with pattern matching support
        def is_mime_type_allowed(mime_type: str, allowed_types: list) -> bool:
            """Check if MIME type is allowed, supporting wildcard patterns"""
            for allowed_type in allowed_types:
                if allowed_type == mime_type:
                    return True
                # Handle wildcard patterns like audio/* and video/*
                if allowed_type.endswith('/*'):
                    prefix = allowed_type[:-2]  # Remove /*
                    if mime_type.startswith(prefix + '/'):
                        return True
            return False
        
        if not is_mime_type_allowed(request.mime_type, config.allowed_mime_types):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {request.mime_type}. We support all audio and video formats for transcription."
            )
        
        # Calculate number of chunks needed
        chunk_size = config.chunk_size
        total_chunks = (request.total_size + chunk_size - 1) // chunk_size
        
        # Create upload session
        session = UploadSession(
            user_id=current_user["id"] if current_user else None,
            filename=request.filename,
            total_size=request.total_size,
            mime_type=request.mime_type,
            chunk_size=chunk_size
        )
        
        session = await UploadSessionStore.create_session(session)
        
        logger.info(f"Created upload session {session.id} for file {request.filename} ({request.total_size} bytes, {total_chunks} chunks)")
        
        # Generate response
        response = UploadSessionResponse(
            upload_id=session.id,
            chunk_size=chunk_size,
            max_duration_hours=config.max_duration_hours,
            allowed_mime_types=config.allowed_mime_types
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create upload session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create upload session")

@router.post("/sessions/{upload_id}/chunks/{chunk_index}", response_model=ChunkUploadResponse)
async def upload_chunk(
    upload_id: str,
    chunk_index: int,
    chunk: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Upload a single chunk of the file
    Supports resumable upload by tracking which chunks have been uploaded
    """
    try:
        # Get upload session
        session = await UploadSessionStore.get_session(upload_id)
        if not session:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        if session.status != "active":
            raise HTTPException(status_code=400, detail="Upload session is not active")
        
        # Verify ownership
        if current_user and session.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Calculate expected chunk size
        total_chunks = (session.total_size + session.chunk_size - 1) // session.chunk_size
        if chunk_index >= total_chunks:
            raise HTTPException(status_code=400, detail="Invalid chunk index")
        
        # Check if chunk already uploaded
        chunks_uploaded = await UploadSessionStore.get_chunks_uploaded(upload_id)
        if chunk_index in chunks_uploaded:
            logger.info(f"Chunk {chunk_index} already uploaded for session {upload_id}")
            return ChunkUploadResponse(chunk_index=chunk_index, uploaded=True)
        
        # Read and store chunk
        chunk_data = await chunk.read()
        
        # Validate chunk size (last chunk can be smaller)
        expected_size = session.chunk_size
        if chunk_index == total_chunks - 1:  # Last chunk
            remaining = session.total_size % session.chunk_size
            if remaining > 0:
                expected_size = remaining
        
        if len(chunk_data) != expected_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid chunk size. Expected: {expected_size}, got: {len(chunk_data)}"
            )
        
        # Store chunk to temporary storage
        chunk_dir = CHUNK_STORAGE / upload_id
        chunk_dir.mkdir(exist_ok=True)
        chunk_path = chunk_dir / f"chunk_{chunk_index:04d}"
        
        with open(chunk_path, "wb") as f:
            f.write(chunk_data)
        
        # Mark chunk as uploaded
        await UploadSessionStore.update_chunks_uploaded(upload_id, chunk_index)
        
        logger.info(f"Uploaded chunk {chunk_index}/{total_chunks-1} for session {upload_id}")
        
        return ChunkUploadResponse(
            chunk_index=chunk_index,
            uploaded=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload chunk {chunk_index} for session {upload_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload chunk")

@router.get("/sessions/{upload_id}/status")
async def get_upload_status(
    upload_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get upload session status and progress
    Shows which chunks have been uploaded for resuming
    """
    try:
        session = await UploadSessionStore.get_session(upload_id)
        if not session:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        # Verify ownership
        if current_user and session.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Calculate progress
        total_chunks = (session.total_size + session.chunk_size - 1) // session.chunk_size
        uploaded_chunks = len(session.chunks_uploaded)
        progress = (uploaded_chunks / total_chunks * 100) if total_chunks > 0 else 0
        
        return {
            "upload_id": upload_id,
            "status": session.status,
            "progress": progress,
            "chunks_uploaded": sorted(session.chunks_uploaded),
            "total_chunks": total_chunks,
            "bytes_uploaded": uploaded_chunks * session.chunk_size,
            "total_bytes": session.total_size,
            "created_at": session.created_at,
            "expires_at": session.expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload status for {upload_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get upload status")

@router.post("/sessions/{upload_id}/complete", response_model=FinalizeUploadResponse)
async def finalize_upload(
    upload_id: str,
    request: FinalizeUploadRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Finalize upload by combining chunks and creating transcription job
    Validates all chunks are present and creates the final file
    """
    try:
        # Get upload session
        session = await UploadSessionStore.get_session(upload_id)
        if not session:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        if session.status != "active":
            raise HTTPException(status_code=400, detail="Upload session is not active")
        
        # Verify ownership
        if current_user and session.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Check all chunks are uploaded
        total_chunks = (session.total_size + session.chunk_size - 1) // session.chunk_size
        chunks_uploaded = set(session.chunks_uploaded)
        expected_chunks = set(range(total_chunks))
        
        if chunks_uploaded != expected_chunks:
            missing_chunks = expected_chunks - chunks_uploaded
            raise HTTPException(
                status_code=400,
                detail=f"Missing chunks: {sorted(list(missing_chunks))}"
            )
        
        # Combine chunks into final file
        chunk_dir = CHUNK_STORAGE / upload_id
        final_path = chunk_dir / session.filename
        
        logger.info(f"Combining {total_chunks} chunks for session {upload_id}")
        
        sha256_hash = hashlib.sha256()
        total_bytes_written = 0
        
        with open(final_path, "wb") as final_file:
            for chunk_index in range(total_chunks):
                chunk_path = chunk_dir / f"chunk_{chunk_index:04d}"
                if not chunk_path.exists():
                    raise HTTPException(
                        status_code=500,
                        detail=f"Chunk file missing: {chunk_index}"
                    )
                
                with open(chunk_path, "rb") as chunk_file:
                    chunk_data = chunk_file.read()
                    final_file.write(chunk_data)
                    sha256_hash.update(chunk_data)
                    total_bytes_written += len(chunk_data)
        
        # Verify final file size
        if total_bytes_written != session.total_size:
            raise HTTPException(
                status_code=500,
                detail=f"File size mismatch. Expected: {session.total_size}, got: {total_bytes_written}"
            )
        
        # Calculate file hash
        calculated_sha256 = sha256_hash.hexdigest()
        
        # Verify hash if provided
        if request.sha256 and request.sha256.lower() != calculated_sha256.lower():
            raise HTTPException(
                status_code=400,
                detail="File integrity check failed - SHA256 mismatch"
            )
        
        # Store final file using existing storage system
        with open(final_path, "rb") as f:
            file_content = f.read()
            storage_key = store_file(file_content, session.filename)
        
        # Mark session as completed
        await UploadSessionStore.complete_session(upload_id, storage_key, calculated_sha256)
        
        # Create transcription job
        job = TranscriptionJob(
            user_id=session.user_id,
            upload_id=upload_id,
            filename=session.filename,
            total_size=session.total_size,
            mime_type=session.mime_type,
            language=None,  # Will be auto-detected
            enable_diarization=True  # Default enabled
        )
        
        job = await TranscriptionJobStore.create_job(job)
        
        # Create backward-compatible Note record
        note_id = await EnhancedNotesStore.create_from_transcription_job(job)
        
        # 🔥 CRITICAL: Link the job to the main note for result transfer
        job.note_id = note_id
        await TranscriptionJobStore.update_job(job)
        
        # Clean up chunk files
        try:
            import shutil
            shutil.rmtree(chunk_dir)
            logger.info(f"Cleaned up chunks for session {upload_id}")
        except Exception as e:
            logger.warning(f"Failed to clean up chunks for {upload_id}: {e}")
        
        # Enqueue job for pipeline processing
        from tasks import enqueue_pipeline_job
        background_tasks.add_task(enqueue_pipeline_job, job.id)
        logger.info(f"Enqueued transcription job {job.id} for pipeline processing")
        
        return FinalizeUploadResponse(
            job_id=job.id,
            upload_id=upload_id,
            status="created"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to finalize upload {upload_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to finalize upload")

@router.delete("/sessions/{upload_id}")
async def cancel_upload(
    upload_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Cancel upload session and clean up chunks"""
    try:
        session = await UploadSessionStore.get_session(upload_id)
        if not session:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        # Verify ownership
        if current_user and session.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Clean up chunk files
        chunk_dir = CHUNK_STORAGE / upload_id
        if chunk_dir.exists():
            import shutil
            shutil.rmtree(chunk_dir)
            logger.info(f"Cleaned up chunks for cancelled session {upload_id}")
        
        # Mark session as cancelled (update status)
        await UploadSessionStore.collection.update_one(
            {"id": upload_id},
            {"$set": {"status": "cancelled"}}
        )
        
        return {"message": "Upload session cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel upload {upload_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel upload")

# Cleanup task (should be run periodically)
@router.post("/cleanup")
async def cleanup_expired_sessions(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Clean up expired upload sessions (admin only)"""
    # Only allow admin users to trigger cleanup
    if not current_user or not current_user.get("email", "").endswith("@admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        await UploadSessionStore.cleanup_expired_sessions()
        
        # Clean up orphaned chunk directories
        cleanup_count = 0
        for chunk_dir in CHUNK_STORAGE.iterdir():
            if chunk_dir.is_dir():
                # Check if session still exists
                session = await UploadSessionStore.get_session(chunk_dir.name)
                if not session or session.status in ["completed", "cancelled", "expired"]:
                    import shutil
                    shutil.rmtree(chunk_dir)
                    cleanup_count += 1
        
        return {
            "message": f"Cleanup completed. Removed {cleanup_count} orphaned chunk directories."
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")