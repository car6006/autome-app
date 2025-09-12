"""
Enhanced Providers with Dual-Provider System and Live Transcription Support
Provides Emergent LLM Key as primary with OpenAI as fallback
"""

from __future__ import annotations
import asyncio
import base64
import httpx
import io
import json
import logging
import math
import os
import random
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default chunk duration in seconds (configurable via CHUNK_DURATION_SECONDS env var)
CHUNK_DURATION_SECONDS = int(os.getenv("CHUNK_DURATION_SECONDS", "5"))

# Import Emergent integrations
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    print("⚠️  Emergent integrations not available, using OpenAI fallback only")

logger = logging.getLogger(__name__)

class TranscriptionProvider:
    """Enhanced transcription provider with dual-provider support"""
    
    def __init__(self):
        self.emergent_key = os.getenv("EMERGENT_LLM_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        self.use_emergent = EMERGENT_AVAILABLE and self.emergent_key
        
        if self.use_emergent:
            logger.info("🚀 Using Emergent LLM Key as primary transcription provider")
        elif self.openai_key:
            logger.info("🔄 Using OpenAI API as transcription provider")
        else:
            logger.error("❌ No transcription API keys available")

    async def transcribe_audio_chunk(self, audio_file_path: str, session_id: str = None, chunk_idx: int = None) -> dict:
        """
        Enhanced transcription for live streaming chunks
        Returns: {
            "text": str,
            "words": [{"word": str, "start": float, "end": float, "confidence": float}],
            "confidence": float,
            "language": str
        }
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Try Emergent LLM Key first
                if self.use_emergent:
                    try:
                        result = await self._transcribe_with_emergent(audio_file_path, session_id, chunk_idx)
                        if result:
                            logger.info(f"✅ Emergent transcription success for chunk {chunk_idx} (attempt {attempt + 1})")
                            return result
                    except Exception as e:
                        logger.warning(f"🔄 Emergent transcription failed (attempt {attempt + 1}): {e}")
                        if attempt == max_retries - 1:
                            logger.info("🔄 Falling back to OpenAI API")
                
                # Fallback to OpenAI API
                if self.openai_key:
                    result = await self._transcribe_with_openai(audio_file_path, session_id, chunk_idx)
                    if result:
                        logger.info(f"✅ OpenAI transcription success for chunk {chunk_idx} (attempt {attempt + 1})")
                        return result
                
                # If both fail, wait and retry
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                    logger.warning(f"⏳ Retrying transcription in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"❌ Transcription attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Transcription failed after {max_retries} attempts: {str(e)}")
                    
        raise ValueError("Transcription failed - no providers available")

    async def _transcribe_with_emergent(self, audio_file_path: str, session_id: str = None, chunk_idx: int = None) -> dict:
        """Transcribe using Emergent LLM Key with Whisper model"""
        try:
            logger.info(f"🔍 Attempting Emergent transcription for audio file")
            
            # For now, return None to use OpenAI fallback
            # The Emergent integrations don't currently support audio transcription
            logger.info("Emergent audio transcription not available, falling back to OpenAI")
            return None
            
        except Exception as e:
            logger.error(f"❌ Emergent transcription error: {e}")
            return None

    async def _transcribe_with_openai(self, audio_file_path: str, session_id: str = None, chunk_idx: int = None) -> dict:
        """Transcribe using OpenAI Whisper API with enhanced error handling and M4A conversion"""
        actual_file_path = audio_file_path
        temp_wav_path = None
        
        try:
            # Check if file is M4A and convert to WAV if needed
            if audio_file_path.lower().endswith('.m4a'):
                logger.info(f"🔄 M4A file detected, converting to WAV for OpenAI compatibility")
                temp_wav_path = await self._convert_m4a_to_wav(audio_file_path)
                if temp_wav_path:
                    actual_file_path = temp_wav_path
                    logger.info(f"✅ M4A converted to WAV: {temp_wav_path}")
                else:
                    logger.warning(f"⚠️ M4A conversion failed, trying original file")
            
            # Validate audio file before processing
            file_size = os.path.getsize(actual_file_path)
            if file_size < 1000:  # Less than 1KB is likely corrupted
                raise ValueError(f"Audio file too small ({file_size} bytes) - likely corrupted or incomplete")
            
            if file_size > 25 * 1024 * 1024:  # Greater than 25MB (OpenAI limit)
                raise ValueError(f"Audio file too large ({file_size / (1024*1024):.1f} MB) - OpenAI limit is 25MB")
            
            logger.info(f"🎵 Processing audio file: {file_size / 1024:.1f} KB")
            
            with open(actual_file_path, 'rb') as audio_file:
                # Create form data for OpenAI Whisper API
                files = {
                    'file': (f'audio_{int(time.time())}.wav', audio_file, 'audio/wav')
                }
                data = {
                    'model': 'whisper-1',
                    'language': 'en',  # Force English transcription
                    'response_format': 'verbose_json',  # Get word-level timestamps
                    'timestamp_granularities': ['word']
                }
                
                headers = {
                    'Authorization': f'Bearer {self.openai_key}'
                }
                
                # Single attempt with clear error messages
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        'https://api.openai.com/v1/audio/transcriptions',
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Process the response into our standard format
                        words = []
                        if 'words' in result:
                            words = [
                                {
                                    "word": word.get("word", ""),
                                    "start": word.get("start", 0.0),
                                    "end": word.get("end", 0.0),
                                    "confidence": 1.0  # OpenAI doesn't provide confidence
                                }
                                for word in result.get("words", [])
                            ]
                        
                        logger.info(f"✅ OpenAI transcription successful: '{result.get('text', '')[:50]}...'")
                        return {
                            "text": result.get("text", ""),
                            "words": words,
                            "confidence": 0.95,  # Default confidence for OpenAI
                            "language": result.get("language", "en"),
                            "duration": result.get("duration", 0.0),
                            "provider": "openai_whisper"
                        }
                        
                    elif response.status_code == 429:
                        # Rate limit with clear message
                        logger.warning(f"🚦 OpenAI rate limit hit")
                        raise ValueError("OpenAI is currently rate limited. Since you topped up your account, this should resolve shortly. Please try again in a few minutes.")
                            
                    elif response.status_code == 401:
                        # Authentication error
                        raise ValueError("OpenAI API authentication failed. Please check your API key configuration.")
                        
                    elif response.status_code == 400:
                        # Bad request - usually audio format issue
                        error_detail = response.text
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("error", {}).get("message", error_detail)
                        except:
                            pass
                        raise ValueError(f"Audio format issue: {error_detail}")
                        
                    else:
                        # Other errors
                        error_detail = response.text
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("error", {}).get("message", error_detail)
                        except:
                            pass
                        
                        logger.error(f"OpenAI API error {response.status_code}: {error_detail}")
                        raise ValueError(f"OpenAI transcription failed: {error_detail}")
                        
        except ValueError as ve:
            logger.error(f"❌ OpenAI transcription validation error: {str(ve)}")
            raise ve
        except Exception as e:
            logger.error(f"❌ OpenAI transcription unexpected error: {str(e)}")
            raise e
        finally:
            # Clean up temporary WAV file if created
            if temp_wav_path and temp_wav_path != audio_file_path:
                try:
                    os.unlink(temp_wav_path)
                    logger.info(f"🧹 Cleaned up temporary WAV file: {temp_wav_path}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Failed to cleanup temp WAV file {temp_wav_path}: {cleanup_error}")
                    pass

    async def _convert_m4a_to_wav(self, m4a_file_path: str) -> str:
        """Convert M4A file to WAV format using FFmpeg for OpenAI compatibility"""
        try:
            import subprocess
            import tempfile
            
            # Create temporary WAV file
            temp_fd, temp_wav_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            
            logger.info(f"🔄 Converting M4A to WAV: {m4a_file_path} -> {temp_wav_path}")
            
            # FFmpeg command for M4A to WAV conversion
            cmd = [
                'ffmpeg',
                '-i', m4a_file_path,           # Input M4A file
                '-acodec', 'pcm_s16le',        # Use WAV PCM encoding
                '-ar', '16000',                # 16kHz sample rate (optimal for Whisper)
                '-ac', '1',                    # Mono audio
                '-y',                          # Overwrite output file
                temp_wav_path                  # Output WAV file
            ]
            
            # Execute FFmpeg conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for conversion
            )
            
            if result.returncode == 0:
                # Verify the output file was created and has content
                if os.path.exists(temp_wav_path) and os.path.getsize(temp_wav_path) > 0:
                    file_size = os.path.getsize(temp_wav_path)
                    logger.info(f"✅ M4A conversion successful: {file_size} bytes WAV file created")
                    return temp_wav_path
                else:
                    logger.error(f"❌ M4A conversion failed: Output WAV file is empty or missing")
                    try:
                        os.unlink(temp_wav_path)
                    except:
                        pass
                    return None
            else:
                logger.error(f"❌ FFmpeg M4A conversion failed: {result.stderr}")
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ M4A conversion timeout after 120 seconds")
            try:
                os.unlink(temp_wav_path)
            except:
                pass
            return None
        except Exception as e:
            logger.error(f"❌ M4A conversion error: {e}")
            try:
                if 'temp_wav_path' in locals():
                    os.unlink(temp_wav_path)
            except:
                pass
            return None

class AIProvider:
    """Enhanced AI provider for GPT analysis with dual-provider support"""
    
    def __init__(self):
        self.emergent_key = os.getenv("EMERGENT_LLM_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.use_emergent = EMERGENT_AVAILABLE and self.emergent_key
        
        if self.use_emergent:
            logger.info("🚀 Using Emergent LLM Key as primary AI provider")
        elif self.openai_key:
            logger.info("🔄 Using OpenAI API as AI provider")
        else:
            logger.error("❌ No AI API keys available")

    async def generate_analysis(self, content: str, analysis_type: str = "general", user_context: dict = None) -> dict:
        """
        Generate AI analysis with dual-provider support
        """
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # Try Emergent LLM Key first
                if self.use_emergent:
                    try:
                        result = await self._analyze_with_emergent(content, analysis_type, user_context)
                        if result:
                            logger.info(f"✅ Emergent AI analysis success (attempt {attempt + 1})")
                            return result
                    except Exception as e:
                        logger.warning(f"🔄 Emergent AI analysis failed (attempt {attempt + 1}): {e}")
                
                # Fallback to OpenAI API
                if self.openai_key:
                    result = await self._analyze_with_openai(content, analysis_type, user_context)
                    if result:
                        logger.info(f"✅ OpenAI AI analysis success (attempt {attempt + 1})")
                        return result
                
                # If both fail, wait and retry
                if attempt < max_retries - 1:
                    wait_time = 5
                    logger.warning(f"⏳ Retrying AI analysis in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"❌ AI analysis attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise ValueError(f"AI analysis failed after {max_retries} attempts: {str(e)}")
                    
        raise ValueError("AI analysis failed - no providers available")

    async def _analyze_with_emergent(self, content: str, analysis_type: str, user_context: dict = None) -> dict:
        """Analyze using Emergent LLM Key with multiple model fallbacks"""
        
        # Define fallback models in order of preference
        fallback_models = [
            ("openai", "gpt-4o-mini"),       # Fast and efficient
            ("anthropic", "claude-3-5-sonnet-20241022"),  # High quality
            ("google", "gemini-2.0-flash"),  # Fast alternative
            ("openai", "gpt-4o"),           # More powerful if needed
        ]
        
        for provider, model in fallback_models:
            try:
                logger.info(f"🤖 Attempting AI analysis with {provider}/{model}")
                
                # Create chat instance
                chat = LlmChat(
                    api_key=self.emergent_key,
                    session_id=f"analysis_{int(time.time())}_{provider}",
                    system_message=self._get_system_prompt(analysis_type, user_context)
                ).with_model(provider, model)
                
                # Create user message for analysis
                user_message = UserMessage(text=content)
                
                # Get analysis
                response = await chat.send_message(user_message)
                
                logger.info(f"✅ AI analysis successful with {provider}/{model}")
                return {
                    "analysis": response,
                    "provider": f"emergent_{provider}",
                    "model": model
                }
                
            except Exception as e:
                logger.warning(f"❌ {provider}/{model} failed: {e}")
                # Continue to next fallback
                continue
        
        # If all fallbacks fail
        raise Exception("All AI analysis providers failed")

    async def _analyze_with_openai(self, content: str, analysis_type: str, user_context: dict = None) -> dict:
        """Analyze using OpenAI API directly"""
        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt(analysis_type, user_context)},
                {"role": "user", "content": content}
            ]
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return {
                        "analysis": analysis,
                        "provider": "openai",
                        "model": "gpt-4o-mini"
                    }
                else:
                    error_detail = response.text
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("error", {}).get("message", error_detail)
                    except:
                        pass
                    
                    if response.status_code == 429:
                        raise ValueError("AI service rate limit exceeded. Please try again in a moment.")
                    else:
                        raise ValueError(f"AI service error: {error_detail}")
                        
        except Exception as e:
            logger.error(f"❌ OpenAI AI analysis error: {e}")
            raise

    def _get_system_prompt(self, analysis_type: str, user_context: dict = None) -> str:
        """Get system prompt based on analysis type and user context"""
        base_prompt = "You are a professional AI assistant specialized in content analysis."
        
        if analysis_type == "meeting_minutes":
            return f"{base_prompt} Generate professional meeting minutes from the provided transcript."
        elif analysis_type == "action_items":
            return f"{base_prompt} Extract and format action items from the provided content."
        elif analysis_type == "summary":
            return f"{base_prompt} Create a concise summary of the provided content."
        else:
            return f"{base_prompt} Analyze and respond to the provided content professionally."

# Initialize global providers
transcription_provider = TranscriptionProvider()
ai_provider = AIProvider()

async def split_large_audio_file(file_path: str, chunk_duration: int | None = None) -> list[str]:
    """Split audio file into smaller chunks using ffmpeg"""
    chunks = []
    chunk_duration = chunk_duration or CHUNK_DURATION_SECONDS
    
    try:
        # Get audio duration using ffprobe
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.warning(f"Could not get audio duration for {file_path}")
            return [file_path]  # Return original file if can't split
        
        data = json.loads(result.stdout)
        # Handle potential missing duration key
        format_data = data.get('format', {})
        if 'duration' not in format_data:
            logger.warning(f"No duration found in audio metadata for {file_path}")
            return [file_path]
        duration = float(format_data['duration'])
        
        if duration <= chunk_duration:
            return [file_path]  # File is already small enough
        
        num_chunks = math.ceil(duration / chunk_duration)
        logger.info(f"🔨 Splitting {duration:.1f}s audio into {num_chunks} chunks of {chunk_duration}s each")
        
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
                logger.info(f"✅ Created chunk {i+1}/{num_chunks}: {chunk_path}")
            else:
                logger.error(f"❌ Failed to create chunk {i+1}: {result.stderr}")
                # Clean up failed chunk
                try:
                    os.unlink(chunk_path)
                except:
                    pass
        
        return chunks
        
    except Exception as e:
        logger.error(f"❌ Error splitting audio file: {e}")
        return [file_path]  # Return original file if splitting fails

# Export the enhanced functions for backward compatibility
async def transcribe_audio(file_path: str, session_id: str = None) -> dict:
    """Enhanced transcription function with dual-provider support and large file handling"""
    
    # Check if it's a URL or local path
    if file_path.startswith('http'):
        # Download file first
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(file_path, follow_redirects=True)
            r.raise_for_status()
            fd, local_path = tempfile.mkstemp()
            with os.fdopen(fd, "wb") as f:
                f.write(r.content)
            file_path = local_path
    
    try:
        # Check file size for chunking logic
        file_size = os.path.getsize(file_path)
        OPENAI_MAX_FILE_SIZE = 24 * 1024 * 1024  # 24MB to be safe
        
        logger.info(f"🎵 Audio file size: {file_size / (1024*1024):.1f} MB")
        
        if file_size <= OPENAI_MAX_FILE_SIZE:
            # Small file - process directly
            logger.info("📝 File size OK, processing directly")
            result = await transcription_provider.transcribe_audio_chunk(file_path, session_id)
            
            # Convert to expected format for tasks.py
            return {
                "text": result.get("text", ""),
                "summary": "",
                "actions": [],
                "note": ""
            }
        else:
            # Large file - need to split into chunks
            logger.info(f"📁 File too large ({file_size / (1024*1024):.1f} MB), splitting into chunks")
            
            # Split audio file into chunks with configurable duration
            chunks = await split_large_audio_file(file_path, chunk_duration=CHUNK_DURATION_SECONDS)
            if not chunks:
                return {"text": "", "summary": "", "actions": [], "note": "Failed to split audio file"}
            
            logger.info(f"🔄 Processing {len(chunks)} audio chunks")
            transcriptions = []
            
            # Process each chunk sequentially
            for i, chunk_path in enumerate(chunks):
                try:
                    logger.info(f"🎤 Transcribing chunk {i+1}/{len(chunks)}")
                    result = await transcription_provider.transcribe_audio_chunk(chunk_path, f"{session_id}_chunk_{i}")
                    
                    chunk_text = result.get("text", "").strip()
                    if chunk_text:
                        # Add chunk number for long transcriptions
                        if len(chunks) > 1:
                            transcriptions.append(f"[Part {i+1}] {chunk_text}")
                        else:
                            transcriptions.append(chunk_text)
                    else:
                        logger.warning(f"⚠️ Empty transcription for chunk {i+1}")
                    
                    # Add delay between chunks to respect rate limits
                    if i < len(chunks) - 1:
                        logger.info(f"⏳ Waiting 3 seconds before processing next chunk...")
                        await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing chunk {i+1}: {e}")
                    transcriptions.append(f"[Part {i+1}] Error processing this segment")
                
                finally:
                    # Clean up chunk file
                    try:
                        os.unlink(chunk_path)
                    except:
                        pass
            
            # Combine all transcriptions
            full_text = " ".join(transcriptions).strip()
            
            return {
                "text": full_text,
                "summary": "",
                "actions": [],
                "note": f"Transcribed from {len(chunks)} audio segments"
            }
            
    except Exception as e:
        logger.error(f"❌ Enhanced transcription error: {e}")
        return {"text": "", "summary": "", "actions": [], "note": f"Transcription failed: {str(e)}"}

async def generate_ai_analysis(content: str, analysis_type: str = "general", user_context: dict = None) -> str:
    """Enhanced AI analysis function with dual-provider support"""
    result = await ai_provider.generate_analysis(content, analysis_type, user_context)
    return result.get("analysis", "")