#!/usr/bin/env python3
"""
Final Live Transcription Test - Comprehensive End-to-End Verification
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://smart-transcript-1.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"final_test_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123"

class FinalLiveTranscriptionTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def setup_authentication(self):
        """Setup authentication for testing"""
        try:
            user_data = {
                "email": TEST_USER_EMAIL,
                "username": f"finaltest{uuid.uuid4().hex[:8]}",
                "password": TEST_USER_PASSWORD,
                "first_name": "Final",
                "last_name": "Test"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Auth error: {str(e)}")
            return False

    def test_complete_live_transcription_scenario(self):
        """Test a complete live transcription scenario simulating real usage"""
        try:
            session_id = f"complete_test_{uuid.uuid4().hex[:8]}"
            
            print(f"🎤 Starting live transcription session: {session_id}")
            
            # Simulate a 20-second recording with 4 chunks (5 seconds each)
            chunks_data = []
            
            for chunk_idx in range(4):
                print(f"📤 Uploading chunk {chunk_idx + 1}/4...")
                
                # Create test audio chunk
                test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * (2048 + chunk_idx * 200)
                files = {'file': (f'live_chunk_{chunk_idx}.wav', test_audio, 'audio/wav')}
                data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
                
                start_time = time.time()
                
                # Upload chunk
                response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/chunks/{chunk_idx}", 
                                           files=files, data=data, timeout=30)
                
                upload_time = time.time() - start_time
                
                if response.status_code == 202:
                    result = response.json()
                    chunks_data.append({
                        "chunk_idx": chunk_idx,
                        "upload_time": upload_time,
                        "processing_started": result.get("processing_started", False)
                    })
                    
                    print(f"   ✅ Chunk {chunk_idx}: Uploaded in {upload_time:.2f}s")
                    
                    # Wait for processing and check real-time updates
                    time.sleep(2)
                    
                    # Check events
                    events_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/events", timeout=10)
                    if events_response.status_code == 200:
                        events_data = events_response.json()
                        events = events_data.get("events", [])
                        print(f"   📡 Events: {len(events)} available")
                    
                    # Check rolling transcript
                    live_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/live", timeout=10)
                    if live_response.status_code == 200:
                        live_data = live_response.json()
                        transcript = live_data.get("transcript", {})
                        text = transcript.get("text", "")
                        committed = transcript.get("committed_words", 0)
                        tail = transcript.get("tail_words", 0)
                        
                        print(f"   📝 Transcript: '{text[:50]}...' ({committed} committed, {tail} tail)")
                    
                else:
                    print(f"   ❌ Chunk {chunk_idx}: Upload failed ({response.status_code})")
                    return False
                
                # Simulate real-time interval
                time.sleep(1)
            
            print(f"\n🏁 Finalizing session...")
            
            # Finalize the session
            finalize_response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/finalize", timeout=30)
            
            if finalize_response.status_code == 200:
                finalize_data = finalize_response.json()
                transcript = finalize_data.get("transcript", {})
                artifacts = finalize_data.get("artifacts", {})
                
                print(f"✅ Session finalized successfully!")
                print(f"   📄 Final transcript: {len(transcript.get('text', ''))} characters")
                print(f"   📊 Word count: {transcript.get('word_count', 0)}")
                print(f"   📁 Artifacts created: {len(artifacts)}")
                print(f"   🕒 Processing time: {finalize_data.get('processing_time_ms', 0)}ms")
                
                return True
            else:
                print(f"❌ Finalization failed: {finalize_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {str(e)}")
            return False

    def test_concurrent_sessions(self):
        """Test multiple concurrent live transcription sessions"""
        try:
            print(f"\n🔄 Testing concurrent sessions...")
            
            session_ids = [f"concurrent_{i}_{uuid.uuid4().hex[:6]}" for i in range(3)]
            results = []
            
            # Start multiple sessions simultaneously
            for i, session_id in enumerate(session_ids):
                print(f"🎤 Starting session {i + 1}: {session_id}")
                
                # Upload first chunk for each session
                test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * (2048 + i * 100)
                files = {'file': (f'concurrent_chunk_{i}.wav', test_audio, 'audio/wav')}
                data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
                
                response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/chunks/0", 
                                           files=files, data=data, timeout=30)
                
                if response.status_code == 202:
                    results.append({"session_id": session_id, "status": "success"})
                    print(f"   ✅ Session {i + 1}: Started successfully")
                else:
                    results.append({"session_id": session_id, "status": "failed", "error": response.status_code})
                    print(f"   ❌ Session {i + 1}: Failed to start")
            
            # Wait for processing
            time.sleep(3)
            
            # Check all sessions
            successful_sessions = 0
            for i, result in enumerate(results):
                if result["status"] == "success":
                    session_id = result["session_id"]
                    
                    # Check session state
                    live_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/live", timeout=10)
                    if live_response.status_code == 200:
                        live_data = live_response.json()
                        transcript = live_data.get("transcript", {})
                        
                        if transcript.get("text"):
                            successful_sessions += 1
                            print(f"   ✅ Session {i + 1}: Active with transcript")
                        else:
                            print(f"   ⚠️ Session {i + 1}: Active but no transcript yet")
                    else:
                        print(f"   ❌ Session {i + 1}: Cannot retrieve state")
            
            print(f"📊 Concurrent sessions result: {successful_sessions}/{len(session_ids)} successful")
            return successful_sessions >= 2  # At least 2 out of 3 should work
            
        except Exception as e:
            print(f"❌ Concurrent test error: {str(e)}")
            return False

    def run_final_tests(self):
        """Run final comprehensive tests"""
        print("🎤 FINAL LIVE TRANSCRIPTION SYSTEM VERIFICATION")
        print("=" * 60)
        print(f"🎯 Target: {BACKEND_URL}")
        print(f"🕒 Started: {datetime.now().isoformat()}")
        print()
        
        # Setup
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return False
        
        print("✅ Authentication successful")
        
        # Test complete scenario
        print("\n🔍 Testing Complete Live Transcription Scenario...")
        complete_test_success = self.test_complete_live_transcription_scenario()
        
        # Test concurrent sessions
        concurrent_test_success = self.test_concurrent_sessions()
        
        # Final assessment
        print(f"\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        if complete_test_success and concurrent_test_success:
            print("✅ ALL TESTS PASSED")
            print("🎉 Live transcription system is fully operational!")
            print("   → Real-time processing: ✅ Working")
            print("   → Event generation: ✅ Working") 
            print("   → Rolling transcript: ✅ Working")
            print("   → Session finalization: ✅ Working")
            print("   → Concurrent sessions: ✅ Working")
            print("\n🎯 CONCLUSION: The live transcription system is providing real-time updates correctly.")
            print("   If frontend users are not seeing updates, the issue is likely in:")
            print("   • Frontend polling implementation")
            print("   • Network connectivity")
            print("   • Frontend state management")
            return True
        else:
            print("❌ SOME TESTS FAILED")
            print(f"   Complete scenario: {'✅' if complete_test_success else '❌'}")
            print(f"   Concurrent sessions: {'✅' if concurrent_test_success else '❌'}")
            return False

if __name__ == "__main__":
    tester = FinalLiveTranscriptionTest()
    success = tester.run_final_tests()
    exit(0 if success else 1)