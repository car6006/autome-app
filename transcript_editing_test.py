#!/usr/bin/env python3
"""
Focused Test Suite for Transcript Editing Save Functionality
Tests the newly added PUT /api/notes/{note_id} endpoint
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://transcript-master.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123"
TEST_USER_NAME = "Test User"
TEST_USERNAME = "testuser123"

class TranscriptEditingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def setup_authentication(self):
        """Set up authentication for testing"""
        try:
            # Generate unique email and username for this test
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"transcript_test_{unique_id}@example.com"
            unique_username = f"transcripttest{unique_id}"
            
            user_data = {
                "email": unique_email,
                "username": unique_username,
                "password": TEST_USER_PASSWORD,
                "first_name": "Transcript",
                "last_name": "Tester"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("user"):
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    self.registered_email = unique_email
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print(f"✅ Authentication setup successful - User ID: {self.user_id}")
                    return True
                else:
                    print("❌ Authentication setup failed - Missing token or user data")
                    return False
            else:
                print(f"❌ Authentication setup failed - HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication setup error: {str(e)}")
            return False

    def test_transcript_editing_save_functionality(self):
        """Test the new transcript editing save functionality - PUT /api/notes/{note_id} endpoint"""
        try:
            # First, create a note with some initial content
            note_data = {
                "title": f"Transcript Edit Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "kind": "text",
                "text_content": "This is the original transcript content that will be edited."
            }
            
            create_response = self.session.post(
                f"{BACKEND_URL}/notes",
                json=note_data,
                timeout=10
            )
            
            if create_response.status_code != 200:
                self.log_result("Transcript Editing Save Functionality", False, f"Failed to create test note: HTTP {create_response.status_code}")
                return
                
            created_note = create_response.json()
            test_note_id = created_note.get("id")
            
            if not test_note_id:
                self.log_result("Transcript Editing Save Functionality", False, "No note ID returned from creation")
                return
            
            # Test 1: Valid transcript update with proper artifacts
            edited_transcript = "This is the EDITED transcript content with important changes and new information."
            update_data = {
                "artifacts": {
                    "transcript": edited_transcript,
                    "text": edited_transcript,
                    "last_edited": datetime.now().isoformat(),
                    "edit_count": 1
                }
            }
            
            update_response = self.session.put(
                f"{BACKEND_URL}/notes/{test_note_id}",
                json=update_data,
                timeout=10
            )
            
            if update_response.status_code == 200:
                # Verify the update was saved by retrieving the note
                get_response = self.session.get(f"{BACKEND_URL}/notes/{test_note_id}", timeout=10)
                
                if get_response.status_code == 200:
                    updated_note = get_response.json()
                    artifacts = updated_note.get("artifacts", {})
                    saved_transcript = artifacts.get("transcript", "")
                    
                    if saved_transcript == edited_transcript:
                        self.log_result("Transcript Editing Save Functionality", True, 
                                      "✅ Transcript editing save working - artifacts updated successfully", 
                                      {"note_id": test_note_id, "transcript_length": len(saved_transcript)})
                    else:
                        self.log_result("Transcript Editing Save Functionality", False, 
                                      f"Transcript not saved correctly. Expected: '{edited_transcript[:50]}...', Got: '{saved_transcript[:50]}...'")
                else:
                    self.log_result("Transcript Editing Save Functionality", False, 
                                  f"Could not retrieve updated note: HTTP {get_response.status_code}")
            else:
                self.log_result("Transcript Editing Save Functionality", False, 
                              f"PUT request failed: HTTP {update_response.status_code}: {update_response.text}")
                
        except Exception as e:
            self.log_result("Transcript Editing Save Functionality", False, f"Transcript editing test error: {str(e)}")

    def test_transcript_editing_user_ownership_validation(self):
        """Test that transcript editing validates user ownership and rejects unauthorized updates"""
        try:
            # Create a second user to test unauthorized access
            unique_id = uuid.uuid4().hex[:8]
            second_user_data = {
                "email": f"seconduser_{unique_id}@example.com",
                "username": f"seconduser{unique_id}",
                "password": TEST_USER_PASSWORD,
                "first_name": "Second",
                "last_name": "User"
            }
            
            # Register second user
            register_response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=second_user_data,
                timeout=10
            )
            
            if register_response.status_code != 200:
                self.log_result("Transcript Editing User Ownership", False, "Could not create second user for ownership test")
                return
                
            second_user_token = register_response.json().get("access_token")
            
            # Create a note with the first user (current authenticated user)
            note_data = {
                "title": f"Ownership Test Note {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "kind": "text", 
                "text_content": "This note belongs to the first user."
            }
            
            create_response = self.session.post(
                f"{BACKEND_URL}/notes",
                json=note_data,
                timeout=10
            )
            
            if create_response.status_code != 200:
                self.log_result("Transcript Editing User Ownership", False, "Could not create test note")
                return
                
            test_note_id = create_response.json().get("id")
            
            # Now try to update the note with the second user's token
            original_auth = self.session.headers.get("Authorization")
            self.session.headers["Authorization"] = f"Bearer {second_user_token}"
            
            unauthorized_update = {
                "artifacts": {
                    "transcript": "This is an UNAUTHORIZED edit attempt!",
                    "text": "This should not be allowed!"
                }
            }
            
            unauthorized_response = self.session.put(
                f"{BACKEND_URL}/notes/{test_note_id}",
                json=unauthorized_update,
                timeout=10
            )
            
            # Restore original auth
            self.session.headers["Authorization"] = original_auth
            
            # Should get 403 Forbidden
            if unauthorized_response.status_code == 403:
                self.log_result("Transcript Editing User Ownership", True, 
                              "✅ User ownership validation working - unauthorized update rejected with HTTP 403")
            elif unauthorized_response.status_code == 404:
                self.log_result("Transcript Editing User Ownership", True, 
                              "✅ User ownership validation working - note not found for unauthorized user (HTTP 404)")
            else:
                self.log_result("Transcript Editing User Ownership", False, 
                              f"Expected HTTP 403 or 404, got HTTP {unauthorized_response.status_code}")
                
        except Exception as e:
            self.log_result("Transcript Editing User Ownership", False, f"User ownership validation test error: {str(e)}")

    def test_transcript_editing_error_handling(self):
        """Test error handling for invalid note IDs, missing notes, and malformed requests"""
        try:
            # Test 1: Invalid/non-existent note ID
            fake_note_id = "nonexistent-note-id-12345"
            update_data = {
                "artifacts": {
                    "transcript": "This should fail because note doesn't exist"
                }
            }
            
            invalid_id_response = self.session.put(
                f"{BACKEND_URL}/notes/{fake_note_id}",
                json=update_data,
                timeout=10
            )
            
            if invalid_id_response.status_code == 404:
                self.log_result("Transcript Editing Error Handling - Invalid ID", True, 
                              "✅ Invalid note ID properly returns HTTP 404")
            else:
                self.log_result("Transcript Editing Error Handling - Invalid ID", False, 
                              f"Expected HTTP 404 for invalid note ID, got HTTP {invalid_id_response.status_code}")
            
            # Test 2: Empty update data
            empty_response = self.session.put(
                f"{BACKEND_URL}/notes/{fake_note_id}",
                json={},
                timeout=10
            )
            
            # Should still return 404 for non-existent note, even with empty data
            if empty_response.status_code == 404:
                self.log_result("Transcript Editing Error Handling - Empty Data", True, 
                              "✅ Empty update data handled correctly (HTTP 404 for non-existent note)")
            else:
                self.log_result("Transcript Editing Error Handling - Empty Data", False, 
                              f"Unexpected response to empty data: HTTP {empty_response.status_code}")
                
        except Exception as e:
            self.log_result("Transcript Editing Error Handling", False, f"Error handling test error: {str(e)}")

    def test_transcript_editing_database_persistence(self):
        """Test that artifacts are properly saved to database via NotesStore.set_artifacts()"""
        try:
            # Create a note for testing database persistence
            note_data = {
                "title": f"DB Persistence Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "kind": "text",
                "text_content": "Original content for database persistence test."
            }
            
            create_response = self.session.post(
                f"{BACKEND_URL}/notes",
                json=note_data,
                timeout=10
            )
            
            if create_response.status_code != 200:
                self.log_result("Transcript Editing Database Persistence", False, "Could not create test note")
                return
                
            test_note_id = create_response.json().get("id")
            
            # Perform multiple updates to test database persistence
            updates = [
                {
                    "artifacts": {
                        "transcript": "First edit - testing database persistence",
                        "text": "First edit - testing database persistence",
                        "edit_number": 1,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                {
                    "artifacts": {
                        "transcript": "Second edit - verifying data persists across updates",
                        "text": "Second edit - verifying data persists across updates", 
                        "edit_number": 2,
                        "timestamp": datetime.now().isoformat(),
                        "additional_field": "Testing complex artifact structure"
                    }
                }
            ]
            
            for i, update_data in enumerate(updates, 1):
                # Apply update
                update_response = self.session.put(
                    f"{BACKEND_URL}/notes/{test_note_id}",
                    json=update_data,
                    timeout=10
                )
                
                if update_response.status_code != 200:
                    self.log_result("Transcript Editing Database Persistence", False, 
                                  f"Update {i} failed: HTTP {update_response.status_code}")
                    return
                
                # Wait a moment for database write
                time.sleep(0.5)
                
                # Verify persistence by retrieving the note
                get_response = self.session.get(f"{BACKEND_URL}/notes/{test_note_id}", timeout=10)
                
                if get_response.status_code != 200:
                    self.log_result("Transcript Editing Database Persistence", False, 
                                  f"Could not retrieve note after update {i}")
                    return
                
                retrieved_note = get_response.json()
                artifacts = retrieved_note.get("artifacts", {})
                expected_transcript = update_data["artifacts"]["transcript"]
                actual_transcript = artifacts.get("transcript", "")
                
                if actual_transcript != expected_transcript:
                    self.log_result("Transcript Editing Database Persistence", False, 
                                  f"Update {i} not persisted correctly. Expected: '{expected_transcript}', Got: '{actual_transcript}'")
                    return
            
            # Final verification - check that all fields from the last update are present
            final_artifacts = retrieved_note.get("artifacts", {})
            expected_fields = ["transcript", "text", "edit_number", "timestamp", "additional_field"]
            missing_fields = [field for field in expected_fields if field not in final_artifacts]
            
            if not missing_fields:
                self.log_result("Transcript Editing Database Persistence", True, 
                              "✅ Database persistence working - all updates saved correctly with complex artifact structure", 
                              {"final_edit_number": final_artifacts.get("edit_number"), 
                               "artifact_fields": list(final_artifacts.keys())})
            else:
                self.log_result("Transcript Editing Database Persistence", False, 
                              f"Missing artifact fields after persistence: {missing_fields}")
                
        except Exception as e:
            self.log_result("Transcript Editing Database Persistence", False, f"Database persistence test error: {str(e)}")

    def test_transcript_editing_response_format(self):
        """Test that the PUT endpoint returns appropriate HTTP status codes and response messages"""
        try:
            # Create a test note
            note_data = {
                "title": f"Response Format Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "kind": "text",
                "text_content": "Testing response format for transcript editing."
            }
            
            create_response = self.session.post(
                f"{BACKEND_URL}/notes",
                json=note_data,
                timeout=10
            )
            
            if create_response.status_code != 200:
                self.log_result("Transcript Editing Response Format", False, "Could not create test note")
                return
                
            test_note_id = create_response.json().get("id")
            
            # Test successful update response format
            update_data = {
                "artifacts": {
                    "transcript": "Testing response format for successful update",
                    "text": "Testing response format for successful update"
                }
            }
            
            success_response = self.session.put(
                f"{BACKEND_URL}/notes/{test_note_id}",
                json=update_data,
                timeout=10
            )
            
            # Check status code
            if success_response.status_code == 200:
                # Check response format
                try:
                    response_data = success_response.json()
                    if isinstance(response_data, dict) and "message" in response_data:
                        success_message = response_data.get("message", "")
                        if "updated successfully" in success_message.lower() or "success" in success_message.lower():
                            self.log_result("Transcript Editing Response Format", True, 
                                          "✅ Success response format correct - HTTP 200 with success message", 
                                          {"status_code": 200, "message": success_message})
                        else:
                            self.log_result("Transcript Editing Response Format", False, 
                                          f"Success message format unexpected: '{success_message}'")
                    else:
                        self.log_result("Transcript Editing Response Format", False, 
                                      f"Success response format unexpected: {response_data}")
                except:
                    self.log_result("Transcript Editing Response Format", False, 
                                  "Success response is not valid JSON")
            else:
                self.log_result("Transcript Editing Response Format", False, 
                              f"Expected HTTP 200 for successful update, got HTTP {success_response.status_code}")
                
        except Exception as e:
            self.log_result("Transcript Editing Response Format", False, f"Response format test error: {str(e)}")

    def run_all_tests(self):
        """Run all transcript editing tests"""
        print("🚀 Starting Transcript Editing Save Functionality Test Suite")
        print(f"🎯 Target URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot proceed with tests")
            return 0, 1
        
        print("\n" + "=" * 80)
        print("✏️ TRANSCRIPT EDITING SAVE FUNCTIONALITY TESTS - PUT /api/notes/{note_id} Endpoint")
        print("=" * 80)
        
        # Run all transcript editing tests
        self.test_transcript_editing_save_functionality()
        self.test_transcript_editing_user_ownership_validation()
        self.test_transcript_editing_error_handling()
        self.test_transcript_editing_database_persistence()
        self.test_transcript_editing_response_format()
        
        # Print summary
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TRANSCRIPT EDITING TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        return passed, failed

if __name__ == "__main__":
    tester = TranscriptEditingTester()
    passed, failed = tester.run_all_tests()
    
    if failed == 0:
        print("🎉 All transcript editing tests passed!")
        exit(0)
    else:
        print(f"⚠️  {failed} test(s) failed")
        exit(1)