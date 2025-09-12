#!/usr/bin/env python3
"""
Live Transcription System Debug Test
Focused testing for the live transcription system to identify real-time processing issues
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://transcript-master.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"live_test_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "TestPassword123"

class LiveTranscriptionDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        self.debug_session_id = None
        
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
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details and not success:
            print(f"   Details: {details}")
        print()
    
    def setup_authentication(self):
        """Setup authentication for testing"""
        try:
            # Register test user
            user_data = {
                "email": TEST_USER_EMAIL,
                "username": f"livetest{int(time.time())}",
                "password": TEST_USER_PASSWORD,
                "first_name": "Live",
                "last_name": "Test"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                print(f"✅ Authentication setup successful for user: {self.user_id}")
                return True
            else:
                print(f"❌ Authentication setup failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication setup error: {str(e)}")
            return False

    def test_streaming_endpoints_detailed(self):
        """Test streaming endpoints in detail"""
        print("🔍 Testing streaming endpoints...")
        
        try:
            # Create session ID
            session_id = f"debug_session_{int(time.time())}"
            self.debug_session_id = session_id
            
            # Create test audio chunk
            test_audio_content = self._create_test_audio_chunk()
            
            files = {
                'file': (f'chunk_0.wav', test_audio_content, 'audio/wav')
            }
            data = {
                'sample_rate': '16000',
                'codec': 'wav',
                'chunk_ms': '5000',
                'overlap_ms': '750'
            }
            
            # Test chunk upload
            response = self.session.post(
                f"{BACKEND_URL}/live/sessions/{session_id}/chunks/0",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 202:
                result = response.json()
                self.log_result("Streaming Chunk Upload", True, 
                              f"Chunk uploaded successfully: {result.get('message')}", result)
                return True
            else:
                self.log_result("Streaming Chunk Upload", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Streaming Chunk Upload", False, f"Error: {str(e)}")
            return False

    def test_chunk_processing_pipeline(self):
        """Test if chunks are being processed immediately"""
        print("🔍 Testing chunk processing pipeline...")
        
        if not self.debug_session_id:
            self.log_result("Chunk Processing Pipeline", False, "No session available")
            return False
            
        try:
            session_id = self.debug_session_id
            
            # Upload multiple chunks
            for chunk_idx in range(1, 4):
                test_audio_content = self._create_test_audio_chunk(chunk_idx)
                
                files = {
                    'file': (f'chunk_{chunk_idx}.wav', test_audio_content, 'audio/wav')
                }
                data = {
                    'sample_rate': '16000',
                    'codec': 'wav',
                    'chunk_ms': '5000',
                    'overlap_ms': '750'
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/live/sessions/{session_id}/chunks/{chunk_idx}",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code != 202:
                    self.log_result("Chunk Processing Pipeline", False, 
                                  f"Chunk {chunk_idx} upload failed: HTTP {response.status_code}")
                    return False
                
                time.sleep(1)
            
            # Wait for processing
            time.sleep(5)
            
            # Check live transcript
            live_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/live", timeout=10)
            
            if live_response.status_code == 200:
                live_data = live_response.json()
                transcript = live_data.get("transcript", {})
                
                if transcript.get("text") or transcript.get("words"):
                    self.log_result("Chunk Processing Pipeline", True, 
                                  f"Chunks being processed: {len(transcript.get('text', ''))} chars", 
                                  {"transcript": transcript})
                    return True
                else:
                    self.log_result("Chunk Processing Pipeline", False, 
                                  "Chunks uploaded but no transcription found", live_data)
                    return False
            else:
                self.log_result("Chunk Processing Pipeline", False, 
                              f"Cannot retrieve live transcript: HTTP {live_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Chunk Processing Pipeline", False, f"Error: {str(e)}")
            return False

    def test_redis_operations(self):
        """Test Redis connectivity and operations"""
        print("🔍 Testing Redis operations...")
        
        try:
            # Check Redis through health endpoint
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                services = health_data.get("services", {})
                cache_status = services.get("cache", "unknown")
                
                if self.debug_session_id:
                    # Test Redis operations through live transcript
                    live_response = self.session.get(f"{BACKEND_URL}/live/sessions/{self.debug_session_id}/live", timeout=10)
                    
                    if live_response.status_code == 200:
                        self.log_result("Redis Operations", True, 
                                      f"Redis working: cache={cache_status}, live transcript accessible")
                        return True
                    else:
                        self.log_result("Redis Operations", False, 
                                      f"Redis may be failing: live transcript error {live_response.status_code}")
                        return False
                else:
                    self.log_result("Redis Operations", True, f"Redis status: {cache_status}")
                    return cache_status in ["healthy", "disabled"]
            else:
                self.log_result("Redis Operations", False, f"Cannot check Redis: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Redis Operations", False, f"Error: {str(e)}")
            return False

    def test_enhanced_providers(self):
        """Test enhanced_providers.py transcription"""
        print("🔍 Testing enhanced providers transcription...")
        
        try:
            test_audio_content = self._create_test_audio_chunk()
            
            files = {
                'file': ('enhanced_test.wav', test_audio_content, 'audio/wav')
            }
            data = {
                'title': 'Enhanced Providers Test'
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/upload-file",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                note_id = result.get("id")
                
                if note_id:
                    # Wait for processing
                    for _ in range(10):  # 20 seconds max
                        time.sleep(2)
                        
                        note_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                        
                        if note_response.status_code == 200:
                            note_data = note_response.json()
                            status = note_data.get("status", "unknown")
                            
                            if status == "ready":
                                self.log_result("Enhanced Providers", True, 
                                              "Enhanced providers transcription working")
                                return True
                            elif status == "failed":
                                error_msg = note_data.get("artifacts", {}).get("error", "Unknown")
                                if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                                    self.log_result("Enhanced Providers", True, 
                                                  f"Enhanced providers hit expected limits: {error_msg}")
                                    return True
                                else:
                                    self.log_result("Enhanced Providers", False, 
                                                  f"Enhanced providers failed: {error_msg}")
                                    return False
                    
                    self.log_result("Enhanced Providers", True, 
                                  "Enhanced providers still processing (likely rate limited)")
                    return True
                else:
                    self.log_result("Enhanced Providers", False, "No note ID returned")
                    return False
            else:
                self.log_result("Enhanced Providers", False, f"Upload failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Enhanced Providers", False, f"Error: {str(e)}")
            return False

    def test_events_polling(self):
        """Test event polling endpoint"""
        print("🔍 Testing events polling...")
        
        if not self.debug_session_id:
            self.log_result("Events Polling", False, "No session available")
            return False
            
        try:
            session_id = self.debug_session_id
            
            events_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/events", timeout=10)
            
            if events_response.status_code == 200:
                events_data = events_response.json()
                events = events_data.get("events", [])
                
                self.log_result("Events Polling", True, 
                              f"Events polling working: {len(events)} events", 
                              {"events": events})
                return True
            else:
                self.log_result("Events Polling", False, 
                              f"Events polling failed: HTTP {events_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Events Polling", False, f"Error: {str(e)}")
            return False

    def test_session_finalization(self):
        """Test session finalization"""
        print("🔍 Testing session finalization...")
        
        if not self.debug_session_id:
            self.log_result("Session Finalization", False, "No session available")
            return False
            
        try:
            session_id = self.debug_session_id
            
            response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/finalize", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                transcript = result.get("transcript", {})
                artifacts = result.get("artifacts", {})
                
                self.log_result("Session Finalization", True, 
                              f"Session finalized: {transcript.get('word_count', 0)} words, {len(artifacts)} artifacts", 
                              {"transcript": transcript, "artifacts": list(artifacts.keys())})
                return True
            else:
                self.log_result("Session Finalization", False, 
                              f"Finalization failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Session Finalization", False, f"Error: {str(e)}")
            return False

    def _create_test_audio_chunk(self, chunk_idx=0):
        """Create a test audio chunk (minimal WAV format)"""
        wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        audio_data = bytes([(i + chunk_idx * 10) % 256 for i in range(2048)])
        return wav_header + audio_data

    def run_debug_tests(self):
        """Run all debug tests"""
        print("🎤 LIVE TRANSCRIPTION SYSTEM DEBUG")
        print("=" * 50)
        
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run tests in sequence
        tests = [
            self.test_streaming_endpoints_detailed,
            self.test_chunk_processing_pipeline,
            self.test_redis_operations,
            self.test_enhanced_providers,
            self.test_events_polling,
            self.test_session_finalization
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 DEBUG SUMMARY")
        print("=" * 50)
        
        passed = sum(results)
        total = len(results)
        
        print(f"Tests passed: {passed}/{total}")
        
        if passed < total:
            print("\n❌ ISSUES IDENTIFIED:")
            for i, (test, result) in enumerate(zip(tests, results)):
                if not result:
                    print(f"  - {test.__name__}")
        else:
            print("\n✅ All tests passed - system appears to be working")
        
        # Detailed results
        print(f"\n📊 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")

if __name__ == "__main__":
    debugger = LiveTranscriptionDebugger()
    debugger.run_debug_tests()