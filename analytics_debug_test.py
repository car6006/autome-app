#!/usr/bin/env python3
"""
Analytics Debugging Test - Focused test for analytics data issue
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://insight-api.preview.emergentagent.com/api"

class AnalyticsDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def register_and_login(self):
        """Register a new user for testing"""
        try:
            # Generate unique email and username for this test
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"analytics_debug_{unique_id}@example.com"
            unique_username = f"analyticsuser{unique_id}"
            
            user_data = {
                "email": unique_email,
                "username": unique_username,
                "password": "TestPassword123",
                "first_name": "Analytics",
                "last_name": "Debugger"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("user"):
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    self.registered_email = unique_email
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print(f"✅ Registered and logged in: {unique_email} (ID: {self.user_id})")
                    return True
                else:
                    print(f"❌ Registration failed: Missing token or user data")
                    return False
            else:
                print(f"❌ Registration failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return False
    
    def create_test_notes(self, count=6):
        """Create test notes to simulate user with notes"""
        created_notes = []
        
        for i in range(count):
            note_data = {
                "title": f"Analytics Debug Note {i+1} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "kind": "text",
                "text_content": f"This is analytics debug note number {i+1}. Created for debugging analytics data issue where user has {count} notes but analytics shows 0 stats."
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/notes",
                json=note_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                created_notes.append(result.get("id"))
                print(f"✅ Created note {i+1}: {result.get('id')}")
            else:
                print(f"❌ Failed to create note {i+1}: HTTP {response.status_code}")
        
        print(f"📝 Created {len(created_notes)} test notes")
        return created_notes
    
    def verify_notes_in_database(self):
        """Verify notes exist in database"""
        response = self.session.get(f"{BACKEND_URL}/notes", timeout=10)
        
        if response.status_code == 200:
            notes_list = response.json()
            print(f"📊 User has {len(notes_list)} total notes in database")
            
            if notes_list:
                # Show sample note structure
                sample_note = notes_list[0]
                print(f"📝 Sample Note Structure:")
                print(f"   ID: {sample_note.get('id')}")
                print(f"   User ID: {sample_note.get('user_id')}")
                print(f"   Status: {sample_note.get('status')}")
                print(f"   Kind: {sample_note.get('kind')}")
                print(f"   Created At: {sample_note.get('created_at')}")
                print(f"   Title: {sample_note.get('title')}")
                
                # Check for issues
                if sample_note.get('user_id') != self.user_id:
                    print(f"⚠️  USER ID MISMATCH: Note has '{sample_note.get('user_id')}', expected '{self.user_id}'")
                
                # Count by status
                status_counts = {}
                for note in notes_list:
                    status = note.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"📊 Notes by Status: {status_counts}")
            
            return notes_list
        else:
            print(f"❌ Failed to list notes: HTTP {response.status_code}")
            return []
    
    def test_analytics_endpoints(self):
        """Test all analytics endpoints"""
        analytics_endpoints = [
            ("/analytics/weekly-usage", "Weekly Usage"),
            ("/analytics/monthly-overview", "Monthly Overview"), 
            ("/analytics/daily-activity", "Daily Activity"),
            ("/analytics/performance-insights", "Performance Insights")
        ]
        
        analytics_results = {}
        zero_data_endpoints = []
        
        for endpoint, name in analytics_endpoints:
            print(f"\n🔍 Testing {name} endpoint: {endpoint}")
            
            response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                analytics_results[name] = data
                
                if data.get("success"):
                    endpoint_data = data.get("data", {})
                    
                    if name == "Weekly Usage":
                        total_notes = sum(week.get("notes", 0) for week in endpoint_data)
                        print(f"   ✅ Weekly Usage: {len(endpoint_data)} weeks, {total_notes} total notes")
                        if total_notes == 0:
                            zero_data_endpoints.append(name)
                            print(f"   ❌ ZERO DATA DETECTED in Weekly Usage")
                            
                    elif name == "Monthly Overview":
                        total_notes = sum(month.get("notes", 0) for month in endpoint_data)
                        print(f"   ✅ Monthly Overview: {len(endpoint_data)} months, {total_notes} total notes")
                        if total_notes == 0:
                            zero_data_endpoints.append(name)
                            print(f"   ❌ ZERO DATA DETECTED in Monthly Overview")
                            
                    elif name == "Daily Activity":
                        activity_data = endpoint_data.get("activity_data", {})
                        total_activity = sum(sum(day_data) for day_data in activity_data.values())
                        print(f"   ✅ Daily Activity: {total_activity} total activities")
                        if total_activity == 0:
                            zero_data_endpoints.append(name)
                            print(f"   ❌ ZERO DATA DETECTED in Daily Activity")
                            
                    elif name == "Performance Insights":
                        total_notes = endpoint_data.get("total_notes", 0)
                        success_rate = endpoint_data.get("success_rate", 0)
                        print(f"   ✅ Performance Insights: {total_notes} total notes, {success_rate}% success rate")
                        if total_notes == 0:
                            zero_data_endpoints.append(name)
                            print(f"   ❌ ZERO DATA DETECTED in Performance Insights")
                else:
                    print(f"   ❌ {name}: Response not successful")
                    
            elif response.status_code == 403:
                print(f"   ❌ {name}: Authentication required (HTTP 403)")
            else:
                print(f"   ❌ {name}: HTTP {response.status_code} - {response.text[:100]}")
        
        return analytics_results, zero_data_endpoints
    
    def debug_analytics_issue(self):
        """Main debugging function"""
        print("🔍 ANALYTICS DEBUGGING - Starting comprehensive investigation...")
        print("=" * 80)
        
        # Step 1: Register and login
        if not self.register_and_login():
            print("❌ Failed to register/login. Cannot continue debugging.")
            return
        
        # Step 2: Create test notes
        print(f"\n📝 Creating 6 test notes to simulate the user issue...")
        created_notes = self.create_test_notes(6)
        
        # Step 3: Verify notes in database
        print(f"\n📊 Verifying notes exist in database...")
        notes_list = self.verify_notes_in_database()
        
        # Step 4: Test analytics endpoints
        print(f"\n🔍 Testing analytics endpoints...")
        analytics_results, zero_data_endpoints = self.test_analytics_endpoints()
        
        # Step 5: Analysis and diagnosis
        print(f"\n🔍 ANALYTICS ISSUE ANALYSIS:")
        print(f"=" * 50)
        print(f"   Database Notes Count: {len(notes_list)}")
        print(f"   Created Test Notes: {len(created_notes)}")
        print(f"   User ID: {self.user_id}")
        print(f"   Zero Data Endpoints: {zero_data_endpoints}")
        
        if zero_data_endpoints:
            print(f"\n❌ ISSUE CONFIRMED: {len(zero_data_endpoints)} endpoints showing zero data")
            print(f"   Affected endpoints: {zero_data_endpoints}")
            
            print(f"\n🔍 POTENTIAL ROOT CAUSES:")
            print(f"   1. User ID mismatch between notes and analytics queries")
            print(f"   2. Date/timezone issues in analytics date range calculations")
            print(f"   3. Note status filtering excluding user's notes")
            print(f"   4. Database field name mismatches (user_id vs userId)")
            print(f"   5. Notes created outside expected date ranges")
            
            # Additional debugging
            if notes_list:
                sample_note = notes_list[0]
                print(f"\n🔍 DETAILED DEBUGGING INFO:")
                print(f"   Sample Note User ID: {sample_note.get('user_id')}")
                print(f"   Expected User ID: {self.user_id}")
                print(f"   User ID Match: {sample_note.get('user_id') == self.user_id}")
                print(f"   Sample Note Created At: {sample_note.get('created_at')}")
                print(f"   Sample Note Status: {sample_note.get('status')}")
                
                # Check if created_at is recent
                try:
                    from datetime import datetime, timezone
                    if isinstance(sample_note.get('created_at'), str):
                        created_at = datetime.fromisoformat(sample_note.get('created_at').replace('Z', '+00:00'))
                    else:
                        created_at = sample_note.get('created_at')
                    
                    now = datetime.now(timezone.utc)
                    time_diff = now - created_at
                    print(f"   Note Age: {time_diff.total_seconds()} seconds ago")
                    
                    if time_diff.total_seconds() > 3600:  # More than 1 hour
                        print(f"   ⚠️  Note is older than 1 hour - may be outside analytics date range")
                    
                except Exception as e:
                    print(f"   ❌ Error parsing created_at: {e}")
            
            return False
        else:
            print(f"\n✅ Analytics data appears to be working correctly")
            return True

if __name__ == "__main__":
    debugger = AnalyticsDebugger()
    success = debugger.debug_analytics_issue()
    
    if success:
        print(f"\n✅ ANALYTICS DEBUGGING COMPLETE: No issues found")
    else:
        print(f"\n❌ ANALYTICS DEBUGGING COMPLETE: Issues identified")