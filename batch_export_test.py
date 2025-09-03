#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class BatchExportTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"batch_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "BatchTest123"
        self.auth_token = None
        self.test_note_ids = []

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
        """Create a test user for batch export testing"""
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
                    await self.log_test("User Registration", True, f"User created with email: {self.test_user_email}")
                    return True
                else:
                    await self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False

    async def create_test_notes(self):
        """Create multiple test notes for batch export testing"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create 3 test notes with different content
            test_notes = [
                {
                    "title": "Q4 Sales Performance Review 2024",
                    "kind": "text",
                    "text_content": "Executive Summary: Q4 2024 sales performance exceeded targets by 15%. Key achievements include new client acquisitions in the logistics sector, improved customer retention rates, and successful implementation of digital transformation initiatives. Revenue growth was driven by strategic partnerships and enhanced service delivery capabilities. Challenges identified include supply chain disruptions and increased competition in key markets. Recommendations for Q1 2025 include expanding digital services, strengthening customer relationships, and investing in technology infrastructure."
                },
                {
                    "title": "Digital Transformation Project Status",
                    "kind": "text", 
                    "text_content": "Project Overview: The digital transformation initiative is progressing according to schedule with 75% completion rate. Major milestones achieved include cloud migration, API integration, and user training programs. Current focus areas include data analytics implementation, mobile application development, and cybersecurity enhancements. Budget utilization is at 68% with remaining funds allocated for final phase activities. Risk mitigation strategies are in place for potential delays and technical challenges. Expected completion date remains on track for March 2025."
                },
                {
                    "title": "Customer Satisfaction Survey Results",
                    "kind": "text",
                    "text_content": "Survey Results Analysis: Customer satisfaction scores improved to 4.2/5.0 from previous quarter's 3.8/5.0. Key improvement areas include response time, service quality, and communication effectiveness. Customer feedback highlights appreciation for proactive support and personalized service delivery. Areas for improvement include pricing transparency and technical documentation. Net Promoter Score increased to 68, indicating strong customer loyalty. Action items include implementing customer feedback system, enhancing support processes, and developing customer success programs."
                }
            ]
            
            async with httpx.AsyncClient(timeout=30) as client:
                for note_data in test_notes:
                    response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                    
                    if response.status_code == 200:
                        note_response = response.json()
                        note_id = note_response.get("id")
                        self.test_note_ids.append(note_id)
                        await self.log_test(f"Create Note: {note_data['title']}", True, f"Note ID: {note_id}")
                    else:
                        await self.log_test(f"Create Note: {note_data['title']}", False, f"Status: {response.status_code}")
                        return False
                
                await self.log_test("Test Notes Creation", True, f"Created {len(self.test_note_ids)} test notes")
                return True
                
        except Exception as e:
            await self.log_test("Test Notes Creation", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_pdf(self):
        """Test batch export functionality with PDF format"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": self.test_note_ids,
                "title": "Comprehensive Business Analysis Report 2024",
                "format": "pdf"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{BACKEND_URL}/notes/batch-report", json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    # Check if response is binary PDF data
                    content_type = response.headers.get("content-type", "")
                    content_length = len(response.content)
                    
                    if "application/pdf" in content_type and content_length > 1000:
                        await self.log_test("Batch Export PDF", True, f"PDF generated successfully. Size: {content_length} bytes, Content-Type: {content_type}")
                        
                        # Verify PDF content starts with PDF signature
                        if response.content.startswith(b'%PDF'):
                            await self.log_test("PDF Format Validation", True, "Valid PDF signature detected")
                        else:
                            await self.log_test("PDF Format Validation", False, "Invalid PDF signature")
                        
                        return True
                    else:
                        await self.log_test("Batch Export PDF", False, f"Invalid PDF response. Content-Type: {content_type}, Size: {content_length}")
                        return False
                else:
                    error_text = response.text if response.status_code != 500 else "Internal Server Error"
                    await self.log_test("Batch Export PDF", False, f"Status: {response.status_code}, Error: {error_text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export PDF", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_docx(self):
        """Test batch export functionality with DOCX format"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": self.test_note_ids,
                "title": "Comprehensive Business Analysis Report 2024",
                "format": "docx"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{BACKEND_URL}/notes/batch-report", json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    # Check if response is binary DOCX data
                    content_type = response.headers.get("content-type", "")
                    content_length = len(response.content)
                    
                    expected_content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    if expected_content_type in content_type and content_length > 5000:
                        await self.log_test("Batch Export DOCX", True, f"DOCX generated successfully. Size: {content_length} bytes, Content-Type: {content_type}")
                        
                        # Verify DOCX content starts with ZIP signature (DOCX is a ZIP file)
                        if response.content.startswith(b'PK'):
                            await self.log_test("DOCX Format Validation", True, "Valid DOCX/ZIP signature detected")
                        else:
                            await self.log_test("DOCX Format Validation", False, "Invalid DOCX/ZIP signature")
                        
                        return True
                    else:
                        await self.log_test("Batch Export DOCX", False, f"Invalid DOCX response. Content-Type: {content_type}, Size: {content_length}")
                        return False
                else:
                    error_text = response.text if response.status_code != 500 else "Internal Server Error"
                    await self.log_test("Batch Export DOCX", False, f"Status: {response.status_code}, Error: {error_text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export DOCX", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_txt(self):
        """Test batch export functionality with TXT format for comparison"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": self.test_note_ids,
                "title": "Comprehensive Business Analysis Report 2024",
                "format": "txt"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{BACKEND_URL}/notes/batch-report", json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    format_type = data.get("format", "")
                    note_count = data.get("note_count", 0)
                    
                    if format_type == "txt" and len(content) > 500 and note_count == len(self.test_note_ids):
                        await self.log_test("Batch Export TXT", True, f"TXT generated successfully. Content length: {len(content)} chars, Notes: {note_count}")
                        return True
                    else:
                        await self.log_test("Batch Export TXT", False, f"Invalid TXT response. Format: {format_type}, Content length: {len(content)}, Notes: {note_count}")
                        return False
                else:
                    await self.log_test("Batch Export TXT", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export TXT", False, f"Exception: {str(e)}")
            return False

    async def test_batch_export_rtf(self):
        """Test batch export functionality with RTF format for comparison"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": self.test_note_ids,
                "title": "Comprehensive Business Analysis Report 2024",
                "format": "rtf"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{BACKEND_URL}/notes/batch-report", json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    format_type = data.get("format", "")
                    note_count = data.get("note_count", 0)
                    
                    if format_type == "rtf" and content.startswith("{\\rtf1") and note_count == len(self.test_note_ids):
                        await self.log_test("Batch Export RTF", True, f"RTF generated successfully. Content length: {len(content)} chars, Notes: {note_count}")
                        return True
                    else:
                        await self.log_test("Batch Export RTF", False, f"Invalid RTF response. Format: {format_type}, Content starts: {content[:20]}, Notes: {note_count}")
                        return False
                else:
                    await self.log_test("Batch Export RTF", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Batch Export RTF", False, f"Exception: {str(e)}")
            return False

    async def test_error_scenarios(self):
        """Test error scenarios to ensure proper error handling"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with empty note_ids
            empty_request = {
                "note_ids": [],
                "title": "Empty Test",
                "format": "pdf"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{BACKEND_URL}/notes/batch-report", json=empty_request, headers=headers)
                
                if response.status_code == 400:
                    await self.log_test("Error Handling - Empty Notes", True, "Correctly returned 400 for empty note_ids")
                else:
                    await self.log_test("Error Handling - Empty Notes", False, f"Expected 400, got {response.status_code}")
                
                # Test with invalid format
                invalid_format_request = {
                    "note_ids": self.test_note_ids,
                    "title": "Invalid Format Test",
                    "format": "invalid_format"
                }
                
                response = await client.post(f"{BACKEND_URL}/notes/batch-report", json=invalid_format_request, headers=headers)
                
                # Should either work (default to professional) or return error
                if response.status_code in [200, 400, 422]:
                    await self.log_test("Error Handling - Invalid Format", True, f"Handled invalid format appropriately: {response.status_code}")
                else:
                    await self.log_test("Error Handling - Invalid Format", False, f"Unexpected status: {response.status_code}")
                
                return True
                    
        except Exception as e:
            await self.log_test("Error Scenarios", False, f"Exception: {str(e)}")
            return False

    async def cleanup_test_data(self):
        """Clean up test notes"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=30) as client:
                for note_id in self.test_note_ids:
                    response = await client.delete(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                    if response.status_code == 200:
                        await self.log_test(f"Cleanup Note {note_id}", True, "Note deleted successfully")
                    else:
                        await self.log_test(f"Cleanup Note {note_id}", False, f"Status: {response.status_code}")
                        
        except Exception as e:
            await self.log_test("Cleanup", False, f"Exception: {str(e)}")

    async def run_comprehensive_test(self):
        """Run all batch export tests"""
        print("🚀 Starting Comprehensive Batch Export Testing...")
        print("=" * 60)
        
        # Step 1: Create test user
        if not await self.create_test_user():
            print("❌ Failed to create test user. Aborting tests.")
            return
        
        # Step 2: Create test notes
        if not await self.create_test_notes():
            print("❌ Failed to create test notes. Aborting tests.")
            return
        
        # Step 3: Test all export formats
        await self.test_batch_export_txt()  # Test TXT first as baseline
        await self.test_batch_export_rtf()  # Test RTF as baseline
        await self.test_batch_export_pdf()  # Test PDF (critical fix)
        await self.test_batch_export_docx() # Test DOCX (critical fix)
        
        # Step 4: Test error scenarios
        await self.test_error_scenarios()
        
        # Step 5: Cleanup
        await self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 BATCH EXPORT TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Critical findings
        print("\n🎯 CRITICAL FINDINGS:")
        
        # Check if PDF and DOCX exports are working
        pdf_working = any(r["test"] == "Batch Export PDF" and r["success"] for r in self.test_results)
        docx_working = any(r["test"] == "Batch Export DOCX" and r["success"] for r in self.test_results)
        
        if pdf_working and docx_working:
            print("✅ CRITICAL FIX VERIFIED: Both PDF and DOCX batch exports are working correctly")
            print("✅ NO MORE 500 INTERNAL SERVER ERRORS: Import os statements fix successful")
        elif pdf_working:
            print("✅ PDF batch export working correctly")
            print("❌ DOCX batch export still has issues")
        elif docx_working:
            print("❌ PDF batch export still has issues") 
            print("✅ DOCX batch export working correctly")
        else:
            print("❌ CRITICAL: Both PDF and DOCX batch exports are still failing")
            print("❌ Import os statements may not be properly implemented")
        
        return passed_tests, failed_tests

async def main():
    """Main test execution"""
    tester = BatchExportTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())