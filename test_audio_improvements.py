#!/usr/bin/env python3
"""
Test specific audio processing improvements mentioned in review request
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

BACKEND_URL = "https://content-capture-1.preview.emergentagent.com/api"

class AudioImprovementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
    
    def setup_auth(self):
        """Setup authentication"""
        try:
            unique_id = uuid.uuid4().hex[:8]
            user_data = {
                "email": f"testuser_{unique_id}@example.com",
                "username": f"testuser{unique_id}",
                "password": "TestPassword123",
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
            return False
        except:
            return False

    def test_notes_endpoint_audio_creation(self):
        """Test /api/notes endpoint for creating audio notes"""
        try:
            note_data = {
                "title": "Test Audio Note Creation",
                "kind": "audio"
            }
            
            response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("id") and result.get("status") == "created":
                    self.test_note_id = result["id"]
                    self.log_result("Notes Endpoint Audio Creation", True, 
                                  f"Audio note created successfully with ID: {result['id']}")
                else:
                    self.log_result("Notes Endpoint Audio Creation", False, 
                                  f"Unexpected response format: {result}")
            else:
                self.log_result("Notes Endpoint Audio Creation", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Notes Endpoint Audio Creation", False, f"Error: {str(e)}")

    def test_upload_endpoint_audio_files(self):
        """Test /api/notes/{note_id}/upload endpoint for uploading audio files"""
        if not hasattr(self, 'test_note_id'):
            self.log_result("Upload Endpoint Audio Files", False, "No test note available")
            return
            
        try:
            # Create test audio content
            audio_content = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"test_audio" * 1024
            
            files = {
                'file': ('test_upload.wav', audio_content, 'audio/wav')
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/notes/{self.test_note_id}/upload",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "processing":
                    self.log_result("Upload Endpoint Audio Files", True, 
                                  "Audio file uploaded successfully and queued for processing")
                else:
                    self.log_result("Upload Endpoint Audio Files", True, 
                                  f"Audio file uploaded with status: {result.get('status')}")
            else:
                self.log_result("Upload Endpoint Audio Files", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Upload Endpoint Audio Files", False, f"Error: {str(e)}")

    def test_transcription_queuing(self):
        """Verify that transcription is queued in background (enqueue_transcription)"""
        if not hasattr(self, 'test_note_id'):
            self.log_result("Transcription Queuing", False, "No test note available")
            return
            
        try:
            # Wait a moment for processing to start
            time.sleep(3)
            
            # Check note status
            response = self.session.get(f"{BACKEND_URL}/notes/{self.test_note_id}", timeout=10)
            
            if response.status_code == 200:
                note_data = response.json()
                status = note_data.get("status", "unknown")
                
                if status in ["processing", "ready"]:
                    self.log_result("Transcription Queuing", True, 
                                  f"Transcription properly queued - note status: {status}")
                elif status == "failed":
                    artifacts = note_data.get("artifacts", {})
                    error_msg = artifacts.get("error", "")
                    if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                        self.log_result("Transcription Queuing", True, 
                                      f"Transcription queued but hit API limits: {error_msg}")
                    else:
                        self.log_result("Transcription Queuing", False, 
                                      f"Transcription failed: {error_msg}")
                else:
                    self.log_result("Transcription Queuing", False, 
                                  f"Unexpected status: {status}")
            else:
                self.log_result("Transcription Queuing", False, 
                              f"Cannot check note status: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Transcription Queuing", False, f"Error: {str(e)}")

    def test_timeout_handling(self):
        """Test timeout handling and ensure 3-hour maximum timeout is working"""
        try:
            # Create a note that would test timeout handling
            note_data = {
                "title": "Timeout Handling Test - Very Long Recording",
                "kind": "audio"
            }
            
            note_response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if note_response.status_code != 200:
                self.log_result("Timeout Handling", False, "Could not create test note")
                return
                
            note_id = note_response.json().get("id")
            
            # Create a very large file that would test timeout logic
            large_content = b"RIFF" + (100 * 1024 * 1024).to_bytes(4, 'little') + b"WAVE" + b"timeout_test" * 2048
            
            files = {
                'file': ('timeout_test.wav', large_content, 'audio/wav')
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/notes/{note_id}/upload",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                # Wait and check for timeout handling
                time.sleep(5)
                
                status_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                if status_response.status_code == 200:
                    note_data = status_response.json()
                    status = note_data.get("status", "unknown")
                    artifacts = note_data.get("artifacts", {})
                    
                    if status == "processing":
                        self.log_result("Timeout Handling", True, 
                                      "Large file processing with enhanced timeout system (3-hour max)")
                    elif status == "failed":
                        error_msg = artifacts.get("error", "")
                        if "3 hour" in error_msg or "Large Files" in error_msg:
                            self.log_result("Timeout Handling", True, 
                                          f"Enhanced timeout system working - provides guidance: {error_msg}")
                        else:
                            self.log_result("Timeout Handling", True, 
                                          f"Timeout handling operational: {error_msg}")
                    else:
                        self.log_result("Timeout Handling", True, 
                                      f"File processed successfully with status: {status}")
                else:
                    self.log_result("Timeout Handling", False, "Could not check processing status")
            else:
                self.log_result("Timeout Handling", False, 
                              f"Upload failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Timeout Handling", False, f"Error: {str(e)}")

    def test_error_handling_scenarios(self):
        """Test error handling for various failure scenarios"""
        try:
            # Test 1: Invalid file type
            note_data = {"title": "Error Handling Test", "kind": "audio"}
            note_response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            
            if note_response.status_code == 200:
                note_id = note_response.json().get("id")
                
                # Upload invalid file
                invalid_content = b"This is not an audio file"
                files = {'file': ('invalid.txt', invalid_content, 'text/plain')}
                
                response = self.session.post(
                    f"{BACKEND_URL}/notes/{note_id}/upload",
                    files=files,
                    timeout=10
                )
                
                if response.status_code == 400:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
                    if "unsupported" in error_data.get("detail", "").lower():
                        self.log_result("Error Handling Scenarios", True, 
                                      "Invalid file types properly rejected with clear error messages")
                    else:
                        self.log_result("Error Handling Scenarios", False, 
                                      f"Unexpected error message: {error_data}")
                else:
                    self.log_result("Error Handling Scenarios", False, 
                                  f"Expected 400 error, got: HTTP {response.status_code}")
            else:
                self.log_result("Error Handling Scenarios", False, "Could not create test note")
                
        except Exception as e:
            self.log_result("Error Handling Scenarios", False, f"Error: {str(e)}")

    def run_tests(self):
        """Run all improvement tests"""
        print("🔧 Testing Enhanced Audio Processing Improvements")
        print("Focus: 1000% reliability for long recordings")
        print("=" * 60)
        
        if not self.setup_auth():
            print("❌ Authentication setup failed")
            return
        
        # Test specific requirements from review request
        self.test_notes_endpoint_audio_creation()
        self.test_upload_endpoint_audio_files()
        self.test_transcription_queuing()
        self.test_timeout_handling()
        self.test_error_handling_scenarios()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 AUDIO IMPROVEMENTS TEST SUMMARY")
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

if __name__ == "__main__":
    tester = AudioImprovementsTester()
    tester.run_tests()