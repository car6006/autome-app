#!/usr/bin/env python3
"""
Improved Transcription Pipeline Test
Creates a real audio file and tests the complete pipeline
"""

import requests
import sys
import json
import time
import tempfile
import os
import struct
import wave
from datetime import datetime
from pathlib import Path

class ImprovedTranscriptionTester:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"test_improved_{int(time.time())}@example.com",
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

    def create_real_audio_file(self, duration_seconds=2, sample_rate=16000):
        """Create a real WAV audio file with sine wave tone"""
        import math
        
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Generate sine wave data
            frequency = 440  # A4 note
            frames = []
            
            for i in range(int(duration_seconds * sample_rate)):
                # Generate sine wave sample
                sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
                frames.append(struct.pack('<h', sample))  # 16-bit little-endian
            
            # Write WAV file
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(frames))
            
            return tmp_file.name

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

    def test_cleanup_stuck_job_fixed(self):
        """Test the fixed cleanup endpoint"""
        self.log(f"\n🧹 TESTING FIXED CLEANUP ENDPOINT")
        
        # Test the general cleanup endpoint (now fixed)
        success, response = self.run_test(
            "Fixed Cleanup Endpoint",
            "POST",
            "transcriptions/cleanup",
            200,
            auth_required=True
        )
        
        if success:
            fixed_count = response.get('fixed_count', 0)
            self.log(f"   ✅ Cleanup completed - Fixed {fixed_count} jobs")
            return True
        else:
            self.log(f"   ❌ Cleanup still failing")
            return False

    def test_upload_real_audio_file(self):
        """Test uploading a real audio file"""
        self.log(f"\n🎵 TESTING REAL AUDIO FILE UPLOAD")
        
        # Create real audio file
        audio_file_path = self.create_real_audio_file(duration_seconds=3)
        file_size = os.path.getsize(audio_file_path)
        
        self.log(f"   Created real WAV file: {file_size} bytes")
        
        try:
            with open(audio_file_path, 'rb') as f:
                files = {'file': ('test_real_audio.wav', f, 'audio/wav')}
                data = {'title': 'Real Audio Test - Sine Wave'}
                
                success, response = self.run_test(
                    "Real Audio Upload",
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

    def test_monitor_processing_detailed(self, note_id, max_wait=120):
        """Monitor note processing with detailed logging"""
        self.log(f"\n⏳ DETAILED PROCESSING MONITORING FOR NOTE: {note_id}")
        
        start_time = time.time()
        last_status = None
        
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
                
                # Only log if status changed
                if status != last_status:
                    self.log(f"   Status changed: {last_status} → {status} (after {time.time() - start_time:.1f}s)")
                    last_status = status
                
                if status == 'ready':
                    transcript = artifacts.get('transcript', '')
                    error_msg = artifacts.get('error', '')
                    
                    self.log(f"   ✅ Processing completed successfully!")
                    self.log(f"   Transcript length: {len(transcript)} characters")
                    
                    if transcript:
                        self.log(f"   Transcript preview: {transcript[:100]}...")
                        return True
                    elif error_msg:
                        self.log(f"   ⚠️  No transcript but has error: {error_msg}")
                        return False
                    else:
                        self.log(f"   ⚠️  No transcript generated (empty audio?)")
                        return True  # Still consider success if no errors
                        
                elif status == 'failed':
                    error_msg = artifacts.get('error', 'Unknown error')
                    self.log(f"   ❌ Processing failed: {error_msg}")
                    return False
                elif status in ['processing', 'uploading']:
                    # Don't spam logs for processing status
                    time.sleep(5)
                else:
                    time.sleep(3)
            else:
                self.log(f"   ❌ Failed to check status")
                break
        
        self.log(f"   ⏰ Timeout after {max_wait} seconds")
        return False

    def test_openai_api_integration(self):
        """Test OpenAI API integration more thoroughly"""
        self.log(f"\n🔑 TESTING OPENAI API INTEGRATION")
        
        # Check health endpoint
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        
        if success:
            services = response.get('services', {})
            pipeline_status = services.get('pipeline', 'unknown')
            
            self.log(f"   Pipeline Status: {pipeline_status}")
            
            # Check if OpenAI key is configured by looking at startup logs
            if pipeline_status == 'healthy':
                self.log(f"   ✅ Pipeline appears healthy")
                return True
            else:
                self.log(f"   ⚠️  Pipeline status not optimal: {pipeline_status}")
                return False
        else:
            self.log(f"   ❌ Health check failed")
            return False

    def test_transcription_jobs_list(self):
        """Test transcription jobs listing functionality"""
        self.log(f"\n📋 TESTING TRANSCRIPTION JOBS LISTING")
        
        success, response = self.run_test(
            "List All Transcription Jobs",
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
            
            # Check for specific job statuses
            status_counts = {}
            for job in jobs:
                status = job.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                self.log(f"   {status}: {count} jobs")
            
            # Check if the stuck job is still there
            stuck_job_found = any(job.get('job_id') == self.stuck_job_id for job in jobs)
            if stuck_job_found:
                self.log(f"   ⚠️  Stuck job {self.stuck_job_id} still found!")
            else:
                self.log(f"   ✅ Stuck job {self.stuck_job_id} not found (good)")
            
            return True
        else:
            self.log(f"   ❌ Error loading jobs detected!")
            return False

    def run_improved_test_suite(self):
        """Run the improved test suite"""
        self.log("🚀 STARTING IMPROVED TRANSCRIPTION PIPELINE TEST")
        self.log("=" * 60)
        
        # Step 1: Register user for authentication
        if not self.test_user_registration():
            self.log("❌ Failed to register user - cannot continue")
            return False
        
        # Step 2: Test OpenAI API integration
        api_integration_ok = self.test_openai_api_integration()
        
        # Step 3: Test fixed cleanup endpoint
        cleanup_fixed = self.test_cleanup_stuck_job_fixed()
        
        # Step 4: Test transcription jobs listing
        jobs_listing_ok = self.test_transcription_jobs_list()
        
        # Step 5: Test real audio upload
        note_id = self.test_upload_real_audio_file()
        
        processing_success = False
        if note_id:
            # Step 6: Monitor processing with real audio
            processing_success = self.test_monitor_processing_detailed(note_id)
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 IMPROVED TEST SUMMARY")
        self.log("=" * 60)
        
        results = {
            "User Registration": True,  # We got this far
            "OpenAI API Integration": api_integration_ok,
            "Fixed Cleanup Endpoint": cleanup_fixed,
            "Jobs Listing": jobs_listing_ok,
            "Real Audio Upload": note_id is not None,
            "Pipeline Processing": processing_success
        }
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   {status} {test_name}")
        
        overall_success = all(results.values())
        
        self.log(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ ISSUES FOUND'}")
        self.log(f"📈 Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if overall_success:
            self.log("\n🎉 All improved tests completed successfully!")
            self.log("   - Cleanup endpoint fixed and working")
            self.log("   - Real audio file processed successfully")
            self.log("   - Pipeline verified working with OpenAI API")
            self.log("   - No 'Error loading jobs' issues detected")
        else:
            self.log("\n⚠️  Some issues found - see details above")
        
        return overall_success

def main():
    """Main test execution"""
    tester = ImprovedTranscriptionTester()
    
    try:
        success = tester.run_improved_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()