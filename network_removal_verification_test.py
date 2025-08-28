#!/usr/bin/env python3
"""
OPEN AUTO-ME v1 Network Diagram Removal Verification Test
Quick verification test after network diagram feature removal
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class NetworkRemovalVerificationTester:
    def __init__(self, base_url="https://whisper-async-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"testremoval{int(time.time())}@example.com",
            "username": f"testremoval{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        self.expeditors_user_data = {
            "email": f"testexpeditors{int(time.time())}@expeditors.com",
            "username": f"expeditorstest{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "User"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False, use_expeditors_token=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authentication header if required and available
        if auth_required:
            token = self.expeditors_token if use_expeditors_token else self.auth_token
            if token:
                headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
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

    def test_api_health(self):
        """Test API health check - verify no import errors"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        if success:
            message = response.get('message', '')
            self.log(f"   API Message: {message}")
            if 'AUTO-ME' in message:
                self.log(f"   ✅ API responding correctly after network diagram removal")
            return True
        return False

    def test_user_registration(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Registered user: {user_data.get('email')}")
            return True
        return False

    def test_expeditors_user_registration(self):
        """Test Expeditors user registration"""
        success, response = self.run_test(
            "Expeditors User Registration",
            "POST",
            "auth/register",
            200,
            data=self.expeditors_user_data
        )
        if success:
            self.expeditors_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Registered Expeditors user: {user_data.get('email')}")
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        if success:
            self.log(f"   ✅ Authentication system working correctly")
            return True
        return False

    def test_create_text_note(self):
        """Test creating a text note"""
        success, response = self.run_test(
            "Create Text Note",
            "POST",
            "notes",
            200,
            data={
                "title": "Test Text Note After Network Removal",
                "kind": "text",
                "text_content": "This is a test text note to verify core functionality after network diagram removal."
            },
            auth_required=True
        )
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   ✅ Text note creation working: {note_id}")
            return note_id
        return None

    def test_create_audio_note(self):
        """Test creating an audio note"""
        success, response = self.run_test(
            "Create Audio Note",
            "POST",
            "notes",
            200,
            data={
                "title": "Test Audio Note After Network Removal",
                "kind": "audio"
            },
            auth_required=True
        )
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   ✅ Audio note creation working: {note_id}")
            return note_id
        return None

    def test_create_photo_note(self):
        """Test creating a photo note"""
        success, response = self.run_test(
            "Create Photo Note",
            "POST",
            "notes",
            200,
            data={
                "title": "Test Photo Note After Network Removal",
                "kind": "photo"
            },
            auth_required=True
        )
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   ✅ Photo note creation working: {note_id}")
            return note_id
        return None

    def test_upload_audio_file(self, note_id):
        """Test uploading an audio file"""
        # Create a small dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            # Write minimal MP3 header
            dummy_data = b'\xff\xfb\x90\x00' + b'\x00' * 100
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_audio.mp3', f, 'audio/mp3')}
                success, response = self.run_test(
                    "Upload Audio File",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            if success:
                self.log(f"   ✅ Audio upload working correctly")
            return success

    def test_upload_photo_file(self, note_id):
        """Test uploading a photo file"""
        # Create a minimal PNG file
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_image.png', f, 'image/png')}
                success, response = self.run_test(
                    "Upload Photo File",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            if success:
                self.log(f"   ✅ Photo upload working correctly")
            return success

    def test_direct_file_upload(self):
        """Test direct file upload endpoint"""
        # Test with audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            dummy_data = b'\xff\xfb\x90\x00' + b'\x00' * 100
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('direct_upload_test.mp3', f, 'audio/mp3')}
                data = {'title': 'Direct Upload Test'}
                success, response = self.run_test(
                    "Direct File Upload",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            if success and 'id' in response:
                note_id = response['id']
                self.created_notes.append(note_id)
                self.log(f"   ✅ Direct file upload working: {note_id}")
                return True
        return False

    def test_iisb_analysis_access_control(self):
        """Test IISB analysis access control"""
        # Test with regular user (should fail)
        success, response = self.run_test(
            "IISB Analysis - Regular User (Should Fail)",
            "POST",
            "iisb/analyze",
            404,  # Should get 404 "Feature not found"
            data={
                "client_name": "Test Client",
                "issues_text": "Test supply chain issues for verification"
            },
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ IISB access control working - regular users blocked")
        
        # Test with Expeditors user (should work)
        if self.expeditors_token:
            success2, response2 = self.run_test(
                "IISB Analysis - Expeditors User",
                "POST",
                "iisb/analyze",
                200,
                data={
                    "client_name": "Test Expeditors Client",
                    "issues_text": "Supply chain bottleneck at Shanghai port affecting delivery schedules to European distribution centers"
                },
                auth_required=True,
                use_expeditors_token=True
            )
            
            if success2:
                self.log(f"   ✅ IISB analysis working for Expeditors users")
                return True
        
        return success

    def test_list_notes(self):
        """Test listing notes"""
        success, response = self.run_test(
            "List Notes",
            "GET",
            "notes",
            200,
            auth_required=True
        )
        if success:
            notes_count = len(response) if isinstance(response, list) else 0
            self.log(f"   ✅ Notes listing working - found {notes_count} notes")
            return True
        return False

    def test_get_note(self, note_id):
        """Test getting a specific note"""
        success, response = self.run_test(
            f"Get Note {note_id[:8]}...",
            "GET",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        if success:
            self.log(f"   Note status: {response.get('status', 'N/A')}")
            self.log(f"   Note kind: {response.get('kind', 'N/A')}")
            return True
        return False

    def test_export_functionality(self, note_id):
        """Test export functionality"""
        formats = ['txt', 'md', 'json']
        all_success = True
        
        for fmt in formats:
            success, response = self.run_test(
                f"Export Note as {fmt.upper()}",
                "GET",
                f"notes/{note_id}/export?format={fmt}",
                200,
                auth_required=True
            )
            if success:
                self.log(f"   ✅ {fmt.upper()} export working")
            else:
                all_success = False
        
        return all_success

    def test_network_endpoints_removed(self):
        """Test that network diagram endpoints are properly removed"""
        network_endpoints = [
            "network/process",
            "network/csv-template",
            "notes/network-diagram"
        ]
        
        all_removed = True
        for endpoint in network_endpoints:
            success, response = self.run_test(
                f"Network Endpoint Removed Check - {endpoint}",
                "POST",
                endpoint,
                404,  # Should return 404 since endpoints are removed
                data={"test": "data"},
                auth_required=True,
                use_expeditors_token=True
            )
            
            if success:
                self.log(f"   ✅ Network endpoint {endpoint} properly removed")
            else:
                all_removed = False
                self.log(f"   ❌ Network endpoint {endpoint} still exists")
        
        return all_removed

    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        success, response = self.run_test(
            "Get Metrics",
            "GET",
            "metrics?days=7",
            200,
            auth_required=True
        )
        if success:
            self.log(f"   Total notes: {response.get('notes_total', 0)}")
            self.log(f"   Success rate: {response.get('success_rate', 0)}%")
            self.log(f"   ✅ Metrics endpoint working")
            return True
        return False

    def run_verification_test(self):
        """Run the network removal verification test"""
        self.log("🚀 Starting OPEN AUTO-ME v1 Network Diagram Removal Verification")
        self.log(f"   Base URL: {self.base_url}")
        self.log("   Focus: Quick verification after network diagram feature removal")
        
        # 1. API Health Check
        self.log("\n🏥 API HEALTH CHECK")
        if not self.test_api_health():
            self.log("❌ API health check failed - stopping tests")
            return False
        
        # 2. Authentication System
        self.log("\n🔐 AUTHENTICATION VERIFICATION")
        if not self.test_user_registration():
            self.log("❌ User registration failed")
            return False
        
        if not self.test_user_login():
            self.log("❌ User login failed")
            return False
        
        # Register Expeditors user for IISB testing
        if not self.test_expeditors_user_registration():
            self.log("⚠️  Expeditors user registration failed - IISB tests will be limited")
        
        # 3. Core Note Functionality
        self.log("\n📝 CORE NOTE FUNCTIONALITY")
        
        # Test text note creation
        text_note_id = self.test_create_text_note()
        if not text_note_id:
            self.log("❌ Text note creation failed")
            return False
        
        # Test audio note creation
        audio_note_id = self.test_create_audio_note()
        if not audio_note_id:
            self.log("❌ Audio note creation failed")
            return False
        
        # Test photo note creation
        photo_note_id = self.test_create_photo_note()
        if not photo_note_id:
            self.log("❌ Photo note creation failed")
            return False
        
        # 4. File Upload Functionality
        self.log("\n📁 FILE UPLOAD VERIFICATION")
        
        if not self.test_upload_audio_file(audio_note_id):
            self.log("❌ Audio file upload failed")
            return False
        
        if not self.test_upload_photo_file(photo_note_id):
            self.log("❌ Photo file upload failed")
            return False
        
        if not self.test_direct_file_upload():
            self.log("❌ Direct file upload failed")
            return False
        
        # 5. IISB Feature Verification
        self.log("\n🏢 IISB FEATURE VERIFICATION")
        if not self.test_iisb_analysis_access_control():
            self.log("❌ IISB analysis access control failed")
            return False
        
        # 6. Basic API Endpoints
        self.log("\n🔗 API ENDPOINTS VERIFICATION")
        
        if not self.test_list_notes():
            self.log("❌ Notes listing failed")
            return False
        
        if not self.test_get_note(text_note_id):
            self.log("❌ Note retrieval failed")
            return False
        
        if not self.test_export_functionality(text_note_id):
            self.log("❌ Export functionality failed")
            return False
        
        if not self.test_metrics_endpoint():
            self.log("❌ Metrics endpoint failed")
            return False
        
        # 7. Network Endpoints Removal Verification
        self.log("\n🚫 NETWORK ENDPOINTS REMOVAL VERIFICATION")
        if not self.test_network_endpoints_removed():
            self.log("❌ Network endpoints not properly removed")
            return False
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 NETWORK REMOVAL VERIFICATION SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = NetworkRemovalVerificationTester()
    
    try:
        success = tester.run_verification_test()
        all_passed = tester.print_summary()
        
        if success and all_passed:
            print("\n🎉 VERIFICATION PASSED! Network diagram removal successful.")
            print("✅ Core functionality intact")
            print("✅ No broken imports detected")
            print("✅ IISB feature working for Expeditors users")
            print("✅ Authentication system working")
            print("✅ Note creation (text, audio, photo) working")
            print("✅ Network endpoints properly removed")
            return 0
        else:
            print(f"\n⚠️  VERIFICATION ISSUES DETECTED!")
            print("❌ Some core functionality may be broken after network diagram removal")
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