import os, time, json, datetime, subprocess, pathlib
import asyncio
from dotenv import load_dotenv
from pathlib import Path
from store import NotesStore, db
from storage import create_presigned_get_url
from enhanced_providers import transcribe_audio as stt_transcribe
from providers import ocr_read

import httpx
import logging

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# Minimal SendGrid via HTTP API (no SDK)
async def send_email(to_list, subject, html):
    key = os.getenv("SENDGRID_API_KEY")
    if not key:
        logger.error("SendGrid API key missing")
        raise ValueError("SendGrid API key not configured")
    
    if not to_list:
        logger.warning("No recipients provided for email")
        return
    
    payload = {
        "personalizations": [{"to": [{"email": x} for x in to_list]}],
        "from": {"email": "no-reply@autome.local"},
        "subject": subject,
        "content": [{"type":"text/html","value": html}],
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {key}"},
                json=payload
            )
            r.raise_for_status()
            logger.info(f"Email sent successfully to {len(to_list)} recipients")
    except httpx.HTTPStatusError as e:
        logger.error(f"SendGrid API error: {e.response.status_code} - {e.response.text}")
        # Don't raise - background task failures should not affect main API responses
        return
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        # Don't raise - background task failures should not affect main API responses
        return

def _repo_url_with_pat(repo_url: str, pat: str) -> str:
    if not pat or not repo_url.startswith("https://"):
        return repo_url
    return repo_url.replace("https://","https://"+pat+"@")

def _write_note_files(base: pathlib.Path, note_id: str, title: str, artifacts: dict):
    now = datetime.datetime.utcnow()
    d = base / "notes" / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d") / note_id
    d.mkdir(parents=True, exist_ok=True)
    
    (d / "meta.json").write_text(json.dumps({
        "id": note_id,
        "title": title,
        "created_utc": now.isoformat() + "Z"
    }, ensure_ascii=False, indent=2))
    
    md = ["# " + title]
    if "summary" in artifacts and artifacts["summary"]:
        md += ["", "## Summary", artifacts["summary"]]
    if "transcript" in artifacts and artifacts["transcript"]:
        md += ["", "## Transcript", artifacts["transcript"]]
    if "text" in artifacts and artifacts["text"]:
        md += ["", "## OCR Text", artifacts["text"]]
    if "actions" in artifacts and artifacts["actions"]:
        md += ["", "## Action items"] + [f"- {a}" for a in artifacts["actions"]]
    
    (d / "note.md").write_text("\n".join(md))

