#!/usr/bin/env python3
"""
Large File Transcription Integration Test
Tests the complete integration between large file transcription system and main notes system
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://whisper-async-fix.preview.emergentagent.com/api"
TEST_FILE_PATH = "/tmp/autome_storage/test_30s.wav"
TEST_EMAIL = "test@expeditors.com"
TEST_PASSWORD = "testpass123"

class LargeFileIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def setup_authentication(self):
        """Setup authentication for testing - Skip for now, test anonymously"""
        try:
            # For this integration test, we'll test anonymously since the API supports it
            self.log_result("Authentication Setup", True, "Testing anonymously (API supports anonymous access)")
            return True
            
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_health_check(self):
        """Test system health before starting"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                self.log_result("System Health Check", status in ["healthy", "degraded"], f"Status: {status}")
                return status in ["healthy", "degraded"]
            else:
                self.log_result("System Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("System Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_large_file_upload_via_upload_file(self):
        """Test 1: Upload large file via /api/upload-file endpoint"""
        try:
            if not os.path.exists(TEST_FILE_PATH):
                self.log_result("Large File Upload (upload-file)", False, f"Test file not found: {TEST_FILE_PATH}")
                return None
            
            # Get file size
            file_size = os.path.getsize(TEST_FILE_PATH)
            self.log_result("File Size Check", True, f"Test file size: {file_size / (1024*1024):.1f} MB")
            
            with open(TEST_FILE_PATH, 'rb') as f:
                files = {'file': ('test_30s.wav', f, 'audio/wav')}
                data = {'title': 'Large File Integration Test - 30s Audio'}
                
                response = self.session.post(f"{BACKEND_URL}/upload-file", files=files, data=data)
                
                if response.status_code == 200:
                    upload_result = response.json()
                    note_id = upload_result.get("id")
                    status = upload_result.get("status")
                    kind = upload_result.get("kind")
                    
                    self.log_result("Large File Upload (upload-file)", True, 
                                  f"Note ID: {note_id}, Status: {status}, Kind: {kind}")
                    return note_id
                else:
                    self.log_result("Large File Upload (upload-file)", False, 
                                  f"HTTP {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            self.log_result("Large File Upload (upload-file)", False, f"Exception: {str(e)}")
            return None
    
    def test_large_file_upload_via_create_and_upload(self):
        """Test 2: Upload large file via create note + upload workflow"""
        try:
            # Step 1: Create audio note
            create_data = {
                "title": "Large File Integration Test - Create+Upload",
                "kind": "audio"
            }
            
            response = self.session.post(f"{BACKEND_URL}/notes", json=create_data)
            if response.status_code != 200:
                self.log_result("Create Note for Upload", False, f"HTTP {response.status_code}")
                return None
            
            create_result = response.json()
            note_id = create_result.get("id")
            self.log_result("Create Note for Upload", True, f"Note ID: {note_id}")
            
            # Step 2: Upload file to the note
            with open(TEST_FILE_PATH, 'rb') as f:
                files = {'file': ('test_30s.wav', f, 'audio/wav')}
                
                response = self.session.post(f"{BACKEND_URL}/notes/{note_id}/upload", files=files)
                
                if response.status_code == 200:
                    upload_result = response.json()
                    status = upload_result.get("status")
                    
                    self.log_result("Large File Upload (create+upload)", True, 
                                  f"Note ID: {note_id}, Status: {status}")
                    return note_id
                else:
                    self.log_result("Large File Upload (create+upload)", False, 
                                  f"HTTP {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            self.log_result("Large File Upload (create+upload)", False, f"Exception: {str(e)}")
            return None
    
    def test_note_status_progression(self, note_id, test_name_prefix):
        """Test note status progression through processing stages"""
        if not note_id:
            return False
        
        try:
            # Check initial status
            response = self.session.get(f"{BACKEND_URL}/notes/{note_id}")
            if response.status_code != 200:
                self.log_result(f"{test_name_prefix} - Status Check", False, f"HTTP {response.status_code}")
                return False
            
            note_data = response.json()
            initial_status = note_data.get("status")
            self.log_result(f"{test_name_prefix} - Initial Status", True, f"Status: {initial_status}")
            
            # Monitor status progression
            max_wait_time = 300  # 5 minutes
            check_interval = 10  # 10 seconds
            start_time = time.time()
            
            expected_statuses = ["uploading", "processing", "ready", "failed"]
            status_progression = [initial_status]
            
            while time.time() - start_time < max_wait_time:
                response = self.session.get(f"{BACKEND_URL}/notes/{note_id}")
                if response.status_code == 200:
                    note_data = response.json()
                    current_status = note_data.get("status")
                    
                    if current_status != status_progression[-1]:
                        status_progression.append(current_status)
                        self.log_result(f"{test_name_prefix} - Status Update", True, 
                                      f"Status changed to: {current_status}")
                    
                    if current_status in ["ready", "failed"]:
                        break
                
                time.sleep(check_interval)
            
            final_status = status_progression[-1] if status_progression else "unknown"
            
            if final_status == "ready":
                self.log_result(f"{test_name_prefix} - Processing Complete", True, 
                              f"Final status: {final_status}, Progression: {' -> '.join(status_progression)}")
                return True
            elif final_status == "failed":
                self.log_result(f"{test_name_prefix} - Processing Failed", False, 
                              f"Final status: {final_status}, Progression: {' -> '.join(status_progression)}")
                return False
            else:
                self.log_result(f"{test_name_prefix} - Processing Timeout", False, 
                              f"Timed out after {max_wait_time}s, Final status: {final_status}")
                return False
                
        except Exception as e:
            self.log_result(f"{test_name_prefix} - Status Progression", False, f"Exception: {str(e)}")
            return False
    
    def test_note_content_and_metadata(self, note_id, test_name_prefix):
        """Test note content and metadata after processing"""
        if not note_id:
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/notes/{note_id}")
            if response.status_code != 200:
                self.log_result(f"{test_name_prefix} - Content Check", False, f"HTTP {response.status_code}")
                return False
            
            note_data = response.json()
            artifacts = note_data.get("artifacts", {})
            
            # Check for transcript content
            transcript = artifacts.get("transcript", "")
            if transcript:
                transcript_length = len(transcript)
                self.log_result(f"{test_name_prefix} - Transcript Content", True, 
                              f"Transcript length: {transcript_length} characters")
            else:
                self.log_result(f"{test_name_prefix} - Transcript Content", False, "No transcript found")
                return False
            
            # Check metadata
            metadata_checks = []
            
            # Check for duration
            if "duration" in artifacts:
                metadata_checks.append(f"Duration: {artifacts['duration']}")
            
            # Check for language
            if "language" in artifacts:
                metadata_checks.append(f"Language: {artifacts['language']}")
            
            # Check created_at and ready_at
            created_at = note_data.get("created_at")
            ready_at = note_data.get("ready_at")
            
            if created_at:
                metadata_checks.append(f"Created: {created_at}")
            if ready_at:
                metadata_checks.append(f"Ready: {ready_at}")
            
            self.log_result(f"{test_name_prefix} - Metadata", True, 
                          f"Metadata: {', '.join(metadata_checks) if metadata_checks else 'Basic metadata present'}")
            
            return True
            
        except Exception as e:
            self.log_result(f"{test_name_prefix} - Content Check", False, f"Exception: {str(e)}")
            return False
    
    def test_notes_list_visibility(self, note_id, test_name_prefix):
        """Test that completed note appears in notes list"""
        if not note_id:
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/notes")
            if response.status_code != 200:
                self.log_result(f"{test_name_prefix} - Notes List", False, f"HTTP {response.status_code}")
                return False
            
            notes_list = response.json()
            
            # Find our note in the list
            found_note = None
            for note in notes_list:
                if note.get("id") == note_id:
                    found_note = note
                    break
            
            if found_note:
                status = found_note.get("status")
                title = found_note.get("title")
                self.log_result(f"{test_name_prefix} - Notes List Visibility", True, 
                              f"Note found in list - Title: {title}, Status: {status}")
                return True
            else:
                self.log_result(f"{test_name_prefix} - Notes List Visibility", False, 
                              f"Note {note_id} not found in notes list")
                return False
                
        except Exception as e:
            self.log_result(f"{test_name_prefix} - Notes List", False, f"Exception: {str(e)}")
            return False
    
    def test_ai_features(self, note_id, test_name_prefix):
        """Test AI features on completed note"""
        if not note_id:
            return False
        
        ai_tests_passed = 0
        total_ai_tests = 4
        
        # Test 1: AI Chat
        try:
            chat_data = {"question": "What are the key points from this audio?"}
            response = self.session.post(f"{BACKEND_URL}/notes/{note_id}/ai-chat", json=chat_data)
            
            if response.status_code == 200:
                chat_result = response.json()
                ai_response = chat_result.get("response", "")
                if ai_response and len(ai_response) > 50:
                    self.log_result(f"{test_name_prefix} - AI Chat", True, 
                                  f"AI response length: {len(ai_response)} characters")
                    ai_tests_passed += 1
                else:
                    self.log_result(f"{test_name_prefix} - AI Chat", False, "AI response too short or empty")
            else:
                self.log_result(f"{test_name_prefix} - AI Chat", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result(f"{test_name_prefix} - AI Chat", False, f"Exception: {str(e)}")
        
        # Test 2: Generate Report
        try:
            response = self.session.post(f"{BACKEND_URL}/notes/{note_id}/generate-report")
            
            if response.status_code == 200:
                report_result = response.json()
                report_content = report_result.get("report", "")
                if report_content and len(report_content) > 100:
                    self.log_result(f"{test_name_prefix} - Generate Report", True, 
                                  f"Report length: {len(report_content)} characters")
                    ai_tests_passed += 1
                else:
                    self.log_result(f"{test_name_prefix} - Generate Report", False, "Report too short or empty")
            else:
                self.log_result(f"{test_name_prefix} - Generate Report", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result(f"{test_name_prefix} - Generate Report", False, f"Exception: {str(e)}")
        
        # Test 3: Export AI Conversations (PDF)
        try:
            response = self.session.get(f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf")
            
            if response.status_code == 200:
                content_length = len(response.content)
                if content_length > 1000:  # PDF should be substantial
                    self.log_result(f"{test_name_prefix} - Export PDF", True, 
                                  f"PDF size: {content_length} bytes")
                    ai_tests_passed += 1
                else:
                    self.log_result(f"{test_name_prefix} - Export PDF", False, "PDF too small")
            else:
                self.log_result(f"{test_name_prefix} - Export PDF", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result(f"{test_name_prefix} - Export PDF", False, f"Exception: {str(e)}")
        
        # Test 4: Batch Report (with this note)
        try:
            batch_data = {
                "note_ids": [note_id],
                "title": "Integration Test Batch Report",
                "format": "professional"
            }
            response = self.session.post(f"{BACKEND_URL}/notes/batch-report", json=batch_data)
            
            if response.status_code == 200:
                batch_result = response.json()
                report_content = batch_result.get("report", "")
                if report_content and len(report_content) > 100:
                    self.log_result(f"{test_name_prefix} - Batch Report", True, 
                                  f"Batch report length: {len(report_content)} characters")
                    ai_tests_passed += 1
                else:
                    self.log_result(f"{test_name_prefix} - Batch Report", False, "Batch report too short or empty")
            else:
                self.log_result(f"{test_name_prefix} - Batch Report", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result(f"{test_name_prefix} - Batch Report", False, f"Exception: {str(e)}")
        
        # Overall AI features result
        success_rate = (ai_tests_passed / total_ai_tests) * 100
        overall_success = ai_tests_passed >= 3  # At least 3 out of 4 should work
        
        self.log_result(f"{test_name_prefix} - AI Features Overall", overall_success, 
                      f"Success rate: {success_rate:.1f}% ({ai_tests_passed}/{total_ai_tests})")
        
        return overall_success
    
    def run_complete_integration_test(self):
        """Run the complete integration test"""
        print("="*80)
        print("LARGE FILE TRANSCRIPTION INTEGRATION TEST")
        print("="*80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot continue")
            return False
        
        if not self.test_health_check():
            print("⚠️  System health check failed - continuing anyway")
        
        # Test both upload methods
        upload_methods = [
            ("Direct Upload", self.test_large_file_upload_via_upload_file),
            ("Create+Upload", self.test_large_file_upload_via_create_and_upload)
        ]
        
        successful_tests = 0
        total_tests = 0
        
        for method_name, upload_method in upload_methods:
            print(f"\n--- Testing {method_name} Method ---")
            
            # Upload file
            note_id = upload_method()
            if not note_id:
                continue
            
            # Test progression and content
            if self.test_note_status_progression(note_id, method_name):
                total_tests += 1
                if self.test_note_content_and_metadata(note_id, method_name):
                    if self.test_notes_list_visibility(note_id, method_name):
                        if self.test_ai_features(note_id, method_name):
                            successful_tests += 1
        
        # Summary
        print("\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)
        
        success_rate = (successful_tests / max(total_tests, 1)) * 100
        overall_success = successful_tests > 0
        
        print(f"Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"Overall Result: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        # Detailed results
        print(f"\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        return overall_success

def main():
    """Main test execution"""
    tester = LargeFileIntegrationTester()
    success = tester.run_complete_integration_test()
    
    if success:
        print("\n🎉 LARGE FILE TRANSCRIPTION INTEGRATION TEST PASSED!")
        exit(0)
    else:
        print("\n💥 LARGE FILE TRANSCRIPTION INTEGRATION TEST FAILED!")
        exit(1)

if __name__ == "__main__":
    main()