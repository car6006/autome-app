#!/usr/bin/env python3
"""
Focused Audio Upload Test - Testing existing audio functionality
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class FocusedAudioTester:
    def __init__(self, base_url="https://voice-capture-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.auth_token = None
        self.created_notes = []

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def register_user(self):
        """Register a test user"""
        user_data = {
            "email": f"focused_audio_{int(time.time())}@example.com",
            "username": f"focuseduser_{int(time.time())}",
            "password": "FocusedTest123!",
            "first_name": "Focused",
            "last_name": "Tester"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=user_data)
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access_token')
            self.log(f"✅ User registered successfully")
            return True
        else:
            self.log(f"❌ User registration failed: {response.status_code}")
            return False

    def create_audio_note(self):
        """Create an audio note"""
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        data = {"title": "Focused Audio Test", "kind": "audio"}
        
        response = requests.post(f"{self.api_url}/notes", json=data, headers=headers)
        if response.status_code == 200:
            note_data = response.json()
            note_id = note_data['id']
            self.created_notes.append(note_id)
            self.log(f"✅ Audio note created: {note_id}")
            return note_id
        else:
            self.log(f"❌ Audio note creation failed: {response.status_code}")
            return None

    def upload_audio_to_note(self, note_id, format_type="mp3"):
        """Upload audio file to existing note"""
        # Create dummy audio file
        audio_data = {
            "mp3": b'\xff\xfb\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
            "wav": b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00',
            "webm": b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
        }
        
        with tempfile.NamedTemporaryFile(suffix=f'.{format_type}', delete=False) as tmp_file:
            tmp_file.write(audio_data.get(format_type, audio_data["mp3"]))
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': (f'test_audio.{format_type}', f, f'audio/{format_type}')}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                
                response = requests.post(
                    f"{self.api_url}/notes/{note_id}/upload",
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ Audio uploaded successfully: {data.get('status')}")
                    return True
                else:
                    self.log(f"❌ Audio upload failed: {response.status_code} - {response.text}")
                    return False
            
            os.unlink(tmp_file.name)

    def check_note_processing(self, note_id, max_wait=60):
        """Check note processing status"""
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        start_time = time.time()
        
        self.log(f"⏳ Monitoring processing for note {note_id[:8]}...")
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{self.api_url}/notes/{note_id}", headers=headers)
            
            if response.status_code == 200:
                note_data = response.json()
                status = note_data.get('status', 'unknown')
                
                self.log(f"   Status: {status}")
                
                if status == 'ready':
                    artifacts = note_data.get('artifacts', {})
                    self.log(f"✅ Processing completed!")
                    self.log(f"   Artifacts: {list(artifacts.keys())}")
                    if 'transcript' in artifacts:
                        transcript = artifacts['transcript']
                        self.log(f"   Transcript length: {len(transcript)} chars")
                        self.log(f"   Transcript preview: {transcript[:100]}...")
                    return True, note_data
                elif status == 'failed':
                    self.log(f"❌ Processing failed!")
                    return False, note_data
                elif status in ['uploading', 'processing']:
                    time.sleep(3)
                else:
                    self.log(f"   Unknown status: {status}")
                    time.sleep(2)
            else:
                self.log(f"❌ Failed to check status: {response.status_code}")
                break
        
        self.log(f"⏰ Processing timeout after {max_wait}s")
        return False, {}

    def test_audio_formats(self):
        """Test different audio formats"""
        formats = ["mp3", "wav", "webm"]
        results = []
        
        for format_type in formats:
            self.log(f"\n🎵 Testing {format_type.upper()} format")
            
            # Create note
            note_id = self.create_audio_note()
            if not note_id:
                results.append((format_type, False, "Note creation failed"))
                continue
            
            # Upload audio
            upload_success = self.upload_audio_to_note(note_id, format_type)
            if not upload_success:
                results.append((format_type, False, "Upload failed"))
                continue
            
            # Check processing
            processing_success, note_data = self.check_note_processing(note_id)
            if processing_success:
                results.append((format_type, True, "Success"))
            else:
                results.append((format_type, False, "Processing failed"))
        
        return results

    def run_focused_tests(self):
        """Run focused audio tests"""
        self.log("🎯 Starting Focused Audio Upload Tests")
        
        # Register user
        if not self.register_user():
            return False
        
        # Test audio formats
        results = self.test_audio_formats()
        
        # Print results
        self.log("\n" + "="*50)
        self.log("📊 FOCUSED AUDIO TEST RESULTS")
        self.log("="*50)
        
        for format_type, success, message in results:
            status = "✅" if success else "❌"
            self.log(f"{status} {format_type.upper()}: {message}")
        
        successful = sum(1 for _, success, _ in results if success)
        total = len(results)
        self.log(f"\nSuccess rate: {successful}/{total} ({successful/total*100:.1f}%)")
        
        if self.created_notes:
            self.log(f"Created notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        return successful > 0

def main():
    tester = FocusedAudioTester()
    
    try:
        success = tester.run_focused_tests()
        if success:
            print("\n🎉 Audio upload functionality is working!")
            return 0
        else:
            print("\n⚠️  Audio upload functionality has issues.")
            return 1
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())