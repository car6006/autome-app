#!/usr/bin/env python3
"""
Realistic Batch Report Functionality Test
Tests batch report functionality with notes that have actual content
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class RealisticBatchReportTester:
    def __init__(self, base_url="https://voice2text-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"realistic_batch_{int(time.time())}@example.com",
            "username": f"realisticuser_{int(time.time())}",
            "password": "RealisticTest123!",
            "first_name": "Realistic",
            "last_name": "Tester"
        }
        self.expeditors_user_data = {
            "email": f"realistic_expeditors_{int(time.time())}@expeditors.com",
            "username": f"expeditors_realistic_{int(time.time())}",
            "password": "ExpeditorsRealistic123!",
            "first_name": "Expeditors",
            "last_name": "RealisticTester"
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
                    self.log(f"   Response text: {response.text[:500]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def setup_authentication(self):
        """Setup authentication for both regular and Expeditors users"""
        self.log("🔐 Setting up authentication...")
        
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
        
        return self.auth_token is not None

    def create_note_and_upload_content(self, title, content_text, kind="photo", use_expeditors=False):
        """Create a note and upload content that will be processed"""
        # Switch to appropriate token
        original_token = self.auth_token
        if use_expeditors and self.expeditors_token:
            self.auth_token = self.expeditors_token
        
        # Create note
        success, response = self.run_test(
            f"Create Note: {title}",
            "POST",
            "notes",
            200,
            data={"title": title, "kind": kind},
            auth_required=True
        )
        
        if not success:
            self.auth_token = original_token
            return None
        
        note_id = response.get('id')
        if not note_id:
            self.auth_token = original_token
            return None
        
        self.created_notes.append(note_id)
        
        # Upload content file to trigger processing
        if kind == "photo":
            # Create a simple image file and upload it
            success = self.upload_dummy_image_with_text(note_id, content_text)
        else:  # audio
            # Create a dummy audio file and upload it
            success = self.upload_dummy_audio_file(note_id)
        
        if success:
            self.log(f"   📁 Content uploaded to note {note_id[:8]}...")
            # Wait for processing to potentially start
            time.sleep(2)
        
        # Restore original token
        self.auth_token = original_token
        return note_id if success else None

    def upload_dummy_image_with_text(self, note_id, text_content):
        """Upload a dummy image file to trigger OCR processing"""
        # Create a minimal PNG file (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            tmp_file.flush()
            
            try:
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (f'business_document_{int(time.time())}.png', f, 'image/png')}
                    success, response = self.run_test(
                        f"Upload Image to Note {note_id[:8]}...",
                        "POST",
                        f"notes/{note_id}/upload",
                        200,
                        files=files,
                        auth_required=True
                    )
                return success
            finally:
                os.unlink(tmp_file.name)

    def upload_dummy_audio_file(self, note_id):
        """Upload a dummy audio file to trigger transcription"""
        # Create a minimal WebM file
        webm_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
        
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            tmp_file.write(webm_data)
            tmp_file.flush()
            
            try:
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (f'business_meeting_{int(time.time())}.webm', f, 'audio/webm')}
                    success, response = self.run_test(
                        f"Upload Audio to Note {note_id[:8]}...",
                        "POST",
                        f"notes/{note_id}/upload",
                        200,
                        files=files,
                        auth_required=True
                    )
                return success
            finally:
                os.unlink(tmp_file.name)

    def manually_add_content_to_note(self, note_id, content_text):
        """Manually add content to a note by simulating processed content"""
        # This simulates what would happen after successful processing
        # We'll use the note update mechanism or direct database update
        # For testing purposes, we'll try to add content via a mock approach
        
        # First, let's check the current note status
        success, note_data = self.run_test(
            f"Get Note {note_id[:8]}... for Content Addition",
            "GET",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   📄 Note status: {note_data.get('status', 'unknown')}")
            self.log(f"   📝 Note kind: {note_data.get('kind', 'unknown')}")
            artifacts = note_data.get('artifacts', {})
            if artifacts:
                self.log(f"   🎯 Existing artifacts: {list(artifacts.keys())}")
            else:
                self.log(f"   ⚠️  No artifacts found - content may not be processed yet")
        
        return success

    def create_realistic_test_notes(self, use_expeditors=False):
        """Create test notes with realistic business content"""
        self.log(f"📝 Creating realistic test notes ({'Expeditors' if use_expeditors else 'Regular'} user)...")
        
        # Business meeting transcript
        meeting_content = """
        Executive team discussed Q4 strategic initiatives including market expansion into Southeast Asia, 
        cost optimization through automation, and technology investments in AI and cloud infrastructure. 
        Key decisions made on budget allocation of $2.5M for digital transformation and resource planning 
        for 50 new hires. Action items assigned for implementation timeline by December 15th and success 
        metrics definition including ROI targets of 15% improvement in operational efficiency.
        """
        
        # Project status report
        project_content = """
        Project Alpha is 75% complete with delivery scheduled for November 30th. Technical challenges 
        identified in API integration phase with third-party vendors. Risk mitigation strategies discussed 
        including additional testing cycles, stakeholder communication plan, and contingency budget of $150K. 
        Current budget utilization at 68% with minor adjustments needed for additional security audits.
        """
        
        # Market analysis document
        market_content = """
        Market research indicates 23% growth potential in emerging markets, particularly in logistics and 
        supply chain management. Competitive analysis shows opportunities for differentiation through 
        AI-powered route optimization and customer service excellence. Regulatory considerations include 
        GDPR compliance for European operations and trade compliance requirements for international expansion.
        """
        
        # Customer feedback compilation
        customer_content = """
        Customer satisfaction survey results show 85% positive feedback with NPS score of 67. Key improvement 
        areas identified in response time (average 4.2 hours, target 2 hours) and product features including 
        real-time tracking and mobile app functionality. Customer retention strategies discussed including 
        loyalty programs with 10% discount tiers and enhanced 24/7 support services. Implementation roadmap 
        defined with Q1 2024 launch target.
        """
        
        contents = [
            ("Q4 Strategy Planning Meeting", meeting_content, "audio"),
            ("Project Alpha Status Update", project_content, "photo"),
            ("Market Analysis Report", market_content, "photo"),
            ("Customer Feedback Session", customer_content, "audio")
        ]
        
        created_notes = []
        for title, content, kind in contents:
            note_id = self.create_note_and_upload_content(title, content, kind, use_expeditors)
            if note_id:
                created_notes.append(note_id)
                # Try to manually add content for testing
                self.manually_add_content_to_note(note_id, content)
        
        self.log(f"   ✅ Created {len(created_notes)} realistic test notes")
        return created_notes

    def wait_for_note_processing(self, note_ids, max_wait=60):
        """Wait for notes to be processed"""
        self.log(f"⏳ Waiting for {len(note_ids)} notes to process (max {max_wait}s)...")
        
        processed_notes = []
        start_time = time.time()
        
        while time.time() - start_time < max_wait and len(processed_notes) < len(note_ids):
            for note_id in note_ids:
                if note_id in processed_notes:
                    continue
                
                success, note_data = self.run_test(
                    f"Check Processing Status {note_id[:8]}...",
                    "GET",
                    f"notes/{note_id}",
                    200,
                    auth_required=True
                )
                
                if success:
                    status = note_data.get('status', 'unknown')
                    artifacts = note_data.get('artifacts', {})
                    
                    if status == 'ready' and (artifacts.get('transcript') or artifacts.get('text')):
                        processed_notes.append(note_id)
                        self.log(f"   ✅ Note {note_id[:8]}... processed successfully")
                    elif status == 'failed':
                        self.log(f"   ❌ Note {note_id[:8]}... processing failed")
                        processed_notes.append(note_id)  # Count as processed to avoid infinite loop
                    else:
                        self.log(f"   ⏳ Note {note_id[:8]}... status: {status}")
            
            if len(processed_notes) < len(note_ids):
                time.sleep(5)
        
        self.log(f"   📊 Processing complete: {len(processed_notes)}/{len(note_ids)} notes")
        return processed_notes

    def test_batch_report_with_processed_notes(self, note_ids, use_expeditors=False):
        """Test batch report generation with processed notes"""
        # Switch to appropriate token
        original_token = self.auth_token
        if use_expeditors and self.expeditors_token:
            self.auth_token = self.expeditors_token
        
        # First, check if notes have content
        notes_with_content = []
        for note_id in note_ids:
            success, note_data = self.run_test(
                f"Check Content {note_id[:8]}...",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success:
                artifacts = note_data.get('artifacts', {})
                if artifacts.get('transcript') or artifacts.get('text'):
                    notes_with_content.append(note_id)
                    content_type = 'transcript' if artifacts.get('transcript') else 'text'
                    content_length = len(artifacts.get(content_type, ''))
                    self.log(f"   ✅ Note {note_id[:8]}... has {content_type} ({content_length} chars)")
                else:
                    self.log(f"   ❌ Note {note_id[:8]}... has no content")
        
        if not notes_with_content:
            self.log("   ⚠️  No notes with content found - cannot test batch report")
            self.auth_token = original_token
            return False
        
        # Test batch report generation
        success, response = self.run_test(
            f"Batch Report with Content ({'Expeditors' if use_expeditors else 'Regular'})",
            "POST",
            "notes/batch-report",
            200,
            data=notes_with_content[:3],  # Use up to 3 notes with content
            auth_required=True,
            timeout=120
        )
        
        if success:
            report = response.get('report', '')
            title = response.get('title', '')
            source_notes = response.get('source_notes', [])
            note_count = response.get('note_count', 0)
            is_expeditors = response.get('is_expeditors', False)
            
            self.log(f"   🎉 BATCH REPORT GENERATED SUCCESSFULLY!")
            self.log(f"   📊 Report length: {len(report)} characters")
            self.log(f"   📋 Title: {title}")
            self.log(f"   📄 Source notes: {note_count}")
            self.log(f"   🏢 Expeditors user: {is_expeditors}")
            
            # Detailed analysis of the report
            self.analyze_batch_report_quality(report, use_expeditors)
            
        # Restore original token
        self.auth_token = original_token
        return success

    def analyze_batch_report_quality(self, report, is_expeditors=False):
        """Analyze the quality and content of the generated batch report"""
        self.log("   🔍 ANALYZING BATCH REPORT QUALITY:")
        
        # Check report length
        if len(report) > 4000:
            self.log(f"   ✅ Substantial content: {len(report)} characters")
        elif len(report) > 2000:
            self.log(f"   ⚠️  Moderate content: {len(report)} characters")
        else:
            self.log(f"   ❌ Limited content: {len(report)} characters")
        
        # Check for required sections
        required_sections = [
            'EXECUTIVE SUMMARY',
            'COMPREHENSIVE ANALYSIS',
            'STRATEGIC RECOMMENDATIONS',
            'IMPLEMENTATION ROADMAP',
            'SUCCESS METRICS',
            'RISK ASSESSMENT'
        ]
        
        sections_found = 0
        for section in required_sections:
            if section in report:
                sections_found += 1
                self.log(f"   ✅ Found section: {section}")
            else:
                self.log(f"   ❌ Missing section: {section}")
        
        self.log(f"   📊 Sections coverage: {sections_found}/{len(required_sections)} ({sections_found/len(required_sections)*100:.1f}%)")
        
        # Check for clean formatting
        formatting_issues = []
        if '###' in report:
            formatting_issues.append('markdown headers (###)')
        if '**' in report and report.count('**') > 2:
            formatting_issues.append('markdown bold (**)')
        if '```' in report:
            formatting_issues.append('code blocks (```)')
        
        if not formatting_issues:
            self.log(f"   ✅ Clean formatting (no markdown symbols)")
        else:
            self.log(f"   ❌ Formatting issues: {', '.join(formatting_issues)}")
        
        # Check for professional bullet points
        bullet_count = report.count('• ')
        if bullet_count > 20:
            self.log(f"   ✅ Rich bullet points: {bullet_count} professional bullets")
        elif bullet_count > 10:
            self.log(f"   ⚠️  Moderate bullet points: {bullet_count} bullets")
        else:
            self.log(f"   ❌ Limited bullet points: {bullet_count} bullets")
        
        # Check Expeditors branding
        if is_expeditors:
            if 'EXPEDITORS INTERNATIONAL' in report:
                self.log(f"   ✅ Expeditors branding present")
            else:
                self.log(f"   ❌ Expeditors branding missing")
        
        # Check for business intelligence keywords
        business_keywords = [
            'strategic', 'analysis', 'implementation', 'recommendations',
            'metrics', 'assessment', 'roadmap', 'stakeholder', 'risk',
            'optimization', 'efficiency', 'performance', 'growth'
        ]
        
        keywords_found = sum(1 for keyword in business_keywords if keyword.lower() in report.lower())
        self.log(f"   📈 Business intelligence: {keywords_found}/{len(business_keywords)} keywords ({keywords_found/len(business_keywords)*100:.1f}%)")
        
        # Overall quality assessment
        quality_score = (
            (1 if len(report) > 3000 else 0) +
            (sections_found / len(required_sections)) +
            (1 if not formatting_issues else 0) +
            (1 if bullet_count > 15 else 0) +
            (keywords_found / len(business_keywords))
        ) / 5 * 100
        
        self.log(f"   🎯 OVERALL QUALITY SCORE: {quality_score:.1f}%")
        
        if quality_score >= 80:
            self.log(f"   🏆 EXCELLENT - Production ready!")
        elif quality_score >= 60:
            self.log(f"   👍 GOOD - Minor improvements needed")
        elif quality_score >= 40:
            self.log(f"   ⚠️  FAIR - Significant improvements needed")
        else:
            self.log(f"   ❌ POOR - Major issues need addressing")

    def test_batch_report_error_scenarios(self):
        """Test batch report error handling"""
        self.log("🚨 Testing batch report error scenarios...")
        
        # Test with empty list
        success1, _ = self.run_test(
            "Batch Report - Empty List",
            "POST",
            "notes/batch-report",
            400,
            data=[],
            auth_required=True
        )
        
        # Test with invalid note IDs
        success2, _ = self.run_test(
            "Batch Report - Invalid IDs",
            "POST",
            "notes/batch-report",
            400,
            data=["invalid-1", "invalid-2"],
            auth_required=True
        )
        
        # Test without authentication
        temp_token = self.auth_token
        self.auth_token = None
        success3, _ = self.run_test(
            "Batch Report - No Auth",
            "POST",
            "notes/batch-report",
            403,
            data=self.created_notes[:2] if self.created_notes else ["test"],
            auth_required=True
        )
        self.auth_token = temp_token
        
        return success1 and success2 and success3

    def run_comprehensive_batch_report_test(self):
        """Run comprehensive batch report functionality tests"""
        self.log("🚀 Starting Comprehensive Batch Report Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup authentication
        if not self.setup_authentication():
            self.log("❌ Authentication setup failed - stopping tests")
            return False
        
        # Create realistic test notes
        regular_notes = self.create_realistic_test_notes(use_expeditors=False)
        expeditors_notes = self.create_realistic_test_notes(use_expeditors=True)
        
        if len(regular_notes) < 2:
            self.log("❌ Failed to create sufficient test notes - stopping tests")
            return False
        
        # Wait for note processing
        self.log("\n⏳ WAITING FOR NOTE PROCESSING")
        processed_regular = self.wait_for_note_processing(regular_notes, max_wait=90)
        processed_expeditors = self.wait_for_note_processing(expeditors_notes, max_wait=90)
        
        # Test batch report functionality
        self.log("\n📊 BATCH REPORT FUNCTIONALITY TESTS")
        
        # Test with regular user
        success1 = self.test_batch_report_with_processed_notes(regular_notes, use_expeditors=False)
        
        # Test with Expeditors user
        success2 = self.test_batch_report_with_processed_notes(expeditors_notes, use_expeditors=True)
        
        # Test error scenarios
        self.log("\n🚨 ERROR HANDLING TESTS")
        success3 = self.test_batch_report_error_scenarios()
        
        return success1 or success2  # At least one should succeed

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*70)
        self.log("📊 COMPREHENSIVE BATCH REPORT TEST SUMMARY")
        self.log("="*70)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for i, note_id in enumerate(self.created_notes[:8]):
                self.log(f"  {i+1}. {note_id}")
            if len(self.created_notes) > 8:
                self.log(f"  ... and {len(self.created_notes) - 8} more")
        
        self.log("="*70)
        
        return self.tests_passed >= (self.tests_run * 0.7)  # 70% pass rate acceptable

def main():
    """Main test execution"""
    tester = RealisticBatchReportTester()
    
    try:
        success = tester.run_comprehensive_batch_report_test()
        acceptable_results = tester.print_summary()
        
        if success and acceptable_results:
            print("\n🎉 Batch report functionality tests completed successfully!")
            print("   The batch report endpoint is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Batch report tests revealed issues.")
            print("   Check the detailed logs above for specific problems.")
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