#!/usr/bin/env python3
"""
Critical Notes Loading Test - Testing the fix for missing created_at timestamps
Testing the specific issue where user car6006@gmail.com was seeing "Failed to load notes" error
"""

import asyncio
import httpx
import json
import os
import time
from datetime import datetime, timezone

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://pwa-integration-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class NotesLoadingTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.auth_token = None
        self.test_user_email = "car6006@gmail.com"  # The specific user mentioned in review
        self.test_user_password = "TestPassword123!"
        
    async def cleanup(self):
        """Clean up HTTP client"""
        await self.client.aclose()
    
    async def authenticate_user(self):
        """Authenticate as the specific user mentioned in the review"""
        try:
            # Try to login as the existing user
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            print(f"🔐 Attempting to login as user: {self.test_user_email}")
            response = await self.client.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                user_info = data.get("user", {})
                print(f"✅ Successfully authenticated as: {user_info.get('email', 'Unknown')}")
                return True
            elif response.status_code == 401:
                # User exists but wrong password, try to register
                print(f"⚠️  Login failed, attempting to register user...")
                register_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password,
                    "username": "car6006",
                    "name": "Test User Car6006"
                }
                
                register_response = await self.client.post(f"{API_BASE}/auth/register", json=register_data)
                
                if register_response.status_code in [200, 201]:
                    data = register_response.json()
                    self.auth_token = data.get("access_token")
                    print(f"✅ Successfully registered and authenticated user: {self.test_user_email}")
                    return True
                else:
                    print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def test_notes_endpoint_basic(self):
        """Test 1: Basic GET /api/notes endpoint functionality"""
        print("\n🧪 Test 1: Basic Notes Endpoint Access")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            print("   📡 Making GET request to /api/notes...")
            response = await self.client.get(f"{API_BASE}/notes", headers=headers)
            
            print(f"   📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                notes_data = response.json()
                print(f"   ✅ Notes endpoint accessible")
                print(f"   📝 Number of notes returned: {len(notes_data)}")
                
                # Check if response is a list
                if isinstance(notes_data, list):
                    print(f"   ✅ Response format is correct (list)")
                    return True, notes_data
                else:
                    print(f"   ❌ Response format incorrect - expected list, got {type(notes_data)}")
                    return False, None
            elif response.status_code == 401:
                print(f"   ❌ Authentication required - token may be invalid")
                return False, None
            elif response.status_code == 403:
                print(f"   ❌ Access forbidden - user may not have permission")
                return False, None
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Notes endpoint test error: {str(e)}")
            return False, None
    
    async def test_notes_pydantic_validation(self):
        """Test 2: Verify Pydantic validation passes for all notes"""
        print("\n🧪 Test 2: Pydantic Validation for All Notes")
        
        try:
            success, notes_data = await self.test_notes_endpoint_basic()
            if not success or not notes_data:
                print("   ❌ Cannot test Pydantic validation without notes data")
                return False
            
            print(f"   🔍 Validating {len(notes_data)} notes...")
            
            validation_errors = []
            valid_notes = 0
            
            for i, note in enumerate(notes_data):
                note_id = note.get("id", f"note_{i}")
                
                # Check required fields for Pydantic NoteResponse model
                required_fields = ["id", "title", "kind", "status", "created_at"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in note:
                        missing_fields.append(field)
                
                if missing_fields:
                    error_msg = f"Note {note_id}: Missing fields {missing_fields}"
                    validation_errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                else:
                    # Validate created_at field specifically (the main issue from review)
                    created_at = note.get("created_at")
                    if created_at:
                        try:
                            # Try to parse the datetime
                            if isinstance(created_at, str):
                                datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            print(f"   ✅ Note {note_id}: Valid created_at timestamp")
                            valid_notes += 1
                        except Exception as dt_error:
                            error_msg = f"Note {note_id}: Invalid created_at format: {created_at}"
                            validation_errors.append(error_msg)
                            print(f"   ❌ {error_msg}")
                    else:
                        error_msg = f"Note {note_id}: created_at is None or empty"
                        validation_errors.append(error_msg)
                        print(f"   ❌ {error_msg}")
            
            print(f"\n   📊 Validation Summary:")
            print(f"   ✅ Valid notes: {valid_notes}")
            print(f"   ❌ Invalid notes: {len(validation_errors)}")
            
            if len(validation_errors) == 0:
                print(f"   🎉 All notes pass Pydantic validation!")
                return True
            else:
                print(f"   ⚠️  Found {len(validation_errors)} validation issues:")
                for error in validation_errors[:5]:  # Show first 5 errors
                    print(f"      - {error}")
                if len(validation_errors) > 5:
                    print(f"      ... and {len(validation_errors) - 5} more")
                return False
                
        except Exception as e:
            print(f"❌ Pydantic validation test error: {str(e)}")
            return False
    
    async def test_specific_note_search(self):
        """Test 3: Search for Delta Service Provider Meeting note specifically"""
        print("\n🧪 Test 3: Search for Delta Service Provider Meeting Note")
        
        try:
            success, notes_data = await self.test_notes_endpoint_basic()
            if not success or not notes_data:
                print("   ❌ Cannot search for specific note without notes data")
                return False
            
            print(f"   🔍 Searching for 'Delta Service Provider Meeting' in {len(notes_data)} notes...")
            
            delta_notes = []
            for note in notes_data:
                title = note.get("title", "").lower()
                if "delta" in title and ("service" in title or "provider" in title or "meeting" in title):
                    delta_notes.append(note)
                    print(f"   ✅ Found matching note: '{note.get('title')}'")
                    print(f"      ID: {note.get('id')}")
                    print(f"      Status: {note.get('status')}")
                    print(f"      Created: {note.get('created_at')}")
            
            if len(delta_notes) > 0:
                print(f"   🎉 Found {len(delta_notes)} Delta Service Provider Meeting note(s)")
                
                # Verify the specific note has proper created_at
                for note in delta_notes:
                    created_at = note.get("created_at")
                    if created_at:
                        print(f"   ✅ Delta note has created_at timestamp: {created_at}")
                    else:
                        print(f"   ❌ Delta note missing created_at timestamp!")
                        return False
                
                return True
            else:
                print(f"   ⚠️  No Delta Service Provider Meeting notes found")
                print(f"   📝 Available note titles:")
                for note in notes_data[:10]:  # Show first 10 titles
                    print(f"      - {note.get('title', 'Untitled')}")
                return False
                
        except Exception as e:
            print(f"❌ Specific note search error: {str(e)}")
            return False
    
    async def test_notes_count_verification(self):
        """Test 4: Verify expected number of notes (6 notes mentioned in review)"""
        print("\n🧪 Test 4: Verify Expected Notes Count")
        
        try:
            success, notes_data = await self.test_notes_endpoint_basic()
            if not success or not notes_data:
                print("   ❌ Cannot verify count without notes data")
                return False
            
            notes_count = len(notes_data)
            expected_count = 6  # From review request
            
            print(f"   📊 Notes count: {notes_count}")
            print(f"   🎯 Expected count: {expected_count}")
            
            if notes_count == expected_count:
                print(f"   ✅ Exact match - found expected {expected_count} notes")
                return True
            elif notes_count > expected_count:
                print(f"   ✅ Found more notes than expected ({notes_count} > {expected_count})")
                print(f"      This is acceptable - user may have created additional notes")
                return True
            else:
                print(f"   ⚠️  Found fewer notes than expected ({notes_count} < {expected_count})")
                print(f"      This may indicate some notes are missing or not loading")
                return False
                
        except Exception as e:
            print(f"❌ Notes count verification error: {str(e)}")
            return False
    
    async def test_individual_note_access(self):
        """Test 5: Test individual note access to verify no loading issues"""
        print("\n🧪 Test 5: Individual Note Access Verification")
        
        try:
            success, notes_data = await self.test_notes_endpoint_basic()
            if not success or not notes_data:
                print("   ❌ Cannot test individual access without notes data")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            print(f"   🔍 Testing individual access for {len(notes_data)} notes...")
            
            successful_access = 0
            failed_access = 0
            
            for i, note in enumerate(notes_data[:5]):  # Test first 5 notes
                note_id = note.get("id")
                note_title = note.get("title", "Untitled")
                
                if not note_id:
                    print(f"   ❌ Note {i+1}: Missing ID")
                    failed_access += 1
                    continue
                
                try:
                    response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                    
                    if response.status_code == 200:
                        individual_note = response.json()
                        print(f"   ✅ Note {i+1}: '{note_title}' - Accessible")
                        
                        # Verify created_at in individual response
                        if individual_note.get("created_at"):
                            print(f"      ✅ Has created_at: {individual_note.get('created_at')}")
                        else:
                            print(f"      ❌ Missing created_at in individual response")
                        
                        successful_access += 1
                    else:
                        print(f"   ❌ Note {i+1}: '{note_title}' - Access failed ({response.status_code})")
                        failed_access += 1
                        
                except Exception as note_error:
                    print(f"   ❌ Note {i+1}: '{note_title}' - Error: {str(note_error)}")
                    failed_access += 1
            
            print(f"\n   📊 Individual Access Summary:")
            print(f"   ✅ Successful: {successful_access}")
            print(f"   ❌ Failed: {failed_access}")
            
            if failed_access == 0:
                print(f"   🎉 All individual notes accessible!")
                return True
            elif successful_access > failed_access:
                print(f"   ✅ Majority of notes accessible")
                return True
            else:
                print(f"   ❌ Significant issues with individual note access")
                return False
                
        except Exception as e:
            print(f"❌ Individual note access test error: {str(e)}")
            return False
    
    async def run_critical_notes_tests(self):
        """Run all critical notes loading tests"""
        print("🚨 CRITICAL NOTES LOADING TEST SUITE")
        print("Testing fix for missing created_at timestamps causing 'Failed to load notes' error")
        print("=" * 80)
        
        # Authenticate user
        if not await self.authenticate_user():
            print("❌ Cannot proceed without user authentication")
            return False
        
        test_results = []
        
        # Test 1: Basic notes endpoint access
        basic_success, _ = await self.test_notes_endpoint_basic()
        test_results.append(("Basic Notes Endpoint Access", basic_success))
        
        # Test 2: Pydantic validation for all notes
        validation_success = await self.test_notes_pydantic_validation()
        test_results.append(("Pydantic Validation (created_at fix)", validation_success))
        
        # Test 3: Search for Delta Service Provider Meeting note
        delta_search_success = await self.test_specific_note_search()
        test_results.append(("Delta Service Provider Meeting Note", delta_search_success))
        
        # Test 4: Verify expected notes count
        count_success = await self.test_notes_count_verification()
        test_results.append(("Expected Notes Count (6 notes)", count_success))
        
        # Test 5: Individual note access
        individual_success = await self.test_individual_note_access()
        test_results.append(("Individual Note Access", individual_success))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 CRITICAL NOTES LOADING TEST RESULTS")
        print("=" * 80)
        
        passed = 0
        total = len(test_results)
        critical_tests = ["Basic Notes Endpoint Access", "Pydantic Validation (created_at fix)"]
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            critical_marker = " [CRITICAL]" if test_name in critical_tests else ""
            print(f"{status} {test_name}{critical_marker}")
            if success:
                passed += 1
        
        print(f"\n📈 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Check critical tests specifically
        critical_passed = sum(1 for name, success in test_results if name in critical_tests and success)
        critical_total = len(critical_tests)
        
        print(f"🚨 Critical Tests: {critical_passed}/{critical_total} passed")
        
        if critical_passed == critical_total:
            print("🎉 CRITICAL ISSUE RESOLVED - Notes loading fix working correctly!")
            print("✅ User car6006@gmail.com should no longer see 'Failed to load notes' error")
            return True
        else:
            print("❌ CRITICAL ISSUE PERSISTS - Notes loading still has problems")
            print("⚠️  User may still experience 'Failed to load notes' error")
            return False

async def main():
    """Main test execution"""
    tester = NotesLoadingTester()
    
    try:
        success = await tester.run_critical_notes_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)