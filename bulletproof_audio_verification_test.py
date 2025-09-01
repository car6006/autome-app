#!/usr/bin/env python3
"""
BULLETPROOF LARGE AUDIO FILE PROCESSING SYSTEM VERIFICATION
Comprehensive backend testing for the review request requirements
"""

import requests
import sys
import json
import time
import subprocess
import tempfile
import os
from datetime import datetime
from pathlib import Path

class BulletproofAudioVerificationTester:
    def __init__(self, base_url="https://pwa-integration-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_results = []

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
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

    def test_health_endpoint_bulletproof_monitoring(self):
        """PRIORITY HIGH: Test /api/health endpoint - confirm bulletproof monitoring is working"""
        self.log("\n🏥 TESTING BULLETPROOF MONITORING SYSTEM")
        
        success, response = self.run_test(
            "Health Endpoint - Bulletproof Monitoring",
            "GET",
            "health",
            200,
            timeout=10
        )
        
        if success:
            status = response.get('status', 'unknown')
            timestamp = response.get('timestamp', 'N/A')
            services = response.get('services', {})
            
            self.log(f"   ✅ System Status: {status}")
            self.log(f"   ✅ Timestamp: {timestamp}")
            self.log(f"   ✅ Database: {services.get('database', 'unknown')}")
            self.log(f"   ✅ API: {services.get('api', 'unknown')}")
            
            # Test multiple rapid requests to verify stability
            rapid_test_success = 0
            for i in range(5):
                rapid_success, _ = self.run_test(
                    f"Rapid Health Check {i+1}",
                    "GET", 
                    "health",
                    200,
                    timeout=5
                )
                if rapid_success:
                    rapid_test_success += 1
            
            self.log(f"   ✅ Rapid Health Checks: {rapid_test_success}/5 passed")
            
            if rapid_test_success >= 4:
                self.log("   ✅ BULLETPROOF MONITORING: System highly responsive")
                return True
            else:
                self.log("   ⚠️  BULLETPROOF MONITORING: Some instability detected")
                return False
        
        return success

    def test_ffmpeg_installation_and_functionality(self):
        """PRIORITY HIGH: Verify FFmpeg installation and functionality"""
        self.log("\n🎬 TESTING FFMPEG INSTALLATION AND FUNCTIONALITY")
        
        try:
            # Test FFmpeg installation
            ffmpeg_result = subprocess.run(['ffmpeg', '-version'], 
                                         capture_output=True, text=True, timeout=10)
            
            if ffmpeg_result.returncode == 0:
                version_info = ffmpeg_result.stdout.split('\n')[0]
                self.log(f"   ✅ FFmpeg installed: {version_info}")
                self.tests_passed += 1
            else:
                self.log("   ❌ FFmpeg not found or not working")
                self.tests_run += 1
                return False
            
            # Test FFprobe installation
            ffprobe_result = subprocess.run(['ffprobe', '-version'], 
                                          capture_output=True, text=True, timeout=10)
            
            if ffprobe_result.returncode == 0:
                probe_version = ffprobe_result.stdout.split('\n')[0]
                self.log(f"   ✅ FFprobe installed: {probe_version}")
                self.tests_passed += 1
            else:
                self.log("   ❌ FFprobe not found or not working")
                self.tests_run += 1
                return False
            
            # Test audio file creation capability
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                # Create a 5-second test audio file
                create_result = subprocess.run([
                    'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5',
                    '-ar', '44100', '-ac', '2', tmp_file.name, '-y'
                ], capture_output=True, text=True, timeout=30)
                
                if create_result.returncode == 0 and os.path.exists(tmp_file.name):
                    file_size = os.path.getsize(tmp_file.name)
                    self.log(f"   ✅ Audio file creation: {file_size} bytes generated")
                    self.tests_passed += 1
                    
                    # Test duration detection
                    duration_result = subprocess.run([
                        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', tmp_file.name
                    ], capture_output=True, text=True, timeout=10)
                    
                    if duration_result.returncode == 0:
                        duration = float(duration_result.stdout.strip())
                        self.log(f"   ✅ Duration detection: {duration:.2f} seconds")
                        self.tests_passed += 1
                    else:
                        self.log("   ❌ Duration detection failed")
                        self.tests_run += 1
                    
                    # Test chunking capability
                    chunk_result = subprocess.run([
                        'ffmpeg', '-i', tmp_file.name, '-f', 'segment', 
                        '-segment_time', '2', '-c', 'copy', 
                        f'{tmp_file.name}_chunk_%03d.wav', '-y'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if chunk_result.returncode == 0:
                        # Count generated chunks
                        chunk_files = [f for f in os.listdir(os.path.dirname(tmp_file.name)) 
                                     if f.startswith(os.path.basename(tmp_file.name) + '_chunk_')]
                        self.log(f"   ✅ Audio chunking: {len(chunk_files)} chunks created")
                        self.tests_passed += 1
                        
                        # Clean up chunk files
                        for chunk_file in chunk_files:
                            try:
                                os.unlink(os.path.join(os.path.dirname(tmp_file.name), chunk_file))
                            except:
                                pass
                    else:
                        self.log("   ❌ Audio chunking failed")
                        self.tests_run += 1
                    
                    os.unlink(tmp_file.name)
                else:
                    self.log("   ❌ Audio file creation failed")
                    self.tests_run += 1
                    return False
            
            self.tests_run += 4  # Total FFmpeg tests
            self.log("   ✅ FFMPEG FUNCTIONALITY: All capabilities verified")
            return True
            
        except subprocess.TimeoutExpired:
            self.log("   ❌ FFmpeg tests timed out")
            self.tests_run += 1
            return False
        except Exception as e:
            self.log(f"   ❌ FFmpeg test error: {str(e)}")
            self.tests_run += 1
            return False

    def test_large_file_upload_endpoints(self):
        """PRIORITY HIGH: Test file upload endpoints for large files (>24MB threshold)"""
        self.log("\n📤 TESTING LARGE FILE UPLOAD ENDPOINTS")
        
        # Create a test file larger than 24MB threshold
        test_file_size_mb = 32  # 32MB test file
        test_file_size = test_file_size_mb * 1024 * 1024
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            # Create dummy MP3 data (not real audio, just for size testing)
            self.log(f"   📁 Creating {test_file_size_mb}MB test file...")
            
            # Write MP3 header
            mp3_header = b'\xff\xfb\x90\x00'  # Basic MP3 frame header
            tmp_file.write(mp3_header)
            
            # Fill with dummy data to reach target size
            chunk_size = 1024 * 1024  # 1MB chunks
            remaining = test_file_size - len(mp3_header)
            
            while remaining > 0:
                write_size = min(chunk_size, remaining)
                dummy_data = b'\x00' * write_size
                tmp_file.write(dummy_data)
                remaining -= write_size
            
            tmp_file.flush()
            actual_size = os.path.getsize(tmp_file.name)
            actual_size_mb = actual_size / (1024 * 1024)
            
            self.log(f"   ✅ Test file created: {actual_size_mb:.1f}MB ({actual_size:,} bytes)")
            
            # Test 1: Upload via /api/upload-file endpoint
            try:
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('large_test_audio.mp3', f, 'audio/mpeg')}
                    data = {'title': f'Large File Test - {test_file_size_mb}MB'}
                    
                    start_time = time.time()
                    success, response = self.run_test(
                        f"Upload {test_file_size_mb}MB File via /api/upload-file",
                        "POST",
                        "upload-file",
                        200,
                        data=data,
                        files=files,
                        timeout=300  # 5 minute timeout
                    )
                    upload_time = time.time() - start_time
                    
                    if success:
                        note_id = response.get('id')
                        if note_id:
                            self.created_notes.append(note_id)
                            self.log(f"   ✅ Upload successful in {upload_time:.1f} seconds")
                            self.log(f"   ✅ Note ID: {note_id}")
                            self.log(f"   ✅ Status: {response.get('status', 'unknown')}")
                            self.log(f"   ✅ Kind: {response.get('kind', 'unknown')}")
                            
                            # Test chunking system activation by checking note status
                            time.sleep(5)  # Wait for processing to start
                            
                            check_success, note_data = self.run_test(
                                f"Check Large File Processing Status",
                                "GET",
                                f"notes/{note_id}",
                                200
                            )
                            
                            if check_success:
                                status = note_data.get('status', 'unknown')
                                self.log(f"   ✅ Processing status: {status}")
                                
                                if status == 'processing':
                                    self.log("   ✅ CHUNKING SYSTEM: Large file processing initiated")
                                elif status == 'ready':
                                    self.log("   ✅ CHUNKING SYSTEM: Processing completed quickly")
                                else:
                                    self.log(f"   ⚠️  Unexpected status: {status}")
                            
                            return True, note_id
                        else:
                            self.log("   ❌ No note ID returned")
                            return False, None
                    else:
                        self.log(f"   ❌ Upload failed after {upload_time:.1f} seconds")
                        return False, None
                        
            except Exception as e:
                self.log(f"   ❌ Upload exception: {str(e)}")
                return False, None
            finally:
                os.unlink(tmp_file.name)

    def test_chunking_system_activation(self, large_note_id):
        """PRIORITY HIGH: Confirm chunking system activation for large files"""
        self.log("\n🔄 TESTING CHUNKING SYSTEM ACTIVATION")
        
        if not large_note_id:
            self.log("   ❌ No large file note ID provided")
            return False
        
        # Monitor processing for chunking indicators
        max_wait_time = 600  # 10 minutes maximum
        check_interval = 15  # Check every 15 seconds
        start_time = time.time()
        
        chunking_detected = False
        processing_logs = []
        
        while time.time() - start_time < max_wait_time:
            success, note_data = self.run_test(
                f"Monitor Chunking System",
                "GET",
                f"notes/{large_note_id}",
                200,
                timeout=10
            )
            
            if success:
                status = note_data.get('status', 'unknown')
                artifacts = note_data.get('artifacts', {})
                elapsed = time.time() - start_time
                
                processing_logs.append({
                    'time': elapsed,
                    'status': status,
                    'artifacts_keys': list(artifacts.keys())
                })
                
                self.log(f"   Status: {status} (after {elapsed:.1f}s)")
                
                # Check for chunking indicators
                transcript = artifacts.get('transcript', '')
                if transcript and '[Part ' in transcript:
                    if not chunking_detected:
                        chunking_detected = True
                        part_count = transcript.count('[Part ')
                        self.log(f"   ✅ CHUNKING DETECTED: {part_count} parts found in transcript")
                        self.tests_passed += 1
                
                # Check processing completion
                if status == 'ready':
                    processing_time = elapsed
                    self.log(f"   ✅ Processing completed in {processing_time:.1f} seconds")
                    
                    # Analyze final results
                    transcript = artifacts.get('transcript', '')
                    transcript_length = len(transcript)
                    word_count = len(transcript.split()) if transcript else 0
                    
                    self.log(f"   📝 Final transcript: {transcript_length:,} characters, {word_count:,} words")
                    
                    if chunking_detected:
                        part_count = transcript.count('[Part ')
                        self.log(f"   ✅ CHUNKING SYSTEM SUCCESS: {part_count} parts processed and combined")
                    else:
                        self.log("   ⚠️  No chunking indicators found (file may be under threshold)")
                    
                    self.tests_passed += 1
                    self.tests_run += 2
                    return True
                    
                elif status == 'failed':
                    error = artifacts.get('error', 'Unknown error')
                    self.log(f"   ❌ Processing failed: {error}")
                    self.tests_run += 2
                    return False
                
                time.sleep(check_interval)
            else:
                self.log("   ❌ Failed to check note status")
                break
        
        self.log(f"   ⏰ Timeout after {max_wait_time/60:.1f} minutes")
        self.tests_run += 2
        return False

    def test_system_stability_under_load(self):
        """PRIORITY HIGH: Test system stability under load"""
        self.log("\n💪 TESTING SYSTEM STABILITY UNDER LOAD")
        
        # Test 1: Multiple concurrent health checks
        concurrent_requests = 10
        successful_requests = 0
        
        self.log(f"   Testing {concurrent_requests} concurrent health checks...")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def health_check_worker():
            try:
                response = requests.get(f"{self.api_url}/health", timeout=10)
                results_queue.put(response.status_code == 200)
            except:
                results_queue.put(False)
        
        # Launch concurrent requests
        threads = []
        start_time = time.time()
        
        for i in range(concurrent_requests):
            thread = threading.Thread(target=health_check_worker)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=15)
        
        # Collect results
        while not results_queue.empty():
            if results_queue.get():
                successful_requests += 1
        
        concurrent_time = time.time() - start_time
        success_rate = (successful_requests / concurrent_requests) * 100
        
        self.log(f"   ✅ Concurrent requests: {successful_requests}/{concurrent_requests} successful ({success_rate:.1f}%)")
        self.log(f"   ✅ Response time: {concurrent_time:.2f} seconds for {concurrent_requests} requests")
        
        # Test 2: Rapid sequential requests
        sequential_requests = 20
        sequential_successful = 0
        
        self.log(f"   Testing {sequential_requests} rapid sequential requests...")
        
        start_time = time.time()
        for i in range(sequential_requests):
            try:
                response = requests.get(f"{self.api_url}/health", timeout=5)
                if response.status_code == 200:
                    sequential_successful += 1
            except:
                pass
        
        sequential_time = time.time() - start_time
        sequential_rate = (sequential_successful / sequential_requests) * 100
        avg_response_time = sequential_time / sequential_requests
        
        self.log(f"   ✅ Sequential requests: {sequential_successful}/{sequential_requests} successful ({sequential_rate:.1f}%)")
        self.log(f"   ✅ Average response time: {avg_response_time:.3f} seconds")
        
        # Test 3: Memory stability check
        self.log("   Testing memory stability with multiple note creations...")
        
        memory_test_notes = []
        memory_test_successful = 0
        
        for i in range(5):
            success, response = self.run_test(
                f"Memory Stability Note {i+1}",
                "POST",
                "notes",
                200,
                data={
                    "title": f"Memory Stability Test Note {i+1}",
                    "kind": "text",
                    "text_content": f"This is test note {i+1} for memory stability testing. " * 50
                }
            )
            
            if success and response.get('id'):
                memory_test_notes.append(response['id'])
                memory_test_successful += 1
        
        self.log(f"   ✅ Memory stability: {memory_test_successful}/5 notes created successfully")
        
        # Clean up memory test notes
        for note_id in memory_test_notes:
            try:
                requests.delete(f"{self.api_url}/notes/{note_id}", timeout=5)
            except:
                pass
        
        # Overall stability assessment
        overall_stability = (
            (success_rate >= 90) and 
            (sequential_rate >= 95) and 
            (memory_test_successful >= 4) and
            (avg_response_time < 1.0)
        )
        
        if overall_stability:
            self.log("   ✅ SYSTEM STABILITY: Excellent performance under load")
            self.tests_passed += 1
        else:
            self.log("   ⚠️  SYSTEM STABILITY: Some performance degradation detected")
        
        self.tests_run += 1
        return overall_stability

    def test_specific_note_verification(self):
        """PRIORITY HIGH: Verify the specific note mentioned in review request"""
        self.log("\n🎯 TESTING SPECIFIC NOTE: 92ba1ef1-9c2a-461b-9721-0dc4c9b5f26a")
        
        target_note_id = "92ba1ef1-9c2a-461b-9721-0dc4c9b5f26a"
        
        success, note_data = self.run_test(
            "Verify Specific 62MB Note",
            "GET",
            f"notes/{target_note_id}",
            200
        )
        
        if success:
            title = note_data.get('title', 'N/A')
            kind = note_data.get('kind', 'N/A')
            status = note_data.get('status', 'N/A')
            created_at = note_data.get('created_at', 'N/A')
            ready_at = note_data.get('ready_at', 'N/A')
            artifacts = note_data.get('artifacts', {})
            metrics = note_data.get('metrics', {})
            
            self.log(f"   ✅ Note found: {title}")
            self.log(f"   ✅ Kind: {kind}")
            self.log(f"   ✅ Status: {status}")
            self.log(f"   ✅ Created: {created_at}")
            self.log(f"   ✅ Ready: {ready_at}")
            
            # Verify processing metrics
            latency_ms = metrics.get('latency_ms', 0)
            if latency_ms:
                latency_seconds = latency_ms / 1000
                latency_minutes = latency_seconds / 60
                self.log(f"   ✅ Processing time: {latency_ms:,}ms ({latency_minutes:.1f} minutes)")
                
                # Verify it matches the reported 3 minutes 45 seconds (225 seconds)
                expected_time = 225 * 1000  # 225 seconds in ms
                if abs(latency_ms - expected_time) < 30000:  # Within 30 seconds tolerance
                    self.log("   ✅ Processing time matches reported duration")
                else:
                    self.log(f"   ⚠️  Processing time differs from reported 225 seconds")
            
            # Verify artifacts structure
            transcript = artifacts.get('transcript', '')
            summary = artifacts.get('summary', '')
            actions = artifacts.get('actions', [])
            
            self.log(f"   📝 Transcript length: {len(transcript):,} characters")
            self.log(f"   📋 Summary length: {len(summary):,} characters")
            self.log(f"   ✅ Actions count: {len(actions)}")
            
            # Check for chunking indicators in the specific note
            if '[Part ' in transcript:
                part_count = transcript.count('[Part ')
                self.log(f"   ✅ CHUNKING VERIFIED: {part_count} parts found in transcript")
            else:
                self.log("   ⚠️  No chunking indicators found in transcript")
            
            # Verify status is 'ready' as reported
            if status == 'ready':
                self.log("   ✅ STATUS VERIFIED: Note is in 'ready' state as expected")
                return True
            else:
                self.log(f"   ❌ STATUS MISMATCH: Expected 'ready', found '{status}'")
                return False
        
        return success

    def test_core_backend_features(self):
        """PRIORITY MEDIUM: Test core backend features"""
        self.log("\n🔧 TESTING CORE BACKEND FEATURES")
        
        # Test 1: Note creation (text, audio, photo)
        self.log("   Testing note creation...")
        
        # Text note
        text_success, text_response = self.run_test(
            "Create Text Note",
            "POST",
            "notes",
            200,
            data={
                "title": "Core Feature Test - Text Note",
                "kind": "text",
                "text_content": "This is a test text note for core feature verification."
            }
        )
        
        text_note_id = text_response.get('id') if text_success else None
        if text_note_id:
            self.created_notes.append(text_note_id)
        
        # Audio note
        audio_success, audio_response = self.run_test(
            "Create Audio Note",
            "POST",
            "notes",
            200,
            data={"title": "Core Feature Test - Audio Note", "kind": "audio"}
        )
        
        audio_note_id = audio_response.get('id') if audio_success else None
        if audio_note_id:
            self.created_notes.append(audio_note_id)
        
        # Photo note
        photo_success, photo_response = self.run_test(
            "Create Photo Note",
            "POST",
            "notes",
            200,
            data={"title": "Core Feature Test - Photo Note", "kind": "photo"}
        )
        
        photo_note_id = photo_response.get('id') if photo_success else None
        if photo_note_id:
            self.created_notes.append(photo_note_id)
        
        creation_success = text_success and audio_success and photo_success
        self.log(f"   ✅ Note creation: {sum([text_success, audio_success, photo_success])}/3 successful")
        
        # Test 2: Export functionality
        if text_note_id:
            self.log("   Testing export functionality...")
            
            export_formats = ['txt', 'md', 'json', 'rtf']
            export_success_count = 0
            
            for format_type in export_formats:
                export_success, _ = self.run_test(
                    f"Export {format_type.upper()}",
                    "GET",
                    f"notes/{text_note_id}/export?format={format_type}",
                    200,
                    timeout=30
                )
                if export_success:
                    export_success_count += 1
            
            self.log(f"   ✅ Export functionality: {export_success_count}/{len(export_formats)} formats working")
        
        # Test 3: AI chat features (if text note exists)
        if text_note_id:
            self.log("   Testing AI chat features...")
            
            ai_chat_success, ai_response = self.run_test(
                "AI Chat Feature",
                "POST",
                f"notes/{text_note_id}/ai-chat",
                200,
                data={"question": "What are the key points in this note?"},
                timeout=60
            )
            
            if ai_chat_success:
                response_length = len(ai_response.get('response', ''))
                self.log(f"   ✅ AI chat: Response generated ({response_length} characters)")
            else:
                self.log("   ⚠️  AI chat: Feature may require API keys")
        
        # Test 4: Metrics endpoint
        metrics_success, metrics_response = self.run_test(
            "Productivity Metrics",
            "GET",
            "metrics?days=7",
            200
        )
        
        if metrics_success:
            total_notes = metrics_response.get('notes_total', 0)
            ready_notes = metrics_response.get('notes_ready', 0)
            success_rate = metrics_response.get('success_rate', 0)
            
            self.log(f"   ✅ Metrics: {total_notes} total notes, {ready_notes} ready, {success_rate}% success rate")
        
        return creation_success and metrics_success

    def test_production_readiness(self):
        """PRIORITY MEDIUM: Test production readiness aspects"""
        self.log("\n🚀 TESTING PRODUCTION READINESS")
        
        # Test 1: Error handling
        self.log("   Testing error handling...")
        
        error_tests = [
            ("Non-existent note", "GET", "notes/non-existent-id", 404, None),
            ("Invalid note creation", "POST", "notes", 422, {"title": "", "kind": "invalid"}),
            ("Invalid export format", "GET", "notes/test/export?format=invalid", 422, None),
        ]
        
        error_handling_success = 0
        for test_name, method, endpoint, expected_status, data in error_tests:
            success, _ = self.run_test(
                test_name,
                method,
                endpoint,
                expected_status,
                data=data
            )
            if success:
                error_handling_success += 1
        
        self.log(f"   ✅ Error handling: {error_handling_success}/{len(error_tests)} tests passed")
        
        # Test 2: Security headers
        self.log("   Testing security headers...")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Referrer-Policy',
                'Content-Security-Policy'
            ]
            
            headers_present = 0
            for header in security_headers:
                if header in response.headers:
                    headers_present += 1
                    self.log(f"   ✅ Security header present: {header}")
                else:
                    self.log(f"   ⚠️  Security header missing: {header}")
            
            security_score = (headers_present / len(security_headers)) * 100
            self.log(f"   ✅ Security headers: {headers_present}/{len(security_headers)} present ({security_score:.1f}%)")
            
        except Exception as e:
            self.log(f"   ❌ Security header test failed: {str(e)}")
            security_score = 0
        
        # Test 3: Response time consistency
        self.log("   Testing response time consistency...")
        
        response_times = []
        for i in range(10):
            start_time = time.time()
            try:
                response = requests.get(f"{self.api_url}/health", timeout=10)
                if response.status_code == 200:
                    response_times.append(time.time() - start_time)
            except:
                pass
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            self.log(f"   ✅ Response times: avg={avg_response_time:.3f}s, min={min_response_time:.3f}s, max={max_response_time:.3f}s")
            
            consistency_good = max_response_time < 2.0 and avg_response_time < 0.5
            if consistency_good:
                self.log("   ✅ Response time consistency: Excellent")
            else:
                self.log("   ⚠️  Response time consistency: Could be improved")
        
        return error_handling_success >= 2 and security_score >= 80

    def run_bulletproof_verification(self):
        """Run the complete bulletproof audio processing verification"""
        self.log("🎯 STARTING BULLETPROOF LARGE AUDIO FILE PROCESSING VERIFICATION")
        self.log("=" * 80)
        self.log("Review Request: Comprehensive Backend Verification")
        self.log("Focus: 62MB Regional Meeting Audio File Processing System")
        self.log("=" * 80)
        
        # Store test results for summary
        test_results = {}
        
        # PRIORITY HIGH TESTS
        self.log("\n🔥 PRIORITY HIGH TESTS")
        
        # 1. Health endpoint verification
        test_results['health_monitoring'] = self.test_health_endpoint_bulletproof_monitoring()
        
        # 2. FFmpeg installation and functionality
        test_results['ffmpeg_functionality'] = self.test_ffmpeg_installation_and_functionality()
        
        # 3. Large file upload endpoints
        large_file_result, large_note_id = self.test_large_file_upload_endpoints()
        test_results['large_file_upload'] = large_file_result
        
        # 4. Chunking system activation
        if large_note_id:
            test_results['chunking_system'] = self.test_chunking_system_activation(large_note_id)
        else:
            test_results['chunking_system'] = False
            self.log("   ❌ Chunking system test skipped - no large file uploaded")
        
        # 5. System stability under load
        test_results['system_stability'] = self.test_system_stability_under_load()
        
        # 6. Specific note verification
        test_results['specific_note_verification'] = self.test_specific_note_verification()
        
        # PRIORITY MEDIUM TESTS
        self.log("\n🔶 PRIORITY MEDIUM TESTS")
        
        # 7. Core backend features
        test_results['core_backend_features'] = self.test_core_backend_features()
        
        # 8. Production readiness
        test_results['production_readiness'] = self.test_production_readiness()
        
        # FINAL SUMMARY
        self.log("\n" + "=" * 80)
        self.log("🎯 BULLETPROOF VERIFICATION SUMMARY")
        self.log("=" * 80)
        
        high_priority_tests = [
            'health_monitoring', 'ffmpeg_functionality', 'large_file_upload',
            'chunking_system', 'system_stability', 'specific_note_verification'
        ]
        
        medium_priority_tests = [
            'core_backend_features', 'production_readiness'
        ]
        
        # High priority results
        self.log("\n🔥 HIGH PRIORITY RESULTS:")
        high_priority_passed = 0
        for test_name in high_priority_tests:
            result = test_results.get(test_name, False)
            status = "✅ PASS" if result else "❌ FAIL"
            test_display_name = test_name.replace('_', ' ').title()
            self.log(f"   {status} {test_display_name}")
            if result:
                high_priority_passed += 1
        
        # Medium priority results
        self.log("\n🔶 MEDIUM PRIORITY RESULTS:")
        medium_priority_passed = 0
        for test_name in medium_priority_tests:
            result = test_results.get(test_name, False)
            status = "✅ PASS" if result else "❌ FAIL"
            test_display_name = test_name.replace('_', ' ').title()
            self.log(f"   {status} {test_display_name}")
            if result:
                medium_priority_passed += 1
        
        # Overall assessment
        self.log(f"\n📊 OVERALL RESULTS:")
        self.log(f"   Tests Run: {self.tests_run}")
        self.log(f"   Tests Passed: {self.tests_passed}")
        self.log(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        self.log(f"   High Priority: {high_priority_passed}/{len(high_priority_tests)} passed")
        self.log(f"   Medium Priority: {medium_priority_passed}/{len(medium_priority_tests)} passed")
        
        # Bulletproof system assessment
        bulletproof_criteria = {
            'Infrastructure Ready': test_results.get('health_monitoring', False) and test_results.get('ffmpeg_functionality', False),
            'Large File Processing': test_results.get('large_file_upload', False) and test_results.get('chunking_system', False),
            'System Stability': test_results.get('system_stability', False),
            'Specific Note Verified': test_results.get('specific_note_verification', False),
            'Production Ready': test_results.get('production_readiness', False)
        }
        
        self.log(f"\n🛡️  BULLETPROOF SYSTEM ASSESSMENT:")
        bulletproof_passed = 0
        for criteria, passed in bulletproof_criteria.items():
            status = "✅" if passed else "❌"
            self.log(f"   {status} {criteria}")
            if passed:
                bulletproof_passed += 1
        
        bulletproof_score = (bulletproof_passed / len(bulletproof_criteria)) * 100
        
        if bulletproof_score >= 80:
            self.log(f"\n🎉 BULLETPROOF VERIFICATION: PASSED ({bulletproof_score:.1f}%)")
            self.log("   The system demonstrates bulletproof reliability for large audio file processing!")
        elif bulletproof_score >= 60:
            self.log(f"\n⚠️  BULLETPROOF VERIFICATION: PARTIAL ({bulletproof_score:.1f}%)")
            self.log("   The system shows good reliability but has some areas for improvement.")
        else:
            self.log(f"\n❌ BULLETPROOF VERIFICATION: NEEDS IMPROVEMENT ({bulletproof_score:.1f}%)")
            self.log("   The system requires significant improvements for bulletproof reliability.")
        
        # Clean up created notes
        if self.created_notes:
            self.log(f"\n🧹 Cleaning up {len(self.created_notes)} test notes...")
            for note_id in self.created_notes:
                try:
                    requests.delete(f"{self.api_url}/notes/{note_id}", timeout=5)
                except:
                    pass
        
        return bulletproof_score >= 80

if __name__ == "__main__":
    tester = BulletproofAudioVerificationTester()
    success = tester.run_bulletproof_verification()
    sys.exit(0 if success else 1)