async def enqueue_transcription(note_id: str):
    note = await NotesStore.get(note_id)
    if not note:
        logger.error(f"Note not found: {note_id}")
        return
        
    try:
        signed = create_presigned_get_url(note["media_key"])
        start = time.time()
        
        # Add timeout for transcription to prevent hanging
        # Calculate dynamic timeout based on file size and expected processing time
        try:
            # Get file size to estimate processing time
            signed = create_presigned_get_url(note["media_key"])
            
            # For large files, allow much more time
            import os
            try:
                if os.path.exists(signed):
                    file_size = os.path.getsize(signed)
                    # Allow 2 minutes per MB, minimum 10 minutes, maximum 30 minutes
                    timeout_seconds = min(max(600, (file_size // (1024*1024)) * 120), 1800)
                else:
                    timeout_seconds = 1200  # 20 minutes default
            except:
                timeout_seconds = 1200  # 20 minutes default
                
            logger.info(f"Using timeout of {timeout_seconds} seconds ({timeout_seconds//60} minutes) for transcription")
            
            result = await asyncio.wait_for(stt_transcribe(signed), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.error(f"Transcription timeout for note {note_id} after {timeout_seconds} seconds")
            await NotesStore.update_status(note_id, "failed")
            await NotesStore.set_artifacts(note_id, {"error": f"Transcription timed out after {timeout_seconds//60} minutes. This is an unusually long processing time - please try again or contact support if the issue persists."})
            return
            
        latency_ms = int((time.time() - start) * 1000)
        
        artifacts = {
            "transcript": result.get("text",""),
            "summary": result.get("summary",""),
            "actions": result.get("actions",[])
        }
        
        await NotesStore.set_artifacts(note_id, artifacts)
        await NotesStore.set_metrics(note_id, {"latency_ms": latency_ms})
        await NotesStore.update_status(note_id, "ready")
        logger.info(f"Transcription completed for note {note_id}")
        
    except Exception as e:
        logger.error(f"Transcription failed for note {note_id}: {str(e)}")
        await NotesStore.update_status(note_id, "failed")
        await NotesStore.set_artifacts(note_id, {"error": "Transcription failed"})

async def enqueue_ocr(note_id: str):
    note = await NotesStore.get(note_id)
    if not note:
        logger.error(f"Note not found: {note_id}")
        return
    
    # Ensure this is actually a photo note that should be processed for OCR
    if note.get("kind") != "photo":
        logger.error(f"OCR requested for non-photo note {note_id} with kind: {note.get('kind')}")
        await NotesStore.update_status(note_id, "failed")
        await NotesStore.set_artifacts(note_id, {"error": "OCR can only process photo notes. This appears to be a different note type."})
        return
    
    # Ensure note has a media_key
    if not note.get("media_key"):
        logger.error(f"OCR requested for note {note_id} without media_key")
        await NotesStore.update_status(note_id, "failed")
        await NotesStore.set_artifacts(note_id, {"error": "No image file found to process."})
        return
        
    try:
        signed = create_presigned_get_url(note["media_key"])
        
        # Validate that the file actually exists
        if not os.path.exists(signed):
            logger.error(f"Media file not found for note {note_id}: {signed}")
            await NotesStore.update_status(note_id, "failed")
            await NotesStore.set_artifacts(note_id, {"error": "Image file not found. Please try uploading again."})
            return
        
        start = time.time()
        
        # Add timeout for OCR to prevent hanging
        try:
            result = await asyncio.wait_for(ocr_read(signed), timeout=180)  # 3 minute timeout
            
            # If we get here, OCR was successful
            latency_ms = int((time.time() - start) * 1000)
            
            artifacts = {
                "text": result.get("text",""),
                "summary": result.get("summary",""),
                "actions": result.get("actions",[])
            }
            
            await NotesStore.set_artifacts(note_id, artifacts)
            await NotesStore.set_metrics(note_id, {"latency_ms": latency_ms})
            await NotesStore.update_status(note_id, "ready")
            
        except asyncio.TimeoutError:
            logger.error(f"OCR timeout for note {note_id}")
            await NotesStore.update_status(note_id, "failed")
            await NotesStore.set_artifacts(note_id, {"error": "OCR processing timed out after 3 minutes. Please try with a smaller or clearer image."})
            return
        except ValueError as ve:
            # These are our custom validation errors
            logger.error(f"OCR validation error for note {note_id}: {str(ve)}")
            await NotesStore.update_status(note_id, "failed")
            await NotesStore.set_artifacts(note_id, {"error": str(ve)})
            return
        except Exception as e:
            # Unexpected errors
            logger.error(f"OCR processing error for note {note_id}: {str(e)}")
            await NotesStore.update_status(note_id, "failed")
            await NotesStore.set_artifacts(note_id, {"error": "OCR processing failed due to an unexpected error. Please try again."})
            return
        await NotesStore.update_status(note_id, "ready")
        logger.info(f"OCR completed for note {note_id}")
        
    except Exception as e:
        logger.error(f"OCR failed for note {note_id}: {str(e)}")
        await NotesStore.update_status(note_id, "failed")
        await NotesStore.set_artifacts(note_id, {"error": "OCR processing failed"})

async def enqueue_email(note_id: str, to_list: list, subject: str):
    note = await NotesStore.get(note_id)
    if not note:
        logger.error(f"Note not found: {note_id}")
        return
    
    try:
        art = note["artifacts"]
        body = art.get("summary") or art.get("transcript") or art.get("text") or ""
        if not body:
            body = f"Note: {note['title']}\nNo content available yet."
        
        html = f"<h3>{note['title']}</h3><p>{body.replace(chr(10), '<br>')}</p>"
        await send_email(to_list, subject, html)
        logger.info(f"Email sent for note {note_id} to {len(to_list)} recipients")
        
    except Exception as e:
        logger.error(f"Email delivery failed for note {note_id}: {str(e)}")
        # Don't raise - background task failures should not affect main API responses
        return

async def notify_transcription_delay(note_id: str, user_email: str, delay_reason: str = "high_demand"):
    """Notify user about transcription delays due to rate limiting"""
    try:
        if not user_email:
            logger.info(f"No email provided for transcription delay notification: {note_id}")
            return
            
        # Get note details
        note = await NotesStore.get(note_id)
        if not note:
            logger.error(f"Note not found for delay notification: {note_id}")
            return
            
        note_title = note.get('title', 'Your Recording')
        
        delay_messages = {
            "rate_limit": "Due to high demand for our transcription service",
            "high_demand": "Due to high demand for our transcription service", 
            "api_limit": "Due to API service limitations"
        }
        
        delay_message = delay_messages.get(delay_reason, "Due to temporary service constraints")
        
        subject = f"⏳ Transcription Delayed - {note_title}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">⏳ Transcription In Progress</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333; margin-top: 0;">Your recording is being processed</h2>
                
                <div style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #667eea; margin-top: 0;">📝 Recording Details</h3>
                    <p><strong>Title:</strong> {note_title}</p>
                    <p><strong>Status:</strong> Processing (Delayed)</p>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffeaa7;">
                    <p style="margin: 0; color: #856404;">
                        <strong>📢 Notice:</strong> {delay_message}, your transcription is taking longer than usual. 
                        We're working to process it as quickly as possible.
                    </p>
                </div>
                
                <div style="margin: 30px 0; text-align: center;">
                    <p style="color: #666;">We'll notify you as soon as your transcription is ready!</p>
                    <p style="color: #666; font-size: 14px;">Expected processing time: 5-15 minutes</p>
                </div>
                
                <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #0066cc; font-size: 14px;">
                        💡 <strong>Tip:</strong> Large files may take longer to process. Your content will be preserved and ready when processing completes.
                    </p>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p style="margin: 0;">AUTO-ME PWA | Intelligent Content Processing</p>
            </div>
        </div>
        """
        
        await send_email([user_email], subject, html_content)
        logger.info(f"📧 Transcription delay notification sent to {user_email} for note {note_id}")
        
    except Exception as e:
        logger.error(f"Failed to send transcription delay notification: {str(e)}")
        # Don't raise - notifications shouldn't break the main process
        return

async def notify_ocr_delay(note_id: str, user_email: str, delay_reason: str = "high_demand"):
    """Notify user about OCR delays due to rate limiting"""
    try:
        if not user_email:
            logger.info(f"No email provided for OCR delay notification: {note_id}")
            return
            
        # Get note details
        note = await NotesStore.get(note_id)
        if not note:
            logger.error(f"Note not found for delay notification: {note_id}")
            return
            
        note_title = note.get('title', 'Your Document')
        
        delay_messages = {
            "rate_limit": "Due to high demand for our OCR service",
            "high_demand": "Due to high demand for our OCR service", 
            "api_limit": "Due to API service limitations"
        }
        
        delay_message = delay_messages.get(delay_reason, "Due to temporary service constraints")
        
        subject = f"⏳ OCR Processing Delayed - {note_title}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">⏳ OCR In Progress</h1>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <h2 style="color: #333; margin-top: 0;">Your document is being processed</h2>
                
                <div style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #FF6B6B; margin-top: 0;">📄 Document Details</h3>
                    <p><strong>Title:</strong> {note_title}</p>
                    <p><strong>Status:</strong> Processing (Delayed)</p>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffeaa7;">
                    <p style="margin: 0; color: #856404;">
                        <strong>📢 Notice:</strong> {delay_message}, your OCR processing is taking longer than usual. 
                        We're working to extract the text as quickly as possible.
                    </p>
                </div>
                
                <div style="margin: 30px 0; text-align: center;">
                    <p style="color: #666;">We'll notify you as soon as your text extraction is ready!</p>
                    <p style="color: #666; font-size: 14px;">Expected processing time: 1-5 minutes</p>
                </div>
                
                <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #0066cc; font-size: 14px;">
                        💡 <strong>Tip:</strong> Complex or large images may take longer to process. Your content will be preserved and ready when processing completes.
                    </p>
                </div>
            </div>
            
            <div style="background: #333; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p style="margin: 0;">AUTO-ME PWA | Intelligent Content Processing</p>
            </div>
        </div>
        """
        
        await send_email([user_email], subject, html_content)
        logger.info(f"📧 OCR delay notification sent to {user_email} for note {note_id}")
        
    except Exception as e:
        logger.error(f"Failed to send OCR delay notification: {str(e)}")
        # Don't raise - notifications shouldn't break the main process
        return


async def enqueue_iisb_processing(client_name: str, issues_text: str, user_id: str):
    """Process IISB analysis for client issues (Expeditors only)"""
    try:
        from .iisb_processor import iisb_processor
        
        start = time.time()
        result = await iisb_processor.process_iisb_input(client_name, issues_text)
        latency_ms = int((time.time() - start) * 1000)
        
        if result.get("success"):
            # Store IISB analysis results (could be stored in a separate collection)
            iisb_data = {
                "client_name": client_name,
                "user_id": user_id,
                "analysis_results": result,
                "created_at": datetime.datetime.utcnow(),
                "processing_time_ms": latency_ms,
                "type": "iisb_analysis"
            }
            
            # Store in database (using notes collection for now, could be separate)
            await db()["iisb_analyses"].insert_one(iisb_data)
            
            logger.info(f"IISB analysis completed for client: {client_name}")
            return result
        else:
            logger.error(f"IISB analysis failed for client: {client_name}")
            return result
            
    except Exception as e:
        logger.error(f"Error in IISB processing: {str(e)}")
        return {"error": "IISB processing failed", "success": False}

async def enqueue_git_sync(note_id: str):
    note = await NotesStore.get(note_id)
    if not note:
        logger.error(f"Note not found: {note_id}")
        return
        
    repo = os.getenv("GIT_REPO_URL")
    if not repo:
        logger.warning("Git sync skipped - no GIT_REPO_URL configured")
        return
    
    # Workdir
    work = pathlib.Path(os.getenv("GIT_WORKDIR", "/tmp/autome_repo"))
    work.mkdir(parents=True, exist_ok=True)
    
    if not (work / ".git").exists():
        ru = _repo_url_with_pat(repo, os.getenv("GIT_PAT", ""))
        subprocess.run(["git","clone","--depth","1",ru,str(work)], check=True)
    else:
        subprocess.run(["git","-C",str(work),"pull","--rebase","--autostash"], check=True)
    
    _write_note_files(work, note_id, note["title"], note["artifacts"])
    subprocess.run(["git","-C",str(work),"add","-A"], check=True)
    msg = f"feat(note): {note['title']} [{note_id}]"
    subprocess.run(["git","-C",str(work),"commit","-m",msg], check=False)
    subprocess.run(["git","-C",str(work),"push"], check=True)

async def enqueue_pipeline_job(job_id: str):
    """Enqueue a transcription job for pipeline processing"""
    try:
        from enhanced_store import TranscriptionJobStore
        
        # Verify job exists and is in correct state
        job = await TranscriptionJobStore.get_job(job_id)
        if not job:
            logger.error(f"Pipeline job not found: {job_id}")
            return
        
        # Import pipeline_worker to trigger processing
        from pipeline_worker import process_single_job
        
        logger.info(f"🚀 Enqueuing pipeline job {job_id} for processing")
        
        # Process the job asynchronously
        await process_single_job(job_id)
        
    except Exception as e:
        logger.error(f"Failed to enqueue pipeline job {job_id}: {str(e)}")
        # Don't raise - background task failures should not affect main API responses