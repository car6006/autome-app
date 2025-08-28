"""
Phase 4: Production-grade cloud storage integration
Supports multiple storage backends: local, S3, Google Cloud Storage
"""
import os
import uuid
import boto3
import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class StorageBackend(ABC):
    """Abstract storage backend interface"""
    
    @abstractmethod
    async def store_file(self, content: bytes, key: str, metadata: Optional[Dict] = None) -> str:
        """Store file and return storage key"""
        pass
    
    @abstractmethod
    async def get_file(self, key: str) -> bytes:
        """Retrieve file content"""
        pass
    
    @abstractmethod
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Get presigned URL for file access"""
        pass
    
    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    async def file_exists(self, key: str) -> bool:
        """Check if file exists"""
        pass
    
    @abstractmethod
    async def get_file_metadata(self, key: str) -> Dict[str, Any]:
        """Get file metadata"""
        pass

class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, storage_dir: str = "/tmp/autome_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True, parents=True)
    
    async def store_file(self, content: bytes, key: str, metadata: Optional[Dict] = None) -> str:
        """Store file locally"""
        file_path = self.storage_dir / key
        file_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Store file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store metadata
        if metadata:
            metadata_path = file_path.with_suffix(f"{file_path.suffix}.meta")
            with open(metadata_path, "w") as f:
                import json
                json.dump({
                    **metadata,
                    "stored_at": datetime.now(timezone.utc).isoformat(),
                    "size": len(content)
                }, f)
        
        return key
    
    async def get_file(self, key: str) -> bytes:
        """Retrieve file content"""
        file_path = self.storage_dir / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        
        with open(file_path, "rb") as f:
            return f.read()
    
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Get file path (local files don't need presigned URLs)"""
        file_path = self.storage_dir / key
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return str(file_path.absolute())
    
    async def delete_file(self, key: str) -> bool:
        """Delete file"""
        try:
            file_path = self.storage_dir / key
            if file_path.exists():
                file_path.unlink()
            
            # Delete metadata if exists
            metadata_path = file_path.with_suffix(f"{file_path.suffix}.meta")
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {key}: {e}")
            return False
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists"""
        file_path = self.storage_dir / key
        return file_path.exists()
    
    async def get_file_metadata(self, key: str) -> Dict[str, Any]:
        """Get file metadata"""
        file_path = self.storage_dir / key
        metadata_path = file_path.with_suffix(f"{file_path.suffix}.meta")
        
        metadata = {}
        if file_path.exists():
            stat = file_path.stat()
            metadata.update({
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "exists": True
            })
        
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                import json
                stored_metadata = json.load(f)
                metadata.update(stored_metadata)
        
        return metadata

class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend"""
    
    def __init__(self, bucket_name: str, aws_access_key: Optional[str] = None, 
                 aws_secret_key: Optional[str] = None, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        session = boto3.Session(
            aws_access_key_id=aws_access_key or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region
        )
        
        self.s3_client = session.client("s3")
        self.s3_resource = session.resource("s3")
        
        # Ensure bucket exists
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 bucket {bucket_name} is accessible")
        except Exception as e:
            logger.warning(f"S3 bucket {bucket_name} not accessible: {e}")
    
    async def store_file(self, content: bytes, key: str, metadata: Optional[Dict] = None) -> str:
        """Store file in S3"""
        try:
            extra_args = {}
            
            if metadata:
                # S3 metadata must be strings
                s3_metadata = {k: str(v) for k, v in metadata.items()}
                extra_args["Metadata"] = s3_metadata
            
            # Add default metadata
            extra_args["Metadata"] = {
                **extra_args.get("Metadata", {}),
                "stored-at": datetime.now(timezone.utc).isoformat(),
                "size": str(len(content))
            }
            
            # Upload to S3
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                    **extra_args
                )
            )
            
            return key
        except Exception as e:
            logger.error(f"Failed to store file in S3: {e}")
            raise e
    
    async def get_file(self, key: str) -> bytes:
        """Retrieve file from S3"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            )
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to retrieve file from S3: {e}")
            raise FileNotFoundError(f"File not found in S3: {key}")
    
    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for S3 object"""
        try:
            url = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expires_in
                )
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise e
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            )
            return True
        except Exception as e:
            return False
    
    async def get_file_metadata(self, key: str) -> Dict[str, Any]:
        """Get S3 object metadata"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            )
            
            metadata = {
                "size": response.get("ContentLength", 0),
                "last_modified": response.get("LastModified", "").isoformat() if response.get("LastModified") else None,
                "content_type": response.get("ContentType", ""),
                "etag": response.get("ETag", "").strip('"'),
                "exists": True
            }
            
            # Add custom metadata
            if "Metadata" in response:
                metadata.update(response["Metadata"])
            
            return metadata
        except Exception as e:
            logger.error(f"Failed to get S3 metadata: {e}")
            return {"exists": False}

class StorageManager:
    """Production storage manager with multiple backend support"""
    
    def __init__(self):
        self.backend = self._initialize_backend()
        self.usage_stats = {
            "files_stored": 0,
            "bytes_stored": 0,
            "files_retrieved": 0,
            "bytes_retrieved": 0
        }
    
    def _initialize_backend(self) -> StorageBackend:
        """Initialize storage backend based on configuration"""
        storage_type = os.getenv("STORAGE_TYPE", "local").lower()
        
        if storage_type == "s3":
            bucket_name = os.getenv("S3_BUCKET_NAME", "autome-transcription-storage")
            return S3StorageBackend(bucket_name)
        elif storage_type == "local":
            storage_dir = os.getenv("LOCAL_STORAGE_DIR", "/tmp/autome_storage")
            return LocalStorageBackend(storage_dir)
        else:
            logger.warning(f"Unknown storage type: {storage_type}, falling back to local")
            return LocalStorageBackend()
    
    async def store_file(self, content: Union[bytes, str], filename: str, 
                        user_id: Optional[str] = None, job_id: Optional[str] = None,
                        metadata: Optional[Dict] = None) -> str:
        """Store file with enhanced metadata and organization"""
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        # Generate organized storage key
        timestamp = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        file_uuid = str(uuid.uuid4())
        
        if job_id:
            storage_key = f"jobs/{job_id}/{file_uuid}_{filename}"
        elif user_id:
            storage_key = f"users/{user_id}/{timestamp}/{file_uuid}_{filename}"
        else:
            storage_key = f"temp/{timestamp}/{file_uuid}_{filename}"
        
        # Enhanced metadata
        enhanced_metadata = {
            "filename": filename,
            "user_id": user_id,
            "job_id": job_id,
            "content_type": self._get_content_type(filename),
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {})
        }
        
        try:
            result_key = await self.backend.store_file(content, storage_key, enhanced_metadata)
            
            # Update usage stats
            self.usage_stats["files_stored"] += 1
            self.usage_stats["bytes_stored"] += len(content)
            
            logger.info(f"Stored file: {filename} -> {result_key} ({len(content)} bytes)")
            return result_key
            
        except Exception as e:
            logger.error(f"Failed to store file {filename}: {e}")
            raise e
    
    async def get_file(self, storage_key: str) -> bytes:
        """Retrieve file with usage tracking"""
        try:
            content = await self.backend.get_file(storage_key)
            
            # Update usage stats
            self.usage_stats["files_retrieved"] += 1
            self.usage_stats["bytes_retrieved"] += len(content)
            
            return content
        except Exception as e:
            logger.error(f"Failed to retrieve file {storage_key}: {e}")
            raise e
    
    async def get_file_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """Get presigned URL for file access"""
        return await self.backend.get_file_url(storage_key, expires_in)
    
    async def delete_file(self, storage_key: str) -> bool:
        """Delete file with cleanup tracking"""
        return await self.backend.delete_file(storage_key)
    
    async def file_exists(self, storage_key: str) -> bool:
        """Check if file exists"""
        return await self.backend.file_exists(storage_key)
    
    async def get_file_metadata(self, storage_key: str) -> Dict[str, Any]:
        """Get comprehensive file metadata"""
        return await self.backend.get_file_metadata(storage_key)
    
    async def cleanup_expired_files(self, older_than_days: int = 30) -> int:
        """Cleanup old files (implementation depends on backend)"""
        # This would be implemented based on the storage backend
        # For now, return 0 as cleanup count
        logger.info(f"Cleanup requested for files older than {older_than_days} days")
        return 0
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        return {
            **self.usage_stats,
            "backend_type": type(self.backend).__name__,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename"""
        extension = Path(filename).suffix.lower()
        
        content_types = {
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.webm': 'audio/webm',
            '.ogg': 'audio/ogg',
            '.srt': 'application/x-subrip',
            '.vtt': 'text/vtt'
        }
        
        return content_types.get(extension, 'application/octet-stream')

# Global storage manager instance
storage_manager = StorageManager()

# Convenience functions for backward compatibility
async def store_file_content_async(content: bytes, filename: str, **kwargs) -> str:
    """Store file content (backward compatibility)"""
    return await storage_manager.store_file(content, filename, **kwargs)

async def get_file_path(storage_key: str) -> str:
    """Get file path/URL (backward compatibility)"""
    return await storage_manager.get_file_url(storage_key)

def get_file_path_sync(storage_key: str) -> str:
    """Synchronous version that directly accesses local storage"""
    # For local storage, we can directly construct the path
    storage_dir = Path(os.getenv("LOCAL_STORAGE_DIR", "/tmp/autome_storage"))
    file_path = storage_dir / storage_key
    
    if file_path.exists():
        return str(file_path.absolute())
    else:
        # Try to find the file in common locations
        possible_paths = [
            storage_dir / storage_key,
            Path("/tmp/autome_storage") / storage_key,
            Path("./storage") / storage_key
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path.absolute())
        
        raise FileNotFoundError(f"File not found: {storage_key}")