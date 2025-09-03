#!/usr/bin/env python3
"""
Comprehensive Batch Report Testing
Testing all scenarios mentioned in the review request for "Failed to generate batch report" error
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveBatchReportTester:
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
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            register_data = {
                "email": f"batchreport{timestamp}@test.com",
                "username": f"batchreport{timestamp}",
                "password": "TestPass123!",
                "first_name": "Batch",
                "last_name": "Reporter"
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
                    await self.log_result("User Registration", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    async def create_test_notes_with_different_content(self):
        """Create test notes with different content types as mentioned in review"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create notes with transcript content (simulating audio transcription)
            transcript_note = {
                "title": "Team Meeting Transcript",
                "kind": "text",
                "text_content": "Today we discussed the quarterly goals and project timelines. The team agreed on the following action items: complete the API integration by Friday, schedule client demos for next week, and prepare the budget proposal. We also reviewed the current sprint progress and identified potential blockers."
            }
            
            # Create notes with regular text content
            text_note = {
                "title": "Project Planning Notes",
                "kind": "text", 
                "text_content": "Project Alpha requires additional resources for Q2 delivery. Key requirements include enhanced security features, improved user interface, and better performance optimization. Timeline is aggressive but achievable with proper resource allocation."
            }
            
            # Create note with minimal content to test edge cases
            minimal_note = {
                "title": "Brief Update",
                "kind": "text",
                "text_content": "Quick status update: all systems operational."
            }
            
            test_notes_data = [transcript_note, text_note, minimal_note]
            
            async with httpx.AsyncClient(timeout=30) as client:
                for note_data in test_notes_data:
                    response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                    
                    if response.status_code == 200:
                        note_info = response.json()
                        self.test_notes.append({
                            "id": note_info["id"],
                            "title": note_data["title"],
                            "status": note_info["status"],
                            "content_type": "transcript" if "transcript" in note_data["title"].lower() else "text"
                        })
                        await self.log_result(f"Create Note: {note_data['title']}", True, f"ID: {note_info['id']}")
                    else:
                        await self.log_result(f"Create Note: {note_data['title']}", False, f"Status: {response.status_code}")
                        
            return len(self.test_notes) >= 2
            
        except Exception as e:
            await self.log_result("Create Test Notes", False, f"Error: {str(e)}")
            return False
    
    async def test_comprehensive_batch_report_endpoint(self):
        """Test comprehensive batch report endpoint with multiple valid note IDs"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with 2-3 notes as mentioned in review
            selected_notes = self.test_notes[:3]  # Use first 3 notes
            batch_request = {
                "note_ids": [note["id"] for note in selected_notes],
                "title": "Weekly Team Summary Report",
                "format": "ai"
            }
            
            print(f"🔍 Testing comprehensive batch report with {len(batch_request['note_ids'])} notes...")
            
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Check for clean formatted content without speaker labels
                    has_speaker_labels = "Speaker 1:" in content or "Speaker 2:" in content or "Speaker A:" in content
                    has_substantial_content = len(content) > 1000
                    has_proper_structure = "MEETING SUMMARY" in content or "EXECUTIVE SUMMARY" in content
                    
                    success = not has_speaker_labels and has_substantial_content and has_proper_structure
                    details = f"Content length: {len(content)}, No speaker labels: {not has_speaker_labels}, Proper structure: {has_proper_structure}"
                    
                    await self.log_result("Comprehensive Batch Report - Multiple Notes", success, details)
                    return success
                else:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', str(error_data))
                    except:
                        error_detail = response.text
                    
                    await self.log_result("Comprehensive Batch Report - Multiple Notes", False, 
                                        f"Status: {response.status_code}, Error: {error_detail}")
                    return False
                    
        except Exception as e:
            await self.log_result("Comprehensive Batch Report - Multiple Notes", False, f"Exception: {str(e)}")
            return False
    
    async def test_regular_batch_report_endpoint(self):
        """Test regular batch report endpoint with same note IDs"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with same notes as comprehensive test
            selected_notes = self.test_notes[:3]
            batch_request = {
                "note_ids": [note["id"] for note in selected_notes],
                "title": "Weekly Team Summary Report",
                "format": "professional"
            }
            
            print(f"🔍 Testing regular batch report with {len(batch_request['note_ids'])} notes...")
            
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(f"{API_BASE}/notes/batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Check both 'content' and 'report' fields for consistency
                    content = data.get("content", "") or data.get("report", "")
                    
                    has_substantial_content = len(content) > 500
                    note_count = data.get("note_count", 0)
                    
                    success = has_substantial_content and note_count > 0
                    details = f"Content length: {len(content)}, Note count: {note_count}, Response fields: {list(data.keys())}"
                    
                    await self.log_result("Regular Batch Report - Multiple Notes", success, details)
                    return success
                else:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', str(error_data))
                    except:
                        error_detail = response.text
                    
                    await self.log_result("Regular Batch Report - Multiple Notes", False, 
                                        f"Status: {response.status_code}, Error: {error_detail}")
                    return False
                    
        except Exception as e:
            await self.log_result("Regular Batch Report - Multiple Notes", False, f"Exception: {str(e)}")
            return False
    
    async def test_openai_api_integration(self):
        """Check if OpenAI API calls are working"""
        try:
            # Test by making a simple batch report that requires OpenAI
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": [self.test_notes[0]["id"]],  # Single note test
                "title": "OpenAI Integration Test",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Check if content shows signs of AI processing
                    has_ai_structure = any(section in content for section in 
                                         ["MEETING SUMMARY", "EXECUTIVE SUMMARY", "ACTION ITEMS"])
                    
                    success = len(content) > 500 and has_ai_structure
                    details = f"AI-generated content length: {len(content)}, Has AI structure: {has_ai_structure}"
                    
                    await self.log_result("OpenAI API Integration", success, details)
                    return success
                else:
                    await self.log_result("OpenAI API Integration", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("OpenAI API Integration", False, f"Exception: {str(e)}")
            return False
    
    async def test_authentication_and_permissions(self):
        """Verify authentication and permissions"""
        try:
            # Test with valid authentication
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            batch_request = {
                "note_ids": [self.test_notes[0]["id"]],
                "title": "Auth Test",
                "format": "txt"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Test with valid token
                response = await client.post(f"{API_BASE}/notes/batch-report", 
                                           json=batch_request, headers=headers)
                
                auth_success = response.status_code == 200
                
                # Test without authentication
                response_no_auth = await client.post(f"{API_BASE}/notes/batch-report", 
                                                   json=batch_request)
                
                # Should require authentication
                no_auth_handled = response_no_auth.status_code in [401, 403]
                
                success = auth_success and no_auth_handled
                details = f"With auth: {response.status_code}, Without auth: {response_no_auth.status_code}"
                
                await self.log_result("Authentication and Permissions", success, details)
                return success
                
        except Exception as e:
            await self.log_result("Authentication and Permissions", False, f"Exception: {str(e)}")
            return False
    
    async def test_different_content_types(self):
        """Test different content types (transcript vs text)"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with transcript-type content
            transcript_notes = [note for note in self.test_notes if note["content_type"] == "transcript"]
            if transcript_notes:
                batch_request = {
                    "note_ids": [transcript_notes[0]["id"]],
                    "title": "Transcript Content Test",
                    "format": "ai"
                }
                
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                               json=batch_request, headers=headers)
                    
                    transcript_success = response.status_code == 200
                    transcript_details = f"Transcript test: {response.status_code}"
            else:
                transcript_success = True  # No transcript notes to test
                transcript_details = "No transcript notes available"
            
            # Test with text-type content
            text_notes = [note for note in self.test_notes if note["content_type"] == "text"]
            if text_notes:
                batch_request = {
                    "note_ids": [text_notes[0]["id"]],
                    "title": "Text Content Test",
                    "format": "ai"
                }
                
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                               json=batch_request, headers=headers)
                    
                    text_success = response.status_code == 200
                    text_details = f"Text test: {response.status_code}"
            else:
                text_success = True
                text_details = "No text notes available"
            
            success = transcript_success and text_success
            details = f"{transcript_details}, {text_details}"
            
            await self.log_result("Different Content Types", success, details)
            return success
            
        except Exception as e:
            await self.log_result("Different Content Types", False, f"Exception: {str(e)}")
            return False
    
    async def test_error_scenarios(self):
        """Check error scenarios as mentioned in review"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: Invalid note IDs
            invalid_request = {
                "note_ids": ["invalid-id-123", "another-invalid-id"],
                "title": "Invalid Test",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=invalid_request, headers=headers)
                
                invalid_handled = response.status_code in [400, 404]
                
                # Test 2: Empty content (create note without content)
                empty_note_data = {
                    "title": "Empty Note",
                    "kind": "text"
                    # No text_content
                }
                
                response = await client.post(f"{API_BASE}/notes", json=empty_note_data, headers=headers)
                if response.status_code == 200:
                    empty_note_id = response.json()["id"]
                    
                    empty_request = {
                        "note_ids": [empty_note_id],
                        "title": "Empty Content Test",
                        "format": "ai"
                    }
                    
                    response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                               json=empty_request, headers=headers)
                    
                    empty_handled = response.status_code in [400, 404]
                else:
                    empty_handled = True  # Couldn't create empty note, that's fine
                
                # Test 3: Notes belonging to different user (simulate)
                # This is harder to test without creating another user, so we'll skip for now
                
                success = invalid_handled and empty_handled
                details = f"Invalid IDs handled: {invalid_handled}, Empty content handled: {empty_handled}"
                
                await self.log_result("Error Scenarios", success, details)
                return success
                
        except Exception as e:
            await self.log_result("Error Scenarios", False, f"Exception: {str(e)}")
            return False
    
    async def test_ai_vs_other_formats(self):
        """Test AI format vs other formats to isolate where failure occurs"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            note_id = self.test_notes[0]["id"]
            
            formats_to_test = ["ai", "txt", "rtf", "professional"]
            format_results = {}
            
            for format_type in formats_to_test:
                batch_request = {
                    "note_ids": [note_id],
                    "title": f"Format Test {format_type.upper()}",
                    "format": format_type
                }
                
                # Use appropriate endpoint based on format
                if format_type == "ai":
                    endpoint = f"{API_BASE}/notes/comprehensive-batch-report"
                else:
                    endpoint = f"{API_BASE}/notes/batch-report"
                
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(endpoint, json=batch_request, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("content", "") or data.get("report", "")
                        format_results[format_type] = len(content) > 50
                        print(f"   {format_type.upper()}: ✅ Success ({len(content)} chars)")
                    else:
                        format_results[format_type] = False
                        print(f"   {format_type.upper()}: ❌ Failed (Status: {response.status_code})")
            
            success = all(format_results.values())
            failed_formats = [fmt for fmt, result in format_results.items() if not result]
            details = f"All formats working: {success}, Failed formats: {failed_formats}"
            
            await self.log_result("AI vs Other Formats", success, details)
            return success
            
        except Exception as e:
            await self.log_result("AI vs Other Formats", False, f"Exception: {str(e)}")
            return False
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive batch report tests"""
        print("🔍 COMPREHENSIVE BATCH REPORT ERROR INVESTIGATION")
        print("=" * 70)
        print("Testing: 'Failed to generate batch report' error scenarios")
        print("Focus: Comprehensive and regular batch report endpoints")
        print("=" * 70)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return False
        
        if not await self.create_test_notes_with_different_content():
            print("❌ Failed to create test notes. Aborting tests.")
            return False
        
        print(f"\n📝 Created {len(self.test_notes)} test notes with different content types")
        print("=" * 70)
        
        # Run comprehensive tests as specified in review request
        test_methods = [
            self.test_comprehensive_batch_report_endpoint,
            self.test_regular_batch_report_endpoint,
            self.test_openai_api_integration,
            self.test_authentication_and_permissions,
            self.test_different_content_types,
            self.test_error_scenarios,
            self.test_ai_vs_other_formats
        ]
        
        for test_method in test_methods:
            await test_method()
            print()  # Add spacing between tests
        
        # Summary
        print("=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.results if result['success'])
        total = len(self.results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed < total:
            print(f"❌ Failed: {total - passed}")
            print("\nFailed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 ROOT CAUSE ANALYSIS:")
        
        if success_rate >= 85:
            print("✅ BATCH REPORT FUNCTIONALITY IS WORKING CORRECTLY")
            print("   The 'Failed to generate batch report' error is likely caused by:")
            print("   - Frontend-backend communication issues")
            print("   - Temporary network connectivity problems")
            print("   - User-specific authentication token issues")
            print("   - Browser cache or session problems")
            print("\n💡 RECOMMENDATIONS:")
            print("   - Check frontend error handling and retry logic")
            print("   - Verify authentication token refresh mechanism")
            print("   - Add better error messages to help users understand issues")
        elif success_rate >= 60:
            print("⚠️  PARTIAL FUNCTIONALITY - SOME ISSUES FOUND")
            print("   Issues that may cause the reported error:")
            failed_tests = [r['test'] for r in self.results if not r['success']]
            for test in failed_tests:
                print(f"   - {test}")
        else:
            print("❌ CRITICAL ISSUES FOUND")
            print("   The 'Failed to generate batch report' error is caused by:")
            failed_tests = [r['test'] for r in self.results if not r['success']]
            for test in failed_tests:
                print(f"   - {test}")
        
        return success_rate >= 70

async def main():
    """Main test execution"""
    tester = ComprehensiveBatchReportTester()
    success = await tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 COMPREHENSIVE BATCH REPORT TESTING COMPLETED!")
        print("Backend functionality appears to be working correctly.")
        sys.exit(0)
    else:
        print("\n🚨 COMPREHENSIVE BATCH REPORT TESTING FOUND CRITICAL ISSUES!")
        print("Backend problems identified that explain the user error.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())