#!/usr/bin/env python3
"""
Transfer-to-Notes Functionality Test
Tests the specific review request functionality
"""

import requests
import sys
import json
import time
from datetime import datetime

class TransferToNotesTest:
    def __init__(self, base_url="https://voice-capture-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"transfer_test_{int(time.time())}@example.com",
            "username": f"transfertest{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Transfer",
            "last_name": "Test"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def setup_authentication(self):
        """Setup authentication for testing"""
        self.log("🔐 Setting up authentication...")
        
        # Register test user
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   Registered user: {self.test_user_data['email']}")
            return True
        else:
            self.log("❌ Failed to register user")
            return False

    def test_transcription_jobs_list(self):
        """Test listing transcription jobs"""
        self.log("📋 Testing transcription jobs listing...")
        
        success, response = self.run_test(
            "List Transcription Jobs",
            "GET",
            "transcriptions/",
            200,
            auth_required=True
        )
        
        if success:
            jobs = response.get('jobs', [])
            self.log(f"   Found {len(jobs)} transcription jobs")
            
            # Look for the specific job mentioned in the review request
            target_job = None
            for job in jobs:
                if "Regional Meeting 20 August 2025" in job.get('filename', ''):
                    target_job = job
                    break
            
            if target_job:
                self.log(f"✅ Found target job: {target_job['job_id']}")
                self.log(f"   Status: {target_job.get('status', 'unknown')}")
                self.log(f"   Filename: {target_job.get('filename', 'unknown')}")
                return target_job
            else:
                self.log("⚠️  Target job 'Regional Meeting 20 August 2025.mp3' not found")
                return None
        else:
            self.log("❌ Failed to list transcription jobs")
            return None

    def test_transfer_to_notes_endpoint(self, job_id=None):
        """Test the transfer-to-notes endpoint"""
        self.log("🔄 Testing transfer-to-notes endpoint...")
        
        if not job_id:
            # Test with non-existent job ID
            job_id = "non-existent-job-id"
            expected_status = 404
            test_name = "Transfer Non-existent Job (Should Fail)"
        else:
            expected_status = 200  # or 400 if job is not complete
            test_name = f"Transfer Job {job_id[:8]}... to Notes"
        
        success, response = self.run_test(
            test_name,
            "POST",
            f"transcriptions/{job_id}/transfer-to-notes",
            expected_status,
            auth_required=True
        )
        
        if success:
            if expected_status == 200:
                self.log("✅ Transfer to notes successful!")
                self.log(f"   Message: {response.get('message', 'N/A')}")
                note_id = response.get('note_id')
                if note_id:
                    self.log(f"   Note ID: {note_id}")
                    return note_id
            elif expected_status == 404:
                self.log("✅ Correctly handled non-existent job")
            elif expected_status == 400:
                self.log("✅ Correctly rejected incomplete job")
                self.log(f"   Error: {response.get('detail', 'N/A')}")
        else:
            self.log("❌ Transfer endpoint test failed")
        
        return None

    def test_note_verification(self, note_id):
        """Verify the transferred note"""
        self.log(f"🔍 Verifying transferred note {note_id[:8]}...")
        
        success, response = self.run_test(
            f"Get Transferred Note {note_id[:8]}...",
            "GET",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        
        if success:
            self.log("✅ Note retrieved successfully")
            self.log(f"   Status: {response.get('status', 'unknown')}")
            self.log(f"   Kind: {response.get('kind', 'unknown')}")
            
            artifacts = response.get('artifacts', {})
            if artifacts.get('transcript'):
                self.log("✅ Transcript content found in note")
                transcript_length = len(artifacts['transcript'])
                self.log(f"   Transcript length: {transcript_length} characters")
                
                # Check if status is "ready"
                if response.get('status') == 'ready':
                    self.log("✅ Note status is 'ready' - transfer successful")
                    return True
                else:
                    self.log(f"⚠️  Note status is '{response.get('status')}', expected 'ready'")
                    return False
            else:
                self.log("❌ No transcript content found in transferred note")
                return False
        else:
            self.log("❌ Failed to retrieve transferred note")
            return False

    def test_ai_features_on_note(self, note_id):
        """Test AI features on the transferred note"""
        self.log(f"🤖 Testing AI features on note {note_id[:8]}...")
        
        success, response = self.run_test(
            "AI Chat on Transferred Note",
            "POST",
            f"notes/{note_id}/ai-chat",
            200,
            data={"question": "Provide a summary of this meeting transcript"},
            auth_required=True,
            timeout=60
        )
        
        if success:
            self.log("✅ AI features working on transferred note")
            ai_response_text = response.get('response', '')
            self.log(f"   AI response length: {len(ai_response_text)} characters")
            return True
        else:
            self.log("❌ AI features not working on transferred note")
            return False

    def test_cleanup_functionality(self):
        """Test cleanup functionality"""
        self.log("🧹 Testing cleanup functionality...")
        
        success, response = self.run_test(
            "Cleanup Stuck Jobs",
            "POST",
            "transcriptions/cleanup",
            200,
            auth_required=True
        )
        
        if success:
            self.log("✅ Cleanup functionality working")
            self.log(f"   Message: {response.get('message', 'N/A')}")
            fixed_count = response.get('fixed_count', 0)
            self.log(f"   Fixed jobs: {fixed_count}")
            return True
        else:
            self.log("⚠️  Cleanup functionality not available or failed")
            return False

    def run_all_tests(self):
        """Run all transfer-to-notes tests"""
        self.log("🚀 Starting Transfer-to-Notes Functionality Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup authentication
        if not self.setup_authentication():
            return False
        
        # Test 1: List transcription jobs and find target
        target_job = self.test_transcription_jobs_list()
        
        # Test 2: Test transfer-to-notes endpoint
        if target_job:
            job_id = target_job['job_id']
            
            # Get detailed job status first
            success, job_details = self.run_test(
                f"Get Job Details {job_id[:8]}...",
                "GET",
                f"transcriptions/{job_id}",
                200,
                auth_required=True
            )
            
            if success:
                self.log(f"   Current stage: {job_details.get('current_stage', 'unknown')}")
                self.log(f"   Progress: {job_details.get('progress', 0)}%")
                self.log(f"   Error: {job_details.get('error_message', 'None')}")
                
                # Test transfer based on job status
                if job_details.get('status') == 'complete':
                    note_id = self.test_transfer_to_notes_endpoint(job_id)
                    if note_id:
                        # Test 3: Verify the transferred note
                        if self.test_note_verification(note_id):
                            # Test 4: Test AI features on the note
                            self.test_ai_features_on_note(note_id)
                elif job_details.get('status') == 'failed':
                    # Test with failed job (should return 400)
                    self.test_transfer_to_notes_endpoint(job_id)
                else:
                    self.log(f"⚠️  Job status is '{job_details.get('status')}' - not testable")
        else:
            # Test with non-existent job
            self.test_transfer_to_notes_endpoint()
        
        # Test 5: Test cleanup functionality
        self.test_cleanup_functionality()
        
        # Print results
        self.log("\n" + "="*60)
        self.log("📊 TRANSFER-TO-NOTES TEST RESULTS")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 ALL TRANSFER-TO-NOTES TESTS PASSED!")
            return True
        else:
            self.log("⚠️  Some tests failed - check details above")
            return False

def main():
    """Main test execution"""
    tester = TransferToNotesTest()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 Transfer-to-notes functionality is working correctly!")
            return 0
        else:
            print(f"\n⚠️  Some issues found with transfer-to-notes functionality.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())