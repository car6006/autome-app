"""
Transcription job API endpoints
Provides job status tracking, downloads, and management
"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse

from models import (
    JobStatusResponse, RetryJobRequest, TranscriptionStage, TranscriptionStatus
)
from enhanced_store import TranscriptionJobStore, TranscriptionAssetStore
from auth import get_current_user_optional
from storage import create_presigned_get_url
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get transcription job status and progress
    Returns detailed progress information for each pipeline stage
    """
    try:
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Transcription job not found")
        
        # Check ownership
        if current_user and job.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to access this job")
        
        # Calculate estimated completion time
        estimated_completion = None
        if job.status == TranscriptionStatus.PROCESSING:
            # Estimate based on stage progress and historical data
            # This is a simplified estimation - can be enhanced with ML
            if job.total_duration:
                # Rough estimate: 1 minute of audio = 2-5 minutes processing
                estimated_minutes = job.total_duration / 60 * 3.5  # 3.5x realtime
                remaining_progress = (100 - job.progress) / 100
                estimated_completion = estimated_minutes * remaining_progress
        
        # Get download URLs if job is complete
        download_urls = None
        if job.status == TranscriptionStatus.COMPLETE:
            assets = await TranscriptionAssetStore.get_assets_for_job(job_id)
            download_urls = {}
            
            for asset in assets:
                if asset.kind in ["txt", "json", "srt", "vtt", "docx"]:
                    # Create presigned download URL
                    signed_url = await create_presigned_get_url(asset.storage_key)
                    download_urls[asset.kind] = signed_url
        
        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            current_stage=job.current_stage,
            progress=job.progress,
            stage_progress=job.stage_progress,
            durations=job.stage_durations,
            error_code=job.error_code,
            error_message=job.error_message,
            estimated_completion=None,  # TODO: Implement estimation
            detected_language=job.detected_language,
            confidence_score=job.confidence_score,
            total_duration=job.total_duration,
            word_count=job.word_count,
            download_urls=download_urls
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job status")

