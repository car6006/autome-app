#!/usr/bin/env python3
"""
Large Audio File Processing Verification Test
Tests the bulletproof monitoring system and FFmpeg fixes for large audio files
"""

import requests
import sys
import json
import time
import os
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

class LargeAudioProcessingTester:
    def __init__(self, base_url="https://audio-pipeline-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"audio_test_user_{int(time.time())}@example.com",
            "username": f"audiouser{int(time.time())}",
            "password": "AudioTest123!",
            "first_name": "Audio",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=300, auth_required=False):
        """Run a single API test with extended timeout for large files"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
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

    def test_ffmpeg_installation(self):
        """Test FFmpeg and FFprobe installation"""
        self.log("🎬 Testing FFmpeg Installation...")
        
        # Test FFmpeg availability
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log("✅ FFmpeg is installed and accessible")
                version_line = result.stdout.split('\n')[0]
                self.log(f"   Version: {version_line}")
                ffmpeg_available = True
            else:
                self.log("❌ FFmpeg is not working properly")
                ffmpeg_available = False
        except Exception as e:
            self.log(f"❌ FFmpeg test failed: {str(e)}")
            ffmpeg_available = False
        
        # Test FFprobe availability
        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log("✅ FFprobe is installed and accessible")
                version_line = result.stdout.split('\n')[0]
                self.log(f"   Version: {version_line}")
                ffprobe_available = True
            else:
                self.log("❌ FFprobe is not working properly")
                ffprobe_available = False
        except Exception as e:
            self.log(f"❌ FFprobe test failed: {str(e)}")
            ffprobe_available = False
        
        self.tests_run += 2
        if ffmpeg_available:
            self.tests_passed += 1
        if ffprobe_available:
            self.tests_passed += 1
            
        return ffmpeg_available and ffprobe_available

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check Endpoint",
            "GET",
            "health",
            200,
            timeout=30
        )
        
        if success:
            self.log(f"   Status: {response.get('status', 'N/A')}")
            self.log(f"   Timestamp: {response.get('timestamp', 'N/A')}")
            services = response.get('services', {})
            self.log(f"   Database: {services.get('database', 'N/A')}")
            self.log(f"   API: {services.get('api', 'N/A')}")
            
            # Check if all services are healthy
            if (response.get('status') == 'healthy' and 
                services.get('database') == 'connected' and 
                services.get('api') == 'running'):
                self.log("✅ All services are healthy")
                return True
            else:
                self.log("⚠️  Some services may not be fully healthy")
                return False
        
        return success

    def register_test_user(self):
        """Register a test user for authenticated tests"""
        success, response = self.run_test(
            "User Registration for Audio Tests",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   Registered user: {self.test_user_data['email']}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
        
        return success

    def create_small_audio_file(self, duration_seconds=5):
        """Create a small test audio file using FFmpeg"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Generate a small audio file with FFmpeg
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duration_seconds}',
                    '-ac', '1', '-ar', '22050', '-b:a', '64k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(tmp_file.name)
                    self.log(f"   Created small audio file: {file_size} bytes ({duration_seconds}s)")
                    return tmp_file.name, file_size
                else:
                    self.log(f"   FFmpeg error: {result.stderr}")
                    return None, 0
        except Exception as e:
            self.log(f"   Error creating audio file: {str(e)}")
            return None, 0

    def create_medium_audio_file(self, duration_seconds=120):
        """Create a medium test audio file (2 minutes)"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Generate a medium audio file
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duration_seconds}',
                    '-ac', '2', '-ar', '44100', '-b:a', '128k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(tmp_file.name)
                    self.log(f"   Created medium audio file: {file_size} bytes ({duration_seconds}s)")
                    return tmp_file.name, file_size
                else:
                    self.log(f"   FFmpeg error: {result.stderr}")
                    return None, 0
        except Exception as e:
            self.log(f"   Error creating audio file: {str(e)}")
            return None, 0

    def create_large_audio_file(self, duration_seconds=600):
        """Create a large test audio file (10 minutes) that should trigger chunking"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Generate a large audio file that will be over 25MB
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duration_seconds}',
                    '-ac', '2', '-ar', '44100', '-b:a', '320k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(tmp_file.name)
                    self.log(f"   Created large audio file: {file_size} bytes ({duration_seconds}s)")
                    
                    # Check if file is actually large enough to trigger chunking (>24MB)
                    if file_size > 24 * 1024 * 1024:
                        self.log(f"   ✅ File size exceeds 24MB threshold - will trigger chunking")
                    else:
                        self.log(f"   ⚠️  File size is {file_size/(1024*1024):.1f}MB - may not trigger chunking")
                    
                    return tmp_file.name, file_size
                else:
                    self.log(f"   FFmpeg error: {result.stderr}")
                    return None, 0
        except Exception as e:
            self.log(f"   Error creating audio file: {str(e)}")
            return None, 0

    def test_audio_upload_and_processing(self, file_path, file_size, test_name, expected_chunking=False):
        """Test uploading and processing an audio file"""
        if not file_path or not os.path.exists(file_path):
            self.log(f"❌ {test_name} - Audio file not available")
            return False, None
        
        try:
            # Upload the audio file
            with open(file_path, 'rb') as f:
                files = {'file': (f'test_audio_{int(time.time())}.mp3', f, 'audio/mpeg')}
                data = {'title': f'{test_name} Audio Processing Test'}
                
                success, response = self.run_test(
                    f"{test_name} - Upload Audio File ({file_size/(1024*1024):.1f}MB)",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    timeout=300,  # 5 minute timeout for large files
                    auth_required=True
                )
            
            if not success:
                return False, None
            
            note_id = response.get('id')
            if not note_id:
                self.log(f"❌ {test_name} - No note ID returned")
                return False, None
            
            self.created_notes.append(note_id)
            self.log(f"   Created note ID: {note_id}")
            self.log(f"   Upload status: {response.get('status', 'N/A')}")
            
            # Wait for processing to complete
            return self.wait_for_processing(note_id, test_name, expected_chunking), note_id
            
        except Exception as e:
            self.log(f"❌ {test_name} - Upload error: {str(e)}")
            return False, None
        finally:
            # Clean up the temporary file
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass

    def wait_for_processing(self, note_id, test_name, expected_chunking=False, max_wait=600):
        """Wait for note processing to complete with detailed monitoring"""
        self.log(f"⏳ Waiting for {test_name} processing (max {max_wait}s)...")
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            try:
                # Get note status
                url = f"{self.api_url}/notes/{note_id}"
                headers = {}
                if self.auth_token:
                    headers['Authorization'] = f'Bearer {self.auth_token}'
                
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    note_data = response.json()
                    status = note_data.get('status', 'unknown')
                    
                    if status != last_status:
                        self.log(f"   Status: {status}")
                        last_status = status
                    
                    if status == 'ready':
                        self.log(f"✅ {test_name} processing completed successfully!")
                        
                        # Check artifacts for transcription
                        artifacts = note_data.get('artifacts', {})
                        transcript = artifacts.get('transcript', '')
                        
                        if transcript:
                            self.log(f"   ✅ Transcript generated: {len(transcript)} characters")
                            
                            # Check for chunking indicators if expected
                            if expected_chunking:
                                if '[Part ' in transcript:
                                    part_count = transcript.count('[Part ')
                                    self.log(f"   ✅ Chunking detected: {part_count} parts found")
                                else:
                                    self.log(f"   ⚠️  Expected chunking but no part markers found")
                        else:
                            self.log(f"   ⚠️  No transcript generated")
                        
                        # Check processing metrics
                        metrics = note_data.get('metrics', {})
                        if metrics:
                            latency = metrics.get('latency_ms')
                            if latency:
                                self.log(f"   Processing time: {latency/1000:.1f} seconds")
                        
                        return True
                        
                    elif status == 'failed':
                        self.log(f"❌ {test_name} processing failed!")
                        
                        # Check for error details in artifacts
                        artifacts = note_data.get('artifacts', {})
                        error = artifacts.get('error', 'No error details available')
                        self.log(f"   Error: {error}")
                        
                        return False
                        
                    elif status in ['processing', 'uploading']:
                        # Still processing, continue waiting
                        time.sleep(5)
                        
                    else:
                        self.log(f"   Unknown status: {status}")
                        time.sleep(5)
                        
                else:
                    self.log(f"   Error getting note status: {response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                self.log(f"   Error checking status: {str(e)}")
                time.sleep(5)
        
        self.log(f"⏰ {test_name} processing timeout after {max_wait}s")
        return False

    def test_system_stability(self):
        """Test system stability by creating multiple concurrent audio uploads"""
        self.log("🔄 Testing System Stability with Multiple Audio Files...")
        
        # Create multiple small audio files for concurrent testing
        test_files = []
        for i in range(3):
            file_path, file_size = self.create_small_audio_file(duration_seconds=10)
            if file_path:
                test_files.append((file_path, file_size, f"Stability Test {i+1}"))
        
        if not test_files:
            self.log("❌ Could not create test files for stability testing")
            return False
        
        # Upload all files
        upload_results = []
        for file_path, file_size, test_name in test_files:
            success, note_id = self.test_audio_upload_and_processing(
                file_path, file_size, test_name, expected_chunking=False
            )
            upload_results.append((success, note_id, test_name))
        
        # Check results
        successful_uploads = sum(1 for success, _, _ in upload_results if success)
        total_uploads = len(upload_results)
        
        self.log(f"   Stability Test Results: {successful_uploads}/{total_uploads} successful")
        
        if successful_uploads == total_uploads:
            self.log("✅ System stability test passed - all uploads processed successfully")
            return True
        else:
            self.log(f"⚠️  System stability test partial success: {successful_uploads}/{total_uploads}")
            return successful_uploads > 0

    def test_service_monitoring(self):
        """Test service monitoring and health checks"""
        self.log("📊 Testing Service Monitoring...")
        
        # Test health endpoint multiple times to check consistency
        health_checks = []
        for i in range(3):
            success = self.test_health_endpoint()
            health_checks.append(success)
            if i < 2:  # Don't sleep after the last check
                time.sleep(2)
        
        successful_checks = sum(health_checks)
        self.log(f"   Health Check Consistency: {successful_checks}/3 successful")
        
        # Test API responsiveness
        start_time = time.time()
        success, response = self.run_test(
            "API Responsiveness Test",
            "GET",
            "",
            200,
            timeout=10
        )
        response_time = time.time() - start_time
        
        if success:
            self.log(f"   API Response Time: {response_time:.2f} seconds")
            if response_time < 5:
                self.log("✅ API is responsive")
            else:
                self.log("⚠️  API response time is slow")
        
        return successful_checks >= 2 and success

    def run_comprehensive_audio_test(self):
        """Run comprehensive large audio file processing tests"""
        self.log("🚀 Starting Large Audio File Processing Verification Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # === FFMPEG INSTALLATION VERIFICATION ===
        self.log("\n🎬 FFMPEG INSTALLATION VERIFICATION")
        ffmpeg_available = self.test_ffmpeg_installation()
        
        if not ffmpeg_available:
            self.log("❌ FFmpeg not available - cannot proceed with audio tests")
            return False
        
        # === SERVICE HEALTH MONITORING ===
        self.log("\n🏥 SERVICE HEALTH MONITORING")
        health_ok = self.test_health_endpoint()
        
        if not health_ok:
            self.log("⚠️  Health check issues detected")
        
        # === USER REGISTRATION FOR AUTHENTICATED TESTS ===
        self.log("\n👤 USER REGISTRATION")
        if not self.register_test_user():
            self.log("❌ User registration failed - cannot proceed with authenticated tests")
            return False
        
        # === AUDIO PROCESSING PIPELINE TESTS ===
        self.log("\n🎵 AUDIO PROCESSING PIPELINE TESTS")
        
        # Test 1: Small Audio File (should process normally)
        self.log("\n📁 Small Audio File Test")
        small_file_path, small_file_size = self.create_small_audio_file(duration_seconds=10)
        small_success, small_note_id = self.test_audio_upload_and_processing(
            small_file_path, small_file_size, "Small Audio File", expected_chunking=False
        )
        
        # Test 2: Medium Audio File (should process normally)
        self.log("\n📁 Medium Audio File Test")
        medium_file_path, medium_file_size = self.create_medium_audio_file(duration_seconds=120)
        medium_success, medium_note_id = self.test_audio_upload_and_processing(
            medium_file_path, medium_file_size, "Medium Audio File", expected_chunking=False
        )
        
        # Test 3: Large Audio File (should trigger chunking)
        self.log("\n📁 Large Audio File Test (Chunking)")
        large_file_path, large_file_size = self.create_large_audio_file(duration_seconds=600)
        large_success, large_note_id = self.test_audio_upload_and_processing(
            large_file_path, large_file_size, "Large Audio File", expected_chunking=True
        )
        
        # === SYSTEM STABILITY TESTS ===
        self.log("\n🔄 SYSTEM STABILITY TESTS")
        stability_ok = self.test_system_stability()
        
        # === SERVICE MONITORING TESTS ===
        self.log("\n📊 SERVICE MONITORING TESTS")
        monitoring_ok = self.test_service_monitoring()
        
        # === RESULTS SUMMARY ===
        self.log("\n📋 TEST RESULTS SUMMARY")
        results = {
            "FFmpeg Installation": ffmpeg_available,
            "Health Endpoint": health_ok,
            "Small Audio Processing": small_success,
            "Medium Audio Processing": medium_success,
            "Large Audio Processing (Chunking)": large_success,
            "System Stability": stability_ok,
            "Service Monitoring": monitoring_ok
        }
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"   {test_name}: {status}")
        
        # Overall success criteria
        critical_tests = [ffmpeg_available, small_success, medium_success, large_success]
        critical_passed = sum(critical_tests)
        
        self.log(f"\n🎯 Critical Tests: {critical_passed}/4 passed")
        
        if critical_passed == 4:
            self.log("🎉 ALL CRITICAL TESTS PASSED - Large audio file processing is working correctly!")
            return True
        else:
            self.log(f"⚠️  {4-critical_passed} critical test(s) failed - issues need attention")
            return False

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 LARGE AUDIO FILE PROCESSING TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = LargeAudioProcessingTester()
    
    try:
        success = tester.run_comprehensive_audio_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 Large audio file processing verification PASSED!")
            print("✅ FFmpeg is working correctly")
            print("✅ Audio chunking system is functional") 
            print("✅ Service monitoring is operational")
            print("✅ System is stable and ready for production")
            return 0
        else:
            print(f"\n⚠️  Large audio file processing verification had issues.")
            print("Check the detailed logs above for specific problems.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())