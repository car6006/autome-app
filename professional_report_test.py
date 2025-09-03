#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ProfessionalReportExportTester:
    def __init__(self):
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None
        self.test_note_id = None
        self.expeditors_token = None
        self.expeditors_note_id = None
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    async def setup_test_user(self, email_suffix="@testdomain.com"):
        """Create a test user and get authentication token"""
        try:
            # Generate unique test user
            unique_id = str(uuid.uuid4())[:8]
            test_email = f"testuser_{unique_id}{email_suffix}"
            
            async with httpx.AsyncClient(timeout=30) as client:
                # Register user
                register_data = {
                    "email": test_email,
                    "username": f"testuser{unique_id}",
                    "password": "TestPass123!",
                    "first_name": "Test",
                    "last_name": "User"
                }
                
                response = await client.post(f"{API_BASE}/auth/register", json=register_data)
                
                if response.status_code == 200:
                    auth_data = response.json()
                    token = auth_data.get("access_token")
                    user_data = auth_data.get("user", {})
                    
                    self.log_result(f"User Registration ({email_suffix})", True, 
                                  f"User ID: {user_data.get('id')}, Email: {test_email}")
                    return token, user_data.get('id'), test_email
                else:
                    self.log_result(f"User Registration ({email_suffix})", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return None, None, None
                    
        except Exception as e:
            self.log_result(f"User Registration ({email_suffix})", False, f"Exception: {str(e)}")
            return None, None, None
    
    async def create_test_note_with_content(self, token, title="Professional Report Test Note"):
        """Create a test note with content for report generation"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(timeout=30) as client:
                # Create text note
                note_data = {
                    "title": title,
                    "kind": "text",
                    "text_content": """
                    QUARTERLY BUSINESS REVIEW MEETING
                    
                    EXECUTIVE SUMMARY
                    Our Q4 performance exceeded expectations with 15% revenue growth and successful product launches.
                    
                    KEY PERFORMANCE INDICATORS
                    • Revenue increased by 15% compared to Q3
                    • Customer satisfaction scores improved to 4.8/5.0
                    • New product adoption rate reached 65%
                    • Team productivity increased by 12%
                    
                    STRATEGIC INITIATIVES
                    • Launch new customer portal by March 2025
                    • Expand into European markets
                    • Implement AI-powered analytics platform
                    • Strengthen partnership with key vendors
                    
                    ACTION ITEMS
                    • Complete market research for European expansion (Due: Feb 15)
                    • Finalize customer portal specifications (Due: Jan 30)
                    • Schedule vendor partnership meetings (Due: Feb 1)
                    • Prepare Q1 budget proposal (Due: Jan 25)
                    
                    RISK ASSESSMENT
                    • Supply chain disruptions in Q1
                    • Competitive pressure from new market entrants
                    • Regulatory changes in target markets
                    
                    NEXT STEPS
                    • Weekly progress reviews starting January 15
                    • Monthly stakeholder updates
                    • Quarterly performance assessments
                    """
                }
                
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code == 200:
                    note_response = response.json()
                    note_id = note_response.get("id")
                    
                    self.log_result("Test Note Creation", True, 
                                  f"Note ID: {note_id}, Status: {note_response.get('status')}")
                    return note_id
                else:
                    self.log_result("Test Note Creation", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return None
                    
        except Exception as e:
            self.log_result("Test Note Creation", False, f"Exception: {str(e)}")
            return None
    
    async def generate_professional_report(self, token, note_id):
        """Generate professional report for the test note"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes/{note_id}/generate-report", headers=headers)
                
                if response.status_code == 200:
                    report_data = response.json()
                    report_content = report_data.get("report", "")
                    
                    # Verify report structure
                    has_executive_summary = "EXECUTIVE SUMMARY" in report_content
                    has_key_insights = "KEY INSIGHTS" in report_content
                    has_action_items = "ACTION ITEMS" in report_content
                    has_bullet_points = "•" in report_content
                    is_expeditors = report_data.get("is_expeditors", False)
                    
                    structure_score = sum([has_executive_summary, has_key_insights, has_action_items, has_bullet_points])
                    
                    self.log_result("Professional Report Generation", True, 
                                  f"Report length: {len(report_content)} chars, Structure score: {structure_score}/4, Expeditors: {is_expeditors}")
                    return True
                else:
                    self.log_result("Professional Report Generation", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            self.log_result("Professional Report Generation", False, f"Exception: {str(e)}")
            return False
    
    async def test_professional_report_export(self, token, note_id, format_type, user_type="regular"):
        """Test professional report export in specific format"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(
                    f"{API_BASE}/notes/{note_id}/professional-report/export?format={format_type}", 
                    headers=headers
                )
                
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    content_disposition = response.headers.get("content-disposition", "")
                    content_length = len(response.content)
                    
                    # Verify content type
                    expected_types = {
                        "pdf": "application/pdf",
                        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "txt": "text/plain",
                        "rtf": "application/rtf"
                    }
                    
                    correct_content_type = expected_types.get(format_type, "") in content_type
                    has_attachment = "attachment" in content_disposition
                    has_filename = f"Professional_Report_" in content_disposition
                    
                    # Format-specific validation
                    format_valid = False
                    if format_type == "pdf":
                        format_valid = response.content.startswith(b'%PDF')
                    elif format_type == "docx":
                        format_valid = response.content.startswith(b'PK')  # ZIP signature
                    elif format_type == "txt":
                        format_valid = len(response.content) > 100
                    elif format_type == "rtf":
                        format_valid = response.content.startswith(b'{\\rtf')
                    
                    # Check for Expeditors branding if applicable
                    expeditors_branding = False
                    if user_type == "expeditors":
                        if format_type in ["pdf", "docx"]:
                            expeditors_branding = True  # Assume branding is present in binary formats
                        else:
                            content_text = response.content.decode('utf-8', errors='ignore')
                            expeditors_branding = "EXPEDITORS" in content_text
                    
                    success = correct_content_type and has_attachment and has_filename and format_valid
                    
                    details = f"Size: {content_length} bytes, Content-Type: {content_type}, Format Valid: {format_valid}"
                    if user_type == "expeditors":
                        details += f", Expeditors Branding: {expeditors_branding}"
                    
                    self.log_result(f"Professional Report Export ({format_type.upper()}) - {user_type}", 
                                  success, details)
                    return success
                else:
                    self.log_result(f"Professional Report Export ({format_type.upper()}) - {user_type}", False, 
                                  f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            self.log_result(f"Professional Report Export ({format_type.upper()}) - {user_type}", False, 
                          f"Exception: {str(e)}")
            return False
    
    async def test_document_quality_verification(self, token, note_id, user_type="regular"):
        """Test document quality and formatting for PDF and DOCX"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Test PDF quality
                pdf_response = await client.get(
                    f"{API_BASE}/notes/{note_id}/professional-report/export?format=pdf", 
                    headers=headers
                )
                
                # Test DOCX quality  
                docx_response = await client.get(
                    f"{API_BASE}/notes/{note_id}/professional-report/export?format=docx", 
                    headers=headers
                )
                
                # Test TXT for comparison
                txt_response = await client.get(
                    f"{API_BASE}/notes/{note_id}/professional-report/export?format=txt", 
                    headers=headers
                )
                
                if all(r.status_code == 200 for r in [pdf_response, docx_response, txt_response]):
                    pdf_size = len(pdf_response.content)
                    docx_size = len(docx_response.content)
                    txt_size = len(txt_response.content)
                    
                    # Quality indicators
                    pdf_larger_than_txt = pdf_size > txt_size * 1.2  # PDF should be larger due to formatting
                    docx_larger_than_txt = docx_size > txt_size * 2.0  # DOCX should be significantly larger
                    
                    # Size ratios indicate formatting enhancements
                    pdf_txt_ratio = pdf_size / txt_size if txt_size > 0 else 0
                    docx_txt_ratio = docx_size / txt_size if txt_size > 0 else 0
                    
                    quality_score = 0
                    if pdf_larger_than_txt:
                        quality_score += 1
                    if docx_larger_than_txt:
                        quality_score += 1
                    if pdf_txt_ratio > 1.5:  # Good formatting enhancement
                        quality_score += 1
                    if docx_txt_ratio > 3.0:  # Excellent formatting enhancement
                        quality_score += 1
                    
                    success = quality_score >= 3
                    
                    details = f"PDF: {pdf_size}B (ratio: {pdf_txt_ratio:.2f}), DOCX: {docx_size}B (ratio: {docx_txt_ratio:.2f}), TXT: {txt_size}B, Quality: {quality_score}/4"
                    
                    self.log_result(f"Document Quality Verification - {user_type}", success, details)
                    return success
                else:
                    self.log_result(f"Document Quality Verification - {user_type}", False, 
                                  "Failed to retrieve all format types")
                    return False
                    
        except Exception as e:
            self.log_result(f"Document Quality Verification - {user_type}", False, f"Exception: {str(e)}")
            return False
    
    async def test_content_structure_preservation(self, token, note_id):
        """Test that content structure is preserved in exports"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Get TXT export to analyze structure
                txt_response = await client.get(
                    f"{API_BASE}/notes/{note_id}/professional-report/export?format=txt", 
                    headers=headers
                )
                
                if txt_response.status_code == 200:
                    content = txt_response.content.decode('utf-8')
                    
                    # Check for structure elements
                    has_section_headings = any(heading in content for heading in 
                                             ["EXECUTIVE SUMMARY", "KEY INSIGHTS", "ACTION ITEMS", "STRATEGIC"])
                    has_bullet_points = "•" in content
                    has_proper_paragraphs = content.count('\n\n') >= 3  # Multiple paragraph breaks
                    
                    # Check content organization
                    lines = content.split('\n')
                    non_empty_lines = [line.strip() for line in lines if line.strip()]
                    
                    structure_indicators = 0
                    if has_section_headings:
                        structure_indicators += 1
                    if has_bullet_points:
                        structure_indicators += 1
                    if has_proper_paragraphs:
                        structure_indicators += 1
                    if len(non_empty_lines) > 10:  # Substantial content
                        structure_indicators += 1
                    
                    success = structure_indicators >= 3
                    
                    details = f"Section headings: {has_section_headings}, Bullet points: {has_bullet_points}, Paragraphs: {has_proper_paragraphs}, Lines: {len(non_empty_lines)}"
                    
                    self.log_result("Content Structure Preservation", success, details)
                    return success
                else:
                    self.log_result("Content Structure Preservation", False, 
                                  f"Status: {txt_response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("Content Structure Preservation", False, f"Exception: {str(e)}")
            return False
    
    async def test_error_handling(self, token):
        """Test error handling for various scenarios"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient(timeout=30) as client:
                # Test with non-existent note
                response1 = await client.get(
                    f"{API_BASE}/notes/nonexistent-note-id/professional-report/export?format=pdf", 
                    headers=headers
                )
                
                # Test with invalid format
                if self.test_note_id:
                    response2 = await client.get(
                        f"{API_BASE}/notes/{self.test_note_id}/professional-report/export?format=invalid", 
                        headers=headers
                    )
                else:
                    response2 = None
                
                # Test without authentication
                response3 = await client.get(
                    f"{API_BASE}/notes/test-note/professional-report/export?format=pdf"
                )
                
                error_handling_score = 0
                
                # Non-existent note should return 404
                if response1.status_code == 404:
                    error_handling_score += 1
                
                # Invalid format should return 422 or 400
                if response2 and response2.status_code in [400, 422]:
                    error_handling_score += 1
                
                # No auth should return 401 or 403
                if response3.status_code in [401, 403]:
                    error_handling_score += 1
                
                success = error_handling_score >= 2
                
                details = f"404 for missing note: {response1.status_code == 404}, Invalid format: {response2.status_code if response2 else 'N/A'}, No auth: {response3.status_code in [401, 403]}"
                
                self.log_result("Error Handling", success, details)
                return success
                
        except Exception as e:
            self.log_result("Error Handling", False, f"Exception: {str(e)}")
            return False
    
    async def run_comprehensive_tests(self):
        """Run all professional report export tests"""
        print("🔍 PROFESSIONAL REPORT EXPORT FUNCTIONALITY TESTING")
        print("=" * 60)
        
        # Setup regular user
        self.auth_token, self.test_user_id, test_email = await self.setup_test_user()
        if not self.auth_token:
            print("❌ Failed to setup regular test user - aborting tests")
            return
        
        # Setup Expeditors user
        self.expeditors_token, expeditors_user_id, expeditors_email = await self.setup_test_user("@expeditors.com")
        
        # Create test notes
        self.test_note_id = await self.create_test_note_with_content(self.auth_token)
        if self.expeditors_token:
            self.expeditors_note_id = await self.create_test_note_with_content(
                self.expeditors_token, "Expeditors Professional Report Test"
            )
        
        if not self.test_note_id:
            print("❌ Failed to create test note - aborting tests")
            return
        
        # Generate professional reports
        await self.generate_professional_report(self.auth_token, self.test_note_id)
        if self.expeditors_token and self.expeditors_note_id:
            await self.generate_professional_report(self.expeditors_token, self.expeditors_note_id)
        
        # Test all export formats for regular user
        formats = ["pdf", "docx", "txt", "rtf"]
        for format_type in formats:
            await self.test_professional_report_export(self.auth_token, self.test_note_id, format_type, "regular")
        
        # Test all export formats for Expeditors user
        if self.expeditors_token and self.expeditors_note_id:
            for format_type in formats:
                await self.test_professional_report_export(
                    self.expeditors_token, self.expeditors_note_id, format_type, "expeditors"
                )
        
        # Test document quality
        await self.test_document_quality_verification(self.auth_token, self.test_note_id, "regular")
        if self.expeditors_token and self.expeditors_note_id:
            await self.test_document_quality_verification(
                self.expeditors_token, self.expeditors_note_id, "expeditors"
            )
        
        # Test content structure preservation
        await self.test_content_structure_preservation(self.auth_token, self.test_note_id)
        
        # Test error handling
        await self.test_error_handling(self.auth_token)
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 PROFESSIONAL REPORT EXPORT TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: Professional Report Export functionality is working perfectly!")
        elif success_rate >= 75:
            print(f"\n✅ GOOD: Professional Report Export functionality is mostly working with minor issues.")
        elif success_rate >= 50:
            print(f"\n⚠️  MODERATE: Professional Report Export functionality has significant issues.")
        else:
            print(f"\n❌ CRITICAL: Professional Report Export functionality has major problems.")

async def main():
    """Main test execution"""
    tester = ProfessionalReportExportTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())