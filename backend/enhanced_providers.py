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

# Default chunk duration in seconds - Optimized for faster processing
CHUNK_DURATION_SECONDS = int(os.getenv("CHUNK_DURATION_SECONDS", "3"))  # Reduced from 5 to 3 seconds

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
        """Transcribe using OpenAI Whisper API with universal audio conversion"""
        actual_file_path = audio_file_path
        temp_converted_path = None
        
        try:
            # Convert any audio/video format to MP3 for consistent processing
            logger.info(f"🔄 Converting audio to MP3 for optimal processing: {audio_file_path}")
            temp_converted_path = await self._convert_any_to_mp3(audio_file_path)
            if temp_converted_path:
                actual_file_path = temp_converted_path
                logger.info(f"✅ Audio converted to MP3: {temp_converted_path}")
            else:
                logger.warning(f"⚠️ Audio conversion failed, trying original file")
            
            # Validate audio file before processing
            file_size = os.path.getsize(actual_file_path)
            if file_size < 1000:  # Less than 1KB is likely corrupted
                raise ValueError(f"Audio file too small ({file_size} bytes) - likely corrupted or incomplete")
            
            if file_size > 25 * 1024 * 1024:  # Greater than 25MB (OpenAI limit)
                raise ValueError(f"Audio file too large ({file_size / (1024*1024):.1f} MB) - OpenAI limit is 25MB")
            
            logger.info(f"🎵 Processing converted audio file: {file_size / 1024:.1f} KB")
            
            with open(actual_file_path, 'rb') as audio_file:
                # Create form data for OpenAI Whisper API
                files = {
                    'file': (f'audio_{int(time.time())}.mp3', audio_file, 'audio/mpeg')
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
            # Clean up temporary converted file if created
            if temp_converted_path and temp_converted_path != audio_file_path:
                try:
                    os.unlink(temp_converted_path)
                    logger.info(f"🧹 Cleaned up temporary converted file: {temp_converted_path}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Failed to cleanup temp converted file {temp_converted_path}: {cleanup_error}")
                    pass

    async def _convert_any_to_mp3(self, input_file_path: str) -> str:
        """Convert any audio/video file to MP3 format using FFmpeg for consistent processing"""
        try:
            import subprocess
            import tempfile
            
            # Create temporary MP3 file
            temp_fd, temp_mp3_path = tempfile.mkstemp(suffix='.mp3')
            os.close(temp_fd)
            
            logger.info(f"🔄 Converting to MP3: {input_file_path} -> {temp_mp3_path}")
            
            # Universal FFmpeg command for any format to MP3 conversion
            cmd = [
                'ffmpeg',
                '-i', input_file_path,         # Input file (any format)
                '-vn',                         # No video (audio only)  
                '-acodec', 'libmp3lame',       # Use MP3 encoder
                '-ab', '128k',                 # 128kbps bitrate (good quality, reasonable size)
                '-ar', '44100',                # 44.1kHz sample rate (standard)
                '-ac', '2',                    # Stereo audio
                '-f', 'mp3',                   # Force MP3 format
                '-y',                          # Overwrite output file
                temp_mp3_path                  # Output MP3 file
            ]
            
            # Execute FFmpeg conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for conversion
            )
            
            if result.returncode == 0:
                # Verify the output file was created and has content
                if os.path.exists(temp_mp3_path) and os.path.getsize(temp_mp3_path) > 0:
                    file_size = os.path.getsize(temp_mp3_path)
                    logger.info(f"✅ Universal audio conversion successful: {file_size} bytes MP3 file created")
                    return temp_mp3_path
                else:
                    logger.error(f"❌ Audio conversion failed: Output MP3 file is empty or missing")
                    try:
                        os.unlink(temp_mp3_path)
                    except:
                        pass
                    raise ValueError("Conversion produced empty MP3 file")
            else:
                logger.error(f"❌ FFmpeg conversion failed: {result.stderr}")
                try:
                    os.unlink(temp_mp3_path)
                except:
                    pass
                raise ValueError(f"FFmpeg conversion failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Audio conversion timeout after 5 minutes")
            try:
                os.unlink(temp_mp3_path)
            except:
                pass
            raise ValueError("Audio conversion timed out - file may be too large or corrupted")
        except Exception as e:
            logger.error(f"❌ Audio conversion error: {str(e)}")
            try:
                os.unlink(temp_mp3_path)
            except:
                pass
            raise ValueError(f"Audio conversion failed: {str(e)}")

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
            
            # Enhanced ffmpeg command that preserves audio quality
            cmd = [
                'ffmpeg', '-i', file_path,
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-acodec', 'pcm_s16le',  # PCM 16-bit for compatibility
                '-ar', '44100',  # Preserve higher sample rate for quality
                '-ac', '2',  # Preserve stereo if available (Whisper handles both)
                '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
                '-f', 'wav',  # Explicitly specify WAV format
                '-y',  # Overwrite output file
                chunk_path
            ]
            
            # Create chunk with enhanced ffmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error creating chunk {i+1}: {result.stderr}")
                continue
                
            # Validate chunk was created successfully and has audio content
            if not os.path.exists(chunk_path):
                logger.error(f"Chunk file not created: {chunk_path}")
                continue
                
            # Check if chunk has reasonable file size (not too small, indicating empty audio)
            chunk_size = os.path.getsize(chunk_path)
            if chunk_size < 1000:  # Less than 1KB indicates likely empty/corrupted audio
                logger.warning(f"Chunk {i+1} is suspiciously small ({chunk_size} bytes), may be corrupted")
                os.unlink(chunk_path)  # Remove corrupted chunk
                continue
                
            # Validate audio content using ffprobe
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                '-show_format', '-show_streams', chunk_path
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            
            if probe_result.returncode == 0:
                try:
                    probe_data = json.loads(probe_result.stdout)
                    if 'streams' in probe_data and len(probe_data['streams']) > 0:
                        stream = probe_data['streams'][0]
                        duration = float(stream.get('duration', 0))
                        if duration > 0.5:  # Chunk should have reasonable duration
                            chunks.append(chunk_path)
                            logger.info(f"✅ Valid chunk {i+1} created: {chunk_size} bytes, {duration:.2f}s duration")
                        else:
                            logger.warning(f"Chunk {i+1} has invalid duration: {duration}s")
                            os.unlink(chunk_path)
                    else:
                        logger.warning(f"Chunk {i+1} has no audio streams")
                        os.unlink(chunk_path)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse ffprobe output for chunk {i+1}")
                    # Still add chunk if ffprobe parsing fails but file exists
                    chunks.append(chunk_path)
            else:
                logger.warning(f"Could not validate chunk {i+1} with ffprobe")
                # Still add chunk if ffprobe fails but file was created successfully
                chunks.append(chunk_path)
        
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
            
            # For very long recordings, use larger chunks to reduce API calls and improve reliability
            # Calculate optimal chunk duration based on file size
            file_size_mb = file_size / (1024*1024)
            if file_size_mb > 50:  # Files larger than 50MB (likely very long recordings)
                chunk_duration = 120  # 2 minutes per chunk for very long files
                logger.info(f"🕒 Using 2-minute chunks for very long recording ({file_size_mb:.1f} MB)")
            elif file_size_mb > 20:  # Files larger than 20MB
                chunk_duration = 60   # 1 minute per chunk for long files
                logger.info(f"🕒 Using 1-minute chunks for long recording ({file_size_mb:.1f} MB)")
            else:
                chunk_duration = CHUNK_DURATION_SECONDS  # Use default for smaller files
                logger.info(f"🕒 Using {chunk_duration}-second chunks for standard file ({file_size_mb:.1f} MB)")
            
            # Split audio file into chunks with optimal duration
            chunks = await split_large_audio_file(file_path, chunk_duration=chunk_duration)
            if not chunks:
                return {"text": "", "summary": "", "actions": [], "note": "Failed to split audio file"}
            
            logger.info(f"🔄 Processing {len(chunks)} audio chunks")
            transcriptions = []
            
            # Process each chunk sequentially with enhanced reliability
            for i, chunk_path in enumerate(chunks):
                max_retries = 3
                retry_delay = 5  # Start with 5 seconds
                
                for attempt in range(max_retries):
                    try:
                        logger.info(f"🎤 Transcribing chunk {i+1}/{len(chunks)} (attempt {attempt+1})")
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
                        
                        # Success - break out of retry loop
                        break
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing chunk {i+1} (attempt {attempt+1}): {e}")
                        
                        if attempt < max_retries - 1:
                            logger.info(f"🔄 Retrying chunk {i+1} in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            # Final attempt failed
                            logger.error(f"💥 Failed to process chunk {i+1} after {max_retries} attempts")
                            transcriptions.append(f"[Part {i+1}] Error processing this segment after multiple attempts")
                
                # Add delay between chunks to respect rate limits and prevent overwhelming the API
                if i < len(chunks) - 1:
                    delay = 2 if len(chunks) > 50 else 3  # Shorter delay for very long files
                    logger.info(f"⏳ Waiting {delay} seconds before processing next chunk...")
                    await asyncio.sleep(delay)
                
                # Clean up chunk file immediately to save disk space
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