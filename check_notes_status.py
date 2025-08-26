#!/usr/bin/env python3
"""
Check the status of created notes to understand processing issues
"""

import requests
import json
import time

def check_note_status(note_id, auth_token):
    """Check the status of a specific note"""
    url = f"https://transcribe-ocr.preview.emergentagent.com/api/notes/{note_id}"
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"\n📝 Note ID: {note_id}")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Kind: {data.get('kind', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Created: {data.get('created_at', 'N/A')}")
            print(f"   Ready: {data.get('ready_at', 'N/A')}")
            
            artifacts = data.get('artifacts', {})
            print(f"   Artifacts: {list(artifacts.keys())}")
            
            if 'transcript' in artifacts:
                transcript = artifacts['transcript']
                print(f"   Transcript length: {len(transcript)} chars")
                if transcript:
                    print(f"   Transcript preview: {transcript[:100]}...")
            
            if 'text' in artifacts:
                text = artifacts['text']
                print(f"   OCR text length: {len(text)} chars")
            
            return data
        else:
            print(f"❌ Failed to get note {note_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking note {note_id}: {str(e)}")
        return None

def main():
    # Test notes from the previous run
    note_ids = [
        "2bb1a17c-4cb4-4e43-8ae2-17da6deb19d9",  # Large audio file
        "003f6538-9fec-4a53-afbb-b3aec3506839",  # Direct upload
        "bc54875f-1388-4e59-87bc-60a3d81614c4",  # AI chat test
        "8eeb8fa9-a1ec-440a-86fb-7c0c0d4769d3"   # Report generation test
    ]
    
    # Get auth token (register a new user)
    auth_data = {
        "email": f"status_check_{int(time.time())}@example.com",
        "username": f"statuscheck_{int(time.time())}",
        "password": "StatusCheck123!",
        "first_name": "Status",
        "last_name": "Checker"
    }
    
    try:
        response = requests.post(
            "https://transcribe-ocr.preview.emergentagent.com/api/auth/register",
            json=auth_data,
            timeout=10
        )
        
        if response.status_code == 200:
            auth_token = response.json().get('access_token')
            print(f"✅ Authentication successful")
            
            print("🔍 Checking note statuses...")
            for note_id in note_ids:
                check_note_status(note_id, auth_token)
                time.sleep(1)
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()