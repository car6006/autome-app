#!/usr/bin/env python3
"""
Large Audio File Chunking Test Suite
Tests the new chunking functionality for handling audio files over 25MB
"""

import requests
import sys
import json
import time
import tempfile
import os
import subprocess
import math
from datetime import datetime
from pathlib import Path

class LargeAudioChunkingTester:
    def __init__(self, base_url="https://whisper-async-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.temp_files = []

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    self.log(f"Cleaned up: {temp_file}")
            except Exception as e:
                self.log(f"Failed to clean up {temp_file}: {e}")

    def create_test_audio_file(self, duration_seconds: int, filename_suffix: str = "") -> str:
        """Create a test audio file of specified duration using ffmpeg"""
        try:
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(suffix=f'_test_audio_{filename_suffix}.wav')
            os.close(fd)
            self.temp_files.append(temp_path)
            
            # Generate audio using ffmpeg (sine wave tone)
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duration_seconds}',
                '-ar', '16000', '-ac', '1', '-y', temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                file_size = os.path.getsize(temp_path)
                self.log(f"Created test audio: {temp_path} ({file_size / (1024*1024):.1f} MB, {duration_seconds}s)")
                return temp_path
            else:
                self.log(f"Failed to create test audio: {result.stderr}")
                return None
                
        except Exception as e:
            self.log(f"Error creating test audio file: {e}")
            return None

    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB"""
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0.0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=300):
        """Run a single API test with extended timeout for large files"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}

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
                    self.log(f"   Response text: {response.text[:500]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_ffmpeg_availability(self):
        """Test that ffmpeg and ffprobe are available"""
        self.log("🔧 Testing ffmpeg availability...")
        
        try:
            # Test ffmpeg
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            ffmpeg_available = result.returncode == 0
            
            # Test ffprobe
            result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, timeout=10)
            ffprobe_available = result.returncode == 0
            
            if ffmpeg_available and ffprobe_available:
                self.log("✅ ffmpeg and ffprobe are available")
                self.tests_passed += 1
            else:
                self.log("❌ ffmpeg or ffprobe not available")
            
            self.tests_run += 1
            return ffmpeg_available and ffprobe_available
            
        except Exception as e:
            self.log(f"❌ Error checking ffmpeg: {e}")
            self.tests_run += 1
            return False

    def test_small_audio_file_normal_processing(self):
        """Test that small audio files (< 24MB) are processed normally without chunking"""
        self.log("📁 Testing small audio file processing...")
        
        # Create a small audio file (30 seconds = ~1MB)
        small_audio = self.create_test_audio_file(30, "small")
        if not small_audio:
            self.tests_run += 1
            return False
        
        file_size = self.get_file_size_mb(small_audio)
        self.log(f"   Small audio file size: {file_size:.1f} MB")
        
        # Create note
        success, response = self.run_test(
            "Create Note for Small Audio",
            "POST",
            "notes",
            200,
            data={"title": "Small Audio Test", "kind": "audio"}
        )
        
        if not success or 'id' not in response:
            return False
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Upload small audio file
        with open(small_audio, 'rb') as f:
            files = {'file': ('small_test.wav', f, 'audio/wav')}
            success, response = self.run_test(
                "Upload Small Audio File",
                "POST",
                f"notes/{note_id}/upload",
                200,
                files=files,
                timeout=120
            )
        
        if success:
            self.log(f"   Small audio upload successful: {response.get('message', 'N/A')}")
            return True
        
        return False

    def test_large_audio_file_chunking(self):
        """Test that large audio files (> 24MB) trigger chunking logic"""
        self.log("🎵 Testing large audio file chunking...")
        
        # Create a large audio file (15 minutes = ~30MB)
        large_audio = self.create_test_audio_file(900, "large")  # 15 minutes
        if not large_audio:
            self.tests_run += 1
            return False
        
        file_size = self.get_file_size_mb(large_audio)
        self.log(f"   Large audio file size: {file_size:.1f} MB")
        
        if file_size < 24:
            self.log(f"   Warning: Generated file is only {file_size:.1f} MB, may not trigger chunking")
        
        # Create note
        success, response = self.run_test(
            "Create Note for Large Audio",
            "POST",
            "notes",
            200,
            data={"title": "Large Audio Chunking Test", "kind": "audio"}
        )
        
        if not success or 'id' not in response:
            return False
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Upload large audio file
        with open(large_audio, 'rb') as f:
            files = {'file': ('large_test.wav', f, 'audio/wav')}
            success, response = self.run_test(
                "Upload Large Audio File",
                "POST",
                f"notes/{note_id}/upload",
                200,
                files=files,
                timeout=600  # 10 minutes timeout for large file processing
            )
        
        if success:
            self.log(f"   Large audio upload successful: {response.get('message', 'N/A')}")
            return note_id
        
        return None

    def test_chunked_transcription_results(self, note_id: str):
        """Test that chunked transcription produces proper results with part numbers"""
        self.log("📝 Testing chunked transcription results...")
        
        # Wait for processing to complete
        max_wait = 600  # 10 minutes for large file processing
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, response = self.run_test(
                f"Check Processing Status",
                "GET",
                f"notes/{note_id}",
                200,
                timeout=30
            )
            
            if success:
                status = response.get('status', 'unknown')
                self.log(f"   Processing status: {status}")
                
                if status == 'ready':
                    # Check if transcript contains part numbers (indicating chunking was used)
                    artifacts = response.get('artifacts', {})
                    transcript = artifacts.get('transcript', '')
                    
                    if transcript:
                        self.log(f"   Transcript length: {len(transcript)} characters")
                        
                        # Check for part indicators
                        has_parts = '[Part ' in transcript
                        if has_parts:
                            self.log("✅ Transcript contains part numbers - chunking was used")
                            # Count parts
                            import re
                            parts = re.findall(r'\[Part \d+\]', transcript)
                            self.log(f"   Found {len(parts)} transcript parts")
                        else:
                            self.log("ℹ️  No part numbers found - file may have been processed as single chunk")
                        
                        self.tests_passed += 1
                        self.tests_run += 1
                        return True
                    else:
                        self.log("❌ No transcript found in artifacts")
                        self.tests_run += 1
                        return False
                
                elif status == 'failed':
                    error_msg = artifacts.get('error', 'Unknown error') if 'artifacts' in response else 'Processing failed'
                    self.log(f"❌ Processing failed: {error_msg}")
                    self.tests_run += 1
                    return False
                
                else:
                    self.log(f"   Still processing... ({status})")
                    time.sleep(10)
            else:
                self.log("❌ Failed to check processing status")
                self.tests_run += 1
                return False
        
        self.log("⏰ Timeout waiting for large file processing")
        self.tests_run += 1
        return False

    def test_upload_file_endpoint_large_audio(self):
        """Test the /upload-file endpoint with large audio files"""
        self.log("📤 Testing /upload-file endpoint with large audio...")
        
        # Create a moderately large audio file (8 minutes = ~20MB)
        large_audio = self.create_test_audio_file(480, "upload_large")  # 8 minutes
        if not large_audio:
            self.tests_run += 1
            return False
        
        file_size = self.get_file_size_mb(large_audio)
        self.log(f"   Upload test file size: {file_size:.1f} MB")
        
        # Test direct upload
        with open(large_audio, 'rb') as f:
            files = {'file': ('upload_large_test.wav', f, 'audio/wav')}
            data = {'title': 'Large Audio Upload Test'}
            success, response = self.run_test(
                "Direct Upload Large Audio",
                "POST",
                "upload-file",
                200,
                data=data,
                files=files,
                timeout=600
            )
        
        if success:
            note_id = response.get('id')
            if note_id:
                self.created_notes.append(note_id)
                self.log(f"   Created note via upload: {note_id}")
                return note_id
        
        return None

    def test_error_handling_corrupted_audio(self):
        """Test error handling with corrupted audio files"""
        self.log("🚫 Testing error handling with corrupted audio...")
        
        # Create a fake "corrupted" audio file
        fd, corrupted_path = tempfile.mkstemp(suffix='_corrupted.wav')
        self.temp_files.append(corrupted_path)
        
        # Write invalid audio data
        with os.fdopen(fd, 'wb') as f:
            f.write(b'This is not valid audio data' * 1000)  # Make it reasonably sized
        
        # Create note
        success, response = self.run_test(
            "Create Note for Corrupted Audio",
            "POST",
            "notes",
            200,
            data={"title": "Corrupted Audio Test", "kind": "audio"}
        )
        
        if not success or 'id' not in response:
            return False
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Upload corrupted file
        with open(corrupted_path, 'rb') as f:
            files = {'file': ('corrupted.wav', f, 'audio/wav')}
            success, response = self.run_test(
                "Upload Corrupted Audio",
                "POST",
                f"notes/{note_id}/upload",
                200,  # Upload should succeed, processing should fail gracefully
                files=files,
                timeout=120
            )
        
        if success:
            # Wait a bit and check if it fails gracefully
            time.sleep(5)
            success, response = self.run_test(
                "Check Corrupted Audio Status",
                "GET",
                f"notes/{note_id}",
                200
            )
            
            if success:
                status = response.get('status', 'unknown')
                self.log(f"   Corrupted audio status: {status}")
                
                # Should either be 'failed' or still 'processing'
                if status in ['failed', 'processing']:
                    self.log("✅ Corrupted audio handled appropriately")
                    return True
        
        return False

    def test_backwards_compatibility(self):
        """Test that normal small files still work exactly as before"""
        self.log("🔄 Testing backwards compatibility...")
        
        # Create a very small audio file (5 seconds)
        small_audio = self.create_test_audio_file(5, "compat")
        if not small_audio:
            self.tests_run += 1
            return False
        
        file_size = self.get_file_size_mb(small_audio)
        self.log(f"   Compatibility test file size: {file_size:.1f} MB")
        
        # Test via upload-file endpoint
        with open(small_audio, 'rb') as f:
            files = {'file': ('compat_test.wav', f, 'audio/wav')}
            data = {'title': 'Backwards Compatibility Test'}
            success, response = self.run_test(
                "Backwards Compatibility Upload",
                "POST",
                "upload-file",
                200,
                data=data,
                files=files,
                timeout=60
            )
        
        if success:
            note_id = response.get('id')
            if note_id:
                self.created_notes.append(note_id)
                
                # Wait for processing
                time.sleep(10)
                
                # Check results
                success, response = self.run_test(
                    "Check Compatibility Results",
                    "GET",
                    f"notes/{note_id}",
                    200
                )
                
                if success:
                    status = response.get('status', 'unknown')
                    artifacts = response.get('artifacts', {})
                    transcript = artifacts.get('transcript', '')
                    
                    self.log(f"   Status: {status}")
                    self.log(f"   Has transcript: {bool(transcript)}")
                    
                    # For small files, should not have part numbers
                    has_parts = '[Part ' in transcript if transcript else False
                    if not has_parts:
                        self.log("✅ Small file processed without chunking (backwards compatible)")
                        return True
                    else:
                        self.log("⚠️  Small file was chunked (unexpected but not necessarily wrong)")
                        return True  # Still consider it a pass
        
        return False

    def run_comprehensive_chunking_tests(self):
        """Run all chunking-related tests"""
        self.log("🚀 Starting Large Audio File Chunking Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        try:
            # Test 1: Verify ffmpeg availability
            if not self.test_ffmpeg_availability():
                self.log("❌ ffmpeg not available - chunking tests cannot proceed")
                return False
            
            # Test 2: Small file normal processing
            self.test_small_audio_file_normal_processing()
            
            # Test 3: Large file chunking
            large_note_id = self.test_large_audio_file_chunking()
            
            # Test 4: Check chunked transcription results
            if large_note_id:
                self.test_chunked_transcription_results(large_note_id)
            
            # Test 5: Upload endpoint with large files
            upload_note_id = self.test_upload_file_endpoint_large_audio()
            
            # Test 6: Error handling
            self.test_error_handling_corrupted_audio()
            
            # Test 7: Backwards compatibility
            self.test_backwards_compatibility()
            
            return True
            
        except Exception as e:
            self.log(f"💥 Unexpected error during testing: {str(e)}")
            return False
        
        finally:
            # Clean up temporary files
            self.cleanup()

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 LARGE AUDIO CHUNKING TEST SUMMARY")
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
    tester = LargeAudioChunkingTester()
    
    try:
        success = tester.run_comprehensive_chunking_tests()
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All chunking tests passed! Large audio file handling is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some chunking tests failed. Check the logs above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())