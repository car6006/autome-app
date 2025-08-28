#!/usr/bin/env python3
"""
Large Audio File Processing Test
Tests the specific user file: "JNB Management Meeting 22 August 2025.mp3"
"""

import requests
import sys
import json
import time
import os
from datetime import datetime
from pathlib import Path

class LargeAudioTester:
    def __init__(self, base_url="https://audio-pipeline-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_file_path = "/tmp/test_audio.mp3"
        self.created_notes = []
        
    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def test_file_info(self):
        """Check the test file information"""
        if not os.path.exists(self.test_file_path):
            self.log(f"❌ Test file not found: {self.test_file_path}")
            return False
            
        file_size = os.path.getsize(self.test_file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        self.log(f"📁 Test file: {self.test_file_path}")
        self.log(f"📊 File size: {file_size:,} bytes ({file_size_mb:.1f} MB)")
        
        # Expected values from review request
        expected_size = 33514991
        expected_mb = 31.9
        
        if file_size == expected_size:
            self.log(f"✅ File size matches expected: {expected_size:,} bytes")
        else:
            self.log(f"⚠️  File size differs from expected: {expected_size:,} bytes")
            
        return True

    def create_audio_note(self):
        """Create an audio note for testing"""
        self.log("🎵 Creating audio note for large file test...")
        
        try:
            response = requests.post(
                f"{self.api_url}/notes",
                json={"title": "JNB Management Meeting 22 August 2025", "kind": "audio"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                note_id = data.get('id')
                self.created_notes.append(note_id)
                self.log(f"✅ Created note ID: {note_id}")
                return note_id
            else:
                self.log(f"❌ Failed to create note: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error creating note: {str(e)}")
            return None

    def upload_large_audio_file(self, note_id):
        """Upload the large audio file to the note"""
        self.log(f"📤 Uploading large audio file to note {note_id[:8]}...")
        
        try:
            with open(self.test_file_path, 'rb') as f:
                files = {'file': ('JNB Management Meeting 22 August 2025.mp3', f, 'audio/mpeg')}
                
                # Use longer timeout for large file upload
                response = requests.post(
                    f"{self.api_url}/notes/{note_id}/upload",
                    files=files,
                    timeout=300  # 5 minutes for upload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ File uploaded successfully")
                    self.log(f"   Status: {data.get('status', 'N/A')}")
                    self.log(f"   Message: {data.get('message', 'N/A')}")
                    return True
                else:
                    self.log(f"❌ Upload failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Upload error: {str(e)}")
            return False

    def test_direct_file_upload(self):
        """Test direct file upload via /api/upload-file endpoint"""
        self.log("📤 Testing direct file upload endpoint...")
        
        try:
            with open(self.test_file_path, 'rb') as f:
                files = {'file': ('JNB Management Meeting 22 August 2025.mp3', f, 'audio/mpeg')}
                data = {'title': 'JNB Management Meeting 22 August 2025 - Direct Upload'}
                
                response = requests.post(
                    f"{self.api_url}/upload-file",
                    files=files,
                    data=data,
                    timeout=300  # 5 minutes for upload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    note_id = result.get('id')
                    if note_id:
                        self.created_notes.append(note_id)
                    self.log(f"✅ Direct upload successful")
                    self.log(f"   Note ID: {note_id}")
                    self.log(f"   Kind: {result.get('kind', 'N/A')}")
                    self.log(f"   Status: {result.get('status', 'N/A')}")
                    return note_id
                else:
                    self.log(f"❌ Direct upload failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Direct upload error: {str(e)}")
            return None

    def monitor_processing(self, note_id, max_wait_minutes=35):
        """Monitor note processing with extended timeout for large files"""
        self.log(f"⏳ Monitoring processing for note {note_id[:8]}... (max {max_wait_minutes} minutes)")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        last_status = None
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = requests.get(f"{self.api_url}/notes/{note_id}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    artifacts = data.get('artifacts', {})
                    
                    # Log status changes
                    if status != last_status:
                        elapsed_minutes = (time.time() - start_time) / 60
                        self.log(f"   Status: {status} (after {elapsed_minutes:.1f} minutes)")
                        last_status = status
                    
                    if status == 'ready':
                        elapsed_minutes = (time.time() - start_time) / 60
                        self.log(f"✅ Processing completed in {elapsed_minutes:.1f} minutes!")
                        
                        # Check for chunking evidence
                        transcript = artifacts.get('transcript', '')
                        if '[Part ' in transcript:
                            parts = transcript.count('[Part ')
                            self.log(f"   ✅ Chunking detected: {parts} parts found")
                        else:
                            self.log(f"   ℹ️  No chunking markers found (may be processed as single file)")
                            
                        transcript_length = len(transcript)
                        self.log(f"   📝 Transcript length: {transcript_length:,} characters")
                        
                        if transcript_length > 1000:
                            self.log(f"   📄 Transcript preview: {transcript[:200]}...")
                        
                        return True, data
                        
                    elif status == 'failed':
                        elapsed_minutes = (time.time() - start_time) / 60
                        self.log(f"❌ Processing failed after {elapsed_minutes:.1f} minutes")
                        error = artifacts.get('error', 'Unknown error')
                        self.log(f"   Error: {error}")
                        return False, data
                        
                    elif status in ['processing', 'uploading']:
                        # Continue waiting
                        time.sleep(10)  # Check every 10 seconds
                    else:
                        self.log(f"   Unknown status: {status}")
                        time.sleep(5)
                        
                else:
                    self.log(f"❌ Error checking status: {response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                self.log(f"❌ Error monitoring: {str(e)}")
                time.sleep(5)
        
        elapsed_minutes = (time.time() - start_time) / 60
        self.log(f"⏰ Timeout after {elapsed_minutes:.1f} minutes - processing may still be ongoing")
        return False, {}

    def analyze_chunking_behavior(self, note_data):
        """Analyze the chunking behavior from the processed note"""
        self.log("🔍 Analyzing chunking behavior...")
        
        artifacts = note_data.get('artifacts', {})
        transcript = artifacts.get('transcript', '')
        
        if not transcript:
            self.log("   ❌ No transcript found")
            return
            
        # Count parts
        part_count = transcript.count('[Part ')
        if part_count > 0:
            self.log(f"   ✅ File was chunked into {part_count} parts")
            
            # Expected chunks calculation
            # File: 31.9MB, Duration: ~93 minutes (5585 seconds)
            # Chunk size: 4 minutes (240 seconds)
            expected_chunks = 5585 / 240  # ~23.3 chunks
            self.log(f"   📊 Expected chunks (~93 min / 4 min): ~{expected_chunks:.1f}")
            self.log(f"   📊 Actual chunks found: {part_count}")
            
            if abs(part_count - expected_chunks) <= 2:
                self.log(f"   ✅ Chunk count matches expectation (±2)")
            else:
                self.log(f"   ⚠️  Chunk count differs from expectation")
                
        else:
            self.log("   ℹ️  No chunking markers found - processed as single file")
            
        # Check transcript length
        char_count = len(transcript)
        self.log(f"   📝 Total transcript length: {char_count:,} characters")
        
        # Estimate words (rough: 5 chars per word)
        word_estimate = char_count / 5
        self.log(f"   📝 Estimated words: {word_estimate:,.0f}")
        
        # For 93 minutes of meeting, expect roughly 13,000-18,000 words (150-200 wpm)
        if 10000 <= word_estimate <= 25000:
            self.log(f"   ✅ Word count reasonable for 93-minute meeting")
        else:
            self.log(f"   ⚠️  Word count may be unusual for 93-minute meeting")

    def run_large_audio_test(self):
        """Run the complete large audio file test"""
        self.log("🚀 Starting Large Audio File Processing Test")
        self.log("   Target: JNB Management Meeting 22 August 2025.mp3 (31.9MB, 93 minutes)")
        
        # Check file info
        if not self.test_file_info():
            return False
            
        # Test Method 1: Create note then upload
        self.log("\n📝 METHOD 1: Create note then upload file")
        note_id = self.create_audio_note()
        if note_id:
            if self.upload_large_audio_file(note_id):
                success, note_data = self.monitor_processing(note_id)
                if success:
                    self.analyze_chunking_behavior(note_data)
                    self.log("✅ Method 1 completed successfully")
                else:
                    self.log("❌ Method 1 failed during processing")
            else:
                self.log("❌ Method 1 failed during upload")
        else:
            self.log("❌ Method 1 failed during note creation")
            
        # Test Method 2: Direct file upload
        self.log("\n📤 METHOD 2: Direct file upload")
        direct_note_id = self.test_direct_file_upload()
        if direct_note_id:
            success, note_data = self.monitor_processing(direct_note_id)
            if success:
                self.analyze_chunking_behavior(note_data)
                self.log("✅ Method 2 completed successfully")
            else:
                self.log("❌ Method 2 failed during processing")
        else:
            self.log("❌ Method 2 failed during upload")
            
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 LARGE AUDIO FILE TEST SUMMARY")
        self.log("="*60)
        self.log(f"Test file: JNB Management Meeting 22 August 2025.mp3")
        self.log(f"File size: 31.9MB (33,514,991 bytes)")
        self.log(f"Expected duration: 93 minutes (5585 seconds)")
        self.log(f"Expected chunks: ~23 (at 4 minutes each)")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*60)

def main():
    """Main test execution"""
    tester = LargeAudioTester()
    
    try:
        success = tester.run_large_audio_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 Large audio file test completed!")
            return 0
        else:
            print(f"\n⚠️  Large audio file test encountered issues.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())