import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

# Simple local storage for development
STORAGE_DIR = Path("/tmp/autome_storage")
STORAGE_DIR.mkdir(exist_ok=True)

def store_file(file_data: bytes, filename: str) -> str:
    """Store file locally and return a key"""
    file_key = str(uuid.uuid4()) + "_" + filename
    file_path = STORAGE_DIR / file_key
    
    with open(file_path, "wb") as f:
        f.write(file_data)
    
    return file_key

def get_file_path(file_key: str) -> Path:
    """Get local file path for stored file"""
    file_path = STORAGE_DIR / file_key
    if file_path.exists():
        return file_path
    raise FileNotFoundError(f"File not found: {file_key}")

def get_file_url(file_key: str) -> str:
    """Get URL for accessing stored file"""
    file_path = STORAGE_DIR / file_key
    if file_path.exists():
        return f"file://{file_path}"
    raise FileNotFoundError(f"File not found: {file_key}")

def store_file_content(content: bytes, filename: str) -> str:
    """Store content as file and return a key"""
    file_key = str(uuid.uuid4()) + "_" + filename
    file_path = STORAGE_DIR / file_key
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_key

async def store_file_content_async(content: bytes, filename: str) -> str:
    """Async version of store_file_content"""
    return store_file_content(content, filename)

def create_presigned_get_url(file_key: str) -> str:
    """Create a presigned URL for file access (returns local path for processing)"""
    if not file_key:
        raise ValueError("File key cannot be None or empty")
    file_path = get_file_path(file_key)
    return str(file_path)  # Return absolute path for local processing