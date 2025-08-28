#!/usr/bin/env python3
import requests
import tempfile
import os
import time

# Test the file upload endpoint
base_url = 'https://whisper-async-fix.preview.emergentagent.com'
api_url = f'{base_url}/api'

print("Testing file upload endpoint...")

# Create a test image
png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'

with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
    tmp_file.write(png_data)
    tmp_file.flush()
    
    with open(tmp_file.name, 'rb') as f:
        files = {'file': ('test_upload.png', f, 'image/png')}
        data = {'title': 'File Upload Test'}
        
        response = requests.post(f'{api_url}/upload-file', data=data, files=files)
        print(f'Upload file endpoint status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Upload successful: {result}')
            note_id = result.get('id')
            
            # Check the note status
            time.sleep(2)
            note_response = requests.get(f'{api_url}/notes/{note_id}')
            if note_response.status_code == 200:
                note_data = note_response.json()
                print(f'Note status: {note_data.get("status")}')
                print(f'Note artifacts: {list(note_data.get("artifacts", {}).keys())}')
                
                # Test JSON export
                export_response = requests.get(f'{api_url}/notes/{note_id}/export?format=json')
                print(f'JSON export status: {export_response.status_code}')
                if export_response.status_code == 200:
                    export_data = export_response.json()
                    print(f'JSON export successful with created_at: {export_data.get("created_at")}')
        else:
            print(f'Upload failed: {response.text}')
    
    os.unlink(tmp_file.name)