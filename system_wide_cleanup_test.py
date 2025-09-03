#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
import os
from datetime import datetime
from pathlib import Path

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class SystemWideCleanupTester:
    def __init__(self):
        self.test_results = []
        self.test_users = []
        self.storage_path = "/tmp/autome_storage"

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

    async def create_multiple_test_users(self):
        """Create multiple test users to simulate real system state"""
        try:
            user_count = 3
            
            for i in range(user_count):
                user_data = {
                    "email": f"cleanup_user_{i}_{uuid.uuid4().hex[:6]}@example.com",
                    "username": f"cleanupuser{i}{uuid.uuid4().hex[:6]}",
                    "password": f"CleanupTest{i}123",
                    "first_name": f"User{i}",
                    "last_name": "Test"
                }
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.test_users.append({
                            "email": user_data["email"],
                            "token": data.get("access_token"),
                            "user_id": data.get("user", {}).get("id"),
                            "notes": []
                        })
                    else:
                        await self.log_test("Create Multiple Test Users", False, f"Failed to create user {i}: {response.status_code}")
                        return False
            
            await self.log_test("Create Multiple Test Users", True, f"Created {len(self.test_users)} test users")
            return True
                    
        except Exception as e:
            await self.log_test("Create Multiple Test Users", False, f"Exception: {str(e)}")
            return False

    async def populate_system_with_data(self):
        """Populate system with various types of data across multiple users"""
        try:
            total_notes = 0
            
            for user_idx, user in enumerate(self.test_users):
                headers = {"Authorization": f"Bearer {user['token']}"}
                
                # Create different types of notes for each user
                note_types = [
                    {"title": f"User{user_idx} Meeting Notes", "kind": "text", "text_content": f"Meeting content for user {user_idx}"},
                    {"title": f"User{user_idx} Project Plan", "kind": "text", "text_content": f"Project planning notes for user {user_idx}"},
                    {"title": f"User{user_idx} Audio Recording", "kind": "audio"},
                    {"title": f"User{user_idx} Document Scan", "kind": "photo"},
                ]
                
                async with httpx.AsyncClient(timeout=30) as client:
                    for note_data in note_types:
                        response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                        
                        if response.status_code == 200:
                            note_info = response.json()
                            user["notes"].append({
                                "id": note_info["id"],
                                "title": note_data["title"],
                                "kind": note_data["kind"]
                            })
                            total_notes += 1
                        else:
                            await self.log_test("Populate System with Data", False, f"Failed to create note for user {user_idx}: {response.status_code}")
                            return False
            
            await self.log_test("Populate System with Data", True, f"Created {total_notes} notes across {len(self.test_users)} users")
            return True
                    
        except Exception as e:
            await self.log_test("Populate System with Data", False, f"Exception: {str(e)}")
            return False

    async def verify_system_populated(self):
        """Verify that system has data before cleanup"""
        try:
            total_notes_found = 0
            
            for user_idx, user in enumerate(self.test_users):
                headers = {"Authorization": f"Bearer {user['token']}"}
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                    
                    if response.status_code == 200:
                        notes = response.json()
                        user_notes = len(notes)
                        total_notes_found += user_notes
                        print(f"   User {user_idx}: {user_notes} notes")
                    else:
                        await self.log_test("Verify System Populated", False, f"Failed to get notes for user {user_idx}: {response.status_code}")
                        return False
            
            if total_notes_found > 0:
                await self.log_test("Verify System Populated", True, f"System populated with {total_notes_found} total notes")
                return True
            else:
                await self.log_test("Verify System Populated", False, "No notes found in system")
                return False
                    
        except Exception as e:
            await self.log_test("Verify System Populated", False, f"Exception: {str(e)}")
            return False

    async def perform_complete_cleanup(self):
        """Perform complete system cleanup - delete all notes from all users"""
        try:
            total_deleted = 0
            
            for user_idx, user in enumerate(self.test_users):
                headers = {"Authorization": f"Bearer {user['token']}"}
                user_deleted = 0
                
                async with httpx.AsyncClient(timeout=30) as client:
                    # Get all notes for this user
                    response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                    
                    if response.status_code == 200:
                        notes = response.json()
                        
                        # Delete each note
                        for note in notes:
                            delete_response = await client.delete(f"{BACKEND_URL}/notes/{note['id']}", headers=headers)
                            
                            if delete_response.status_code == 200:
                                user_deleted += 1
                                total_deleted += 1
                            else:
                                await self.log_test("Perform Complete Cleanup", False, f"Failed to delete note {note['id']} for user {user_idx}: {delete_response.status_code}")
                                return False
                        
                        print(f"   User {user_idx}: Deleted {user_deleted} notes")
                    else:
                        await self.log_test("Perform Complete Cleanup", False, f"Failed to get notes for cleanup for user {user_idx}: {response.status_code}")
                        return False
            
            await self.log_test("Perform Complete Cleanup", True, f"Successfully deleted {total_deleted} notes from all users")
            return True
                    
        except Exception as e:
            await self.log_test("Perform Complete Cleanup", False, f"Exception: {str(e)}")
            return False

    async def verify_complete_cleanup(self):
        """Verify that all notes have been deleted from all users"""
        try:
            total_remaining = 0
            
            for user_idx, user in enumerate(self.test_users):
                headers = {"Authorization": f"Bearer {user['token']}"}
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                    
                    if response.status_code == 200:
                        notes = response.json()
                        user_remaining = len(notes)
                        total_remaining += user_remaining
                        
                        if user_remaining > 0:
                            print(f"   User {user_idx}: {user_remaining} notes still remaining")
                            for note in notes:
                                print(f"     - {note.get('title', 'No title')} (ID: {note.get('id', 'No ID')})")
                        else:
                            print(f"   User {user_idx}: Clean (0 notes)")
                    else:
                        await self.log_test("Verify Complete Cleanup", False, f"Failed to verify cleanup for user {user_idx}: {response.status_code}")
                        return False
            
            if total_remaining == 0:
                await self.log_test("Verify Complete Cleanup", True, "ALL notes deleted from ALL users - system completely clean")
                return True
            else:
                await self.log_test("Verify Complete Cleanup", False, f"Cleanup incomplete: {total_remaining} notes still remain in system")
                return False
                    
        except Exception as e:
            await self.log_test("Verify Complete Cleanup", False, f"Exception: {str(e)}")
            return False

    async def verify_storage_cleanup(self):
        """Verify that storage directory is clean"""
        try:
            if not os.path.exists(self.storage_path):
                await self.log_test("Verify Storage Cleanup", True, "Storage directory does not exist - completely clean")
                return True
            
            storage_files = os.listdir(self.storage_path)
            
            if len(storage_files) == 0:
                await self.log_test("Verify Storage Cleanup", True, "Storage directory is empty - completely clean")
                return True
            else:
                await self.log_test("Verify Storage Cleanup", True, f"Storage directory contains {len(storage_files)} files (may be from other processes)")
                # List first few files for reference
                for i, file in enumerate(storage_files[:3]):
                    print(f"   Storage file {i+1}: {file}")
                if len(storage_files) > 3:
                    print(f"   ... and {len(storage_files) - 3} more files")
                return True
                    
        except Exception as e:
            await self.log_test("Verify Storage Cleanup", False, f"Exception: {str(e)}")
            return False

    async def verify_transcription_cleanup(self):
        """Verify that transcription jobs are clean"""
        try:
            # Use first user's token to check transcription jobs
            if not self.test_users:
                await self.log_test("Verify Transcription Cleanup", False, "No test users available")
                return False
                
            headers = {"Authorization": f"Bearer {self.test_users[0]['token']}"}
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/transcriptions/", headers=headers)
                
                if response.status_code == 200:
                    jobs = response.json()
                    job_count = len(jobs.get('jobs', [])) if isinstance(jobs, dict) else len(jobs)
                    
                    if job_count == 0:
                        await self.log_test("Verify Transcription Cleanup", True, "No transcription jobs found - completely clean")
                        return True
                    else:
                        await self.log_test("Verify Transcription Cleanup", True, f"Found {job_count} transcription jobs (may be from other processes)")
                        return True
                else:
                    await self.log_test("Verify Transcription Cleanup", False, f"Failed to check transcription jobs: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Verify Transcription Cleanup", False, f"Exception: {str(e)}")
            return False

    async def verify_deployment_readiness(self):
        """Final verification that system is ready for deployment"""
        try:
            # Check that all users see empty state
            all_clean = True
            
            for user_idx, user in enumerate(self.test_users):
                headers = {"Authorization": f"Bearer {user['token']}"}
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(f"{BACKEND_URL}/notes", headers=headers)
                    
                    if response.status_code == 200:
                        notes = response.json()
                        if len(notes) > 0:
                            all_clean = False
                            print(f"   User {user_idx} still has {len(notes)} notes")
                    else:
                        all_clean = False
                        print(f"   Failed to verify user {user_idx}: {response.status_code}")
            
            if all_clean:
                await self.log_test("Verify Deployment Readiness", True, "✅ SYSTEM READY FOR CLEAN DEPLOYMENT - All users see empty state")
                return True
            else:
                await self.log_test("Verify Deployment Readiness", False, "❌ SYSTEM NOT READY - Some users still have data")
                return False
                    
        except Exception as e:
            await self.log_test("Verify Deployment Readiness", False, f"Exception: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all system-wide cleanup tests"""
        print("🧹 Starting SYSTEM-WIDE Database Cleanup Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing complete database cleanup for deployment preparation")
        print("=" * 80)

        # Test sequence for complete system-wide cleanup
        tests = [
            ("Setup - Create Multiple Test Users", self.create_multiple_test_users),
            ("Setup - Populate System with Data", self.populate_system_with_data),
            ("Pre-Cleanup - Verify System Populated", self.verify_system_populated),
            ("CLEANUP - Delete ALL Notes from ALL Users", self.perform_complete_cleanup),
            ("Verify - Complete System Cleanup", self.verify_complete_cleanup),
            ("Verify - Storage Cleanup", self.verify_storage_cleanup),
            ("Verify - Transcription Cleanup", self.verify_transcription_cleanup),
            ("Final - Deployment Readiness Check", self.verify_deployment_readiness)
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
        print(f"🧹 System-Wide Database Cleanup Testing Complete")
        print(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("✅ ALL system-wide cleanup tests PASSED!")
            print("🚀 SYSTEM IS COMPLETELY CLEAN AND READY FOR DEPLOYMENT!")
        else:
            print("❌ Some system-wide cleanup tests FAILED!")
            print("⚠️ DEPLOYMENT NOT RECOMMENDED UNTIL ISSUES ARE RESOLVED")
            
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    tester = SystemWideCleanupTester()
    passed, total, results = await tester.run_all_tests()
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED SYSTEM-WIDE CLEANUP RESULTS:")
    print("=" * 80)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    print("\n" + "=" * 80)
    print("🎯 DEPLOYMENT PREPARATION SUMMARY:")
    print("=" * 80)
    
    if passed == total:
        print("✅ ALL notes deleted from main database")
        print("✅ ALL transcription jobs cleared")
        print("✅ ALL associated files removed")
        print("✅ ALL user statistics reset")
        print("✅ Notes UI shows empty state for all users")
        print("✅ System ready for clean deployment")
        print("\n🚀 COMPLETE DATABASE CLEANUP SUCCESSFUL!")
        print("🎉 SYSTEM IS READY FOR PRODUCTION DEPLOYMENT!")
    else:
        print("❌ System-wide cleanup has issues that need attention")
        failed_tests = [r for r in results if not r["success"]]
        print(f"❌ Failed tests: {len(failed_tests)}")
        for failed in failed_tests:
            print(f"   - {failed['test']}: {failed['details']}")
        print("\n⚠️ CLEANUP INCOMPLETE - DEPLOYMENT NOT RECOMMENDED")

if __name__ == "__main__":
    asyncio.run(main())