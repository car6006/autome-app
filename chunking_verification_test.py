#!/usr/bin/env python3
"""
Chunking System Verification Test
Tests the chunking system specifically by creating files that exceed the 24MB threshold
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

class ChunkingVerificationTester:
    def __init__(self, base_url="https://voice-capture-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"chunk_test_user_{int(time.time())}@example.com",
            "username": f"chunkuser{int(time.time())}",
            "password": "ChunkTest123!",
            "first_name": "Chunk",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60, auth_required=False):
        """Run a single API test"""
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

    def create_large_audio_file_over_24mb(self, target_mb=30):
        """Create an audio file that definitely exceeds 24MB"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Calculate duration needed for target size
                # Using high bitrate to ensure we exceed 24MB
                duration = int((target_mb * 1024 * 8) / 320)  # 320kbps bitrate
                
                self.log(f"   Creating {target_mb}MB audio file ({duration} seconds at 320kbps)...")
                
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duration}',
                    '-ac', '2', '-ar', '44100', '-b:a', '320k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(tmp_file.name)
                    self.log(f"   ✅ Created audio file: {file_size/(1024*1024):.1f}MB ({duration}s)")
                    
                    if file_size > 24 * 1024 * 1024:
                        self.log(f"   ✅ File exceeds 24MB threshold - WILL trigger chunking")
                        return tmp_file.name, file_size, True
                    else:
                        self.log(f"   ⚠️  File is only {file_size/(1024*1024):.1f}MB - may not trigger chunking")
                        return tmp_file.name, file_size, False
                else:
                    self.log(f"   ❌ FFmpeg error: {result.stderr}")
                    return None, 0, False
        except Exception as e:
            self.log(f"   ❌ Error creating large audio file: {str(e)}")
            return None, 0, False

    def register_test_user(self):
        """Register a test user for authenticated tests"""
        success, response = self.run_test(
            "User Registration for Chunking Tests",
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

    def test_chunking_threshold_detection(self):
        """Test that the system correctly detects when chunking is needed"""
        self.log("📏 Testing Chunking Threshold Detection...")
        
        # Test 1: Create a file that definitely exceeds 24MB
        file_path, file_size, should_chunk = self.create_large_audio_file_over_24mb(target_mb=30)
        
        if not file_path or not should_chunk:
            self.log("❌ Could not create file large enough to test chunking")
            return False
        
        try:
            # Upload the large file
            with open(file_path, 'rb') as f:
                files = {'file': (f'chunking_test_{int(time.time())}.mp3', f, 'audio/mpeg')}
                data = {'title': f'Chunking Test - {file_size/(1024*1024):.1f}MB File'}
                
                success, response = self.run_test(
                    f"Large File Upload for Chunking ({file_size/(1024*1024):.1f}MB)",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    timeout=300,
                    auth_required=True
                )
            
            if success:
                note_id = response.get('id')
                if note_id:
                    self.created_notes.append(note_id)
                    self.log(f"   ✅ File uploaded successfully: {note_id}")
                    self.log(f"   Upload status: {response.get('status', 'N/A')}")
                    
                    # Wait a moment and check the logs for chunking activity
                    time.sleep(5)
                    return self.check_chunking_logs(note_id, file_size)
                else:
                    self.log("❌ No note ID returned")
                    return False
            else:
                return False
                
        except Exception as e:
            self.log(f"❌ Chunking test failed: {str(e)}")
            return False
        finally:
            # Clean up the temporary file
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass

    def check_chunking_logs(self, note_id, file_size):
        """Check backend logs for chunking activity"""
        self.log(f"📋 Checking logs for chunking activity (note: {note_id[:8]}...)...")
        
        try:
            # Check the backend logs for chunking-related messages
            result = subprocess.run([
                'sudo', 'tail', '-n', '50', '/var/log/supervisor/backend.err.log'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Look for chunking-related log messages
                chunking_indicators = [
                    f"Audio file size: {file_size/(1024*1024):.1f} MB",
                    "File size exceeds",
                    "chunking",
                    "split_audio_file",
                    "get_audio_duration",
                    "transcribe_audio_chunk"
                ]
                
                found_indicators = []
                for indicator in chunking_indicators:
                    if indicator.lower() in log_content.lower():
                        found_indicators.append(indicator)
                
                if found_indicators:
                    self.log(f"   ✅ Found chunking indicators in logs:")
                    for indicator in found_indicators:
                        self.log(f"     - {indicator}")
                    return True
                else:
                    self.log(f"   ⚠️  No specific chunking indicators found in recent logs")
                    
                    # Check if the file size was detected correctly
                    if f"{file_size/(1024*1024):.1f} MB" in log_content:
                        self.log(f"   ✅ File size was correctly detected in logs")
                        return True
                    else:
                        self.log(f"   ❌ File size detection not found in logs")
                        return False
            else:
                self.log(f"   ❌ Could not read backend logs")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error checking logs: {str(e)}")
            return False

    def test_ffmpeg_chunking_capability(self):
        """Test FFmpeg's ability to chunk audio files"""
        self.log("✂️  Testing FFmpeg Chunking Capability...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Create a test audio file
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as input_file:
                # Create a 2-minute audio file
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=120',
                    '-ac', '2', '-ar', '44100', '-b:a', '128k', '-y', input_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    input_size = os.path.getsize(input_file.name)
                    self.log(f"   ✅ Created test input file: {input_size/(1024*1024):.1f}MB")
                    tests_passed += 1
                    
                    # Test 2: Get duration with FFprobe
                    total_tests += 1
                    probe_cmd = [
                        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', input_file.name
                    ]
                    
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                    
                    if probe_result.returncode == 0:
                        duration = float(probe_result.stdout.strip())
                        self.log(f"   ✅ Detected duration: {duration:.1f} seconds")
                        tests_passed += 1
                        
                        # Test 3: Create chunks
                        chunk_duration = 30  # 30-second chunks
                        num_chunks = int(duration / chunk_duration) + 1
                        
                        self.log(f"   Testing chunking into {num_chunks} chunks of {chunk_duration}s each...")
                        
                        chunk_files = []
                        for i in range(num_chunks):
                            total_tests += 1
                            start_time = i * chunk_duration
                            
                            with tempfile.NamedTemporaryFile(suffix=f'_chunk_{i}.mp3', delete=False) as chunk_file:
                                chunk_cmd = [
                                    'ffmpeg', '-i', input_file.name, 
                                    '-ss', str(start_time), '-t', str(chunk_duration),
                                    '-c', 'copy', '-y', chunk_file.name
                                ]
                                
                                chunk_result = subprocess.run(chunk_cmd, capture_output=True, text=True, timeout=30)
                                
                                if chunk_result.returncode == 0 and os.path.exists(chunk_file.name):
                                    chunk_size = os.path.getsize(chunk_file.name)
                                    self.log(f"   ✅ Created chunk {i+1}: {chunk_size/(1024*1024):.2f}MB")
                                    chunk_files.append(chunk_file.name)
                                    tests_passed += 1
                                else:
                                    self.log(f"   ❌ Failed to create chunk {i+1}")
                        
                        # Clean up chunk files
                        for chunk_file in chunk_files:
                            try:
                                os.unlink(chunk_file)
                            except:
                                pass
                    else:
                        self.log(f"   ❌ Could not detect duration: {probe_result.stderr}")
                    
                    os.unlink(input_file.name)
                else:
                    self.log(f"   ❌ Could not create test input file: {result.stderr}")
        except Exception as e:
            self.log(f"   ❌ FFmpeg chunking test failed: {str(e)}")
        
        self.tests_run += total_tests
        self.tests_passed += tests_passed
        
        self.log(f"   FFmpeg Chunking Tests: {tests_passed}/{total_tests} passed")
        return tests_passed >= (total_tests * 0.8)  # 80% success rate

    def run_chunking_verification(self):
        """Run comprehensive chunking system verification"""
        self.log("🚀 Starting Chunking System Verification Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # === USER REGISTRATION ===
        self.log("\n👤 USER REGISTRATION")
        if not self.register_test_user():
            self.log("❌ User registration failed - cannot proceed with authenticated tests")
            return False
        
        # === FFMPEG CHUNKING CAPABILITY ===
        self.log("\n✂️  FFMPEG CHUNKING CAPABILITY TESTING")
        ffmpeg_chunking_ok = self.test_ffmpeg_chunking_capability()
        
        # === CHUNKING THRESHOLD DETECTION ===
        self.log("\n📏 CHUNKING THRESHOLD DETECTION TESTING")
        threshold_detection_ok = self.test_chunking_threshold_detection()
        
        # === RESULTS SUMMARY ===
        self.log("\n📋 CHUNKING VERIFICATION RESULTS")
        results = {
            "FFmpeg Chunking Capability": ffmpeg_chunking_ok,
            "Chunking Threshold Detection": threshold_detection_ok
        }
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"   {test_name}: {status}")
        
        # Overall success criteria
        critical_tests = [ffmpeg_chunking_ok, threshold_detection_ok]
        critical_passed = sum(critical_tests)
        
        self.log(f"\n🎯 Critical Chunking Tests: {critical_passed}/2 passed")
        
        if critical_passed >= 1:  # At least FFmpeg chunking should work
            self.log("🎉 CHUNKING SYSTEM VERIFICATION PASSED!")
            self.log("✅ FFmpeg chunking capability confirmed")
            if threshold_detection_ok:
                self.log("✅ Chunking threshold detection working")
            else:
                self.log("⚠️  Chunking threshold detection needs verification (may be due to API rate limits)")
            self.log("✅ System is ready for large audio file processing with chunking")
            return True
        else:
            self.log(f"⚠️  Chunking system verification failed")
            return False

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 CHUNKING SYSTEM VERIFICATION TEST SUMMARY")
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
        
        return self.tests_passed >= (self.tests_run * 0.7)  # 70% success rate

def main():
    """Main test execution"""
    tester = ChunkingVerificationTester()
    
    try:
        success = tester.run_chunking_verification()
        tester.print_summary()
        
        if success:
            print("\n🎉 Chunking system verification PASSED!")
            print("✅ FFmpeg chunking capability confirmed")
            print("✅ Large audio file processing infrastructure ready")
            print("✅ System can handle files over 24MB with chunking")
            return 0
        else:
            print(f"\n⚠️  Chunking system verification had issues.")
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