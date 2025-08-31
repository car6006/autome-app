#!/usr/bin/env python3
"""
Focused Backend Tests for AUTO-ME Review Request
Tests specific areas mentioned in the review request:
1. Notes Processing Fix
2. Email Delivery 
3. File Upload for Scan
4. Export Functionality
5. Error Handling
"""

import requests
import sys
import json
import time
import tempfile
import os
from datetime import datetime
from pathlib import Path

class FocusedBackendTester:
    def __init__(self, base_url="https://typescript-auth.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"focused_test_{int(time.time())}@example.com",
            "username": f"focuseduser_{int(time.time())}",
            "password": "FocusedTest123!",
            "first_name": "Focused",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

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
        """Setup authentication for tests"""
        self.log("🔐 Setting up authentication...")
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
        return False

    def test_notes_processing_fix(self):
        """Test 1: Notes Processing Fix - Test creating audio and photo notes"""
        self.log("\n🎵 TESTING NOTES PROCESSING FIX")
        
        # Create audio note
        success, response = self.run_test(
            "Create Audio Note for Processing Test",
            "POST",
            "notes",
            200,
            data={"title": "Audio Processing Test", "kind": "audio"},
            auth_required=True
        )
        
        audio_note_id = None
        if success and 'id' in response:
            audio_note_id = response['id']
            self.created_notes.append(audio_note_id)
            self.log(f"   Created audio note ID: {audio_note_id}")
        
        # Create photo note
        success, response = self.run_test(
            "Create Photo Note for Processing Test",
            "POST",
            "notes",
            200,
            data={"title": "Photo Processing Test", "kind": "photo"},
            auth_required=True
        )
        
        photo_note_id = None
        if success and 'id' in response:
            photo_note_id = response['id']
            self.created_notes.append(photo_note_id)
            self.log(f"   Created photo note ID: {photo_note_id}")
        
        # Upload files and test processing
        processing_results = []
        
        if audio_note_id:
            # Upload audio file
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
                # Create a more realistic WebM file header
                webm_header = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm\x42\x87\x81\x02\x42\x85\x81\x02'
                tmp_file.write(webm_header)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('processing_test.webm', f, 'audio/webm')}
                    success, response = self.run_test(
                        "Upload Audio for Processing",
                        "POST",
                        f"notes/{audio_note_id}/upload",
                        200,
                        files=files,
                        auth_required=True
                    )
                    if success:
                        self.log(f"   Audio upload successful, status: {response.get('status', 'unknown')}")
                
                os.unlink(tmp_file.name)
            
            # Wait and check processing status
            time.sleep(5)
            success, note_data = self.run_test(
                "Check Audio Note Processing Status",
                "GET",
                f"notes/{audio_note_id}",
                200,
                auth_required=True
            )
            if success:
                status = note_data.get('status', 'unknown')
                self.log(f"   Audio note status after processing: {status}")
                processing_results.append(('audio', status, note_data.get('artifacts', {})))
                
                # Check if stuck in processing
                if status == 'processing':
                    self.log(f"   ⚠️  Audio note stuck in processing state!")
                elif status == 'ready':
                    self.log(f"   ✅ Audio note processed successfully")
                elif status == 'failed':
                    self.log(f"   ❌ Audio note processing failed")
                    artifacts = note_data.get('artifacts', {})
                    if 'error' in artifacts:
                        self.log(f"   Error details: {artifacts['error']}")
        
        if photo_note_id:
            # Upload image file
            # Create a minimal PNG file (1x1 pixel)
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_file.write(png_data)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('processing_test.png', f, 'image/png')}
                    success, response = self.run_test(
                        "Upload Image for Processing",
                        "POST",
                        f"notes/{photo_note_id}/upload",
                        200,
                        files=files,
                        auth_required=True
                    )
                    if success:
                        self.log(f"   Image upload successful, status: {response.get('status', 'unknown')}")
                
                os.unlink(tmp_file.name)
            
            # Wait and check processing status
            time.sleep(5)
            success, note_data = self.run_test(
                "Check Photo Note Processing Status",
                "GET",
                f"notes/{photo_note_id}",
                200,
                auth_required=True
            )
            if success:
                status = note_data.get('status', 'unknown')
                self.log(f"   Photo note status after processing: {status}")
                processing_results.append(('photo', status, note_data.get('artifacts', {})))
                
                # Check if stuck in processing
                if status == 'processing':
                    self.log(f"   ⚠️  Photo note stuck in processing state!")
                elif status == 'ready':
                    self.log(f"   ✅ Photo note processed successfully")
                elif status == 'failed':
                    self.log(f"   ❌ Photo note processing failed")
                    artifacts = note_data.get('artifacts', {})
                    if 'error' in artifacts:
                        self.log(f"   Error details: {artifacts['error']}")
        
        return processing_results

    def test_email_delivery(self):
        """Test 2: Email Delivery - Test email sending functionality"""
        self.log("\n📧 TESTING EMAIL DELIVERY")
        
        # Create a note first
        success, response = self.run_test(
            "Create Note for Email Test",
            "POST",
            "notes",
            200,
            data={"title": "Email Test Note", "kind": "photo"},
            auth_required=True
        )
        
        note_id = None
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
        
        if not note_id:
            self.log("   ❌ Failed to create note for email test")
            return False
        
        # Test email sending
        email_data = {
            "to": ["test@example.com", "another@example.com"],
            "subject": "AUTO-ME Test Email - Processing Results"
        }
        
        success, response = self.run_test(
            "Send Email via API",
            "POST",
            f"notes/{note_id}/email",
            200,
            data=email_data,
            auth_required=True
        )
        
        if success:
            self.log(f"   Email queued successfully: {response.get('message', 'No message')}")
            
            # Test with invalid email data
            invalid_email_data = {
                "to": [],  # Empty recipient list
                "subject": "Test"
            }
            
            success2, response2 = self.run_test(
                "Send Email with Empty Recipients",
                "POST",
                f"notes/{note_id}/email",
                200,  # Should still return 200 but handle gracefully
                data=invalid_email_data,
                auth_required=True
            )
            
            return success and success2
        
        return False

    def test_file_upload_for_scan(self):
        """Test 3: File Upload for Scan - Test the new /api/upload-file endpoint"""
        self.log("\n📁 TESTING FILE UPLOAD FOR SCAN")
        
        # Test various image formats
        test_files = [
            ('test.jpg', b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9', 'image/jpeg'),
            ('test.png', b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82', 'image/png'),
            ('test.pdf', b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF', 'application/pdf')
        ]
        
        upload_results = []
        
        for filename, file_data, content_type in test_files:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(file_data)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (filename, f, content_type)}
                    form_data = {'title': f'Scan Upload Test - {filename}'}
                    
                    success, response = self.run_test(
                        f"Upload {filename} for Scan",
                        "POST",
                        "upload-file",
                        200,
                        data=form_data,
                        files=files,
                        auth_required=True
                    )
                    
                    if success:
                        note_id = response.get('id')
                        if note_id:
                            self.created_notes.append(note_id)
                            self.log(f"   Created note ID: {note_id}")
                            self.log(f"   Upload status: {response.get('status', 'unknown')}")
                            self.log(f"   Filename: {response.get('filename', 'unknown')}")
                            upload_results.append((filename, True, note_id))
                        else:
                            upload_results.append((filename, False, None))
                    else:
                        upload_results.append((filename, False, None))
                
                os.unlink(tmp_file.name)
        
        # Test unsupported file type
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b'This is a text file')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                form_data = {'title': 'Unsupported File Test'}
                
                success, response = self.run_test(
                    "Upload Unsupported File Type (Should Fail)",
                    "POST",
                    "upload-file",
                    400,  # Should fail with 400
                    data=form_data,
                    files=files,
                    auth_required=True
                )
                
                if success:
                    self.log(f"   Correctly rejected unsupported file type")
            
            os.unlink(tmp_file.name)
        
        return upload_results

    def test_export_functionality(self):
        """Test 4: Export Functionality - Test the /api/notes/{note_id}/export endpoint"""
        self.log("\n📤 TESTING EXPORT FUNCTIONALITY")
        
        # Create a note with some content
        success, response = self.run_test(
            "Create Note for Export Test",
            "POST",
            "notes",
            200,
            data={"title": "Export Test Note", "kind": "photo"},
            auth_required=True
        )
        
        note_id = None
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
        
        if not note_id:
            self.log("   ❌ Failed to create note for export test")
            return False
        
        # Test different export formats
        export_formats = ['txt', 'md', 'json']
        export_results = []
        
        for format_type in export_formats:
            success, response = self.run_test(
                f"Export Note as {format_type.upper()}",
                "GET",
                f"notes/{note_id}/export?format={format_type}",
                200,
                auth_required=True
            )
            
            if success:
                if format_type == 'json':
                    # JSON response should have note data
                    if isinstance(response, dict) and 'id' in response:
                        self.log(f"   JSON export successful - Note ID: {response.get('id')}")
                        self.log(f"   JSON export title: {response.get('title')}")
                        export_results.append((format_type, True))
                    else:
                        self.log(f"   JSON export failed - Invalid response format")
                        export_results.append((format_type, False))
                else:
                    # Text/Markdown response should have content
                    content = response.get('text', '')
                    if content and len(content) > 0:
                        self.log(f"   {format_type.upper()} export successful - Content length: {len(content)}")
                        export_results.append((format_type, True))
                    else:
                        self.log(f"   {format_type.upper()} export failed - No content")
                        export_results.append((format_type, False))
            else:
                export_results.append((format_type, False))
        
        # Test invalid format
        success, response = self.run_test(
            "Export with Invalid Format (Should Fail)",
            "GET",
            f"notes/{note_id}/export?format=invalid",
            422,  # Should fail with validation error
            auth_required=True
        )
        
        if success:
            self.log(f"   Correctly rejected invalid export format")
        
        return export_results

    def test_error_handling(self):
        """Test 5: Error Handling - Test that background tasks have proper exception handling"""
        self.log("\n🛡️  TESTING ERROR HANDLING")
        
        # Test accessing non-existent note
        success, response = self.run_test(
            "Access Non-existent Note",
            "GET",
            "notes/non-existent-id",
            404
        )
        
        # Test email for non-existent note
        success2, response2 = self.run_test(
            "Email Non-existent Note",
            "POST",
            "notes/non-existent-id/email",
            404,
            data={"to": ["test@example.com"], "subject": "Test"},
            auth_required=True
        )
        
        # Test export for non-existent note
        success3, response3 = self.run_test(
            "Export Non-existent Note",
            "GET",
            "notes/non-existent-id/export",
            404,
            auth_required=True
        )
        
        # Test upload to non-existent note
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test.png', f, 'image/png')}
                success4, response4 = self.run_test(
                    "Upload to Non-existent Note",
                    "POST",
                    "notes/non-existent-id/upload",
                    404,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
        
        return success and success2 and success3 and success4

    def run_focused_tests(self):
        """Run all focused tests"""
        self.log("🎯 Starting Focused Backend Tests for Review Request")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup authentication
        if not self.setup_auth():
            self.log("❌ Authentication setup failed - stopping tests")
            return False
        
        # Run focused tests
        test_results = {}
        
        # Test 1: Notes Processing Fix
        processing_results = self.test_notes_processing_fix()
        test_results['notes_processing'] = processing_results
        
        # Test 2: Email Delivery
        email_result = self.test_email_delivery()
        test_results['email_delivery'] = email_result
        
        # Test 3: File Upload for Scan
        upload_results = self.test_file_upload_for_scan()
        test_results['file_upload_scan'] = upload_results
        
        # Test 4: Export Functionality
        export_results = self.test_export_functionality()
        test_results['export_functionality'] = export_results
        
        # Test 5: Error Handling
        error_handling_result = self.test_error_handling()
        test_results['error_handling'] = error_handling_result
        
        return test_results

    def print_focused_summary(self, test_results):
        """Print focused test summary"""
        self.log("\n" + "="*60)
        self.log("📊 FOCUSED BACKEND TEST SUMMARY")
        self.log("="*60)
        self.log(f"Total API calls: {self.tests_run}")
        self.log(f"Successful API calls: {self.tests_passed}")
        self.log(f"Failed API calls: {self.tests_run - self.tests_passed}")
        self.log(f"API Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        self.log("\n🎯 FOCUS AREA RESULTS:")
        
        # Notes Processing Results
        if 'notes_processing' in test_results:
            self.log("\n1. 🎵 NOTES PROCESSING FIX:")
            processing_results = test_results['notes_processing']
            if processing_results:
                for note_type, status, artifacts in processing_results:
                    if status == 'ready':
                        self.log(f"   ✅ {note_type.upper()} processing: SUCCESS")
                    elif status == 'failed':
                        self.log(f"   ❌ {note_type.upper()} processing: FAILED")
                        if 'error' in artifacts:
                            self.log(f"      Error: {artifacts['error']}")
                    elif status == 'processing':
                        self.log(f"   ⚠️  {note_type.upper()} processing: STUCK IN PROCESSING")
                    else:
                        self.log(f"   ❓ {note_type.upper()} processing: UNKNOWN STATUS ({status})")
            else:
                self.log("   ❌ No processing results available")
        
        # Email Delivery Results
        if 'email_delivery' in test_results:
            self.log("\n2. 📧 EMAIL DELIVERY:")
            if test_results['email_delivery']:
                self.log("   ✅ Email functionality: WORKING")
            else:
                self.log("   ❌ Email functionality: FAILED")
        
        # File Upload Results
        if 'file_upload_scan' in test_results:
            self.log("\n3. 📁 FILE UPLOAD FOR SCAN:")
            upload_results = test_results['file_upload_scan']
            if upload_results:
                for filename, success, note_id in upload_results:
                    if success:
                        self.log(f"   ✅ {filename}: SUCCESS (Note: {note_id[:8]}...)")
                    else:
                        self.log(f"   ❌ {filename}: FAILED")
            else:
                self.log("   ❌ No upload results available")
        
        # Export Results
        if 'export_functionality' in test_results:
            self.log("\n4. 📤 EXPORT FUNCTIONALITY:")
            export_results = test_results['export_functionality']
            if export_results:
                for format_type, success in export_results:
                    if success:
                        self.log(f"   ✅ {format_type.upper()} export: SUCCESS")
                    else:
                        self.log(f"   ❌ {format_type.upper()} export: FAILED")
            else:
                self.log("   ❌ No export results available")
        
        # Error Handling Results
        if 'error_handling' in test_results:
            self.log("\n5. 🛡️  ERROR HANDLING:")
            if test_results['error_handling']:
                self.log("   ✅ Error handling: WORKING")
            else:
                self.log("   ❌ Error handling: FAILED")
        
        if self.created_notes:
            self.log(f"\n📝 Created test notes: {len(self.created_notes)}")
            for note_id in self.created_notes[:5]:  # Show first 5
                self.log(f"   - {note_id}")
            if len(self.created_notes) > 5:
                self.log(f"   ... and {len(self.created_notes) - 5} more")
        
        self.log("="*60)

def main():
    """Main test execution"""
    tester = FocusedBackendTester()
    
    try:
        test_results = tester.run_focused_tests()
        tester.print_focused_summary(test_results)
        
        # Determine overall success
        critical_issues = []
        
        # Check for critical issues
        if 'notes_processing' in test_results:
            processing_results = test_results['notes_processing']
            for note_type, status, artifacts in processing_results:
                if status == 'processing':
                    critical_issues.append(f"{note_type} notes stuck in processing")
                elif status == 'failed':
                    critical_issues.append(f"{note_type} notes processing failed")
        
        if not test_results.get('email_delivery', False):
            critical_issues.append("Email delivery not working")
        
        if not test_results.get('error_handling', False):
            critical_issues.append("Error handling not working properly")
        
        if critical_issues:
            print(f"\n⚠️  CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue}")
            return 1
        else:
            print(f"\n🎉 All focused tests completed successfully!")
            return 0
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())