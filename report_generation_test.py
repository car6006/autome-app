#!/usr/bin/env python3
"""
Professional Report Generation Testing - Critical User Issue
Tests the report generation functionality that users are reporting as failing
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class ReportGenerationTester:
    def __init__(self, base_url="https://typescript-auth.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.created_notes = []
        self.test_user_data = {
            "email": f"report_test_user_{int(time.time())}@example.com",
            "username": f"reportuser{int(time.time())}",  # No underscore for validation
            "password": "ReportTest123!",
            "first_name": "Report",
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

    def setup_auth(self):
        """Setup authentication with proper error handling"""
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
            user_data = response.get('user', {})
            self.log(f"   Registered user ID: {user_data.get('id')}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
            return True
        else:
            self.log("❌ Authentication setup failed - cannot proceed with tests")
            return False

    def create_text_note_with_content(self, title, content):
        """Create a text note with specific content for testing"""
        note_data = {
            "title": title,
            "kind": "text",
            "text_content": content
        }
        
        success, response = self.run_test(
            f"Create Text Note: {title}",
            "POST",
            "notes",
            200,
            data=note_data,
            auth_required=True
        )
        
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   Created note ID: {note_id}")
            self.log(f"   Status: {response.get('status', 'N/A')}")
            return note_id
        return None

    def test_professional_report_generation(self, note_id):
        """Test POST /api/notes/{id}/generate-report endpoint"""
        success, response = self.run_test(
            f"Generate Professional Report for Note {note_id[:8]}...",
            "POST",
            f"notes/{note_id}/generate-report",
            200,
            auth_required=True,
            timeout=90  # Allow more time for AI processing
        )
        
        if success:
            # Check different possible response formats
            report = response.get('professional_report') or response.get('report', '')
            self.log(f"   Report generated: {len(report)} characters")
            self.log(f"   Note title: {response.get('note_title', 'N/A')}")
            self.log(f"   Generated at: {response.get('generated_at', 'N/A')}")
            
            # Check report quality
            if len(report) > 500:
                self.log(f"   ✅ Substantial report content")
            else:
                self.log(f"   ⚠️  Report seems short")
            
            # Check for professional sections
            professional_sections = ['EXECUTIVE SUMMARY', 'KEY INSIGHTS', 'ACTION ITEMS', 'RECOMMENDATIONS']
            found_sections = [section for section in professional_sections if section in report.upper()]
            
            if found_sections:
                self.log(f"   ✅ Professional sections found: {', '.join(found_sections)}")
            else:
                self.log(f"   ⚠️  No standard professional sections detected")
        
        return success, response

    def test_meeting_minutes_generation(self, note_id):
        """Test POST /api/notes/{id}/generate-meeting-minutes endpoint"""
        success, response = self.run_test(
            f"Generate Meeting Minutes for Note {note_id[:8]}...",
            "POST",
            f"notes/{note_id}/generate-meeting-minutes",
            200,
            auth_required=True,
            timeout=90  # Allow more time for AI processing
        )
        
        if success:
            meeting_minutes = response.get('meeting_minutes', '')
            self.log(f"   Meeting minutes generated: {len(meeting_minutes)} characters")
            self.log(f"   Note title: {response.get('note_title', 'N/A')}")
            self.log(f"   Generated at: {response.get('generated_at', 'N/A')}")
            self.log(f"   Is Expeditors user: {response.get('is_expeditors', False)}")
            
            # Check meeting minutes quality
            if len(meeting_minutes) > 300:
                self.log(f"   ✅ Substantial meeting minutes content")
            else:
                self.log(f"   ⚠️  Meeting minutes seem short")
            
            # Check for meeting minutes sections
            meeting_sections = ['EXECUTIVE SUMMARY', 'DISCUSSION', 'DECISIONS', 'ACTION ITEMS']
            found_sections = [section for section in meeting_sections if section in meeting_minutes.upper()]
            
            if found_sections:
                self.log(f"   ✅ Meeting sections found: {', '.join(found_sections)}")
            else:
                self.log(f"   ⚠️  No standard meeting sections detected")
        
        return success, response

    def test_batch_report_generation(self, note_ids):
        """Test batch report functionality"""
        if len(note_ids) < 2:
            self.log("⚠️  Need at least 2 notes for batch report testing")
            return False, {}
        
        # Try different batch report formats based on the server.py code
        batch_data = {
            "note_ids": note_ids[:3],  # Use up to 3 notes
            "title": "Test Batch Analysis Report",
            "format": "professional"
        }
        
        success, response = self.run_test(
            f"Generate Batch Report for {len(batch_data['note_ids'])} Notes",
            "POST",
            "notes/batch-report",
            200,
            data=batch_data,
            auth_required=True,
            timeout=120  # Allow more time for batch processing
        )
        
        if success:
            # Check different possible response formats
            batch_report = response.get('batch_report') or response.get('report', '')
            self.log(f"   Batch report generated: {len(batch_report)} characters")
            self.log(f"   Report title: {response.get('title', 'N/A')}")
            self.log(f"   Notes processed: {response.get('notes_processed', 0)}")
            self.log(f"   Generated at: {response.get('generated_at', 'N/A')}")
            
            # Check batch report quality
            if len(batch_report) > 1000:
                self.log(f"   ✅ Substantial batch report content")
            else:
                self.log(f"   ⚠️  Batch report seems short")
            
            # Check for comprehensive analysis sections
            batch_sections = ['EXECUTIVE SUMMARY', 'COMPREHENSIVE ANALYSIS', 'STRATEGIC RECOMMENDATIONS']
            found_sections = [section for section in batch_sections if section in batch_report.upper()]
            
            if found_sections:
                self.log(f"   ✅ Batch analysis sections found: {', '.join(found_sections)}")
            else:
                self.log(f"   ⚠️  No standard batch analysis sections detected")
        
        return success, response

    def test_error_handling_no_content(self):
        """Test report generation with notes that have no content"""
        # Create a note without content (empty audio note)
        success, response = self.run_test(
            "Create Empty Audio Note",
            "POST",
            "notes",
            200,
            data={"title": "Empty Note for Error Testing", "kind": "audio"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            return False
        
        empty_note_id = response['id']
        self.created_notes.append(empty_note_id)
        
        # Try to generate report for empty note
        success, response = self.run_test(
            "Generate Report for Empty Note (Should Fail)",
            "POST",
            f"notes/{empty_note_id}/generate-report",
            400,  # Should fail with 400
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Proper error handling for empty content")
        
        return success

    def test_error_handling_invalid_note_id(self):
        """Test report generation with invalid note IDs"""
        invalid_note_id = "invalid-note-id-12345"
        
        success, response = self.run_test(
            "Generate Report for Invalid Note ID (Should Fail)",
            "POST",
            f"notes/{invalid_note_id}/generate-report",
            404,  # Should fail with 404
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Proper error handling for invalid note ID")
        
        return success

    def test_error_handling_unauthorized(self):
        """Test report generation without authentication"""
        if not self.created_notes:
            return False
        
        # Temporarily remove auth token
        temp_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Generate Report Without Auth (Should Fail)",
            "POST",
            f"notes/{self.created_notes[0]}/generate-report",
            403,  # Should fail with 403
            auth_required=True
        )
        
        # Restore auth token
        self.auth_token = temp_token
        
        if success:
            self.log(f"   ✅ Proper authentication requirement enforced")
        
        return success

    def run_comprehensive_report_tests(self):
        """Run all report generation tests as requested in the review"""
        self.log("🚀 STARTING PROFESSIONAL REPORT GENERATION TESTS")
        self.log("Testing the report generation functionality that users report as failing")
        self.log("=" * 80)
        
        # Step 1: Create a test user account and authenticate
        if not self.setup_auth():
            return False
        
        # Step 2: Create test notes with content (audio transcripts or text content)
        self.log("\n📝 CREATING TEST NOTES WITH CONTENT")
        
        # Create text notes with different types of content as specified in review
        meeting_content = """
        Meeting: Q4 Strategy Planning Session
        Date: December 19, 2024
        Attendees: CEO, CTO, VP Sales, VP Marketing
        
        Key Discussion Points:
        - Reviewed Q3 performance metrics showing 15% growth
        - Discussed market expansion opportunities in Asia-Pacific region
        - Analyzed competitor landscape and positioning strategies
        - Evaluated technology infrastructure needs for scaling
        - Assessed team capacity and hiring requirements
        
        Decisions Made:
        - Approved $2M budget for Asia-Pacific expansion
        - Authorized hiring of 10 additional engineers
        - Selected new CRM platform for sales team
        - Established quarterly review process for strategic initiatives
        
        Action Items:
        - Legal team to research regulatory requirements in target markets
        - HR to begin recruitment process for engineering positions
        - IT to implement new CRM system by Q1 2025
        - Marketing to develop localized campaigns for new regions
        
        Risks and Concerns:
        - Currency fluctuation impact on international operations
        - Potential talent shortage in competitive tech market
        - Integration challenges with new technology systems
        - Regulatory compliance complexity in multiple jurisdictions
        """
        
        project_content = """
        Project Status Report: Digital Transformation Initiative
        
        Current Progress:
        - Phase 1 (Infrastructure): 85% complete
        - Phase 2 (Application Migration): 60% complete  
        - Phase 3 (User Training): 25% complete
        
        Key Achievements:
        - Successfully migrated 12 core applications to cloud platform
        - Reduced system downtime by 40% compared to legacy infrastructure
        - Trained 150+ employees on new digital tools and processes
        - Established automated backup and disaster recovery procedures
        
        Challenges Encountered:
        - Data migration complexity higher than anticipated
        - User adoption slower than expected in some departments
        - Integration issues between legacy and new systems
        - Budget overrun of 8% due to additional security requirements
        
        Upcoming Milestones:
        - Complete remaining application migrations by January 31
        - Finish comprehensive user training program by February 15
        - Conduct full system security audit by March 1
        - Go-live with complete digital platform by March 15
        """
        
        sales_content = """
        Sales Performance Analysis - Q4 2024
        
        Revenue Metrics:
        - Total Revenue: $4.2M (12% above target)
        - New Customer Acquisition: 85 accounts
        - Customer Retention Rate: 94%
        - Average Deal Size: $49,500 (8% increase from Q3)
        
        Top Performing Products:
        - Enterprise Software Suite: $1.8M revenue
        - Professional Services: $1.2M revenue
        - Cloud Infrastructure: $900K revenue
        - Training and Certification: $300K revenue
        
        Strategic Recommendations:
        - Invest in AI-powered sales tools for better lead qualification
        - Expand presence in healthcare vertical market
        - Develop partnership program with system integrators
        - Create specialized pricing for mid-market customers
        """
        
        # Create the test notes
        meeting_note_id = self.create_text_note_with_content("Q4 Strategy Planning Meeting", meeting_content)
        project_note_id = self.create_text_note_with_content("Digital Transformation Project Status", project_content)
        sales_note_id = self.create_text_note_with_content("Q4 Sales Performance Analysis", sales_content)
        
        valid_note_ids = [note_id for note_id in [meeting_note_id, project_note_id, sales_note_id] if note_id]
        
        if len(valid_note_ids) < 2:
            self.log("❌ Failed to create sufficient test notes")
            return False
        
        self.log(f"✅ Created {len(valid_note_ids)} test notes successfully")
        
        # Step 3: Test report generation endpoint: POST /api/notes/{id}/generate-report
        self.log("\n📊 TESTING REPORT GENERATION ENDPOINT")
        
        report_tests_passed = 0
        total_report_tests = 0
        
        for note_id in valid_note_ids:
            total_report_tests += 1
            success, response = self.test_professional_report_generation(note_id)
            if success:
                report_tests_passed += 1
        
        # Step 4: Test meeting minutes endpoint: POST /api/notes/{id}/generate-meeting-minutes
        self.log("\n📋 TESTING MEETING MINUTES ENDPOINT")
        
        minutes_tests_passed = 0
        total_minutes_tests = 0
        
        for note_id in valid_note_ids:
            total_minutes_tests += 1
            success, response = self.test_meeting_minutes_generation(note_id)
            if success:
                minutes_tests_passed += 1
        
        # Step 5: Test batch report functionality if available
        self.log("\n📈 TESTING BATCH REPORT FUNCTIONALITY")
        
        batch_success, batch_response = self.test_batch_report_generation(valid_note_ids)
        
        # Step 6: Error handling - test with notes that have no content, invalid note IDs
        self.log("\n🚨 TESTING ERROR HANDLING")
        
        error_tests = [
            self.test_error_handling_no_content(),
            self.test_error_handling_invalid_note_id(),
            self.test_error_handling_unauthorized()
        ]
        
        error_tests_passed = sum(error_tests)
        
        # Step 7: Summary and Analysis
        self.log("\n" + "=" * 80)
        self.log("📊 PROFESSIONAL REPORT GENERATION TEST RESULTS")
        self.log("=" * 80)
        
        self.log(f"Total Tests Run: {self.tests_run}")
        self.log(f"Total Tests Passed: {self.tests_passed}")
        self.log(f"Overall Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        self.log(f"\n📊 Professional Reports: {report_tests_passed}/{total_report_tests} passed")
        self.log(f"📋 Meeting Minutes: {minutes_tests_passed}/{total_minutes_tests} passed")
        self.log(f"📈 Batch Reports: {1 if batch_success else 0}/1 passed")
        self.log(f"🚨 Error Handling: {error_tests_passed}/{len(error_tests)} passed")
        
        # Determine if the critical functionality is working
        critical_functionality_working = (
            report_tests_passed > 0 and 
            minutes_tests_passed > 0 and 
            error_tests_passed >= 2
        )
        
        if critical_functionality_working:
            self.log("\n✅ CRITICAL REPORT GENERATION FUNCTIONALITY IS WORKING")
            self.log("   Users should be able to generate reports from the actions dropdown")
            if batch_success:
                self.log("✅ BATCH REPORT FUNCTIONALITY IS ALSO WORKING")
            else:
                self.log("⚠️  Batch report functionality may have issues")
        else:
            self.log("\n❌ CRITICAL REPORT GENERATION FUNCTIONALITY HAS ISSUES")
            self.log("   This explains why users cannot generate reports from actions dropdown")
            
            # Provide specific diagnostics
            if report_tests_passed == 0:
                self.log("   🔍 Professional report generation is completely failing")
            if minutes_tests_passed == 0:
                self.log("   🔍 Meeting minutes generation is completely failing")
            if error_tests_passed < 2:
                self.log("   🔍 Error handling is not working properly")
        
        # Cleanup info
        self.log(f"\n🧹 Created {len(self.created_notes)} test notes during testing")
        
        return critical_functionality_working

def main():
    tester = ReportGenerationTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())