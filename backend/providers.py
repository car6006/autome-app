from __future__ import annotations
import base64, os, tempfile, httpx, asyncio
import logging
import subprocess
import math
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Constants
OPENAI_MAX_FILE_SIZE = 24 * 1024 * 1024  # 24MB to be safe (OpenAI limit is 25MB)
CHUNK_DURATION_SECONDS = 300  # 5 minutes per chunk

OPENAI_STT = "openai"
AZURE_OCR = "azure"
GCV_OCR = "gcv"

async def get_audio_duration(file_path: str) -> float:
    """Get audio duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        else:
            logger.warning(f"Could not get audio duration for {file_path}")
            return 0.0
    except Exception as e:
        logger.warning(f"Error getting audio duration: {e}")
        return 0.0

async def split_audio_file(file_path: str, chunk_duration: int = CHUNK_DURATION_SECONDS) -> list[str]:
    """Split audio file into smaller chunks using ffmpeg"""
    chunks = []
    
    try:
        duration = await get_audio_duration(file_path)
        if duration <= 0:
            logger.warning(f"Could not determine audio duration, processing as single file")
            return [file_path]
        
        num_chunks = math.ceil(duration / chunk_duration)
        logger.info(f"Splitting {duration:.1f}s audio into {num_chunks} chunks of {chunk_duration}s each")
        
        for i in range(num_chunks):
            start_time = i * chunk_duration
            
            # Create temporary file for chunk
            chunk_fd, chunk_path = tempfile.mkstemp(suffix='.wav')
            os.close(chunk_fd)
            
            cmd = [
                'ffmpeg', '-i', file_path,
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-acodec', 'pcm_s16le',  # Use WAV format for compatibility
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                chunk_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                chunks.append(chunk_path)
                logger.info(f"Created chunk {i+1}/{num_chunks}: {chunk_path}")
            else:
                logger.error(f"Failed to create chunk {i+1}: {result.stderr}")
                # Clean up failed chunk
                try:
                    os.unlink(chunk_path)
                except:
                    pass
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error splitting audio file: {e}")
        return [file_path]  # Return original file if splitting fails

async def transcribe_audio_chunk(chunk_path: str, api_key: str) -> str:
    """Transcribe a single audio chunk"""
    try:
        with open(chunk_path, "rb") as audio_file:
            files = {"file": audio_file}
            form = {"model": "whisper-1", "response_format": "json"}
            
            async with httpx.AsyncClient(timeout=600) as client:  # 10 minute timeout per chunk
                r = await client.post(
                    f'{os.getenv("WHISPER_API_BASE","https://api.openai.com/v1")}/audio/transcriptions',
                    data=form,
                    files=files,
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                r.raise_for_status()
                data = r.json()
                return data.get("text", "")
                
    except Exception as e:
        logger.error(f"Error transcribing chunk {chunk_path}: {e}")
        return ""

async def _download(url: str) -> str:
    """Download file from URL or return local path if it's a local file"""
    # Check if it's a local file path
    if os.path.exists(url):
        return url
    
    # Otherwise download from URL
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, follow_redirects=True)
        r.raise_for_status()
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "wb") as f:
            f.write(r.content)
        return path

async def stt_transcribe(file_url: str):
    """
    Perform speech-to-text transcription with automatic chunking for large files
    """
    key = os.getenv("WHISPER_API_KEY")
    if not key:
        return {"text": "", "summary": "", "actions": [], "note": "missing WHISPER_API_KEY"}
    
    if (os.getenv("STT_PROVIDER") or OPENAI_STT).lower() == OPENAI_STT:
        local = await _download(file_url)
        
        try:
            # Check file size
            file_size = os.path.getsize(local)
            logger.info(f"Audio file size: {file_size / (1024*1024):.1f} MB")
            
            if file_size <= OPENAI_MAX_FILE_SIZE:
                # Small file - process normally
                logger.info("File size OK, processing directly")
                
                with open(local, "rb") as audio_file:
                    files = {"file": audio_file}
                    form = {"model": "whisper-1", "response_format": "json"}
                    
                    async with httpx.AsyncClient(timeout=300) as client:
                        r = await client.post(
                            f'{os.getenv("WHISPER_API_BASE","https://api.openai.com/v1")}/audio/transcriptions',
                            data=form,
                            files=files,
                            headers={"Authorization": f"Bearer {key}"}
                        )
                        r.raise_for_status()
                        data = r.json()
                        text = data.get("text", "")
                        return {"text": text, "summary": "", "actions": []}
            
            else:
                # Large file - split into chunks
                logger.info(f"File too large ({file_size / (1024*1024):.1f} MB), splitting into chunks")
                
                chunks = await split_audio_file(local)
                if not chunks:
                    return {"text": "", "summary": "", "actions": [], "note": "Failed to split audio file"}
                
                logger.info(f"Processing {len(chunks)} audio chunks")
                transcriptions = []
                
                # Process each chunk
                for i, chunk_path in enumerate(chunks):
                    try:
                        logger.info(f"Transcribing chunk {i+1}/{len(chunks)}")
                        chunk_text = await transcribe_audio_chunk(chunk_path, key)
                        
                        if chunk_text.strip():
                            # Add chunk number for long transcriptions
                            if len(chunks) > 1:
                                transcriptions.append(f"[Part {i+1}] {chunk_text}")
                            else:
                                transcriptions.append(chunk_text)
                        
                    except Exception as e:
                        logger.error(f"Error processing chunk {i+1}: {e}")
                        transcriptions.append(f"[Part {i+1}] Error processing this segment")
                    
                    finally:
                        # Clean up chunk file
                        try:
                            os.unlink(chunk_path)
                        except:
                            pass
                
                # Combine all transcriptions
                full_text = " ".join(transcriptions).strip()
                
                if not full_text:
                    return {"text": "", "summary": "", "actions": [], "note": "No transcription generated from chunks"}
                
                logger.info(f"Successfully transcribed {len(chunks)} chunks, total length: {len(full_text)} characters")
                return {"text": full_text, "summary": "", "actions": []}
                
        finally:
            # Clean up original temporary file
            try:
                if local != file_url:  # Only delete if it was downloaded
                    os.unlink(local)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {local}: {e}")
    
    raise RuntimeError("Unsupported STT_PROVIDER")

