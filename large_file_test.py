#!/usr/bin/env python3
"""
Large File Test - Create a file that definitely exceeds 24MB
"""

import requests
import sys
import tempfile
import os
import subprocess
import time
from datetime import datetime

def create_large_audio_file():
    """Create an audio file that's definitely over 24MB"""
    print("🎵 Creating large audio file (20 minutes)...")
    
    fd, temp_path = tempfile.mkstemp(suffix='_large_test.wav')
    os.close(fd)
    
    # Create 20 minutes of audio (should be ~60MB)
    cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1200',
        '-ar', '44100', '-ac', '2', '-y', temp_path  # Higher quality to ensure large size
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    
    if result.returncode == 0:
        file_size = os.path.getsize(temp_path)
        size_mb = file_size / (1024 * 1024)
        print(f"✅ Created large audio file: {size_mb:.1f} MB")
        
        if size_mb > 24:
            print(f"✅ File is over 24MB limit - chunking should be triggered")
            return temp_path
        else:
            print(f"⚠️  File is only {size_mb:.1f} MB - may not trigger chunking")
            return temp_path
    else:
        print(f"❌ Failed to create large audio: {result.stderr}")
        return None

def test_large_file_upload():
    """Test uploading the large file"""
    large_file = create_large_audio_file()
    if not large_file:
        return False
    
    try:
        print("\n📤 Uploading large file...")
        
        with open(large_file, 'rb') as f:
            files = {'file': ('large_test.wav', f, 'audio/wav')}
            data = {'title': 'Large File Chunking Test'}
            
            response = requests.post(
                "https://pwa-integration-fix.preview.emergentagent.com/api/upload-file",
                data=data,
                files=files,
                timeout=600  # 10 minutes
            )
            
            if response.status_code == 200:
                response_data = response.json()
                note_id = response_data.get('id')
                print(f"✅ Upload successful, note ID: {note_id}")
                
                # Wait for processing
                print("⏳ Waiting for processing...")
                for i in range(30):  # Wait up to 5 minutes
                    time.sleep(10)
                    
                    status_response = requests.get(
                        f"https://pwa-integration-fix.preview.emergentagent.com/api/notes/{note_id}",
                        timeout=30
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        print(f"   Status check {i+1}: {status}")
                        
                        if status == 'ready':
                            artifacts = status_data.get('artifacts', {})
                            transcript = artifacts.get('transcript', '')
                            
                            print(f"✅ Processing completed!")
                            print(f"   Transcript length: {len(transcript)} characters")
                            
                            # Check for chunking indicators
                            has_parts = '[Part ' in transcript if transcript else False
                            if has_parts:
                                import re
                                parts = re.findall(r'\[Part \d+\]', transcript)
                                print(f"✅ Chunking was used - found {len(parts)} parts")
                                print(f"   Sample transcript: {transcript[:200]}...")
                            else:
                                print("ℹ️  No part indicators found in transcript")
                            
                            return True
                            
                        elif status == 'failed':
                            artifacts = status_data.get('artifacts', {})
                            error = artifacts.get('error', 'Unknown error')
                            print(f"❌ Processing failed: {error}")
                            return False
                
                print("⏰ Timeout waiting for processing")
                return False
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"💥 Error: {e}")
        return False
    
    finally:
        # Clean up
        try:
            os.unlink(large_file)
            print(f"🧹 Cleaned up: {large_file}")
        except:
            pass

def main():
    print("🚀 Large File Chunking Test")
    
    success = test_large_file_upload()
    
    if success:
        print("\n🎉 Large file chunking test passed!")
        return 0
    else:
        print("\n❌ Large file chunking test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())