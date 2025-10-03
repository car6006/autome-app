#!/usr/bin/env python3
"""
Debug Performance Insights Endpoint
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
    unique_email = f"debug_perf_{unique_id}@example.com"
    unique_username = f"debugperf{unique_id}"
    
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

def debug_performance_insights(session):
    """Debug performance insights endpoint step by step"""
    print("\n🔍 Debugging Performance Insights Endpoint...")
    
    response = session.get(f"{BACKEND_URL}/analytics/performance-insights", timeout=15)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Non-200 status: {response.text}")
        return
    
    try:
        data = response.json()
        print(f"✅ JSON Response received")
        print(f"Response keys: {list(data.keys())}")
        
        # Check success field
        success = data.get("success")
        print(f"Success field: {success} (type: {type(success)})")
        
        # Check data field
        if "data" in data:
            insights_data = data["data"]
            print(f"✅ Data field exists")
            print(f"Data type: {type(insights_data)}")
            print(f"Data keys: {list(insights_data.keys())}")
            
            # Check each required field
            required_fields = ["weekly_average", "peak_day", "streak", "success_rate", 
                             "total_notes", "estimated_minutes_saved"]
            
            print("\n🔍 Checking required fields:")
            for field in required_fields:
                if field in insights_data:
                    value = insights_data[field]
                    print(f"✅ {field}: {value} (type: {type(value)})")
                else:
                    print(f"❌ {field}: MISSING")
            
            # Show all fields in data
            print(f"\n📋 All fields in insights_data:")
            for key, value in insights_data.items():
                print(f"   {key}: {value} (type: {type(value)})")
                
        else:
            print("❌ No 'data' field in response")
            
    except Exception as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    session = setup_auth()
    if session:
        debug_performance_insights(session)