#!/usr/bin/env python3
"""
Audio API Test - Focus on API endpoints and workflow validation
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class AudioAPITester:
    def __init__(self, base_url="https://voice2text-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.auth_token = None
        self.expeditors_token = None
        self.test_results = []

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def register_users(self):
        """Register test users"""
        # Regular user
        user_data = {
            "email": f"api_audio_{int(time.time())}@example.com",
            "username": f"apiuser_{int(time.time())}",
            "password": "APITest123!",
            "first_name": "API",
            "last_name": "Tester"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=user_data)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
            self.log(f"✅ Regular user registered")
        else:
            self.log(f"❌ Regular user registration failed: {response.status_code}")
            return False

        # Expeditors user
        expeditors_data = {
            "email": f"api_expeditors_{int(time.time())}@expeditors.com",
            "username": f"apiexpeditors_{int(time.time())}",
            "password": "APIExpeditors123!",
            "first_name": "API",
            "last_name": "Expeditors"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=expeditors_data)
        if response.status_code == 200:
            data = response.json()
            self.expeditors_token = data.get('access_token')
            self.log(f"✅ Expeditors user registered")
        else:
            self.log(f"❌ Expeditors user registration failed: {response.status_code}")

        return True

    def test_upload_file_endpoint_audio_support(self):
        """Test if /api/upload-file supports audio files"""
        self.log("\n🔍 Testing /api/upload-file endpoint for audio support")
        
        # Create a small audio-like file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'\xff\xfb\x90\x00' * 10)  # Minimal MP3-like header
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_audio.mp3', f, 'audio/mpeg')}
                data = {'title': 'Audio Upload Test'}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                
                response = requests.post(
                    f"{self.api_url}/upload-file",
                    data=data,
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.log(f"✅ /api/upload-file accepts audio files")
                    self.test_results.append(("upload-file audio support", True, "Accepts MP3 files"))
                    return True, response.json()
                elif response.status_code == 400:
                    error_data = response.json()
                    if "Unsupported file type" in error_data.get('detail', ''):
                        self.log(f"❌ /api/upload-file does NOT support audio files")
                        self.log(f"   Supported types: {error_data.get('detail', '')}")
                        self.test_results.append(("upload-file audio support", False, "Audio files not supported"))
                        return False, error_data
                else:
                    self.log(f"❌ Unexpected response: {response.status_code}")
                    self.test_results.append(("upload-file audio support", False, f"Unexpected status: {response.status_code}"))
                    return False, {}
            
            os.unlink(tmp_file.name)

    def test_note_upload_audio_support(self):
        """Test if /api/notes/{id}/upload supports audio files"""
        self.log("\n🔍 Testing /api/notes/{id}/upload endpoint for audio support")
        
        # Create audio note
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        data = {"title": "Audio Upload API Test", "kind": "audio"}
        
        response = requests.post(f"{self.api_url}/notes", json=data, headers=headers)
        if response.status_code != 200:
            self.log(f"❌ Failed to create audio note: {response.status_code}")
            return False
        
        note_id = response.json()['id']
        self.log(f"✅ Created audio note: {note_id[:8]}...")
        
        # Test uploading audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'\xff\xfb\x90\x00' * 10)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_audio.mp3', f, 'audio/mpeg')}
                
                response = requests.post(
                    f"{self.api_url}/notes/{note_id}/upload",
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.log(f"✅ /api/notes/{{id}}/upload accepts audio files")
                    data = response.json()
                    self.log(f"   Status: {data.get('status')}")
                    self.log(f"   Message: {data.get('message')}")
                    self.test_results.append(("note upload audio support", True, "Accepts audio files"))
                    return True, note_id
                else:
                    self.log(f"❌ Audio upload failed: {response.status_code}")
                    self.test_results.append(("note upload audio support", False, f"Upload failed: {response.status_code}"))
                    return False, None
            
            os.unlink(tmp_file.name)

    def test_network_audio_upload(self):
        """Test network diagram audio upload for Expeditors users"""
        if not self.expeditors_token:
            self.log("\n⏭️  Skipping network audio test (no Expeditors user)")
            return False
        
        self.log("\n🔍 Testing network diagram audio upload")
        
        # Create network diagram note
        headers = {'Authorization': f'Bearer {self.expeditors_token}'}
        data = {"title": "Network Audio API Test", "kind": "network_diagram"}
        
        response = requests.post(f"{self.api_url}/notes/network-diagram", json=data, headers=headers)
        if response.status_code != 200:
            self.log(f"❌ Failed to create network diagram note: {response.status_code}")
            return False
        
        network_note_id = response.json()['id']
        self.log(f"✅ Created network diagram note: {network_note_id[:8]}...")
        
        # Test uploading audio for network processing
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            tmp_file.write(b'\x1a\x45\xdf\xa3' * 10)  # WebM-like header
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('network_audio.webm', f, 'audio/webm')}
                
                response = requests.post(
                    f"{self.api_url}/notes/{network_note_id}/process-network",
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Network audio upload successful")
                    try:
                        data = response.json()
                        self.log(f"   Status: {data.get('status', 'N/A')}")
                    except:
                        self.log(f"   Response: Success (no JSON)")
                    self.test_results.append(("network audio upload", True, "Network processing accepts audio"))
                    return True
                else:
                    self.log(f"❌ Network audio upload failed: {response.status_code}")
                    self.test_results.append(("network audio upload", False, f"Failed: {response.status_code}"))
                    return False
            
            os.unlink(tmp_file.name)

    def test_audio_workflow_validation(self, note_id):
        """Test that audio notes follow proper workflow"""
        if not note_id:
            return False
        
        self.log(f"\n🔍 Testing audio workflow for note {note_id[:8]}...")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Check note immediately after upload
        response = requests.get(f"{self.api_url}/notes/{note_id}", headers=headers)
        if response.status_code != 200:
            self.log(f"❌ Failed to get note: {response.status_code}")
            return False
        
        note_data = response.json()
        
        # Validate note properties
        validations = [
            ("Note kind is 'audio'", note_data.get('kind') == 'audio'),
            ("Note has ID", bool(note_data.get('id'))),
            ("Note has title", bool(note_data.get('title'))),
            ("Note has status", note_data.get('status') in ['uploading', 'processing', 'ready', 'failed']),
            ("Note has created_at", bool(note_data.get('created_at'))),
            ("Note has user_id", bool(note_data.get('user_id')))
        ]
        
        all_valid = True
        for validation_name, is_valid in validations:
            if is_valid:
                self.log(f"   ✅ {validation_name}")
            else:
                self.log(f"   ❌ {validation_name}")
                all_valid = False
        
        # Check if processing was triggered (status should not be 'created')
        status = note_data.get('status')
        if status in ['uploading', 'processing', 'ready', 'failed']:
            self.log(f"   ✅ Processing triggered (status: {status})")
            processing_triggered = True
        else:
            self.log(f"   ❌ Processing not triggered (status: {status})")
            processing_triggered = False
        
        self.test_results.append(("audio workflow validation", all_valid and processing_triggered, f"Status: {status}"))
        return all_valid and processing_triggered

    def test_audio_format_acceptance(self):
        """Test different audio format acceptance"""
        self.log("\n🔍 Testing audio format acceptance")
        
        formats = [
            ("mp3", "audio/mpeg", b'\xff\xfb\x90\x00'),
            ("wav", "audio/wav", b'RIFF\x24\x00\x00\x00WAVE'),
            ("m4a", "audio/m4a", b'\x00\x00\x00\x20ftypM4A'),
            ("webm", "audio/webm", b'\x1a\x45\xdf\xa3'),
            ("ogg", "audio/ogg", b'OggS\x00\x02\x00\x00')
        ]
        
        format_results = []
        
        for format_ext, mime_type, header_bytes in formats:
            # Create audio note
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            data = {"title": f"Format Test - {format_ext.upper()}", "kind": "audio"}
            
            response = requests.post(f"{self.api_url}/notes", json=data, headers=headers)
            if response.status_code != 200:
                format_results.append((format_ext, False, "Note creation failed"))
                continue
            
            note_id = response.json()['id']
            
            # Test upload
            with tempfile.NamedTemporaryFile(suffix=f'.{format_ext}', delete=False) as tmp_file:
                tmp_file.write(header_bytes * 10)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': (f'test.{format_ext}', f, mime_type)}
                    
                    response = requests.post(
                        f"{self.api_url}/notes/{note_id}/upload",
                        files=files,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        format_results.append((format_ext, True, "Upload successful"))
                        self.log(f"   ✅ {format_ext.upper()} format accepted")
                    else:
                        format_results.append((format_ext, False, f"Upload failed: {response.status_code}"))
                        self.log(f"   ❌ {format_ext.upper()} format rejected: {response.status_code}")
                
                os.unlink(tmp_file.name)
        
        successful_formats = [fmt for fmt, success, _ in format_results if success]
        self.test_results.append(("audio format support", len(successful_formats) > 0, f"{len(successful_formats)}/5 formats supported"))
        
        return format_results

    def run_comprehensive_api_tests(self):
        """Run comprehensive API tests"""
        self.log("🎯 Starting Audio API Comprehensive Tests")
        
        # Register users
        if not self.register_users():
            return False
        
        # Test 1: Check if /api/upload-file supports audio
        self.test_upload_file_endpoint_audio_support()
        
        # Test 2: Check if /api/notes/{id}/upload supports audio
        upload_success, note_id = self.test_note_upload_audio_support()
        
        # Test 3: Test network audio upload
        self.test_network_audio_upload()
        
        # Test 4: Test audio workflow validation
        if upload_success and note_id:
            self.test_audio_workflow_validation(note_id)
        
        # Test 5: Test different audio format acceptance
        self.test_audio_format_acceptance()
        
        return True

    def print_summary(self):
        """Print comprehensive test summary"""
        self.log("\n" + "="*60)
        self.log("🎯 AUDIO API TEST SUMMARY")
        self.log("="*60)
        
        if not self.test_results:
            self.log("No test results to display")
            return False
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, success, details in self.test_results:
            status = "✅" if success else "❌"
            self.log(f"{status} {test_name}: {details}")
            if success:
                passed += 1
        
        self.log(f"\nOverall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Key findings
        self.log("\n🔍 KEY FINDINGS:")
        
        upload_file_support = any(result[0] == "upload-file audio support" and result[1] for result in self.test_results)
        note_upload_support = any(result[0] == "note upload audio support" and result[1] for result in self.test_results)
        network_support = any(result[0] == "network audio upload" and result[1] for result in self.test_results)
        
        if upload_file_support:
            self.log("   ✅ /api/upload-file endpoint supports audio files")
        else:
            self.log("   ❌ /api/upload-file endpoint does NOT support audio files")
        
        if note_upload_support:
            self.log("   ✅ /api/notes/{id}/upload endpoint supports audio files")
        else:
            self.log("   ❌ /api/notes/{id}/upload endpoint does NOT support audio files")
        
        if network_support:
            self.log("   ✅ Network diagram audio upload is working")
        else:
            self.log("   ❌ Network diagram audio upload is not working")
        
        self.log("="*60)
        
        return passed == total

def main():
    tester = AudioAPITester()
    
    try:
        tester.run_comprehensive_api_tests()
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All audio API tests passed!")
            return 0
        else:
            print("\n⚠️  Some audio API tests failed.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())