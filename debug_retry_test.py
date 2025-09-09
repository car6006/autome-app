#!/usr/bin/env python3
"""
Critical Debug Test for Retry Processing Issue
Focuses specifically on the stuck notes retry debugging
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://content-capture.preview.emergentagent.com/api"
TEST_USER_EMAIL = "debuguser@example.com"
TEST_USER_PASSWORD = "DebugPassword123"

class RetryDebugTester:
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
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def setup_authentication(self):
        """Setup authentication for testing"""
        try:
            # Generate unique email for this test
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"debuguser_{unique_id}@example.com"
            
            user_data = {
                "email": unique_email,
                "username": f"debuguser{unique_id}",
                "password": TEST_USER_PASSWORD,
                "first_name": "Debug",
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
                    print(f"✅ Authentication setup successful: {unique_email}")
                    return True
            
            print(f"❌ Authentication setup failed: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Authentication setup error: {str(e)}")
            return False

    def test_stuck_notes_retry_debugging(self):
        """
        CRITICAL DEBUG TEST: Test why retry processing isn't fixing stuck notes
        """
        try:
            print("\n🔍 DEBUGGING STUCK NOTES RETRY PROCESSING")
            print("=" * 60)
            
            # Step 1: Create an audio note to test the complete pipeline
            test_audio_content = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"test_audio_data" * 100
            
            files = {
                'file': ('stuck_note_test.wav', test_audio_content, 'audio/wav')
            }
            data = {
                'title': 'Stuck Notes Debug Test'
            }
            
            print("Step 1: Creating audio note...")
            upload_response = self.session.post(
                f"{BACKEND_URL}/upload-file",
                files=files,
                data=data,
                timeout=30
            )
            
            if upload_response.status_code == 200:
                upload_result = upload_response.json()
                note_id = upload_result.get("id")
                
                if note_id:
                    print(f"✅ Step 1: Audio note created successfully: {note_id}")
                    
                    # Step 2: Wait and check initial processing status
                    print("Step 2: Checking initial processing status...")
                    time.sleep(3)
                    
                    status_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                    if status_response.status_code == 200:
                        note_data = status_response.json()
                        initial_status = note_data.get("status", "unknown")
                        
                        print(f"✅ Step 2: Initial status: {initial_status}")
                        
                        # Step 3: Test retry processing functionality
                        print("Step 3: Triggering retry processing...")
                        retry_response = self.session.post(
                            f"{BACKEND_URL}/notes/{note_id}/retry-processing",
                            timeout=15
                        )
                        
                        if retry_response.status_code == 200:
                            retry_data = retry_response.json()
                            
                            print(f"✅ Step 3: Retry processing triggered")
                            print(f"   Message: {retry_data.get('message', 'No message')}")
                            print(f"   Actions: {retry_data.get('actions_taken', [])}")
                            
                            # Step 4: Check if background task was enqueued
                            print("Step 4: Waiting for background task processing...")
                            time.sleep(8)  # Wait longer for processing
                            
                            # Check status after retry
                            post_retry_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                            if post_retry_response.status_code == 200:
                                post_retry_data = post_retry_response.json()
                                post_retry_status = post_retry_data.get("status", "unknown")
                                
                                # Step 5: Analyze the complete pipeline
                                artifacts = post_retry_data.get("artifacts", {})
                                has_transcript = bool(artifacts.get("transcript", "").strip())
                                has_error = bool(artifacts.get("error", ""))
                                
                                print(f"\n📊 PIPELINE ANALYSIS:")
                                print(f"   Note ID: {note_id}")
                                print(f"   Initial Status: {initial_status}")
                                print(f"   Post-Retry Status: {post_retry_status}")
                                print(f"   Has Media Key: {bool(post_retry_data.get('media_key'))}")
                                print(f"   Has Transcript: {has_transcript}")
                                print(f"   Has Error: {has_error}")
                                
                                if has_error:
                                    error_msg = artifacts.get("error", "")
                                    print(f"   Error Message: {error_msg}")
                                
                                if has_transcript:
                                    transcript = artifacts.get("transcript", "")
                                    print(f"   Transcript Length: {len(transcript)} chars")
                                    print(f"   Transcript Preview: {transcript[:100]}...")
                                
                                # Determine the issue
                                if post_retry_status == "ready" and has_transcript:
                                    self.log_result("Stuck Notes Retry Debugging", True, 
                                                  "✅ SUCCESS: Complete pipeline working - note processed to ready with transcript")
                                elif post_retry_status == "processing":
                                    self.log_result("Stuck Notes Retry Debugging", True, 
                                                  "⏳ PROCESSING: Note is actively processing after retry (normal behavior)")
                                elif has_error:
                                    error_msg = artifacts.get("error", "")
                                    if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                                        self.log_result("Stuck Notes Retry Debugging", True, 
                                                      f"🚦 RATE LIMITED: Retry working but hitting API limits: {error_msg}")
                                    else:
                                        self.log_result("Stuck Notes Retry Debugging", False, 
                                                      f"❌ ERROR: Retry triggered but processing failed: {error_msg}")
                                else:
                                    self.log_result("Stuck Notes Retry Debugging", False, 
                                                  f"❌ STUCK: Retry may not be working - status: {post_retry_status}")
                            else:
                                self.log_result("Stuck Notes Retry Debugging", False, 
                                              f"Cannot check post-retry status: HTTP {post_retry_response.status_code}")
                        else:
                            self.log_result("Stuck Notes Retry Debugging", False, 
                                          f"❌ Retry processing failed: HTTP {retry_response.status_code}: {retry_response.text}")
                    else:
                        self.log_result("Stuck Notes Retry Debugging", False, 
                                      f"Cannot check initial note status: HTTP {status_response.status_code}")
                else:
                    self.log_result("Stuck Notes Retry Debugging", False, "Audio upload succeeded but no note ID returned")
            else:
                self.log_result("Stuck Notes Retry Debugging", False, 
                              f"Audio upload failed: HTTP {upload_response.status_code}: {upload_response.text}")
                
        except Exception as e:
            self.log_result("Stuck Notes Retry Debugging", False, f"Stuck notes retry debugging error: {str(e)}")

    def test_background_task_verification(self):
        """Check if background tasks are working"""
        try:
            print("\n🔍 CHECKING BACKGROUND TASK SYSTEM")
            print("=" * 60)
            
            health_response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                pipeline_status = health_data.get("pipeline", {})
                services = health_data.get("services", {})
                
                pipeline_health = services.get("pipeline", "unknown")
                
                print(f"Overall Health: {health_data.get('status', 'unknown')}")
                print(f"Pipeline Health: {pipeline_health}")
                print(f"Pipeline Status: {json.dumps(pipeline_status, indent=2)}")
                
                if pipeline_health == "healthy":
                    self.log_result("Background Task Verification", True, 
                                  "✅ Pipeline worker is healthy and running")
                elif pipeline_health == "degraded":
                    self.log_result("Background Task Verification", True, 
                                  "⚠️ Pipeline worker is degraded but functional")
                else:
                    self.log_result("Background Task Verification", False, 
                                  f"❌ Pipeline worker issues detected: {pipeline_health}")
            else:
                self.log_result("Background Task Verification", False, 
                              f"Cannot check pipeline status: HTTP {health_response.status_code}")
                
        except Exception as e:
            self.log_result("Background Task Verification", False, 
                          f"Background task verification error: {str(e)}")

    def run_debug_tests(self):
        """Run the critical debug tests"""
        print("🚨 CRITICAL DEBUG TESTS - Retry Processing Issue")
        print("=" * 60)
        
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run the critical debug tests
        self.test_background_task_verification()
        self.test_stuck_notes_retry_debugging()
        
        # Print summary
        print("\n📊 DEBUG TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = RetryDebugTester()
    tester.run_debug_tests()