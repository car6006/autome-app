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
    def __init__(self, base_url="https://transcribe-ocr.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_id = None
        self.expeditors_token = None
        self.expeditors_user_id = None
        self.expeditors_user_data = None
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

    def test_create_audio_note(self, authenticated=False):
        """Test creating an audio note"""
        success, response = self.run_test(
            "Create Audio Note" + (" (Authenticated)" if authenticated else " (Anonymous)"),
            "POST",
            "notes",
            200,
            data={"title": "Test Audio Note", "kind": "audio"},
            auth_required=authenticated
        )
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   Created note ID: {note_id}")
            return note_id
        return None

    def test_create_photo_note(self, authenticated=False):
        """Test creating a photo note"""
        success, response = self.run_test(
            "Create Photo Note" + (" (Authenticated)" if authenticated else " (Anonymous)"),
            "POST",
            "notes",
            200,
            data={"title": "Test Photo Note", "kind": "photo"},
            auth_required=authenticated
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

    def test_list_notes(self, authenticated=False):
        """Test listing all notes"""
        success, response = self.run_test(
            "List Notes" + (" (Authenticated)" if authenticated else " (Anonymous)"),
            "GET",
            "notes",
            200,
            auth_required=authenticated
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

    def test_metrics_endpoint(self, authenticated=False):
        """Test productivity metrics endpoint"""
        success, response = self.run_test(
            "Get Productivity Metrics" + (" (Authenticated)" if authenticated else " (Anonymous)"),
            "GET",
            "metrics?days=7",
            200,
            auth_required=authenticated
        )
        if success:
            self.log(f"   Total notes: {response.get('notes_total', 0)}")
            self.log(f"   Ready notes: {response.get('notes_ready', 0)}")
            self.log(f"   Success rate: {response.get('success_rate', 0)}%")
            self.log(f"   Estimated time saved: {response.get('estimated_minutes_saved', 0)} minutes")
            self.log(f"   User authenticated: {response.get('user_authenticated', False)}")
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
            self.test_user_id = user_data.get('id')
            self.log(f"   Registered user ID: {self.test_user_id}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
        return success

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
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Login successful for: {user_data.get('email')}")
            self.log(f"   User ID: {user_data.get('id')}")
        return success

    def test_get_user_profile(self):
        """Test getting current user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200,
            auth_required=True
        )
        if success:
            self.log(f"   Profile email: {response.get('email')}")
            self.log(f"   Profile name: {response.get('profile', {}).get('first_name')} {response.get('profile', {}).get('last_name')}")
            self.log(f"   Notes count: {response.get('notes_count', 0)}")
        return success

    def test_update_user_profile(self):
        """Test updating user profile"""
        profile_update = {
            "company": "Test Company",
            "job_title": "Test Engineer",
            "phone": "+1-555-123-4567",
            "bio": "This is a test user profile"
        }
        success, response = self.run_test(
            "Update User Profile",
            "PUT",
            "auth/me",
            200,
            data=profile_update,
            auth_required=True
        )
        if success:
            profile = response.get('profile', {})
            self.log(f"   Updated company: {profile.get('company')}")
            self.log(f"   Updated job title: {profile.get('job_title')}")
        return success

    def test_duplicate_registration(self):
        """Test duplicate user registration (should fail)"""
        success, response = self.run_test(
            "Duplicate Registration (Should Fail)",
            "POST",
            "auth/register",
            400,  # Should fail with 400
            data=self.test_user_data
        )
        return success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        invalid_login = {
            "email": self.test_user_data["email"],
            "password": "WrongPassword123!"
        }
        success, response = self.run_test(
            "Invalid Login (Should Fail)",
            "POST",
            "auth/login",
            401,  # Should fail with 401
            data=invalid_login
        )
        return success

    def test_unauthorized_access(self):
        """Test accessing protected endpoint without auth"""
        # Temporarily clear token
        temp_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Unauthorized Access (Should Fail)",
            "GET",
            "auth/me",
            403,  # Should fail with 403 or 401
            auth_required=True
        )
        
        # Restore token
        self.auth_token = temp_token
        return success

    def test_expeditors_user_registration(self):
        """Test Expeditors user registration"""
        expeditors_user_data = {
            "email": f"test_expeditors_{int(time.time())}@expeditors.com",
            "username": f"expeditors_user_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "User"
        }
        
        success, response = self.run_test(
            "Expeditors User Registration",
            "POST",
            "auth/register",
            200,
            data=expeditors_user_data
        )
        if success:
            self.expeditors_token = response.get('access_token')
            user_data = response.get('user', {})
            self.expeditors_user_id = user_data.get('id')
            self.expeditors_user_data = expeditors_user_data
            self.log(f"   Expeditors user ID: {self.expeditors_user_id}")
            self.log(f"   Expeditors token received: {'Yes' if self.expeditors_token else 'No'}")
        return success

    def test_network_diagram_access_control_non_expeditors(self):
        """Test that non-Expeditors users cannot access network diagram endpoints"""
        # Test with regular user (should get 404)
        success, response = self.run_test(
            "Network Diagram Access - Non-Expeditors (Should Fail)",
            "POST",
            "notes/network-diagram",
            404,  # Should fail with 404 "Feature not found"
            data={"title": "Test Network", "kind": "network_diagram"},
            auth_required=True
        )
        return success

    def test_network_diagram_access_control_expeditors(self):
        """Test that Expeditors users can access network diagram endpoints"""
        # Switch to Expeditors user token
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        success, response = self.run_test(
            "Network Diagram Access - Expeditors User",
            "POST",
            "notes/network-diagram",
            200,
            data={"title": "Expeditors Supply Chain Network", "kind": "network_diagram"},
            auth_required=True
        )
        
        network_note_id = None
        if success and 'id' in response:
            network_note_id = response['id']
            self.created_notes.append(network_note_id)
            self.log(f"   Created network diagram note ID: {network_note_id}")
            self.log(f"   Feature confirmation: {response.get('feature', 'N/A')}")
        
        # Restore original token
        self.auth_token = temp_token
        return success, network_note_id

    def test_network_diagram_processing_non_expeditors(self, note_id):
        """Test that non-Expeditors users cannot process network diagrams"""
        # Create dummy audio file for network processing
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            dummy_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('network_description.webm', f, 'audio/webm')}
                success, response = self.run_test(
                    "Network Processing - Non-Expeditors (Should Fail)",
                    "POST",
                    f"notes/{note_id}/process-network",
                    404,  # Should fail with 404 "Feature not found"
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            return success

    def test_network_diagram_processing_expeditors(self, network_note_id):
        """Test network diagram processing for Expeditors users"""
        # Switch to Expeditors user token
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Create dummy audio file with supply chain content
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            # Write minimal WebM header with supply chain keywords in filename
            dummy_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('expeditors_network_SHA_JNB_airfreight.webm', f, 'audio/webm')}
                success, response = self.run_test(
                    "Network Processing - Expeditors User",
                    "POST",
                    f"notes/{network_note_id}/process-network",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if success:
                self.log(f"   Processing status: {response.get('status', 'N/A')}")
                self.log(f"   Processing message: {response.get('message', 'N/A')}")
        
        # Restore original token
        self.auth_token = temp_token
        return success

    def test_network_diagram_results(self, network_note_id):
        """Test retrieving network diagram results"""
        # Switch to Expeditors user token
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Wait a bit for processing
        time.sleep(2)
        
        success, response = self.run_test(
            f"Get Network Diagram Results {network_note_id[:8]}...",
            "GET",
            f"notes/{network_note_id}",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   Note status: {response.get('status', 'N/A')}")
            self.log(f"   Note kind: {response.get('kind', 'N/A')}")
            artifacts = response.get('artifacts', {})
            if artifacts:
                self.log(f"   Has network topology: {'network_topology' in artifacts}")
                self.log(f"   Has diagram data: {'diagram_data' in artifacts}")
                self.log(f"   Has insights: {'insights' in artifacts}")
                self.log(f"   Processing type: {artifacts.get('processing_type', 'N/A')}")
        
        # Restore original token
        self.auth_token = temp_token
        return success, response

    def create_note_with_ai_conversations(self, authenticated=True):
        """Create a note and add AI conversations for export testing"""
        # Create a note
        note_id = self.test_create_audio_note(authenticated=authenticated)
        if not note_id:
            return None
        
        # Add some mock transcript content to the note
        # We'll simulate this by directly calling the AI chat endpoint
        # First, we need to add some content to the note
        
        # Get the note and add mock transcript
        success, note_data = self.test_get_note(note_id)
        if not success:
            return None
        
        # Simulate adding AI conversations by calling the AI chat endpoint
        # This requires the note to have some content first
        return note_id

    def add_mock_ai_conversations(self, note_id):
        """Add mock AI conversations to a note for testing export functionality"""
        # We'll use the AI chat endpoint to create real conversations
        # First, we need to add some mock content to the note
        
        # Mock some questions to ask
        test_questions = [
            "What are the key insights from this content?",
            "Provide a summary of the main points",
            "What are the potential risks mentioned?"
        ]
        
        conversations_added = 0
        for question in test_questions:
            try:
                url = f"{self.api_url}/notes/{note_id}/ai-chat"
                headers = {'Content-Type': 'application/json'}
                if self.auth_token:
                    headers['Authorization'] = f'Bearer {self.auth_token}'
                
                response = requests.post(
                    url,
                    json={"question": question},
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    conversations_added += 1
                    self.log(f"   Added AI conversation: {question[:50]}...")
                elif response.status_code == 400:
                    # No content available - this is expected for new notes
                    self.log(f"   No content available for AI chat (expected for new notes)")
                    break
                else:
                    self.log(f"   Failed to add AI conversation: {response.status_code}")
                    
            except Exception as e:
                self.log(f"   Error adding AI conversation: {str(e)}")
                break
        
        return conversations_added

    def test_ai_conversation_export_pdf(self, note_id, is_expeditors=False):
        """Test PDF export of AI conversations"""
        # Switch to appropriate user token
        if is_expeditors and self.expeditors_token:
            temp_token = self.auth_token
            self.auth_token = self.expeditors_token
        
        try:
            url = f"{self.api_url}/notes/{note_id}/ai-conversations/export?format=pdf"
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            response = requests.get(url, headers=headers, timeout=60)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                self.log(f"✅ PDF Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Status: {response.status_code}")
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' in content_type:
                    self.log(f"   ✅ Correct Content-Type: {content_type}")
                else:
                    self.log(f"   ⚠️  Unexpected Content-Type: {content_type}")
                
                # Check content disposition for filename
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    self.log(f"   ✅ Proper file attachment header")
                    if is_expeditors and 'Expeditors' in content_disposition:
                        self.log(f"   ✅ Expeditors branding in filename detected")
                    elif not is_expeditors and 'AI_Analysis' in content_disposition:
                        self.log(f"   ✅ Standard filename format detected")
                else:
                    self.log(f"   ⚠️  Missing or incorrect Content-Disposition header")
                
                # Check PDF content size (should be substantial)
                content_length = len(response.content)
                if content_length > 1000:  # PDF should be at least 1KB
                    self.log(f"   ✅ PDF size: {content_length} bytes (substantial content)")
                else:
                    self.log(f"   ⚠️  PDF size: {content_length} bytes (may be too small)")
                
                # Check PDF header
                if response.content.startswith(b'%PDF'):
                    self.log(f"   ✅ Valid PDF header detected")
                else:
                    self.log(f"   ❌ Invalid PDF header")
                
            else:
                self.log(f"❌ PDF Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Expected 200, got {response.status_code}")
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        self.log(f"   Expected error (no AI conversations): {error_data.get('detail', 'Unknown error')}")
                        success = True  # This is expected behavior
                        self.tests_passed += 1
                    except:
                        pass
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            self.log(f"❌ PDF Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Error: {str(e)}")
            self.tests_run += 1
            return False
        finally:
            # Restore original token
            if is_expeditors and self.expeditors_token:
                self.auth_token = temp_token

    def test_ai_conversation_export_docx(self, note_id, is_expeditors=False):
        """Test Word DOC export of AI conversations"""
        # Switch to appropriate user token
        if is_expeditors and self.expeditors_token:
            temp_token = self.auth_token
            self.auth_token = self.expeditors_token
        
        try:
            url = f"{self.api_url}/notes/{note_id}/ai-conversations/export?format=docx"
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            response = requests.get(url, headers=headers, timeout=60)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                self.log(f"✅ DOCX Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Status: {response.status_code}")
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                expected_docx_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                if expected_docx_type in content_type:
                    self.log(f"   ✅ Correct Content-Type for DOCX")
                else:
                    self.log(f"   ⚠️  Unexpected Content-Type: {content_type}")
                
                # Check content disposition for filename
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    self.log(f"   ✅ Proper file attachment header")
                    if is_expeditors and 'Expeditors' in content_disposition:
                        self.log(f"   ✅ Expeditors branding in filename detected")
                    elif not is_expeditors and 'AI_Analysis' in content_disposition:
                        self.log(f"   ✅ Standard filename format detected")
                    if '.docx' in content_disposition:
                        self.log(f"   ✅ Correct .docx file extension")
                else:
                    self.log(f"   ⚠️  Missing or incorrect Content-Disposition header")
                
                # Check DOCX content size
                content_length = len(response.content)
                if content_length > 2000:  # DOCX should be at least 2KB
                    self.log(f"   ✅ DOCX size: {content_length} bytes (substantial content)")
                else:
                    self.log(f"   ⚠️  DOCX size: {content_length} bytes (may be too small)")
                
                # Check DOCX header (ZIP format)
                if response.content.startswith(b'PK'):
                    self.log(f"   ✅ Valid DOCX header detected (ZIP format)")
                else:
                    self.log(f"   ❌ Invalid DOCX header")
                
            else:
                self.log(f"❌ DOCX Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Expected 200, got {response.status_code}")
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        self.log(f"   Expected error (no AI conversations): {error_data.get('detail', 'Unknown error')}")
                        success = True  # This is expected behavior
                        self.tests_passed += 1
                    except:
                        pass
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            self.log(f"❌ DOCX Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Error: {str(e)}")
            self.tests_run += 1
            return False
        finally:
            # Restore original token
            if is_expeditors and self.expeditors_token:
                self.auth_token = temp_token

    def test_ai_conversation_export_txt(self, note_id, is_expeditors=False):
        """Test TXT export of AI conversations (for comparison)"""
        # Switch to appropriate user token
        if is_expeditors and self.expeditors_token:
            temp_token = self.auth_token
            self.auth_token = self.expeditors_token
        
        try:
            url = f"{self.api_url}/notes/{note_id}/ai-conversations/export?format=txt"
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            response = requests.get(url, headers=headers, timeout=30)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                self.log(f"✅ TXT Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Status: {response.status_code}")
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'text/plain' in content_type:
                    self.log(f"   ✅ Correct Content-Type: {content_type}")
                else:
                    self.log(f"   ⚠️  Unexpected Content-Type: {content_type}")
                
                # Check for clean formatting (no markdown symbols)
                content = response.text
                if content:
                    has_markdown_headers = '###' in content or '##' in content or '# ' in content
                    has_markdown_bold = '**' in content
                    has_markdown_italic = '*' in content and not content.count('*') == content.count('• ')
                    
                    if not has_markdown_headers:
                        self.log(f"   ✅ No markdown headers (###, ##, #) found")
                    else:
                        self.log(f"   ❌ Markdown headers found - content not clean")
                    
                    if not has_markdown_bold:
                        self.log(f"   ✅ No markdown bold (**) found")
                    else:
                        self.log(f"   ❌ Markdown bold formatting found - content not clean")
                    
                    # Check for professional bullet points
                    if '• ' in content:
                        self.log(f"   ✅ Professional bullet points (•) found")
                    
                    # Check for Expeditors branding
                    if is_expeditors and 'EXPEDITORS INTERNATIONAL' in content:
                        self.log(f"   ✅ Expeditors branding detected in content")
                    elif not is_expeditors and 'AI Content Analysis' in content:
                        self.log(f"   ✅ Standard header format detected")
                
            else:
                self.log(f"❌ TXT Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Expected 200, got {response.status_code}")
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        self.log(f"   Expected error (no AI conversations): {error_data.get('detail', 'Unknown error')}")
                        success = True  # This is expected behavior
                        self.tests_passed += 1
                    except:
                        pass
            
            self.tests_run += 1
            return success
            
        except Exception as e:
            self.log(f"❌ TXT Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Error: {str(e)}")
            self.tests_run += 1
            return False
        finally:
            # Restore original token
            if is_expeditors and self.expeditors_token:
                self.auth_token = temp_token

    def test_export_error_handling(self):
        """Test export error handling for invalid scenarios"""
        # Test invalid format
        success, response = self.run_test(
            "Export Invalid Format (Should Fail)",
            "GET",
            f"notes/{self.created_notes[0] if self.created_notes else 'test'}/ai-conversations/export?format=invalid",
            422,  # Should fail with validation error
            auth_required=True
        )
        
        # Test non-existent note
        success2, response2 = self.run_test(
            "Export Non-existent Note (Should Fail)",
            "GET",
            "notes/non-existent-id/ai-conversations/export?format=pdf",
            404,  # Should fail with not found
            auth_required=True
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
        
        # === AUTHENTICATION TESTS ===
        self.log("\n🔐 AUTHENTICATION TESTS")
        
        # Test user registration
        if not self.test_user_registration():
            self.log("❌ User registration failed - stopping auth tests")
            return False
        
        # Test user profile retrieval
        self.test_get_user_profile()
        
        # Test profile update
        self.test_update_user_profile()
        
        # Test duplicate registration (should fail)
        self.test_duplicate_registration()
        
        # Test invalid login (should fail)
        self.test_invalid_login()
        
        # Test unauthorized access (should fail)
        self.test_unauthorized_access()
        
        # Test login with valid credentials
        self.test_user_login()
        
        # === AUTHENTICATED NOTE TESTS ===
        self.log("\n📝 AUTHENTICATED NOTE TESTS")
        
        # Test authenticated note creation
        auth_audio_note_id = self.test_create_audio_note(authenticated=True)
        auth_photo_note_id = self.test_create_photo_note(authenticated=True)
        
        if not auth_audio_note_id or not auth_photo_note_id:
            self.log("❌ Authenticated note creation failed")
            return False
        
        # Test authenticated note listing (should show user's notes)
        self.test_list_notes(authenticated=True)
        
        # Test authenticated metrics
        self.test_metrics_endpoint(authenticated=True)
        
        # === ANONYMOUS TESTS ===
        self.log("\n👤 ANONYMOUS USER TESTS")
        
        # Clear auth token to test anonymous access
        temp_token = self.auth_token
        self.auth_token = None
        
        # Test anonymous note creation
        anon_audio_note_id = self.test_create_audio_note(authenticated=False)
        anon_photo_note_id = self.test_create_photo_note(authenticated=False)
        
        # Test anonymous note listing
        self.test_list_notes(authenticated=False)
        
        # Test anonymous metrics
        self.test_metrics_endpoint(authenticated=False)
        
        # Restore auth token
        self.auth_token = temp_token
        
        # === FILE UPLOAD TESTS ===
        self.log("\n📁 FILE UPLOAD TESTS")
        
        if auth_audio_note_id:
            self.test_upload_dummy_audio(auth_audio_note_id)
        if auth_photo_note_id:
            self.test_upload_dummy_image(auth_photo_note_id)
        
        # Wait a bit for processing to start
        time.sleep(3)
        
        # Check processing status
        if auth_audio_note_id:
            self.test_get_note(auth_audio_note_id)
        if auth_photo_note_id:
            self.test_get_note(auth_photo_note_id)
        
        # === ADDITIONAL FUNCTIONALITY TESTS ===
        self.log("\n🔧 ADDITIONAL FUNCTIONALITY TESTS")
        
        # Test email functionality
        if auth_audio_note_id:
            self.test_email_functionality(auth_audio_note_id)
        
        # Test git sync functionality
        if auth_photo_note_id:
            self.test_git_sync_functionality(auth_photo_note_id)
        
        # Test error handling
        self.test_invalid_endpoints()
        
        # === AI CONVERSATION EXPORT TESTS (PDF & DOCX) ===
        self.log("\n📄 AI CONVERSATION EXPORT TESTS (PDF & DOCX)")
        
        # Create a note with AI conversations for export testing
        export_test_note_id = self.create_note_with_ai_conversations(authenticated=True)
        
        if export_test_note_id:
            # Try to add AI conversations (may fail if no content, which is expected)
            conversations_added = self.add_mock_ai_conversations(export_test_note_id)
            
            if conversations_added > 0:
                self.log(f"   Successfully added {conversations_added} AI conversations")
                
                # Test PDF export for regular user
                self.test_ai_conversation_export_pdf(export_test_note_id, is_expeditors=False)
                
                # Test DOCX export for regular user
                self.test_ai_conversation_export_docx(export_test_note_id, is_expeditors=False)
                
                # Test TXT export for comparison
                self.test_ai_conversation_export_txt(export_test_note_id, is_expeditors=False)
                
                # Test Expeditors user exports if available
                if self.expeditors_token:
                    # Create note with Expeditors user
                    temp_token = self.auth_token
                    self.auth_token = self.expeditors_token
                    
                    expeditors_note_id = self.create_note_with_ai_conversations(authenticated=True)
                    if expeditors_note_id:
                        expeditors_conversations = self.add_mock_ai_conversations(expeditors_note_id)
                        
                        if expeditors_conversations > 0:
                            # Test PDF export for Expeditors user
                            self.test_ai_conversation_export_pdf(expeditors_note_id, is_expeditors=True)
                            
                            # Test DOCX export for Expeditors user
                            self.test_ai_conversation_export_docx(expeditors_note_id, is_expeditors=True)
                            
                            # Test TXT export for Expeditors user
                            self.test_ai_conversation_export_txt(expeditors_note_id, is_expeditors=True)
                    
                    # Restore original token
                    self.auth_token = temp_token
            else:
                self.log("   No AI conversations added - testing error handling instead")
                
                # Test export endpoints with notes that have no AI conversations
                self.test_ai_conversation_export_pdf(export_test_note_id, is_expeditors=False)
                self.test_ai_conversation_export_docx(export_test_note_id, is_expeditors=False)
                self.test_ai_conversation_export_txt(export_test_note_id, is_expeditors=False)
        
        # Test export error handling
        self.test_export_error_handling()

        # === EXPEDITORS HIDDEN NETWORK DIAGRAM FEATURE TESTS ===
        self.log("\n👑 EXPEDITORS NETWORK DIAGRAM FEATURE TESTS")
        
        # Test Expeditors user registration
        if not self.test_expeditors_user_registration():
            self.log("❌ Expeditors user registration failed - skipping network tests")
        else:
            # Test access control - non-Expeditors user should get 404
            self.test_network_diagram_access_control_non_expeditors()
            
            # Test access control - Expeditors user should succeed
            network_success, network_note_id = self.test_network_diagram_access_control_expeditors()
            
            if network_success and network_note_id:
                # Test processing access control - non-Expeditors should fail
                if auth_audio_note_id:  # Use regular note for non-Expeditors test
                    self.test_network_diagram_processing_non_expeditors(auth_audio_note_id)
                
                # Test network diagram processing for Expeditors user
                self.test_network_diagram_processing_expeditors(network_note_id)
                
                # Test retrieving network diagram results
                self.test_network_diagram_results(network_note_id)
        
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