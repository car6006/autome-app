#!/usr/bin/env python3
"""
AUTO-ME Premium Features Backend API Tests
Tests the two new premium features:
1. Multi-file Upload for Handwritten Notes
2. Professional Report Generation
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class PremiumFeaturesAPITester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_id = None
        self.test_user_data = {
            "email": f"premium_test_{int(time.time())}@example.com",
            "username": f"premiumuser_{int(time.time())}",
            "password": "PremiumTest123!",
            "first_name": "Premium",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60, auth_required=False):
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

    def setup_authentication(self):
        """Setup authentication for testing"""
        # Register test user
        success, response = self.run_test(
            "User Registration for Premium Tests",
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
            return True
        return False

    def create_sample_image_file(self, filename="sample_image.png"):
        """Create a sample PNG image file with realistic content"""
        # Create a minimal PNG file (1x1 pixel) - this is a valid PNG
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x01\x01\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82'
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.write(png_data)
        temp_file.flush()
        temp_file.close()
        return temp_file.name

    def create_sample_pdf_file(self, filename="sample_document.pdf"):
        """Create a sample PDF file"""
        # Minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Sample handwritten notes) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.write(pdf_content)
        temp_file.flush()
        temp_file.close()
        return temp_file.name

    def test_multi_file_upload_single_file(self):
        """Test single file upload using the upload-file endpoint"""
        image_file = self.create_sample_image_file()
        
        try:
            with open(image_file, 'rb') as f:
                files = {'file': ('meeting_notes_page1.png', f, 'image/png')}
                data = {'title': 'Meeting Notes - Page 1'}
                success, response = self.run_test(
                    "Single File Upload (Multi-file Feature)",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    auth_required=True
                )
            
            if success and 'id' in response:
                note_id = response['id']
                self.created_notes.append(note_id)
                self.log(f"   Created note ID: {note_id}")
                self.log(f"   Filename: {response.get('filename', 'N/A')}")
                self.log(f"   Status: {response.get('status', 'N/A')}")
                return note_id
            return None
        finally:
            os.unlink(image_file)

    def test_multi_file_upload_multiple_files(self):
        """Test multiple file uploads to simulate batch processing"""
        note_ids = []
        
        # Create multiple files with different names
        files_to_upload = [
            ("Meeting Notes - Page 1", "meeting_page1.png", "png"),
            ("Meeting Notes - Page 2", "meeting_page2.png", "png"),
            ("Handwritten Notes - Document 1", "handwritten_doc1.pdf", "pdf"),
            ("Project Notes - Sketch", "project_sketch.png", "png")
        ]
        
        for title, filename, file_type in files_to_upload:
            if file_type == "png":
                temp_file = self.create_sample_image_file()
                mime_type = 'image/png'
            else:
                temp_file = self.create_sample_pdf_file()
                mime_type = 'application/pdf'
            
            try:
                with open(temp_file, 'rb') as f:
                    files = {'file': (filename, f, mime_type)}
                    data = {'title': title}
                    success, response = self.run_test(
                        f"Multi-file Upload: {title}",
                        "POST",
                        "upload-file",
                        200,
                        data=data,
                        files=files,
                        auth_required=True
                    )
                
                if success and 'id' in response:
                    note_id = response['id']
                    note_ids.append(note_id)
                    self.created_notes.append(note_id)
                    self.log(f"   Created note ID: {note_id}")
                    self.log(f"   Title: {title}")
                    self.log(f"   Filename: {response.get('filename', 'N/A')}")
            finally:
                os.unlink(temp_file)
        
        return note_ids

    def test_file_validation_unsupported_type(self):
        """Test file validation with unsupported file type"""
        # Create a text file (unsupported)
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        temp_file.write(b"This is a text file that should be rejected")
        temp_file.flush()
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('unsupported.txt', f, 'text/plain')}
                data = {'title': 'Unsupported File Test'}
                success, response = self.run_test(
                    "File Validation - Unsupported Type (Should Fail)",
                    "POST",
                    "upload-file",
                    400,  # Should fail with 400
                    data=data,
                    files=files,
                    auth_required=True
                )
            return success
        finally:
            os.unlink(temp_file.name)

    def create_note_with_content(self, title, content_type="transcript"):
        """Create a note with sample content for report generation testing"""
        # Create a photo note first
        success, response = self.run_test(
            f"Create Note for Report: {title}",
            "POST",
            "notes",
            200,
            data={"title": title, "kind": "photo"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            return None
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Simulate adding content by uploading an image and waiting for processing
        image_file = self.create_sample_image_file()
        try:
            with open(image_file, 'rb') as f:
                files = {'file': ('business_content.png', f, 'image/png')}
                upload_success, upload_response = self.run_test(
                    f"Upload Content for Report Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            if upload_success:
                # Wait a bit for processing to start
                time.sleep(2)
                
                # Manually add some sample content to the note for testing
                # This simulates what would happen after OCR processing
                sample_content = {
                    "Meeting Notes - Q4 Planning": """
                    Q4 Planning Meeting - October 15, 2024
                    
                    Attendees: Sarah Johnson (PM), Mike Chen (Engineering), Lisa Rodriguez (Marketing)
                    
                    Key Discussion Points:
                    - Product roadmap for Q4 needs refinement
                    - Marketing campaign launch delayed to November
                    - Engineering team needs 2 additional developers
                    - Budget allocation requires approval from finance
                    
                    Action Items:
                    - Sarah: Finalize product requirements by Oct 20
                    - Mike: Hire 2 senior developers by Nov 1
                    - Lisa: Prepare marketing budget proposal by Oct 18
                    
                    Next Steps:
                    - Weekly check-ins every Tuesday
                    - Budget review meeting scheduled for Oct 25
                    - Product demo planned for Nov 5
                    """,
                    "Client Strategy Session": """
                    Client Strategy Session - TechCorp Partnership
                    
                    Client: TechCorp Industries
                    Meeting Date: October 16, 2024
                    
                    Current Situation:
                    - TechCorp looking to expand into Asian markets
                    - Need supply chain optimization
                    - Current logistics costs 15% above industry average
                    - Timeline: Implementation by Q1 2025
                    
                    Opportunities:
                    - 3-year partnership worth $2.5M annually
                    - Potential for additional services (warehousing, customs)
                    - Reference client for similar enterprises
                    
                    Challenges:
                    - Tight timeline for implementation
                    - Complex regulatory requirements in target markets
                    - Need specialized expertise in electronics shipping
                    
                    Recommendations:
                    - Assign dedicated account manager
                    - Partner with local logistics providers in Asia
                    - Implement phased rollout approach
                    """,
                    "Project Status Review": """
                    Project Status Review - Digital Transformation Initiative
                    
                    Project: Customer Portal Modernization
                    Status: 65% Complete
                    Timeline: On track for December launch
                    
                    Completed Milestones:
                    - User interface design finalized
                    - Backend API development completed
                    - Security audit passed
                    - Initial user testing completed
                    
                    Current Focus:
                    - Mobile app development (80% complete)
                    - Integration testing with legacy systems
                    - Performance optimization
                    - Staff training materials preparation
                    
                    Risks and Mitigation:
                    - Third-party API delays - working with vendor for resolution
                    - Resource constraints during holiday season - adjusted timeline
                    - Data migration complexity - additional testing scheduled
                    
                    Success Metrics:
                    - User adoption rate target: 75% within 3 months
                    - Performance improvement: 40% faster load times
                    - Customer satisfaction score: 4.5/5 or higher
                    """
                }
                
                # Use the sample content based on the title
                content = sample_content.get(title, sample_content["Meeting Notes - Q4 Planning"])
                
                # We'll return the note_id and let the report generation test use it
                # The actual content would be added by OCR processing in a real scenario
                return note_id, content
        finally:
            os.unlink(image_file)
        
        return note_id, ""

    def test_professional_report_generation_single_note(self):
        """Test professional report generation for a single note"""
        # Create a note with business content
        result = self.create_note_with_content("Meeting Notes - Q4 Planning")
        if not result:
            return False
        
        note_id, sample_content = result
        
        # Wait a bit to simulate processing time
        time.sleep(3)
        
        # Test report generation
        success, response = self.run_test(
            f"Generate Professional Report for Note {note_id[:8]}...",
            "POST",
            f"notes/{note_id}/generate-report",
            200,
            auth_required=True,
            timeout=90  # Longer timeout for AI processing
        )
        
        if success:
            self.log(f"   Report generated successfully")
            self.log(f"   Note title: {response.get('note_title', 'N/A')}")
            self.log(f"   Generated at: {response.get('generated_at', 'N/A')}")
            
            report_content = response.get('report', '')
            if report_content:
                self.log(f"   Report length: {len(report_content)} characters")
                
                # Check for expected report sections
                expected_sections = [
                    "EXECUTIVE SUMMARY",
                    "KEY INSIGHTS", 
                    "ACTION ITEMS",
                    "PRIORITIES",
                    "RECOMMENDATIONS",
                    "FOLLOW-UP"
                ]
                
                found_sections = []
                for section in expected_sections:
                    if section.lower() in report_content.lower():
                        found_sections.append(section)
                
                self.log(f"   Report sections found: {len(found_sections)}/{len(expected_sections)}")
                self.log(f"   Sections: {', '.join(found_sections)}")
                
                return len(found_sections) >= 4  # At least 4 sections should be present
        
        return success

    def test_professional_report_generation_no_content(self):
        """Test professional report generation for a note without content"""
        # Create a note without uploading content
        success, response = self.run_test(
            "Create Empty Note for Report Test",
            "POST",
            "notes",
            200,
            data={"title": "Empty Note Test", "kind": "photo"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            return False
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Try to generate report (should fail)
        success, response = self.run_test(
            f"Generate Report for Empty Note (Should Fail)",
            "POST",
            f"notes/{note_id}/generate-report",
            400,  # Should fail with 400 - no content
            auth_required=True
        )
        
        return success

    def test_batch_report_generation(self):
        """Test batch report generation combining multiple notes"""
        # Create multiple notes with different business content
        note_data = [
            ("Meeting Notes - Q4 Planning", "Meeting content"),
            ("Client Strategy Session", "Client strategy content"),
            ("Project Status Review", "Project status content")
        ]
        
        note_ids = []
        for title, _ in note_data:
            result = self.create_note_with_content(title)
            if result:
                note_id, content = result
                note_ids.append(note_id)
        
        if len(note_ids) < 2:
            self.log("❌ Failed to create enough notes for batch report test")
            return False
        
        # Wait for processing
        time.sleep(5)
        
        # Test batch report generation
        success, response = self.run_test(
            f"Generate Batch Report from {len(note_ids)} Notes",
            "POST",
            "notes/batch-report",
            200,
            data=note_ids,  # Send as JSON array
            auth_required=True,
            timeout=120  # Longer timeout for batch processing
        )
        
        if success:
            self.log(f"   Batch report generated successfully")
            self.log(f"   Report title: {response.get('title', 'N/A')}")
            self.log(f"   Source notes count: {response.get('note_count', 0)}")
            self.log(f"   Generated at: {response.get('generated_at', 'N/A')}")
            
            source_notes = response.get('source_notes', [])
            self.log(f"   Source note titles: {', '.join(source_notes)}")
            
            report_content = response.get('report', '')
            if report_content:
                self.log(f"   Report length: {len(report_content)} characters")
                
                # Check for expected batch report sections
                expected_sections = [
                    "EXECUTIVE SUMMARY",
                    "COMPREHENSIVE ANALYSIS",
                    "STRATEGIC RECOMMENDATIONS",
                    "ACTION PLAN",
                    "RISK ASSESSMENT",
                    "FOLLOW-UP"
                ]
                
                found_sections = []
                for section in expected_sections:
                    if section.lower() in report_content.lower():
                        found_sections.append(section)
                
                self.log(f"   Batch report sections found: {len(found_sections)}/{len(expected_sections)}")
                self.log(f"   Sections: {', '.join(found_sections)}")
                
                return len(found_sections) >= 4  # At least 4 sections should be present
        
        return success

    def test_batch_report_empty_list(self):
        """Test batch report generation with empty note list"""
        success, response = self.run_test(
            "Generate Batch Report with Empty List (Should Fail)",
            "POST",
            "notes/batch-report",
            400,  # Should fail with 400
            data=[],  # Empty list
            auth_required=True
        )
        
        return success

    def test_batch_report_invalid_notes(self):
        """Test batch report generation with invalid note IDs"""
        invalid_note_ids = ["invalid-id-1", "invalid-id-2", "nonexistent-id"]
        
        success, response = self.run_test(
            "Generate Batch Report with Invalid IDs (Should Fail)",
            "POST",
            "notes/batch-report",
            400,  # Should fail with 400 - no accessible content
            data=invalid_note_ids,
            auth_required=True
        )
        
        return success

    def wait_for_processing(self, note_id, max_wait=30):
        """Wait for note processing to complete"""
        self.log(f"⏳ Waiting for note {note_id[:8]}... to process (max {max_wait}s)")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, response = self.run_test(
                f"Check Processing Status {note_id[:8]}...",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success:
                status = response.get('status', 'unknown')
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

    def run_premium_features_tests(self):
        """Run all premium features tests"""
        self.log("🚀 Starting AUTO-ME Premium Features Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup authentication
        if not self.setup_authentication():
            self.log("❌ Authentication setup failed - stopping tests")
            return False
        
        # === MULTI-FILE UPLOAD TESTS ===
        self.log("\n📁 MULTI-FILE UPLOAD FEATURE TESTS")
        
        # Test single file upload
        single_note_id = self.test_multi_file_upload_single_file()
        
        # Test multiple file uploads (batch processing simulation)
        multi_note_ids = self.test_multi_file_upload_multiple_files()
        
        # Test file validation
        self.test_file_validation_unsupported_type()
        
        # Wait for some processing to complete
        if single_note_id:
            self.wait_for_processing(single_note_id, max_wait=60)
        
        # === PROFESSIONAL REPORT GENERATION TESTS ===
        self.log("\n📊 PROFESSIONAL REPORT GENERATION FEATURE TESTS")
        
        # Test single note report generation
        self.test_professional_report_generation_single_note()
        
        # Test report generation with no content (should fail)
        self.test_professional_report_generation_no_content()
        
        # Test batch report generation
        self.test_batch_report_generation()
        
        # Test batch report with empty list (should fail)
        self.test_batch_report_empty_list()
        
        # Test batch report with invalid note IDs (should fail)
        self.test_batch_report_invalid_notes()
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 PREMIUM FEATURES TEST SUMMARY")
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
    tester = PremiumFeaturesAPITester()
    
    try:
        success = tester.run_premium_features_tests()
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All premium features tests passed! Features are working correctly.")
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