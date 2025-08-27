#!/usr/bin/env python3
"""
Test OpenAI API directly
"""

import asyncio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def test_openai_api():
    """Test OpenAI API with a simple transcription"""
    
    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ No API key found!")
        return
        
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Test with the models endpoint first
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            r.raise_for_status()
            data = r.json()
            print(f"✅ API key is valid - found {len(data.get('data', []))} models")
            
            # Check if whisper models are available
            whisper_models = [m for m in data.get('data', []) if 'whisper' in m.get('id', '')]
            if whisper_models:
                print(f"✅ Whisper models available: {[m['id'] for m in whisper_models]}")
            else:
                print("⚠️ No whisper models found")
                
    except Exception as e:
        print(f"❌ API key validation failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    asyncio.run(test_openai_api())