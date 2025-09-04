#!/usr/bin/env python3
"""
Debug Meeting Minutes Generation Issue
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-ai.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def debug_meeting_minutes():
    """Debug the meeting minutes generation issue"""
    
    # Register user
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    register_data = {
        "email": f"debugtest{timestamp}@test.com",
        "username": f"debugtest{timestamp}",
        "password": "TestPass123!",
        "first_name": "Debug",
        "last_name": "Test"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Register
        response = await client.post(f"{API_BASE}/auth/register", json=register_data)
        if response.status_code != 200:
            print(f"❌ Registration failed: {response.status_code}")
            return
        
        data = response.json()
        auth_token = data["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        print(f"✅ User registered: {data['user']['id']}")
        
        # Create simple text note
        note_data = {
            "title": "Simple Meeting Test",
            "kind": "text",
            "text_content": "This is a simple meeting note with some content for testing meeting minutes generation."
        }
        
        response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Note creation failed: {response.status_code}")
            return
        
        note_info = response.json()
        note_id = note_info["id"]
        print(f"✅ Note created: {note_id}")
        
        # Check note content
        response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
        if response.status_code == 200:
            note_data = response.json()
            artifacts = note_data.get("artifacts", {})
            text_content = artifacts.get("text", "")
            print(f"✅ Note text content: '{text_content}' (length: {len(text_content)})")
        
        # Test professional report first (should work)
        print("\n🔍 Testing professional report generation...")
        response = await client.post(f"{API_BASE}/notes/{note_id}/generate-report", headers=headers)
        if response.status_code == 200:
            report_data = response.json()
            report = report_data.get("report", "")
            print(f"✅ Professional report generated: {len(report)} characters")
        else:
            print(f"❌ Professional report failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error text: {response.text}")
        
        # Test meeting minutes (the problematic one)
        print("\n🔍 Testing meeting minutes generation...")
        response = await client.post(f"{API_BASE}/notes/{note_id}/generate-meeting-minutes", headers=headers)
        if response.status_code == 200:
            minutes_data = response.json()
            minutes = minutes_data.get("meeting_minutes", "")
            print(f"✅ Meeting minutes generated: {len(minutes)} characters")
        else:
            print(f"❌ Meeting minutes failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error text: {response.text}")
        
        # Cleanup
        await client.delete(f"{API_BASE}/notes/{note_id}", headers=headers)

if __name__ == "__main__":
    asyncio.run(debug_meeting_minutes())