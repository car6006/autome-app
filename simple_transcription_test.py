#!/usr/bin/env python3
"""
Simple test to verify the OpenAI Whisper rate limit fix
"""

import requests
import time
import tempfile
import os
import subprocess
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_test_audio_file():
    """Create a small test audio file"""
    try:
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(temp_fd)
        
        # Generate a simple sine wave audio file
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3',
            '-ar', '16000', '-ac', '1', '-y', temp_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            file_size = os.path.getsize(temp_path)
            log(f"✅ Created test audio file: {file_size / 1024:.1f} KB")
            return temp_path
        else:
            log(f"❌ Failed to create audio file: {result.stderr}")
            return None
            
    except Exception as e:
        log(f"❌ Error creating test audio file: {str(e)}")
        return None

def test_transcription():
    """Test transcription with rate limit handling"""
    base_url = "https://voice-capture-9.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    log("🚀 Testing OpenAI Whisper Rate Limit Fix")
    
    # Register a test user
    test_user_data = {
        "email": f"rate_limit_test_{int(time.time())}@example.com",
        "username": f"ratelimituser{int(time.time())}",
        "password": "RateLimit123!",
        "first_name": "Rate",
        "last_name": "Limit"
    }
    
    try:
        response = requests.post(f"{api_url}/auth/register", json=test_user_data, timeout=30)
        if response.status_code == 200:
            auth_token = response.json().get('access_token')
            log("✅ User registered successfully")
        else:
            log(f"❌ User registration failed: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Registration error: {str(e)}")
        return False
    
    # Create test audio file
    audio_file_path = create_test_audio_file()
    if not audio_file_path:
        return False
    
    try:
        # Upload the audio file
        with open(audio_file_path, 'rb') as f:
            files = {'file': ('rate_limit_test.wav', f, 'audio/wav')}
            data = {'title': 'Rate Limit Test Audio'}
            headers = {'Authorization': f'Bearer {auth_token}'}
            
            response = requests.post(f"{api_url}/upload-file", data=data, files=files, headers=headers, timeout=60)
            
            if response.status_code == 200:
                note_id = response.json().get('id')
                log(f"✅ Audio file uploaded, note ID: {note_id}")
            else:
                log(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
        
        # Monitor transcription progress
        log("⏳ Monitoring transcription progress...")
        start_time = time.time()
        max_wait = 120  # 2 minutes
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{api_url}/notes/{note_id}", headers=headers, timeout=30)
                if response.status_code == 200:
                    note_data = response.json()
                    status = note_data.get('status', 'unknown')
                    
                    if status == 'ready':
                        artifacts = note_data.get('artifacts', {})
                        transcript = artifacts.get('transcript', '')
                        
                        log(f"✅ Transcription completed!")
                        log(f"   Transcript length: {len(transcript)} characters")
                        
                        if transcript and transcript.strip():
                            log("✅ SUCCESS: Non-empty transcript generated!")
                            log(f"   Sample: {transcript[:100]}...")
                            return True
                        else:
                            log("❌ FAILURE: Empty transcript generated")
                            return False
                            
                    elif status == 'failed':
                        artifacts = note_data.get('artifacts', {})
                        error_msg = artifacts.get('error', 'Unknown error')
                        log(f"❌ Transcription failed: {error_msg}")
                        return False
                    else:
                        log(f"   Status: {status}")
                        
                time.sleep(5)
                
            except Exception as e:
                log(f"❌ Error checking status: {str(e)}")
                break
        
        log("⏰ Transcription timeout")
        return False
        
    finally:
        # Clean up test file
        try:
            os.unlink(audio_file_path)
        except:
            pass

if __name__ == "__main__":
    success = test_transcription()
    if success:
        print("\n🎉 RATE LIMIT FIX VERIFIED!")
    else:
        print("\n⚠️  Rate limit fix needs more work")