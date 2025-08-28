"""
Enhanced data models for large-file audio transcription pipeline
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid

# Upload Session Models
class UploadSession(BaseModel):
    """Resumable upload session"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    filename: str
    total_size: int
    mime_type: str
    chunk_size: int = 5 * 1024 * 1024  # 5MB default
    chunks_uploaded: List[int] = Field(default_factory=list)  # List of chunk indices uploaded
    sha256: Optional[str] = None
    status: str = "active"  # active, completed, expired, failed
    storage_key: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(hour=23, minute=59, second=59))
    completed_at: Optional[datetime] = None

# Transcription Job Models
class TranscriptionStage(str, Enum):
    """Pipeline stages for transcription jobs"""
    CREATED = "created"
    QUEUED = "queued" 
    VALIDATING = "validating"
    TRANSCODING = "transcoding"
    SEGMENTING = "segmenting"
    DETECTING_LANGUAGE = "detecting_language"
    TRANSCRIBING = "transcribing"
    MERGING = "merging"
    DIARIZING = "diarizing"
    GENERATING_OUTPUTS = "generating_outputs"
    COMPLETE = "complete"
    FAILED = "failed"

class TranscriptionStatus(str, Enum):
    """Overall job status"""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TranscriptionJob(BaseModel):
    """Main transcription job with pipeline tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    upload_id: str  # Reference to UploadSession
    
    # Job configuration
    filename: str
    total_size: int
    mime_type: str
    language: Optional[str] = None  # Auto-detect if None
    enable_diarization: bool = True
    model: str = "whisper-large-v3"
    
    # Phase 3: Advanced processing options
    enable_ai_diarization: bool = True  # Use AI for better speaker detection
    enable_multi_language: bool = False  # Multi-language detection
    output_formats: List[str] = Field(default_factory=lambda: ["txt", "json", "srt", "vtt", "docx"])
    processing_priority: str = "normal"  # normal, high, low
    
    # Pipeline state
    status: TranscriptionStatus = TranscriptionStatus.CREATED
    current_stage: TranscriptionStage = TranscriptionStage.CREATED
    progress: float = 0.0  # 0-100
    
    # Stage tracking
    stage_progress: Dict[str, float] = Field(default_factory=dict)  # Per-stage progress
    stage_durations: Dict[str, float] = Field(default_factory=dict)  # Duration in seconds
    stage_checkpoints: Dict[str, Any] = Field(default_factory=dict)  # Resume data
    
    # Results
    detected_language: Optional[str] = None
    confidence_score: Optional[float] = None
    total_duration: Optional[float] = None  # Audio duration in seconds
    word_count: Optional[int] = None
    
    # Error handling
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Storage references
    storage_paths: Dict[str, str] = Field(default_factory=dict)  # normalized_audio, segments, etc.

class TranscriptionAsset(BaseModel):
    """Output files generated from transcription"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    kind: str  # txt, json, srt, vtt, docx, waveform, segments
    storage_key: str
    file_size: int
    mime_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request/Response Models
class UploadSessionRequest(BaseModel):
    """Request to create upload session"""
    filename: str
    total_size: int
    mime_type: str
    language: Optional[str] = None
    enable_diarization: bool = True

class UploadSessionResponse(BaseModel):
    """Response with upload session details"""
    upload_id: str
    chunk_size: int
    max_duration_hours: int = 10
    allowed_mime_types: List[str] = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/webm", "audio/ogg"]
    presigned_urls: Optional[Dict[int, str]] = None  # For S3 multipart
    tus_endpoint: Optional[str] = None  # For tus.io resumable uploads

class ChunkUploadResponse(BaseModel):
    """Response after chunk upload"""
    chunk_index: int
    uploaded: bool
    next_chunk_url: Optional[str] = None

class FinalizeUploadRequest(BaseModel):
    """Request to finalize upload"""
    upload_id: str
    sha256: Optional[str] = None

class FinalizeUploadResponse(BaseModel):
    """Response with job ID"""
    job_id: str
    upload_id: str
    status: str

class JobStatusResponse(BaseModel):
    """Job status and progress response"""
    job_id: str
    status: TranscriptionStatus
    current_stage: TranscriptionStage
    progress: float
    stage_progress: Dict[str, float]
    durations: Dict[str, float]
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    
    # Results (when available)
    detected_language: Optional[str] = None
    confidence_score: Optional[float] = None
    total_duration: Optional[float] = None
    word_count: Optional[int] = None
    
    # Downloads (when complete)
    download_urls: Optional[Dict[str, str]] = None

class RetryJobRequest(BaseModel):
    """Request to retry failed job"""
    job_id: str
    from_stage: Optional[TranscriptionStage] = None  # Resume from specific stage

# Configuration Models
class PipelineConfig(BaseModel):
    """Pipeline configuration"""
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    max_duration_hours: int = 10
    chunk_size: int = 5 * 1024 * 1024  # 5MB
    segment_duration: int = 60  # seconds
    segment_overlap: float = 1.0  # seconds
    max_concurrent_jobs: int = 10
    max_concurrent_segments: int = 5
    
    # Allowed file types
    allowed_mime_types: List[str] = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/webm", "audio/ogg", "audio/x-wav", "audio/wave"]
    
    # Model configuration
    whisper_model: str = "whisper-large-v3"
    fallback_model: str = "whisper-base"
    temperature: float = 0.2
    
    # Storage configuration
    storage_bucket: str = "transcription-pipeline"
    presigned_url_expiry: int = 3600  # 1 hour
    
    # Retention policy (days)
    raw_upload_retention: int = 30
    processed_files_retention: int = 14
    final_outputs_retention: int = 365

# Storage path helpers
def get_upload_path(user_id: str, upload_id: str, filename: str) -> str:
    """Generate storage path for uploads"""
    return f"uploads/{user_id or 'anonymous'}/{upload_id}/{filename}"

def get_job_path(job_id: str, file_type: str) -> str:
    """Generate storage path for job files"""
    return f"jobs/{job_id}/{file_type}"

def get_output_path(job_id: str, format: str) -> str:
    """Generate storage path for output files"""
    return f"jobs/{job_id}/outputs/transcript.{format}"