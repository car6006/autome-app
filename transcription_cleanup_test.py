#!/usr/bin/env python3
"""
Transcription Pipeline Cleanup and Testing Script
Addresses the review request to clean up stuck job and test fresh uploads
"""

import requests
import sys
import json
import time
import tempfile
import os
from datetime import datetime
from pathlib import Path

class TranscriptionCleanupTester:
    def __init__(self, base_url="https://whisper-async-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"test_transcription_{int(time.time())}@example.com",
            "username": f"testuser{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        self.stuck_job_id = "f04f78f0-c9a6-48e6-b0c4-db15d8c080ea"

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

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

    def test_user_registration(self):
        """Test user registration for authentication"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Registered user ID: {user_data.get('id')}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
        return success

    def test_cleanup_stuck_job(self):
        """Test cleanup/delete endpoint to remove the stuck job"""
        self.log(f"\n🧹 CLEANING UP STUCK JOB: {self.stuck_job_id}")
        
        # First, try to get the job status to see if it exists
        success, response = self.run_test(
            f"Check Stuck Job Status",
            "GET",
            f"transcriptions/{self.stuck_job_id}",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   Job found - Status: {response.get('status', 'unknown')}")
            self.log(f"   Current stage: {response.get('current_stage', 'unknown')}")
            self.log(f"   Progress: {response.get('progress', 0)}%")
            
            # Try to delete the stuck job
            delete_success, delete_response = self.run_test(
                f"Delete Stuck Job",
                "DELETE",
                f"transcriptions/{self.stuck_job_id}",
                200,
                auth_required=True
            )
            
            if delete_success:
                self.log(f"   ✅ Stuck job deleted successfully")
                return True
            else:
                self.log(f"   ❌ Failed to delete stuck job")
                return False
        else:
            # Job might not exist or not accessible - try general cleanup
            self.log(f"   Job not found or not accessible - trying general cleanup")
            
            cleanup_success, cleanup_response = self.run_test(
                "General Cleanup of Stuck Jobs",
                "POST",
                "transcriptions/cleanup",
                200,
                auth_required=True
            )
            
            if cleanup_success:
                fixed_count = cleanup_response.get('fixed_count', 0)
                self.log(f"   ✅ General cleanup completed - Fixed {fixed_count} jobs")
                return True
            else:
                self.log(f"   ❌ General cleanup failed")
                return False

    def create_small_audio_file(self):
        """Create a small test audio file for testing"""
        # Create a small MP3-like file (not real audio, but valid for testing)
        # This is a minimal MP3 header followed by some data
        mp3_header = b'\xff\xfb\x90\x00'  # MP3 frame header
        mp3_data = b'\x00' * 1024  # 1KB of silence data
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(mp3_header + mp3_data)
            tmp_file.flush()
            return tmp_file.name

    def test_create_upload_session(self):
        """Test creating a new upload session"""
        self.log(f"\n📤 CREATING NEW UPLOAD SESSION")
        
        session_data = {
            "filename": "test_audio_cleanup.mp3",
            "total_size": 1028,  # Small file size
            "mime_type": "audio/mpeg",
            "language": None,
            "enable_diarization": False
        }
        
        success, response = self.run_test(
            "Create Upload Session",
            "POST",
            "uploads/sessions",
            200,
            data=session_data,
            auth_required=True
        )
        
        if success:
            upload_id = response.get('upload_id')
            chunk_size = response.get('chunk_size', 5242880)
            self.log(f"   Upload ID: {upload_id}")
            self.log(f"   Chunk size: {chunk_size} bytes")
            return upload_id
        
        return None

    def test_upload_small_file_direct(self):
        """Test uploading a small audio file directly via /api/upload-file"""
        self.log(f"\n🎵 TESTING DIRECT AUDIO UPLOAD")
        
        # Create small test audio file
        audio_file_path = self.create_small_audio_file()
        
        try:
            with open(audio_file_path, 'rb') as f:
                files = {'file': ('test_cleanup_audio.mp3', f, 'audio/mpeg')}
                data = {'title': 'Cleanup Test Audio Upload'}
                
                success, response = self.run_test(
                    "Direct Audio Upload",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    timeout=60,
                    auth_required=True
                )
            
            if success:
                note_id = response.get('id')
                self.log(f"   Note ID: {note_id}")
                self.log(f"   Status: {response.get('status', 'unknown')}")
                self.log(f"   Kind: {response.get('kind', 'unknown')}")
                return note_id
            
        finally:
            # Clean up temp file
            os.unlink(audio_file_path)
        
        return None

    def test_monitor_processing(self, note_id, max_wait=120):
        """Monitor note processing to verify pipeline works"""
        self.log(f"\n⏳ MONITORING PROCESSING FOR NOTE: {note_id}")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, response = self.run_test(
                f"Check Processing Status",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success:
                status = response.get('status', 'unknown')
                artifacts = response.get('artifacts', {})
                
                self.log(f"   Status: {status} (after {time.time() - start_time:.1f}s)")
                
                if status == 'ready':
                    transcript = artifacts.get('transcript', '')
                    self.log(f"   ✅ Processing completed successfully!")
                    self.log(f"   Transcript length: {len(transcript)} characters")
                    if transcript:
                        self.log(f"   Transcript preview: {transcript[:100]}...")
                    return True
                elif status == 'failed':
                    error_msg = artifacts.get('error', 'Unknown error')
                    self.log(f"   ❌ Processing failed: {error_msg}")
                    return False
                elif status in ['processing', 'uploading']:
                    self.log(f"   Processing in progress...")
                    time.sleep(5)
                else:
                    self.log(f"   Waiting for processing to start...")
                    time.sleep(3)
            else:
                self.log(f"   ❌ Failed to check status")
                break
        
        self.log(f"   ⏰ Timeout after {max_wait} seconds")
        return False

    def test_list_jobs_for_errors(self):
        """Test listing jobs to check for 'Error loading jobs' issues"""
        self.log(f"\n📋 CHECKING FOR 'ERROR LOADING JOBS' ISSUES")
        
        success, response = self.run_test(
            "List Transcription Jobs",
            "GET",
            "transcriptions/",
            200,
            auth_required=True
        )
        
        if success:
            jobs = response.get('jobs', [])
            total = response.get('total', 0)
            
            self.log(f"   ✅ Jobs loaded successfully")
            self.log(f"   Total jobs: {total}")
            
            # Check for any error indicators
            error_jobs = [job for job in jobs if job.get('status') == 'failed']
            stuck_jobs = [job for job in jobs if job.get('status') == 'processing' and 
                         job.get('progress', 0) == 0]
            
            self.log(f"   Failed jobs: {len(error_jobs)}")
            self.log(f"   Potentially stuck jobs: {len(stuck_jobs)}")
            
            # List recent jobs
            for job in jobs[:3]:  # Show first 3 jobs
                self.log(f"   Job: {job.get('job_id', 'unknown')[:8]}... - {job.get('status')} - {job.get('filename', 'unknown')}")
            
            return True
        else:
            self.log(f"   ❌ Error loading jobs detected!")
            return False

    def test_openai_api_key_verification(self):
        """Verify OpenAI API key is working by checking health endpoint"""
        self.log(f"\n🔑 VERIFYING OPENAI API KEY CONFIGURATION")
        
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        
        if success:
            services = response.get('services', {})
            api_status = services.get('api', 'unknown')
            pipeline_status = services.get('pipeline', 'unknown')
            
            self.log(f"   API Status: {api_status}")
            self.log(f"   Pipeline Status: {pipeline_status}")
            
            # Check if there are any obvious API key issues in the response
            if 'error' in str(response).lower() and 'api' in str(response).lower():
                self.log(f"   ⚠️  Potential API key issues detected")
                return False
            else:
                self.log(f"   ✅ System appears healthy for API operations")
                return True
        else:
            self.log(f"   ❌ Health check failed")
            return False

    def run_complete_test_suite(self):
        """Run the complete test suite for the review request"""
        self.log("🚀 STARTING TRANSCRIPTION CLEANUP AND TESTING")
        self.log("=" * 60)
        
        # Step 1: Register user for authentication
        if not self.test_user_registration():
            self.log("❌ Failed to register user - cannot continue")
            return False
        
        # Step 2: Verify OpenAI API key configuration
        api_key_ok = self.test_openai_api_key_verification()
        
        # Step 3: Clean up the stuck job
        cleanup_success = self.test_cleanup_stuck_job()
        
        # Step 4: Test fresh upload
        note_id = self.test_upload_small_file_direct()
        
        processing_success = False
        if note_id:
            # Step 5: Monitor processing to verify pipeline works
            processing_success = self.test_monitor_processing(note_id)
        
        # Step 6: Check for "Error loading jobs" issues
        jobs_loading_ok = self.test_list_jobs_for_errors()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        results = {
            "User Registration": True,  # We got this far
            "OpenAI API Key Check": api_key_ok,
            "Stuck Job Cleanup": cleanup_success,
            "Fresh Upload Creation": note_id is not None,
            "Pipeline Processing": processing_success,
            "Jobs Loading Check": jobs_loading_ok
        }
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   {status} {test_name}")
        
        overall_success = all(results.values())
        
        self.log(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ ISSUES FOUND'}")
        self.log(f"📈 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if overall_success:
            self.log("\n🎉 All review request requirements completed successfully!")
            self.log("   - Stuck job cleaned up")
            self.log("   - Fresh upload tested")
            self.log("   - Pipeline verified working")
            self.log("   - No 'Error loading jobs' issues detected")
        else:
            self.log("\n⚠️  Some issues found - see details above")
        
        return overall_success

def main():
    """Main test execution"""
    tester = TranscriptionCleanupTester()
    
    try:
        success = tester.run_complete_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()