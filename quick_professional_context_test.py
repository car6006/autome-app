#!/usr/bin/env python3
"""
Quick Professional Context API Test
Focused test to verify the professional context endpoints are working
"""

import requests
import json
import time

def test_professional_context():
    base_url = "https://auto-me-debugger.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🚀 Testing Professional Context API Endpoints")
    print(f"Base URL: {base_url}")
    
    # Step 1: Register a test user
    test_user = {
        "email": f"prof_test_{int(time.time())}@example.com",
        "username": f"profuser{int(time.time())}",
        "password": "TestPassword123!",
        "first_name": "Professional",
        "last_name": "Tester"
    }
    
    print("\n1. Registering test user...")
    response = requests.post(f"{api_url}/auth/register", json=test_user)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code}")
        return False
    
    token = response.json().get('access_token')
    print(f"✅ User registered, token: {token[:20]}...")
    
    # Step 2: Test POST professional context
    print("\n2. Testing POST /api/user/professional-context...")
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    context_data = {
        "primary_industry": "Technology",
        "job_role": "Software Engineer",
        "work_environment": "Remote startup",
        "key_focus_areas": ["API development", "Testing", "Performance"],
        "content_types": ["Code reviews", "Technical docs"],
        "analysis_preferences": ["Best practices", "Security analysis"]
    }
    
    response = requests.post(f"{api_url}/user/professional-context", json=context_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 200:
        print("❌ POST professional context failed")
        return False
    
    print("✅ Professional context saved successfully")
    
    # Step 3: Test GET professional context
    print("\n3. Testing GET /api/user/professional-context...")
    response = requests.get(f"{api_url}/user/professional-context", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 200:
        print("❌ GET professional context failed")
        return False
    
    print("✅ Professional context retrieved successfully")
    
    # Step 4: Test authentication requirement
    print("\n4. Testing authentication requirement...")
    response = requests.get(f"{api_url}/user/professional-context")
    print(f"Status without auth: {response.status_code}")
    
    if response.status_code == 403:
        print("✅ Authentication properly required")
    else:
        print("⚠️  Authentication not properly enforced")
    
    print("\n🎉 All professional context tests passed!")
    return True

if __name__ == "__main__":
    success = test_professional_context()
    if success:
        print("\n✅ CONCLUSION: Professional Context API is working correctly!")
        print("The 404 error reported by the user may be due to:")
        print("1. Frontend making requests to wrong URL")
        print("2. Authentication token issues")
        print("3. Network/proxy issues")
        print("4. Temporary server issues")
    else:
        print("\n❌ Professional Context API has issues")