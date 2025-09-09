"""
Worker manager for transcription pipeline
Handles starting/stopping workers and job queue management
"""
import asyncio
import logging
import signal
from typing import Optional
from contextlib import asynccontextmanager

from pipeline_worker import PipelineWorker
from enhanced_store import TranscriptionJobStore
from models import TranscriptionStatus

logger = logging.getLogger(__name__)

class WorkerManager:
    """Manages pipeline workers and job processing"""
    
    def __init__(self):
        self.worker: Optional[PipelineWorker] = None
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
        
    async def start_worker(self):
        """Start the pipeline worker"""
        if self.running:
            logger.warning("Worker already running")
            return
            
        try:
            self.worker = PipelineWorker()
            
            # Start worker in background task
            self.worker_task = asyncio.create_task(self.worker.start())
            self.running = True
            
            logger.info("🚀 Worker manager started pipeline worker")
            
        except Exception as e:
            logger.error(f"Failed to start worker: {str(e)}")
            raise
    
    async def stop_worker(self):
        """Stop the pipeline worker gracefully"""
        if not self.running:
            return
            
        try:
            if self.worker:
                self.worker.stop()
            
            if self.worker_task and not self.worker_task.done():
                # Give worker time to finish current job
                try:
                    await asyncio.wait_for(self.worker_task, timeout=30)
                except asyncio.TimeoutError:
                    logger.warning("Worker didn't stop gracefully, cancelling...")
                    self.worker_task.cancel()
                    try:
                        await self.worker_task
                    except asyncio.CancelledError:
                        pass
            
            self.running = False
            self.worker = None
            self.worker_task = None
            
            logger.info("🛑 Worker manager stopped pipeline worker")
            
        except Exception as e:
            logger.error(f"Error stopping worker: {str(e)}")
    
    async def get_worker_status(self):
        """Get current worker status"""
        return {
            "running": self.running,
            "worker_active": self.worker is not None,
            "task_running": self.worker_task is not None and not self.worker_task.done()
        }
    
    async def process_job_manually(self, job_id: str):
        """Process a specific job manually (for testing/debugging)"""
        if not self.worker:
            raise Exception("Worker not running")
        
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            raise Exception(f"Job {job_id} not found")
        
        await self.worker.process_job(job)
    
    async def get_queue_status(self):
        """Get job queue status"""
        try:
            created_jobs = await TranscriptionJobStore.list_jobs_by_status(TranscriptionStatus.CREATED, limit=50)
            processing_jobs = await TranscriptionJobStore.list_jobs_by_status(TranscriptionStatus.PROCESSING, limit=50)
            failed_jobs = await TranscriptionJobStore.get_jobs_ready_for_retry()
            
            return {
                "created_jobs": len(created_jobs),
                "processing_jobs": len(processing_jobs),
                "failed_jobs_ready_for_retry": len(failed_jobs),
                "total_queued": len(created_jobs) + len(processing_jobs)
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            return {
                "created_jobs": 0,
                "processing_jobs": 0,
                "failed_jobs_ready_for_retry": 0,
                "total_queued": 0,
                "error": str(e)
            }

# Global worker manager instance
worker_manager = WorkerManager()

# Lifespan manager for FastAPI integration
@asynccontextmanager
async def worker_lifespan(app):
    """FastAPI lifespan context manager for worker"""
    # Startup
    logger.info("Starting transcription pipeline worker...")
    await worker_manager.start_worker()
    
    # Initialize live transcription manager
    try:
        from live_transcription import live_transcription_manager
        logger.info("Initializing live transcription manager...")
        await live_transcription_manager.initialize()
        logger.info("✅ Live transcription manager initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize live transcription manager: {e}")
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(worker_manager.stop_worker())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    yield
    
    # Shutdown
    logger.info("Shutting down transcription pipeline worker...")
    await worker_manager.stop_worker()

# Convenience functions for external use
async def start_pipeline_worker():
    """Start the pipeline worker"""
    await worker_manager.start_worker()

async def stop_pipeline_worker():
    """Stop the pipeline worker"""
    await worker_manager.stop_worker()

async def get_pipeline_status():
    """Get pipeline status"""
    worker_status = await worker_manager.get_worker_status()
    queue_status = await worker_manager.get_queue_status()
    
    return {
        "worker": worker_status,
        "queue": queue_status
    }

async def process_job(job_id: str):
    """Process a specific job manually"""
    await worker_manager.process_job_manually(job_id)

# Health check function
async def pipeline_health_check():
    """Health check for pipeline system"""
    try:
        status = await get_pipeline_status()
        
        # Check if worker is running
        if not status["worker"]["running"]:
            return {"status": "unhealthy", "reason": "Worker not running"}
        
        # Check if there are too many failed jobs
        if status["queue"]["failed_jobs_ready_for_retry"] > 10:
            return {"status": "degraded", "reason": "Too many failed jobs in queue"}
        
        # Check if queue is backing up
        if status["queue"]["total_queued"] > 50:
            return {"status": "degraded", "reason": "Job queue backing up"}
        
        return {"status": "healthy", "queue_size": status["queue"]["total_queued"]}
        
    except Exception as e:
        return {"status": "unhealthy", "reason": f"Health check failed: {str(e)}"}