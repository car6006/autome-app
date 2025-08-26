#!/usr/bin/env python3
"""
OPEN AUTO-ME v1 Backend API Tests
Focused testing for the updated system with Expeditors branding
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class OpenAutoMeV1Tester:
    def __init__(self, base_url="https://transcribe-ocr.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "username": f"testuser_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        self.expeditors_user_data = {
            "email": f"test_expeditors_{int(time.time())}@expeditors.com",
            "username": f"expeditors_user_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "User"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60, auth_required=False, use_expeditors_token=False):
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
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

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

    def test_api_health_check(self):
        """Test API health check endpoint"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        if success:
            message = response.get('message', '')
            self.log(f"   API Message: {message}")
            # Check if it mentions OPEN AUTO-ME v1 or AUTO-ME
            if 'AUTO-ME' in message:
                self.log(f"   ✅ API identifies as AUTO-ME system")
            return True
        return False

    def setup_test_users(self):
        """Setup both regular and Expeditors test users"""
        self.log("\n🔐 Setting up test users...")
        
        # Register regular user
        success, response = self.run_test(
            "Register Regular User",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   Regular user registered: {self.test_user_data['email']}")
        
        # Register Expeditors user
        success2, response2 = self.run_test(
            "Register Expeditors User",
            "POST",
            "auth/register",
            200,
            data=self.expeditors_user_data
        )
        if success2:
            self.expeditors_token = response2.get('access_token')
            self.log(f"   Expeditors user registered: {self.expeditors_user_data['email']}")
        
        return success and success2

    def test_user_authentication(self):
        """Test user authentication endpoints"""
        self.log("\n🔐 TESTING USER AUTHENTICATION")
        
        # Test login with regular user
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        success1, response1 = self.run_test(
            "Regular User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        # Test login with Expeditors user
        expeditors_login_data = {
            "email": self.expeditors_user_data["email"],
            "password": self.expeditors_user_data["password"]
        }
        success2, response2 = self.run_test(
            "Expeditors User Login",
            "POST",
            "auth/login",
            200,
            data=expeditors_login_data
        )
        
        # Test profile retrieval for both users
        success3, response3 = self.run_test(
            "Get Regular User Profile",
            "GET",
            "auth/me",
            200,
            auth_required=True,
            use_expeditors_token=False
        )
        
        success4, response4 = self.run_test(
            "Get Expeditors User Profile",
            "GET",
            "auth/me",
            200,
            auth_required=True,
            use_expeditors_token=True
        )
        
        if success4:
            email = response4.get('email', '')
            self.log(f"   Expeditors user email confirmed: {email}")
            if email.endswith('@expeditors.com'):
                self.log(f"   ✅ Expeditors domain verified")
        
        return success1 and success2 and success3 and success4

    def create_test_note_with_content(self, title, kind, use_expeditors_token=False):
        """Create a note and add content for testing reports"""
        # Create note
        success, response = self.run_test(
            f"Create {kind.title()} Note - {title}",
            "POST",
            "notes",
            200,
            data={"title": title, "kind": kind},
            auth_required=True,
            use_expeditors_token=use_expeditors_token
        )
        
        if not success or 'id' not in response:
            return None
        
        note_id = response['id']
        self.created_notes.append(note_id)
        self.log(f"   Created note ID: {note_id}")
        
        # Add content based on kind
        if kind == "audio":
            # Create dummy audio file with business content
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Write minimal MP3 header for testing
                mp3_header = b'\xff\xfb\x90\x00' + b'\x00' * 100  # Minimal MP3 frame
                tmp_file.write(mp3_header)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('business_meeting.mp3', f, 'audio/mp3')}
                    upload_success, _ = self.run_test(
                        f"Upload Audio Content to Note {note_id[:8]}...",
                        "POST",
                        f"notes/{note_id}/upload",
                        200,
                        files=files,
                        auth_required=True,
                        use_expeditors_token=use_expeditors_token
                    )
                
                os.unlink(tmp_file.name)
                
                if upload_success:
                    # Simulate transcript by directly updating the note (for testing purposes)
                    # In real scenario, this would be done by the transcription service
                    self.log(f"   Audio uploaded successfully for note {note_id[:8]}...")
        
        elif kind == "photo":
            # Create minimal PNG file
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_file.write(png_data)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('business_document.png', f, 'image/png')}
                    upload_success, _ = self.run_test(
                        f"Upload Image Content to Note {note_id[:8]}...",
                        "POST",
                        f"notes/{note_id}/upload",
                        200,
                        files=files,
                        auth_required=True,
                        use_expeditors_token=use_expeditors_token
                    )
                
                os.unlink(tmp_file.name)
                
                if upload_success:
                    self.log(f"   Image uploaded successfully for note {note_id[:8]}...")
        
        return note_id

    def test_file_upload_functionality(self):
        """Test file upload functionality for both audio and image files"""
        self.log("\n📁 TESTING FILE UPLOAD FUNCTIONALITY")
        
        # Test direct file upload endpoint with audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            mp3_header = b'\xff\xfb\x90\x00' + b'\x00' * 100
            tmp_file.write(mp3_header)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_audio.mp3', f, 'audio/mp3')}
                data = {'title': 'Direct Audio Upload Test'}
                success1, response1 = self.run_test(
                    "Direct Audio File Upload",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if success1 and 'id' in response1:
                self.created_notes.append(response1['id'])
                self.log(f"   Audio upload created note: {response1['id']}")
                self.log(f"   File kind: {response1.get('kind', 'N/A')}")
        
        # Test direct file upload endpoint with image
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_image.png', f, 'image/png')}
                data = {'title': 'Direct Image Upload Test'}
                success2, response2 = self.run_test(
                    "Direct Image File Upload",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if success2 and 'id' in response2:
                self.created_notes.append(response2['id'])
                self.log(f"   Image upload created note: {response2['id']}")
                self.log(f"   File kind: {response2.get('kind', 'N/A')}")
        
        # Test unsupported file type
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b'This is a text file')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_file.txt', f, 'text/plain')}
                data = {'title': 'Unsupported File Test'}
                success3, response3 = self.run_test(
                    "Unsupported File Upload (Should Fail)",
                    "POST",
                    "upload-file",
                    400,
                    data=data,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
        
        return success1 and success2 and success3

    def wait_for_note_processing(self, note_id, max_wait=60, use_expeditors_token=False):
        """Wait for note processing to complete or add mock content"""
        self.log(f"⏳ Waiting for note {note_id[:8]}... to process (max {max_wait}s)")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, note_data = self.run_test(
                f"Check Note Status {note_id[:8]}...",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True,
                use_expeditors_token=use_expeditors_token
            )
            
            if success:
                status = note_data.get('status', 'unknown')
                artifacts = note_data.get('artifacts', {})
                
                if status == 'ready' and (artifacts.get('transcript') or artifacts.get('text')):
                    self.log(f"✅ Note processing completed with content!")
                    return True, note_data
                elif status == 'failed':
                    self.log(f"❌ Note processing failed!")
                    return False, note_data
                else:
                    self.log(f"   Status: {status}, waiting...")
                    time.sleep(3)
            else:
                break
        
        # If processing didn't complete, we'll still try to test with mock content
        self.log(f"⏰ Processing timeout - will test with mock content if needed")
        return False, {}

    def test_professional_report_generation_regular_user(self):
        """Test professional report generation for regular users (no Expeditors branding)"""
        self.log("\n📊 TESTING PROFESSIONAL REPORT GENERATION - REGULAR USER")
        
        # Create a note with business content
        note_id = self.create_test_note_with_content(
            "Business Strategy Meeting", 
            "audio", 
            use_expeditors_token=False
        )
        
        if not note_id:
            self.log("❌ Failed to create test note")
            return False
        
        # Wait for processing or add mock content
        processed, note_data = self.wait_for_note_processing(note_id, use_expeditors_token=False)
        
        # Test single note report generation
        success, response = self.run_test(
            "Generate Professional Report - Regular User",
            "POST",
            f"notes/{note_id}/generate-report",
            200,
            auth_required=True,
            use_expeditors_token=False,
            timeout=90
        )
        
        if success:
            report = response.get('report', '')
            is_expeditors = response.get('is_expeditors', False)
            note_title = response.get('note_title', '')
            
            self.log(f"   Report generated for: {note_title}")
            self.log(f"   Report length: {len(report)} characters")
            self.log(f"   Is Expeditors user: {is_expeditors}")
            
            # Check that regular user does NOT get Expeditors branding
            if 'EXPEDITORS INTERNATIONAL' not in report:
                self.log(f"   ✅ No Expeditors branding for regular user")
            else:
                self.log(f"   ❌ Unexpected Expeditors branding found for regular user")
                return False
            
            # Check for required report sections
            required_sections = [
                'EXECUTIVE SUMMARY',
                'KEY INSIGHTS',
                'STRATEGIC RECOMMENDATIONS',
                'ACTION ITEMS',
                'PRIORITIES',
                'FOLLOW-UP'
            ]
            
            sections_found = 0
            for section in required_sections:
                if section in report:
                    sections_found += 1
            
            self.log(f"   Report sections found: {sections_found}/{len(required_sections)}")
            
            if sections_found >= 4:  # At least 4 sections should be present
                self.log(f"   ✅ Professional report structure verified")
                return True
            else:
                self.log(f"   ❌ Insufficient report sections")
                return False
        
        return False

    def test_professional_report_generation_expeditors_user(self):
        """Test professional report generation for Expeditors users (with branding)"""
        self.log("\n📊 TESTING PROFESSIONAL REPORT GENERATION - EXPEDITORS USER")
        
        # Create a note with business content using Expeditors user
        note_id = self.create_test_note_with_content(
            "Supply Chain Analysis Meeting", 
            "audio", 
            use_expeditors_token=True
        )
        
        if not note_id:
            self.log("❌ Failed to create test note")
            return False
        
        # Wait for processing
        processed, note_data = self.wait_for_note_processing(note_id, use_expeditors_token=True)
        
        # Test single note report generation
        success, response = self.run_test(
            "Generate Professional Report - Expeditors User",
            "POST",
            f"notes/{note_id}/generate-report",
            200,
            auth_required=True,
            use_expeditors_token=True,
            timeout=90
        )
        
        if success:
            report = response.get('report', '')
            is_expeditors = response.get('is_expeditors', False)
            note_title = response.get('note_title', '')
            
            self.log(f"   Report generated for: {note_title}")
            self.log(f"   Report length: {len(report)} characters")
            self.log(f"   Is Expeditors user: {is_expeditors}")
            
            # Check that Expeditors user DOES get Expeditors branding
            if 'EXPEDITORS INTERNATIONAL' in report:
                self.log(f"   ✅ Expeditors branding found for Expeditors user")
            else:
                self.log(f"   ❌ Missing Expeditors branding for Expeditors user")
                return False
            
            # Check for professional report header
            if 'Professional Business Report' in report:
                self.log(f"   ✅ Professional report header found")
            else:
                self.log(f"   ❌ Missing professional report header")
            
            # Check for required report sections
            required_sections = [
                'EXECUTIVE SUMMARY',
                'KEY INSIGHTS',
                'STRATEGIC RECOMMENDATIONS',
                'ACTION ITEMS',
                'PRIORITIES',
                'FOLLOW-UP'
            ]
            
            sections_found = 0
            for section in required_sections:
                if section in report:
                    sections_found += 1
            
            self.log(f"   Report sections found: {sections_found}/{len(required_sections)}")
            
            if sections_found >= 4:  # At least 4 sections should be present
                self.log(f"   ✅ Professional report structure verified")
                return True
            else:
                self.log(f"   ❌ Insufficient report sections")
                return False
        
        return False

    def test_batch_report_generation(self):
        """Test batch report generation with Expeditors branding"""
        self.log("\n📊 TESTING BATCH REPORT GENERATION")
        
        # Create multiple notes for batch processing
        note_ids = []
        
        # Create notes with Expeditors user
        for i, title in enumerate([
            "Q4 Supply Chain Review",
            "Client Logistics Analysis", 
            "Operational Efficiency Meeting"
        ]):
            note_id = self.create_test_note_with_content(
                title, 
                "audio" if i % 2 == 0 else "photo", 
                use_expeditors_token=True
            )
            if note_id:
                note_ids.append(note_id)
        
        if len(note_ids) < 2:
            self.log("❌ Failed to create sufficient test notes for batch report")
            return False
        
        self.log(f"   Created {len(note_ids)} notes for batch processing")
        
        # Wait a bit for any processing
        time.sleep(5)
        
        # Test batch report generation
        success, response = self.run_test(
            "Generate Batch Report - Expeditors User",
            "POST",
            "notes/batch-report",
            200,
            data=note_ids,
            auth_required=True,
            use_expeditors_token=True,
            timeout=120
        )
        
        if success:
            report = response.get('report', '')
            is_expeditors = response.get('is_expeditors', False)
            title = response.get('title', '')
            source_notes = response.get('source_notes', [])
            note_count = response.get('note_count', 0)
            
            self.log(f"   Batch report title: {title}")
            self.log(f"   Report length: {len(report)} characters")
            self.log(f"   Source notes: {note_count}")
            self.log(f"   Is Expeditors user: {is_expeditors}")
            
            # Check that Expeditors user gets Expeditors branding in batch report
            if 'EXPEDITORS INTERNATIONAL' in report:
                self.log(f"   ✅ Expeditors branding found in batch report")
            else:
                self.log(f"   ❌ Missing Expeditors branding in batch report")
                return False
            
            # Check for comprehensive business analysis header
            if 'Comprehensive Business Analysis Report' in report:
                self.log(f"   ✅ Comprehensive analysis header found")
            else:
                self.log(f"   ❌ Missing comprehensive analysis header")
            
            # Check for batch-specific sections
            batch_sections = [
                'EXECUTIVE SUMMARY',
                'COMPREHENSIVE ANALYSIS',
                'STRATEGIC RECOMMENDATIONS',
                'IMPLEMENTATION ROADMAP',
                'RISK ASSESSMENT',
                'STAKEHOLDER INVOLVEMENT'
            ]
            
            sections_found = 0
            for section in batch_sections:
                if section in report:
                    sections_found += 1
            
            self.log(f"   Batch report sections found: {sections_found}/{len(batch_sections)}")
            
            if sections_found >= 4:  # At least 4 sections should be present
                self.log(f"   ✅ Batch report structure verified")
                return True
            else:
                self.log(f"   ❌ Insufficient batch report sections")
                return False
        
        return False

    def test_notes_crud_operations(self):
        """Test basic CRUD operations for notes"""
        self.log("\n📝 TESTING NOTES CRUD OPERATIONS")
        
        # Create note
        success1, response1 = self.run_test(
            "Create Note for CRUD Test",
            "POST",
            "notes",
            200,
            data={"title": "CRUD Test Note", "kind": "photo"},
            auth_required=True
        )
        
        if not success1 or 'id' not in response1:
            return False
        
        note_id = response1['id']
        self.created_notes.append(note_id)
        
        # Read note
        success2, response2 = self.run_test(
            "Read Note",
            "GET",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        
        # List notes
        success3, response3 = self.run_test(
            "List Notes",
            "GET",
            "notes",
            200,
            auth_required=True
        )
        
        # Delete note
        success4, response4 = self.run_test(
            "Delete Note",
            "DELETE",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        
        if success4:
            # Remove from our tracking since it's deleted
            self.created_notes.remove(note_id)
        
        return success1 and success2 and success3 and success4

    def run_comprehensive_test(self):
        """Run all OPEN AUTO-ME v1 specific tests"""
        self.log("🚀 Starting OPEN AUTO-ME v1 Comprehensive Backend Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Test 1: Basic API Health
        if not self.test_api_health_check():
            self.log("❌ API health check failed - stopping tests")
            return False
        
        # Test 2: Setup test users
        if not self.setup_test_users():
            self.log("❌ User setup failed - stopping tests")
            return False
        
        # Test 3: User Authentication
        if not self.test_user_authentication():
            self.log("❌ User authentication tests failed")
            return False
        
        # Test 4: File Upload Functionality
        if not self.test_file_upload_functionality():
            self.log("❌ File upload functionality tests failed")
            return False
        
        # Test 5: Notes CRUD Operations
        if not self.test_notes_crud_operations():
            self.log("❌ Notes CRUD operations failed")
            return False
        
        # Test 6: Professional Report Generation - Regular User
        if not self.test_professional_report_generation_regular_user():
            self.log("❌ Professional report generation for regular user failed")
            return False
        
        # Test 7: Professional Report Generation - Expeditors User
        if not self.test_professional_report_generation_expeditors_user():
            self.log("❌ Professional report generation for Expeditors user failed")
            return False
        
        # Test 8: Batch Report Generation
        if not self.test_batch_report_generation():
            self.log("❌ Batch report generation failed")
            return False
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 OPEN AUTO-ME v1 TEST SUMMARY")
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
    tester = OpenAutoMeV1Tester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 All OPEN AUTO-ME v1 tests passed! Backend API is working correctly.")
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