"""
YouTube URL Processing for AUTO-ME
Extracts audio from YouTube videos for transcription
"""

import os
import asyncio
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
import json
import subprocess
from urllib.parse import urlparse, parse_qs
import re

logger = logging.getLogger(__name__)

class YouTubeProcessor:
    """Process YouTube URLs for audio extraction and transcription"""
    
    def __init__(self):
        self.youtube_dl_path = self._check_youtube_dl()
    
    def _check_youtube_dl(self) -> Optional[str]:
        """Check if yt-dlp is available"""
        # Try common paths for yt-dlp
        possible_paths = [
            'yt-dlp',
            '/usr/local/bin/yt-dlp',
            '/usr/bin/yt-dlp',
            '/root/.venv/bin/yt-dlp',
            '/opt/venv/bin/yt-dlp'
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"✅ yt-dlp found at {path}: {result.stdout.strip()}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        # Fallback to youtube-dl
        youtube_dl_paths = [
            'youtube-dl',
            '/usr/local/bin/youtube-dl',
            '/usr/bin/youtube-dl',
            '/root/.venv/bin/youtube-dl'
        ]
        
        for path in youtube_dl_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"✅ youtube-dl found at {path}: {result.stdout.strip()}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        logger.error("❌ Neither yt-dlp nor youtube-dl found. Install with: pip install yt-dlp")
        return None
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/.*[?&]v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def validate_youtube_url(self, url: str) -> bool:
        """Validate if URL is a supported YouTube URL"""
        video_id = self.extract_video_id(url)
        return video_id is not None
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video metadata without downloading"""
        if not self.youtube_dl_path:
            raise RuntimeError("YouTube download tool not available")
        
        if not self.validate_youtube_url(url):
            raise ValueError("Invalid YouTube URL format")
        
        try:
            cmd = [
                self.youtube_dl_path,
                '--dump-json',
                '--no-playlist',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '--referer', 'https://www.youtube.com/',
                '--add-header', 'Accept-Language:en-US,en;q=0.9',
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error(f"❌ Video info extraction failed: {error_msg}")
                raise RuntimeError(f"Failed to get video info: {error_msg}")
            
            video_info = json.loads(stdout.decode('utf-8'))
            
            # Extract key information
            return {
                'id': video_info.get('id'),
                'title': video_info.get('title', 'Unknown Title'),
                'duration': video_info.get('duration', 0),
                'uploader': video_info.get('uploader', 'Unknown'),
                'upload_date': video_info.get('upload_date'),
                'view_count': video_info.get('view_count', 0),
                'description': video_info.get('description', '')[:500] + '...' if video_info.get('description', '') else '',
                'thumbnail': video_info.get('thumbnail'),
                'webpage_url': video_info.get('webpage_url', url)
            }
            
        except asyncio.TimeoutError:
            logger.error("❌ Video info extraction timed out")
            raise RuntimeError("Video info extraction timed out after 30 seconds")
        except json.JSONDecodeError:
            logger.error("❌ Failed to parse video info JSON")
            raise RuntimeError("Failed to parse video information")
        except Exception as e:
            logger.error(f"❌ Unexpected error getting video info: {str(e)}")
            raise RuntimeError(f"Unexpected error: {str(e)}")
    
    async def extract_audio(self, url: str, output_path: Optional[str] = None, retry_count: int = 0) -> str:
        """Extract audio from YouTube video with multiple fallback strategies"""
        if not self.youtube_dl_path:
            raise RuntimeError("YouTube download tool not available")
        
        if not self.validate_youtube_url(url):
            raise ValueError("Invalid YouTube URL format")
        
        # Create temp directory if no output path provided
        if output_path is None:
            temp_dir = tempfile.mkdtemp(prefix='autome_youtube_')
            output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        # Different extraction strategies to try
        strategies = [
            # Strategy 1: Standard with browser spoofing
            {
                'name': 'Browser Spoofing',
                'extra_args': [
                    '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    '--referer', 'https://www.youtube.com/',
                    '--add-header', 'Accept-Language:en-US,en;q=0.9'
                ]
            },
            # Strategy 2: Different user agent
            {
                'name': 'Alternative User Agent', 
                'extra_args': [
                    '--user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
                ]
            },
            # Strategy 3: No extra headers (basic)
            {
                'name': 'Basic Extraction',
                'extra_args': []
            }
        ]
        
        current_strategy = strategies[min(retry_count, len(strategies) - 1)]
        logger.info(f"🎵 Trying extraction strategy: {current_strategy['name']}")
        
        try:
            cmd = [
                self.youtube_dl_path,
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '0',  # Best quality
                '--no-playlist',
                '--output', output_path,
                url
            ] + current_strategy['extra_args']
            
            logger.info(f"🎵 Extracting audio from: {url}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 minutes
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error(f"❌ Audio extraction failed: {error_msg}")
                
                # Check for specific YouTube errors and retry with different strategy
                if ("403: Forbidden" in error_msg or "HTTP Error 403" in error_msg) and retry_count < 2:
                    logger.warning(f"⚠️ Strategy '{current_strategy['name']}' blocked, trying different approach...")
                    await asyncio.sleep(2)  # Brief delay before retry
                    return await self.extract_audio(url, output_path, retry_count + 1)
                elif "403: Forbidden" in error_msg or "HTTP Error 403" in error_msg:
                    raise RuntimeError("YouTube blocked this video download after trying multiple methods. This may be due to copyright restrictions, geographic limitations, or temporary YouTube protections. Please try a different video or try again later.")
                elif "unavailable" in error_msg.lower():
                    raise RuntimeError("This YouTube video is unavailable or has been removed. Please try a different video.")
                elif "private" in error_msg.lower():
                    raise RuntimeError("This YouTube video is private and cannot be processed. Please try a public video.")
                elif "age-restricted" in error_msg.lower():
                    raise RuntimeError("This YouTube video is age-restricted and cannot be processed automatically.")
                else:
                    if retry_count < 2:
                        logger.warning(f"⚠️ Extraction failed with '{current_strategy['name']}', trying different approach...")
                        await asyncio.sleep(2)
                        return await self.extract_audio(url, output_path, retry_count + 1)
                    else:
                        raise RuntimeError(f"YouTube audio extraction failed after trying multiple methods. This may be temporary - please try again later. Details: {error_msg[:200]}")
            
            # Find the extracted audio file
            output_dir = os.path.dirname(output_path)
            audio_files = []
            for ext in ['.wav', '.mp3', '.m4a']:
                audio_files.extend(Path(output_dir).glob(f'*{ext}'))
            
            if not audio_files:
                raise RuntimeError("No audio file was created")
            
            # Return the path to the extracted audio file
            audio_file_path = str(audio_files[0])
            logger.info(f"✅ Audio extracted successfully: {audio_file_path}")
            return audio_file_path
            
        except asyncio.TimeoutError:
            logger.error("❌ Audio extraction timed out")
            raise RuntimeError("Audio extraction timed out after 5 minutes")
        except Exception as e:
            logger.error(f"❌ Unexpected error during audio extraction: {str(e)}")
            raise RuntimeError(f"Audio extraction failed: {str(e)}")
    
    async def process_youtube_url(self, url: str, user_id: str) -> Dict[str, Any]:
        """Complete YouTube URL processing pipeline"""
        try:
            # Step 1: Get video information
            logger.info(f"🔍 Getting video info for: {url}")
            video_info = await self.get_video_info(url)
            
            # Step 2: Validate video duration (max 2 hours)
            max_duration = 7200  # 2 hours in seconds
            if video_info['duration'] > max_duration:
                raise ValueError(f"Video too long ({video_info['duration']/60:.1f} minutes). Maximum: {max_duration/60} minutes")
            
            # Step 3: Extract audio
            logger.info(f"🎵 Extracting audio from: {video_info['title']}")
            audio_file_path = await self.extract_audio(url)
            
            # Step 4: Verify audio file
            if not os.path.exists(audio_file_path):
                raise RuntimeError("Audio file was not created successfully")
            
            file_size = os.path.getsize(audio_file_path)
            if file_size < 1000:  # Less than 1KB
                raise RuntimeError("Audio file appears to be corrupted (too small)")
            
            logger.info(f"✅ YouTube processing complete. Audio file: {file_size / (1024*1024):.1f} MB")
            
            return {
                'success': True,
                'audio_file_path': audio_file_path,
                'video_info': video_info,
                'file_size': file_size,
                'estimated_processing_time': min(300, video_info['duration'] * 0.1)  # Estimate based on duration
            }
            
        except Exception as e:
            logger.error(f"❌ YouTube processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'video_info': None
            }
    
    def cleanup_temp_files(self, file_path: str):
        """Clean up temporary files"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                # Also clean up the directory if it's empty
                directory = os.path.dirname(file_path)
                if os.path.exists(directory) and not os.listdir(directory):
                    os.rmdir(directory)
                logger.info(f"🧹 Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up temporary file {file_path}: {e}")

# Global instance
youtube_processor = YouTubeProcessor()
logger.info(f"🎬 YouTube processor initialized with path: {youtube_processor.youtube_dl_path}")