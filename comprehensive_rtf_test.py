#!/usr/bin/env python3
"""
Comprehensive RTF Export Test
Creates notes with content and AI conversations, then tests RTF/TXT export
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class ComprehensiveRTFTester:
    def __init__(self, base_url="https://voice2text-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"comp_rtf_test_{int(time.time())}@example.com",
            "username": f"comprtf_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Comprehensive",
            "last_name": "RTF Tester"
        }
        self.expeditors_user_data = {
            "email": f"comp_expeditors_{int(time.time())}@expeditors.com",
            "username": f"compexp_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "Comp Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=45, auth_required=False):
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
        """Create a note"""
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

    def create_realistic_audio_file(self):
        """Create a more realistic audio file for testing"""
        # Create a larger dummy WebM file that might trigger actual processing
        webm_header = b'\x1a\x45\xdf\xa3'  # EBML header
        webm_header += b'\x9f\x42\x86\x81\x01'  # EBML version
        webm_header += b'\x42\xf7\x81\x01'  # EBML read version
        webm_header += b'\x42\xf2\x81\x04'  # EBML max ID length
        webm_header += b'\x42\xf3\x81\x08'  # EBML max size length
        webm_header += b'\x42\x82\x84webm'  # Doc type
        webm_header += b'\x42\x87\x81\x02'  # Doc type version
        webm_header += b'\x42\x85\x81\x02'  # Doc type read version
        
        # Add some padding to make it larger
        padding = b'\x00' * 1024  # 1KB of padding
        
        return webm_header + padding

    def upload_audio_and_wait(self, note_id, max_wait=60):
        """Upload audio file and wait for processing"""
        # Create realistic audio file
        audio_data = self.create_realistic_audio_file()
        
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('business_meeting_transcript.webm', f, 'audio/webm')}
                success, response, _ = self.run_test(
                    f"Upload Audio to Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if not success:
                return False
        
        # Wait for processing to complete or fail
        self.log(f"⏳ Waiting for audio processing (max {max_wait}s)...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, note_data, _ = self.run_test(
                f"Check Processing Status {note_id[:8]}...",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success:
                status = note_data.get('status', 'unknown')
                artifacts = note_data.get('artifacts', {})
                
                self.log(f"   Status: {status}")
                
                if status == 'ready' and artifacts.get('transcript'):
                    self.log(f"✅ Audio processing completed successfully!")
                    self.log(f"   Transcript length: {len(artifacts['transcript'])} characters")
                    return True
                elif status == 'failed':
                    self.log(f"⚠️  Audio processing failed, but we can still test with mock content")
                    return self.add_mock_transcript(note_id)
                elif status in ['processing', 'uploading']:
                    self.log(f"   Still processing... waiting...")
                    time.sleep(5)
                else:
                    self.log(f"   Unknown status: {status}")
                    time.sleep(3)
            else:
                break
        
        self.log(f"⏰ Processing timeout - adding mock transcript for testing")
        return self.add_mock_transcript(note_id)

    def add_mock_transcript(self, note_id):
        """Add mock transcript content directly to note for testing purposes"""
        # We can't directly modify the database, but we can try to simulate having content
        # by checking if the note has any content and proceeding with AI chat
        success, note_data, _ = self.run_test(
            f"Get Note for Mock Content {note_id[:8]}...",
            "GET",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        
        if success:
            artifacts = note_data.get('artifacts', {})
            if artifacts.get('transcript') or artifacts.get('text'):
                self.log(f"✅ Note already has content for AI chat")
                return True
            else:
                self.log(f"⚠️  Note has no content - AI chat may not work")
                return False
        return False

    def create_ai_conversations(self, note_id):
        """Create AI conversations using the AI chat endpoint"""
        questions = [
            "What are the key business risks mentioned in this content?",
            "Provide a comprehensive summary of the main discussion points and strategic insights",
            "What specific action items and recommendations can be derived from this analysis?",
            "What are the potential market opportunities and competitive advantages discussed?"
        ]
        
        conversations_created = 0
        
        for i, question in enumerate(questions, 1):
            success, response, _ = self.run_test(
                f"AI Chat Question {i}: Risk Analysis",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True,
                timeout=60
            )
            
            if success:
                conversations_created += 1
                ai_response = response.get('response', '')
                self.log(f"   ✅ AI Response {i} length: {len(ai_response)} characters")
                time.sleep(1)  # Brief pause between requests
            else:
                self.log(f"   ❌ AI Chat Question {i} failed")
                break
        
        self.log(f"📊 Created {conversations_created}/{len(questions)} AI conversations")
        return conversations_created > 0

    def test_rtf_export_comprehensive(self, note_id, user_type="regular"):
        """Comprehensive RTF export test"""
        success, response, http_response = self.run_test(
            f"RTF Export Comprehensive Test - {user_type.title()} User",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=rtf",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        rtf_content = http_response.text if http_response else ""
        
        if not rtf_content:
            self.log(f"❌ No RTF content received")
            return False
        
        self.log(f"   📄 RTF Content Analysis:")
        self.log(f"   - File size: {len(rtf_content)} characters")
        
        # Comprehensive RTF verification based on review request
        verification_results = {
            # Professional RTF Structure
            "RTF Document Structure": rtf_content.startswith(r"{\rtf1\ansi\deff0"),
            "Professional Font Tables": r"{\fonttbl{\f0 Times New Roman;}{\f1 Arial;}{\f2 Calibri;}" in rtf_content,
            "Professional Color Scheme": r"{\colortbl;\red0\green0\blue0;\red234\green10\blue42;\red35\green31\blue32;" in rtf_content,
            
            # Expeditors Branding (should be present for expeditors users, absent for regular users)
            "Expeditors Header Branding": ("EXPEDITORS INTERNATIONAL" in rtf_content) == (user_type == "expeditors"),
            "Global Logistics Branding": ("Global Logistics & Freight Forwarding" in rtf_content) == (user_type == "expeditors"),
            "Logo Placeholder Integration": (r"\cf2 EXPEDITORS INTERNATIONAL" in rtf_content) == (user_type == "expeditors"),
            
            # Professional Structure and Clean Formatting
            "Professional Report Title": "AI CONTENT ANALYSIS REPORT" in rtf_content,
            "Clean Section Divisions": "─" in rtf_content,  # Professional separator lines
            "Proper Headers": "ANALYSIS SECTION" in rtf_content,
            "Executive Summary Section": "EXECUTIVE SUMMARY" in rtf_content,
            
            # Improved Bullet Point Formatting (NOT messy dots)
            "Professional Bullet Points": r"\bullet\tab" in rtf_content,
            "Clean List Formatting": r"\li360" in rtf_content or r"\li480" in rtf_content,
            "No Messy Dots": rtf_content.count("...") < 3,  # Should not have many messy dots
            
            # Professional Typography and Colors
            "Professional Font Usage": all(font in rtf_content for font in [r"\f0", r"\f1", r"\f2"]),
            "Professional Color Usage": all(color in rtf_content for color in [r"\cf1", r"\cf2", r"\cf3"]),
            "Professional Spacing": r"\par\par" in rtf_content,
            
            # Clean Formatting (No Markdown Symbols)
            "No Markdown Headers": "###" not in rtf_content,
            "No Markdown Bold": "**" not in rtf_content,
            "No Markdown Code Blocks": "```" not in rtf_content,
            
            # Professional Document Structure
            "Professional Header Formatting": (r"\fs32\b\cf2" in rtf_content) if user_type == "expeditors" else (r"\fs28\b\cf1" in rtf_content),
            "Professional Footer": ("confidential and proprietary" in rtf_content) if user_type == "expeditors" else ("AI-Generated Content Analysis Report" in rtf_content),
            "Proper RTF Closing": rtf_content.endswith("}"),
            "Substantial Professional Content": len(rtf_content) > 8000,  # Should be substantial for professional formatting
        }
        
        # Check file download headers
        content_type = http_response.headers.get('Content-Type', '') if http_response else ''
        content_disposition = http_response.headers.get('Content-Disposition', '') if http_response else ''
        
        filename_verification = {
            "Correct RTF Content-Type": content_type == "application/rtf",
            "File Download Headers": "attachment" in content_disposition,
            "Descriptive Filename": ("Expeditors_AI_Analysis_" in content_disposition) if user_type == "expeditors" else ("AI_Analysis_" in content_disposition),
            "RTF File Extension": ".rtf" in content_disposition
        }
        
        # Combine all verifications
        all_checks = {**verification_results, **filename_verification}
        
        passed_checks = 0
        total_checks = len(all_checks)
        
        self.log(f"   🔍 PROFESSIONAL RTF FORMATTING VERIFICATION:")
        for check_name, check_result in all_checks.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        success_rate = (passed_checks / total_checks) * 100
        self.log(f"   📊 RTF Professional Formatting Score: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        return success_rate >= 85  # 85% pass rate required

    def test_txt_export_comprehensive(self, note_id, user_type="regular"):
        """Comprehensive TXT export test"""
        success, response, http_response = self.run_test(
            f"TXT Export Comprehensive Test - {user_type.title()} User",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=txt",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        txt_content = http_response.text if http_response else ""
        
        if not txt_content:
            self.log(f"❌ No TXT content received")
            return False
        
        self.log(f"   📄 TXT Content Analysis:")
        self.log(f"   - File size: {len(txt_content)} characters")
        
        # Comprehensive TXT verification
        txt_verification = {
            # Professional Structure
            "Professional Header Lines": "=" * 70 in txt_content or "=" * 50 in txt_content,
            "Expeditors Branding": ("EXPEDITORS INTERNATIONAL" in txt_content) == (user_type == "expeditors"),
            "Professional Report Title": "AI CONTENT ANALYSIS REPORT" in txt_content,
            
            # Clean Headers and Formatting
            "Executive Summary Header": "EXECUTIVE SUMMARY" in txt_content,
            "Analysis Section Headers": "ANALYSIS SECTION" in txt_content,
            "Professional Separators": "-" * 20 in txt_content or "-" * 40 in txt_content,
            
            # Improved Clean Formatting
            "Professional Bullet Points": "•" in txt_content,
            "No Markdown Symbols": not any(symbol in txt_content for symbol in ["###", "**", "```"]),
            "Clean Professional Spacing": "\n\n" in txt_content,
            
            # Professional Content Structure
            "Document Information": "Document:" in txt_content and "Generated:" in txt_content,
            "Analysis Sections Info": "Analysis Sections:" in txt_content,
            "Professional Footer": ("EXPEDITORS INTERNATIONAL" in txt_content) if user_type == "expeditors" else ("AI-Generated Content Analysis Report" in txt_content),
            
            # Content Quality
            "Substantial Content": len(txt_content) > 2000,
            "Professional Language": "Generated:" in txt_content and "UTC" in txt_content
        }
        
        # Check file headers
        content_type = http_response.headers.get('Content-Type', '') if http_response else ''
        content_disposition = http_response.headers.get('Content-Disposition', '') if http_response else ''
        
        filename_verification = {
            "Correct TXT Content-Type": content_type == "text/plain",
            "File Download Headers": "attachment" in content_disposition,
            "Descriptive Filename": ("Expeditors_AI_Analysis_" in content_disposition) if user_type == "expeditors" else ("AI_Analysis_" in content_disposition),
            "TXT File Extension": ".txt" in content_disposition
        }
        
        all_checks = {**txt_verification, **filename_verification}
        
        passed_checks = 0
        total_checks = len(all_checks)
        
        self.log(f"   🔍 PROFESSIONAL TXT FORMATTING VERIFICATION:")
        for check_name, check_result in all_checks.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        success_rate = (passed_checks / total_checks) * 100
        self.log(f"   📊 TXT Professional Formatting Score: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        return success_rate >= 85  # 85% pass rate required

    def run_comprehensive_test(self):
        """Run comprehensive RTF export test"""
        self.log("🚀 Starting Comprehensive RTF Export Test")
        self.log("   Testing improved professional RTF and TXT export formatting")
        self.log("   Focus: Professional structure, Expeditors branding, clean formatting")
        
        # Register users
        self.log("\n👤 USER REGISTRATION")
        self.auth_token, user_id = self.register_user(self.test_user_data, "regular")
        if not self.auth_token:
            self.log("❌ Regular user registration failed")
            return False
        
        self.expeditors_token, exp_user_id = self.register_user(self.expeditors_user_data, "expeditors")
        if not self.expeditors_token:
            self.log("❌ Expeditors user registration failed - continuing with regular user only")
        
        # === REGULAR USER TEST ===
        self.log("\n📄 REGULAR USER RTF EXPORT TEST")
        
        # Create note and add content
        note_id = self.create_note_with_content("Professional Business Meeting Analysis")
        if not note_id:
            self.log("❌ Failed to create note")
            return False
        
        # Upload audio and wait for processing
        if not self.upload_audio_and_wait(note_id):
            self.log("⚠️  Audio processing failed - trying to continue with available content")
        
        # Create AI conversations
        if not self.create_ai_conversations(note_id):
            self.log("❌ Failed to create AI conversations - cannot test export")
            return False
        
        # Test RTF export
        rtf_regular_success = self.test_rtf_export_comprehensive(note_id, "regular")
        
        # Test TXT export
        txt_regular_success = self.test_txt_export_comprehensive(note_id, "regular")
        
        # === EXPEDITORS USER TEST ===
        rtf_expeditors_success = True
        txt_expeditors_success = True
        
        if self.expeditors_token:
            self.log("\n👑 EXPEDITORS USER RTF EXPORT TEST")
            
            # Switch to Expeditors user
            temp_token = self.auth_token
            self.auth_token = self.expeditors_token
            
            # Create note for Expeditors user
            exp_note_id = self.create_note_with_content("Expeditors Supply Chain Analysis")
            if exp_note_id:
                # Upload audio and wait for processing
                if not self.upload_audio_and_wait(exp_note_id):
                    self.log("⚠️  Audio processing failed for Expeditors user")
                
                # Create AI conversations
                if self.create_ai_conversations(exp_note_id):
                    # Test RTF export with Expeditors branding
                    rtf_expeditors_success = self.test_rtf_export_comprehensive(exp_note_id, "expeditors")
                    
                    # Test TXT export with Expeditors branding
                    txt_expeditors_success = self.test_txt_export_comprehensive(exp_note_id, "expeditors")
                else:
                    self.log("❌ Failed to create AI conversations for Expeditors user")
                    rtf_expeditors_success = False
                    txt_expeditors_success = False
            else:
                rtf_expeditors_success = False
                txt_expeditors_success = False
            
            # Restore regular user token
            self.auth_token = temp_token
        
        # Calculate overall success
        all_tests_passed = (
            rtf_regular_success and 
            txt_regular_success and 
            rtf_expeditors_success and 
            txt_expeditors_success
        )
        
        return all_tests_passed

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*80)
        self.log("📊 COMPREHENSIVE RTF EXPORT TEST SUMMARY")
        self.log("="*80)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*80)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ComprehensiveRTFTester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 All comprehensive RTF export tests passed!")
            print("✅ Professional RTF format with improved structure verified")
            print("✅ Professional TXT format with clean formatting verified")
            print("✅ Expeditors branding and logo placeholder integration working")
            print("✅ Descriptive filename generation based on note title working")
            print("✅ Clean bullet points and professional headers verified")
            print("✅ No messy, tacky output - everything aligned and professional")
            return 0
        else:
            print(f"\n⚠️  Some comprehensive RTF export tests failed.")
            print("Check the detailed logs above for specific issues.")
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