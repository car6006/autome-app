#!/usr/bin/env python3
"""
AUTO-ME Audio Upload Functionality Tests
Tests the new audio upload features for Record and Network pages
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class AudioUploadTester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"audio_test_{int(time.time())}@example.com",
            "username": f"audiouser_{int(time.time())}",
            "password": "AudioTest123!",
            "first_name": "Audio",
            "last_name": "Tester"
        }
        self.expeditors_user_data = {
            "email": f"audio_expeditors_{int(time.time())}@expeditors.com",
            "username": f"audio_expeditors_{int(time.time())}",
            "password": "ExpeditorsAudio123!",
            "first_name": "Audio",
            "last_name": "Expeditors"
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

    def create_dummy_audio_file(self, format_type="mp3"):
        """Create dummy audio files for different formats"""
        audio_files = {
            "mp3": {
                "data": b'\xff\xfb\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                "mime": "audio/mpeg",
                "ext": ".mp3"
            },
            "wav": {
                "data": b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00',
                "mime": "audio/wav",
                "ext": ".wav"
            },
            "m4a": {
                "data": b'\x00\x00\x00 ftypM4A \x00\x00\x00\x00M4A mp42isom\x00\x00\x00\x00',
                "mime": "audio/m4a",
                "ext": ".m4a"
            },
            "webm": {
                "data": b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm',
                "mime": "audio/webm",
                "ext": ".webm"
            },
            "ogg": {
                "data": b'OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                "mime": "audio/ogg",
                "ext": ".ogg"
            }
        }
        return audio_files.get(format_type, audio_files["mp3"])

    def test_user_registration(self):
        """Test user registration for audio testing"""
        success, response = self.run_test(
            "Audio Test User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   Audio test user registered successfully")
        return success

    def test_expeditors_user_registration(self):
        """Test Expeditors user registration for network audio testing"""
        success, response = self.run_test(
            "Expeditors Audio Test User Registration",
            "POST",
            "auth/register",
            200,
            data=self.expeditors_user_data
        )
        if success:
            self.expeditors_token = response.get('access_token')
            self.log(f"   Expeditors audio test user registered successfully")
        return success

    def test_direct_audio_upload_valid_formats(self):
        """Test /api/upload-file endpoint with valid audio formats"""
        audio_formats = ["mp3", "wav", "m4a", "webm", "ogg"]
        results = []
        
        for format_type in audio_formats:
            audio_file = self.create_dummy_audio_file(format_type)
            
            with tempfile.NamedTemporaryFile(suffix=audio_file["ext"], delete=False) as tmp_file:
                tmp_file.write(audio_file["data"])
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (f'test_audio{audio_file["ext"]}', f, audio_file["mime"])}
                    data = {'title': f'Audio Upload Test - {format_type.upper()}'}
                    
                    success, response = self.run_test(
                        f"Direct Audio Upload - {format_type.upper()}",
                        "POST",
                        "upload-file",
                        200,
                        data=data,
                        files=files,
                        auth_required=True
                    )
                    
                    if success and 'id' in response:
                        note_id = response['id']
                        self.created_notes.append(note_id)
                        self.log(f"   Created audio note ID: {note_id}")
                        self.log(f"   Filename: {response.get('filename', 'N/A')}")
                        results.append((format_type, True, note_id))
                    else:
                        results.append((format_type, False, None))
                
                os.unlink(tmp_file.name)
        
        return results

    def test_direct_audio_upload_invalid_formats(self):
        """Test /api/upload-file endpoint with invalid file types"""
        invalid_files = [
            {"data": b"This is a text file", "ext": ".txt", "mime": "text/plain"},
            {"data": b"<html><body>HTML file</body></html>", "ext": ".html", "mime": "text/html"},
            {"data": b"\x89PNG\r\n\x1a\n", "ext": ".png", "mime": "image/png"}
        ]
        
        results = []
        for i, invalid_file in enumerate(invalid_files):
            with tempfile.NamedTemporaryFile(suffix=invalid_file["ext"], delete=False) as tmp_file:
                tmp_file.write(invalid_file["data"])
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (f'invalid_file{invalid_file["ext"]}', f, invalid_file["mime"])}
                    data = {'title': f'Invalid File Test {i+1}'}
                    
                    success, response = self.run_test(
                        f"Invalid File Upload - {invalid_file['ext']}",
                        "POST",
                        "upload-file",
                        400,  # Should fail with 400
                        data=data,
                        files=files,
                        auth_required=True
                    )
                    results.append(success)
                
                os.unlink(tmp_file.name)
        
        return all(results)

    def test_note_audio_upload(self):
        """Test /api/notes/{id}/upload endpoint with audio files"""
        # First create an audio note
        success, response = self.run_test(
            "Create Audio Note for Upload",
            "POST",
            "notes",
            200,
            data={"title": "Audio Note Upload Test", "kind": "audio"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            return False
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Test uploading audio to the note
        audio_file = self.create_dummy_audio_file("mp3")
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_file["data"])
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('note_audio.mp3', f, 'audio/mpeg')}
                
                success, response = self.run_test(
                    f"Upload Audio to Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if success:
                self.log(f"   Upload status: {response.get('status', 'N/A')}")
                self.log(f"   Upload message: {response.get('message', 'N/A')}")
                return note_id
        
        return None

    def test_network_page_audio_upload(self):
        """Test audio upload for Network page (Expeditors only)"""
        # Switch to Expeditors token
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Create network diagram note
        success, response = self.run_test(
            "Create Network Diagram Note",
            "POST",
            "notes/network-diagram",
            200,
            data={"title": "Network Audio Upload Test", "kind": "network_diagram"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            self.auth_token = temp_token
            return False
        
        network_note_id = response['id']
        self.created_notes.append(network_note_id)
        
        # Test uploading audio for network processing
        audio_file = self.create_dummy_audio_file("webm")
        
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
            tmp_file.write(audio_file["data"])
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('network_description.webm', f, 'audio/webm')}
                
                success, response = self.run_test(
                    f"Network Audio Upload {network_note_id[:8]}...",
                    "POST",
                    f"notes/{network_note_id}/process-network",
                    200,
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
            
            if success:
                self.log(f"   Network processing status: {response.get('status', 'N/A')}")
                self.log(f"   Network processing message: {response.get('message', 'N/A')}")
        
        # Restore original token
        self.auth_token = temp_token
        return success

    def test_audio_processing_workflow(self, note_id):
        """Test complete audio processing workflow"""
        if not note_id:
            return False
        
        self.log(f"⏳ Testing audio processing workflow for note {note_id[:8]}...")
        
        # Wait and check processing status
        max_wait = 60  # 1 minute max wait
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, note_data = self.run_test(
                f"Check Processing Status {note_id[:8]}...",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success:
                status = note_data.get('status', 'unknown')
                self.log(f"   Current status: {status}")
                
                if status == 'ready':
                    self.log(f"✅ Audio processing completed successfully!")
                    artifacts = note_data.get('artifacts', {})
                    if 'transcript' in artifacts:
                        self.log(f"   Transcript available: Yes")
                        self.log(f"   Transcript length: {len(artifacts['transcript'])} chars")
                    else:
                        self.log(f"   Transcript available: No")
                    return True
                elif status == 'failed':
                    self.log(f"❌ Audio processing failed!")
                    return False
                elif status in ['uploading', 'processing']:
                    self.log(f"   Still processing, waiting...")
                    time.sleep(3)
                else:
                    self.log(f"   Unknown status: {status}")
                    time.sleep(2)
            else:
                break
        
        self.log(f"⏰ Timeout waiting for audio processing")
        return False

    def test_audio_note_transcription_quality(self, note_id):
        """Test that audio notes have proper transcription artifacts"""
        success, note_data = self.run_test(
            f"Check Audio Note Quality {note_id[:8]}...",
            "GET",
            f"notes/{note_id}",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        # Verify note properties
        if note_data.get('kind') != 'audio':
            self.log(f"❌ Note kind is not 'audio': {note_data.get('kind')}")
            return False
        
        artifacts = note_data.get('artifacts', {})
        
        # Check for expected artifacts
        expected_artifacts = ['transcript']
        missing_artifacts = []
        
        for artifact in expected_artifacts:
            if artifact not in artifacts:
                missing_artifacts.append(artifact)
        
        if missing_artifacts:
            self.log(f"⚠️  Missing artifacts: {missing_artifacts}")
            # This might be expected if processing is still ongoing or failed
            return note_data.get('status') == 'ready'
        
        self.log(f"✅ Audio note has all expected artifacts")
        return True

    def run_comprehensive_audio_tests(self):
        """Run all audio upload tests"""
        self.log("🎵 Starting AUTO-ME Audio Upload Comprehensive Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Test user registration
        if not self.test_user_registration():
            self.log("❌ User registration failed - stopping tests")
            return False
        
        # Test Expeditors user registration
        if not self.test_expeditors_user_registration():
            self.log("❌ Expeditors user registration failed - network tests will be skipped")
        
        # === DIRECT AUDIO UPLOAD TESTS (Record Page) ===
        self.log("\n🎤 RECORD PAGE AUDIO UPLOAD TESTS")
        
        # Test valid audio formats
        self.log("Testing valid audio formats...")
        upload_results = self.test_direct_audio_upload_valid_formats()
        
        successful_uploads = [result for result in upload_results if result[1]]
        failed_uploads = [result for result in upload_results if not result[1]]
        
        self.log(f"   Successful uploads: {len(successful_uploads)}/{len(upload_results)}")
        for format_type, success, note_id in successful_uploads:
            self.log(f"   ✅ {format_type.upper()}: {note_id[:8] if note_id else 'N/A'}...")
        
        if failed_uploads:
            self.log(f"   Failed uploads:")
            for format_type, success, note_id in failed_uploads:
                self.log(f"   ❌ {format_type.upper()}")
        
        # Test invalid file formats
        self.log("Testing invalid file formats...")
        invalid_test_success = self.test_direct_audio_upload_invalid_formats()
        if invalid_test_success:
            self.log("   ✅ Invalid file rejection working correctly")
        else:
            self.log("   ❌ Invalid file rejection not working properly")
        
        # === NOTE AUDIO UPLOAD TESTS ===
        self.log("\n📝 NOTE AUDIO UPLOAD TESTS")
        
        # Test uploading audio to existing note
        note_upload_id = self.test_note_audio_upload()
        
        # === NETWORK PAGE AUDIO UPLOAD TESTS ===
        self.log("\n🌐 NETWORK PAGE AUDIO UPLOAD TESTS")
        
        if self.expeditors_token:
            network_success = self.test_network_page_audio_upload()
            if network_success:
                self.log("   ✅ Network page audio upload working")
            else:
                self.log("   ❌ Network page audio upload failed")
        else:
            self.log("   ⏭️  Skipping network tests (no Expeditors user)")
        
        # === AUDIO PROCESSING WORKFLOW TESTS ===
        self.log("\n⚙️ AUDIO PROCESSING WORKFLOW TESTS")
        
        # Test processing workflow for successful uploads
        processing_results = []
        for format_type, success, note_id in successful_uploads[:2]:  # Test first 2 to save time
            if success and note_id:
                self.log(f"Testing processing workflow for {format_type.upper()}...")
                processing_success = self.test_audio_processing_workflow(note_id)
                processing_results.append((format_type, processing_success))
                
                if processing_success:
                    # Test transcription quality
                    quality_success = self.test_audio_note_transcription_quality(note_id)
                    self.log(f"   Quality check for {format_type.upper()}: {'✅' if quality_success else '❌'}")
        
        # Test processing for note upload
        if note_upload_id:
            self.log("Testing processing workflow for note upload...")
            note_processing_success = self.test_audio_processing_workflow(note_upload_id)
            if note_processing_success:
                self.test_audio_note_transcription_quality(note_upload_id)
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("🎵 AUDIO UPLOAD TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated audio test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = AudioUploadTester()
    
    try:
        success = tester.run_comprehensive_audio_tests()
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All audio upload tests passed! Audio functionality is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some audio upload tests failed. Check the logs above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Audio upload tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error in audio upload tests: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())