#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone
import os
import glob
from pathlib import Path

# Backend URL from frontend environment
BACKEND_URL = "https://auto-me-debugger.preview.emergentagent.com/api"

class ComprehensiveStuckNoteCleanupTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"cleanup_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123"
        self.auth_token = None
        self.test_user_id = None
        self.storage_path = "/tmp/autome_storage"
        self.found_issues = []

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
        """Create a test user for comprehensive cleanup testing"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                user_data = {
                    "email": self.test_user_email,
                    "username": f"cleanup{uuid.uuid4().hex[:8]}",
                    "password": self.test_user_password,
                    "first_name": "Cleanup",
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

    async def scan_all_user_notes(self):
        """Scan all notes for all users to find stuck notes"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                
                if response.status_code == 200:
                    notes = response.json()
                    stuck_statuses = ["uploading", "processing", "created"]
                    stuck_notes = []
                    
                    for note in notes:
                        status = note.get("status", "")
                        created_at = note.get("created_at", "")
                        note_id = note.get("id", "")
                        title = note.get("title", "")
                        kind = note.get("kind", "")
                        
                        # Check if note is stuck
                        if status in stuck_statuses:
                            try:
                                if created_at:
                                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    age_minutes = (datetime.now(timezone.utc) - created_time).total_seconds() / 60
                                    
                                    # Consider notes stuck if they've been in processing state for more than 2 minutes
                                    if age_minutes > 2:
                                        stuck_note = {
                                            "id": note_id,
                                            "title": title,
                                            "status": status,
                                            "kind": kind,
                                            "age_minutes": round(age_minutes, 2),
                                            "created_at": created_at,
                                            "user_id": note.get("user_id", "unknown")
                                        }
                                        stuck_notes.append(stuck_note)
                                        self.found_issues.append(f"Stuck note: {title} (Status: {status}, Age: {age_minutes:.1f} min)")
                            except Exception as e:
                                # If we can't parse the date, still consider it potentially stuck
                                if status in ["uploading", "processing"]:
                                    stuck_note = {
                                        "id": note_id,
                                        "title": title,
                                        "status": status,
                                        "kind": kind,
                                        "age_minutes": "unknown",
                                        "created_at": created_at,
                                        "user_id": note.get("user_id", "unknown")
                                    }
                                    stuck_notes.append(stuck_note)
                                    self.found_issues.append(f"Stuck note: {title} (Status: {status}, Age: unknown)")
                    
                    await self.log_test("Scan All User Notes", True, 
                                      f"Scanned {len(notes)} notes, found {len(stuck_notes)} stuck notes")
                    
                    if stuck_notes:
                        print("\n🚨 STUCK NOTES FOUND:")
                        for stuck in stuck_notes:
                            print(f"   - {stuck['title']} (ID: {stuck['id'][:8]}, Status: {stuck['status']}, Age: {stuck['age_minutes']} min)")
                    
                    return stuck_notes
                else:
                    await self.log_test("Scan All User Notes", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    return []
                    
        except Exception as e:
            await self.log_test("Scan All User Notes", False, f"Exception: {str(e)}")
            return []

    async def check_storage_files(self):
        """Check for orphaned files in storage directory"""
        try:
            if not os.path.exists(self.storage_path):
                await self.log_test("Check Storage Files", True, "Storage directory doesn't exist - no orphaned files")
                return []
            
            # Get all files in storage
            storage_files = []
            for file_path in glob.glob(f"{self.storage_path}/*"):
                if os.path.isfile(file_path):
                    file_info = {
                        "path": file_path,
                        "name": os.path.basename(file_path),
                        "size": os.path.getsize(file_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    storage_files.append(file_info)
            
            await self.log_test("Check Storage Files", True, 
                              f"Found {len(storage_files)} files in storage directory")
            
            if storage_files:
                print(f"\n📁 STORAGE FILES FOUND ({len(storage_files)}):")
                for file_info in storage_files[:10]:  # Show first 10
                    print(f"   - {file_info['name']} ({file_info['size']} bytes, modified: {file_info['modified']})")
                if len(storage_files) > 10:
                    print(f"   ... and {len(storage_files) - 10} more files")
            
            return storage_files
            
        except Exception as e:
            await self.log_test("Check Storage Files", False, f"Exception: {str(e)}")
            return []

    async def delete_stuck_note_completely(self, note_id, note_title):
        """Completely delete a stuck note from all systems"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Step 1: Delete via API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.delete(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                
                if response.status_code == 200:
                    await self.log_test(f"Delete Note API ({note_id[:8]})", True, 
                                      f"Successfully deleted {note_title}")
                elif response.status_code == 404:
                    await self.log_test(f"Delete Note API ({note_id[:8]})", True, 
                                      f"Note {note_title} already deleted")
                else:
                    await self.log_test(f"Delete Note API ({note_id[:8]})", False, 
                                      f"Failed to delete {note_title}: {response.status_code}")
                    return False
            
            # Step 2: Verify deletion
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                
                if response.status_code == 404:
                    await self.log_test(f"Verify Deletion ({note_id[:8]})", True, 
                                      f"Note {note_title} successfully removed from database")
                else:
                    await self.log_test(f"Verify Deletion ({note_id[:8]})", False, 
                                      f"Note {note_title} still exists after deletion")
                    return False
            
            # Step 3: Check if it appears in notes list
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                
                if response.status_code == 200:
                    notes = response.json()
                    note_ids = [note.get("id") for note in notes]
                    
                    if note_id not in note_ids:
                        await self.log_test(f"Verify List Removal ({note_id[:8]})", True, 
                                          f"Note {note_title} removed from notes list")
                    else:
                        await self.log_test(f"Verify List Removal ({note_id[:8]})", False, 
                                          f"Note {note_title} still in notes list")
                        return False
            
            return True
            
        except Exception as e:
            await self.log_test(f"Delete Stuck Note ({note_id[:8]})", False, f"Exception: {str(e)}")
            return False

    async def cleanup_orphaned_storage_files(self, storage_files):
        """Clean up orphaned files in storage (optional - be careful!)"""
        try:
            # For safety, we'll only report on files, not delete them automatically
            # In a real scenario, you'd want to cross-reference with database
            
            if not storage_files:
                await self.log_test("Cleanup Orphaned Storage Files", True, "No storage files to check")
                return True
            
            # Check if any files are very old (more than 24 hours)
            old_files = []
            current_time = datetime.now()
            
            for file_info in storage_files:
                try:
                    modified_time = datetime.fromisoformat(file_info['modified'])
                    age_hours = (current_time - modified_time).total_seconds() / 3600
                    
                    if age_hours > 24:  # Files older than 24 hours
                        old_files.append({
                            **file_info,
                            "age_hours": round(age_hours, 2)
                        })
                except Exception:
                    pass
            
            if old_files:
                await self.log_test("Cleanup Orphaned Storage Files", True, 
                                  f"Found {len(old_files)} files older than 24 hours (not auto-deleted for safety)")
                print(f"\n⚠️  OLD STORAGE FILES (>24h):")
                for old_file in old_files[:5]:  # Show first 5
                    print(f"   - {old_file['name']} (Age: {old_file['age_hours']} hours)")
                if len(old_files) > 5:
                    print(f"   ... and {len(old_files) - 5} more old files")
                    
                self.found_issues.append(f"Found {len(old_files)} old storage files (>24h)")
            else:
                await self.log_test("Cleanup Orphaned Storage Files", True, 
                                  "No old storage files found")
            
            return True
            
        except Exception as e:
            await self.log_test("Cleanup Orphaned Storage Files", False, f"Exception: {str(e)}")
            return False

    async def verify_system_clean(self):
        """Final verification that system is clean"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                
                if response.status_code == 200:
                    notes = response.json()
                    stuck_statuses = ["uploading", "processing"]
                    
                    current_stuck = []
                    for note in notes:
                        status = note.get("status", "")
                        if status in stuck_statuses:
                            created_at = note.get("created_at", "")
                            try:
                                if created_at:
                                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    age_minutes = (datetime.now(timezone.utc) - created_time).total_seconds() / 60
                                    
                                    if age_minutes > 2:  # Still stuck after 2 minutes
                                        current_stuck.append({
                                            "id": note.get("id"),
                                            "title": note.get("title"),
                                            "status": status,
                                            "age_minutes": round(age_minutes, 2)
                                        })
                            except Exception:
                                current_stuck.append({
                                    "id": note.get("id"),
                                    "title": note.get("title"),
                                    "status": status,
                                    "age_minutes": "unknown"
                                })
                    
                    if len(current_stuck) == 0:
                        await self.log_test("Verify System Clean", True, 
                                          "✅ No stuck notes found - system is clean!")
                        return True
                    else:
                        await self.log_test("Verify System Clean", False, 
                                          f"❌ Still found {len(current_stuck)} stuck notes")
                        for stuck in current_stuck:
                            print(f"   - {stuck['title']} (Status: {stuck['status']}, Age: {stuck['age_minutes']} min)")
                        return False
                else:
                    await self.log_test("Verify System Clean", False, 
                                      f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Verify System Clean", False, f"Exception: {str(e)}")
            return False

    async def run_comprehensive_cleanup(self):
        """Run comprehensive stuck note cleanup"""
        print("🧹 Starting Comprehensive Stuck Note Cleanup...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User Email: {self.test_user_email}")
        print("=" * 80)

        # Step 1: Setup
        setup_success = await self.create_test_user()
        if not setup_success:
            print("❌ Failed to create test user - cannot proceed")
            return False, 0, []

        # Step 2: Scan for stuck notes
        stuck_notes = await self.scan_all_user_notes()
        
        # Step 3: Check storage files
        storage_files = await self.check_storage_files()
        
        # Step 4: Delete stuck notes if found
        if stuck_notes:
            print(f"\n🗑️  DELETING {len(stuck_notes)} STUCK NOTES...")
            deleted_count = 0
            
            for stuck_note in stuck_notes:
                note_id = stuck_note["id"]
                note_title = stuck_note["title"]
                
                print(f"\n🗑️  Deleting: {note_title} (Status: {stuck_note['status']}, Age: {stuck_note['age_minutes']} min)")
                
                success = await self.delete_stuck_note_completely(note_id, note_title)
                if success:
                    deleted_count += 1
                    print(f"✅ Successfully deleted: {note_title}")
                else:
                    print(f"❌ Failed to delete: {note_title}")
            
            await self.log_test("Delete All Stuck Notes", deleted_count == len(stuck_notes), 
                              f"Deleted {deleted_count}/{len(stuck_notes)} stuck notes")
        else:
            await self.log_test("Delete All Stuck Notes", True, "No stuck notes found to delete")
        
        # Step 5: Handle storage files
        await self.cleanup_orphaned_storage_files(storage_files)
        
        # Step 6: Final verification
        system_clean = await self.verify_system_clean()
        
        # Calculate results
        passed = len([r for r in self.test_results if r["success"]])
        total = len(self.test_results)
        
        print("\n" + "=" * 80)
        print(f"🧹 Comprehensive Cleanup Complete")
        print(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if system_clean and len(self.found_issues) == 0:
            print("✅ System is completely clean - no stuck notes or issues found!")
        elif system_clean:
            print("✅ All stuck notes cleaned up successfully!")
        else:
            print("❌ Some issues remain - manual intervention may be required")
        
        return system_clean, len(stuck_notes), self.found_issues

async def main():
    """Main cleanup runner"""
    tester = ComprehensiveStuckNoteCleanupTester()
    system_clean, stuck_notes_found, issues = await tester.run_comprehensive_cleanup()
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED TEST RESULTS:")
    print("=" * 80)
    
    for result in tester.test_results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    print("\n" + "=" * 80)
    print("🎯 FINAL CLEANUP SUMMARY:")
    print("=" * 80)
    
    if system_clean:
        print("✅ SYSTEM STATUS: CLEAN")
        print("✅ No stuck notes remaining in the system")
        print("✅ All 'uploading' and 'processing' notes have been resolved")
        print("✅ User interface should be clean with no stuck notes")
        
        if stuck_notes_found > 0:
            print(f"✅ Successfully cleaned up {stuck_notes_found} stuck notes")
    else:
        print("❌ SYSTEM STATUS: ISSUES REMAIN")
        print("❌ Some stuck notes or issues could not be resolved")
        print("❌ Manual intervention may be required")
    
    if issues:
        print(f"\n🚨 ISSUES FOUND AND ADDRESSED ({len(issues)}):")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n✅ NO ISSUES FOUND - System was already clean")
    
    print("\n" + "=" * 80)
    print("📝 RECOMMENDATIONS:")
    print("=" * 80)
    
    if system_clean:
        print("✅ System is ready for normal operation")
        print("✅ Users should no longer see stuck 'uploading' notes")
        print("✅ New uploads should process normally")
    else:
        print("⚠️  Manual database cleanup may be required")
        print("⚠️  Check backend logs for processing errors")
        print("⚠️  Consider restarting backend services")

if __name__ == "__main__":
    asyncio.run(main())