@router.get("/{job_id}/download")
async def download_transcription(
    job_id: str,
    format: str = Query("txt", regex="^(txt|json|srt|vtt|docx)$"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Download transcription output in specified format
    Returns signed URL for secure download
    """
    try:
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Transcription job not found")
        
        # Check ownership
        if current_user and job.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to access this job")
        
        if job.status != TranscriptionStatus.COMPLETE:
            raise HTTPException(
                status_code=400, 
                detail=f"Job not complete. Current status: {job.status.value}"
            )
        
        # Get asset for requested format
        asset = await TranscriptionAssetStore.get_asset_by_kind(job_id, format)
        if not asset:
            raise HTTPException(
                status_code=404, 
                detail=f"Output format '{format}' not available for this job"
            )
        
        # Create presigned download URL
        download_url = await create_presigned_get_url(asset.storage_key)
        
        # Return redirect to signed URL
        return RedirectResponse(url=download_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download transcription {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download transcription")

@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    request: RetryJobRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Retry failed transcription job from specified stage
    Allows resuming from any pipeline stage for efficient recovery
    """
    try:
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Transcription job not found")
        
        # Check ownership
        if current_user and job.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to retry this job")
        
        if job.status not in [TranscriptionStatus.FAILED]:
            raise HTTPException(
                status_code=400, 
                detail=f"Job cannot be retried. Current status: {job.status.value}"
            )
        
        if job.retry_count >= job.max_retries:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum retry attempts reached ({job.max_retries})"
            )
        
        # Determine retry stage
        retry_stage = request.from_stage or job.current_stage
        if retry_stage == TranscriptionStage.FAILED:
            # Retry from the stage before failure
            stage_order = [
                TranscriptionStage.CREATED,
                TranscriptionStage.VALIDATING,
                TranscriptionStage.TRANSCODING,
                TranscriptionStage.SEGMENTING,
                TranscriptionStage.DETECTING_LANGUAGE,
                TranscriptionStage.TRANSCRIBING,
                TranscriptionStage.MERGING,
                TranscriptionStage.DIARIZING,
                TranscriptionStage.GENERATING_OUTPUTS
            ]
            
            # Find the last successful stage
            for i, stage in enumerate(stage_order):
                if stage.value in job.stage_durations:
                    retry_stage = stage_order[min(i + 1, len(stage_order) - 1)]
        
        # Reset job state for retry
        update_data = {
            "status": TranscriptionStatus.PROCESSING.value,
            "current_stage": retry_stage.value,
            "error_code": None,
            "error_message": None,
            "progress": job.stage_progress.get(retry_stage.value, 0.0)
        }
        
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {
                "$set": update_data,
                "$inc": {"retry_count": 1}
            }
        )
        
        logger.info(f"🔄 Job {job_id} queued for retry from stage {retry_stage.value}")
        
        return {
            "message": f"Job queued for retry from stage {retry_stage.value}",
            "retry_stage": retry_stage.value,
            "retry_count": job.retry_count + 1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retry job")

@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Cancel running transcription job"""
    try:
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Transcription job not found")
        
        # Check ownership
        if current_user and job.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this job")
        
        if job.status in [TranscriptionStatus.COMPLETE, TranscriptionStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail=f"Job cannot be cancelled. Current status: {job.status.value}"
            )
        
        # Mark job as cancelled
        await TranscriptionJobStore.collection.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": TranscriptionStatus.CANCELLED.value,
                    "current_stage": TranscriptionStage.FAILED.value,
                    "error_code": "CANCELLED",
                    "error_message": "Job cancelled by user"
                }
            }
        )
        
        logger.info(f"🚫 Job {job_id} cancelled by user")
        
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Delete transcription job and associated files"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get job to verify ownership
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Cancel job first if it's still processing
        if job.status in [TranscriptionStatus.CREATED, TranscriptionStatus.PROCESSING]:
            logger.info(f"🛑 Cancelling job {job_id} before deletion")
            await TranscriptionJobStore.set_job_results(job_id, {"status": TranscriptionStatus.CANCELLED.value})
        
        # Delete associated files from storage
        try:
            from cloud_storage import storage_manager
            
            # Delete transcription assets
            assets = await TranscriptionAssetStore.list_assets_by_job(job_id)
            for asset in assets:
                try:
                    await storage_manager.delete_file(asset.storage_key)
                    logger.info(f"🗑️ Deleted asset file: {asset.storage_key}")
                except Exception as e:
                    logger.warning(f"Failed to delete asset file {asset.storage_key}: {e}")
            
            # Delete assets from database
            await TranscriptionAssetStore.delete_assets_by_job(job_id)
            
            # Delete upload session and associated files if exists
            if hasattr(job, 'upload_id') and job.upload_id:
                from enhanced_store import UploadSessionStore
                try:
                    session = await UploadSessionStore.get_session(job.upload_id)
                    if session and session.storage_key:
                        await storage_manager.delete_file(session.storage_key)
                        logger.info(f"🗑️ Deleted upload file: {session.storage_key}")
                    await UploadSessionStore.delete_session(job.upload_id)
                except Exception as e:
                    logger.warning(f"Failed to delete upload session: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to clean up files for job {job_id}: {e}")
        
        # Delete job from database
        await TranscriptionJobStore.delete_job(job_id)
        
        logger.info(f"🗑️ Job {job_id} and associated files deleted successfully")
        
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete job")

@router.get("/")
async def list_jobs(
    status: Optional[str] = Query(None, regex="^(created|processing|complete|failed|cancelled)$"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    List transcription jobs for current user
    Optionally filter by status
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get jobs for user
        if status:
            # Filter by specific status
            status_enum = TranscriptionStatus(status)
            jobs = await TranscriptionJobStore.list_jobs_by_status(status_enum, limit)
            # Filter by user
            jobs = [job for job in jobs if job.user_id == current_user["id"]]
        else:
            # Get all jobs for user
            jobs = await TranscriptionJobStore.list_jobs_for_user(current_user["id"], limit)
        
        # Convert to response format
        job_summaries = []
        for job in jobs:
            job_summaries.append({
                "job_id": job.id,
                "filename": job.filename,
                "status": job.status,
                "current_stage": job.current_stage,
                "progress": job.progress,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "total_duration": job.total_duration,
                "detected_language": job.detected_language,
                "error_message": job.error_message
            })
        
        return {
            "jobs": job_summaries,
            "total": len(job_summaries),
            "filter": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")

@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get processing logs for transcription job (for debugging)
    Admin only feature
    """
    try:
        # Check admin access
        if not current_user or not current_user.get("email", "").endswith("@admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Transcription job not found")
        
        # Return detailed job information for debugging
        return {
            "job_id": job.id,
            "status": job.status,
            "stage_progress": job.stage_progress,
            "stage_durations": job.stage_durations,
            "stage_checkpoints": job.stage_checkpoints,
            "storage_paths": job.storage_paths,
            "retry_count": job.retry_count,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "error_code": job.error_code,
            "error_message": job.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job logs {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job logs")

@router.post("/cleanup")
async def cleanup_stuck_jobs(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Clean up stuck or inconsistent jobs"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Find and fix stuck jobs for this user
        from enhanced_store import TranscriptionJobStore
        
        # Get user's jobs
        user_jobs = await TranscriptionJobStore.list_jobs_for_user(current_user["id"])
        
        fixed_count = 0
        for job in user_jobs:
            # Fix jobs stuck in processing for more than 1 hour
            if (job.status == TranscriptionStatus.PROCESSING and 
                job.updated_at and 
                (datetime.now(timezone.utc) - job.updated_at).total_seconds() > 3600):
                
                await TranscriptionJobStore.set_job_results(job.id, {
                    "status": TranscriptionStatus.FAILED.value,
                    "error_message": "Job timed out after 1 hour"
                })
                fixed_count += 1
                logger.info(f"Fixed stuck job: {job.id}")
            
            # Fix jobs stuck in pending
            elif job.status == TranscriptionStatus.PENDING:
                await TranscriptionJobStore.set_job_results(job.id, {
                    "status": TranscriptionStatus.CREATED.value
                })
                fixed_count += 1
                logger.info(f"Reset pending job: {job.id}")
        
        return {
            "message": f"Cleaned up {fixed_count} stuck jobs",
            "fixed_count": fixed_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup jobs")