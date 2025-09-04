#!/usr/bin/env python3
"""
Batch Report Error Investigation
Testing the specific "Failed to generate batch report" error reported by users
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import traceback

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-ai.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BatchReportInvestigator:
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
    
    async def create_realistic_test_notes(self):
        """Create realistic test notes similar to what users would have"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Realistic test notes with different content types
            test_notes_data = [
                {
                    "title": "Weekly Team Standup - January 15",
                    "kind": "text",
                    "text_content": "Team discussed current sprint progress. Sarah mentioned the API integration is 80% complete. Mike reported some database performance issues that need attention. Action items: 1. Complete API testing by Friday 2. Investigate database optimization 3. Schedule code review session. Next standup scheduled for Monday."
                },
                {
                    "title": "Client Meeting - Project Alpha",
                    "kind": "text", 
                    "text_content": "Met with client to discuss Project Alpha requirements. They want additional features for user authentication and reporting dashboard. Timeline is tight - delivery expected by end of month. Key concerns: security compliance, scalability, user experience. Follow-up meeting scheduled for next week to finalize specifications."
                },
                {
                    "title": "Budget Planning Session",
                    "kind": "text",
                    "text_content": "Reviewed Q1 budget allocations. Marketing budget increased by 15%. Development team resources need expansion. Infrastructure costs rising due to increased usage. Action items: prepare detailed cost analysis, evaluate cloud provider options, present recommendations to leadership team."
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
                            "status": note_info["status"],
                            "content_length": len(note_data.get("text_content", ""))
                        })
                        await self.log_result(f"Create Note: {note_data['title']}", True, f"ID: {note_info['id']}, Status: {note_info['status']}")
                    else:
                        await self.log_result(f"Create Note: {note_data['title']}", False, f"Status: {response.status_code}")
                        
            return len(self.test_notes) >= 2  # Need at least 2 notes for batch testing
            
        except Exception as e:
            await self.log_result("Create Test Notes", False, f"Error: {str(e)}")
            return False
    
    async def test_comprehensive_batch_report_detailed(self):
        """Test comprehensive batch report endpoint with detailed error analysis"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with multiple valid note IDs
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Comprehensive Weekly Report",
                "format": "ai"
            }
            
            print(f"🔍 Testing comprehensive batch report with {len(batch_request['note_ids'])} notes...")
            print(f"   Note IDs: {batch_request['note_ids']}")
            
            async with httpx.AsyncClient(timeout=180) as client:  # Extended timeout for AI processing
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                print(f"   Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    note_count = data.get("note_count", 0)
                    
                    # Detailed analysis
                    has_content = len(content) > 100
                    has_meeting_summary = "MEETING SUMMARY" in content
                    has_action_items = "ACTION ITEMS" in content
                    
                    success = has_content and has_meeting_summary and has_action_items
                    details = f"Content length: {len(content)}, Note count: {note_count}, Has sections: {has_meeting_summary and has_action_items}"
                    
                    await self.log_result("Comprehensive Batch Report - Valid Notes", success, details)
                    return success
                else:
                    # Detailed error analysis
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', str(error_data))
                    except:
                        error_detail = response.text
                    
                    await self.log_result("Comprehensive Batch Report - Valid Notes", False, 
                                        f"Status: {response.status_code}, Error: {error_detail}")
                    return False
                    
        except Exception as e:
            await self.log_result("Comprehensive Batch Report - Valid Notes", False, f"Exception: {str(e)}")
            print(f"   Full traceback: {traceback.format_exc()}")
            return False
    
    async def test_regular_batch_report_detailed(self):
        """Test regular batch report endpoint with detailed error analysis"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with same note IDs as comprehensive test
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Regular Weekly Report",
                "format": "professional"
            }
            
            print(f"🔍 Testing regular batch report with {len(batch_request['note_ids'])} notes...")
            
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(f"{API_BASE}/notes/batch-report", 
                                           json=batch_request, headers=headers)
                
                print(f"   Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    note_count = data.get("note_count", 0)
                    
                    success = len(content) > 100 and note_count > 0
                    details = f"Content length: {len(content)}, Note count: {note_count}"
                    
                    await self.log_result("Regular Batch Report - Valid Notes", success, details)
                    return success
                else:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', str(error_data))
                    except:
                        error_detail = response.text
                    
                    await self.log_result("Regular Batch Report - Valid Notes", False, 
                                        f"Status: {response.status_code}, Error: {error_detail}")
                    return False
                    
        except Exception as e:
            await self.log_result("Regular Batch Report - Valid Notes", False, f"Exception: {str(e)}")
            return False
    
    async def test_openai_api_connectivity(self):
        """Test if OpenAI API is accessible and working"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                await self.log_result("OpenAI API Connectivity", False, "No API key found in environment")
                return False
            
            # Test direct OpenAI API call
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": "Test message"}],
                        "max_tokens": 10
                    },
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                success = response.status_code == 200
                details = f"Status: {response.status_code}"
                if not success:
                    try:
                        error_data = response.json()
                        details += f", Error: {error_data}"
                    except:
                        details += f", Response: {response.text}"
                
                await self.log_result("OpenAI API Connectivity", success, details)
                return success
                
        except Exception as e:
            await self.log_result("OpenAI API Connectivity", False, f"Exception: {str(e)}")
            return False
    
    async def test_authentication_scenarios(self):
        """Test different authentication scenarios"""
        try:
            # Test with valid authentication
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            batch_request = {
                "note_ids": [self.test_notes[0]["id"]],
                "title": "Auth Test Report",
                "format": "txt"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes/batch-report", 
                                           json=batch_request, headers=headers)
                
                auth_success = response.status_code == 200
                await self.log_result("Authentication - Valid Token", auth_success, 
                                    f"Status: {response.status_code}")
                
                # Test without authentication
                response = await client.post(f"{API_BASE}/notes/batch-report", 
                                           json=batch_request)  # No headers
                
                no_auth_success = response.status_code in [401, 403]  # Should be unauthorized
                await self.log_result("Authentication - No Token", no_auth_success, 
                                    f"Status: {response.status_code}")
                
                return auth_success and no_auth_success
                
        except Exception as e:
            await self.log_result("Authentication Tests", False, f"Exception: {str(e)}")
            return False
    
    async def test_note_content_verification(self):
        """Verify that notes have valid content for processing"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Check each note individually
            valid_notes = 0
            for note in self.test_notes:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{API_BASE}/notes/{note['id']}", headers=headers)
                    
                    if response.status_code == 200:
                        note_data = response.json()
                        artifacts = note_data.get("artifacts", {})
                        content = artifacts.get("transcript") or artifacts.get("text", "")
                        
                        if content and len(content.strip()) > 10:
                            valid_notes += 1
                            print(f"   ✅ Note '{note['title']}': {len(content)} characters")
                        else:
                            print(f"   ❌ Note '{note['title']}': No valid content")
                    else:
                        print(f"   ❌ Note '{note['title']}': Cannot access (Status: {response.status_code})")
            
            success = valid_notes == len(self.test_notes)
            details = f"Valid notes: {valid_notes}/{len(self.test_notes)}"
            await self.log_result("Note Content Verification", success, details)
            return success
            
        except Exception as e:
            await self.log_result("Note Content Verification", False, f"Exception: {str(e)}")
            return False
    
    async def test_error_scenarios_detailed(self):
        """Test various error scenarios that might cause batch report failures"""
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
                print(f"   Invalid IDs test: Status {response.status_code} ({'✅' if invalid_handled else '❌'})")
                
                # Test 2: Empty note IDs list
                empty_request = {
                    "note_ids": [],
                    "title": "Empty Test",
                    "format": "ai"
                }
                
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=empty_request, headers=headers)
                
                empty_handled = response.status_code == 400
                print(f"   Empty IDs test: Status {response.status_code} ({'✅' if empty_handled else '❌'})")
                
                # Test 3: Mixed valid/invalid IDs
                mixed_request = {
                    "note_ids": [self.test_notes[0]["id"], "invalid-id-456"],
                    "title": "Mixed Test",
                    "format": "ai"
                }
                
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=mixed_request, headers=headers)
                
                mixed_handled = response.status_code in [200, 400]  # Should either work with valid note or fail gracefully
                print(f"   Mixed IDs test: Status {response.status_code} ({'✅' if mixed_handled else '❌'})")
                
                success = invalid_handled and empty_handled and mixed_handled
                details = f"Invalid: {response.status_code if not invalid_handled else 'OK'}, Empty: {'OK' if empty_handled else 'FAIL'}, Mixed: {'OK' if mixed_handled else 'FAIL'}"
                await self.log_result("Error Scenarios Handling", success, details)
                return success
                
        except Exception as e:
            await self.log_result("Error Scenarios Handling", False, f"Exception: {str(e)}")
            return False
    
    async def test_different_content_types(self):
        """Test batch reports with different content types"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create notes with different content characteristics
            test_cases = [
                {
                    "title": "Short Note Test",
                    "kind": "text",
                    "text_content": "Brief meeting summary."
                },
                {
                    "title": "Long Note Test", 
                    "kind": "text",
                    "text_content": "This is a very long note with extensive content. " * 50  # Long content
                }
            ]
            
            created_notes = []
            async with httpx.AsyncClient(timeout=30) as client:
                for note_data in test_cases:
                    response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                    if response.status_code == 200:
                        note_info = response.json()
                        created_notes.append(note_info["id"])
            
            if len(created_notes) >= 2:
                # Test batch report with different content types
                batch_request = {
                    "note_ids": created_notes,
                    "title": "Content Types Test",
                    "format": "ai"
                }
                
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                success = response.status_code == 200
                details = f"Status: {response.status_code}, Notes: {len(created_notes)}"
                if success:
                    data = response.json()
                    details += f", Content length: {len(data.get('content', ''))}"
                
                await self.log_result("Different Content Types", success, details)
                return success
            else:
                await self.log_result("Different Content Types", False, "Failed to create test notes")
                return False
                
        except Exception as e:
            await self.log_result("Different Content Types", False, f"Exception: {str(e)}")
            return False
    
    async def run_investigation(self):
        """Run comprehensive batch report investigation"""
        print("🔍 BATCH REPORT ERROR INVESTIGATION")
        print("=" * 60)
        print("Investigating: 'Failed to generate batch report' error")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user. Aborting investigation.")
            return False
        
        if not await self.create_realistic_test_notes():
            print("❌ Failed to create test notes. Aborting investigation.")
            return False
        
        print(f"\n📝 Created {len(self.test_notes)} realistic test notes")
        print("=" * 60)
        
        # Run investigation tests
        test_methods = [
            self.test_openai_api_connectivity,
            self.test_note_content_verification,
            self.test_authentication_scenarios,
            self.test_comprehensive_batch_report_detailed,
            self.test_regular_batch_report_detailed,
            self.test_error_scenarios_detailed,
            self.test_different_content_types
        ]
        
        for test_method in test_methods:
            await test_method()
            print()  # Add spacing between tests
        
        # Summary
        print("=" * 60)
        print("📊 INVESTIGATION SUMMARY")
        print("=" * 60)
        
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
        
        print("\n🎯 INVESTIGATION CONCLUSIONS:")
        
        if success_rate >= 90:
            print("✅ EXCELLENT: Batch report functionality is working correctly!")
            print("   The 'Failed to generate batch report' error is likely due to:")
            print("   - Temporary network issues")
            print("   - User-specific authentication problems")
            print("   - Frontend-backend communication issues")
        elif success_rate >= 70:
            print("⚠️  PARTIAL: Some batch report functionality working")
            print("   Issues found that may cause the reported error:")
            failed_tests = [r['test'] for r in self.results if not r['success']]
            for test in failed_tests:
                print(f"   - {test}")
        else:
            print("❌ CRITICAL: Significant problems with batch report functionality")
            print("   The 'Failed to generate batch report' error is likely caused by:")
            failed_tests = [r['test'] for r in self.results if not r['success']]
            for test in failed_tests:
                print(f"   - {test}")
        
        return success_rate >= 70

async def main():
    """Main investigation execution"""
    investigator = BatchReportInvestigator()
    success = await investigator.run_investigation()
    
    if success:
        print("\n🎉 BATCH REPORT INVESTIGATION COMPLETED!")
        print("The system appears to be working correctly.")
        sys.exit(0)
    else:
        print("\n🚨 BATCH REPORT INVESTIGATION FOUND ISSUES!")
        print("Critical problems identified that explain the user error.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())