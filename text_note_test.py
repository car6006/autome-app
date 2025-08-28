#!/usr/bin/env python3
"""
Test script for text note functionality
"""

import asyncio
import httpx
import json

BASE_URL = "https://whisper-async-fix.preview.emergentagent.com/api"

async def test_text_note_creation():
    """Test creating a text note"""
    print("Testing text note creation...")
    
    async with httpx.AsyncClient() as client:
        # Test creating a text note
        note_data = {
            "title": "Test Text Note",
            "kind": "text",
            "text_content": "This is a test text note with some sample content."
        }
        
        response = await client.post(f"{BASE_URL}/notes", json=note_data)
        print(f"Create note response: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        if response.status_code == 200:
            note_id = response.json()["id"]
            print(f"Created note with ID: {note_id}")
            
            # Get the note to verify it was created correctly
            get_response = await client.get(f"{BASE_URL}/notes/{note_id}")
            print(f"Get note response: {get_response.status_code}")
            
            if get_response.status_code == 200:
                note = get_response.json()
                print(f"Note details: {json.dumps(note, indent=2)}")
                
                # Verify the note has the correct properties
                assert note["kind"] == "text"
                assert note["status"] == "ready"
                assert "text" in note["artifacts"]
                assert note["artifacts"]["text"] == "This is a test text note with some sample content."
                print("✅ Text note creation test passed!")
                return True
            else:
                print(f"❌ Failed to get note: {get_response.text}")
                return False
        else:
            print(f"❌ Failed to create note: {response.text}")
            return False

async def test_text_note_without_content():
    """Test creating a text note without content"""
    print("\nTesting text note creation without content...")
    
    async with httpx.AsyncClient() as client:
        note_data = {
            "title": "Empty Text Note",
            "kind": "text"
        }
        
        response = await client.post(f"{BASE_URL}/notes", json=note_data)
        print(f"Create note response: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        if response.status_code == 200:
            note_id = response.json()["id"]
            
            # Get the note to verify it was created correctly
            get_response = await client.get(f"{BASE_URL}/notes/{note_id}")
            
            if get_response.status_code == 200:
                note = get_response.json()
                print(f"Note details: {json.dumps(note, indent=2)}")
                
                # Verify the note has the correct properties
                assert note["kind"] == "text"
                assert note["status"] == "created"  # Should not be ready without content
                print("✅ Empty text note creation test passed!")
                return True
            else:
                print(f"❌ Failed to get note: {get_response.text}")
                return False
        else:
            print(f"❌ Failed to create note: {response.text}")
            return False

async def main():
    """Run all tests"""
    print("Starting text note functionality tests...\n")
    
    try:
        # Test 1: Create text note with content
        test1_passed = await test_text_note_creation()
        
        # Test 2: Create text note without content
        test2_passed = await test_text_note_without_content()
        
        if test1_passed and test2_passed:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())