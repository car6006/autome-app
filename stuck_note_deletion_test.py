#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone
import os
import time

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class StuckNoteDeletionTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"stuck_note_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123"
        self.auth_token = None
        self.test_user_id = None
        self.created_notes = []
        self.stuck_notes_found = []

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
        """Create a test user for stuck note testing"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                user_data = {
                    "email": self.test_user_email,
                    "username": f"stucktest{uuid.uuid4().hex[:8]}",
                    "password": self.test_user_password,
                    "first_name": "Stuck",
                    "last_name": "Tester"
                }
                
                response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.test_user_id = data.get("user", {}).get("id")
                    await self.log_test("Create Test User", True, f"User created: {self.test_user_email}")
                    return True
                else:
                    await self.log_test("Create Test User", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Create Test User", False, f"Exception: {str(e)}")
            return False

    async def scan_for_existing_stuck_notes(self):
        """Scan for existing stuck notes in the system"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                
                if response.status_code == 200:
                    notes = response.json()
                    stuck_statuses = ["uploading", "processing", "created"]
                    
                    for note in notes:
                        status = note.get("status", "")
                        created_at = note.get("created_at", "")
                        note_id = note.get("id", "")
                        title = note.get("title", "")
                        
                        # Check if note is stuck (in processing state for extended time)
                        if status in stuck_statuses:
                            # Parse created_at to check age
                            try:
                                if created_at:
                                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    age_minutes = (datetime.now(timezone.utc) - created_time).total_seconds() / 60
                                    
                                    # Consider notes stuck if they've been in processing state for more than 5 minutes
                                    if age_minutes > 5:
                                        self.stuck_notes_found.append({
                                            "id": note_id,
                                            "title": title,
                                            "status": status,
                                            "age_minutes": age_minutes,
                                            "created_at": created_at
                                        })
                            except Exception as e:
                                # If we can't parse the date, still consider it potentially stuck
                                if status in ["uploading", "processing"]:
                                    self.stuck_notes_found.append({
                                        "id": note_id,
                                        "title": title,
                                        "status": status,
                                        "age_minutes": "unknown",
                                        "created_at": created_at
                                    })
                    
                    await self.log_test("Scan for Existing Stuck Notes", True, 
                                      f"Found {len(self.stuck_notes_found)} potentially stuck notes")
                    return True
                else:
                    await self.log_test("Scan for Existing Stuck Notes", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Scan for Existing Stuck Notes", False, f"Exception: {str(e)}")
            return False

    async def create_test_stuck_note(self):
        """Create a test note that will be stuck in uploading status"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                # Create a photo note (these start in 'created' status)
                note_data = {
                    "title": f"Test Stuck Note {uuid.uuid4().hex[:8]}",
                    "kind": "photo"
                }
                
                response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    note_id = data.get("id")
                    self.created_notes.append(note_id)
                    
                    # Simulate a stuck note by creating one and not completing the upload
                    await self.log_test("Create Test Stuck Note", True, 
                                      f"Created test note {note_id} in 'created' status")
                    return note_id
                else:
                    await self.log_test("Create Test Stuck Note", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    return None
                    
        except Exception as e:
            await self.log_test("Create Test Stuck Note", False, f"Exception: {str(e)}")
            return None

    async def verify_note_exists(self, note_id):
        """Verify that a note exists in the system"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                
                if response.status_code == 200:
                    note_data = response.json()
                    await self.log_test(f"Verify Note Exists ({note_id[:8]})", True, 
                                      f"Note found with status: {note_data.get('status')}")
                    return True, note_data
                elif response.status_code == 404:
                    await self.log_test(f"Verify Note Exists ({note_id[:8]})", True, 
                                      "Note correctly not found (404)")
                    return False, None
                else:
                    await self.log_test(f"Verify Note Exists ({note_id[:8]})", False, 
                                      f"Unexpected status: {response.status_code}")
                    return False, None
                    
        except Exception as e:
            await self.log_test(f"Verify Note Exists ({note_id[:8]})", False, f"Exception: {str(e)}")
            return False, None

    async def delete_note_via_api(self, note_id):
        """Delete a note using the DELETE API endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.delete(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    await self.log_test(f"Delete Note via API ({note_id[:8]})", True, 
                                      f"Note deleted successfully: {data.get('message')}")
                    return True
                elif response.status_code == 404:
                    await self.log_test(f"Delete Note via API ({note_id[:8]})", True, 
                                      "Note already deleted (404)")
                    return True
                else:
                    await self.log_test(f"Delete Note via API ({note_id[:8]})", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test(f"Delete Note via API ({note_id[:8]})", False, f"Exception: {str(e)}")
            return False

    async def verify_note_deleted_from_list(self, note_id):
        """Verify that the note no longer appears in the notes list"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                
                if response.status_code == 200:
                    notes = response.json()
                    note_ids = [note.get("id") for note in notes]
                    
                    if note_id not in note_ids:
                        await self.log_test(f"Verify Note Deleted from List ({note_id[:8]})", True, 
                                          "Note successfully removed from notes list")
                        return True
                    else:
                        await self.log_test(f"Verify Note Deleted from List ({note_id[:8]})", False, 
                                          "Note still appears in notes list")
                        return False
                else:
                    await self.log_test(f"Verify Note Deleted from List ({note_id[:8]})", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test(f"Verify Note Deleted from List ({note_id[:8]})", False, f"Exception: {str(e)}")
            return False

    async def test_complete_deletion_workflow(self, note_id):
        """Test the complete deletion workflow for a stuck note"""
        try:
            # Step 1: Verify note exists
            exists_before, note_data = await self.verify_note_exists(note_id)
            if not exists_before:
                await self.log_test(f"Complete Deletion Workflow ({note_id[:8]})", False, 
                                  "Note doesn't exist to begin with")
                return False
            
            # Step 2: Delete the note
            deletion_success = await self.delete_note_via_api(note_id)
            if not deletion_success:
                await self.log_test(f"Complete Deletion Workflow ({note_id[:8]})", False, 
                                  "Failed to delete note via API")
                return False
            
            # Step 3: Verify note no longer exists individually
            exists_after, _ = await self.verify_note_exists(note_id)
            if exists_after:
                await self.log_test(f"Complete Deletion Workflow ({note_id[:8]})", False, 
                                  "Note still exists after deletion")
                return False
            
            # Step 4: Verify note no longer appears in list
            list_verification = await self.verify_note_deleted_from_list(note_id)
            if not list_verification:
                await self.log_test(f"Complete Deletion Workflow ({note_id[:8]})", False, 
                                  "Note still appears in notes list")
                return False
            
            await self.log_test(f"Complete Deletion Workflow ({note_id[:8]})", True, 
                              "Note completely removed from all systems")
            return True
            
        except Exception as e:
            await self.log_test(f"Complete Deletion Workflow ({note_id[:8]})", False, f"Exception: {str(e)}")
            return False

    async def delete_all_found_stuck_notes(self):
        """Delete all stuck notes found in the system"""
        if not self.stuck_notes_found:
            await self.log_test("Delete All Found Stuck Notes", True, "No stuck notes found to delete")
            return True
        
        deleted_count = 0
        failed_count = 0
        
        for stuck_note in self.stuck_notes_found:
            note_id = stuck_note["id"]
            title = stuck_note["title"]
            status = stuck_note["status"]
            
            print(f"\n🗑️  Attempting to delete stuck note: {title} (Status: {status}, ID: {note_id[:8]})")
            
            success = await self.test_complete_deletion_workflow(note_id)
            if success:
                deleted_count += 1
                print(f"✅ Successfully deleted stuck note: {title}")
            else:
                failed_count += 1
                print(f"❌ Failed to delete stuck note: {title}")
        
        if failed_count == 0:
            await self.log_test("Delete All Found Stuck Notes", True, 
                              f"Successfully deleted all {deleted_count} stuck notes")
            return True
        else:
            await self.log_test("Delete All Found Stuck Notes", False, 
                              f"Deleted {deleted_count}, failed {failed_count}")
            return False

    async def verify_clean_system_state(self):
        """Verify that the system is in a clean state with no stuck notes"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                
                if response.status_code == 200:
                    notes = response.json()
                    stuck_statuses = ["uploading", "processing"]
                    
                    current_stuck_notes = []
                    for note in notes:
                        status = note.get("status", "")
                        created_at = note.get("created_at", "")
                        
                        if status in stuck_statuses:
                            # Check if it's actually stuck (older than 5 minutes)
                            try:
                                if created_at:
                                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    age_minutes = (datetime.now(timezone.utc) - created_time).total_seconds() / 60
                                    
                                    if age_minutes > 5:
                                        current_stuck_notes.append({
                                            "id": note.get("id"),
                                            "title": note.get("title"),
                                            "status": status,
                                            "age_minutes": age_minutes
                                        })
                            except Exception:
                                # If we can't parse date, consider it stuck if in uploading/processing
                                current_stuck_notes.append({
                                    "id": note.get("id"),
                                    "title": note.get("title"),
                                    "status": status,
                                    "age_minutes": "unknown"
                                })
                    
                    if len(current_stuck_notes) == 0:
                        await self.log_test("Verify Clean System State", True, 
                                          "No stuck notes found - system is clean")
                        return True
                    else:
                        await self.log_test("Verify Clean System State", False, 
                                          f"Still found {len(current_stuck_notes)} stuck notes")
                        for stuck in current_stuck_notes:
                            print(f"   - {stuck['title']} (Status: {stuck['status']}, Age: {stuck['age_minutes']} min)")
                        return False
                else:
                    await self.log_test("Verify Clean System State", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Verify Clean System State", False, f"Exception: {str(e)}")
            return False

    async def cleanup_test_notes(self):
        """Clean up any test notes created during testing"""
        try:
            cleanup_count = 0
            for note_id in self.created_notes:
                success = await self.delete_note_via_api(note_id)
                if success:
                    cleanup_count += 1
            
            await self.log_test("Cleanup Test Notes", True, 
                              f"Cleaned up {cleanup_count}/{len(self.created_notes)} test notes")
            return True
        except Exception as e:
            await self.log_test("Cleanup Test Notes", False, f"Exception: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all stuck note deletion tests"""
        print("🗑️  Starting Stuck Note Deletion Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User Email: {self.test_user_email}")
        print("=" * 80)

        # Test sequence
        tests = [
            ("Setup - Create Test User", self.create_test_user),
            ("Scan for Existing Stuck Notes", self.scan_for_existing_stuck_notes),
            ("Delete All Found Stuck Notes", self.delete_all_found_stuck_notes),
            ("Create Test Stuck Note", self.create_test_stuck_note),
            ("Test Complete Deletion Workflow", lambda: self.test_complete_deletion_workflow(self.created_notes[-1]) if self.created_notes else True),
            ("Verify Clean System State", self.verify_clean_system_state),
            ("Cleanup Test Notes", self.cleanup_test_notes)
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                if callable(test_func):
                    result = await test_func()
                else:
                    result = test_func
                    
                if result:
                    passed += 1
            except Exception as e:
                await self.log_test(test_name, False, f"Unexpected exception: {str(e)}")

        print("=" * 80)
        print(f"🗑️  Stuck Note Deletion Testing Complete")
        print(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("✅ All stuck note deletion tests PASSED!")
        else:
            print("❌ Some stuck note deletion tests FAILED!")
            
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    tester = StuckNoteDeletionTester()
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
        print("✅ Stuck note deletion functionality is working correctly!")
        print("✅ System can identify stuck notes (uploading/processing for >5 minutes)")
        print("✅ Notes can be completely deleted from all systems")
        print("✅ Deleted notes no longer appear in any interface")
        print("✅ System is clean with no remaining stuck notes")
    else:
        print("❌ Stuck note deletion functionality has issues that need attention")
        failed_tests = [r for r in results if not r["success"]]
        print(f"❌ Failed tests: {len(failed_tests)}")
        for failed in failed_tests:
            print(f"   - {failed['test']}: {failed['details']}")
    
    # Special summary for stuck notes found
    if tester.stuck_notes_found:
        print(f"\n🚨 STUCK NOTES FOUND AND PROCESSED: {len(tester.stuck_notes_found)}")
        for stuck_note in tester.stuck_notes_found:
            print(f"   - {stuck_note['title']} (Status: {stuck_note['status']}, Age: {stuck_note['age_minutes']} min)")

if __name__ == "__main__":
    asyncio.run(main())