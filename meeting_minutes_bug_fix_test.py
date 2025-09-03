#!/usr/bin/env python3
"""
Meeting Minutes Generation Bug Fix Verification
Testing that meeting minutes can be generated from text notes
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

class MeetingMinutesBugFixTester:
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
                "email": f"minutesbugfix{timestamp}@test.com",
                "username": f"minutesbugfix{timestamp}",  # No underscores
                "password": "TestPass123!",
                "first_name": "Minutes",
                "last_name": "BugFix"
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
                    error_detail = ""
                    try:
                        error_data = response.json()
                        error_detail = str(error_data)
                    except:
                        error_detail = response.text
                    await self.log_result("User Registration", False, f"Status: {response.status_code}, Error: {error_detail}")
                    return False
                    
        except Exception as e:
            await self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    async def test_meeting_minutes_from_text_note(self):
        """Test meeting minutes generation from text note (the bug fix)"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create text note with meeting content
            meeting_content = """
            Weekly Team Meeting - Project Alpha Status Update
            
            Date: January 15, 2025
            Time: 2:00 PM - 3:00 PM
            Location: Conference Room B
            
            Attendees:
            - Alice Johnson (Project Manager)
            - Bob Smith (Lead Developer) 
            - Carol Davis (QA Engineer)
            - David Wilson (UI/UX Designer)
            
            Meeting Agenda and Discussion:
            
            1. Project Timeline Review
            Alice presented the current project status. We are currently on track with the development phase, with 75% of core features completed. The testing phase is scheduled to begin next week.
            
            2. Technical Challenges
            Bob reported that the integration with the third-party API is more complex than initially anticipated. The team needs an additional week to resolve authentication issues and implement proper error handling.
            
            3. Quality Assurance Updates
            Carol outlined the testing strategy for the upcoming phase. She has prepared 150 test cases covering all major user workflows. Automated testing setup is 80% complete.
            
            4. Design Feedback Integration
            David shared updates on the UI improvements based on user feedback from the prototype testing. The new navigation structure has been well-received, and the color scheme adjustments are ready for implementation.
            
            Key Decisions Made:
            - Extended development timeline by one week to address API integration challenges
            - Approved additional budget of $5,000 for third-party API documentation and support
            - Scheduled daily standup meetings for the next two weeks to monitor progress closely
            
            Action Items:
            1. Bob to complete API integration and error handling by January 22
            2. Carol to finalize automated testing setup by January 20
            3. David to deliver final UI assets by January 18
            4. Alice to update project timeline and communicate changes to stakeholders by January 16
            
            Next Meeting: January 22, 2025 at 2:00 PM
            
            Meeting adjourned at 3:15 PM.
            """
            
            note_data = {
                "title": "Weekly Team Meeting - Project Alpha",
                "kind": "text",
                "text_content": meeting_content
            }
            
            async with httpx.AsyncClient(timeout=90) as client:
                # Create text note
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Text Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                self.test_notes.append(note_id)
                
                await self.log_result("Text Note Creation", True, f"Note ID: {note_id}")
                
                # Generate meeting minutes from text note (this should work now with the bug fix)
                response = await client.post(f"{API_BASE}/notes/{note_id}/generate-meeting-minutes", 
                                           headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    meeting_minutes = data.get("meeting_minutes", "")
                    
                    # Verify meeting minutes content
                    has_substantial_content = len(meeting_minutes) > 1000  # Should be comprehensive
                    has_meeting_structure = any(keyword in meeting_minutes.upper() for keyword in 
                                              ["EXECUTIVE SUMMARY", "DISCUSSION", "ACTION ITEMS", "MEETING", "ATTENDEES"])
                    contains_key_info = any(info in meeting_minutes for info in 
                                          ["Alice", "Bob", "Project Alpha", "API integration"])
                    
                    success = has_substantial_content and has_meeting_structure and contains_key_info
                    details = f"Length: {len(meeting_minutes)} chars, Structure: {has_meeting_structure}, Key info: {contains_key_info}"
                    await self.log_result("Meeting Minutes from Text Note", success, details)
                    
                    if success:
                        print(f"   Generated meeting minutes preview: {meeting_minutes[:300]}...")
                    
                    return success
                else:
                    error_detail = ""
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", "")
                    except:
                        error_detail = response.text
                    
                    # This is the bug we're testing for - it should NOT return 400 "No content available"
                    if response.status_code == 400 and "No content available" in error_detail:
                        await self.log_result("Meeting Minutes from Text Note", False, 
                                            f"BUG DETECTED: {error_detail} - Meeting minutes endpoint not reading text content!")
                    else:
                        await self.log_result("Meeting Minutes from Text Note", False, 
                                            f"Status: {response.status_code}, Error: {error_detail}")
                    return False
                    
        except Exception as e:
            await self.log_result("Meeting Minutes from Text Note", False, f"Error: {str(e)}")
            return False
    
    async def test_professional_report_comparison(self):
        """Test that professional report works with same text note (for comparison)"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Use the same note from previous test if available
            if not self.test_notes:
                await self.log_result("Professional Report Comparison", False, "No test note available")
                return False
            
            note_id = self.test_notes[0]
            
            async with httpx.AsyncClient(timeout=90) as client:
                # Generate professional report from the same text note
                response = await client.post(f"{API_BASE}/notes/{note_id}/generate-report", 
                                           headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    report = data.get("report", "")
                    
                    # Verify report content
                    has_content = len(report) > 1000  # Should be comprehensive
                    has_business_structure = any(keyword in report.upper() for keyword in 
                                               ["EXECUTIVE SUMMARY", "KEY INSIGHTS", "RECOMMENDATIONS", "ANALYSIS"])
                    
                    success = has_content and has_business_structure
                    details = f"Length: {len(report)} chars, Has business structure: {has_business_structure}"
                    await self.log_result("Professional Report from Same Text Note", success, details)
                    
                    return success
                else:
                    await self.log_result("Professional Report from Same Text Note", False, 
                                        f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Professional Report from Same Text Note", False, f"Error: {str(e)}")
            return False
    
    async def test_empty_note_error_handling(self):
        """Test error handling for notes without content"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create empty text note
            note_data = {
                "title": "Empty Note Test",
                "kind": "text"
                # No text_content provided
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Create empty note
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Empty Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                self.test_notes.append(note_id)
                
                # Try to generate meeting minutes from empty note (should fail appropriately)
                response = await client.post(f"{API_BASE}/notes/{note_id}/generate-meeting-minutes", 
                                           headers=headers)
                
                # Should return 400 with appropriate error message
                if response.status_code == 400:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "")
                    
                    # Should get "No content available" error for truly empty notes
                    appropriate_error = "No content available" in error_detail
                    success = appropriate_error
                    details = f"Error message: {error_detail}"
                    await self.log_result("Empty Note Error Handling", success, details)
                    
                    return success
                else:
                    await self.log_result("Empty Note Error Handling", False, 
                                        f"Expected 400 error, got: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Empty Note Error Handling", False, f"Error: {str(e)}")
            return False
    
    async def cleanup_test_notes(self):
        """Clean up test notes"""
        if not self.test_notes or not self.auth_token:
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with httpx.AsyncClient(timeout=30) as client:
            for note_id in self.test_notes:
                try:
                    await client.delete(f"{API_BASE}/notes/{note_id}", headers=headers)
                except:
                    pass
    
    async def run_all_tests(self):
        """Run all meeting minutes bug fix tests"""
        print("🔍 MEETING MINUTES GENERATION BUG FIX VERIFICATION")
        print("=" * 60)
        print("Testing that meeting minutes can be generated from text notes")
        print("(Previously failed with 'No content available' error)")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Could not setup test user, aborting tests")
            return False
        
        # Run tests
        test_methods = [
            self.test_meeting_minutes_from_text_note,
            self.test_professional_report_comparison,
            self.test_empty_note_error_handling
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                await self.log_result(test_method.__name__, False, f"Test exception: {str(e)}")
        
        # Cleanup
        await self.cleanup_test_notes()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 MEETING MINUTES BUG FIX TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Determine if bug fix is working
        meeting_minutes_test = next((r for r in self.results if "Meeting Minutes from Text Note" in r['test']), None)
        if meeting_minutes_test:
            if meeting_minutes_test['success']:
                print(f"\n🎉 BUG FIX VERIFIED: Meeting minutes can now be generated from text notes!")
            else:
                print(f"\n🚨 BUG STILL EXISTS: Meeting minutes generation from text notes is still failing!")
        
        return success_rate >= 75

async def main():
    """Main test execution"""
    tester = MeetingMinutesBugFixTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 MEETING MINUTES BUG FIX VERIFICATION COMPLETED SUCCESSFULLY")
    else:
        print("\n⚠️  MEETING MINUTES BUG FIX VERIFICATION FAILED")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())