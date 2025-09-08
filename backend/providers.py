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
CHUNK_DURATION_SECONDS = 240  # 4 minutes per chunk (reduced from 5 for better reliability)

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

async def transcribe_audio_chunk(chunk_path: str, api_key: str, language: str = "en", max_retries: int = 5) -> str:
    """Transcribe a single audio chunk with enhanced retry logic for OpenAI rate limiting"""
    import random
    
    for attempt in range(max_retries):
        try:
            with open(chunk_path, "rb") as audio_file:
                files = {"file": audio_file}
                form = {
                    "model": "whisper-1", 
                    "response_format": "json",
                    "language": language  # Explicitly specify language
                }
                
                async with httpx.AsyncClient(timeout=600) as client:  # 10 minute timeout per chunk
                    r = await client.post(
                        f'{os.getenv("WHISPER_API_BASE","https://api.openai.com/v1")}/audio/transcriptions',
                        data=form,
                        files=files,
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    r.raise_for_status()
                    data = r.json()
                    text_result = data.get("text", "")
                    if text_result:
                        logger.info(f"✅ Successfully transcribed chunk: {os.path.basename(chunk_path)}")
                    return text_result
                    
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit error
                # Get retry-after header if available
                retry_after = e.response.headers.get('retry-after')
                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(f"🚦 OpenAI rate limit (retry-after: {wait_time}s) for {os.path.basename(chunk_path)} (attempt {attempt + 1}/{max_retries})")
                else:
                    # Enhanced exponential backoff with jitter for rate limits
                    base_wait = (2 ** attempt) * 15  # 15s, 30s, 60s, 120s, 240s
                    jitter = random.uniform(0.1, 0.3) * base_wait  # Add 10-30% jitter
                    wait_time = base_wait + jitter
                    logger.warning(f"🚦 OpenAI rate limit hit for {os.path.basename(chunk_path)}, backing off {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ OpenAI rate limit exceeded after {max_retries} attempts for {os.path.basename(chunk_path)}")
                    return ""
                    
            elif e.response.status_code == 500:  # Server error - retry with shorter backoff
                wait_time = (2 ** attempt) * 3  # 3s, 6s, 12s, 24s, 48s
                logger.warning(f"🔧 OpenAI server error for {os.path.basename(chunk_path)}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ OpenAI server errors exceeded after {max_retries} attempts for {os.path.basename(chunk_path)}")
                    return ""
            else:
                logger.error(f"❌ HTTP error transcribing chunk {os.path.basename(chunk_path)}: {e.response.status_code} - {e.response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Error transcribing chunk {os.path.basename(chunk_path)} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return ""
            await asyncio.sleep(2 ** attempt)  # Simple backoff for other errors
    
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
                # Small file - process with retry logic for rate limits
                logger.info("File size OK, processing directly with rate limit handling")
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with open(local, "rb") as audio_file:
                            files = {"file": audio_file}
                            form = {"model": "whisper-1", "response_format": "json", "language": "en"}
                            
                            async with httpx.AsyncClient(timeout=600) as client:  # 10 minute timeout
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
                                
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 429:  # Rate limit error
                            wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                            logger.warning(f"Rate limit hit for small file, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        elif e.response.status_code == 500:  # Server error - retry
                            wait_time = (2 ** attempt) * 3  # Exponential backoff: 3s, 6s, 12s
                            logger.warning(f"OpenAI server error for small file, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"HTTP error transcribing small file: {e.response.status_code} - {e.response.text}")
                            return {"text": "", "summary": "", "actions": [], "note": f"Transcription failed: HTTP {e.response.status_code}"}
                    except Exception as e:
                        logger.error(f"Error transcribing small file (attempt {attempt + 1}): {e}")
                        if attempt == max_retries - 1:
                            return {"text": "", "summary": "", "actions": [], "note": "Transcription failed after retries"}
                        await asyncio.sleep(2 ** attempt)  # Simple backoff for other errors
                
                return {"text": "", "summary": "", "actions": [], "note": "Transcription failed after all retries"}
            
            else:
                # Large file - split into chunks
                logger.info(f"File too large ({file_size / (1024*1024):.1f} MB), splitting into chunks")
                
                chunks = await split_audio_file(local)
                if not chunks:
                    return {"text": "", "summary": "", "actions": [], "note": "Failed to split audio file"}
                
                logger.info(f"Processing {len(chunks)} audio chunks")
                transcriptions = []
                
                # Process each chunk sequentially with delays to avoid rate limits
                for i, chunk_path in enumerate(chunks):
                    try:
                        logger.info(f"Transcribing chunk {i+1}/{len(chunks)}")
                        chunk_text = await transcribe_audio_chunk(chunk_path, key, "en")
                        
                        if chunk_text.strip():
                            # Add chunk number for long transcriptions
                            if len(chunks) > 1:
                                transcriptions.append(f"[Part {i+1}] {chunk_text}")
                            else:
                                transcriptions.append(chunk_text)
                        else:
                            logger.warning(f"Empty transcription for chunk {i+1}")
                        
                        # Add delay between chunks to respect rate limits (except for last chunk)
                        if i < len(chunks) - 1:
                            logger.info(f"Waiting 3 seconds before processing next chunk...")
                            await asyncio.sleep(3)
                        
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
    Perform OCR on image using OpenAI Vision API with enhanced retry logic for rate limiting
    """
    which = (os.getenv("OCR_PROVIDER") or "openai").lower()
    local = await _download(file_url)
    
    try:
        if which == "openai":
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not configured. Please contact support.")
            
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
            # Check file size first
            file_size = os.path.getsize(local)
            max_size = 20 * 1024 * 1024  # 20MB limit for OpenAI Vision API
            
            if file_size > max_size:
                raise ValueError(f"Image file too large ({file_size/1024/1024:.1f}MB). Please use an image smaller than 20MB.")
            
            # Check minimum file size (corrupted files are often very small)
            if file_size < 100:  # Very small files are likely corrupted
                raise ValueError("Invalid image file. Please upload a valid PNG or JPG image.")
            
            # Validate image content using PIL
            try:
                from PIL import Image as PILImage
                with PILImage.open(local) as img:
                    # This will raise an exception if not a valid image
                    img.verify()
                    
                # Reopen to get format (verify() closes the image)
                with PILImage.open(local) as img:
                    pil_format = img.format.lower() if img.format else None
                    
                # Map PIL format to OpenAI format
                format_mapping = {
                    'jpeg': 'jpeg',
                    'jpg': 'jpeg', 
                    'png': 'png',
                    'webp': 'webp'
                }
                
                if pil_format not in format_mapping:
                    raise ValueError(f"Unsupported image format: {pil_format}. Please use PNG, JPG, or WebP.")
                
                image_format = format_mapping[pil_format]
                
            except ValueError:
                # Re-raise ValueError as-is (these are our custom validation errors)
                raise
            except Exception as e:
                logger.error(f"Image validation failed: {str(e)}")
                raise ValueError("Invalid or corrupted image file. Please upload a valid PNG or JPG image.")
            
            # Convert image to base64
            with open(local, "rb") as f:
                image_bytes = f.read()
                image_data = base64.b64encode(image_bytes).decode()
            
            # Validate base64 data size (OpenAI has limits)
            if len(image_data) > 25_000_000:  # ~25MB base64 limit
                raise ValueError("Image too large for processing. Please use a smaller image or reduce image quality.")
            
            logger.info(f"Processing OCR for image: size={file_size} bytes, format={image_format}, base64_length={len(image_data)}")
            
            # Use OpenAI Vision API
            payload = {
                "model": "gpt-4o",
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
            
            # Optimized retry logic for OCR with faster backoff
            import random
            max_retries = 3  # Reduced retries for faster processing
            
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=60) as client:  # Reduced timeout
                        r = await client.post(
                            "https://api.openai.com/v1/chat/completions",
                            json=payload,
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        
                        if r.status_code == 200:
                            data = r.json()
                            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            logger.info(f"OCR completed successfully, extracted {len(text)} characters")
                            return {"text": text, "summary":"", "actions":[]}
                        else:
                            error_detail = ""
                            try:
                                error_data = r.json()
                                error_detail = error_data.get("error", {}).get("message", "Unknown error")
                            except:
                                error_detail = r.text
                            
                            logger.error(f"OpenAI OCR API error {r.status_code}: {error_detail}")
                            
                            if r.status_code == 400:
                                raise ValueError("Image format not supported or image too large. Please try a smaller PNG or JPG image.")
                            elif r.status_code == 429:
                                # Get retry-after header if available
                                retry_after = r.headers.get('retry-after')
                                if retry_after:
                                    wait_time = min(int(retry_after), 30)  # Cap at 30 seconds
                                    logger.warning(f"🚦 OpenAI OCR rate limit (retry-after: {wait_time}s) (attempt {attempt + 1}/{max_retries})")
                                else:
                                    # Faster exponential backoff for OCR - OCR is typically quicker than transcription
                                    base_wait = (2 ** attempt) * 5  # 5s, 10s, 20s (much faster than transcription)
                                    jitter = random.uniform(0.1, 0.2) * base_wait  # Less jitter
                                    wait_time = min(base_wait + jitter, 30)  # Cap at 30 seconds
                                    logger.warning(f"🚦 OpenAI OCR rate limit (fast backoff: {wait_time:.1f}s) (attempt {attempt + 1}/{max_retries})")
                                
                                if attempt < max_retries - 1:
                                    # Always notify user about OCR delays since they're shorter
                                    logger.info(f"⏳ OCR processing delayed due to rate limits, retrying in {wait_time:.0f} seconds")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    logger.error(f"❌ OpenAI OCR rate limit exceeded after {max_retries} attempts")
                                    raise ValueError("OCR service is currently busy. Please try again in a moment.")
                            elif r.status_code == 500:
                                # Server error - retry with shorter backoff
                                wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s (faster than before)
                                logger.warning(f"🔧 OpenAI OCR server error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise ValueError("OCR service temporarily unavailable due to server issues. Please try again later.")
                            else:
                                raise ValueError(f"OCR processing temporarily unavailable (Error {r.status_code}). Please try again.")
                                
                except httpx.TimeoutException:
                    logger.error(f"OCR request timed out (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s (very fast for timeouts)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ValueError("OCR processing timed out. Please try with a smaller or clearer image.")
                except ValueError:
                    # Re-raise ValueError as-is (these are our custom validation errors)
                    raise
                except Exception as e:
                    logger.error(f"OCR request failed (attempt {attempt + 1}): {str(e)}")
                    if attempt == max_retries - 1:
                        raise ValueError("OCR processing failed due to network error. Please try again.")
                    await asyncio.sleep(2 ** attempt)  # Simple backoff for other errors
        
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