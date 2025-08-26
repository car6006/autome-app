from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query, Depends, status
from fastapi.responses import JSONResponse, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import httpx
from datetime import datetime, timedelta, timezone

from store import NotesStore
from storage import store_file
from tasks import enqueue_transcription, enqueue_ocr, enqueue_email, enqueue_git_sync, enqueue_network_diagram_processing, enqueue_iisb_processing
from auth import (
    AuthService, User, UserCreate, UserLogin, UserResponse, UserProfileUpdate, 
    Token, get_current_user, get_current_user_optional
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# API Key validation on startup
def validate_api_keys():
    """Validate critical API keys on startup"""
    whisper_key = os.environ.get('WHISPER_API_KEY')
    gcv_key = os.environ.get('GCV_API_KEY')
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    
    warnings = []
    if not whisper_key or whisper_key == 'your_openai_api_key_here':
        warnings.append("⚠️  WHISPER_API_KEY is missing or invalid - audio transcription will fail")
    if not gcv_key or gcv_key == 'your_google_vision_api_key_here':
        warnings.append("⚠️  GCV_API_KEY is missing or invalid - OCR processing will fail")
    if not sendgrid_key or sendgrid_key == 'your_sendgrid_api_key_here':
        warnings.append("⚠️  SENDGRID_API_KEY is missing or invalid - email delivery will fail")
    
    if warnings:
        print("\n" + "="*80)
        print("🚨 API KEY VALIDATION WARNINGS:")
        for warning in warnings:
            print(warning)
        print("="*80 + "\n")
    else:
        print("✅ All API keys appear to be configured")

# Validate keys on startup
validate_api_keys()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AUTO-ME Productivity API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class NoteCreate(BaseModel):
    title: str
    kind: str  # "audio" or "photo"

class EmailRequest(BaseModel):
    to: List[str]
    subject: str

class NoteResponse(BaseModel):
    id: str
    title: str
    kind: str
    status: str
    artifacts: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    created_at: datetime
    ready_at: Optional[datetime] = None
    user_id: Optional[str] = None

# Authentication endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    user_id = await AuthService.create_user(user_data)
    user = await AuthService.get_user_by_id(user_id)
    
    # Create access token
    access_token = AuthService.create_access_token(data={"sub": user_id})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user"""
    user = await AuthService.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = AuthService.create_access_token(data={"sub": user["id"]})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)

@api_router.put("/auth/me", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    success = await AuthService.update_user_profile(current_user["id"], profile_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )
    
    # Get updated user
    updated_user = await AuthService.get_user_by_id(current_user["id"])
    return UserResponse(**updated_user)

# Core endpoints (updated to work with authentication)
@api_router.get("/")
async def root():
    return {"message": "AUTO-ME Productivity API v2.0", "status": "running"}

@api_router.post("/notes", response_model=Dict[str, str])
async def create_note(
    note: NoteCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Create a new note (authenticated or anonymous)"""
    user_id = current_user["id"] if current_user else None
    note_id = await NotesStore.create(note.title, note.kind, user_id)
    return {"id": note_id, "status": "created"}

# Hidden Expeditors Network Diagram Feature
@api_router.post("/notes/network-diagram", response_model=Dict[str, str])
async def create_network_diagram_note(
    note: NoteCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create network diagram note (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    # Override note kind to network_diagram
    note_dict = note.dict()
    note_dict["kind"] = "network_diagram"
    
    user_id = current_user["id"]
    note_id = await NotesStore.create(note_dict["title"], "network_diagram", user_id)
    return {"id": note_id, "status": "created", "feature": "network_diagram"}

@api_router.post("/notes/{note_id}/process-network")
async def process_network_diagram(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """Process network diagram from voice or sketch (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    note = await NotesStore.get(note_id)
    if not note or note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if note.get("kind") != "network_diagram":
        raise HTTPException(status_code=400, detail="Invalid note type for network processing")
    
    # Store the file
    file_content = await file.read()
    media_key = store_file(file_content, file.filename)
    
    # Update note with media key
    await NotesStore.update_media_key(note_id, media_key)
    
    # Queue specialized network processing
# Hidden IISB Analysis Feature (Expeditors only)
@api_router.post("/iisb/analyze", response_model=Dict[str, Any])
async def analyze_client_issues(
    request: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """Analyze client supply chain issues using IISB framework (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    client_name = request.get("client_name", "")
    issues_text = request.get("issues_text", "")
    
    if not client_name or not issues_text:
        raise HTTPException(
            status_code=400,
            detail="Client name and issues text are required"
        )
    
    # Process IISB analysis
    from iisb_processor import iisb_processor
    result = await iisb_processor.process_iisb_input(client_name, issues_text)
    
    return result

@api_router.post("/notes/{note_id}/continue-to-iisb")
async def continue_to_iisb_analysis(
    note_id: str,
    request: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """Continue from Network Diagram to IISB analysis (HIDDEN - Expeditors only)"""
    # Check if user has @expeditors.com email
    if not current_user["email"].endswith("@expeditors.com"):
        raise HTTPException(
            status_code=404, 
            detail="Feature not found"
        )
    
    # Verify note exists and belongs to user
    note = await NotesStore.get(note_id)
    if not note or note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Extract client name from network diagram artifacts if available
    client_name = request.get("client_name", "")
    if not client_name and note.get("artifacts"):
        # Try to extract client name from note title or artifacts
        client_name = note.get("title", "").split("-")[0].strip() or "Client"
    
    return {
        "note_id": note_id,
        "client_name": client_name,
        "network_completed": note.get("status") == "ready",
        "ready_for_iisb": True,
        "message": "Ready to proceed with IISB analysis"
    }

@api_router.post("/notes/{note_id}/upload")
async def upload_media(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    file: UploadFile = File(...)
):
    """Upload media file for a note"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    # Store the file
    file_content = await file.read()
    media_key = store_file(file_content, file.filename)
    
    # Update note with media key
    await NotesStore.update_media_key(note_id, media_key)
    
    # Queue processing based on note kind
    if note["kind"] == "audio":
        background_tasks.add_task(enqueue_transcription, note_id)
    elif note["kind"] == "photo":
        background_tasks.add_task(enqueue_ocr, note_id)
    elif note["kind"] == "network_diagram":
        background_tasks.add_task(enqueue_network_diagram_processing, note_id)
    
    return {"message": "File uploaded successfully", "status": "processing"}

@api_router.post("/upload-file")
async def upload_file_for_scan(
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    file: UploadFile = File(...),
    title: str = Form("Uploaded Document")
):
    """Upload file directly for processing (scan or audio)"""
    
    # Validate file type
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.pdf'}
    audio_extensions = {'.mp3', '.wav', '.m4a', '.webm', '.ogg', '.mpeg'}
    allowed_extensions = image_extensions | audio_extensions
    
    file_ext = os.path.splitext(file.filename or '')[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: Images ({', '.join(image_extensions)}), Audio ({', '.join(audio_extensions)})"
        )
    
    # Determine note kind based on file type
    if file_ext in audio_extensions or file.content_type.startswith('audio/'):
        note_kind = "audio"
    else:
        note_kind = "photo"
    
    # Create note for the upload
    user_id = current_user["id"] if current_user else None
    note_id = await NotesStore.create(title, note_kind, user_id)
    
    # Store the file
    file_content = await file.read()
    media_key = store_file(file_content, file.filename)
    
    # Update note with media key
    await NotesStore.update_media_key(note_id, media_key)
    
    # Queue appropriate processing
    if note_kind == "audio":
        background_tasks.add_task(enqueue_transcription, note_id)
    else:
        background_tasks.add_task(enqueue_ocr, note_id)
    
    return {
        "id": note_id,
        "message": f"{'Audio' if note_kind == 'audio' else 'File'} uploaded successfully",
        "status": "processing",
        "filename": file.filename,
        "kind": note_kind
    }

@api_router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get a specific note"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    return NoteResponse(**note)

@api_router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    limit: int = Query(50, le=100),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """List notes (user's notes if authenticated, public notes if not)"""
    user_id = current_user["id"] if current_user else None
    notes = await NotesStore.list_recent(limit, user_id)
    return [NoteResponse(**note) for note in notes]

@api_router.post("/notes/{note_id}/email")
async def send_note_email(
    note_id: str,
    email_req: EmailRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Send note content via email"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    background_tasks.add_task(enqueue_email, note_id, email_req.to, email_req.subject)
    return {"message": "Email queued for delivery"}

@api_router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Delete a specific note"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this note")
    
    # Delete from database
    await db["notes"].delete_one({"id": note_id})
    
    return {"message": "Note deleted successfully"}

@api_router.post("/notes/{note_id}/ai-chat")
async def ai_chat_with_note(
    note_id: str,
    request: dict,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """AI conversational agent for note content analysis"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    content = artifacts.get("transcript") or artifacts.get("text", "")
    
    if not content:
        raise HTTPException(status_code=400, detail="No content available for analysis")
    
    user_question = request.get("question", "").strip()
    if not user_question:
        raise HTTPException(status_code=400, detail="Please provide a question")
    
    try:
        # Use OpenAI to answer user's question about the content
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Check if user is from Expeditors for context
        is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
        
        # Enhanced context for Expeditors users
        context_prefix = ""
        if is_expeditors_user:
            context_prefix = "You are an AI business analyst working with Expeditors International, a global logistics and freight forwarding company. "
        
        prompt = f"""
        {context_prefix}You are an intelligent assistant analyzing business content. Based on the following content, answer the user's question with detailed, actionable insights.

        Content to analyze:
        {content}

        User's Question: {user_question}

        Instructions:
        - Provide a comprehensive, professional response
        - Include specific details from the content when relevant
        - If the user asks about market intelligence, trade barriers, risks, or business insights, provide thorough analysis
        - Use bullet points for lists and clear structure
        - If asking about summaries, provide executive-level summaries
        - For trade/logistics questions, consider global business implications
        - Be specific and actionable in your recommendations
        - Use professional business language
        """
        
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1200,
                    "temperature": 0.3
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            ai_analysis = response.json()
            ai_response = ai_analysis["choices"][0]["message"]["content"]
            
            # Store the conversation in artifacts for reference
            conversations = artifacts.get("ai_conversations", [])
            conversations.append({
                "question": user_question,
                "response": ai_response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            updated_artifacts = {**artifacts, "ai_conversations": conversations}
            await NotesStore.set_artifacts(note_id, updated_artifacts)
            
            return {
                "response": ai_response,
                "question": user_question,
                "note_title": note["title"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_expeditors": is_expeditors_user
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process AI chat: {str(e)}")

@api_router.get("/notes/{note_id}/ai-conversations/export")
async def export_ai_conversations(
    note_id: str,
    format: str = Query("pdf", regex="^(pdf|docx|txt)$"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Export AI conversation responses to RTF format"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    conversations = artifacts.get("ai_conversations", [])
    
    if not conversations:
        raise HTTPException(status_code=400, detail="No AI conversations found for this note")
    
    # Check if user is from Expeditors for branding
    is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
    
    if format == "rtf":
        # Generate professional RTF content with proper formatting
        rtf_content = r"{\rtf1\ansi\deff0"
        
        # Add fonts for professional appearance
        rtf_content += r"{\fonttbl{\f0 Times New Roman;}{\f1 Arial;}{\f2 Calibri;}}"
        
        # Add colors for Expeditors branding
        rtf_content += r"{\colortbl;\red0\green0\blue0;\red234\green10\blue42;\red35\green31\blue32;\red102\green102\blue102;\red255\green255\blue255;}"
        
        # Header with Expeditors branding and logo placeholder
        if is_expeditors_user:
            rtf_content += r"\pard\qc\f1\fs32\b\cf2 EXPEDITORS INTERNATIONAL\par"
            rtf_content += r"\f2\fs18\b0\cf3 Global Logistics & Freight Forwarding\par"
            rtf_content += r"\pard\qc\f0\fs14\cf4 " + "─" * 60 + r"\par\par"
            rtf_content += r"\pard\qc\f1\fs24\b\cf1 AI CONTENT ANALYSIS REPORT\par"
            rtf_content += r"\f0\fs12\cf4 Generated: " + datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC") + r"\par"
            rtf_content += r"\f0\fs12\cf4 Document: " + note["title"] + r"\par"
            rtf_content += r"\pard\qc\f0\fs14\cf4 " + "─" * 60 + r"\par\par"
        else:
            rtf_content += r"\pard\qc\f1\fs28\b\cf1 AI CONTENT ANALYSIS REPORT\par"
            rtf_content += r"\f0\fs12\b0\cf4 Generated: " + datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC") + r"\par"
            rtf_content += r"\f0\fs12\cf4 Document: " + note["title"] + r"\par"
            rtf_content += r"\pard\qc\f0\fs14\cf4 " + "─" * 50 + r"\par\par"
        
        # Professional content formatting
        rtf_content += r"\pard\ql\f0\fs22\b\cf1 EXECUTIVE SUMMARY\par"
        rtf_content += r"\pard\ql\f0\fs14\cf4 " + "─" * 20 + r"\par"
        
        # Add AI responses with professional formatting
        for i, conv in enumerate(conversations, 1):
            response = conv.get("response", "")
            timestamp = conv.get("timestamp", "")
            
            # Parse timestamp
            time_str = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M")
                except:
                    time_str = timestamp[:10]
            
            # Section header
            rtf_content += r"\par\pard\ql\f1\fs18\b\cf2 ANALYSIS SECTION " + str(i)
            if time_str:
                rtf_content += r" \f0\fs12\cf4 (Generated at " + time_str + r")"
            rtf_content += r"\par"
            rtf_content += r"\pard\ql\f0\fs14\cf4 " + "─" * 40 + r"\par\par"
            
            # Clean and professionally format the response
            clean_response = response.replace('\\', '\\\\').replace('{', r'\{').replace('}', r'\}')
            
            # Process the content for better formatting
            lines = clean_response.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    formatted_lines.append(r'\par')
                    continue
                
                # Format headers (lines starting with ###, ##, #)
                if line.startswith('###'):
                    header_text = line.replace('###', '').strip()
                    formatted_lines.append(r'\par\pard\ql\f1\fs16\b\cf1 ' + header_text + r'\par')
                elif line.startswith('##'):
                    header_text = line.replace('##', '').strip()
                    formatted_lines.append(r'\par\pard\ql\f1\fs18\b\cf2 ' + header_text + r'\par')
                elif line.startswith('#'):
                    header_text = line.replace('#', '').strip()
                    formatted_lines.append(r'\par\pard\ql\f1\fs20\b\cf1 ' + header_text + r'\par')
                
                # Format numbered lists
                elif line.startswith(('.', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    # Extract number and content
                    if line.startswith('.'):
                        list_content = line[1:].strip().lstrip('*').strip()
                        formatted_lines.append(r'\par\pard\li360\f2\fs12\b\cf1 \bullet\tab ' + list_content + r'\par')
                    else:
                        parts = line.split('.', 1)
                        if len(parts) == 2:
                            num = parts[0].strip()
                            content = parts[1].strip().lstrip('*').strip()
                            formatted_lines.append(r'\par\pard\li200\f2\fs12\b\cf2 ' + num + r'.\tab\f0\fs12\b0\cf1 ' + content + r'\par')
                
                # Format bullet points
                elif line.startswith(('•', '-', '*')):
                    bullet_content = line[1:].strip()
                    # Check if it's a sub-bullet (starts with description)
                    if ':' in bullet_content and bullet_content.index(':') < 50:
                        parts = bullet_content.split(':', 1)
                        title = parts[0].strip()
                        desc = parts[1].strip()
                        formatted_lines.append(r'\par\pard\li480\f2\fs11\b\cf2 \bullet\tab ' + title + r':\f0\fs11\b0\cf1 ' + desc + r'\par')
                    else:
                        formatted_lines.append(r'\par\pard\li360\f2\fs11\cf1 \bullet\tab ' + bullet_content + r'\par')
                
                # Format bold text (between **)
                elif '**' in line:
                    # Simple bold formatting
                    parts = line.split('**')
                    formatted_line = r'\pard\ql\f0\fs12\cf1 '
                    for j, part in enumerate(parts):
                        if j % 2 == 1:  # Odd indices are between **
                            formatted_line += r'\b ' + part + r'\b0 '
                        else:
                            formatted_line += part
                    formatted_lines.append(formatted_line + r'\par')
                
                # Regular paragraphs
                else:
                    formatted_lines.append(r'\pard\ql\f0\fs12\cf1 ' + line + r'\par')
            
            # Join all formatted lines
            rtf_content += ''.join(formatted_lines)
            
            # Add spacing between sections
            rtf_content += r'\par\par'
        
        # Professional footer
        rtf_content += r"\pard\qc\f0\fs14\cf4 " + "─" * 60 + r"\par"
        if is_expeditors_user:
            rtf_content += r"\pard\qc\f0\fs10\cf4 This document contains confidential and proprietary information.\par"
            rtf_content += r"\f0\fs10\cf2 EXPEDITORS INTERNATIONAL - " + datetime.now(timezone.utc).strftime("%Y") + r"\par"
        else:
            rtf_content += r"\pard\qc\f0\fs10\cf4 AI-Generated Content Analysis Report\par"
        
        rtf_content += r"}"
        
        # Create descriptive filename based on content
        filename_base = note['title'][:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        if is_expeditors_user:
            filename = f"Expeditors_AI_Analysis_{filename_base}.rtf"
        else:
            filename = f"AI_Analysis_{filename_base}.rtf"
        
        return Response(
            content=rtf_content,
            media_type="application/rtf",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    
    else:  # txt format - clean version
        content = ""
        
        # Simple, clean header
        if is_expeditors_user:
            content += "EXPEDITORS INTERNATIONAL\n"
            content += "AI Content Analysis\n\n"
        else:
            content += "AI Content Analysis\n\n"
        
        content += f"Document: {note['title']}\n"
        content += f"Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}\n\n"
        
        # Process AI responses cleanly like CoPilot
        all_responses = []
        for conv in conversations:
            response = conv.get("response", "")
            all_responses.append(response)
        
        combined_text = " ".join(all_responses)
        
        # Clean up markdown
        import re
        combined_text = re.sub(r'#{1,6}\s*', '', combined_text)
        combined_text = re.sub(r'\*\*(.*?)\*\*', r'\1', combined_text)
        combined_text = re.sub(r'\*(.*?)\*', r'\1', combined_text)
        
        # Process into clean format
        lines = combined_text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith(('•', '-', '*')):
                    content += f"• {line[1:].strip()}\n"
                elif re.match(r'^\d+\.', line):
                    content += f"{line}\n"
                else:
                    content += f"{line}\n"
        
        # Create descriptive filename
        filename_base = note['title'][:30].replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"Expeditors_AI_Analysis_{filename_base}.txt" if is_expeditors_user else f"AI_Analysis_{filename_base}.txt"
        
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )

@api_router.post("/notes/{note_id}/generate-report")
async def generate_professional_report(
    note_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Generate a professional report with insights and action items"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    content = artifacts.get("transcript") or artifacts.get("text", "")
    
    if not content:
        raise HTTPException(status_code=400, detail="No content available to generate report")
    
    try:
        # Use OpenAI to generate professional insights
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Check if user is from Expeditors
        is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
        
        # Add logo header for Expeditors users
        logo_header = ""
        if is_expeditors_user:
            logo_header = """
==================================================
           EXPEDITORS INTERNATIONAL
           Professional Business Report
==================================================

"""
        
        prompt = f"""
        You are a senior executive assistant creating a professional business report{" for Expeditors International" if is_expeditors_user else ""}. Based on the following content, create a clean, well-formatted business analysis.

        Content to analyze:
        {content}

        Create a comprehensive professional report with these sections. Use clean formatting with clear headings and bullet points - NO MARKDOWN SYMBOLS like ### or **. Format as clean text with proper structure:

        EXECUTIVE SUMMARY
        Write 2-3 sentences highlighting the main points and overall situation

        KEY INSIGHTS  
        List 4-6 important findings as bullet points starting with •

        STRATEGIC RECOMMENDATIONS
        List 3-5 high-impact recommendations as bullet points starting with •

        ACTION ITEMS
        List specific, actionable next steps as bullet points starting with •
        - Include timeframes where appropriate (immediate, 1-3 months, etc.)
        - Be specific about who should be responsible

        PRIORITIES
        Categorize the action items:
        HIGH PRIORITY (next 2 weeks):
        • [list items]
        
        MEDIUM PRIORITY (next 1-3 months):
        • [list items]

        FOLLOW-UP & MONITORING
        List key metrics to track and review schedule as bullet points starting with •

        Use professional business language. Make it executive-ready. Use clear section headings in CAPS, bullet points with •, and write in complete sentences. Do NOT use markdown formatting symbols.
        """
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            ai_analysis = response.json()
            report_content = ai_analysis["choices"][0]["message"]["content"]
            
            # Add logo header for Expeditors users
            if is_expeditors_user:
                report_content = logo_header + report_content
            
            # Store the report in artifacts
            updated_artifacts = {**artifacts, "professional_report": report_content}
            await NotesStore.set_artifacts(note_id, updated_artifacts)
            
            return {
                "report": report_content,
                "note_title": note["title"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "note_id": note_id,
                "is_expeditors": is_expeditors_user
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@api_router.post("/notes/batch-report")
async def generate_batch_report(
    note_ids: List[str],
    title: str = "Combined Analysis Report",
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Generate a combined professional report from multiple notes"""
    if not note_ids:
        raise HTTPException(status_code=400, detail="No notes provided")
    
    try:
        combined_content = []
        note_titles = []
        
        # Collect content from all notes
        for note_id in note_ids:
            note = await NotesStore.get(note_id)
            if not note:
                continue
                
            # Check user permissions
            if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
                continue
                
            artifacts = note.get("artifacts", {})
            content = artifacts.get("transcript") or artifacts.get("text", "")
            
            if content:
                note_titles.append(note["title"])
                combined_content.append(f"## {note['title']}\n{content}")
        
        if not combined_content:
            raise HTTPException(status_code=400, detail="No accessible content found in provided notes")
        
        # Generate comprehensive report
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        full_content = "\n\n".join(combined_content)
        
        # Check if user is from Expeditors
        is_expeditors_user = current_user and current_user.get("email", "").endswith("@expeditors.com")
        
        # Add logo header for Expeditors users
        logo_header = ""
        if is_expeditors_user:
            logo_header = """
==================================================
           EXPEDITORS INTERNATIONAL
        Comprehensive Business Analysis Report
==================================================

"""
        
        prompt = f"""
        You are a senior business consultant creating a comprehensive executive report{" for Expeditors International" if is_expeditors_user else ""}. 
        Below is content from multiple sources that need to be synthesized into a professional business analysis.

        Combined Content:
        {full_content}

        Create a comprehensive professional report with these sections. Use clean formatting with clear headings and bullet points - NO MARKDOWN SYMBOLS like ### or **:

        EXECUTIVE SUMMARY
        - Overall situation assessment across all content
        - Key themes and critical findings (3-4 sentences)

        COMPREHENSIVE ANALYSIS
        - Major insights from combined content as bullet points starting with •
        - Patterns and connections between different sources
        - Important details that impact decision-making

        STRATEGIC RECOMMENDATIONS
        HIGH-IMPACT ACTIONS (Immediate - next 2 weeks):
        • [list specific actions]

        MEDIUM-TERM INITIATIVES (next 1-3 months):
        • [list strategic initiatives]

        LONG-TERM CONSIDERATIONS (3+ months):
        • [list long-term items]

        IMPLEMENTATION ROADMAP
        WEEK 1-2:
        • [immediate next steps]

        MONTH 1-3:
        • [short-term goals]

        SUCCESS METRICS:
        • [key metrics to track]

        RISK ASSESSMENT
        POTENTIAL CHALLENGES:
        • [list potential obstacles]

        MITIGATION STRATEGIES:
        • [list mitigation approaches]

        STAKEHOLDER INVOLVEMENT
        • [key stakeholders to involve]
        • [communication plan recommendations]

        Use professional business language with clear structure. Format as clean text with proper headings in CAPS and bullet points with •. Do NOT use markdown formatting symbols like ### or **.
        """
        
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            ai_analysis = response.json()
            report_content = ai_analysis["choices"][0]["message"]["content"]
            
            # Add logo header for Expeditors users
            if is_expeditors_user:
                report_content = logo_header + report_content
            
            return {
                "report": report_content,
                "title": title,
                "source_notes": note_titles,
                "note_count": len(note_titles),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "is_expeditors": is_expeditors_user
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate batch report: {str(e)}")

@api_router.get("/notes/{note_id}/export")
async def export_note(
    note_id: str,
    format: str = Query("txt", regex="^(txt|md|json)$"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Export note in various formats (txt, md, json)"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    artifacts = note.get("artifacts", {})
    
    if format == "json":
        # Convert datetime to string for JSON serialization
        export_data = {
            "id": note["id"],
            "title": note["title"],
            "kind": note["kind"],
            "created_at": note["created_at"].isoformat() if hasattr(note["created_at"], 'isoformat') else str(note["created_at"]),
            "artifacts": artifacts
        }
        return JSONResponse(content=export_data)
    
    elif format == "md":
        content = f"# {note['title']}\n\n"
        content += f"**Created:** {note['created_at']}\n"
        content += f"**Type:** {note['kind']}\n\n"
        
        if artifacts.get("transcript"):
            content += "## Transcript\n\n"
            content += artifacts["transcript"] + "\n\n"
        
        if artifacts.get("text"):
            content += "## OCR Text\n\n"
            content += artifacts["text"] + "\n\n"
        
        if artifacts.get("summary"):
            content += "## Summary\n\n"
            content += artifacts["summary"] + "\n\n"
        
        if artifacts.get("actions"):
            content += "## Action Items\n\n"
            for action in artifacts["actions"]:
                content += f"- {action}\n"
        
        return Response(content=content, media_type="text/markdown")
    
    else:  # txt format
        content = f"{note['title']}\n"
        content += "=" * len(note['title']) + "\n\n"
        content += f"Created: {note['created_at']}\n"
        content += f"Type: {note['kind']}\n\n"
        
        if artifacts.get("transcript"):
            content += "TRANSCRIPT:\n"
            content += artifacts["transcript"] + "\n\n"
        
        if artifacts.get("text"):
            content += "OCR TEXT:\n"
            content += artifacts["text"] + "\n\n"
        
        if artifacts.get("summary"):
            content += "SUMMARY:\n"
            content += artifacts["summary"] + "\n\n"
        
        if artifacts.get("actions"):
            content += "ACTION ITEMS:\n"
            for action in artifacts["actions"]:
                content += f"- {action}\n"
        
        return Response(content=content, media_type="text/plain")

@api_router.post("/notes/{note_id}/git-sync")
async def sync_note_to_git(
    note_id: str,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Sync note to Git repository"""
    note = await NotesStore.get(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check if user owns this note (if authenticated)
    if current_user and note.get("user_id") and note.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    background_tasks.add_task(enqueue_git_sync, note_id)
    return {"message": "Git sync queued"}

@api_router.get("/metrics")
async def get_metrics(
    days: int = Query(7, ge=1, le=90),
    current_user: Optional[dict] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get productivity metrics (user-specific if authenticated)"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Build query based on authentication
    query = {"created_at": {"$gte": since}}
    if current_user:
        query["user_id"] = current_user["id"]
    
    # Get notes from the specified time window
    cursor = db["notes"].find(query)
    notes = await cursor.to_list(None)
    
    total = len(notes)
    ready = sum(1 for n in notes if n.get("status") == "ready")
    latencies = [n.get("metrics", {}).get("latency_ms") for n in notes if n.get("metrics", {}).get("latency_ms")]
    
    p95 = None
    if latencies:
        sorted_latencies = sorted(latencies)
        idx = int(0.95 * len(sorted_latencies)) - 1
        if idx >= 0:
            p95 = sorted_latencies[idx]
    
    # Calculate estimated time saved (rough estimates)
    audio_notes = [n for n in notes if n.get("kind") == "audio" and n.get("status") == "ready"]
    photo_notes = [n for n in notes if n.get("kind") == "photo" and n.get("status") == "ready"]
    
    # Rough time savings estimates
    estimated_minutes_saved = len(audio_notes) * 15 + len(photo_notes) * 10
    
    # Update user's total time saved if authenticated
    if current_user:
        await db["users"].update_one(
            {"id": current_user["id"]},
            {"$set": {"total_time_saved": estimated_minutes_saved, "notes_count": total}}
        )
    
    return {
        "window_days": days,
        "notes_total": total,
        "notes_ready": ready,
        "notes_audio": len(audio_notes),
        "notes_photo": len(photo_notes),
        "p95_latency_ms": p95,
        "estimated_minutes_saved": estimated_minutes_saved,
        "success_rate": round(ready / total * 100, 1) if total > 0 else 0,
        "user_authenticated": current_user is not None
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)