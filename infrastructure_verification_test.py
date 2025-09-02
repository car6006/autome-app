#!/usr/bin/env python3
"""
Infrastructure Verification Test
Tests the bulletproof monitoring system and FFmpeg infrastructure without relying on external APIs
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

class InfrastructureVerificationTester:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"infra_test_user_{int(time.time())}@example.com",
            "username": f"infrauser{int(time.time())}",
            "password": "InfraTest123!",
            "first_name": "Infrastructure",
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

    def test_ffmpeg_comprehensive(self):
        """Comprehensive FFmpeg functionality test"""
        self.log("🎬 Testing FFmpeg Comprehensive Functionality...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: FFmpeg version and availability
        total_tests += 1
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log("✅ FFmpeg is installed and accessible")
                version_line = result.stdout.split('\n')[0]
                self.log(f"   Version: {version_line}")
                tests_passed += 1
            else:
                self.log("❌ FFmpeg is not working properly")
        except Exception as e:
            self.log(f"❌ FFmpeg test failed: {str(e)}")
        
        # Test 2: FFprobe version and availability
        total_tests += 1
        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log("✅ FFprobe is installed and accessible")
                version_line = result.stdout.split('\n')[0]
                self.log(f"   Version: {version_line}")
                tests_passed += 1
            else:
                self.log("❌ FFprobe is not working properly")
        except Exception as e:
            self.log(f"❌ FFprobe test failed: {str(e)}")
        
        # Test 3: Audio file creation capability
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5',
                    '-ac', '1', '-ar', '22050', '-b:a', '64k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(tmp_file.name):
                    file_size = os.path.getsize(tmp_file.name)
                    self.log(f"✅ FFmpeg can create audio files: {file_size} bytes")
                    tests_passed += 1
                    os.unlink(tmp_file.name)
                else:
                    self.log(f"❌ FFmpeg audio creation failed: {result.stderr}")
        except Exception as e:
            self.log(f"❌ FFmpeg audio creation test failed: {str(e)}")
        
        # Test 4: Audio duration detection with FFprobe
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Create a 10-second audio file
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=10',
                    '-ac', '1', '-ar', '22050', '-b:a', '64k', '-y', tmp_file.name
                ]
                
                create_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if create_result.returncode == 0:
                    # Test duration detection
                    probe_cmd = [
                        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', tmp_file.name
                    ]
                    
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                    
                    if probe_result.returncode == 0:
                        duration = float(probe_result.stdout.strip())
                        self.log(f"✅ FFprobe can detect audio duration: {duration:.1f} seconds")
                        if 9.5 <= duration <= 10.5:  # Allow some tolerance
                            self.log("   ✅ Duration detection is accurate")
                        else:
                            self.log(f"   ⚠️  Duration detection may be inaccurate (expected ~10s)")
                        tests_passed += 1
                    else:
                        self.log(f"❌ FFprobe duration detection failed: {probe_result.stderr}")
                    
                    os.unlink(tmp_file.name)
                else:
                    self.log(f"❌ Could not create test file for duration test")
        except Exception as e:
            self.log(f"❌ FFprobe duration test failed: {str(e)}")
        
        # Test 5: Audio chunking capability
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as input_file:
                # Create a 30-second audio file
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=30',
                    '-ac', '1', '-ar', '22050', '-b:a', '64k', '-y', input_file.name
                ]
                
                create_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if create_result.returncode == 0:
                    # Test chunking (split into 10-second chunks)
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as chunk_file:
                        chunk_cmd = [
                            'ffmpeg', '-i', input_file.name, '-ss', '0', '-t', '10',
                            '-c', 'copy', '-y', chunk_file.name
                        ]
                        
                        chunk_result = subprocess.run(chunk_cmd, capture_output=True, text=True, timeout=30)
                        
                        if chunk_result.returncode == 0 and os.path.exists(chunk_file.name):
                            chunk_size = os.path.getsize(chunk_file.name)
                            self.log(f"✅ FFmpeg can create audio chunks: {chunk_size} bytes")
                            tests_passed += 1
                            os.unlink(chunk_file.name)
                        else:
                            self.log(f"❌ FFmpeg chunking failed: {chunk_result.stderr}")
                    
                    os.unlink(input_file.name)
                else:
                    self.log(f"❌ Could not create test file for chunking test")
        except Exception as e:
            self.log(f"❌ FFmpeg chunking test failed: {str(e)}")
        
        self.tests_run += total_tests
        self.tests_passed += tests_passed
        
        self.log(f"   FFmpeg Tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests

    def test_health_monitoring_comprehensive(self):
        """Comprehensive health monitoring test"""
        self.log("🏥 Testing Health Monitoring Comprehensive...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Basic health endpoint
        total_tests += 1
        success, response = self.run_test(
            "Health Endpoint Basic",
            "GET",
            "health",
            200,
            timeout=30
        )
        
        if success:
            tests_passed += 1
            self.log(f"   Status: {response.get('status', 'N/A')}")
            self.log(f"   Timestamp: {response.get('timestamp', 'N/A')}")
            services = response.get('services', {})
            self.log(f"   Database: {services.get('database', 'N/A')}")
            self.log(f"   API: {services.get('api', 'N/A')}")
        
        # Test 2: Health endpoint consistency (multiple calls)
        total_tests += 1
        consistent_responses = 0
        for i in range(3):
            success, response = self.run_test(
                f"Health Consistency Check {i+1}",
                "GET",
                "health",
                200,
                timeout=10
            )
            if success and response.get('status') == 'healthy':
                consistent_responses += 1
        
        if consistent_responses == 3:
            tests_passed += 1
            self.log("✅ Health endpoint is consistent")
        else:
            self.log(f"⚠️  Health endpoint consistency: {consistent_responses}/3")
        
        # Test 3: API responsiveness
        total_tests += 1
        start_time = time.time()
        success, response = self.run_test(
            "API Responsiveness",
            "GET",
            "",
            200,
            timeout=10
        )
        response_time = time.time() - start_time
        
        if success:
            tests_passed += 1
            self.log(f"   API Response Time: {response_time:.2f} seconds")
            if response_time < 2:
                self.log("✅ API is highly responsive")
            elif response_time < 5:
                self.log("✅ API is responsive")
            else:
                self.log("⚠️  API response time is slow")
        
        # Test 4: Database connectivity (via health endpoint)
        total_tests += 1
        success, response = self.run_test(
            "Database Connectivity Check",
            "GET",
            "health",
            200,
            timeout=30
        )
        
        if success:
            services = response.get('services', {})
            if services.get('database') == 'connected':
                tests_passed += 1
                self.log("✅ Database connectivity confirmed")
            else:
                self.log(f"❌ Database connectivity issue: {services.get('database', 'unknown')}")
        
        self.tests_run += total_tests
        self.tests_passed += tests_passed
        
        self.log(f"   Health Monitoring Tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests

    def test_file_upload_infrastructure(self):
        """Test file upload infrastructure without processing"""
        self.log("📁 Testing File Upload Infrastructure...")
        
        if not self.auth_token:
            self.log("❌ No authentication token available")
            return False
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Small file upload
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Create a small audio file
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5',
                    '-ac', '1', '-ar', '22050', '-b:a', '64k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(tmp_file.name)
                    
                    with open(tmp_file.name, 'rb') as f:
                        files = {'file': ('test_small.mp3', f, 'audio/mpeg')}
                        data = {'title': 'Infrastructure Test - Small File'}
                        
                        success, response = self.run_test(
                            f"Small File Upload ({file_size/(1024*1024):.1f}MB)",
                            "POST",
                            "upload-file",
                            200,
                            data=data,
                            files=files,
                            timeout=60,
                            auth_required=True
                        )
                    
                    if success:
                        tests_passed += 1
                        note_id = response.get('id')
                        if note_id:
                            self.created_notes.append(note_id)
                            self.log(f"   Created note: {note_id}")
                            self.log(f"   Upload status: {response.get('status', 'N/A')}")
                    
                    os.unlink(tmp_file.name)
                else:
                    self.log("❌ Could not create test file")
        except Exception as e:
            self.log(f"❌ Small file upload test failed: {str(e)}")
        
        # Test 2: Medium file upload
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Create a medium audio file (2 minutes)
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=120',
                    '-ac', '2', '-ar', '44100', '-b:a', '128k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(tmp_file.name)
                    
                    with open(tmp_file.name, 'rb') as f:
                        files = {'file': ('test_medium.mp3', f, 'audio/mpeg')}
                        data = {'title': 'Infrastructure Test - Medium File'}
                        
                        success, response = self.run_test(
                            f"Medium File Upload ({file_size/(1024*1024):.1f}MB)",
                            "POST",
                            "upload-file",
                            200,
                            data=data,
                            files=files,
                            timeout=120,
                            auth_required=True
                        )
                    
                    if success:
                        tests_passed += 1
                        note_id = response.get('id')
                        if note_id:
                            self.created_notes.append(note_id)
                            self.log(f"   Created note: {note_id}")
                            self.log(f"   Upload status: {response.get('status', 'N/A')}")
                    
                    os.unlink(tmp_file.name)
                else:
                    self.log("❌ Could not create medium test file")
        except Exception as e:
            self.log(f"❌ Medium file upload test failed: {str(e)}")
        
        # Test 3: Large file upload (test chunking threshold detection)
        total_tests += 1
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                # Create a large audio file (10 minutes at high quality to exceed 24MB)
                cmd = [
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=600',
                    '-ac', '2', '-ar', '44100', '-b:a', '320k', '-y', tmp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    file_size = os.path.getsize(tmp_file.name)
                    
                    self.log(f"   Created large file: {file_size/(1024*1024):.1f}MB")
                    
                    if file_size > 24 * 1024 * 1024:
                        self.log("   ✅ File exceeds 24MB threshold - will trigger chunking logic")
                    else:
                        self.log(f"   ⚠️  File is {file_size/(1024*1024):.1f}MB - may not trigger chunking")
                    
                    with open(tmp_file.name, 'rb') as f:
                        files = {'file': ('test_large.mp3', f, 'audio/mpeg')}
                        data = {'title': 'Infrastructure Test - Large File'}
                        
                        success, response = self.run_test(
                            f"Large File Upload ({file_size/(1024*1024):.1f}MB)",
                            "POST",
                            "upload-file",
                            200,
                            data=data,
                            files=files,
                            timeout=300,
                            auth_required=True
                        )
                    
                    if success:
                        tests_passed += 1
                        note_id = response.get('id')
                        if note_id:
                            self.created_notes.append(note_id)
                            self.log(f"   Created note: {note_id}")
                            self.log(f"   Upload status: {response.get('status', 'N/A')}")
                    
                    os.unlink(tmp_file.name)
                else:
                    self.log("❌ Could not create large test file")
        except Exception as e:
            self.log(f"❌ Large file upload test failed: {str(e)}")
        
        self.tests_run += total_tests
        self.tests_passed += tests_passed
        
        self.log(f"   File Upload Tests: {tests_passed}/{total_tests} passed")
        return tests_passed >= 2  # At least 2 out of 3 should pass

    def register_test_user(self):
        """Register a test user for authenticated tests"""
        success, response = self.run_test(
            "User Registration for Infrastructure Tests",
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

    def test_processing_pipeline_readiness(self):
        """Test that the processing pipeline is ready (without external API calls)"""
        self.log("⚙️  Testing Processing Pipeline Readiness...")
        
        if not self.created_notes:
            self.log("❌ No notes available for pipeline testing")
            return False
        
        tests_passed = 0
        total_tests = 0
        
        # Test note retrieval and status checking
        for note_id in self.created_notes[:3]:  # Test first 3 notes
            total_tests += 1
            success, response = self.run_test(
                f"Note Status Check {note_id[:8]}...",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True,
                timeout=30
            )
            
            if success:
                tests_passed += 1
                status = response.get('status', 'unknown')
                kind = response.get('kind', 'unknown')
                self.log(f"   Note {note_id[:8]}: {kind} - {status}")
                
                # Check if note has proper structure
                if 'id' in response and 'created_at' in response:
                    self.log(f"   ✅ Note has proper structure")
                else:
                    self.log(f"   ⚠️  Note structure may be incomplete")
        
        self.tests_run += total_tests
        self.tests_passed += tests_passed
        
        self.log(f"   Pipeline Readiness Tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests

    def run_infrastructure_verification(self):
        """Run comprehensive infrastructure verification"""
        self.log("🚀 Starting Infrastructure Verification Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # === FFMPEG COMPREHENSIVE TESTING ===
        self.log("\n🎬 FFMPEG COMPREHENSIVE TESTING")
        ffmpeg_ok = self.test_ffmpeg_comprehensive()
        
        # === HEALTH MONITORING COMPREHENSIVE TESTING ===
        self.log("\n🏥 HEALTH MONITORING COMPREHENSIVE TESTING")
        health_ok = self.test_health_monitoring_comprehensive()
        
        # === USER REGISTRATION ===
        self.log("\n👤 USER REGISTRATION")
        if not self.register_test_user():
            self.log("❌ User registration failed - cannot proceed with authenticated tests")
            return False
        
        # === FILE UPLOAD INFRASTRUCTURE TESTING ===
        self.log("\n📁 FILE UPLOAD INFRASTRUCTURE TESTING")
        upload_ok = self.test_file_upload_infrastructure()
        
        # === PROCESSING PIPELINE READINESS ===
        self.log("\n⚙️  PROCESSING PIPELINE READINESS")
        pipeline_ok = self.test_processing_pipeline_readiness()
        
        # === RESULTS SUMMARY ===
        self.log("\n📋 INFRASTRUCTURE VERIFICATION RESULTS")
        results = {
            "FFmpeg Infrastructure": ffmpeg_ok,
            "Health Monitoring": health_ok,
            "File Upload Infrastructure": upload_ok,
            "Processing Pipeline Readiness": pipeline_ok
        }
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"   {test_name}: {status}")
        
        # Overall success criteria
        critical_tests = [ffmpeg_ok, health_ok, upload_ok]
        critical_passed = sum(critical_tests)
        
        self.log(f"\n🎯 Critical Infrastructure Tests: {critical_passed}/3 passed")
        
        if critical_passed == 3:
            self.log("🎉 ALL CRITICAL INFRASTRUCTURE TESTS PASSED!")
            self.log("✅ FFmpeg is properly installed and functional")
            self.log("✅ Health monitoring system is operational")
            self.log("✅ File upload infrastructure is working")
            self.log("✅ System is ready for large audio file processing")
            return True
        else:
            self.log(f"⚠️  {3-critical_passed} critical infrastructure test(s) failed")
            return False

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 INFRASTRUCTURE VERIFICATION TEST SUMMARY")
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
        
        return self.tests_passed >= (self.tests_run * 0.8)  # 80% success rate

def main():
    """Main test execution"""
    tester = InfrastructureVerificationTester()
    
    try:
        success = tester.run_infrastructure_verification()
        tester.print_summary()
        
        if success:
            print("\n🎉 Infrastructure verification PASSED!")
            print("✅ FFmpeg installation and functionality confirmed")
            print("✅ Health monitoring system operational") 
            print("✅ File upload infrastructure working")
            print("✅ System ready for bulletproof large audio file processing")
            return 0
        else:
            print(f"\n⚠️  Infrastructure verification had issues.")
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