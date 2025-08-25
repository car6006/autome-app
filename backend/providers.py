from __future__ import annotations
import base64, os, tempfile, httpx, asyncio
import logging

logger = logging.getLogger(__name__)

OPENAI_STT = "openai"
AZURE_OCR = "azure"
GCV_OCR = "gcv"

async def _download(url: str) -> str:
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

async def ocr_read(file_url: str) -> dict:
    which = (os.getenv("OCR_PROVIDER") or GCV_OCR).lower()
    local = await _download(file_url)
    
    if which == GCV_OCR:
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