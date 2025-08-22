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

def get_file_url(file_key: str) -> str:
    """Get URL for accessing stored file"""
    file_path = STORAGE_DIR / file_key
    if file_path.exists():
        return f"file://{file_path}"
    raise FileNotFoundError(f"File not found: {file_key}")

def create_presigned_get_url(file_key: str) -> str:
    """Create a presigned URL for file access (simplified for local storage)"""
    return get_file_url(file_key)