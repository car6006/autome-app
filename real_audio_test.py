#!/usr/bin/env python3
"""
Real Audio Transcription Test
Tests transcription with a more realistic audio file
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid
import tempfile
import wave
import struct
import math

# Configuration
BACKEND_URL = "https://audio-chunk-wizard.preview.emergentagent.com/api"

def create_realistic_audio_file():
    """Create a more realistic audio file with actual audio content"""
    try:
        # Create a WAV file with a simple tone pattern
        sample_rate = 16000
        duration = 3  # 3 seconds
        frequency = 440  # A4 note
        
        # Generate sine wave audio data
        frames = []
        for i in range(int(sample_rate * duration)):
            # Create a simple pattern that might produce some transcription
            # Mix of tones and silence to simulate speech patterns
            t = i / sample_rate
            if int(t * 2) % 2 == 0:  # Alternate between tone and silence
                value = int(16384 * math.sin(2 * math.pi * frequency * t))
            else:
                value = int(8192 * math.sin(2 * math.pi * (frequency * 1.5) * t))
            frames.append(struct.pack('<h', value))
        
        # Create WAV file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
        with os.fdopen(temp_fd, 'wb') as temp_file:
            # Write WAV header
            temp_file.write(b'RIFF')
            temp_file.write(struct.pack('<I', 36 + len(frames) * 2))
            temp_file.write(b'WAVE')
            temp_file.write(b'fmt ')
            temp_file.write(struct.pack('<I', 16))  # PCM format chunk size
            temp_file.write(struct.pack('<H', 1))   # PCM format
            temp_file.write(struct.pack('<H', 1))   # Mono
            temp_file.write(struct.pack('<I', sample_rate))
            temp_file.write(struct.pack('<I', sample_rate * 2))  # Byte rate
            temp_file.write(struct.pack('<H', 2))   # Block align
            temp_file.write(struct.pack('<H', 16))  # Bits per sample
            temp_file.write(b'data')
            temp_file.write(struct.pack('<I', len(frames) * 2))
            
            # Write audio data
            for frame in frames:
                temp_file.write(frame)
        
        return temp_path
        
    except Exception as e:
        print(f"Error creating realistic audio: {e}")
        return None

def test_real_transcription():
    """Test transcription with a realistic audio file"""
    print("🎯 Testing Real Audio Transcription")
    print("=" * 50)
    
    # Create session
    session = requests.Session()
    
    # Register user
    unique_id = uuid.uuid4().hex[:8]
    user_data = {
        "email": f"real_audio_test_{unique_id}@example.com",
        "username": f"realaudiotest{unique_id}",
        "password": "TestPassword123",
        "first_name": "Real",
        "last_name": "AudioTester"
    }
    
    try:
        # Register
        response = session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Registration failed: {response.status_code}")
            return
        
        data = response.json()
        auth_token = data["access_token"]
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        print(f"✅ User registered: {user_data['email']}")
        
        # Create realistic audio file
        audio_path = create_realistic_audio_file()
        if not audio_path:
            print("❌ Failed to create audio file")
            return
        
        print(f"✅ Created realistic audio file: {os.path.getsize(audio_path)} bytes")
        
        # Upload audio file
        with open(audio_path, 'rb') as audio_file:
            files = {
                'file': ('realistic_audio.wav', audio_file, 'audio/wav')
            }
            data = {
                'title': 'Real Audio Transcription Test'
            }
            
            response = session.post(f"{BACKEND_URL}/upload-file", files=files, data=data, timeout=30)
            
        # Clean up temp file
        os.unlink(audio_path)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}: {response.text}")
            return
        
        result = response.json()
        note_id = result.get("id")
        print(f"✅ Audio uploaded: {note_id}")
        
        # Wait for processing
        print("⏳ Waiting for transcription processing...")
        max_checks = 30
        for check in range(max_checks):
            time.sleep(2)
            
            response = session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
            if response.status_code == 200:
                note_data = response.json()
                status = note_data.get("status", "unknown")
                artifacts = note_data.get("artifacts", {})
                
                print(f"Status check {check + 1}: {status}")
                
                if status == "ready":
                    transcript = artifacts.get("transcript", "")
                    print(f"✅ Transcription completed!")
                    print(f"📝 Transcript: '{transcript}'")
                    print(f"📊 Artifacts: {artifacts}")
                    
                    # Check if we got meaningful output
                    if transcript and len(transcript.strip()) > 0:
                        print("✅ Transcription system is working correctly!")
                    else:
                        print("⚠️ Transcription completed but empty (expected for tone-based audio)")
                    return
                    
                elif status == "failed":
                    error_msg = artifacts.get("error", "Unknown error")
                    print(f"❌ Transcription failed: {error_msg}")
                    
                    # Check if error message is descriptive (bug fix verification)
                    if len(error_msg) > 20:
                        print("✅ Error message is descriptive (bug fix working)")
                    else:
                        print("⚠️ Error message could be more descriptive")
                    return
                    
                elif status in ["processing", "uploading"]:
                    continue
                else:
                    print(f"❌ Unexpected status: {status}")
                    return
            else:
                print(f"❌ Cannot check status: {response.status_code}")
                return
        
        print("⏳ Transcription still processing after maximum wait time")
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")

if __name__ == "__main__":
    test_real_transcription()