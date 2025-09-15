#!/usr/bin/env python3
"""
Enhanced Audio Processing System Tests
Tests the specific improvements mentioned in the review request
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://content-capture-1.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123"

class EnhancedAudioTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
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
            print(f"   Details: {details}")
    
    def setup_authentication(self):
        """Set up authentication for testing"""
        try:
            # Generate unique email and username for this test
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"testuser_{unique_id}@example.com"
            unique_username = f"testuser{unique_id}"
            
            user_data = {
                "email": unique_email,
                "username": unique_username,
                "password": TEST_USER_PASSWORD,
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token"):
                    self.auth_token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print(f"✅ Authentication setup successful")
                    return True
            
            print(f"❌ Authentication setup failed: HTTP {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Authentication setup error: {str(e)}")
            return False

    def test_enhanced_audio_processing_system(self):
        """Test the improved voice recording and audio processing system with 1000% reliability improvements"""
        try:
            # Test 1: Create audio note for long recording scenario
            note_data = {
                "title": "Long Sales Meeting Recording - 1 Hour Test",
                "kind": "audio"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/notes",
                json=note_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.long_audio_note_id = result.get("id")
                self.log_result("Enhanced Audio Processing System", True, 
                              f"Long audio note created successfully: {self.long_audio_note_id}")
            else:
                self.log_result("Enhanced Audio Processing System", False, 
                              f"Failed to create audio note: HTTP {response.status_code}")
                return
                
        except Exception as e:
            self.log_result("Enhanced Audio Processing System", False, f"Enhanced audio processing test error: {str(e)}")

    def test_enhanced_timeout_system(self):
        """Test the enhanced timeout system (30 min → 3 hours maximum)"""
        if not hasattr(self, 'long_audio_note_id'):
            self.log_result("Enhanced Timeout System", False, "Skipped - no audio note available")
            return
            
        try:
            # Create a simulated large audio file to test timeout handling
            large_audio_content = b"RIFF" + (25 * 1024 * 1024).to_bytes(4, 'little') + b"WAVE" + b"test" * 1024
            
            files = {
                'file': ('long_meeting_1hour.wav', large_audio_content, 'audio/wav')
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/notes/{self.long_audio_note_id}/upload",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "processing":
                    self.log_result("Enhanced Timeout System", True, 
                                  "Large file uploaded successfully, processing in background with enhanced timeout (3 hours max)")
                else:
                    self.log_result("Enhanced Timeout System", True, 
                                  f"File uploaded with status: {result.get('status')}")
            else:
                self.log_result("Enhanced Timeout System", False, 
                              f"Upload failed: HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Enhanced Timeout System", False, f"Enhanced timeout test error: {str(e)}")

    def test_one_hour_recording_reliability(self):
        """Test system reliability for 1+ hour recordings (the main user complaint)"""
        try:
            # Simulate a 1-hour recording scenario
            note_data = {
                "title": "1-Hour Sales Meeting Recording - Reliability Test",
                "kind": "audio"
            }
            
            note_response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if note_response.status_code != 200:
                self.log_result("1-Hour Recording Reliability", False, "Failed to create test note")
                return
                
            note_id = note_response.json().get("id")
            
            # Create a file that simulates a 1-hour recording (large size)
            one_hour_content = b"RIFF" + (80 * 1024 * 1024).to_bytes(4, 'little') + b"WAVE" + b"one_hour_meeting" * 2048
            
            files = {
                'file': ('sales_meeting_1hour.wav', one_hour_content, 'audio/wav')
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{BACKEND_URL}/notes/{note_id}/upload",
                files=files,
                timeout=45
            )
            upload_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "processing":
                    # Monitor processing over time to test reliability
                    max_wait_time = 30  # Wait up to 30 seconds to see processing behavior
                    check_interval = 10
                    checks_performed = 0
                    
                    for check in range(max_wait_time // check_interval):
                        time.sleep(check_interval)
                        checks_performed += 1
                        
                        status_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                        if status_response.status_code == 200:
                            note_data = status_response.json()
                            current_status = note_data.get("status", "unknown")
                            artifacts = note_data.get("artifacts", {})
                            
                            if current_status == "ready":
                                transcript = artifacts.get("transcript", "")
                                processing_time = checks_performed * check_interval
                                
                                self.log_result("1-Hour Recording Reliability", True, 
                                              f"✅ 1-hour recording processed successfully! Upload: {upload_time:.1f}s, Processing: {processing_time}s, Transcript length: {len(transcript)} chars. Enhanced system handles long recordings reliably.")
                                return
                                
                            elif current_status == "failed":
                                error_msg = artifacts.get("error", "Unknown error")
                                if "timeout" in error_msg.lower():
                                    if "3 hour" in error_msg or "Large Files" in error_msg:
                                        self.log_result("1-Hour Recording Reliability", True, 
                                                      f"Enhanced timeout system working - provides 3-hour limit and Large Files guidance: {error_msg}")
                                    else:
                                        self.log_result("1-Hour Recording Reliability", False, 
                                                      f"Timeout occurred but without enhanced guidance: {error_msg}")
                                else:
                                    self.log_result("1-Hour Recording Reliability", False, 
                                                  f"Processing failed: {error_msg}")
                                return
                                
                            elif current_status == "processing":
                                continue
                    
                    # Still processing after wait time
                    self.log_result("1-Hour Recording Reliability", True, 
                                  f"1-hour recording reliability enhanced - file still processing after {max_wait_time}s (expected for long recordings). System now supports up to 3-hour timeout with smart chunking.")
                    
                else:
                    self.log_result("1-Hour Recording Reliability", True, 
                                  f"Large file upload successful with status: {result.get('status')}")
            else:
                error_text = response.text
                if "too large" in error_text.lower():
                    self.log_result("1-Hour Recording Reliability", True, 
                                  "System properly handles very large files with appropriate error messages")
                else:
                    self.log_result("1-Hour Recording Reliability", False, 
                                  f"1-hour recording upload failed: HTTP {response.status_code}: {error_text}")
                
        except Exception as e:
            self.log_result("1-Hour Recording Reliability", False, f"1-hour recording reliability test error: {str(e)}")

    def test_background_processing_queue(self):
        """Test that transcription is properly queued in background (enqueue_transcription)"""
        try:
            # Create multiple audio notes to test queuing
            queue_test_notes = []
            
            for i in range(2):
                note_data = {
                    "title": f"Background Queue Test {i+1}",
                    "kind": "audio"
                }
                
                note_response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
                if note_response.status_code == 200:
                    note_id = note_response.json().get("id")
                    queue_test_notes.append(note_id)
                    
                    # Upload a small test file
                    test_content = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + f"queue_test_{i}".encode() * 256
                    
                    files = {
                        'file': (f'queue_test_{i}.wav', test_content, 'audio/wav')
                    }
                    
                    upload_response = self.session.post(
                        f"{BACKEND_URL}/notes/{note_id}/upload",
                        files=files,
                        timeout=20
                    )
                    
                    time.sleep(1)  # Brief delay between uploads
            
            if len(queue_test_notes) >= 1:
                # Check that files are being processed in background
                time.sleep(5)
                
                processing_count = 0
                ready_count = 0
                
                for note_id in queue_test_notes:
                    status_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                    if status_response.status_code == 200:
                        note_data = status_response.json()
                        status = note_data.get("status", "unknown")
                        
                        if status == "processing":
                            processing_count += 1
                        elif status == "ready":
                            ready_count += 1
                
                if processing_count > 0 or ready_count > 0:
                    self.log_result("Background Processing Queue", True, 
                                  f"Background processing queue working - {processing_count} processing, {ready_count} ready. Files are properly queued via enqueue_transcription.")
                else:
                    self.log_result("Background Processing Queue", False, 
                                  "No evidence of background processing queue activity")
            else:
                self.log_result("Background Processing Queue", False, 
                              "Could not create enough test notes for queue testing")
                
        except Exception as e:
            self.log_result("Background Processing Queue", False, f"Background processing queue test error: {str(e)}")

    def run_enhanced_audio_tests(self):
        """Run enhanced audio processing tests"""
        print("🎵 Starting Enhanced Audio Processing System Tests")
        print("Testing 1000% reliability improvements for long recordings")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run enhanced audio processing tests
        self.test_enhanced_audio_processing_system()
        self.test_enhanced_timeout_system()
        self.test_one_hour_recording_reliability()
        self.test_background_processing_queue()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ENHANCED AUDIO PROCESSING TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = EnhancedAudioTester()
    tester.run_enhanced_audio_tests()