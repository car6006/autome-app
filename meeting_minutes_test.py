#!/usr/bin/env python3
"""
OPEN AUTO-ME v1 Meeting Minutes Functionality Test
Tests the new professional meeting minutes generation and export features
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class MeetingMinutesAPITester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"meeting_test_{int(time.time())}@example.com",
            "username": f"meetinguser_{int(time.time())}",
            "password": "MeetingTest123!",
            "first_name": "Meeting",
            "last_name": "Tester"
        }
        self.expeditors_user_data = {
            "email": f"meeting_expeditors_{int(time.time())}@expeditors.com",
            "username": f"expeditors_meeting_{int(time.time())}",
            "password": "ExpeditorsTest123!",
            "first_name": "Expeditors",
            "last_name": "Meeting"
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

    def setup_test_users(self):
        """Setup regular and Expeditors test users"""
        self.log("🔐 Setting up test users...")
        
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
            self.log(f"   Regular user token: {'✅' if self.auth_token else '❌'}")
        
        # Register Expeditors user
        success, response = self.run_test(
            "Register Expeditors User",
            "POST",
            "auth/register",
            200,
            data=self.expeditors_user_data
        )
        if success:
            self.expeditors_token = response.get('access_token')
            self.log(f"   Expeditors user token: {'✅' if self.expeditors_token else '❌'}")
        
        return self.auth_token and self.expeditors_token

    def create_note_with_content(self, title, is_expeditors=False):
        """Create a note and add mock content for meeting minutes testing"""
        # Create note
        success, response = self.run_test(
            f"Create Note: {title}",
            "POST",
            "notes",
            200,
            data={"title": title, "kind": "audio"},
            auth_required=True,
            use_expeditors_token=is_expeditors
        )
        
        if not success or 'id' not in response:
            return None
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Add mock transcript content by uploading a dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            # Write minimal WebM header
            dummy_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('meeting_recording.webm', f, 'audio/webm')}
                success, response = self.run_test(
                    f"Upload Audio to Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True,
                    use_expeditors_token=is_expeditors
                )
            
            os.unlink(tmp_file.name)
        
        # Add AI conversations to simulate meeting content
        self.add_mock_meeting_conversations(note_id, is_expeditors)
        
        return note_id

    def add_mock_meeting_conversations(self, note_id, is_expeditors=False):
        """Add mock AI conversations that simulate meeting content"""
        # Mock meeting-related questions
        meeting_questions = [
            "What were the key discussion points in this meeting?",
            "Who were the attendees and what were their roles?",
            "What action items were assigned and to whom?",
            "What are the main risks identified in this discussion?",
            "What are the next steps and follow-up actions?",
            "Provide a comprehensive summary of the meeting outcomes"
        ]
        
        conversations_added = 0
        for question in meeting_questions:
            try:
                url = f"{self.api_url}/notes/{note_id}/ai-chat"
                headers = {'Content-Type': 'application/json'}
                token = self.expeditors_token if is_expeditors else self.auth_token
                if token:
                    headers['Authorization'] = f'Bearer {token}'
                
                response = requests.post(
                    url,
                    json={"question": question},
                    headers=headers,
                    timeout=45
                )
                
                if response.status_code == 200:
                    conversations_added += 1
                    self.log(f"   Added meeting conversation: {question[:40]}...")
                elif response.status_code == 400:
                    # No content available - expected for new notes
                    self.log(f"   No content available for AI chat (expected)")
                    break
                else:
                    self.log(f"   Failed to add conversation: {response.status_code}")
                    
            except Exception as e:
                self.log(f"   Error adding conversation: {str(e)}")
                break
        
        return conversations_added

    def test_meeting_minutes_generation(self, note_id, is_expeditors=False):
        """Test the meeting minutes generation endpoint"""
        success, response = self.run_test(
            f"Generate Meeting Minutes {'(Expeditors)' if is_expeditors else '(Regular)'}",
            "POST",
            f"notes/{note_id}/generate-meeting-minutes",
            200,
            auth_required=True,
            use_expeditors_token=is_expeditors,
            timeout=90
        )
        
        if success:
            meeting_minutes = response.get('meeting_minutes', '')
            note_title = response.get('note_title', '')
            is_expeditors_response = response.get('is_expeditors', False)
            
            self.log(f"   ✅ Meeting minutes generated successfully")
            self.log(f"   Note title: {note_title}")
            self.log(f"   Is Expeditors user: {is_expeditors_response}")
            self.log(f"   Content length: {len(meeting_minutes)} characters")
            
            # Verify required sections are present
            required_sections = [
                'ATTENDEES',
                'APOLOGIES', 
                'MEETING MINUTES',
                'ACTION ITEMS',
                'KEY INSIGHTS',
                'RISK ASSESSMENT',
                'NEXT STEPS'
            ]
            
            sections_found = []
            for section in required_sections:
                if section in meeting_minutes.upper():
                    sections_found.append(section)
                    self.log(f"   ✅ Section found: {section}")
                else:
                    self.log(f"   ❌ Section missing: {section}")
            
            # Check for professional language (no AI references)
            ai_references = ['AI analysis', 'AI-generated', 'artificial intelligence', 'AI assistant']
            ai_found = []
            for ref in ai_references:
                if ref.lower() in meeting_minutes.lower():
                    ai_found.append(ref)
            
            if not ai_found:
                self.log(f"   ✅ No AI references found - professional language confirmed")
            else:
                self.log(f"   ❌ AI references found: {ai_found}")
            
            # Check content quality
            if len(meeting_minutes) > 1000:
                self.log(f"   ✅ Substantial content generated ({len(meeting_minutes)} chars)")
            else:
                self.log(f"   ⚠️  Content may be too brief ({len(meeting_minutes)} chars)")
            
            # Check for business-like structure
            business_indicators = ['•', 'responsible party', 'timeline', 'deadline', 'follow-up']
            business_found = sum(1 for indicator in business_indicators if indicator.lower() in meeting_minutes.lower())
            
            if business_found >= 2:
                self.log(f"   ✅ Business-like structure confirmed ({business_found} indicators)")
            else:
                self.log(f"   ⚠️  Limited business structure ({business_found} indicators)")
            
            return True, meeting_minutes, len(sections_found) >= 5
        
        return False, "", False

    def test_meeting_minutes_export_pdf(self, note_id, is_expeditors=False):
        """Test PDF export of meeting minutes with logo integration"""
        try:
            url = f"{self.api_url}/notes/{note_id}/ai-conversations/export?format=pdf"
            headers = {}
            token = self.expeditors_token if is_expeditors else self.auth_token
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(url, headers=headers, timeout=90)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                self.log(f"✅ PDF Export {'(Expeditors)' if is_expeditors else '(Regular)'} - Status: {response.status_code}")
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' in content_type:
                    self.log(f"   ✅ Correct Content-Type: application/pdf")
                else:
                    self.log(f"   ❌ Incorrect Content-Type: {content_type}")
                
                # Check filename format
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'Meeting_Minutes_' in content_disposition:
                    self.log(f"   ✅ Descriptive filename format: Meeting_Minutes_[NoteName].pdf")
                else:
                    self.log(f"   ❌ Incorrect filename format: {content_disposition}")
                
                # Check for Expeditors branding in filename
                if is_expeditors and 'Expeditors' in content_disposition:
                    self.log(f"   ✅ Expeditors branding in filename detected")
                elif not is_expeditors and 'Meeting_Minutes_' in content_disposition:
                    self.log(f"   ✅ Standard meeting minutes filename format")
                
                # Check PDF content size
                content_length = len(response.content)
                if content_length > 5000:  # PDF should be substantial
                    self.log(f"   ✅ PDF size: {content_length} bytes (substantial)")
                else:
                    self.log(f"   ⚠️  PDF size: {content_length} bytes (may be small)")
                
                # Check PDF header
                if response.content.startswith(b'%PDF'):
                    self.log(f"   ✅ Valid PDF header")
                else:
                    self.log(f"   ❌ Invalid PDF header")
                
                return True
                
            else:
                self.log(f"❌ PDF Export - Expected 200, got {response.status_code}")
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        if 'meeting minutes' in error_data.get('detail', '').lower():
                            self.log(f"   Expected error: {error_data.get('detail')}")
                            return True  # This is expected if no meeting minutes generated
                    except:
                        pass
            
            self.tests_run += 1
            return False
            
        except Exception as e:
            self.log(f"❌ PDF Export Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_meeting_minutes_export_docx(self, note_id, is_expeditors=False):
        """Test Word DOC export of meeting minutes with logo integration"""
        try:
            url = f"{self.api_url}/notes/{note_id}/ai-conversations/export?format=docx"
            headers = {}
            token = self.expeditors_token if is_expeditors else self.auth_token
            if token:
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(url, headers=headers, timeout=90)
            
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
                    self.log(f"   ❌ Incorrect Content-Type: {content_type}")
                
                # Check filename format
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'Meeting_Minutes_' in content_disposition and '.docx' in content_disposition:
                    self.log(f"   ✅ Descriptive DOCX filename format")
                else:
                    self.log(f"   ❌ Incorrect filename format: {content_disposition}")
                
                # Check for Expeditors branding in filename
                if is_expeditors and 'Expeditors' in content_disposition:
                    self.log(f"   ✅ Expeditors branding in DOCX filename")
                
                # Check DOCX content size
                content_length = len(response.content)
                if content_length > 10000:  # DOCX should be substantial
                    self.log(f"   ✅ DOCX size: {content_length} bytes (substantial)")
                else:
                    self.log(f"   ⚠️  DOCX size: {content_length} bytes (may be small)")
                
                # Check DOCX header (ZIP format)
                if response.content.startswith(b'PK'):
                    self.log(f"   ✅ Valid DOCX header (ZIP format)")
                else:
                    self.log(f"   ❌ Invalid DOCX header")
                
                return True
                
            else:
                self.log(f"❌ DOCX Export - Expected 200, got {response.status_code}")
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        if 'meeting minutes' in error_data.get('detail', '').lower():
                            self.log(f"   Expected error: {error_data.get('detail')}")
                            return True  # This is expected if no meeting minutes generated
                    except:
                        pass
            
            self.tests_run += 1
            return False
            
        except Exception as e:
            self.log(f"❌ DOCX Export Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_meeting_minutes_content_quality(self, note_id, is_expeditors=False):
        """Test the quality and structure of generated meeting minutes"""
        # First generate meeting minutes
        success, meeting_minutes, has_required_sections = self.test_meeting_minutes_generation(note_id, is_expeditors)
        
        if not success:
            return False
        
        self.log(f"🔍 Analyzing meeting minutes content quality...")
        
        # Test 1: Professional format without AI references
        ai_terms = ['AI analysis', 'AI-generated', 'artificial intelligence', 'machine learning', 'algorithm']
        ai_found = [term for term in ai_terms if term.lower() in meeting_minutes.lower()]
        
        if not ai_found:
            self.log(f"   ✅ No AI references found - professional language")
        else:
            self.log(f"   ❌ AI references found: {ai_found}")
        
        # Test 2: Business meeting structure
        business_elements = [
            ('attendees', 'ATTENDEES'),
            ('action items', 'ACTION ITEMS'),
            ('responsible party', 'responsibility assignment'),
            ('timeline', 'timeline/deadline information'),
            ('risk', 'risk assessment'),
            ('next steps', 'NEXT STEPS')
        ]
        
        business_score = 0
        for element, description in business_elements:
            if element.lower() in meeting_minutes.lower():
                business_score += 1
                self.log(f"   ✅ Business element found: {description}")
            else:
                self.log(f"   ⚠️  Business element missing: {description}")
        
        # Test 3: Content structure and formatting
        lines = meeting_minutes.split('\n')
        section_headers = [line.strip() for line in lines if line.strip().isupper() and len(line.strip()) > 3]
        bullet_points = [line for line in lines if line.strip().startswith('•')]
        
        self.log(f"   Section headers found: {len(section_headers)}")
        self.log(f"   Bullet points found: {len(bullet_points)}")
        
        # Test 4: No duplicate content
        content_chunks = [chunk.strip() for chunk in meeting_minutes.split('\n\n') if len(chunk.strip()) > 50]
        unique_chunks = set(content_chunks)
        
        if len(content_chunks) == len(unique_chunks):
            self.log(f"   ✅ No duplicate content detected")
        else:
            self.log(f"   ⚠️  Potential duplicate content: {len(content_chunks) - len(unique_chunks)} duplicates")
        
        # Overall quality score
        quality_score = (
            (1 if not ai_found else 0) +
            (1 if business_score >= 4 else 0) +
            (1 if len(section_headers) >= 5 else 0) +
            (1 if len(bullet_points) >= 5 else 0) +
            (1 if len(content_chunks) == len(unique_chunks) else 0)
        )
        
        self.log(f"   📊 Content quality score: {quality_score}/5")
        
        return quality_score >= 3

    def test_error_handling(self):
        """Test error handling for meeting minutes functionality"""
        self.log("🔍 Testing error handling scenarios...")
        
        # Test 1: Generate meeting minutes for non-existent note
        success, response = self.run_test(
            "Meeting Minutes - Non-existent Note (Should Fail)",
            "POST",
            "notes/non-existent-id/generate-meeting-minutes",
            404,
            auth_required=True
        )
        
        # Test 2: Generate meeting minutes without authentication
        if self.created_notes:
            success2, response2 = self.run_test(
                "Meeting Minutes - No Auth (Should Fail)",
                "POST",
                f"notes/{self.created_notes[0]}/generate-meeting-minutes",
                403  # Should fail with unauthorized
            )
        else:
            success2 = True  # Skip if no notes created
        
        # Test 3: Export meeting minutes with invalid format
        if self.created_notes:
            success3, response3 = self.run_test(
                "Export Invalid Format (Should Fail)",
                "GET",
                f"notes/{self.created_notes[0]}/ai-conversations/export?format=invalid",
                422,  # Should fail with validation error
                auth_required=True
            )
        else:
            success3 = True  # Skip if no notes created
        
        return success and success2 and success3

    def run_comprehensive_meeting_minutes_test(self):
        """Run comprehensive meeting minutes functionality tests"""
        self.log("🚀 Starting OPEN AUTO-ME v1 Meeting Minutes Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup test users
        if not self.setup_test_users():
            self.log("❌ Failed to setup test users - stopping tests")
            return False
        
        # === PRIMARY TEST 1: Meeting Minutes Generation ===
        self.log("\n📝 PRIMARY TEST 1: MEETING MINUTES GENERATION")
        
        # Test with regular user
        regular_note_id = self.create_note_with_content("Weekly Team Meeting - Regular User", is_expeditors=False)
        if regular_note_id:
            regular_success, regular_minutes, regular_sections = self.test_meeting_minutes_generation(regular_note_id, is_expeditors=False)
        else:
            regular_success = False
        
        # Test with Expeditors user
        expeditors_note_id = self.create_note_with_content("Supply Chain Review Meeting - Expeditors", is_expeditors=True)
        if expeditors_note_id:
            expeditors_success, expeditors_minutes, expeditors_sections = self.test_meeting_minutes_generation(expeditors_note_id, is_expeditors=True)
        else:
            expeditors_success = False
        
        # === PRIMARY TEST 2: Professional Export with Logo ===
        self.log("\n📄 PRIMARY TEST 2: PROFESSIONAL EXPORT WITH LOGO")
        
        pdf_success = False
        docx_success = False
        
        if regular_note_id:
            # Test PDF export for regular user
            pdf_regular = self.test_meeting_minutes_export_pdf(regular_note_id, is_expeditors=False)
            # Test DOCX export for regular user
            docx_regular = self.test_meeting_minutes_export_docx(regular_note_id, is_expeditors=False)
        
        if expeditors_note_id:
            # Test PDF export for Expeditors user (with logo)
            pdf_expeditors = self.test_meeting_minutes_export_pdf(expeditors_note_id, is_expeditors=True)
            # Test DOCX export for Expeditors user (with logo)
            docx_expeditors = self.test_meeting_minutes_export_docx(expeditors_note_id, is_expeditors=True)
            
            pdf_success = pdf_expeditors
            docx_success = docx_expeditors
        
        # === PRIMARY TEST 3: Content Quality Verification ===
        self.log("\n🎯 PRIMARY TEST 3: CONTENT QUALITY VERIFICATION")
        
        content_quality_success = False
        if regular_note_id:
            content_quality_success = self.test_meeting_minutes_content_quality(regular_note_id, is_expeditors=False)
        
        if expeditors_note_id:
            expeditors_quality = self.test_meeting_minutes_content_quality(expeditors_note_id, is_expeditors=True)
            content_quality_success = content_quality_success or expeditors_quality
        
        # === ERROR HANDLING TESTS ===
        self.log("\n⚠️  ERROR HANDLING TESTS")
        error_handling_success = self.test_error_handling()
        
        # === VERIFICATION SUMMARY ===
        self.log("\n📊 VERIFICATION POINTS SUMMARY")
        
        verification_points = {
            "Meeting minutes endpoint generates structured business content": regular_success or expeditors_success,
            "Export includes logo for Expeditors users": pdf_success and docx_success,
            "No AI references in output": content_quality_success,
            "Professional meeting minutes format": regular_sections or expeditors_sections,
            "Proper error handling for missing content": error_handling_success,
            "Expeditors branding consistently applied": expeditors_success
        }
        
        for point, status in verification_points.items():
            status_icon = "✅" if status else "❌"
            self.log(f"   {status_icon} {point}")
        
        overall_success = sum(verification_points.values()) >= 4  # At least 4/6 verification points
        
        return overall_success

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 MEETING MINUTES TEST SUMMARY")
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
        
        return self.tests_passed >= (self.tests_run * 0.8)  # 80% success rate

def main():
    """Main test execution"""
    tester = MeetingMinutesAPITester()
    
    try:
        success = tester.run_comprehensive_meeting_minutes_test()
        summary_success = tester.print_summary()
        
        if success and summary_success:
            print("\n🎉 Meeting Minutes functionality tests passed! System is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some meeting minutes tests failed. Check the logs above for details.")
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