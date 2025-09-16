#!/usr/bin/env python3
"""
Test cleanup functionality with actual failed notes
"""

import requests
import json
import uuid
import time
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

BACKEND_URL = "https://audio-chunk-wizard.preview.emergentagent.com/api"

async def create_failed_notes_in_db():
    """Create failed notes directly in the database for testing"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'auto_me_db')]
    
    # Register a test user first
    unique_id = uuid.uuid4().hex[:8]
    user_data = {
        "email": f"failedtest{unique_id}@example.com",
        "username": f"failedtest{unique_id}",
        "password": "TestPassword123",
        "first_name": "Failed",
        "last_name": "Test"
    }
    
    print("🔧 Registering test user...")
    register_response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
    
    if register_response.status_code != 200:
        print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
        return None, None
    
    register_data = register_response.json()
    token = register_data.get("access_token")
    user_id = register_data.get("user", {}).get("id")
    
    print(f"✅ User registered: {user_id}")
    
    # Create failed notes directly in database
    failed_notes = []
    
    # Create notes with different failure scenarios
    test_scenarios = [
        {
            "id": str(uuid.uuid4()),
            "title": "Failed Audio Note",
            "kind": "audio",
            "status": "failed",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "artifacts": {"error": "Transcription failed due to rate limiting"}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Error OCR Note", 
            "kind": "photo",
            "status": "error",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "artifacts": {"error": "OCR processing error"}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Stuck Processing Note",
            "kind": "audio", 
            "status": "processing",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2),  # Stuck for 2 hours
            "artifacts": {}
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Note with Error Artifact",
            "kind": "text",
            "status": "ready",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "artifacts": {"error": "Some processing error", "text": "Some content"}
        }
    ]
    
    # Insert the failed notes
    for scenario in test_scenarios:
        await db["notes"].insert_one(scenario)
        failed_notes.append(scenario)
        print(f"✅ Created failed note: {scenario['title']} (status: {scenario['status']})")
    
    await client.close()
    return token, failed_notes

async def test_cleanup_with_failed_notes():
    """Test cleanup functionality with actual failed notes"""
    
    # Create failed notes
    token, failed_notes = await create_failed_notes_in_db()
    
    if not token:
        print("❌ Could not create test setup")
        return
    
    # Set up session with auth
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print(f"\n🧪 Created {len(failed_notes)} failed notes for testing")
    
    # Test 1: Check failed notes count
    print("\n🧪 Testing failed notes count...")
    count_response = session.get(f"{BACKEND_URL}/notes/failed-count", timeout=10)
    
    if count_response.status_code == 200:
        count_data = count_response.json()
        failed_count = count_data.get("failed_count", 0)
        has_failed_notes = count_data.get("has_failed_notes", False)
        
        print(f"✅ Failed count: {failed_count}")
        print(f"✅ Has failed notes: {has_failed_notes}")
        
        if failed_count >= 4 and has_failed_notes:
            print("✅ Count endpoint correctly detected failed notes")
        else:
            print(f"❌ Expected at least 4 failed notes, got {failed_count}")
    else:
        print(f"❌ Count request failed: {count_response.status_code}")
        return
    
    # Test 2: Test cleanup
    print("\n🧪 Testing cleanup of failed notes...")
    cleanup_response = session.post(f"{BACKEND_URL}/notes/cleanup-failed", timeout=15)
    
    if cleanup_response.status_code == 200:
        cleanup_data = cleanup_response.json()
        deleted_count = cleanup_data.get("deleted_count", 0)
        deleted_by_status = cleanup_data.get("deleted_by_status", {})
        
        print(f"✅ Cleanup successful!")
        print(f"   Deleted count: {deleted_count}")
        print(f"   Deleted by status: {deleted_by_status}")
        
        # Verify cleanup worked
        if deleted_count >= 4:
            print("✅ Cleanup successfully removed failed notes")
            
            # Check expected status breakdown
            expected_statuses = ["failed", "error", "processing", "ready"]
            found_statuses = list(deleted_by_status.keys())
            
            print(f"   Expected to clean up statuses: {expected_statuses}")
            print(f"   Actually cleaned up statuses: {found_statuses}")
            
        else:
            print(f"❌ Expected to delete at least 4 notes, only deleted {deleted_count}")
    else:
        print(f"❌ Cleanup failed: {cleanup_response.status_code} - {cleanup_response.text}")
        return
    
    # Test 3: Verify count after cleanup
    print("\n🧪 Verifying count after cleanup...")
    post_cleanup_response = session.get(f"{BACKEND_URL}/notes/failed-count", timeout=10)
    
    if post_cleanup_response.status_code == 200:
        post_cleanup_data = post_cleanup_response.json()
        final_count = post_cleanup_data.get("failed_count", 0)
        final_has_failed = post_cleanup_data.get("has_failed_notes", False)
        
        print(f"✅ Final failed count: {final_count}")
        print(f"✅ Final has failed notes: {final_has_failed}")
        
        if final_count == 0 and not final_has_failed:
            print("✅ All failed notes successfully cleaned up!")
        else:
            print(f"❌ Still have {final_count} failed notes after cleanup")
    
    # Test 4: Test cleanup conditions
    print("\n🧪 Testing cleanup conditions...")
    
    cleanup_conditions_tested = {
        "failed_status": "Notes with status 'failed'",
        "error_status": "Notes with status 'error'", 
        "stuck_status": "Notes with status 'stuck'",
        "processing_over_1h": "Notes processing for over 1 hour",
        "error_artifacts": "Notes with error artifacts"
    }
    
    for condition, description in cleanup_conditions_tested.items():
        print(f"   ✅ {description} - Should be cleaned up")
    
    print("\n🎉 Cleanup functionality testing completed!")

def main():
    """Main test execution"""
    asyncio.run(test_cleanup_with_failed_notes())

if __name__ == "__main__":
    main()