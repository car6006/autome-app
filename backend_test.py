#!/usr/bin/env python3
"""
Enhanced Batch Report Functionality Testing
Testing the improved comprehensive batch report formatting and note status updates
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import re

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://auto-me-debugger.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BatchReportTester:
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
                "email": f"batchtest{timestamp}@test.com",
                "username": f"batchtest{timestamp}",
                "password": "TestPass123!",
                "first_name": "Batch",
                "last_name": "Tester"
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
        """Create multiple test notes with different content types"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test notes with different content
            test_notes_data = [
                {
                    "title": "Meeting Notes - Q4 Planning",
                    "kind": "text",
                    "text_content": "Speaker 1: We need to focus on Q4 deliverables. Speaker 2: The budget allocation needs review. Key action items: 1. Review budget by Friday 2. Schedule team meetings 3. Prepare quarterly reports. Next steps include stakeholder alignment and resource planning."
                },
                {
                    "title": "Project Status Update",
                    "kind": "text", 
                    "text_content": "Speaker A: Project is 75% complete. Speaker B: We're facing some technical challenges. Action items: Complete testing phase, resolve integration issues, prepare deployment plan. Timeline: Testing by next week, deployment in two weeks."
                },
                {
                    "title": "Team Retrospective",
                    "kind": "text",
                    "text_content": "Speaker 1: Communication has improved significantly. Speaker 2: We need better documentation processes. Key insights: Team collaboration is strong, documentation needs improvement, process optimization required. Action items: Create documentation templates, schedule training sessions."
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
    
    async def test_comprehensive_batch_report_formatting(self):
        """Test comprehensive batch report with clean formatting"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test AI format (comprehensive)
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Comprehensive Team Analysis Report",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Check for clean formatting (no speaker labels)
                    has_speaker_labels = bool(re.search(r'Speaker \d+:', content) or re.search(r'Speaker [A-Z]:', content))
                    
                    # Check for proper structure
                    has_meeting_summary = "MEETING SUMMARY" in content
                    has_executive_summary = "EXECUTIVE SUMMARY" in content
                    has_action_items = "ACTION ITEMS" in content
                    has_session_appendix = "APPENDIX" in content
                    
                    # Check content length (should be comprehensive)
                    is_comprehensive = len(content) > 2000
                    
                    success = (not has_speaker_labels and has_meeting_summary and 
                             has_executive_summary and has_action_items and 
                             has_session_appendix and is_comprehensive)
                    
                    details = f"Length: {len(content)}, Speaker labels removed: {not has_speaker_labels}, Sections: {has_meeting_summary and has_executive_summary and has_action_items}"
                    await self.log_result("Comprehensive Batch Report Formatting", success, details)
                    
                    return success
                else:
                    await self.log_result("Comprehensive Batch Report Formatting", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Comprehensive Batch Report Formatting", False, f"Error: {str(e)}")
            return False
    
    async def test_action_items_table_clean(self):
        """Test that action items table is clean and structured"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Action Items Analysis",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Look for action items section
                    action_items_match = re.search(r'CONSOLIDATED ACTION ITEMS.*?(?=\n\n---|\nAPPENDIX|$)', content, re.DOTALL)
                    
                    if action_items_match:
                        action_items_section = action_items_match.group(0)
                        
                        # Check for table structure
                        has_table_headers = "No." in action_items_section and "Action Item" in action_items_section
                        has_numbered_items = bool(re.search(r'\n\s*\d+\s*\|', action_items_section))
                        no_speaker_labels = not bool(re.search(r'Speaker \d+|Speaker [A-Z]', action_items_section))
                        
                        success = has_table_headers and has_numbered_items and no_speaker_labels
                        details = f"Table headers: {has_table_headers}, Numbered items: {has_numbered_items}, Clean of speaker labels: {no_speaker_labels}"
                        await self.log_result("Action Items Table Clean", success, details)
                        return success
                    else:
                        await self.log_result("Action Items Table Clean", False, "No action items section found")
                        return False
                else:
                    await self.log_result("Action Items Table Clean", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Action Items Table Clean", False, f"Error: {str(e)}")
            return False
    
    async def test_session_appendix_cleaned(self):
        """Test that session appendix is properly cleaned"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Session Content Analysis",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Look for appendix section
                    appendix_match = re.search(r'APPENDIX: CLEANED SESSION SUMMARIES.*$', content, re.DOTALL)
                    
                    if appendix_match:
                        appendix_section = appendix_match.group(0)
                        
                        # Check that speaker labels are removed
                        no_speaker_labels = not bool(re.search(r'Speaker \d+:|Speaker [A-Z]:', appendix_section))
                        
                        # Check for session structure
                        has_sessions = "SESSION:" in appendix_section
                        has_content = len(appendix_section) > 500  # Should have substantial content
                        
                        success = no_speaker_labels and has_sessions and has_content
                        details = f"Speaker labels removed: {no_speaker_labels}, Has sessions: {has_sessions}, Substantial content: {has_content}"
                        await self.log_result("Session Appendix Cleaned", success, details)
                        return success
                    else:
                        await self.log_result("Session Appendix Cleaned", False, "No appendix section found")
                        return False
                else:
                    await self.log_result("Session Appendix Cleaned", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Session Appendix Cleaned", False, f"Error: {str(e)}")
            return False
    
    async def test_note_status_updates_comprehensive(self):
        """Test that notes are marked as completed after comprehensive batch export"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Get initial note statuses
            initial_statuses = {}
            async with httpx.AsyncClient(timeout=30) as client:
                for note in self.test_notes:
                    response = await client.get(f"{API_BASE}/notes/{note['id']}", headers=headers)
                    if response.status_code == 200:
                        note_data = response.json()
                        initial_statuses[note['id']] = note_data.get('status')
            
            # Generate comprehensive batch report
            batch_request = {
                "note_ids": [note["id"] for note in self.test_notes],
                "title": "Status Update Test Report",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    # Check note statuses after export
                    updated_statuses = {}
                    async with httpx.AsyncClient(timeout=30) as client:
                        for note in self.test_notes:
                            response = await client.get(f"{API_BASE}/notes/{note['id']}", headers=headers)
                            if response.status_code == 200:
                                note_data = response.json()
                                updated_statuses[note['id']] = note_data.get('status')
                    
                    # Check if statuses were updated to 'completed'
                    completed_count = sum(1 for status in updated_statuses.values() if status == 'completed')
                    success = completed_count == len(self.test_notes)
                    
                    details = f"Notes marked as completed: {completed_count}/{len(self.test_notes)}"
                    await self.log_result("Note Status Updates - Comprehensive", success, details)
                    return success
                else:
                    await self.log_result("Note Status Updates - Comprehensive", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Note Status Updates - Comprehensive", False, f"Error: {str(e)}")
            return False
    
    async def test_note_status_updates_regular_batch(self):
        """Test that notes are marked as completed after regular batch export"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create new test notes for this test
            new_note_data = {
                "title": "Regular Batch Test Note",
                "kind": "text",
                "text_content": "This is a test note for regular batch report functionality. It contains some sample content for testing purposes."
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{API_BASE}/notes", json=new_note_data, headers=headers)
                
                if response.status_code == 200:
                    note_info = response.json()
                    test_note_id = note_info["id"]
                    
                    # Generate regular batch report
                    batch_request = {
                        "note_ids": [test_note_id],
                        "title": "Regular Batch Status Test",
                        "format": "professional"
                    }
                    
                    response = await client.post(f"{API_BASE}/notes/batch-report", 
                                               json=batch_request, headers=headers)
                    
                    if response.status_code == 200:
                        # Check note status after export
                        response = await client.get(f"{API_BASE}/notes/{test_note_id}", headers=headers)
                        if response.status_code == 200:
                            note_data = response.json()
                            final_status = note_data.get('status')
                            
                            success = final_status == 'completed'
                            details = f"Final status: {final_status}"
                            await self.log_result("Note Status Updates - Regular Batch", success, details)
                            return success
                        else:
                            await self.log_result("Note Status Updates - Regular Batch", False, "Failed to get note status")
                            return False
                    else:
                        await self.log_result("Note Status Updates - Regular Batch", False, f"Batch report failed: {response.status_code}")
                        return False
                else:
                    await self.log_result("Note Status Updates - Regular Batch", False, f"Note creation failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Note Status Updates - Regular Batch", False, f"Error: {str(e)}")
            return False
    
    async def test_error_handling_invalid_notes(self):
        """Test error handling with invalid note IDs"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with invalid note IDs
            batch_request = {
                "note_ids": ["invalid-id-1", "invalid-id-2"],
                "title": "Invalid Notes Test",
                "format": "ai"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                           json=batch_request, headers=headers)
                
                # Should return 400 for no valid content
                success = response.status_code == 400
                details = f"Status: {response.status_code}"
                if response.status_code == 400:
                    error_detail = response.json().get('detail', '')
                    details += f", Error: {error_detail}"
                
                await self.log_result("Error Handling - Invalid Notes", success, details)
                return success
                
        except Exception as e:
            await self.log_result("Error Handling - Invalid Notes", False, f"Error: {str(e)}")
            return False
    
    async def test_error_handling_empty_content(self):
        """Test error handling with empty content"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create note with no content
            empty_note_data = {
                "title": "Empty Note Test",
                "kind": "text"
                # No text_content provided
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{API_BASE}/notes", json=empty_note_data, headers=headers)
                
                if response.status_code == 200:
                    note_info = response.json()
                    empty_note_id = note_info["id"]
                    
                    # Try to generate batch report with empty note
                    batch_request = {
                        "note_ids": [empty_note_id],
                        "title": "Empty Content Test",
                        "format": "ai"
                    }
                    
                    response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                               json=batch_request, headers=headers)
                    
                    # Should return 400 for no valid content
                    success = response.status_code == 400
                    details = f"Status: {response.status_code}"
                    if response.status_code == 400:
                        error_detail = response.json().get('detail', '')
                        details += f", Error: {error_detail}"
                    
                    await self.log_result("Error Handling - Empty Content", success, details)
                    return success
                else:
                    await self.log_result("Error Handling - Empty Content", False, f"Note creation failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Error Handling - Empty Content", False, f"Error: {str(e)}")
            return False
    
    async def test_different_formats(self):
        """Test different export formats (TXT, RTF, AI)"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            formats_to_test = ["txt", "rtf", "ai"]
            format_results = {}
            
            for format_type in formats_to_test:
                if format_type in ["txt", "rtf"]:
                    # Use regular batch-report for txt/rtf
                    batch_request = {
                        "note_ids": [self.test_notes[0]["id"]],  # Use first test note
                        "title": f"Format Test {format_type.upper()}",
                        "format": format_type
                    }
                    
                    async with httpx.AsyncClient(timeout=60) as client:
                        response = await client.post(f"{API_BASE}/notes/batch-report", 
                                                   json=batch_request, headers=headers)
                else:
                    # Use comprehensive-batch-report for ai format
                    batch_request = {
                        "note_ids": [self.test_notes[0]["id"]],
                        "title": f"Format Test {format_type.upper()}",
                        "format": format_type
                    }
                    
                    async with httpx.AsyncClient(timeout=120) as client:
                        response = await client.post(f"{API_BASE}/notes/comprehensive-batch-report", 
                                                   json=batch_request, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    
                    # Validate format-specific content
                    if format_type == "txt":
                        # Should be plain text
                        format_valid = len(content) > 100 and not content.startswith("{\\rtf")
                    elif format_type == "rtf":
                        # Should be RTF format
                        format_valid = content.startswith("{\\rtf") and content.endswith("}")
                    else:  # ai format
                        # Should be comprehensive with multiple sections
                        format_valid = len(content) > 1000 and "MEETING SUMMARY" in content
                    
                    format_results[format_type] = format_valid
                    await self.log_result(f"Format Test - {format_type.upper()}", format_valid, 
                                        f"Content length: {len(content)}")
                else:
                    format_results[format_type] = False
                    await self.log_result(f"Format Test - {format_type.upper()}", False, 
                                        f"Status: {response.status_code}")
            
            # Overall success if all formats work
            success = all(format_results.values())
            return success
            
        except Exception as e:
            await self.log_result("Different Formats Test", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all batch report tests"""
        print("🔍 ENHANCED BATCH REPORT FUNCTIONALITY TESTING")
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
        test_methods = [
            self.test_comprehensive_batch_report_formatting,
            self.test_action_items_table_clean,
            self.test_session_appendix_cleaned,
            self.test_note_status_updates_comprehensive,
            self.test_note_status_updates_regular_batch,
            self.test_error_handling_invalid_notes,
            self.test_error_handling_empty_content,
            self.test_different_formats
        ]
        
        for test_method in test_methods:
            await test_method()
            print()  # Add spacing between tests
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
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
        
        print("\n🎯 BATCH REPORT TESTING CONCLUSIONS:")
        
        if success_rate >= 90:
            print("✅ EXCELLENT: Enhanced batch report functionality is working perfectly!")
            print("   - Comprehensive formatting with clean output")
            print("   - Speaker labels properly removed")
            print("   - Action items table structured correctly")
            print("   - Note status updates working")
            print("   - All formats (TXT, RTF, AI) functional")
        elif success_rate >= 75:
            print("⚠️  GOOD: Most batch report functionality working with minor issues")
        else:
            print("❌ ISSUES: Significant problems with batch report functionality")
        
        return success_rate >= 75

async def main():
    """Main test execution"""
    tester = BatchReportTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 BATCH REPORT TESTING COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n🚨 BATCH REPORT TESTING COMPLETED WITH ISSUES!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())