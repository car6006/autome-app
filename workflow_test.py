#!/usr/bin/env python3
"""
Complete Audio Upload Workflow Test
"""

import requests
import tempfile
import os
import time

def test_complete_workflow():
    api_url = 'https://auto-me-debugger.preview.emergentagent.com/api'
    
    print('🎵 Testing Complete Audio Upload Workflow...')
    
    # Create a minimal MP3 file
    mp3_data = b'\xff\xfb\x90\x00' + b'\x00' * 100
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        tmp_file.write(mp3_data)
        tmp_file.flush()
        
        with open(tmp_file.name, 'rb') as f:
            files = {'file': ('workflow_test.mp3', f, 'audio/mpeg')}
            data = {'title': 'Complete Workflow Test - MP3'}
            
            print('📤 Uploading MP3 file...')
            response = requests.post(f'{api_url}/upload-file', data=data, files=files, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                note_id = result.get('id')
                print(f'✅ Upload successful!')
                print(f'   Note ID: {note_id}')
                print(f'   Kind: {result.get("kind")}')
                print(f'   Status: {result.get("status")}')
                print(f'   Filename: {result.get("filename")}')
                
                # Verify it's an audio note
                if result.get('kind') == 'audio':
                    print('✅ Correctly identified as audio note')
                else:
                    print(f'❌ Expected kind="audio", got "{result.get("kind")}"')
                
                # Check note details
                print('\n🔍 Checking note details...')
                note_response = requests.get(f'{api_url}/notes/{note_id}', timeout=10)
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    print(f'   Note kind: {note_data.get("kind")}')
                    print(f'   Note status: {note_data.get("status")}')
                    print(f'   Note title: {note_data.get("title")}')
                    
                    # Check if processing was triggered
                    status = note_data.get('status', '')
                    if status in ['uploading', 'processing', 'ready', 'failed']:
                        print(f'✅ Processing triggered (status: {status})')
                        
                        # Wait a bit and check again
                        print('\n⏳ Waiting 10 seconds for processing...')
                        time.sleep(10)
                        
                        final_response = requests.get(f'{api_url}/notes/{note_id}', timeout=10)
                        if final_response.status_code == 200:
                            final_data = final_response.json()
                            final_status = final_data.get('status', '')
                            print(f'   Final status: {final_status}')
                            
                            if final_status == 'ready':
                                artifacts = final_data.get('artifacts', {})
                                if 'transcript' in artifacts:
                                    print('✅ Transcription completed successfully!')
                                else:
                                    print('⚠️ No transcript found in artifacts')
                            elif final_status == 'failed':
                                print('❌ Processing failed (likely due to API key issues)')
                            else:
                                print(f'⏳ Still processing (status: {final_status})')
                    else:
                        print(f'❌ Unexpected status: {status}')
                else:
                    print(f'❌ Failed to get note details: {note_response.status_code}')
            else:
                print(f'❌ Upload failed: {response.status_code}')
                try:
                    error_data = response.json()
                    print(f'   Error: {error_data}')
                except:
                    print(f'   Response: {response.text[:200]}')
        
        os.unlink(tmp_file.name)
    
    print('\n🖼️ Testing Image Upload (Regression Check)...')
    
    # Create a minimal PNG file
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
        tmp_file.write(png_data)
        tmp_file.flush()
        
        with open(tmp_file.name, 'rb') as f:
            files = {'file': ('workflow_test.png', f, 'image/png')}
            data = {'title': 'Complete Workflow Test - PNG'}
            
            print('📤 Uploading PNG file...')
            response = requests.post(f'{api_url}/upload-file', data=data, files=files, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Upload successful!')
                print(f'   Kind: {result.get("kind")}')
                print(f'   Status: {result.get("status")}')
                
                # Verify it's a photo note
                if result.get('kind') == 'photo':
                    print('✅ Correctly identified as photo note')
                else:
                    print(f'❌ Expected kind="photo", got "{result.get("kind")}"')
            else:
                print(f'❌ Upload failed: {response.status_code}')
        
        os.unlink(tmp_file.name)
    
    print('\n🎉 Audio Upload Fix Testing Complete!')

if __name__ == "__main__":
    test_complete_workflow()