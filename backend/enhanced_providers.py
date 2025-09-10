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
import os
import random
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        """Transcribe using OpenAI Whisper API with enhanced retry logic"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                # Create form data for OpenAI Whisper API
                files = {
                    'file': (f'chunk_{chunk_idx}.wav', audio_file, 'audio/wav')
                }
                data = {
                    'model': 'whisper-1',
                    'response_format': 'verbose_json',  # Get word-level timestamps
                    'timestamp_granularities': ['word']
                }
                
                headers = {
                    'Authorization': f'Bearer {self.openai_key}'
                }
                
                # Enhanced retry logic for live transcription
                for attempt in range(3):
                    try:
                        async with httpx.AsyncClient(timeout=30) as client:
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
                                
                                return {
                                    "text": result.get("text", ""),
                                    "words": words,
                                    "confidence": 0.95,  # Default confidence for OpenAI
                                    "language": result.get("language", "en"),
                                    "duration": result.get("duration", 0.0)
                                }
                                
                            elif response.status_code == 429:
                                # Rate limit - provide helpful message instead of fake text
                                logger.warning(f"🚦 OpenAI rate limit hit for transcription")
                                raise ValueError("OpenAI transcription service is currently rate limited. Please try again in a few minutes, or contact support to increase your quota.")
                                    
                            else:
                                error_detail = response.text
                                try:
                                    error_data = response.json()
                                    error_detail = error_data.get("error", {}).get("message", error_detail)
                                except:
                                    pass
                                
                                if response.status_code == 400:
                                    raise ValueError(f"Invalid audio format: {error_detail}")
                                else:
                                    raise ValueError(f"OpenAI API error {response.status_code}: {error_detail}")
                                    
                    except httpx.TimeoutException:
                        logger.warning(f"⏱️  Transcription timeout (attempt {attempt + 1}) for chunk {chunk_idx}")
                        if attempt == 2:
                            raise ValueError("Transcription timeout")
                        await asyncio.sleep(2 ** attempt)
                        
        except Exception as e:
            logger.error(f"❌ OpenAI transcription error for chunk {chunk_idx}: {e}")
            raise

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

# Export the enhanced functions for backward compatibility
async def transcribe_audio(file_path: str, session_id: str = None) -> dict:
    """Enhanced transcription function with dual-provider support"""
    return await transcription_provider.transcribe_audio_chunk(file_path, session_id)

async def generate_ai_analysis(content: str, analysis_type: str = "general", user_context: dict = None) -> str:
    """Enhanced AI analysis function with dual-provider support"""
    result = await ai_provider.generate_analysis(content, analysis_type, user_context)
    return result.get("analysis", "")