#!/usr/bin/env python3
"""
Debug specific live transcription session m0uevvygg
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://audio-chunk-wizard.preview.emergentagent.com/api"
SESSION_ID = "m0uevvygg"

def debug_session():
    """Debug the specific session m0uevvygg"""
    session = requests.Session()
    
    print(f"🔍 DEBUGGING LIVE TRANSCRIPTION SESSION: {SESSION_ID}")
    print("=" * 60)
    
    # First, we need to authenticate to access the session
    print("0. Authenticating...")
    try:
        # Register a test user
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "email": f"debuguser_{unique_id}@example.com",
            "username": f"debuguser{unique_id}",
            "password": "DebugPassword123",
            "first_name": "Debug",
            "last_name": "User"
        }
        
        response = session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data["access_token"]
            session.headers.update({"Authorization": f"Bearer {auth_token}"})
            print(f"   ✅ Authenticated successfully")
        else:
            print(f"   ❌ Authentication failed: HTTP {response.status_code}")
            return
            
    except Exception as e:
        print(f"   ❌ Authentication error: {str(e)}")
        return
    
    # 1. Check Session State in Redis via live transcript endpoint
    print("\n1. Checking Session State in Redis...")
    try:
        response = session.get(f"{BACKEND_URL}/live/sessions/{SESSION_ID}/live", timeout=10)
        
        if response.status_code == 200:
            live_data = response.json()
            transcript = live_data.get("transcript", {})
            committed_words = transcript.get("committed_words", 0)
            tail_words = transcript.get("tail_words", 0)
            
            print(f"   ✅ Session found in Redis")
            print(f"   📊 Committed words: {committed_words}")
            print(f"   📊 Tail words: {tail_words}")
            print(f"   📊 Is active: {live_data.get('is_active', False)}")
            print(f"   📊 Full transcript: {transcript.get('text', 'No text')[:100]}...")
            
            if committed_words == 0 and tail_words == 0:
                print(f"   ⚠️  WARNING: No words in transcript - transcription may not be working")
            
        elif response.status_code == 404:
            print(f"   ❌ Session {SESSION_ID} not found in Redis")
            
        elif response.status_code == 403:
            print(f"   ❌ Access denied to session {SESSION_ID}")
            print(f"   💡 This means the session belongs to a different user")
            
        else:
            print(f"   ❌ Unexpected response: HTTP {response.status_code}")
            print(f"   📋 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error checking session state: {str(e)}")
    
    # 2. Test Session Events
    print("\n2. Checking Session Events...")
    try:
        response = session.get(f"{BACKEND_URL}/live/sessions/{SESSION_ID}/events", timeout=10)
        
        if response.status_code == 200:
            events_data = response.json()
            events = events_data.get("events", [])
            event_count = len(events)
            
            print(f"   ✅ Events endpoint accessible")
            print(f"   📊 Event count: {event_count}")
            
            if event_count == 0:
                print(f"   ⚠️  WARNING: No events found - transcription pipeline may not be processing")
            else:
                print(f"   📝 Recent events:")
                for i, event in enumerate(events[-3:]):  # Show last 3 events
                    event_type = event.get("type", "unknown")
                    timestamp = event.get("timestamp", 0)
                    content = event.get("content", {})
                    print(f"      {i+1}. Type: {event_type}, Time: {timestamp}, Content: {str(content)[:50]}...")
            
        elif response.status_code == 404:
            print(f"   ❌ Session {SESSION_ID} not found for events")
            
        elif response.status_code == 403:
            print(f"   ❌ Access denied to session events")
            print(f"   💡 Session belongs to a different user")
            
        else:
            print(f"   ❌ Unexpected response: HTTP {response.status_code}")
            print(f"   📋 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error checking session events: {str(e)}")
    
    # 3. Check System Health
    print("\n3. Checking System Health...")
    try:
        response = session.get(f"{BACKEND_URL}/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            services = health_data.get("services", {})
            pipeline_health = services.get("pipeline", "unknown")
            cache_health = services.get("cache", "unknown")
            
            print(f"   📊 Pipeline health: {pipeline_health}")
            print(f"   📊 Redis/Cache health: {cache_health}")
            
            if pipeline_health == "healthy":
                print(f"   ✅ Pipeline is healthy")
            elif pipeline_health == "degraded":
                print(f"   ⚠️  Pipeline is degraded")
            else:
                print(f"   ❌ Pipeline health issue: {pipeline_health}")
                
            if cache_health not in ["healthy", "disabled"]:
                print(f"   ⚠️  Redis/Cache issue may affect live transcription")
                
        else:
            print(f"   ❌ Cannot check system health: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error checking system health: {str(e)}")
    
    # 4. Summary and Recommendations
    print(f"\n📋 DEBUGGING SUMMARY FOR SESSION {SESSION_ID}:")
    print("=" * 60)
    print("💡 Key Findings:")
    print("   - If session returns 403/404: Session belongs to different user or doesn't exist")
    print("   - If session exists but no words: Chunks not being processed or transcription failing")
    print("   - If no events: Pipeline not generating events for this session")
    print("   - Check if user is still actively recording and sending chunks")
    print("\n💡 Recommended Actions:")
    print("   1. Verify the session ID is correct")
    print("   2. Check if the user is still connected and recording")
    print("   3. Verify chunks are being uploaded to the session")
    print("   4. Check if transcription service is working for new chunks")
    print("   5. Monitor Redis for session data persistence")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    debug_session()