from __future__ import annotations
import base64, os, tempfile, httpx, asyncio
import logging

logger = logging.getLogger(__name__)

OPENAI_STT = "openai"
AZURE_OCR = "azure"
GCV_OCR = "gcv"

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

async def stt_transcribe(file_url: str) -> dict:
    provider = (os.getenv("STT_PROVIDER") or OPENAI_STT).lower()
    if provider == OPENAI_STT:
        key = os.getenv("WHISPER_API_KEY")
        if not key:
            return {"text":"", "summary":"", "actions":[], "note":"missing WHISPER_API_KEY"}
        
        local = await _download(file_url)
        form = {"model": "whisper-1", "response_format": "json"}
        
        try:
            with open(local, "rb") as audio_file:
                files = {"file": audio_file}
                
                async with httpx.AsyncClient(timeout=300) as client:
                    r = await client.post(
                        f'{os.getenv("WHISPER_API_BASE","https://api.openai.com/v1")}/audio/transcriptions',
                        data=form,
                        files=files,
                        headers={"Authorization": f"Bearer {key}"}
                    )
                    r.raise_for_status()
                    data = r.json()
                    text = data.get("text","")
                    return {"text": text, "summary": "", "actions": []}
        finally:
            # Clean up temporary file
            try:
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
            
            # Convert image to base64
            with open(local, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
                
            # Determine image format
            image_format = "jpeg"
            if local.lower().endswith('.png'):
                image_format = "png"
            elif local.lower().endswith('.webp'):
                image_format = "webp"
            
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