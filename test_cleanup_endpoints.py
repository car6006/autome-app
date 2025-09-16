#!/usr/bin/env python3
"""
Quick test script for cleanup endpoints
"""

import requests
import json
import uuid
from datetime import datetime, timedelta, timezone

BACKEND_URL = "https://audio-chunk-wizard.preview.emergentagent.com/api"

def test_cleanup_endpoints():
    """Test the cleanup endpoints specifically"""
    
    # Register a new user
    unique_id = uuid.uuid4().hex[:8]
    user_data = {
        "email": f"cleanuptest{unique_id}@example.com",
        "username": f"cleanuptest{unique_id}",
        "password": "TestPassword123",
        "first_name": "Cleanup",
        "last_name": "Test"
    }
    
    print("🔧 Registering test user...")
    register_response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
        return
    
    register_data = register_response.json()
    token = register_data.get("access_token")
    user_id = register_data.get("user", {}).get("id")
    
    if not token:
        print("❌ No token received from registration")
        return
    
    print(f"✅ User registered: {user_id}")
    
    # Set up session with auth
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Test 1: Failed notes count endpoint
    print("\n🧪 Testing /api/notes/failed-count endpoint...")
    count_response = session.get(f"{BACKEND_URL}/notes/failed-count", timeout=10)
    
    print(f"Status: {count_response.status_code}")
    if count_response.status_code == 200:
        count_data = count_response.json()
        print(f"✅ Response: {count_data}")
        
        # Validate response structure
        if "failed_count" in count_data and "has_failed_notes" in count_data:
            print("✅ Response structure is correct")
        else:
            print("❌ Missing required fields in response")
    else:
        print(f"❌ Failed: {count_response.text}")
    
    # Test 2: Cleanup endpoint
    print("\n🧪 Testing /api/notes/cleanup-failed endpoint...")
    cleanup_response = session.post(f"{BACKEND_URL}/notes/cleanup-failed", timeout=15)
    
    print(f"Status: {cleanup_response.status_code}")
    if cleanup_response.status_code == 200:
        cleanup_data = cleanup_response.json()
        print(f"✅ Response: {cleanup_data}")
        
        # Validate response structure
        required_fields = ["message", "deleted_count", "deleted_by_status", "timestamp"]
        if all(field in cleanup_data for field in required_fields):
            print("✅ Response structure is correct")
            print(f"   Deleted count: {cleanup_data['deleted_count']}")
            print(f"   Deleted by status: {cleanup_data['deleted_by_status']}")
        else:
            print(f"❌ Missing required fields. Expected: {required_fields}")
    else:
        print(f"❌ Failed: {cleanup_response.text}")
    
    # Test 3: Create some notes and test cleanup with actual data
    print("\n🧪 Creating test notes and testing cleanup...")
    
    # Create a few test notes
    test_notes = []
    for i in range(3):
        note_data = {
            "title": f"Cleanup Test Note {i+1}",
            "kind": "text", 
            "text_content": f"Test content {i+1}"
        }
        
        note_response = session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
        if note_response.status_code == 200:
            note_result = note_response.json()
            test_notes.append(note_result.get("id"))
            print(f"✅ Created note: {note_result.get('id')}")
    
    # Check count again
    print("\n🧪 Checking failed count after creating notes...")
    count_response2 = session.get(f"{BACKEND_URL}/notes/failed-count", timeout=10)
    if count_response2.status_code == 200:
        count_data2 = count_response2.json()
        print(f"✅ Failed count: {count_data2}")
    
    # Test cleanup again
    print("\n🧪 Testing cleanup after creating notes...")
    cleanup_response2 = session.post(f"{BACKEND_URL}/notes/cleanup-failed", timeout=15)
    if cleanup_response2.status_code == 200:
        cleanup_data2 = cleanup_response2.json()
        print(f"✅ Cleanup result: {cleanup_data2}")
    
    # Test 4: Test authentication requirement
    print("\n🧪 Testing authentication requirement...")
    
    # Remove auth header
    session.headers.pop("Authorization", None)
    
    unauth_count_response = session.get(f"{BACKEND_URL}/notes/failed-count", timeout=10)
    unauth_cleanup_response = session.post(f"{BACKEND_URL}/notes/cleanup-failed", timeout=10)
    
    print(f"Count without auth: {unauth_count_response.status_code}")
    print(f"Cleanup without auth: {unauth_cleanup_response.status_code}")
    
    if unauth_count_response.status_code in [401, 403] and unauth_cleanup_response.status_code in [401, 403]:
        print("✅ Both endpoints correctly require authentication")
    else:
        print("❌ Authentication not properly enforced")
    
    print("\n🎉 Cleanup endpoint testing completed!")

if __name__ == "__main__":
    test_cleanup_endpoints()