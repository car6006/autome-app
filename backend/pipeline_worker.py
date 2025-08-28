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
from storage import get_file_path, store_file_content_async
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
                await self.stage_generate_outputs(job)
            elif job.current_stage == TranscriptionStage.COMPLETE:
                logger.info(f"Job {job.id} already complete")
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
                    normalized_key = await store_file_content_async(f.read(), f"job_{job.id}_normalized.wav")
                
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
                            segment_key = await store_file_content_async(f.read(), f"job_{job.id}_segment_{segment_count:04d}.wav")
                        
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
    
    async def stage_transcribe(self, job: TranscriptionJob):
        """Stage 5: Transcribe audio segments"""
        stage = TranscriptionStage.TRANSCRIBING
        logger.info(f"🎤 Job {job.id}: Transcribing audio segments")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 5.0)
        
        try:
            job_data = await TranscriptionJobStore.get_job(job.id)
            
            # Get segments for transcription
            checkpoint = await TranscriptionJobStore.get_stage_checkpoint(job.id, TranscriptionStage.SEGMENTING)
            if not checkpoint or not checkpoint.get("segments"):
                raise Exception("Segment data not found")
            
            segments = checkpoint["segments"]
            total_segments = len(segments)
            
            transcripts = []
            api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                raise Exception("No OpenAI API key available for transcription")
            
            logger.info(f"Transcribing {total_segments} segments for job {job.id}")
            
            for i, segment in enumerate(segments):
                try:
                    segment_path = get_file_path(segment["storage_key"])
                    
                    # Transcribe segment using OpenAI Whisper
                    with open(segment_path, "rb") as audio_file:
                        files = {"file": audio_file}
                        form = {
                            "model": "whisper-1",
                            "language": job_data.detected_language or "en",
                            "response_format": "verbose_json",
                            "temperature": 0.2
                        }
                        
                        # Use existing retry logic from providers.py
                        max_retries = 3
                        retry_delay = 5
                        
                        for attempt in range(max_retries):
                            try:
                                async with httpx.AsyncClient(timeout=60) as client:
                                    response = await client.post(
                                        "https://api.openai.com/v1/audio/transcriptions",
                                        data=form,
                                        files=files,
                                        headers={"Authorization": f"Bearer {api_key}"}
                                    )
                                    response.raise_for_status()
                                    
                                    result = response.json()
                                    transcript_text = result.get("text", "")
                                    
                                    # Store segment transcript with timing info
                                    transcripts.append({
                                        "index": i,
                                        "start_time": segment["original_start"],
                                        "end_time": segment["original_end"],
                                        "text": transcript_text,
                                        "confidence": 1.0,  # Whisper doesn't provide confidence
                                        "segments": result.get("segments", [])
                                    })
                                    
                                    logger.info(f"Transcribed segment {i+1}/{total_segments} for job {job.id}")
                                    break
                                    
                            except httpx.HTTPStatusError as e:
                                if e.response.status_code == 429 and attempt < max_retries - 1:
                                    # Rate limited, wait with exponential backoff
                                    wait_time = retry_delay * (2 ** attempt)
                                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise Exception(f"Transcription API error: {e.response.status_code}")
                            except Exception as e:
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                    continue
                                else:
                                    raise e
                    
                    # Update progress
                    progress = 10.0 + ((i + 1) / total_segments) * 80.0
                    await TranscriptionJobStore.update_stage_progress(job.id, stage, progress)
                    
                    # Add delay between requests to avoid rate limits
                    if i < total_segments - 1:
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Failed to transcribe segment {i}: {str(e)}")
                    # Continue with other segments, mark this as empty
                    transcripts.append({
                        "index": i,
                        "start_time": segment["original_start"],
                        "end_time": segment["original_end"],
                        "text": "[Transcription failed]",
                        "confidence": 0.0,
                        "segments": []
                    })
            
            if not any(t["text"] for t in transcripts if t["text"] != "[Transcription failed]"):
                raise Exception("All segment transcriptions failed")
            
            # Store transcription results as checkpoint
            checkpoint_data = {
                "transcripts": transcripts,
                "total_segments_transcribed": len([t for t in transcripts if t["text"] != "[Transcription failed]"])
            }
            await TranscriptionJobStore.set_stage_checkpoint(job.id, stage, checkpoint_data)
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
            
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to next stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.MERGING, 0.0)
            logger.info(f"✅ Job {job.id}: Transcription complete ({len(transcripts)} segments)")
            
        except Exception as e:
            await self.handle_job_error(job.id, "TRANSCRIPTION_FAILED", str(e))
    
    async def stage_merge(self, job: TranscriptionJob):
        """Stage 6: Merge segment transcriptions"""
        stage = TranscriptionStage.MERGING
        logger.info(f"🔗 Job {job.id}: Merging transcripts")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 20.0)
        
        try:
            # Get transcription results
            checkpoint = await TranscriptionJobStore.get_stage_checkpoint(job.id, TranscriptionStage.TRANSCRIBING)
            if not checkpoint or not checkpoint.get("transcripts"):
                raise Exception("Transcription data not found")
            
            transcripts = checkpoint["transcripts"]
            
            # Sort by index to ensure correct order
            transcripts.sort(key=lambda x: x["index"])
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 40.0)
            
            # Merge into final transcript
            final_text = []
            total_words = 0
            
            for transcript in transcripts:
                if transcript["text"] and transcript["text"] != "[Transcription failed]":
                    final_text.append(transcript["text"].strip())
                    total_words += len(transcript["text"].split())
            
            merged_transcript = "\n\n".join(final_text)
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 70.0)
            
            # Store merged results
            merge_results = {
                "final_transcript": merged_transcript,
                "word_count": total_words,
                "segment_count": len(transcripts),
                "failed_segments": len([t for t in transcripts if t["text"] == "[Transcription failed]"])
            }
            
            await TranscriptionJobStore.set_stage_checkpoint(job.id, stage, merge_results)
            
            # Update job with results
            await TranscriptionJobStore.set_job_results(job.id, {
                "word_count": total_words
            })
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
            
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to next stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.DIARIZING, 0.0)
            logger.info(f"✅ Job {job.id}: Merge complete ({total_words} words)")
            
        except Exception as e:
            await self.handle_job_error(job.id, "MERGE_FAILED", str(e))
    
    async def stage_diarize(self, job: TranscriptionJob):
        """Stage 7: Speaker diarization (simplified for Phase 2)"""
        stage = TranscriptionStage.DIARIZING
        logger.info(f"👥 Job {job.id}: Speaker diarization")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 20.0)
        
        try:
            job_data = await TranscriptionJobStore.get_job(job.id)
            
            # For Phase 2, we'll skip speaker diarization if not enabled
            # or implement a simplified version
            if not job_data.enable_diarization:
                logger.info(f"Diarization disabled for job {job.id}, skipping")
                await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
                
                # Record stage completion
                duration_seconds = time.time() - start_time
                await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
                
                # Move to next stage
                await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.GENERATING_OUTPUTS, 0.0)
                return
            
            # Get merge results
            checkpoint = await TranscriptionJobStore.get_stage_checkpoint(job.id, TranscriptionStage.MERGING)
            if not checkpoint:
                raise Exception("Merge data not found")
            
            final_transcript = checkpoint.get("final_transcript", "")
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 50.0)
            
            # Simplified diarization - just label as single speaker for now
            # In Phase 3, this would integrate with proper diarization models
            diarized_transcript = f"Speaker 1: {final_transcript}"
            
            diarization_results = {
                "diarized_transcript": diarized_transcript,
                "speaker_count": 1,
                "speakers": [{"id": "Speaker 1", "duration": job_data.total_duration or 0}]
            }
            
            await TranscriptionJobStore.set_stage_checkpoint(job.id, stage, diarization_results)
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
            
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to next stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.GENERATING_OUTPUTS, 0.0)
            logger.info(f"✅ Job {job.id}: Diarization complete")
            
        except Exception as e:
            await self.handle_job_error(job.id, "DIARIZATION_FAILED", str(e))
    
    async def stage_generate_outputs(self, job: TranscriptionJob):
        """Stage 8: Generate multiple output formats"""
        stage = TranscriptionStage.GENERATING_OUTPUTS
        logger.info(f"📄 Job {job.id}: Generating output formats")
        
        start_time = time.time()
        await TranscriptionJobStore.update_job_stage(job.id, stage, 10.0)
        
        try:
            # Get final transcript data
            merge_checkpoint = await TranscriptionJobStore.get_stage_checkpoint(job.id, TranscriptionStage.MERGING)
            diarization_checkpoint = await TranscriptionJobStore.get_stage_checkpoint(job.id, TranscriptionStage.DIARIZING)
            
            if not merge_checkpoint:
                raise Exception("Merge data not found")
            
            final_transcript = merge_checkpoint.get("final_transcript", "")
            diarized_transcript = diarization_checkpoint.get("diarized_transcript", final_transcript) if diarization_checkpoint else final_transcript
            
            # Get detailed segments for JSON/SRT/VTT generation
            transcription_checkpoint = await TranscriptionJobStore.get_stage_checkpoint(job.id, TranscriptionStage.TRANSCRIBING)
            segments = transcription_checkpoint.get("transcripts", []) if transcription_checkpoint else []
            
            assets_created = []
            
            # Generate TXT format
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 20.0)
            txt_content = diarized_transcript
            txt_key = await store_file_content_async(txt_content.encode('utf-8'), f"job_{job.id}_transcript.txt")
            
            txt_asset = TranscriptionAsset(
                job_id=job.id,
                kind="txt",
                storage_key=txt_key,
                file_size=len(txt_content.encode('utf-8')),
                mime_type="text/plain"
            )
            await TranscriptionAssetStore.create_asset(txt_asset)
            assets_created.append("txt")
            
            # Generate JSON format
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 40.0)
            json_data = {
                "transcript": final_transcript,
                "diarized_transcript": diarized_transcript,
                "segments": segments,
                "metadata": {
                    "language": job.detected_language,
                    "duration": job.total_duration,
                    "word_count": merge_checkpoint.get("word_count", 0),
                    "confidence": 0.95  # Simplified confidence
                }
            }
            
            import json
            json_content = json.dumps(json_data, indent=2, ensure_ascii=False)
            json_key = await store_file_content_async(json_content.encode('utf-8'), f"job_{job.id}_transcript.json")
            
            json_asset = TranscriptionAsset(
                job_id=job.id,
                kind="json",
                storage_key=json_key,
                file_size=len(json_content.encode('utf-8')),
                mime_type="application/json"
            )
            await TranscriptionAssetStore.create_asset(json_asset)
            assets_created.append("json")
            
            # Generate SRT format
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 60.0)
            srt_content = self._generate_srt(segments)
            srt_key = await store_file_content_async(srt_content.encode('utf-8'), f"job_{job.id}_transcript.srt")
            
            srt_asset = TranscriptionAsset(
                job_id=job.id,
                kind="srt",
                storage_key=srt_key,
                file_size=len(srt_content.encode('utf-8')),
                mime_type="application/x-subrip"
            )
            await TranscriptionAssetStore.create_asset(srt_asset)
            assets_created.append("srt")
            
            # Generate VTT format
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 80.0)
            vtt_content = self._generate_vtt(segments)
            vtt_key = await store_file_content_async(vtt_content.encode('utf-8'), f"job_{job.id}_transcript.vtt")
            
            vtt_asset = TranscriptionAsset(
                job_id=job.id,
                kind="vtt",
                storage_key=vtt_key,
                file_size=len(vtt_content.encode('utf-8')),
                mime_type="text/vtt"
            )
            await TranscriptionAssetStore.create_asset(vtt_asset)
            assets_created.append("vtt")
            
            await TranscriptionJobStore.update_stage_progress(job.id, stage, 100.0)
            
            # Store output results
            output_results = {
                "assets_created": assets_created,
                "output_formats": ["txt", "json", "srt", "vtt"]
            }
            await TranscriptionJobStore.set_stage_checkpoint(job.id, stage, output_results)
            
            # Record stage completion
            duration_seconds = time.time() - start_time
            await TranscriptionJobStore.record_stage_duration(job.id, stage, duration_seconds)
            
            # Move to final stage
            await TranscriptionJobStore.update_job_stage(job.id, TranscriptionStage.COMPLETE, 0.0)
            logger.info(f"✅ Job {job.id}: Output generation complete ({len(assets_created)} formats)")
            
        except Exception as e:
            await self.handle_job_error(job.id, "OUTPUT_GENERATION_FAILED", str(e))
    
    def _generate_srt(self, segments):
        """Generate SRT subtitle format"""
        srt_lines = []
        
        for i, segment in enumerate(segments, 1):
            if segment.get("text") and segment["text"] != "[Transcription failed]":
                start_time = self._seconds_to_srt_time(segment["start_time"])
                end_time = self._seconds_to_srt_time(segment["end_time"])
                
                srt_lines.extend([
                    str(i),
                    f"{start_time} --> {end_time}",
                    segment["text"].strip(),
                    ""
                ])
        
        return "\n".join(srt_lines)
    
    def _generate_vtt(self, segments):
        """Generate WebVTT format"""
        vtt_lines = ["WEBVTT", ""]
        
        for segment in segments:
            if segment.get("text") and segment["text"] != "[Transcription failed]":
                start_time = self._seconds_to_vtt_time(segment["start_time"])
                end_time = self._seconds_to_vtt_time(segment["end_time"])
                
                vtt_lines.extend([
                    f"{start_time} --> {end_time}",
                    segment["text"].strip(),
                    ""
                ])
        
        return "\n".join(vtt_lines)
    
    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _seconds_to_vtt_time(self, seconds):
        """Convert seconds to VTT time format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

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