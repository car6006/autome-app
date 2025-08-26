#!/usr/bin/env python3
"""
Focused Retest for Critical Fixes
Tests the two specific fixes mentioned in the review request:
1. Notes Processing Fix (file:// URL issue)
2. JSON Export Fix (datetime serialization issue)
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class FocusedRetester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"retest_user_{int(time.time())}@example.com",
            "username": f"retestuser_{int(time.time())}",
            "password": "RetestPassword123!",
            "first_name": "Retest",
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

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response", "text": response.text}
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

    def setup_auth(self):
        """Setup authentication for testing"""
        self.log("🔐 Setting up authentication...")
        
        # Register user
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   Authentication setup successful")
            return True
        else:
            self.log(f"   Authentication setup failed")
            return False

    def test_notes_processing_fix(self):
        """Test the critical notes processing fix (file:// URL issue)"""
        self.log("\n🎯 TESTING NOTES PROCESSING FIX")
        self.log("   Testing that notes no longer get stuck in 'processing' state")
        
        # Test 1: Create and process audio note
        self.log("\n📢 Testing Audio Note Processing...")
        
        # Create audio note
        success, response = self.run_test(
            "Create Audio Note",
            "POST",
            "notes",
            200,
            data={"title": "Audio Processing Test", "kind": "audio"},
            auth_required=True
        )
        
        if not success:
            return False
        
        audio_note_id = response.get('id')
        self.created_notes.append(audio_note_id)
        
        # Upload dummy audio file
        success = self.upload_dummy_audio(audio_note_id)
        if not success:
            return False
        
        # Wait for processing and check results
        audio_success = self.wait_for_processing_and_verify(audio_note_id, "audio")
        
        # Test 2: Create and process photo note
        self.log("\n📷 Testing Photo Note Processing...")
        
        # Create photo note
        success, response = self.run_test(
            "Create Photo Note",
            "POST",
            "notes",
            200,
            data={"title": "Photo Processing Test", "kind": "photo"},
            auth_required=True
        )
        
        if not success:
            return False
        
        photo_note_id = response.get('id')
        self.created_notes.append(photo_note_id)
        
        # Upload dummy image file
        success = self.upload_dummy_image(photo_note_id)
        if not success:
            return False
        
        # Wait for processing and check results
        photo_success = self.wait_for_processing_and_verify(photo_note_id, "photo")
        
        return audio_success and photo_success

    def test_json_export_fix(self):
        """Test the JSON export fix (datetime serialization issue)"""
        self.log("\n🎯 TESTING JSON EXPORT FIX")
        self.log("   Testing that JSON export no longer returns 500 errors")
        
        if not self.created_notes:
            self.log("❌ No notes available for export testing")
            return False
        
        # Test JSON export on each created note
        all_exports_successful = True
        
        for note_id in self.created_notes:
            self.log(f"\n📤 Testing JSON Export for note {note_id[:8]}...")
            
            # Test JSON export
            success, response = self.run_test(
                f"JSON Export Note {note_id[:8]}...",
                "GET",
                f"notes/{note_id}/export?format=json",
                200,
                auth_required=True
            )
            
            if success:
                # Verify it's valid JSON with expected fields
                if isinstance(response, dict):
                    required_fields = ['id', 'title', 'kind', 'created_at']
                    missing_fields = [field for field in required_fields if field not in response]
                    
                    if missing_fields:
                        self.log(f"❌ Missing required fields in JSON export: {missing_fields}")
                        all_exports_successful = False
                    else:
                        self.log(f"✅ JSON export contains all required fields")
                        self.log(f"   ID: {response.get('id', 'N/A')}")
                        self.log(f"   Title: {response.get('title', 'N/A')}")
                        self.log(f"   Kind: {response.get('kind', 'N/A')}")
                        self.log(f"   Created At: {response.get('created_at', 'N/A')}")
                        
                        # Check if artifacts are present
                        artifacts = response.get('artifacts', {})
                        if artifacts:
                            self.log(f"   Artifacts: {list(artifacts.keys())}")
                else:
                    self.log(f"❌ JSON export did not return a valid JSON object")
                    all_exports_successful = False
            else:
                all_exports_successful = False
        
        return all_exports_successful

    def upload_dummy_audio(self, note_id):
        """Upload a dummy audio file for testing"""
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
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            return success

    def upload_dummy_image(self, note_id):
        """Upload a dummy image file for testing"""
        # Create a minimal PNG file (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
        
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
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            return success

    def wait_for_processing_and_verify(self, note_id, note_type, max_wait=60):
        """Wait for note processing to complete and verify it doesn't get stuck"""
        self.log(f"⏳ Waiting for {note_type} note {note_id[:8]}... to process (max {max_wait}s)")
        start_time = time.time()
        
        processing_states = []
        
        while time.time() - start_time < max_wait:
            success, note_data = self.run_test(
                f"Check Note Status {note_id[:8]}...",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success:
                status = note_data.get('status', 'unknown')
                processing_states.append(status)
                
                self.log(f"   Status: {status}")
                
                if status == 'ready':
                    self.log(f"✅ {note_type.title()} note processing completed successfully!")
                    
                    # Verify artifacts are present
                    artifacts = note_data.get('artifacts', {})
                    if artifacts:
                        self.log(f"   Artifacts found: {list(artifacts.keys())}")
                        
                        # Check for expected artifacts based on note type
                        if note_type == 'audio' and 'transcript' in artifacts:
                            self.log(f"   ✅ Audio transcript artifact present")
                        elif note_type == 'photo' and 'text' in artifacts:
                            self.log(f"   ✅ Photo OCR text artifact present")
                        else:
                            self.log(f"   ⚠️  Expected artifacts not found for {note_type} note")
                    else:
                        self.log(f"   ⚠️  No artifacts found in processed note")
                    
                    return True
                    
                elif status == 'failed':
                    self.log(f"❌ {note_type.title()} note processing failed!")
                    
                    # Check for error details in artifacts
                    artifacts = note_data.get('artifacts', {})
                    if 'error' in artifacts:
                        self.log(f"   Error details: {artifacts['error']}")
                    
                    return False
                    
                elif status == 'processing':
                    self.log(f"   Still processing... (elapsed: {int(time.time() - start_time)}s)")
                    time.sleep(3)
                else:
                    self.log(f"   Unknown status: {status}")
                    time.sleep(2)
            else:
                self.log(f"❌ Failed to check note status")
                break
        
        # If we get here, processing timed out
        self.log(f"⏰ Timeout waiting for {note_type} note processing")
        self.log(f"   Processing states observed: {processing_states}")
        
        # Check if note got stuck in processing
        if 'processing' in processing_states and processing_states[-1] == 'processing':
            self.log(f"❌ CRITICAL: Note appears to be stuck in 'processing' state!")
            return False
        
        return False

    def run_focused_retest(self):
        """Run the focused retest for the two critical fixes"""
        self.log("🚀 Starting Focused Retest for Critical Fixes")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup authentication
        if not self.setup_auth():
            self.log("❌ Authentication setup failed - stopping tests")
            return False
        
        # Test 1: Notes Processing Fix
        processing_fix_success = self.test_notes_processing_fix()
        
        # Test 2: JSON Export Fix
        json_export_fix_success = self.test_json_export_fix()
        
        return processing_fix_success and json_export_fix_success

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 FOCUSED RETEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FocusedRetester()
    
    try:
        success = tester.run_focused_retest()
        tester.print_summary()
        
        if success:
            print("\n🎉 All focused retests passed! Critical fixes are working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some focused retests failed. Check the logs above for details.")
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