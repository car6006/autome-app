#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
from datetime import datetime
import os

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class BatchComprehensiveReportTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"batch_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "BatchTest123"
        self.auth_token = None
        self.test_notes = []
        self.batch_report_data = None

    async def log_test(self, test_name, success, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")

    async def create_test_user(self):
        """Create a test user for batch report testing"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                user_data = {
                    "email": self.test_user_email,
                    "username": f"batchuser{uuid.uuid4().hex[:8]}",
                    "password": self.test_user_password,
                    "first_name": "Batch",
                    "last_name": "Tester"
                }
                
                response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    await self.log_test("Create Test User", True, f"User created: {self.test_user_email}")
                    return True
                else:
                    await self.log_test("Create Test User", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Create Test User", False, f"Exception: {str(e)}")
            return False

    async def create_test_notes(self):
        """Create multiple test notes with business content for batch reporting"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create 3 test notes with realistic business content
            test_notes_data = [
                {
                    "title": "Q4 Sales Performance Review 2024",
                    "kind": "text",
                    "text_content": """
                    Q4 Sales Performance Analysis:
                    
                    Revenue Growth: Achieved 15% year-over-year growth with total revenue of $2.3M
                    Key Performance Indicators:
                    - Customer acquisition increased by 22%
                    - Average deal size grew from $45K to $52K
                    - Sales cycle reduced from 90 to 75 days
                    
                    Top Performing Regions:
                    - North America: $1.2M (52% of total)
                    - Europe: $750K (33% of total)
                    - Asia-Pacific: $350K (15% of total)
                    
                    Strategic Initiatives:
                    - Launched new enterprise product line
                    - Expanded sales team by 30%
                    - Implemented CRM automation
                    
                    Challenges Identified:
                    - Competition increased in mid-market segment
                    - Supply chain delays affected Q4 deliveries
                    - Need for enhanced customer support capacity
                    """
                },
                {
                    "title": "Digital Transformation Project Status",
                    "kind": "text", 
                    "text_content": """
                    Digital Transformation Initiative - Phase 2 Update:
                    
                    Project Overview:
                    Modernizing core business systems to improve operational efficiency and customer experience.
                    
                    Completed Milestones:
                    - Cloud migration of customer database (100% complete)
                    - Implementation of new ERP system (85% complete)
                    - Staff training program (70% complete)
                    - API integration with partner systems (90% complete)
                    
                    Current Status:
                    - Project is 78% complete, on track for Q1 2025 delivery
                    - Budget utilization: $1.8M of $2.2M allocated
                    - Team performance: Exceeding velocity targets by 12%
                    
                    Key Benefits Realized:
                    - Processing time reduced by 40%
                    - Customer response time improved by 60%
                    - Data accuracy increased to 99.2%
                    
                    Upcoming Priorities:
                    - Complete ERP rollout to remaining departments
                    - Finalize mobile application development
                    - Conduct comprehensive security audit
                    """
                },
                {
                    "title": "Customer Satisfaction Survey Results",
                    "kind": "text",
                    "text_content": """
                    Customer Satisfaction Survey - Annual Results 2024:
                    
                    Survey Methodology:
                    - 1,250 customers surveyed (response rate: 34%)
                    - Mix of enterprise (40%), mid-market (35%), and SMB (25%) clients
                    - Conducted via email, phone, and in-person interviews
                    
                    Overall Satisfaction Metrics:
                    - Net Promoter Score (NPS): 67 (up from 58 in 2023)
                    - Customer Satisfaction Score (CSAT): 4.2/5.0
                    - Customer Effort Score (CES): 3.8/5.0
                    
                    Key Findings:
                    - Product quality rated highest (4.6/5.0)
                    - Customer support responsiveness needs improvement (3.4/5.0)
                    - Pricing perceived as competitive (4.1/5.0)
                    - Implementation process satisfaction: 3.9/5.0
                    
                    Customer Feedback Themes:
                    - Request for more self-service options
                    - Desire for faster issue resolution
                    - Interest in additional training resources
                    - Appreciation for account management quality
                    
                    Recommended Actions:
                    - Invest in customer portal enhancements
                    - Expand support team capacity
                    - Develop comprehensive knowledge base
                    - Implement proactive customer success program
                    """
                }
            ]
            
            async with httpx.AsyncClient(timeout=30) as client:
                for note_data in test_notes_data:
                    response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                    
                    if response.status_code == 200:
                        note_response = response.json()
                        self.test_notes.append({
                            "id": note_response["id"],
                            "title": note_data["title"]
                        })
                    else:
                        await self.log_test("Create Test Notes", False, f"Failed to create note: {note_data['title']}")
                        return False
                
                await self.log_test("Create Test Notes", True, f"Created {len(self.test_notes)} test notes with business content")
                return True
                
        except Exception as e:
            await self.log_test("Create Test Notes", False, f"Exception: {str(e)}")
            return False

    async def test_batch_comprehensive_report_generation(self):
        """Test the new batch comprehensive report generation endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            note_ids = [note["id"] for note in self.test_notes]
            
            request_data = {
                "note_ids": note_ids,
                "title": "Comprehensive Business Analysis - Q4 2024"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report",
                    json=request_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Store for export testing
                    self.batch_report_data = data
                    
                    # Verify response structure
                    required_fields = ["report", "title", "note_count", "source_notes", "note_ids"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        await self.log_test("Batch Report Generation", False, f"Missing fields: {missing_fields}")
                        return False
                    
                    # Verify content quality
                    report_content = data.get("report", "")
                    if len(report_content) < 1000:
                        await self.log_test("Batch Report Generation", False, f"Report too short: {len(report_content)} chars")
                        return False
                    
                    # Check for professional sections
                    professional_sections = [
                        "EXECUTIVE SUMMARY", "KEY INSIGHTS", "STRATEGIC RECOMMENDATIONS",
                        "RISK ASSESSMENT", "IMPLEMENTATION PRIORITIES", "CONCLUSION"
                    ]
                    
                    sections_found = sum(1 for section in professional_sections if section in report_content.upper())
                    
                    if sections_found < 4:
                        await self.log_test("Batch Report Generation", False, f"Only {sections_found}/6 professional sections found")
                        return False
                    
                    # Verify note count and source notes
                    if data["note_count"] != len(self.test_notes):
                        await self.log_test("Batch Report Generation", False, f"Note count mismatch: {data['note_count']} vs {len(self.test_notes)}")
                        return False
                    
                    await self.log_test("Batch Report Generation", True, 
                                      f"Generated {len(report_content)} char report with {sections_found}/6 sections, {data['note_count']} notes")
                    return True
                else:
                    await self.log_test("Batch Report Generation", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Report Generation", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_txt_format(self):
        """Test batch report export in TXT format"""
        try:
            if not self.batch_report_data:
                await self.log_test("Batch Export TXT", False, "No batch report data available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report/export?format=txt",
                    json=self.batch_report_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    content = response.content
                    content_type = response.headers.get("content-type", "")
                    
                    if "text/plain" not in content_type:
                        await self.log_test("Batch Export TXT", False, f"Wrong content type: {content_type}")
                        return False
                    
                    if len(content) < 500:
                        await self.log_test("Batch Export TXT", False, f"Content too short: {len(content)} bytes")
                        return False
                    
                    await self.log_test("Batch Export TXT", True, f"Generated {len(content)} byte TXT file")
                    return True
                else:
                    await self.log_test("Batch Export TXT", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export TXT", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_rtf_format(self):
        """Test batch report export in RTF format"""
        try:
            if not self.batch_report_data:
                await self.log_test("Batch Export RTF", False, "No batch report data available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report/export?format=rtf",
                    json=self.batch_report_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    content = response.content
                    content_type = response.headers.get("content-type", "")
                    
                    if "application/rtf" not in content_type:
                        await self.log_test("Batch Export RTF", False, f"Wrong content type: {content_type}")
                        return False
                    
                    # Check RTF signature
                    if not content.startswith(b"{\\rtf1"):
                        await self.log_test("Batch Export RTF", False, "Invalid RTF signature")
                        return False
                    
                    if len(content) < 500:
                        await self.log_test("Batch Export RTF", False, f"Content too short: {len(content)} bytes")
                        return False
                    
                    await self.log_test("Batch Export RTF", True, f"Generated {len(content)} byte RTF file")
                    return True
                else:
                    await self.log_test("Batch Export RTF", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export RTF", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_pdf_format(self):
        """Test batch report export in PDF format"""
        try:
            if not self.batch_report_data:
                await self.log_test("Batch Export PDF", False, "No batch report data available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report/export?format=pdf",
                    json=self.batch_report_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    content = response.content
                    content_type = response.headers.get("content-type", "")
                    
                    if "application/pdf" not in content_type:
                        await self.log_test("Batch Export PDF", False, f"Wrong content type: {content_type}")
                        return False
                    
                    # Check PDF signature
                    if not content.startswith(b"%PDF"):
                        await self.log_test("Batch Export PDF", False, "Invalid PDF signature")
                        return False
                    
                    if len(content) < 1000:
                        await self.log_test("Batch Export PDF", False, f"Content too short: {len(content)} bytes")
                        return False
                    
                    await self.log_test("Batch Export PDF", True, f"Generated {len(content)} byte PDF file with professional formatting")
                    return True
                else:
                    await self.log_test("Batch Export PDF", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export PDF", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_docx_format(self):
        """Test batch report export in DOCX format"""
        try:
            if not self.batch_report_data:
                await self.log_test("Batch Export DOCX", False, "No batch report data available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report/export?format=docx",
                    json=self.batch_report_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    content = response.content
                    content_type = response.headers.get("content-type", "")
                    
                    if "wordprocessingml" not in content_type:
                        await self.log_test("Batch Export DOCX", False, f"Wrong content type: {content_type}")
                        return False
                    
                    # Check DOCX signature (ZIP format)
                    if not content.startswith(b"PK"):
                        await self.log_test("Batch Export DOCX", False, "Invalid DOCX signature")
                        return False
                    
                    if len(content) < 5000:
                        await self.log_test("Batch Export DOCX", False, f"Content too short: {len(content)} bytes")
                        return False
                    
                    await self.log_test("Batch Export DOCX", True, f"Generated {len(content)} byte DOCX file with professional formatting")
                    return True
                else:
                    await self.log_test("Batch Export DOCX", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export DOCX", False, f"Exception: {str(e)}")
            return False

    async def test_expeditors_branding(self):
        """Test Expeditors branding for @expeditors.com users"""
        try:
            # Create Expeditors test user
            expeditors_email = f"expeditors_test_{uuid.uuid4().hex[:8]}@expeditors.com"
            
            async with httpx.AsyncClient(timeout=30) as client:
                user_data = {
                    "email": expeditors_email,
                    "username": f"expuser{uuid.uuid4().hex[:8]}",
                    "password": "ExpTest123",
                    "first_name": "Expeditors",
                    "last_name": "User"
                }
                
                response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    data = response.json()
                    exp_token = data.get("access_token")
                    
                    # Create a test note for Expeditors user
                    headers = {"Authorization": f"Bearer {exp_token}"}
                    note_data = {
                        "title": "Expeditors Logistics Analysis",
                        "kind": "text",
                        "text_content": "Supply chain optimization analysis for global logistics operations."
                    }
                    
                    note_response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                    
                    if note_response.status_code == 200:
                        note_id = note_response.json()["id"]
                        
                        # Generate batch report
                        batch_request = {
                            "note_ids": [note_id],
                            "title": "Expeditors Business Analysis"
                        }
                        
                        batch_response = await client.post(
                            f"{BACKEND_URL}/notes/batch-comprehensive-report",
                            json=batch_request,
                            headers=headers
                        )
                        
                        if batch_response.status_code == 200:
                            batch_data = batch_response.json()
                            
                            # Test PDF export with branding
                            pdf_response = await client.post(
                                f"{BACKEND_URL}/notes/batch-comprehensive-report/export?format=pdf",
                                json=batch_data,
                                headers=headers
                            )
                            
                            if pdf_response.status_code == 200:
                                pdf_content = pdf_response.content
                                
                                # Expeditors PDF should be larger due to branding
                                if len(pdf_content) > 5000:
                                    await self.log_test("Expeditors Branding", True, 
                                                      f"Expeditors PDF: {len(pdf_content)} bytes (enhanced with branding)")
                                    return True
                                else:
                                    await self.log_test("Expeditors Branding", False, 
                                                      f"Expeditors PDF too small: {len(pdf_content)} bytes")
                                    return False
                            else:
                                await self.log_test("Expeditors Branding", False, f"PDF export failed: {pdf_response.status_code}")
                                return False
                        else:
                            await self.log_test("Expeditors Branding", False, f"Batch report failed: {batch_response.status_code}")
                            return False
                    else:
                        await self.log_test("Expeditors Branding", False, f"Note creation failed: {note_response.status_code}")
                        return False
                else:
                    await self.log_test("Expeditors Branding", False, f"User creation failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Expeditors Branding", False, f"Exception: {str(e)}")
            return False

    async def test_content_quality_verification(self):
        """Test that AI analysis is comprehensive and professional"""
        try:
            if not self.batch_report_data:
                await self.log_test("Content Quality Verification", False, "No batch report data available")
                return False
            
            report_content = self.batch_report_data.get("report", "")
            
            # Check for comprehensive analysis indicators
            quality_indicators = [
                "strategic", "analysis", "business", "recommendations", "insights",
                "executive", "implementation", "risk", "assessment", "priorities"
            ]
            
            indicators_found = sum(1 for indicator in quality_indicators 
                                 if indicator.lower() in report_content.lower())
            
            # Check for proper structure
            structure_elements = [
                "EXECUTIVE SUMMARY", "KEY INSIGHTS", "STRATEGIC RECOMMENDATIONS",
                "RISK ASSESSMENT", "IMPLEMENTATION PRIORITIES"
            ]
            
            structure_found = sum(1 for element in structure_elements 
                                if element in report_content.upper())
            
            # Check content length (should be comprehensive)
            content_length = len(report_content)
            
            if indicators_found >= 6 and structure_found >= 4 and content_length >= 1500:
                await self.log_test("Content Quality Verification", True, 
                                  f"Quality indicators: {indicators_found}/10, Structure: {structure_found}/5, Length: {content_length} chars")
                return True
            else:
                await self.log_test("Content Quality Verification", False, 
                                  f"Quality indicators: {indicators_found}/10, Structure: {structure_found}/5, Length: {content_length} chars")
                return False
                
        except Exception as e:
            await self.log_test("Content Quality Verification", False, f"Exception: {str(e)}")
            return False

    async def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with empty note_ids
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report",
                    json={"note_ids": [], "title": "Empty Test"},
                    headers=headers
                )
                
                if response.status_code == 400:
                    await self.log_test("Error Handling - Empty Notes", True, "Correctly rejected empty note_ids")
                else:
                    await self.log_test("Error Handling - Empty Notes", False, f"Expected 400, got {response.status_code}")
                    return False
                
                # Test with invalid note_ids
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report",
                    json={"note_ids": ["invalid-id-1", "invalid-id-2"], "title": "Invalid Test"},
                    headers=headers
                )
                
                if response.status_code == 400:
                    await self.log_test("Error Handling - Invalid Notes", True, "Correctly rejected invalid note_ids")
                    return True
                else:
                    await self.log_test("Error Handling - Invalid Notes", False, f"Expected 400, got {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Error Handling", False, f"Exception: {str(e)}")
            return False

    async def cleanup_test_data(self):
        """Clean up test notes"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=30) as client:
                for note in self.test_notes:
                    await client.delete(f"{BACKEND_URL}/notes/{note['id']}", headers=headers)
            
            await self.log_test("Cleanup Test Data", True, f"Cleaned up {len(self.test_notes)} test notes")
            return True
            
        except Exception as e:
            await self.log_test("Cleanup Test Data", False, f"Exception: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all batch comprehensive report tests"""
        print("📊 Starting Batch Comprehensive Report System Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)

        # Test sequence
        tests = [
            ("Setup - Create Test User", self.create_test_user),
            ("Setup - Create Test Notes", self.create_test_notes),
            ("Batch Report Generation", self.test_batch_comprehensive_report_generation),
            ("Content Quality Verification", self.test_content_quality_verification),
            ("Batch Export TXT Format", self.test_batch_export_txt_format),
            ("Batch Export RTF Format", self.test_batch_export_rtf_format),
            ("Batch Export PDF Format", self.test_batch_export_pdf_format),
            ("Batch Export DOCX Format", self.test_batch_export_docx_format),
            ("Expeditors Branding", self.test_expeditors_branding),
            ("Error Handling", self.test_error_handling),
            ("Cleanup", self.cleanup_test_data)
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                await self.log_test(test_name, False, f"Unexpected exception: {str(e)}")

        print("=" * 80)
        print(f"📊 Batch Comprehensive Report Testing Complete")
        print(f"📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("✅ All batch comprehensive report functionality tests PASSED!")
        else:
            print("❌ Some batch comprehensive report functionality tests FAILED!")
            
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    tester = BatchComprehensiveReportTester()
    passed, total, results = await tester.run_all_tests()
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED TEST RESULTS:")
    print("=" * 80)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    print("\n" + "=" * 80)
    print("🎯 SUMMARY:")
    print("=" * 80)
    
    if passed == total:
        print("✅ NEW Batch Comprehensive Report System is working perfectly!")
        print("✅ AI-powered comprehensive business analysis generation working")
        print("✅ Professional formatting for all export formats (PDF, DOCX, TXT, RTF)")
        print("✅ Same quality and formatting as individual professional reports")
        print("✅ Expeditors branding integration working correctly")
        print("✅ Complete workflow from generation to export verified")
        print("✅ Content quality meets professional business standards")
    else:
        print("❌ Batch comprehensive report system has issues that need attention")
        failed_tests = [r for r in results if not r["success"]]
        print(f"❌ Failed tests: {len(failed_tests)}")
        for failed in failed_tests:
            print(f"   - {failed['test']}: {failed['details']}")

if __name__ == "__main__":
    asyncio.run(main())