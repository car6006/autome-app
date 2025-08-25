import os, time, json, datetime, subprocess, pathlib
import asyncio
from store import NotesStore, db
from storage import create_presigned_get_url
from providers import stt_transcribe, ocr_read
from network_processor import network_processor
import httpx
import logging

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
        raise
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        raise

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
        result = await stt_transcribe(signed)
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
        await NotesStore.set_artifacts(note_id, {"error": str(e)})

async def enqueue_ocr(note_id: str):
    note = await NotesStore.get(note_id)
    if not note:
        logger.error(f"Note not found: {note_id}")
        return
        
    try:
        signed = create_presigned_get_url(note["media_key"])
        start = time.time()
        result = await ocr_read(signed)
        latency_ms = int((time.time() - start) * 1000)
        
        artifacts = {
            "text": result.get("text",""),
            "summary": result.get("summary",""),
            "actions": result.get("actions",[])
        }
        
        await NotesStore.set_artifacts(note_id, artifacts)
        await NotesStore.set_metrics(note_id, {"latency_ms": latency_ms})
        await NotesStore.update_status(note_id, "ready")
        logger.info(f"OCR completed for note {note_id}")
        
    except Exception as e:
        logger.error(f"OCR failed for note {note_id}: {str(e)}")
        await NotesStore.update_status(note_id, "failed")
        await NotesStore.set_artifacts(note_id, {"error": str(e)})

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
        raise

async def enqueue_network_diagram_processing(note_id: str):
    """Process network diagram from voice or sketch (Expeditors only)"""
    note = await NotesStore.get(note_id)
    if not note:
        logger.error(f"Note not found: {note_id}")
        return
        
    signed = create_presigned_get_url(note["media_key"])
    start = time.time()
    
    # Determine input type based on file extension or content
    file_key = note.get("media_key", "")
    input_type = "audio" if any(ext in file_key.lower() for ext in ['.mp3', '.wav', '.m4a', '.webm']) else "image"
    
    # Process with specialized network diagram processor
    result = await network_processor.process_network_input(signed, input_type)
    
    latency_ms = int((time.time() - start) * 1000)
    
    if result.get("success"):
        artifacts = {
            "network_topology": result.get("network_topology", {}),
            "diagram_data": result.get("diagram_data", {}),
            "insights": result.get("insights", {}),
            "raw_input": result.get("raw_input", ""),
            "entities": result.get("entities", {}),
            "processing_type": "expeditors_network_diagram"
        }
        
        await NotesStore.set_artifacts(note_id, artifacts)
        await NotesStore.set_metrics(note_id, {"latency_ms": latency_ms})
        await NotesStore.update_status(note_id, "ready")
    else:
        # Handle processing failure
        error_artifacts = {
            "error": result.get("error", "Unknown processing error"),
            "processing_type": "expeditors_network_diagram",
            "status": "failed"
        }
        await NotesStore.set_artifacts(note_id, error_artifacts)
        await NotesStore.update_status(note_id, "failed")

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
        return {"error": str(e), "success": False}

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