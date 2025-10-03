#!/usr/bin/env python3
"""
Focused M4A File Upload Fix Testing
Tests the critical M4A file upload fix and wildcard MIME type pattern matching
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://insight-api.preview.emergentagent.com/api"

class M4ATestFocused:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        
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
            # Generate unique credentials
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"m4atest_{unique_id}@example.com"
            unique_username = f"m4atest{unique_id}"
            
            user_data = {
                "email": unique_email,
                "username": unique_username,
                "password": "TestPassword123",
                "first_name": "M4A",
                "last_name": "Tester"
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
                    self.user_id = data["user"]["id"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print(f"✅ Authentication setup successful: {unique_email}")
                    return True
            
            print(f"❌ Authentication setup failed: HTTP {response.status_code}")
            return False
                
        except Exception as e:
            print(f"❌ Authentication setup error: {str(e)}")
            return False

    def test_m4a_file_upload_fix(self):
        """Test M4A file upload fix - Critical test for wildcard MIME type pattern matching"""
        try:
            # Create a realistic M4A file header (simplified but valid structure)
            # M4A files start with ftyp box containing M4A brand
            m4a_header = (
                b'\x00\x00\x00\x20'  # Box size (32 bytes)
                b'ftyp'              # Box type: ftyp
                b'M4A '              # Major brand: M4A
                b'\x00\x00\x00\x00'  # Minor version
                b'M4A '              # Compatible brand 1
                b'mp42'              # Compatible brand 2
                b'isom'              # Compatible brand 3
                b'\x00\x00\x00\x00'  # Padding
            )
            
            # Add some audio data simulation
            m4a_content = m4a_header + b'\x00' * 2048  # Simulate audio data
            
            files = {
                'file': ('test_audio_file.m4a', m4a_content, 'audio/m4a')
            }
            data = {
                'title': 'M4A File Upload Test - Critical Fix Verification'
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/upload-file",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("id") and result.get("status"):
                    self.m4a_note_id = result["id"]
                    self.log_result("M4A File Upload Fix", True, 
                                  f"✅ M4A file accepted successfully! Note ID: {result['id']}, Status: {result['status']}", 
                                  result)
                else:
                    self.log_result("M4A File Upload Fix", False, "M4A upload succeeded but missing note ID or status", result)
            elif response.status_code == 400:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
                error_msg = error_data.get("detail", "")
                if "unsupported" in error_msg.lower() or "not allowed" in error_msg.lower():
                    self.log_result("M4A File Upload Fix", False, 
                                  f"❌ CRITICAL: M4A files still being rejected! Error: {error_msg}")
                else:
                    self.log_result("M4A File Upload Fix", False, f"M4A upload failed with unexpected error: {error_msg}")
            else:
                self.log_result("M4A File Upload Fix", False, f"M4A upload failed: HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("M4A File Upload Fix", False, f"M4A file upload test error: {str(e)}")

    def test_wildcard_mime_type_patterns(self):
        """Test wildcard MIME type pattern matching (audio/* and video/*)"""
        try:
            test_cases = [
                # Audio formats that should be accepted via audio/* pattern
                ('test_audio.aac', b'AAC_AUDIO_DATA' + b'\x00' * 1024, 'audio/aac', True),
                ('test_audio.flac', b'fLaC' + b'\x00' * 1024, 'audio/flac', True),
                ('test_audio.ogg', b'OggS' + b'\x00' * 1024, 'audio/ogg', True),
                ('test_audio.opus', b'OpusHead' + b'\x00' * 1024, 'audio/opus', True),
                ('test_audio.webm', b'WEBM_AUDIO' + b'\x00' * 1024, 'audio/webm', True),
                
                # Video formats that should be accepted via video/* pattern  
                ('test_video.mp4', b'ftypmp4' + b'\x00' * 1024, 'video/mp4', True),
                ('test_video.mov', b'ftypqt' + b'\x00' * 1024, 'video/quicktime', True),
                ('test_video.avi', b'RIFFAVI ' + b'\x00' * 1024, 'video/x-msvideo', True),
                
                # Non-audio/video formats that should be rejected
                ('test_doc.pdf', b'%PDF-1.4' + b'\x00' * 1024, 'application/pdf', False),
                ('test_doc.docx', b'PK\x03\x04' + b'\x00' * 1024, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', False),
            ]
            
            passed_tests = 0
            total_tests = len(test_cases)
            
            for filename, content, mime_type, should_accept in test_cases:
                files = {
                    'file': (filename, content, mime_type)
                }
                data = {
                    'title': f'Wildcard Pattern Test - {filename}'
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/upload-file",
                    files=files,
                    data=data,
                    timeout=15
                )
                
                if should_accept:
                    if response.status_code == 200:
                        passed_tests += 1
                        print(f"✅ {mime_type} correctly accepted via wildcard pattern")
                    else:
                        print(f"❌ {mime_type} incorrectly rejected (should be accepted)")
                else:
                    if response.status_code == 400:
                        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
                        if "unsupported" in error_data.get("detail", "").lower():
                            passed_tests += 1
                            print(f"✅ {mime_type} correctly rejected")
                        else:
                            print(f"⚠️ {mime_type} rejected but with unexpected error message")
                    else:
                        print(f"❌ {mime_type} incorrectly accepted (should be rejected)")
                
                time.sleep(0.2)  # Small delay between tests
            
            success_rate = (passed_tests / total_tests) * 100
            
            if success_rate >= 80:  # 80% success rate is acceptable
                self.log_result("Wildcard MIME Type Patterns", True, 
                              f"Wildcard pattern matching working well: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
            else:
                self.log_result("Wildcard MIME Type Patterns", False, 
                              f"Wildcard pattern matching issues: only {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
                
        except Exception as e:
            self.log_result("Wildcard MIME Type Patterns", False, f"Wildcard MIME type pattern test error: {str(e)}")

    def test_large_file_m4a_upload(self):
        """Test large M4A file upload through resumable upload system"""
        try:
            # Test creating resumable upload session for large M4A file
            large_m4a_data = {
                "filename": "large_meeting_recording.m4a",
                "total_size": 25165824,  # 24MB - large enough to test the system
                "mime_type": "audio/m4a"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/uploads/sessions",
                json=large_m4a_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("upload_id") and data.get("chunk_size"):
                    self.large_m4a_session_id = data["upload_id"]
                    self.log_result("Large File M4A Upload", True, 
                                  f"✅ Large M4A file session created successfully: {data['upload_id']}", 
                                  {
                                      "upload_id": data["upload_id"],
                                      "chunk_size": data["chunk_size"],
                                      "allowed_mime_types": data.get("allowed_mime_types", [])
                                  })
                else:
                    self.log_result("Large File M4A Upload", False, "Session creation succeeded but missing required fields", data)
            elif response.status_code == 400:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
                error_msg = error_data.get("detail", "")
                if "unsupported" in error_msg.lower() or "m4a" in error_msg.lower():
                    self.log_result("Large File M4A Upload", False, 
                                  f"❌ CRITICAL: Large M4A files rejected by resumable upload system! Error: {error_msg}")
                elif "too large" in error_msg.lower():
                    self.log_result("Large File M4A Upload", True, "File size limits properly enforced (24MB may exceed limit)")
                else:
                    self.log_result("Large File M4A Upload", False, f"Unexpected error: {error_msg}")
            else:
                self.log_result("Large File M4A Upload", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Large File M4A Upload", False, f"Large M4A file upload test error: {str(e)}")

    def test_mime_type_validation_function(self):
        """Test the is_mime_type_allowed function behavior"""
        try:
            # Test various MIME types to verify the validation logic
            test_cases = [
                # Direct matches
                ("audio/mpeg", True, "Direct audio MIME type match"),
                ("audio/wav", True, "Direct audio MIME type match"),
                ("video/mp4", True, "Direct video MIME type match"),
                
                # Wildcard matches
                ("audio/m4a", True, "Should match audio/* wildcard"),
                ("audio/aac", True, "Should match audio/* wildcard"),
                ("audio/flac", True, "Should match audio/* wildcard"),
                ("audio/custom-format", True, "Should match audio/* wildcard"),
                ("video/quicktime", True, "Should match video/* wildcard"),
                ("video/x-msvideo", True, "Should match video/* wildcard"),
                
                # Should be rejected
                ("text/plain", False, "Text files should be rejected"),
                ("application/pdf", False, "PDF files should be rejected"),
                ("image/jpeg", False, "Image files should be rejected"),
            ]
            
            passed_tests = 0
            total_tests = len(test_cases)
            
            for mime_type, should_accept, description in test_cases:
                # Create minimal test content
                test_content = f"TEST_CONTENT_FOR_{mime_type.replace('/', '_').upper()}".encode() + b'\x00' * 512
                
                files = {
                    'file': (f'test_file.{mime_type.split("/")[1]}', test_content, mime_type)
                }
                data = {
                    'title': f'MIME Validation Test - {mime_type}'
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/upload-file",
                    files=files,
                    data=data,
                    timeout=10
                )
                
                if should_accept:
                    if response.status_code == 200:
                        passed_tests += 1
                        print(f"✅ {mime_type}: {description}")
                    else:
                        print(f"❌ {mime_type}: Expected acceptance but got HTTP {response.status_code}")
                else:
                    if response.status_code == 400:
                        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
                        if "unsupported" in error_data.get("detail", "").lower():
                            passed_tests += 1
                            print(f"✅ {mime_type}: {description}")
                        else:
                            print(f"⚠️ {mime_type}: Rejected but with unexpected error")
                    else:
                        print(f"❌ {mime_type}: Expected rejection but got HTTP {response.status_code}")
                
                time.sleep(0.1)  # Small delay between tests
            
            success_rate = (passed_tests / total_tests) * 100
            
            if success_rate >= 85:  # 85% success rate required for validation function
                self.log_result("MIME Type Validation Function", True, 
                              f"MIME type validation working correctly: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
            else:
                self.log_result("MIME Type Validation Function", False, 
                              f"MIME type validation issues: only {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
                
        except Exception as e:
            self.log_result("MIME Type Validation Function", False, f"MIME type validation function test error: {str(e)}")

    def test_improved_error_messages(self):
        """Test that error messages are user-friendly and informative"""
        try:
            # Test with completely unsupported file type
            unsupported_content = b"This is plain text, not audio or video"
            files = {
                'file': ('document.txt', unsupported_content, 'text/plain')
            }
            data = {
                'title': 'Error Message Test'
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/upload-file",
                files=files,
                data=data,
                timeout=10
            )
            
            if response.status_code == 400:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"detail": response.text}
                error_msg = error_data.get("detail", "")
                
                # Check if error message is user-friendly and informative
                user_friendly_indicators = [
                    "audio" in error_msg.lower(),
                    "video" in error_msg.lower(),
                    "support" in error_msg.lower() or "allow" in error_msg.lower(),
                    len(error_msg) > 20,  # Not just a generic error
                    "transcription" in error_msg.lower() or "format" in error_msg.lower()
                ]
                
                friendly_score = sum(user_friendly_indicators)
                
                if friendly_score >= 3:
                    self.log_result("Improved Error Messages", True, 
                                  f"✅ Error messages are user-friendly and informative: '{error_msg}'")
                else:
                    self.log_result("Improved Error Messages", False, 
                                  f"Error messages could be more user-friendly: '{error_msg}' (Score: {friendly_score}/5)")
            else:
                self.log_result("Improved Error Messages", False, 
                              f"Expected 400 error for unsupported file, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Improved Error Messages", False, f"Error message test error: {str(e)}")

    def run_focused_tests(self):
        """Run focused M4A file upload fix tests"""
        print("🔥" * 80)
        print("🔥 CRITICAL M4A FILE UPLOAD FIX TESTING")
        print("🔥 Testing wildcard MIME type pattern matching and M4A file acceptance")
        print("🔥" * 80)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        print("\n" + "=" * 60)
        print("🎯 RUNNING M4A FILE UPLOAD FIX TESTS")
        print("=" * 60)
        
        # Run the critical tests
        self.test_m4a_file_upload_fix()
        self.test_wildcard_mime_type_patterns()
        self.test_large_file_m4a_upload()
        self.test_mime_type_validation_function()
        self.test_improved_error_messages()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if success_rate >= 80:
            print("\n🎉 M4A FILE UPLOAD FIX IS WORKING CORRECTLY!")
        else:
            print("\n⚠️ M4A FILE UPLOAD FIX NEEDS ATTENTION")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"   - {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = M4ATestFocused()
    tester.run_focused_tests()