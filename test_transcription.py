#!/usr/bin/env python3
"""
Test transcription functionality directly
"""

import asyncio
import sys
import os
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

sys.path.append('/app/backend')

from providers import stt_transcribe
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_transcription():
    """Test the transcription function directly"""
    
    # Check environment variables
    whisper_key = os.getenv("WHISPER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"WHISPER_API_KEY: {'Found' if whisper_key else 'NOT FOUND'}")
    print(f"OPENAI_API_KEY: {'Found' if openai_key else 'NOT FOUND'}")
    
    if whisper_key:
        print(f"WHISPER_API_KEY starts with: {whisper_key[:10]}...")
    
    # Test file paths
    test_files = [
        "/app/Regional_Meeting_Test.mp3",
        "/app/Regional_Meeting_20_August_2025.mp3" 
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n🔍 Testing transcription for: {file_path}")
            print(f"File size: {os.path.getsize(file_path) / (1024*1024):.1f} MB")
            
            try:
                result = await stt_transcribe(file_path)
                print(f"Result: {result}")
                
                if result.get('text'):
                    print(f"✅ Transcription successful: {len(result['text'])} characters")
                    print(f"First 200 chars: {result['text'][:200]}...")
                else:
                    print(f"❌ Transcription failed: {result}")
                    
            except Exception as e:
                print(f"❌ Exception during transcription: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ File not found: {file_path}")

if __name__ == "__main__":
    asyncio.run(test_transcription())