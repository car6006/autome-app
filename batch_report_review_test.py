#!/usr/bin/env python3
"""
Batch Report Review Request Testing
Testing the improved batch report functionality to verify the fixes:

1. "Failed to load notes" error fix with new /api/batch-report/ai-chat endpoint
2. Missing source notes fix - all batch report formats should include "SOURCE NOTES" section
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import re
import time

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BatchReportReviewTester:
    def __init__(self):
        self.auth_token = None
        self.user_id = None
        self.test_notes = []
        self.results = []
        
    async def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    async def setup_test_user(self):
        """Create and authenticate a test user"""
        try:
            # Register test user
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            register_data = {
                "email": f"batchreview{timestamp}@test.com",
                "username": f"batchreview{timestamp}",
                "password": "TestPass123!",
                "first_name": "Batch",
                "last_name": "ReviewTester"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{API_BASE}/auth/register", json=register_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    await self.log_result("User Registration", True, f"User ID: {self.user_id}")
                    return True
                else:
                    error_text = ""
                    try:
                        error_data = response.json()
                        error_text = str(error_data)
                    except:
                        error_text = response.text
                    await self.log_result("User Registration", False, f"Status: {response.status_code}, Error: {error_text}")
                    return False
                    
        except Exception as e:
            await self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    async def create_test_notes(self):
        """Create multiple test notes with realistic content for batch testing"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test notes with realistic business content
            test_notes_data = [
                {
                    "title": "Q4 Strategic Planning Meeting",
                    "kind": "text",
                    "text_content": "Meeting focused on Q4 strategic initiatives. Key discussion points included budget allocation for new projects, resource planning for upcoming deliverables, and timeline adjustments for critical milestones. Action items: 1. Review budget proposals by Friday 2. Schedule stakeholder meetings 3. Prepare quarterly performance reports 4. Align team objectives with company goals. Next steps involve cross-departmental coordination and resource optimization."
                },
                {
                    "title": "Product Development Review",
                    "kind": "text", 
                    "text_content": "Comprehensive review of current product development status. Technical challenges discussed include integration complexities and performance optimization requirements. Progress update: 75% completion on core features, testing phase initiated, deployment timeline confirmed. Critical action items: Complete integration testing, resolve performance bottlenecks, prepare production deployment plan, conduct user acceptance testing. Timeline: Testing completion by next week, production deployment in two weeks."
                },
                {
                    "title": "Team Performance Analysis",
                    "kind": "text",
                    "text_content": "Quarterly team performance review covering productivity metrics, collaboration effectiveness, and process improvements. Key insights: Team communication has significantly improved, documentation processes need enhancement, workflow optimization opportunities identified. Recommendations: Implement new documentation standards, schedule regular training sessions, establish performance benchmarks, create knowledge sharing protocols. Follow-up actions include template creation and training schedule development."
                }
            ]
            
            async with httpx.AsyncClient(timeout=30) as client:
                for note_data in test_notes_data:
                    response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                    
                    if response.status_code == 200:
                        note_info = response.json()
                        self.test_notes.append({
                            "id": note_info["id"],
                            "title": note_data["title"],
                            "status": note_info["status"]
                        })
                        await self.log_result(f"Create Note: {note_data['title']}", True, f"ID: {note_info['id']}")
                    else:
                        await self.log_result(f"Create Note: {note_data['title']}", False, f"Status: {response.status_code}")
                        
            return len(self.test_notes) >= 2  # Need at least 2 notes for batch testing
            
        except Exception as e:
            await self.log_result("Create Test Notes", False, f"Error: {str(e)}")
            return False
    
    async def test_comprehensive_batch_report_with_source_notes(self):
        """Test comprehensive batch report includes SOURCE NOTES section"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Comprehensive Business Analysis Report",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Check for SOURCE NOTES section at the top
                    has_source_notes = "SOURCE NOTES:" in content
                    
                    # Check that source notes appear early in the document
                    source_notes_position = content.find("SOURCE NOTES:")
                    is_at_top = source_notes_position < 500 if source_notes_position != -1 else False
                    
                    # Check for note titles in source notes
                    note_titles_found = 0
                    for note in self.test_notes:
                        if note["title"] in content:
                            note_titles_found += 1
                    
                    # Check for bullet points in source notes
                    has_bullet_points = "•" in content or "-" in content
                    
                    success = (has_source_notes and is_at_top and 
                             note_titles_found >= 2 and has_bullet_points)
                    
                    details = f"Source notes section: {has_source_notes}, At top: {is_at_top}, Note titles found: {note_titles_found}/{len(self.test_notes)}, Has bullets: {has_bullet_points}"
                    await self.log_result("Comprehensive Batch Report with Source Notes", success, details)
                    
                    return success, content
                else:
                    await self.log_result("Comprehensive Batch Report with Source Notes", False, f"Status: {response.status_code}")
                    return False, ""
                    
        except Exception as e:
            await self.log_result("Comprehensive Batch Report with Source Notes", False, f"Error: {str(e)}")
            return False, ""
    
    async def test_regular_batch_report_formats_with_source_notes(self):
        """Test regular batch report formats (TXT, RTF, Professional AI) include source notes"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            formats_to_test = ["txt", "rtf", "professional"]
            all_success = True
            
            for format_type in formats_to_test:
                batch_request = {
                    "note_ids": [note["id"] for note in self.test_notes],
                    "title": f"Business Report - {format_type.upper()} Format",
                    "format": format_type
                }
                
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(f"{API_BASE}/notes/batch-report", 
                                               json=batch_request, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("report", "") or data.get("content", "")
                        
                        # Check for SOURCE NOTES section
                        has_source_notes = "SOURCE NOTES:" in content
                        
                        # Check for note titles
                        note_titles_found = sum(1 for note in self.test_notes if note["title"] in content)
                        
                        format_success = has_source_notes and note_titles_found >= 2
                        
                        details = f"Format: {format_type}, Source notes: {has_source_notes}, Titles found: {note_titles_found}/{len(self.test_notes)}"
                        await self.log_result(f"Regular Batch Report - {format_type.upper()} with Source Notes", format_success, details)
                        
                        if not format_success:
                            all_success = False
                    else:
                        await self.log_result(f"Regular Batch Report - {format_type.upper()} with Source Notes", False, f"Status: {response.status_code}")
                        all_success = False
            
            return all_success
                    
        except Exception as e:
            await self.log_result("Regular Batch Report Formats with Source Notes", False, f"Error: {str(e)}")
            return False
    
    async def test_new_batch_ai_chat_endpoint(self):
        """Test new /api/batch-report/ai-chat endpoint handles AI chat without virtual note errors"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # First generate a batch report to get content
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Test Batch Content for AI Chat",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                # Generate batch report
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("New Batch AI Chat Endpoint - Generate Content", False, f"Status: {response.status_code}")
                    return False
                
                batch_data = response.json()
                batch_content = batch_data.get("content", "")
                
                if not batch_content:
                    await self.log_result("New Batch AI Chat Endpoint - Generate Content", False, "No batch content generated")
                    return False
                
                # Test the new AI chat endpoint
                ai_chat_request = {
                    "content": batch_content,
                    "question": "What are the key action items and priorities from this batch report?"
                }
                
                response = await client.post(f"{API_BASE}/batch-report/ai-chat", 
                                           json=ai_chat_request, headers=headers)
                
                if response.status_code == 200:
                    ai_data = response.json()
                    ai_response = ai_data.get("response", "")
                    
                    # Check that we got a meaningful AI response
                    has_response = len(ai_response) > 100
                    no_error_message = "Failed to load notes" not in ai_response
                    no_note_not_found = "Note not found" not in ai_response
                    
                    success = has_response and no_error_message and no_note_not_found
                    
                    details = f"Response length: {len(ai_response)}, No error messages: {no_error_message and no_note_not_found}"
                    await self.log_result("New Batch AI Chat Endpoint", success, details)
                    
                    return success
                else:
                    await self.log_result("New Batch AI Chat Endpoint", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("New Batch AI Chat Endpoint", False, f"Error: {str(e)}")
            return False
    
    async def test_batch_ai_chat_error_handling(self):
        """Test error handling for batch AI chat endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            test_cases = [
                {
                    "name": "Missing Content",
                    "request": {"question": "What are the key points?"},
                    "expected_status": 400
                },
                {
                    "name": "Missing Question", 
                    "request": {"content": "Some batch content here"},
                    "expected_status": 400
                },
                {
                    "name": "Empty Content",
                    "request": {"content": "", "question": "What are the key points?"},
                    "expected_status": 400
                },
                {
                    "name": "Empty Question",
                    "request": {"content": "Some batch content", "question": ""},
                    "expected_status": 400
                }
            ]
            
            all_success = True
            
            async with httpx.AsyncClient(timeout=30) as client:
                for test_case in test_cases:
                    response = await client.post(f"{API_BASE}/batch-report/ai-chat", 
                                               json=test_case["request"], headers=headers)
                    
                    success = response.status_code == test_case["expected_status"]
                    
                    details = f"Expected: {test_case['expected_status']}, Got: {response.status_code}"
                    await self.log_result(f"Batch AI Chat Error Handling - {test_case['name']}", success, details)
                    
                    if not success:
                        all_success = False
            
            return all_success
                    
        except Exception as e:
            await self.log_result("Batch AI Chat Error Handling", False, f"Error: {str(e)}")
            return False
    
    async def test_authentication_requirements(self):
        """Test that batch AI chat requires proper authentication"""
        try:
            # Test without authentication
            ai_chat_request = {
                "content": "Some test content for authentication test",
                "question": "What are the main points?"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{API_BASE}/batch-report/ai-chat", json=ai_chat_request)
                
                # Should return 401 or 403 for unauthenticated request
                success = response.status_code in [401, 403]
                
                details = f"Status: {response.status_code} (expected 401 or 403)"
                await self.log_result("Batch AI Chat Authentication Required", success, details)
                
                return success
                    
        except Exception as e:
            await self.log_result("Batch AI Chat Authentication Required", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all batch report tests"""
        print("🚀 Starting Batch Report Review Request Testing")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return
        
        if not await self.create_test_notes():
            print("❌ Failed to create test notes. Aborting tests.")
            return
        
        print(f"\n📝 Created {len(self.test_notes)} test notes for batch testing")
        print("=" * 60)
        
        # Run tests
        await self.test_comprehensive_batch_report_with_source_notes()
        await self.test_regular_batch_report_formats_with_source_notes()
        await self.test_new_batch_ai_chat_endpoint()
        await self.test_batch_ai_chat_error_handling()
        await self.test_authentication_requirements()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 BATCH REPORT FUNCTIONALITY: WORKING CORRECTLY")
        else:
            print("⚠️  BATCH REPORT FUNCTIONALITY: NEEDS ATTENTION")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")

async def main():
    """Main test execution"""
    tester = BatchReportReviewTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())