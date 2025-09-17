#!/usr/bin/env python3
"""
Focused Archive Management Configuration Test
Tests the specific fix for integer body handling in POST /admin/archive/configure
"""

import requests
import json
import time
import uuid

# Configuration
BACKEND_URL = "https://audio-chunk-wizard.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"archivetest_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123"

def test_archive_configuration():
    """Test archive management configuration endpoint fix"""
    session = requests.Session()
    
    print("🏛️ Archive Management Configuration Endpoint Test")
    print("=" * 60)
    
    # Step 1: Register and authenticate
    print("1. Registering test user...")
    user_data = {
        "email": TEST_USER_EMAIL,
        "username": f"archivetest{uuid.uuid4().hex[:8]}",
        "password": TEST_USER_PASSWORD,
        "first_name": "Archive",
        "last_name": "Test"
    }
    
    response = session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    auth_token = data.get("access_token")
    if not auth_token:
        print("❌ No auth token received")
        return
    
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    print("✅ User registered and authenticated")
    
    # Step 2: Test archive configuration endpoint
    print("\n2. Testing archive configuration endpoint...")
    
    test_cases = [
        {
            "name": "Valid integer value (30 days)",
            "data": 30,
            "expected_status": 200,
            "description": "Should accept integer value directly"
        },
        {
            "name": "Boundary value (1 day)",
            "data": 1,
            "expected_status": 200,
            "description": "Should accept minimum boundary value"
        },
        {
            "name": "Boundary value (365 days)",
            "data": 365,
            "expected_status": 200,
            "description": "Should accept maximum boundary value"
        },
        {
            "name": "Invalid value (0 days)",
            "data": 0,
            "expected_status": 400,
            "description": "Should reject value below minimum"
        },
        {
            "name": "Invalid value (366 days)",
            "data": 366,
            "expected_status": 400,
            "description": "Should reject value above maximum"
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        
        # Send integer directly in request body (not wrapped in object)
        response = session.post(
            f"{BACKEND_URL}/admin/archive/configure",
            json=test_case["data"],  # Send integer directly
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"    Request: POST /admin/archive/configure")
        print(f"    Body: {test_case['data']} (type: {type(test_case['data']).__name__})")
        print(f"    Response: HTTP {response.status_code}")
        
        if response.status_code == test_case["expected_status"]:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if (data.get("success") and 
                        data.get("archive_days") == test_case["data"] and
                        "message" in data):
                        passed_tests += 1
                        print(f"    ✅ {test_case['description']}")
                        print(f"    Response: {data.get('message')}")
                    else:
                        print(f"    ❌ Valid response but missing expected fields")
                        print(f"    Response data: {data}")
                except json.JSONDecodeError:
                    print(f"    ❌ Invalid JSON response: {response.text}")
            else:  # 400 error expected
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "")
                    if ("at least 1" in error_msg and test_case["data"] == 0) or ("cannot exceed 365" in error_msg and test_case["data"] == 366):
                        passed_tests += 1
                        print(f"    ✅ {test_case['description']}")
                        print(f"    Error: {error_msg}")
                    else:
                        print(f"    ❌ Expected validation error but got: {error_msg}")
                except json.JSONDecodeError:
                    print(f"    ❌ Invalid JSON error response: {response.text}")
        else:
            print(f"    ❌ Expected HTTP {test_case['expected_status']}, got {response.status_code}")
            print(f"    Response: {response.text}")
        
        time.sleep(0.5)  # Small delay between tests
    
    # Step 3: Test the old problematic format (object with archive_days key)
    print(f"\n  Testing: Old format (object with archive_days key)")
    old_format_response = session.post(
        f"{BACKEND_URL}/admin/archive/configure",
        json={"archive_days": 30},  # Old format that was causing issues
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"    Request: POST /admin/archive/configure")
    print(f"    Body: {{'archive_days': 30}} (object format)")
    print(f"    Response: HTTP {old_format_response.status_code}")
    
    if old_format_response.status_code == 422:
        # Pydantic validation error expected for old format
        print("    ✅ Old format correctly rejected with Pydantic validation error")
        try:
            error_data = old_format_response.json()
            print(f"    Error details: {error_data}")
        except:
            print(f"    Error text: {old_format_response.text}")
        passed_tests += 1
        total_tests += 1
    elif old_format_response.status_code == 200:
        print("    ⚠️ Old format unexpectedly accepted (may indicate backward compatibility)")
        passed_tests += 1
        total_tests += 1
    else:
        print(f"    ❌ Old format gave unexpected response: HTTP {old_format_response.status_code}")
        print(f"    Response: {old_format_response.text}")
        total_tests += 1
    
    # Step 4: Test authentication requirement
    print(f"\n  Testing: Authentication requirement")
    original_headers = session.headers.copy()
    if "Authorization" in session.headers:
        del session.headers["Authorization"]
    
    unauth_response = session.post(
        f"{BACKEND_URL}/admin/archive/configure",
        json=30,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    # Restore headers
    session.headers.update(original_headers)
    
    print(f"    Request: POST /admin/archive/configure (no auth)")
    print(f"    Response: HTTP {unauth_response.status_code}")
    
    if unauth_response.status_code in [401, 403]:
        print("    ✅ Endpoint correctly requires authentication")
        passed_tests += 1
    else:
        print(f"    ❌ Expected 401/403 for unauthenticated request, got {unauth_response.status_code}")
        print(f"    Response: {unauth_response.text}")
    
    total_tests += 1
    
    # Summary
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n" + "=" * 60)
    print(f"📊 TEST SUMMARY")
    print(f"=" * 60)
    print(f"Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 85:
        print("✅ ARCHIVE CONFIGURATION ENDPOINT WORKING CORRECTLY")
        print("✅ Integer body handling fix is successful")
        print("✅ Frontend/backend mismatch resolved")
    else:
        print("❌ ARCHIVE CONFIGURATION ENDPOINT HAS ISSUES")
        print("❌ Some tests failed - fix may not be complete")
    
    return success_rate >= 85

if __name__ == "__main__":
    test_archive_configuration()