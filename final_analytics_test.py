#!/usr/bin/env python3
"""
Final Analytics Endpoints Test
"""

import requests
import json
import uuid

# Configuration
BACKEND_URL = "https://insight-api.preview.emergentagent.com/api"
TEST_USER_PASSWORD = "TestPassword123"

def setup_auth():
    """Set up authentication"""
    session = requests.Session()
    
    # Generate unique user
    unique_id = uuid.uuid4().hex[:8]
    unique_email = f"final_analytics_{unique_id}@example.com"
    unique_username = f"finaluser{unique_id}"
    
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": TEST_USER_PASSWORD,
        "first_name": "Final",
        "last_name": "User"
    }
    
    response = session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data["access_token"]
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        print(f"✅ Authenticated as {unique_email}")
        return session
    else:
        print(f"❌ Auth failed: {response.status_code} - {response.text}")
        return None

def test_all_analytics_endpoints(session):
    """Test all analytics endpoints"""
    endpoints = [
        "/analytics/weekly-usage",
        "/analytics/monthly-overview",
        "/analytics/daily-activity", 
        "/analytics/performance-insights"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing {endpoint}...")
        
        response = session.get(f"{BACKEND_URL}{endpoint}", timeout=15)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON Response received")
                print(f"Success: {data.get('success')}")
                
                if data.get("success") and "data" in data:
                    endpoint_data = data["data"]
                    print(f"Data type: {type(endpoint_data)}")
                    
                    if isinstance(endpoint_data, dict):
                        print(f"Data keys: {list(endpoint_data.keys())}")
                    elif isinstance(endpoint_data, list):
                        print(f"Data length: {len(endpoint_data)}")
                        if len(endpoint_data) > 0:
                            print(f"First item keys: {list(endpoint_data[0].keys()) if isinstance(endpoint_data[0], dict) else 'Not a dict'}")
                    
                    results[endpoint] = "✅ PASS"
                else:
                    print(f"❌ Invalid response structure")
                    results[endpoint] = "❌ FAIL - Invalid structure"
                    
            except Exception as e:
                print(f"❌ JSON parsing error: {e}")
                results[endpoint] = f"❌ FAIL - JSON error: {e}"
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            results[endpoint] = f"❌ FAIL - HTTP {response.status_code}"
    
    return results

def test_authentication_protection(session):
    """Test authentication protection"""
    print(f"\n🔒 Testing Authentication Protection...")
    
    # Remove auth header
    original_headers = session.headers.copy()
    if "Authorization" in session.headers:
        del session.headers["Authorization"]
    
    endpoints = [
        "/analytics/weekly-usage",
        "/analytics/monthly-overview",
        "/analytics/daily-activity",
        "/analytics/performance-insights"
    ]
    
    protected_count = 0
    for endpoint in endpoints:
        response = session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
        if response.status_code in [401, 403]:
            protected_count += 1
            print(f"✅ {endpoint}: Protected (HTTP {response.status_code})")
        else:
            print(f"❌ {endpoint}: Not protected (HTTP {response.status_code})")
    
    # Restore headers
    session.headers.update(original_headers)
    
    return protected_count == len(endpoints)

if __name__ == "__main__":
    print("📊 Final Analytics Endpoints Test")
    print("=" * 50)
    
    session = setup_auth()
    if not session:
        exit(1)
    
    # Test all endpoints
    results = test_all_analytics_endpoints(session)
    
    # Test authentication
    auth_protected = test_authentication_protection(session)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 50)
    
    for endpoint, result in results.items():
        print(f"{result}: {endpoint}")
    
    if auth_protected:
        print("✅ PASS: Authentication Protection")
    else:
        print("❌ FAIL: Authentication Protection")
    
    passed = sum(1 for result in results.values() if result.startswith("✅"))
    total = len(results) + (1 if auth_protected else 0)
    
    print(f"\n📈 SUCCESS RATE: {passed + (1 if auth_protected else 0)}/{total + 1} ({((passed + (1 if auth_protected else 0))/(total + 1))*100:.1f}%)")