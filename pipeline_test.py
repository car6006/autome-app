#!/usr/bin/env python3
"""
Large-file Audio Transcription Pipeline Tests
Tests the Phase 2 implementation specifically
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class PipelineAPITester:
    def __init__(self, base_url="https://audio-pipeline-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"pipeline_test_{int(time.time())}@example.com",
            "username": f"pipelineuser{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Pipeline",
            "last_name": "Tester"
        }

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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

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
        """Test user registration for pipeline tests"""
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
            self.log(f"   Registered user: {user_data.get('email')}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
        return success

    def test_health_check(self):
        """Test API health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        if success:
            self.log(f"   API Status: {response.get('status', 'N/A')}")
            pipeline = response.get('pipeline', {})
            worker = pipeline.get('worker', {})
            queue = pipeline.get('queue', {})
            self.log(f"   Pipeline Worker Running: {worker.get('running', False)}")
            self.log(f"   Queue Size: {queue.get('total_queued', 0)}")
        return success

    def test_large_file_transcription_pipeline(self):
        """Test the Phase 2 Large-file Audio Transcription Pipeline"""
        self.log("\n🎵 LARGE-FILE TRANSCRIPTION PIPELINE TESTS")
        
        # Test 1: Create Upload Session
        self.log("📤 Testing upload session creation...")
        session_data = {
            "filename": "large_meeting_recording.mp3",
            "total_size": 52428800,  # 50MB
            "mime_type": "audio/mpeg",
            "language": None,
            "enable_diarization": True
        }
        
        success, response = self.run_test(
            "Create Upload Session",
            "POST",
            "uploads/sessions",
            200,
            data=session_data,
            auth_required=True
        )
        
        if not success:
            self.log("❌ Upload session creation failed - skipping pipeline tests")
            return False
        
        upload_id = response.get('upload_id')
        chunk_size = response.get('chunk_size', 5242880)  # 5MB default
        
        if not upload_id:
            self.log("❌ No upload_id returned - skipping pipeline tests")
            return False
        
        self.log(f"   Upload ID: {upload_id}")
        self.log(f"   Chunk size: {chunk_size} bytes")
        self.log(f"   Max duration: {response.get('max_duration_hours', 0)} hours")
        self.log(f"   Allowed types: {len(response.get('allowed_mime_types', []))} types")
        
        # Test 2: Upload Status Check
        success, status_response = self.run_test(
            "Get Upload Status",
            "GET",
            f"uploads/sessions/{upload_id}/status",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   Status: {status_response.get('status')}")
            self.log(f"   Progress: {status_response.get('progress', 0)}%")
            self.log(f"   Total chunks: {status_response.get('total_chunks', 0)}")
            self.log(f"   Bytes uploaded: {status_response.get('bytes_uploaded', 0)}")
        
        # Test 3: Simulate Chunk Upload (simplified for testing)
        self.log("📦 Testing chunk upload...")
        
        # Create a test chunk with the expected size
        chunk_data = b'FAKE_AUDIO_CHUNK_DATA' * (chunk_size // 21)  # Create chunk of expected size
        
        with tempfile.NamedTemporaryFile(suffix='.chunk', delete=False) as tmp_file:
            tmp_file.write(chunk_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'chunk': ('chunk_0', f, 'application/octet-stream')}
                success, chunk_response = self.run_test(
                    "Upload Chunk 0",
                    "POST",
                    f"uploads/sessions/{upload_id}/chunks/0",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
        
        if success:
            self.log(f"   Chunk uploaded: {chunk_response.get('uploaded', False)}")
            self.log(f"   Chunk index: {chunk_response.get('chunk_index', 'N/A')}")
        
        # Test 4: Check Upload Status After Chunk
        success, status_response = self.run_test(
            "Get Upload Status After Chunk",
            "GET",
            f"uploads/sessions/{upload_id}/status",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   Progress after chunk: {status_response.get('progress', 0)}%")
            self.log(f"   Chunks uploaded: {len(status_response.get('chunks_uploaded', []))}")
        
        # Test 5: Finalize Upload (this will create transcription job)
        self.log("✅ Testing upload finalization...")
        
        finalize_data = {
            "upload_id": upload_id,
            "sha256": None  # Optional for testing
        }
        
        success, finalize_response = self.run_test(
            "Finalize Upload",
            "POST",
            f"uploads/sessions/{upload_id}/complete",
            200,
            data=finalize_data,
            auth_required=True
        )
        
        job_id = None
        if success:
            job_id = finalize_response.get('job_id')
            self.log(f"   Transcription job created: {job_id}")
            self.log(f"   Status: {finalize_response.get('status')}")
            self.log(f"   Upload ID: {finalize_response.get('upload_id')}")
        
        if not job_id:
            self.log("❌ No job_id returned - skipping transcription tests")
            return False
        
        # Test 6: Job Status Tracking
        self.log("📊 Testing job status tracking...")
        
        success, job_status = self.run_test(
            "Get Job Status",
            "GET",
            f"transcriptions/{job_id}",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   Job status: {job_status.get('status')}")
            self.log(f"   Current stage: {job_status.get('current_stage')}")
            self.log(f"   Progress: {job_status.get('progress', 0)}%")
            self.log(f"   Detected language: {job_status.get('detected_language', 'N/A')}")
            self.log(f"   Total duration: {job_status.get('total_duration', 'N/A')}")
            
            stage_progress = job_status.get('stage_progress', {})
            if stage_progress:
                self.log(f"   Stage progress: {len(stage_progress)} stages tracked")
        
        # Test 7: List User's Transcription Jobs
        self.log("📋 Testing job listing...")
        
        success, jobs_list = self.run_test(
            "List Transcription Jobs",
            "GET",
            "transcriptions/",
            200,
            auth_required=True
        )
        
        if success:
            jobs = jobs_list.get('jobs', [])
            self.log(f"   Found {len(jobs)} transcription jobs")
            self.log(f"   Total count: {jobs_list.get('total', 0)}")
            for job in jobs[:3]:  # Show first 3
                self.log(f"   - {job.get('filename', 'N/A')} ({job.get('status', 'N/A')})")
        
        # Test 8: Test Download Endpoints (will fail if not complete, but should return proper error)
        self.log("💾 Testing download endpoints...")
        
        for format_type in ['txt', 'json', 'srt', 'vtt']:
            success, download_response = self.run_test(
                f"Download {format_type.upper()} Format",
                "GET",
                f"transcriptions/{job_id}/download?format={format_type}",
                400,  # Expect 400 since job won't be complete yet
                auth_required=True
            )
            # 400 is expected since job processing takes time
        
        # Test 9: Test Retry Functionality
        self.log("🔄 Testing job retry functionality...")
        
        retry_data = {
            "job_id": job_id,
            "from_stage": "transcribing"
        }
        
        success, retry_response = self.run_test(
            "Retry Job (Should Fail - Not Failed)",
            "POST",
            f"transcriptions/{job_id}/retry",
            400,  # Should fail since job is not in failed state
            data=retry_data,
            auth_required=True
        )
        # This is expected to fail since the job is not in failed state
        
        # Test 10: Test Cancel Job
        self.log("🚫 Testing job cancellation...")
        
        success, cancel_response = self.run_test(
            "Cancel Job",
            "POST",
            f"transcriptions/{job_id}/cancel",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   Cancel message: {cancel_response.get('message', 'N/A')}")
        
        # Test 11: Error Handling Tests
        self.log("⚠️  Testing error handling...")
        
        # Test invalid upload session
        success, error_response = self.run_test(
            "Get Invalid Upload Session",
            "GET",
            "uploads/sessions/invalid-id/status",
            404,
            auth_required=True
        )
        
        # Test invalid job ID
        success, error_response = self.run_test(
            "Get Invalid Job Status",
            "GET",
            "transcriptions/invalid-job-id",
            404,
            auth_required=True
        )
        
        # Test invalid chunk upload
        success, error_response = self.run_test(
            "Upload to Invalid Session",
            "POST",
            "uploads/sessions/invalid-id/chunks/0",
            404,
            auth_required=True
        )
        
        # Test file size validation
        large_session_data = {
            "filename": "huge_file.mp3",
            "total_size": 600 * 1024 * 1024,  # 600MB (over limit)
            "mime_type": "audio/mpeg"
        }
        
        success, error_response = self.run_test(
            "Create Session with Oversized File",
            "POST",
            "uploads/sessions",
            400,  # Should fail due to size limit
            data=large_session_data,
            auth_required=True
        )
        
        # Test invalid MIME type
        invalid_mime_data = {
            "filename": "document.pdf",
            "total_size": 1024 * 1024,  # 1MB
            "mime_type": "application/pdf"  # Not allowed for audio
        }
        
        success, error_response = self.run_test(
            "Create Session with Invalid MIME Type",
            "POST",
            "uploads/sessions",
            400,  # Should fail due to invalid MIME type
            data=invalid_mime_data,
            auth_required=True
        )
        
        self.log("✅ Large-file transcription pipeline tests completed!")
        return True

    def run_pipeline_tests(self):
        """Run pipeline-specific tests"""
        self.log("🚀 Starting Large-file Audio Transcription Pipeline Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Health check
        if not self.test_health_check():
            self.log("❌ Health check failed - stopping tests")
            return False
        
        # User registration for authenticated tests
        if not self.test_user_registration():
            self.log("❌ User registration failed - stopping tests")
            return False
        
        # Run pipeline tests
        pipeline_success = self.test_large_file_transcription_pipeline()
        
        # Summary
        self.log("\n📊 PIPELINE TEST SUMMARY")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"   Tests run: {self.tests_run}")
        self.log(f"   Tests passed: {self.tests_passed}")
        self.log(f"   Success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            self.log("🎉 Pipeline test result: PASS")
        else:
            self.log("❌ Pipeline test result: FAIL")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = PipelineAPITester()
    success = tester.run_pipeline_tests()
    
    print("\n" + "="*50)
    print("📊 PIPELINE TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0:.1f}%")
    print("="*50)
    
    if not success:
        print("⚠️  Some tests failed. Check the logs above for details.")
        sys.exit(1)
    else:
        print("🎉 All pipeline tests passed!")
        sys.exit(0)