async def ocr_read(file_url: str):
    """
    Perform OCR on image using OpenAI Vision API
    """
    which = (os.getenv("OCR_PROVIDER") or "openai").lower()
    local = await _download(file_url)
    
    try:
        if which == "openai":
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
            if not api_key:
                return {"text":"", "summary":"", "actions":[], "note":"missing OPENAI_API_KEY"}
            
            # Check if it's a PDF file
            if local.lower().endswith('.pdf'):
                try:
                    # For PDFs, we'll extract text directly using a simple approach
                    # Note: This is a basic implementation. For production, consider using PyPDF2 or similar
                    with open(local, "rb") as f:
                        content = f.read()
                    
                    # Try to extract text from PDF (very basic approach)
                    text_content = ""
                    try:
                        # Convert bytes to string and look for readable text
                        content_str = content.decode('latin1', errors='ignore')
                        # Simple text extraction - look for readable characters
                        import re
                        text_matches = re.findall(r'[A-Za-z0-9\s\.,!?;:()"\'-]+', content_str)
                        text_content = ' '.join([match.strip() for match in text_matches if len(match.strip()) > 3])
                        
                        if len(text_content) < 10:
                            return {"text": "PDF text extraction failed. This PDF may contain images or be encrypted. Please try converting to an image format (PNG/JPG) first.", "summary": "", "actions": []}
                        
                        return {"text": text_content[:2000], "summary": "", "actions": []}  # Limit to 2000 chars
                    except Exception as e:
                        return {"text": "PDF processing not fully supported yet. Please convert your PDF to an image (PNG/JPG) for better OCR results.", "summary": "", "actions": []}
                        
                except Exception as e:
                    return {"text": "PDF processing failed. Please try uploading an image format (PNG, JPG) instead.", "summary": "", "actions": []}
            
            # For image files, continue with OpenAI Vision API
            # Convert image to base64
            with open(local, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
                
            # Determine image format
            image_format = "jpeg"
            if local.lower().endswith('.png'):
                image_format = "png"
            elif local.lower().endswith('.webp'):
                image_format = "webp"
            elif local.lower().endswith('.gif'):
                return {"text": "GIF files are not supported for OCR. Please use PNG or JPG.", "summary": "", "actions": []}
            
            # Use OpenAI Vision API
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image. Return only the extracted text, no explanations or formatting. If no text is found, return 'No text detected'."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                r.raise_for_status()
                data = r.json()
                
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"text": text, "summary":"", "actions":[]}
        
        elif which == "gcv":
            # Keep Google Vision as fallback
            api_key = os.getenv("GCV_API_KEY")
            if not api_key:
                return {"text":"", "summary":"", "actions":[], "note":"missing GCV_API_KEY"}
            
            with open(local, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            
            payload = {
                "requests": [{
                    "image": {"content": b64},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                }]
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
                    json=payload
                )
                r.raise_for_status()
                data = r.json()
                text = data.get("responses",[{}])[0].get("fullTextAnnotation",{}).get("text","") or ""
                return {"text": text, "summary":"", "actions":[]}
        
        raise RuntimeError("Unsupported OCR_PROVIDER")
    finally:
        # Clean up temporary file
        try:
            os.unlink(local)
        except Exception as e:
            logger.warning(f"Failed to clean up temp file {local}: {e}")