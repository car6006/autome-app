#!/usr/bin/env python3
"""
Debug Analytics Endpoints
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
    unique_email = f"debug_analytics_{unique_id}@example.com"
    unique_username = f"debuguser{unique_id}"
    
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": TEST_USER_PASSWORD,
        "first_name": "Debug",
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

def test_performance_insights(session):
    """Test performance insights endpoint and show raw response"""
    print("\n🔍 Testing Performance Insights Endpoint...")
    
    response = session.get(f"{BACKEND_URL}/analytics/performance-insights", timeout=15)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    try:
        data = response.json()
        print(f"Raw Response: {json.dumps(data, indent=2)}")
        
        if data.get("success") and "data" in data:
            insights_data = data["data"]
            print(f"Insights Data Keys: {list(insights_data.keys())}")
            print(f"Insights Data: {json.dumps(insights_data, indent=2)}")
        else:
            print("❌ Invalid response structure")
            
    except Exception as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw text: {response.text}")

if __name__ == "__main__":
    session = setup_auth()
    if session:
        test_performance_insights(session)