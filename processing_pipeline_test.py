#!/usr/bin/env python3
"""
AUTO-ME Processing Pipeline Test - OpenAI API Integration
Critical production test for audio transcription and image OCR processing
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os
import base64

class ProcessingPipelineTester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"pipeline_test_{int(time.time())}@example.com",
            "username": f"pipelinetest_{int(time.time())}",
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
        """Setup test user authentication"""
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
            self.log(f"   Authentication setup successful")
            return True
        else:
            self.log(f"   Authentication setup failed")
            return False

    def create_audio_note_with_real_content(self):
        """Create audio note and upload real audio content for transcription"""
        self.log("🎵 Creating audio note with real content...")
        
        # Create audio note
        success, response = self.run_test(
            "Create Audio Note",
            "POST",
            "notes",
            200,
            data={"title": "OpenAI Whisper Test Audio", "kind": "audio"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            return None
        
        note_id = response['id']
        self.created_notes.append(note_id)
        self.log(f"   Created audio note ID: {note_id}")
        
        # Create a more realistic audio file (WAV format with actual audio data)
        # This creates a simple sine wave audio file
        audio_data = self.create_test_audio_wav()
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_speech.wav', f, 'audio/wav')}
                success, response = self.run_test(
                    f"Upload Audio Content",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if success:
                self.log(f"   Audio upload successful - processing started")
                return note_id
            else:
                self.log(f"   Audio upload failed")
                return None

    def create_photo_note_with_text_image(self):
        """Create photo note and upload image with text for OCR"""
        self.log("📷 Creating photo note with text image...")
        
        # Create photo note
        success, response = self.run_test(
            "Create Photo Note",
            "POST",
            "notes",
            200,
            data={"title": "OpenAI Vision OCR Test Image", "kind": "photo"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            return None
        
        note_id = response['id']
        self.created_notes.append(note_id)
        self.log(f"   Created photo note ID: {note_id}")
        
        # Create a simple image with text using PIL-like approach
        # For testing, we'll create a basic PNG with some recognizable text pattern
        image_data = self.create_test_image_with_text()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(image_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_document.png', f, 'image/png')}
                success, response = self.run_test(
                    f"Upload Image Content",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if success:
                self.log(f"   Image upload successful - OCR processing started")
                return note_id
            else:
                self.log(f"   Image upload failed")
                return None

    def create_test_audio_wav(self):
        """Create a minimal WAV file with sine wave audio data"""
        # WAV file header for 1 second of 8kHz mono audio
        sample_rate = 8000
        duration = 1  # 1 second
        samples = sample_rate * duration
        
        # WAV header
        wav_header = b'RIFF'
        wav_header += (36 + samples * 2).to_bytes(4, 'little')  # File size
        wav_header += b'WAVE'
        wav_header += b'fmt '
        wav_header += (16).to_bytes(4, 'little')  # Subchunk1Size
        wav_header += (1).to_bytes(2, 'little')   # AudioFormat (PCM)
        wav_header += (1).to_bytes(2, 'little')   # NumChannels (mono)
        wav_header += sample_rate.to_bytes(4, 'little')  # SampleRate
        wav_header += (sample_rate * 2).to_bytes(4, 'little')  # ByteRate
        wav_header += (2).to_bytes(2, 'little')   # BlockAlign
        wav_header += (16).to_bytes(2, 'little')  # BitsPerSample
        wav_header += b'data'
        wav_header += (samples * 2).to_bytes(4, 'little')  # Subchunk2Size
        
        # Generate simple sine wave audio data (440Hz tone)
        import math
        audio_data = b''
        for i in range(samples):
            # Generate sine wave sample
            sample = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
            audio_data += sample.to_bytes(2, 'little', signed=True)
        
        return wav_header + audio_data

    def create_test_image_with_text(self):
        """Create a simple PNG image with text content for OCR testing"""
        # Create a minimal PNG with embedded text pattern
        # This is a 100x50 pixel PNG with some text-like patterns
        
        # PNG signature
        png_data = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk (image header)
        width, height = 100, 50
        ihdr_data = width.to_bytes(4, 'big') + height.to_bytes(4, 'big')
        ihdr_data += b'\x08\x02\x00\x00\x00'  # bit depth=8, color type=2 (RGB), compression=0, filter=0, interlace=0
        ihdr_crc = self.crc32(b'IHDR' + ihdr_data)
        png_data += (13).to_bytes(4, 'big') + b'IHDR' + ihdr_data + ihdr_crc.to_bytes(4, 'big')
        
        # IDAT chunk (image data) - simple pattern that might be recognized as text
        # Create a simple pattern that resembles text
        image_bytes = b''
        for y in range(height):
            image_bytes += b'\x00'  # Filter type 0 (None)
            for x in range(width):
                # Create a pattern that resembles "HELLO WORLD" text
                if 10 <= y <= 40:  # Text area
                    if (20 <= x <= 25) or (30 <= x <= 35) or (40 <= x <= 45) or (50 <= x <= 55) or (60 <= x <= 65):
                        # Black pixels for text
                        image_bytes += b'\x00\x00\x00'  # RGB black
                    else:
                        # White background
                        image_bytes += b'\xFF\xFF\xFF'  # RGB white
                else:
                    # White background
                    image_bytes += b'\xFF\xFF\xFF'  # RGB white
        
        # Compress the image data (simplified - just use raw data)
        import zlib
        compressed_data = zlib.compress(image_bytes)
        idat_crc = self.crc32(b'IDAT' + compressed_data)
        png_data += len(compressed_data).to_bytes(4, 'big') + b'IDAT' + compressed_data + idat_crc.to_bytes(4, 'big')
        
        # IEND chunk
        iend_crc = self.crc32(b'IEND')
        png_data += (0).to_bytes(4, 'big') + b'IEND' + iend_crc.to_bytes(4, 'big')
        
        return png_data

    def crc32(self, data):
        """Calculate CRC32 for PNG chunks"""
        import zlib
        return zlib.crc32(data) & 0xffffffff

    def monitor_processing_status(self, note_id, note_type, max_wait=120):
        """Monitor note processing status with detailed logging"""
        self.log(f"⏳ Monitoring {note_type} processing for note {note_id[:8]}... (max {max_wait}s)")
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            success, note_data = self.run_test(
                f"Check {note_type} Status",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success:
                status = note_data.get('status', 'unknown')
                artifacts = note_data.get('artifacts', {})
                
                if status != last_status:
                    self.log(f"   Status changed: {last_status} → {status}")
                    last_status = status
                
                if status == 'ready':
                    processing_time = time.time() - start_time
                    self.log(f"✅ {note_type} processing completed in {processing_time:.1f}s!")
                    
                    # Log artifacts found
                    if note_type == 'Audio':
                        if 'transcript' in artifacts:
                            transcript = artifacts['transcript'][:100] + "..." if len(artifacts.get('transcript', '')) > 100 else artifacts.get('transcript', '')
                            self.log(f"   Transcript: {transcript}")
                        if 'summary' in artifacts:
                            self.log(f"   Summary generated: Yes")
                        if 'actions' in artifacts:
                            self.log(f"   Action items: {len(artifacts.get('actions', []))}")
                    
                    elif note_type == 'Photo':
                        if 'text' in artifacts:
                            ocr_text = artifacts['text'][:100] + "..." if len(artifacts.get('text', '')) > 100 else artifacts.get('text', '')
                            self.log(f"   OCR Text: {ocr_text}")
                        if 'summary' in artifacts:
                            self.log(f"   Summary generated: Yes")
                    
                    return True, processing_time, artifacts
                
                elif status == 'failed':
                    processing_time = time.time() - start_time
                    self.log(f"❌ {note_type} processing failed after {processing_time:.1f}s!")
                    
                    # Log error details if available
                    if 'error' in artifacts:
                        self.log(f"   Error: {artifacts['error']}")
                    
                    return False, processing_time, artifacts
                
                else:
                    elapsed = time.time() - start_time
                    self.log(f"   Status: {status} (elapsed: {elapsed:.1f}s)")
                    time.sleep(5)  # Check every 5 seconds
            else:
                self.log(f"   Failed to check status")
                break
        
        processing_time = time.time() - start_time
        self.log(f"⏰ Timeout waiting for {note_type} processing after {processing_time:.1f}s")
        return False, processing_time, {}

    def test_processing_pipeline(self):
        """Test the complete processing pipeline"""
        self.log("🚀 Starting Processing Pipeline Test")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup authentication
        if not self.setup_authentication():
            return False
        
        # Test 1: Audio Processing Pipeline
        self.log("\n🎵 AUDIO PROCESSING PIPELINE TEST")
        audio_note_id = self.create_audio_note_with_real_content()
        
        if audio_note_id:
            audio_success, audio_time, audio_artifacts = self.monitor_processing_status(
                audio_note_id, "Audio", max_wait=120
            )
            
            if audio_success:
                self.log(f"✅ Audio processing pipeline: SUCCESS")
                self.log(f"   Processing time: {audio_time:.1f}s")
                self.log(f"   Within 2-minute limit: {'Yes' if audio_time < 120 else 'No'}")
            else:
                self.log(f"❌ Audio processing pipeline: FAILED")
                self.log(f"   Processing time: {audio_time:.1f}s")
        else:
            self.log(f"❌ Audio note creation failed")
            audio_success = False
        
        # Test 2: Photo/OCR Processing Pipeline
        self.log("\n📷 PHOTO OCR PROCESSING PIPELINE TEST")
        photo_note_id = self.create_photo_note_with_text_image()
        
        if photo_note_id:
            photo_success, photo_time, photo_artifacts = self.monitor_processing_status(
                photo_note_id, "Photo", max_wait=120
            )
            
            if photo_success:
                self.log(f"✅ Photo OCR processing pipeline: SUCCESS")
                self.log(f"   Processing time: {photo_time:.1f}s")
                self.log(f"   Within 2-minute limit: {'Yes' if photo_time < 120 else 'No'}")
            else:
                self.log(f"❌ Photo OCR processing pipeline: FAILED")
                self.log(f"   Processing time: {photo_time:.1f}s")
        else:
            self.log(f"❌ Photo note creation failed")
            photo_success = False
        
        # Overall pipeline assessment
        self.log("\n📊 PROCESSING PIPELINE ASSESSMENT")
        
        if audio_success and photo_success:
            self.log("✅ COMPLETE PROCESSING PIPELINE: FULLY FUNCTIONAL")
            self.log("   Both audio transcription and image OCR are working")
            self.log("   No notes stuck in processing state")
            self.log("   Processing completes within reasonable time")
            return True
        elif audio_success or photo_success:
            self.log("⚠️  PARTIAL PROCESSING PIPELINE: PARTIALLY FUNCTIONAL")
            self.log(f"   Audio processing: {'✅ Working' if audio_success else '❌ Failed'}")
            self.log(f"   Photo OCR processing: {'✅ Working' if photo_success else '❌ Failed'}")
            return False
        else:
            self.log("❌ COMPLETE PROCESSING PIPELINE: NOT FUNCTIONAL")
            self.log("   Both audio and photo processing failed")
            return False

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 PROCESSING PIPELINE TEST SUMMARY")
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
    tester = ProcessingPipelineTester()
    
    try:
        success = tester.test_processing_pipeline()
        tester.print_summary()
        
        if success:
            print("\n🎉 Processing pipeline is fully functional!")
            print("✅ Ready for production deployment")
            return 0
        else:
            print(f"\n⚠️  Processing pipeline has issues - check logs above")
            print("❌ Not ready for production deployment")
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