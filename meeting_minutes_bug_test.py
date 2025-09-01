#!/usr/bin/env python3
"""
Quick test to verify the meeting minutes bug
"""

import requests
import time

def test_meeting_minutes_bug():
    base_url = "https://pwa-integration-fix.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Register user
    user_data = {
        "email": f"bug_test_{int(time.time())}@example.com",
        "username": f"buguser{int(time.time())}",
        "password": "BugTest123!",
        "first_name": "Bug",
        "last_name": "Tester"
    }
    
    response = requests.post(f"{api_url}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code}")
        return
    
    auth_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    # Create text note with content
    note_data = {
        "title": "Meeting Minutes Bug Test",
        "kind": "text",
        "text_content": "Meeting discussion about project status and next steps."
    }
    
    response = requests.post(f"{api_url}/notes", json=note_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Note creation failed: {response.status_code}")
        return
    
    note_id = response.json()['id']
    print(f"✅ Created note: {note_id}")
    
    # Check note content
    response = requests.get(f"{api_url}/notes/{note_id}", headers=headers)
    if response.status_code == 200:
        note = response.json()
        artifacts = note.get('artifacts', {})
        print(f"📝 Note artifacts: {list(artifacts.keys())}")
        print(f"   Has text: {'text' in artifacts}")
        print(f"   Has transcript: {'transcript' in artifacts}")
        print(f"   Has ai_conversations: {'ai_conversations' in artifacts}")
    
    # Test professional report generation (should work)
    print("\n🔍 Testing professional report generation...")
    response = requests.post(f"{api_url}/notes/{note_id}/generate-report", headers=headers, timeout=60)
    print(f"   Professional report: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.json()}")
    
    # Test meeting minutes generation (should fail due to bug)
    print("\n🔍 Testing meeting minutes generation...")
    response = requests.post(f"{api_url}/notes/{note_id}/generate-meeting-minutes", headers=headers, timeout=60)
    print(f"   Meeting minutes: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.json()}")
        if "No content available" in response.json().get('detail', ''):
            print("   🐛 BUG CONFIRMED: Meeting minutes endpoint doesn't check 'text' content!")

if __name__ == "__main__":
    test_meeting_minutes_bug()