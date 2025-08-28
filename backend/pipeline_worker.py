"""
Pipeline worker for large-file audio transcription
Implements idempotent, checkpointed processing stages
"""
import os
import json
import asyncio
import time
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
from tempfile import NamedTemporaryFile, TemporaryDirectory

from models import TranscriptionJob, TranscriptionStage, TranscriptionStatus, TranscriptionAsset, PipelineConfig
from enhanced_store import TranscriptionJobStore, TranscriptionAssetStore
from providers import stt_transcribe
from storage import get_file_path, store_file_content
import httpx

logger = logging.getLogger(__name__)

class PipelineWorker:
    """Main pipeline worker for processing transcription jobs"""
    
    def __init__(self):
        self.config = PipelineConfig()
        self.running = False
        
    async def start(self):
        """Start the worker process"""
        self.running = True
        logger.info("🚀 Pipeline worker started")
        
        while self.running:
            try:
                # Get next job to process
                jobs = await TranscriptionJobStore.list_jobs_by_status(TranscriptionStatus.CREATED, limit=1)
                if not jobs:
                    jobs = await TranscriptionJobStore.list_jobs_by_status(TranscriptionStatus.PROCESSING, limit=5)
                
                if jobs:
                    for job in jobs:
                        try:
                            await self.process_job(job)
                        except Exception as e:
                            logger.error(f"Failed to process job {job.id}: {str(e)}")
                            await self.handle_job_error(job.id, "PROCESSING_ERROR", str(e))
                else:
                    # No jobs to process, wait
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(30)
    
    def stop(self):
        """Stop the worker process"""
        self.running = False
        logger.info("🛑 Pipeline worker stopped")
    
    async def process_job(self, job: TranscriptionJob):
        """Process a transcription job through the pipeline"""
        logger.info(f"📋 Processing job {job.id} at stage {job.current_stage}")
        
        try:
            # Determine next stage to process
            if job.current_stage == TranscriptionStage.CREATED:
                await self.stage_validate(job)
            elif job.current_stage == TranscriptionStage.VALIDATING:
                await self.stage_transcode(job)
            elif job.current_stage == TranscriptionStage.TRANSCODING:
                await self.stage_segment(job)
            elif job.current_stage == TranscriptionStage.SEGMENTING:
                await self.stage_detect_language(job)
            elif job.current_stage == TranscriptionStage.DETECTING_LANGUAGE:
                await self.stage_transcribe(job)
            elif job.current_stage == TranscriptionStage.TRANSCRIBING:
                await self.stage_merge(job)
            elif job.current_stage == TranscriptionStage.MERGING:
                await self.stage_diarize(job)
            elif job.current_stage == TranscriptionStage.DIARIZING:
                await self.stage_generate_outputs(job)
            elif job.current_stage == TranscriptionStage.GENERATING_OUTPUTS:
                await self.stage_finalize(job)
            else:
                logger.warning(f"Job {job.id} in unknown stage: {job.current_stage}")
                
        except Exception as e:
            logger.error(f"Stage processing failed for job {job.id}: {str(e)}")
            await self.handle_job_error(job.id, "STAGE_ERROR", str(e))
    
    async def stage_validate(self, job: TranscriptionJob):
        """Stage 1: Validate uploaded file"""
        stage = TranscriptionStage.VALIDATING
        logger.info(f"🔍 Job {job.id}: Validating file")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 10.0)
        
        try:
            # Get file path from upload session
            from enhanced_store import UploadSessionStore
            session = await UploadSessionStore.get_session(job.upload_id)
            if not session or not session.storage_key:
                raise Exception("Upload session not found or file not available")
            
            file_path = get_file_path(session.storage_key)
            if not Path(file_path).exists():
                raise Exception(f"Uploaded file not found: {file_path}")
            
            # Validate file integrity
            actual_size = Path(file_path).stat().st_size
            if actual_size != job.total_size:
                raise Exception(f"File size mismatch. Expected: {job.total_size}, actual: {actual_size}")
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 30.0)
            
            # Probe audio file with ffprobe
            try:
                cmd = [
                    "ffprobe", "-v", "quiet", "-print_format", "json", 
                    "-show_format", "-show_streams", file_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise Exception(f"ffprobe failed: {result.stderr}")
                
                probe_data = json.loads(result.stdout)
                format_info = probe_data.get("format", {})
                
                # Extract audio duration
                duration = float(format_info.get("duration", 0))
                if duration <= 0:
                    raise Exception("Invalid audio duration")
                
                # Check duration limits
                max_duration = self.config.max_duration_hours * 3600
                if duration > max_duration:
                    raise Exception(f"Audio too long: {duration/3600:.1f}h > {self.config.max_duration_hours}h")
                
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 60.0)
                
                # Find audio stream
                audio_streams = [s for s in probe_data.get("streams", []) if s.get("codec_type") == "audio"]
                if not audio_streams:
                    raise Exception("No audio stream found")
                
                # Store file info in job
                await TranscriptionJobStore.set_job_results(job.id, {
                    "total_duration": duration,
                    "storage_paths": {"original": session.storage_key}
                })
                
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
                
            except subprocess.TimeoutExpired:
                raise Exception("Audio probe timeout - file may be corrupted")
            except json.JSONDecodeError:
                raise Exception("Invalid audio file format")
                
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to next stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.TRANSCODING, 0.0)
            logger.info(f"✅ Job {job.id}: Validation complete ({duration:.1f}s audio)")
            
        except Exception as e:
            await self.handle_job_error(job.id, "VALIDATION_FAILED", str(e))
    
    async def stage_transcode(self, job: TranscriptionJob):
        """Stage 2: Transcode to normalized format"""
        stage = TranscriptionStage.TRANSCODING
        logger.info(f"🔄 Job {job.id}: Transcoding audio")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 10.0)
        
        try:
            # Get original file path
            job_data = await TranscriptionJobStore.get_job(job.id)
            original_path = get_file_path(job_data.storage_paths["original"])
            
            # Create normalized audio file
            with TemporaryDirectory() as temp_dir:
                normalized_path = Path(temp_dir) / "normalized.wav"
                
                # FFmpeg command for normalization
                cmd = [
                    "ffmpeg", "-i", original_path,
                    "-ar", "16000",  # 16kHz sample rate
                    "-ac", "1",      # Mono
                    "-acodec", "pcm_s16le",  # 16-bit PCM
                    "-af", "volume=1.0",  # Normalize volume
                    "-y", str(normalized_path)
                ]
                
                logger.info(f"Transcoding with: {' '.join(cmd)}")
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Monitor progress (FFmpeg doesn't provide reliable progress, so we estimate)
                for progress in range(20, 90, 10):
                    await TranscriptionJobStore.update_stage_progress(job.id, stage, float(progress))
                    await asyncio.sleep(1)
                    
                    # Check if process completed
                    if process.returncode is not None:
                        break
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"FFmpeg failed: {stderr.decode()}")
                
                if not normalized_path.exists():
                    raise Exception("Normalized audio file not created")
                
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 90.0)
                
                # Store normalized file
                with open(normalized_path, "rb") as f:
                    normalized_key = await store_file_content(f.read(), f"job_{job.id}_normalized.wav")
                
                # Update job with normalized file path
                storage_paths = job_data.storage_paths.copy()
                storage_paths["normalized"] = normalized_key
                await TranscriptionJobStore.set_job_results(job.id, {
                    "storage_paths": storage_paths
                })
                
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
            
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to next stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.SEGMENTING, 0.0)
            logger.info(f"✅ Job {job.id}: Transcoding complete")
            
        except Exception as e:
            await self.handle_job_error(job.id, "TRANSCODING_FAILED", str(e))
    
    async def stage_segment(self, job: TranscriptionJob):
        """Stage 3: Segment audio into chunks for processing"""
        stage = TranscriptionStage.SEGMENTING
        logger.info(f"✂️  Job {job.id}: Segmenting audio")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 10.0)
        
        try:
            # Get normalized audio file
            job_data = await TranscriptionJobStore.get_job(job.id)
            normalized_path = get_file_path(job_data.storage_paths["normalized"])
            
            # Calculate segment parameters
            segment_duration = self.config.segment_duration  # 60 seconds default
            overlap = self.config.segment_overlap  # 1 second default
            total_duration = job_data.total_duration
            
            segments = []
            segment_paths = []
            
            # Create segments
            with TemporaryDirectory() as temp_dir:
                segment_count = 0
                current_time = 0.0
                
                while current_time < total_duration:
                    # Calculate segment timing
                    segment_start = max(0, current_time - overlap)
                    segment_end = min(total_duration, current_time + segment_duration)
                    segment_length = segment_end - segment_start
                    
                    if segment_length < 1.0:  # Skip very short segments
                        break
                    
                    segment_file = Path(temp_dir) / f"segment_{segment_count:04d}.wav"
                    
                    # Extract segment with FFmpeg
                    cmd = [
                        "ffmpeg", "-i", normalized_path,
                        "-ss", str(segment_start),
                        "-t", str(segment_length),
                        "-y", str(segment_file)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    if result.returncode != 0:
                        logger.warning(f"Failed to create segment {segment_count}: {result.stderr.decode()}")
                        current_time += segment_duration
                        continue
                    
                    if segment_file.exists() and segment_file.stat().st_size > 1000:  # Valid segment
                        # Store segment
                        with open(segment_file, "rb") as f:
                            segment_key = await store_file_content(f.read(), f"job_{job.id}_segment_{segment_count:04d}.wav")
                        
                        segments.append({
                            "index": segment_count,
                            "start_time": segment_start,
                            "end_time": segment_end,
                            "duration": segment_length,
                            "storage_key": segment_key,
                            "original_start": current_time,
                            "original_end": current_time + segment_duration
                        })
                        
                        segment_paths.append(segment_key)
                        segment_count += 1
                        
                        # Update progress
                        progress = min(90.0, (current_time / total_duration) * 80.0 + 10.0)
                        await TranscriptionJobStore.update_stage_progress(job.id, stage, progress)
                    
                    current_time += segment_duration
                
                if not segments:
                    raise Exception("No valid segments created")
                
                logger.info(f"Created {len(segments)} segments for job {job.id}")
                
                # Store segment metadata as checkpoint
                checkpoint_data = {
                    "segments": segments,
                    "total_segments": len(segments)
                }
                await TranscriptionJobStore.set_stage_checkpoint(job.id, stage, checkpoint_data)
                
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
            
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to next stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.DETECTING_LANGUAGE, 0.0)
            logger.info(f"✅ Job {job.id}: Segmentation complete ({len(segments)} segments)")
            
        except Exception as e:
            await self.handle_job_error(job.id, "SEGMENTATION_FAILED", str(e))
    
    async def stage_detect_language(self, job: TranscriptionJob):
        """Stage 4: Detect audio language"""
        stage = TranscriptionStage.DETECTING_LANGUAGE
        logger.info(f"🌍 Job {job.id}: Detecting language")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 20.0)
        
        try:
            job_data = await TranscriptionJobStore.get_job(job.id)
            
            # If language already specified, skip detection
            if job_data.language:
                detected_language = job_data.language
                logger.info(f"Language pre-specified: {detected_language}")
            else:
                # Get segments for language detection
                checkpoint = await TranscriptionJobStore.get_stage_checkpoint(job.id, TranscriptionStage.SEGMENTING)
                if not checkpoint or not checkpoint.get("segments"):
                    raise Exception("Segment data not found")
                
                segments = checkpoint["segments"]
                
                # Use first few segments for language detection (max 3 minutes)
                detection_segments = []
                total_detection_time = 0
                
                for segment in segments[:10]:  # First 10 segments max
                    if total_detection_time >= 180:  # 3 minutes max
                        break
                    detection_segments.append(segment)
                    total_detection_time += segment["duration"]
                
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 40.0)
                
                # Run language detection on first segment (simplified for now)
                if detection_segments:
                    first_segment = detection_segments[0]
                    segment_path = get_file_path(first_segment["storage_key"])
                    
                    # Use Whisper for language detection (can be improved with dedicated language detection)
                    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY")
                    if not api_key:
                        detected_language = "en"  # Default fallback
                        logger.warning("No API key for language detection, defaulting to English")
                    else:
                        try:
                            # Quick transcription for language detection
                            with open(segment_path, "rb") as audio_file:
                                files = {"file": audio_file}
                                form = {"model": "whisper-1", "response_format": "verbose_json"}
                                
                                async with httpx.AsyncClient(timeout=60) as client:
                                    response = await client.post(
                                        "https://api.openai.com/v1/audio/transcriptions",
                                        data=form,
                                        files=files,
                                        headers={"Authorization": f"Bearer {api_key}"}
                                    )
                                    response.raise_for_status()
                                    
                                    result = response.json()
                                    detected_language = result.get("language", "en")
                                    
                        except Exception as e:
                            logger.warning(f"Language detection failed: {e}, defaulting to English")
                            detected_language = "en"
                else:
                    detected_language = "en"  # Default
                
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 80.0)
            
            # Store detected language
            await TranscriptionJobStore.set_job_results(job.id, {
                "detected_language": detected_language,
                "language": detected_language  # Set as job language
            })
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
            
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to next stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.TRANSCRIBING, 0.0)
            logger.info(f"✅ Job {job.id}: Language detection complete - {detected_language}")
            
        except Exception as e:
            await self.handle_job_error(job.id, "LANGUAGE_DETECTION_FAILED", str(e))
    
    async def handle_job_error(self, job_id: str, error_code: str, error_message: str):
        """Handle job errors and determine if retry is possible"""
        logger.error(f"❌ Job {job_id} error: {error_code} - {error_message}")
        
        job = await TranscriptionJobStore.get_job(job_id)
        if job and job.retry_count < job.max_retries:
            # Increment retry count but keep in processing state for retry
            await TranscriptionJobStore.collection.update_one(
                {"id": job_id},
                {"$inc": {"retry_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc)}}
            )
            logger.info(f"🔄 Job {job_id} will be retried (attempt {job.retry_count + 1}/{job.max_retries})")
        else:
            # Max retries reached, mark as failed
            await TranscriptionJobStore.set_job_error(job_id, error_code, error_message)

# Global worker instance
worker = PipelineWorker()

# Functions for external control
async def start_worker():
    """Start the pipeline worker"""
    await worker.start()

def stop_worker():
    """Stop the pipeline worker"""
    worker.stop()

async def process_single_job(job_id: str):
    """Process a specific job (for manual processing)"""
    job = await TranscriptionJobStore.get_job(job_id)
    if job:
        await worker.process_job(job)
    else:
        raise Exception(f"Job {job_id} not found")