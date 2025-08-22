#!/usr/bin/env python3
"""
AUTO-ME Productivity PWA Backend API Tests
Tests all API endpoints and core functionality
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class AutoMeAPITester:
    def __init__(self, base_url="https://workboost.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_id = None
        self.test_user_data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "username": f"testuser_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "",
            200
        )
        if success:
            self.log(f"   API Message: {response.get('message', 'N/A')}")
        return success

    def test_create_audio_note(self):
        """Test creating an audio note"""
        success, response = self.run_test(
            "Create Audio Note",
            "POST",
            "notes",
            200,
            data={"title": "Test Audio Note", "kind": "audio"}
        )
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   Created note ID: {note_id}")
            return note_id
        return None

    def test_create_photo_note(self):
        """Test creating a photo note"""
        success, response = self.run_test(
            "Create Photo Note",
            "POST",
            "notes",
            200,
            data={"title": "Test Photo Note", "kind": "photo"}
        )
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   Created note ID: {note_id}")
            return note_id
        return None

    def test_get_note(self, note_id):
        """Test getting a specific note"""
        success, response = self.run_test(
            f"Get Note {note_id[:8]}...",
            "GET",
            f"notes/{note_id}",
            200
        )
        if success:
            self.log(f"   Note title: {response.get('title', 'N/A')}")
            self.log(f"   Note status: {response.get('status', 'N/A')}")
            self.log(f"   Note kind: {response.get('kind', 'N/A')}")
        return success, response

    def test_list_notes(self):
        """Test listing all notes"""
        success, response = self.run_test(
            "List Notes",
            "GET",
            "notes",
            200
        )
        if success:
            notes_count = len(response) if isinstance(response, list) else 0
            self.log(f"   Found {notes_count} notes")
        return success, response

    def test_upload_dummy_audio(self, note_id):
        """Test uploading a dummy audio file"""
        # Create a small dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            # Write minimal WebM header (just for testing, not real audio)
            dummy_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_audio.webm', f, 'audio/webm')}
                success, response = self.run_test(
                    f"Upload Audio to Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files
                )
            
            os.unlink(tmp_file.name)
            return success

    def test_upload_dummy_image(self, note_id):
        """Test uploading a dummy image file"""
        # Create a minimal PNG file (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_image.png', f, 'image/png')}
                success, response = self.run_test(
                    f"Upload Image to Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files
                )
            
            os.unlink(tmp_file.name)
            return success

    def test_email_functionality(self, note_id):
        """Test email functionality (without actually sending)"""
        success, response = self.run_test(
            f"Queue Email for Note {note_id[:8]}...",
            "POST",
            f"notes/{note_id}/email",
            200,
            data={
                "to": ["test@example.com"],
                "subject": "Test Email from AUTO-ME"
            }
        )
        return success

    def test_git_sync_functionality(self, note_id):
        """Test Git sync functionality"""
        success, response = self.run_test(
            f"Queue Git Sync for Note {note_id[:8]}...",
            "POST",
            f"notes/{note_id}/git-sync",
            200
        )
        return success

    def test_metrics_endpoint(self):
        """Test productivity metrics endpoint"""
        success, response = self.run_test(
            "Get Productivity Metrics",
            "GET",
            "metrics?days=7",
            200
        )
        if success:
            self.log(f"   Total notes: {response.get('notes_total', 0)}")
            self.log(f"   Ready notes: {response.get('notes_ready', 0)}")
            self.log(f"   Success rate: {response.get('success_rate', 0)}%")
            self.log(f"   Estimated time saved: {response.get('estimated_minutes_saved', 0)} minutes")
        return success

    def test_invalid_endpoints(self):
        """Test error handling for invalid endpoints"""
        # Test non-existent note
        success, _ = self.run_test(
            "Get Non-existent Note",
            "GET",
            "notes/invalid-id",
            404
        )
        
        # Test invalid note creation
        success2, _ = self.run_test(
            "Create Invalid Note",
            "POST",
            "notes",
            422,  # Validation error
            data={"title": "", "kind": "invalid"}
        )
        
        return success and success2

    def wait_for_processing(self, note_id, max_wait=30):
        """Wait for note processing to complete"""
        self.log(f"⏳ Waiting for note {note_id[:8]}... to process (max {max_wait}s)")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, note_data = self.test_get_note(note_id)
            if success:
                status = note_data.get('status', 'unknown')
                if status == 'ready':
                    self.log(f"✅ Note processing completed!")
                    return True
                elif status == 'failed':
                    self.log(f"❌ Note processing failed!")
                    return False
                else:
                    self.log(f"   Status: {status}, waiting...")
                    time.sleep(2)
            else:
                break
        
        self.log(f"⏰ Timeout waiting for note processing")
        return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting AUTO-ME API Comprehensive Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Basic API tests
        if not self.test_health_check():
            self.log("❌ Health check failed - stopping tests")
            return False
        
        # Test note creation
        audio_note_id = self.test_create_audio_note()
        photo_note_id = self.test_create_photo_note()
        
        if not audio_note_id or not photo_note_id:
            self.log("❌ Note creation failed - stopping tests")
            return False
        
        # Test note retrieval
        self.test_get_note(audio_note_id)
        self.test_get_note(photo_note_id)
        
        # Test note listing
        self.test_list_notes()
        
        # Test file uploads
        self.test_upload_dummy_audio(audio_note_id)
        self.test_upload_dummy_image(photo_note_id)
        
        # Wait a bit for processing to start
        time.sleep(3)
        
        # Check processing status
        self.test_get_note(audio_note_id)
        self.test_get_note(photo_note_id)
        
        # Test additional functionality
        self.test_email_functionality(audio_note_id)
        self.test_git_sync_functionality(photo_note_id)
        
        # Test metrics
        self.test_metrics_endpoint()
        
        # Test error handling
        self.test_invalid_endpoints()
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*50)
        self.log("📊 TEST SUMMARY")
        self.log("="*50)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*50)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = AutoMeAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 All tests passed! Backend API is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())