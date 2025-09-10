#!/usr/bin/env python3
"""
Live Transcription Debug Script
Focused testing of the live transcription system to debug real-time update issues
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://smart-transcript-1.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"livetestuser_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123"

class LiveTranscriptionDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def setup_authentication(self):
        """Setup authentication for testing"""
        try:
            # Register test user
            user_data = {
                "email": TEST_USER_EMAIL,
                "username": f"livetest{uuid.uuid4().hex[:8]}",
                "password": TEST_USER_PASSWORD,
                "first_name": "Live",
                "last_name": "Test"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("Authentication Setup", True, f"User registered: {self.user_id}")
                return True
            else:
                self.log_result("Authentication Setup", False, f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Auth error: {str(e)}")
            return False

    def test_redis_connectivity(self):
        """Test Redis connectivity through health endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", {})
                cache_status = services.get("cache", "unknown")
                
                if cache_status == "healthy":
                    self.log_result("Redis Connectivity", True, "Redis is healthy and accessible")
                else:
                    self.log_result("Redis Connectivity", False, f"Redis status: {cache_status}", data)
            else:
                self.log_result("Redis Connectivity", False, f"Health check failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Redis Connectivity", False, f"Redis test error: {str(e)}")

    def test_chunk_upload_and_processing(self):
        """Test chunk upload and immediate processing"""
        try:
            session_id = f"debug_session_{uuid.uuid4().hex[:8]}"
            
            # Create test audio chunk
            test_audio_content = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * 2048
            
            files = {
                'file': ('chunk_0.wav', test_audio_content, 'audio/wav')
            }
            data = {
                'sample_rate': '16000',
                'codec': 'wav',
                'chunk_ms': '5000',
                'overlap_ms': '750'
            }
            
            start_time = time.time()
            
            # Upload chunk
            response = self.session.post(
                f"{BACKEND_URL}/live/sessions/{session_id}/chunks/0",
                files=files,
                data=data,
                timeout=30
            )
            
            upload_time = time.time() - start_time
            
            if response.status_code == 202:
                result = response.json()
                processing_started = result.get("processing_started", False)
                
                if processing_started:
                    self.log_result("Chunk Upload and Processing", True, 
                                  f"Chunk uploaded and processing started in {upload_time:.2f}s", 
                                  {"session_id": session_id, "response": result})
                    return session_id
                else:
                    self.log_result("Chunk Upload and Processing", False, 
                                  "Chunk uploaded but processing not started", result)
            else:
                self.log_result("Chunk Upload and Processing", False, 
                              f"Upload failed: HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Chunk Upload and Processing", False, f"Upload error: {str(e)}")
        
        return None

    def test_real_time_event_generation(self, session_id):
        """Test if events are generated in real-time after chunk processing"""
        if not session_id:
            self.log_result("Real-time Event Generation", False, "No session ID available")
            return
            
        try:
            # Wait for processing to complete
            print(f"⏳ Waiting for chunk processing to generate events...")
            
            event_found = False
            max_polls = 10
            
            for poll in range(max_polls):
                time.sleep(1)  # Wait 1 second between polls
                
                response = self.session.get(
                    f"{BACKEND_URL}/live/sessions/{session_id}/events",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])
                    
                    print(f"   Poll {poll + 1}: Found {len(events)} events")
                    
                    if events:
                        # Check event types
                        partial_events = [e for e in events if e.get("type") == "partial"]
                        commit_events = [e for e in events if e.get("type") == "commit"]
                        
                        self.log_result("Real-time Event Generation", True, 
                                      f"Events generated after {poll + 1} seconds: {len(partial_events)} partial, {len(commit_events)} commit", 
                                      {"events": events})
                        event_found = True
                        break
                elif response.status_code == 403:
                    self.log_result("Real-time Event Generation", False, 
                                  "Access denied to session events")
                    break
                elif response.status_code == 404:
                    print(f"   Poll {poll + 1}: Session not found yet")
                else:
                    print(f"   Poll {poll + 1}: HTTP {response.status_code}")
            
            if not event_found:
                self.log_result("Real-time Event Generation", False, 
                              f"No events generated after {max_polls} seconds of polling")
                
        except Exception as e:
            self.log_result("Real-time Event Generation", False, f"Event polling error: {str(e)}")

    def test_rolling_transcript_state(self, session_id):
        """Test Redis rolling transcript state"""
        if not session_id:
            self.log_result("Rolling Transcript State", False, "No session ID available")
            return
            
        try:
            # Wait for processing
            time.sleep(3)
            
            response = self.session.get(
                f"{BACKEND_URL}/live/sessions/{session_id}/live",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                transcript = data.get("transcript", {})
                
                if transcript:
                    text = transcript.get("text", "")
                    committed_words = transcript.get("committed_words", 0)
                    tail_words = transcript.get("tail_words", 0)
                    
                    if text or committed_words > 0 or tail_words > 0:
                        self.log_result("Rolling Transcript State", True, 
                                      f"Rolling state active: '{text[:50]}...' ({committed_words} committed, {tail_words} tail)", 
                                      transcript)
                    else:
                        self.log_result("Rolling Transcript State", False, 
                                      "Rolling state exists but empty", transcript)
                else:
                    self.log_result("Rolling Transcript State", False, 
                                  "No transcript data in rolling state", data)
            elif response.status_code == 404:
                self.log_result("Rolling Transcript State", False, 
                              "Session not found - rolling state not created")
            else:
                self.log_result("Rolling Transcript State", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Rolling Transcript State", False, f"Rolling state error: {str(e)}")

    def test_session_finalization(self, session_id):
        """Test session finalization pipeline"""
        if not session_id:
            self.log_result("Session Finalization", False, "No session ID available")
            return
            
        try:
            # Wait for processing to complete
            time.sleep(5)
            
            response = self.session.post(
                f"{BACKEND_URL}/live/sessions/{session_id}/finalize",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                transcript = data.get("transcript", {})
                artifacts = data.get("artifacts", {})
                
                if transcript and transcript.get("text"):
                    text_length = len(transcript["text"])
                    word_count = transcript.get("word_count", 0)
                    artifact_count = len(artifacts)
                    
                    self.log_result("Session Finalization", True, 
                                  f"Session finalized: {text_length} chars, {word_count} words, {artifact_count} artifacts", 
                                  {"transcript_preview": transcript["text"][:100], "artifacts": list(artifacts.keys())})
                else:
                    self.log_result("Session Finalization", False, 
                                  "Finalization succeeded but no transcript generated", data)
            elif response.status_code == 404:
                self.log_result("Session Finalization", False, 
                              "Session not found for finalization")
            else:
                self.log_result("Session Finalization", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Session Finalization", False, f"Finalization error: {str(e)}")

    def test_multiple_chunks_flow(self):
        """Test multiple chunks to verify real-time processing pipeline"""
        try:
            session_id = f"multi_chunk_{uuid.uuid4().hex[:8]}"
            
            chunk_results = []
            
            # Upload 3 chunks sequentially
            for chunk_idx in range(3):
                print(f"📤 Uploading chunk {chunk_idx}...")
                
                # Create slightly different audio content for each chunk
                test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * (2048 + chunk_idx * 100)
                
                files = {'file': (f'chunk_{chunk_idx}.wav', test_audio, 'audio/wav')}
                data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
                
                start_time = time.time()
                response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/chunks/{chunk_idx}", 
                                           files=files, data=data, timeout=30)
                upload_time = time.time() - start_time
                
                if response.status_code == 202:
                    result = response.json()
                    chunk_results.append({
                        "chunk_idx": chunk_idx,
                        "upload_time": upload_time,
                        "processing_started": result.get("processing_started", False)
                    })
                    
                    # Wait briefly and check for events
                    time.sleep(2)
                    
                    events_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/events", timeout=10)
                    if events_response.status_code == 200:
                        events_data = events_response.json()
                        events = events_data.get("events", [])
                        chunk_results[-1]["events_after_upload"] = len(events)
                        print(f"   ✅ Chunk {chunk_idx}: {len(events)} events generated")
                    else:
                        chunk_results[-1]["events_error"] = events_response.status_code
                        print(f"   ⚠️ Chunk {chunk_idx}: Events check failed ({events_response.status_code})")
                else:
                    chunk_results.append({
                        "chunk_idx": chunk_idx,
                        "error": f"HTTP {response.status_code}"
                    })
                    print(f"   ❌ Chunk {chunk_idx}: Upload failed")
                
                time.sleep(1)  # Simulate real-time interval
            
            # Evaluate results
            successful_chunks = [r for r in chunk_results if r.get("processing_started")]
            chunks_with_events = [r for r in chunk_results if r.get("events_after_upload", 0) > 0]
            
            if len(successful_chunks) >= 2 and len(chunks_with_events) >= 1:
                self.log_result("Multiple Chunks Flow", True, 
                              f"Multi-chunk flow working: {len(successful_chunks)} uploaded, {len(chunks_with_events)} generated events", 
                              {"chunk_results": chunk_results})
                return session_id
            else:
                self.log_result("Multiple Chunks Flow", False, 
                              f"Multi-chunk flow issues: {len(successful_chunks)} uploaded, {len(chunks_with_events)} with events", 
                              {"chunk_results": chunk_results})
                
        except Exception as e:
            self.log_result("Multiple Chunks Flow", False, f"Multi-chunk flow error: {str(e)}")
        
        return None

    def run_debug_tests(self):
        """Run focused live transcription debug tests"""
        print("🎤 LIVE TRANSCRIPTION DEBUG TESTS")
        print("=" * 50)
        print(f"🎯 Target: {BACKEND_URL}")
        print(f"🕒 Started: {datetime.now().isoformat()}")
        print()
        
        # Setup
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Core infrastructure tests
        print("🔍 Testing Core Infrastructure...")
        self.test_redis_connectivity()
        
        # Single chunk flow
        print("\n🔍 Testing Single Chunk Flow...")
        session_id = self.test_chunk_upload_and_processing()
        
        if session_id:
            self.test_real_time_event_generation(session_id)
            self.test_rolling_transcript_state(session_id)
            self.test_session_finalization(session_id)
        
        # Multi-chunk flow
        print("\n🔍 Testing Multi-Chunk Flow...")
        multi_session_id = self.test_multiple_chunks_flow()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 DEBUG TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {len(self.test_results)}")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        # Key findings
        print("\n🎯 KEY FINDINGS:")
        
        # Check for specific issues
        redis_test = next((r for r in self.test_results if "Redis" in r["test"]), None)
        if redis_test and not redis_test["success"]:
            print("   🚨 CRITICAL: Redis connectivity issues detected")
        
        event_test = next((r for r in self.test_results if "Event Generation" in r["test"]), None)
        if event_test and not event_test["success"]:
            print("   🚨 CRITICAL: Real-time event generation not working")
        
        processing_test = next((r for r in self.test_results if "Processing" in r["test"]), None)
        if processing_test and not processing_test["success"]:
            print("   🚨 CRITICAL: Chunk processing pipeline issues")
        
        if passed == len(self.test_results):
            print("   ✅ All systems operational - live transcription working correctly")
        
        print(f"\n🕒 Completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    debugger = LiveTranscriptionDebugger()
    debugger.run_debug_tests()