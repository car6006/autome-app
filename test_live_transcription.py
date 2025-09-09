#!/usr/bin/env python3
"""
Focused Live Transcription System Test
Tests the fixed live transcription endpoints with simulated Emergent transcription
"""

import requests
import json
import time
import uuid

# Configuration
BACKEND_URL = "https://content-capture.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"livetest_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123"

def register_and_login():
    """Register a test user and get auth token"""
    session = requests.Session()
    
    # Register user
    user_data = {
        "email": TEST_USER_EMAIL,
        "username": f"livetest{uuid.uuid4().hex[:8]}",
        "password": TEST_USER_PASSWORD,
        "first_name": "Live",
        "last_name": "Test"
    }
    
    response = session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
    if response.status_code == 200:
        data = response.json()
        auth_token = data["access_token"]
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        print(f"✅ Registered and logged in as {TEST_USER_EMAIL}")
        return session, auth_token
    else:
        raise Exception(f"Registration failed: {response.status_code} - {response.text}")

def test_live_transcription_chunk_upload(session):
    """Test uploading audio chunks to live transcription endpoint"""
    print("\n🎤 Testing Live Transcription Chunk Upload...")
    
    session_id = str(uuid.uuid4())
    chunk_idx = 0
    
    # Create test audio content
    test_audio_content = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"test_audio_data" * 100
    
    files = {
        'file': (f'live_chunk_{chunk_idx}.wav', test_audio_content, 'audio/wav')
    }
    data = {
        'sample_rate': 16000,
        'codec': 'wav',
        'chunk_ms': 5000,
        'overlap_ms': 750
    }
    
    response = session.post(
        f"{BACKEND_URL}/live/sessions/{session_id}/chunks/{chunk_idx}",
        files=files,
        data=data,
        timeout=30
    )
    
    if response.status_code == 202:
        result = response.json()
        print(f"✅ Chunk uploaded successfully: {result}")
        return session_id
    else:
        print(f"❌ Chunk upload failed: HTTP {response.status_code} - {response.text}")
        return None

def test_live_transcription_events(session, session_id):
    """Test polling for real-time transcription events"""
    print(f"\n📡 Testing Live Transcription Events for session {session_id}...")
    
    # Wait for processing
    time.sleep(3)
    
    response = session.get(f"{BACKEND_URL}/live/sessions/{session_id}/events", timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        events = result.get("events", [])
        event_count = result.get("event_count", 0)
        print(f"✅ Retrieved {event_count} events: {[e.get('type') for e in events]}")
        return event_count > 0
    else:
        print(f"❌ Events polling failed: HTTP {response.status_code} - {response.text}")
        return False

def test_live_transcript_state(session, session_id):
    """Test getting current live transcript state"""
    print(f"\n📝 Testing Live Transcript State for session {session_id}...")
    
    response = session.get(f"{BACKEND_URL}/live/sessions/{session_id}/live", timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        transcript = result.get("transcript", {})
        text_length = len(transcript.get("text", ""))
        word_count = len(transcript.get("words", []))
        print(f"✅ Live transcript: {text_length} chars, {word_count} words")
        return True
    else:
        print(f"❌ Live transcript failed: HTTP {response.status_code} - {response.text}")
        return False

def test_session_finalization(session, session_id):
    """Test finalizing a live transcription session"""
    print(f"\n🏁 Testing Session Finalization for session {session_id}...")
    
    response = session.post(f"{BACKEND_URL}/live/sessions/{session_id}/finalize", timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        transcript = result.get("transcript", {})
        artifacts = result.get("artifacts", {})
        word_count = transcript.get("word_count", 0)
        artifact_count = len(artifacts)
        print(f"✅ Session finalized: {word_count} words, {artifact_count} artifacts")
        print(f"   Artifacts: {list(artifacts.keys())}")
        return True
    else:
        print(f"❌ Session finalization failed: HTTP {response.status_code} - {response.text}")
        return False

def test_multiple_chunks(session):
    """Test uploading multiple sequential chunks"""
    print("\n🔄 Testing Multiple Sequential Chunks...")
    
    session_id = str(uuid.uuid4())
    chunks_uploaded = 0
    
    for chunk_idx in range(3):
        test_audio_content = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + f"chunk_{chunk_idx}_data".encode() * 50
        
        files = {
            'file': (f'multi_chunk_{chunk_idx}.wav', test_audio_content, 'audio/wav')
        }
        data = {
            'sample_rate': 16000,
            'codec': 'wav',
            'chunk_ms': 5000,
            'overlap_ms': 750
        }
        
        response = session.post(
            f"{BACKEND_URL}/live/sessions/{session_id}/chunks/{chunk_idx}",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 202:
            chunks_uploaded += 1
            time.sleep(0.5)  # Simulate real-time streaming
        else:
            print(f"❌ Chunk {chunk_idx} upload failed: HTTP {response.status_code}")
            break
    
    print(f"✅ Uploaded {chunks_uploaded}/3 chunks successfully")
    return session_id if chunks_uploaded > 0 else None

def main():
    """Run focused live transcription tests"""
    print("🚀 Starting Focused Live Transcription System Tests")
    print("=" * 60)
    
    try:
        # Setup
        session, auth_token = register_and_login()
        
        # Test 1: Single chunk upload
        session_id = test_live_transcription_chunk_upload(session)
        if session_id:
            # Test 2: Events polling
            events_working = test_live_transcription_events(session, session_id)
            
            # Test 3: Live transcript state
            transcript_working = test_live_transcript_state(session, session_id)
            
            # Test 4: Session finalization
            finalization_working = test_session_finalization(session, session_id)
        
        # Test 5: Multiple chunks
        multi_session_id = test_multiple_chunks(session)
        if multi_session_id:
            # Wait and finalize multi-chunk session
            time.sleep(2)
            test_session_finalization(session, multi_session_id)
        
        print("\n" + "=" * 60)
        print("🎯 Live Transcription System Test Summary:")
        print(f"   ✅ Chunk Upload: {'Working' if session_id else 'Failed'}")
        print(f"   ✅ Events System: {'Working' if session_id and events_working else 'Failed'}")
        print(f"   ✅ Live Transcript: {'Working' if session_id and transcript_working else 'Failed'}")
        print(f"   ✅ Finalization: {'Working' if session_id and finalization_working else 'Failed'}")
        print(f"   ✅ Multiple Chunks: {'Working' if multi_session_id else 'Failed'}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()