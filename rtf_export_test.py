#!/usr/bin/env python3
"""
RTF Export Testing for AI Conversations
Tests the improved professional RTF and TXT export formatting
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os
import re

class RTFExportTester:
    def __init__(self, base_url="https://audio-pipeline-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"rtf_test_user_{int(time.time())}@example.com",
            "username": f"rtfuser_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "RTF",
            "last_name": "Tester"
        }
        self.expeditors_user_data = {
            "email": f"rtf_expeditors_{int(time.time())}@expeditors.com",
            "username": f"rtfexpeditors_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "RTF Tester"
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
                    return True, response.json(), response
                except:
                    return True, {"message": "Success but no JSON response"}, response
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}, response

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}, None

    def register_user(self, user_data, user_type="regular"):
        """Register a user and get auth token"""
        success, response, _ = self.run_test(
            f"{user_type.title()} User Registration",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        if success:
            token = response.get('access_token')
            user_info = response.get('user', {})
            self.log(f"   Registered {user_type} user ID: {user_info.get('id')}")
            return token, user_info.get('id')
        return None, None

    def create_note_with_content(self, title, kind="audio"):
        """Create a note and add some content"""
        success, response, _ = self.run_test(
            f"Create {kind.title()} Note",
            "POST",
            "notes",
            200,
            data={"title": title, "kind": kind},
            auth_required=True
        )
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   Created note ID: {note_id}")
            return note_id
        return None

    def upload_dummy_audio(self, note_id):
        """Upload a dummy audio file to trigger transcription"""
        # Create a small dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            # Write minimal WebM header (just for testing, not real audio)
            dummy_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('business_meeting.webm', f, 'audio/webm')}
                success, response, _ = self.run_test(
                    f"Upload Audio to Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            return success

    def simulate_ai_conversations(self, note_id):
        """Simulate AI conversations by directly adding them to note artifacts"""
        # First, let's add some transcript content to the note
        # We'll simulate this by trying to get the note and checking if it has content
        success, note_data, _ = self.run_test(
            f"Get Note {note_id[:8]}... for AI Chat Setup",
            "GET",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        # Add some sample transcript content if none exists
        artifacts = note_data.get('artifacts', {})
        if not artifacts.get('transcript'):
            # We'll simulate having transcript content by using the AI chat endpoint
            # which will fail gracefully if no content exists
            pass
        
        # Try to create AI conversations using the AI chat endpoint
        questions = [
            "What are the key risks mentioned in this meeting?",
            "Provide a summary of the main discussion points",
            "What action items were identified?",
            "What are the strategic recommendations based on this content?"
        ]
        
        conversations_created = 0
        for question in questions:
            success, response, _ = self.run_test(
                f"AI Chat Question {conversations_created + 1}",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True
            )
            if success:
                conversations_created += 1
                self.log(f"   AI response length: {len(response.get('response', ''))}")
            else:
                # If AI chat fails due to no content, we'll manually create some conversations
                self.log(f"   AI chat failed, will create mock conversations")
                break
        
        return conversations_created > 0

    def test_rtf_export_structure(self, note_id, user_type="regular"):
        """Test RTF export structure and formatting"""
        success, response, http_response = self.run_test(
            f"RTF Export - {user_type.title()} User",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=rtf",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        # Get the RTF content from the response
        rtf_content = http_response.text if http_response else ""
        
        if not rtf_content:
            self.log(f"❌ No RTF content received")
            return False
        
        # Verify RTF structure
        rtf_checks = {
            "RTF Header": rtf_content.startswith(r"{\rtf1"),
            "Font Table": r"{\fonttbl" in rtf_content,
            "Color Table": r"{\colortbl" in rtf_content,
            "Professional Fonts": any(font in rtf_content for font in ["Times New Roman", "Arial", "Calibri"]),
            "Expeditors Branding": "EXPEDITORS INTERNATIONAL" in rtf_content if user_type == "expeditors" else "EXPEDITORS INTERNATIONAL" not in rtf_content,
            "Professional Structure": "AI CONTENT ANALYSIS REPORT" in rtf_content,
            "Section Headers": "ANALYSIS SECTION" in rtf_content,
            "Proper RTF Closing": rtf_content.endswith("}"),
            "Professional Colors": r"\cf2" in rtf_content and r"\cf3" in rtf_content,
            "Bullet Points": r"\bullet" in rtf_content
        }
        
        passed_checks = 0
        total_checks = len(rtf_checks)
        
        for check_name, check_result in rtf_checks.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        # Check file size (should be substantial for professional formatting)
        file_size = len(rtf_content)
        self.log(f"   RTF file size: {file_size} characters")
        
        # Verify Content-Type header
        content_type = http_response.headers.get('Content-Type', '') if http_response else ''
        content_disposition = http_response.headers.get('Content-Disposition', '') if http_response else ''
        
        self.log(f"   Content-Type: {content_type}")
        self.log(f"   Content-Disposition: {content_disposition}")
        
        # Check for descriptive filename
        filename_check = False
        if content_disposition:
            if user_type == "expeditors":
                filename_check = "Expeditors_AI_Analysis_" in content_disposition
            else:
                filename_check = "AI_Analysis_" in content_disposition and ".rtf" in content_disposition
        
        if filename_check:
            self.log(f"   ✅ Descriptive filename: PASS")
            passed_checks += 1
        else:
            self.log(f"   ❌ Descriptive filename: FAIL")
        
        total_checks += 1
        
        success_rate = (passed_checks / total_checks) * 100
        self.log(f"   RTF Structure Check: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        return success_rate >= 80  # 80% pass rate required

    def test_txt_export_structure(self, note_id, user_type="regular"):
        """Test TXT export structure and formatting"""
        success, response, http_response = self.run_test(
            f"TXT Export - {user_type.title()} User",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=txt",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        # Get the TXT content from the response
        txt_content = http_response.text if http_response else ""
        
        if not txt_content:
            self.log(f"❌ No TXT content received")
            return False
        
        # Verify TXT structure
        txt_checks = {
            "Professional Header": "AI CONTENT ANALYSIS REPORT" in txt_content,
            "Expeditors Branding": "EXPEDITORS INTERNATIONAL" in txt_content if user_type == "expeditors" else "EXPEDITORS INTERNATIONAL" not in txt_content,
            "Document Info": "Document:" in txt_content and "Generated:" in txt_content,
            "Executive Summary": "EXECUTIVE SUMMARY" in txt_content,
            "Section Headers": "ANALYSIS SECTION" in txt_content,
            "Professional Separators": "=" in txt_content and "-" in txt_content,
            "Bullet Points": "•" in txt_content,
            "Professional Footer": "AI-Generated Content Analysis Report" in txt_content or "EXPEDITORS INTERNATIONAL" in txt_content,
            "Clean Formatting": not any(symbol in txt_content for symbol in ["###", "**", "```"])
        }
        
        passed_checks = 0
        total_checks = len(txt_checks)
        
        for check_name, check_result in txt_checks.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        # Check file size
        file_size = len(txt_content)
        self.log(f"   TXT file size: {file_size} characters")
        
        # Verify headers
        content_type = http_response.headers.get('Content-Type', '') if http_response else ''
        content_disposition = http_response.headers.get('Content-Disposition', '') if http_response else ''
        
        self.log(f"   Content-Type: {content_type}")
        self.log(f"   Content-Disposition: {content_disposition}")
        
        # Check for descriptive filename
        filename_check = False
        if content_disposition:
            if user_type == "expeditors":
                filename_check = "Expeditors_AI_Analysis_" in content_disposition
            else:
                filename_check = "AI_Analysis_" in content_disposition and ".txt" in content_disposition
        
        if filename_check:
            self.log(f"   ✅ Descriptive filename: PASS")
            passed_checks += 1
        else:
            self.log(f"   ❌ Descriptive filename: FAIL")
        
        total_checks += 1
        
        success_rate = (passed_checks / total_checks) * 100
        self.log(f"   TXT Structure Check: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        return success_rate >= 80  # 80% pass rate required

    def test_export_error_handling(self, note_id):
        """Test export error handling scenarios"""
        # Test invalid format
        success, response, _ = self.run_test(
            "Invalid Format Export (Should Fail)",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=invalid",
            422,  # Validation error
            auth_required=True
        )
        
        # Test non-existent note
        success2, response2, _ = self.run_test(
            "Non-existent Note Export (Should Fail)",
            "GET",
            "notes/invalid-id/ai-conversations/export?format=rtf",
            404,
            auth_required=True
        )
        
        return success and success2

    def test_no_conversations_scenario(self):
        """Test export when note has no AI conversations"""
        # Create a note without AI conversations
        note_id = self.create_note_with_content("Empty Note for Export Test")
        if not note_id:
            return False
        
        success, response, _ = self.run_test(
            "Export Note Without AI Conversations (Should Fail)",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=rtf",
            400,  # Bad request - no conversations
            auth_required=True
        )
        
        return success

    def run_comprehensive_rtf_test(self):
        """Run comprehensive RTF export tests"""
        self.log("🚀 Starting RTF Export Comprehensive Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Register regular user
        self.log("\n👤 REGULAR USER SETUP")
        self.auth_token, user_id = self.register_user(self.test_user_data, "regular")
        if not self.auth_token:
            self.log("❌ Regular user registration failed - stopping tests")
            return False
        
        # Register Expeditors user
        self.log("\n👑 EXPEDITORS USER SETUP")
        self.expeditors_token, expeditors_user_id = self.register_user(self.expeditors_user_data, "expeditors")
        if not self.expeditors_token:
            self.log("❌ Expeditors user registration failed - continuing with regular user only")
        
        # === REGULAR USER RTF EXPORT TESTS ===
        self.log("\n📄 REGULAR USER RTF EXPORT TESTS")
        
        # Create note with content for regular user
        note_id = self.create_note_with_content("Business Meeting Analysis - Regular User")
        if not note_id:
            self.log("❌ Failed to create note for regular user")
            return False
        
        # Upload audio to trigger processing
        self.upload_dummy_audio(note_id)
        
        # Wait a bit for processing
        time.sleep(3)
        
        # Create AI conversations
        if not self.simulate_ai_conversations(note_id):
            self.log("⚠️  Could not create AI conversations - may affect export tests")
        
        # Test RTF export for regular user
        rtf_success = self.test_rtf_export_structure(note_id, "regular")
        
        # Test TXT export for regular user
        txt_success = self.test_txt_export_structure(note_id, "regular")
        
        # === EXPEDITORS USER RTF EXPORT TESTS ===
        expeditors_rtf_success = True
        expeditors_txt_success = True
        
        if self.expeditors_token:
            self.log("\n👑 EXPEDITORS USER RTF EXPORT TESTS")
            
            # Switch to Expeditors user
            temp_token = self.auth_token
            self.auth_token = self.expeditors_token
            
            # Create note with content for Expeditors user
            expeditors_note_id = self.create_note_with_content("Supply Chain Analysis - Expeditors User")
            if expeditors_note_id:
                # Upload audio to trigger processing
                self.upload_dummy_audio(expeditors_note_id)
                
                # Wait a bit for processing
                time.sleep(3)
                
                # Create AI conversations
                if not self.simulate_ai_conversations(expeditors_note_id):
                    self.log("⚠️  Could not create AI conversations for Expeditors user")
                
                # Test RTF export for Expeditors user
                expeditors_rtf_success = self.test_rtf_export_structure(expeditors_note_id, "expeditors")
                
                # Test TXT export for Expeditors user
                expeditors_txt_success = self.test_txt_export_structure(expeditors_note_id, "expeditors")
            else:
                self.log("❌ Failed to create note for Expeditors user")
                expeditors_rtf_success = False
                expeditors_txt_success = False
            
            # Restore regular user token
            self.auth_token = temp_token
        
        # === ERROR HANDLING TESTS ===
        self.log("\n🚨 ERROR HANDLING TESTS")
        
        # Test error scenarios
        error_handling_success = self.test_export_error_handling(note_id)
        
        # Test no conversations scenario
        no_conversations_success = self.test_no_conversations_scenario()
        
        # Calculate overall success
        all_tests_passed = (
            rtf_success and 
            txt_success and 
            expeditors_rtf_success and 
            expeditors_txt_success and 
            error_handling_success and 
            no_conversations_success
        )
        
        return all_tests_passed

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 RTF EXPORT TEST SUMMARY")
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
    tester = RTFExportTester()
    
    try:
        success = tester.run_comprehensive_rtf_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 All RTF export tests passed! Professional formatting is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some RTF export tests failed. Check the logs above for details.")
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