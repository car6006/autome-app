#!/usr/bin/env python3
"""
Comprehensive Analytics Endpoints Testing Suite
Tests all analytics endpoints with proper data validation
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "https://insight-api.preview.emergentagent.com/api"
TEST_USER_PASSWORD = "TestPassword123"

class ComprehensiveAnalyticsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def setup_authentication(self):
        """Set up authentication for testing"""
        try:
            # Generate unique user
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"analytics_test_{unique_id}@example.com"
            unique_username = f"analyticsuser{unique_id}"
            
            user_data = {
                "email": unique_email,
                "username": unique_username,
                "password": TEST_USER_PASSWORD,
                "first_name": "Analytics",
                "last_name": "TestUser"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("user"):
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("Authentication Setup", True, f"User authenticated: {unique_email}")
                    return True
                else:
                    self.log_result("Authentication Setup", False, "Missing token or user data", data)
                    return False
            else:
                self.log_result("Authentication Setup", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Authentication error: {str(e)}")
            return False

    def test_weekly_usage_endpoint(self):
        """Test GET /api/analytics/weekly-usage"""
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/weekly-usage", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if not data.get("success"):
                    self.log_result("Weekly Usage Endpoint", False, "Response success=false", data)
                    return
                
                if "data" not in data:
                    self.log_result("Weekly Usage Endpoint", False, "Missing 'data' field", data)
                    return
                
                weekly_data = data["data"]
                if not isinstance(weekly_data, list):
                    self.log_result("Weekly Usage Endpoint", False, "Data is not a list", data)
                    return
                
                # For new users, data might be empty or have default values
                if len(weekly_data) > 0:
                    first_week = weekly_data[0]
                    required_fields = ["week", "notes", "minutes"]
                    missing_fields = [field for field in required_fields if field not in first_week]
                    
                    if missing_fields:
                        self.log_result("Weekly Usage Endpoint", False, 
                                      f"Missing fields: {missing_fields}", first_week)
                        return
                
                self.log_result("Weekly Usage Endpoint", True, 
                              f"Weekly usage data structure valid ({len(weekly_data)} weeks)", 
                              {"sample_data": weekly_data[0] if weekly_data else "No data for new user"})
                
            elif response.status_code == 401:
                self.log_result("Weekly Usage Endpoint", False, "Authentication failed")
            else:
                self.log_result("Weekly Usage Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Weekly Usage Endpoint", False, f"Test error: {str(e)}")

    def test_monthly_overview_endpoint(self):
        """Test GET /api/analytics/monthly-overview"""
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/monthly-overview", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if not data.get("success"):
                    self.log_result("Monthly Overview Endpoint", False, "Response success=false", data)
                    return
                
                if "data" not in data:
                    self.log_result("Monthly Overview Endpoint", False, "Missing 'data' field", data)
                    return
                
                monthly_data = data["data"]
                if not isinstance(monthly_data, list):
                    self.log_result("Monthly Overview Endpoint", False, "Data is not a list", data)
                    return
                
                # For new users, data might be empty or have default values
                if len(monthly_data) > 0:
                    first_month = monthly_data[0]
                    required_fields = ["month", "notes"]
                    missing_fields = [field for field in required_fields if field not in first_month]
                    
                    if missing_fields:
                        self.log_result("Monthly Overview Endpoint", False, 
                                      f"Missing fields: {missing_fields}", first_month)
                        return
                
                self.log_result("Monthly Overview Endpoint", True, 
                              f"Monthly overview data structure valid ({len(monthly_data)} months)", 
                              {"sample_data": monthly_data[0] if monthly_data else "No data for new user"})
                
            elif response.status_code == 401:
                self.log_result("Monthly Overview Endpoint", False, "Authentication failed")
            else:
                self.log_result("Monthly Overview Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Monthly Overview Endpoint", False, f"Test error: {str(e)}")

    def test_daily_activity_endpoint(self):
        """Test GET /api/analytics/daily-activity"""
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/daily-activity", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if not data.get("success"):
                    self.log_result("Daily Activity Endpoint", False, "Response success=false", data)
                    return
                
                if "data" not in data:
                    self.log_result("Daily Activity Endpoint", False, "Missing 'data' field", data)
                    return
                
                heatmap_data = data["data"]
                required_fields = ["activity_data", "hours", "days"]
                missing_fields = [field for field in required_fields if field not in heatmap_data]
                
                if missing_fields:
                    self.log_result("Daily Activity Endpoint", False, 
                                  f"Missing fields: {missing_fields}", heatmap_data)
                    return
                
                # Validate data types
                activity_data = heatmap_data["activity_data"]
                hours = heatmap_data["hours"]
                days = heatmap_data["days"]
                
                if not isinstance(activity_data, dict):
                    self.log_result("Daily Activity Endpoint", False, "activity_data is not a dict", heatmap_data)
                    return
                
                if not isinstance(hours, list):
                    self.log_result("Daily Activity Endpoint", False, "hours is not a list", heatmap_data)
                    return
                
                if not isinstance(days, list):
                    self.log_result("Daily Activity Endpoint", False, "days is not a list", heatmap_data)
                    return
                
                self.log_result("Daily Activity Endpoint", True, 
                              "Daily activity heatmap data structure valid", 
                              {"days_count": len(days), "hours_count": len(hours), 
                               "activity_keys": list(activity_data.keys())})
                
            elif response.status_code == 401:
                self.log_result("Daily Activity Endpoint", False, "Authentication failed")
            else:
                self.log_result("Daily Activity Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Daily Activity Endpoint", False, f"Test error: {str(e)}")

    def test_performance_insights_endpoint(self):
        """Test GET /api/analytics/performance-insights"""
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/performance-insights", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug: print full response
                print(f"DEBUG: Full response: {json.dumps(data, indent=2)}")
                
                # Validate response structure
                if not data.get("success"):
                    self.log_result("Performance Insights Endpoint", False, "Response success=false", data)
                    return
                
                if "data" not in data:
                    self.log_result("Performance Insights Endpoint", False, "Missing 'data' field", data)
                    return
                
                insights_data = data["data"]
                print(f"DEBUG: insights_data type: {type(insights_data)}")
                print(f"DEBUG: insights_data: {insights_data}")
                
                required_fields = ["weekly_average", "peak_day", "streak", "success_rate", 
                                 "total_notes", "estimated_minutes_saved"]
                
                # Debug: print what we actually have
                print(f"DEBUG: insights_data keys: {list(insights_data.keys()) if isinstance(insights_data, dict) else 'Not a dict'}")
                print(f"DEBUG: required_fields: {required_fields}")
                
                if not isinstance(insights_data, dict):
                    self.log_result("Performance Insights Endpoint", False, 
                                  f"insights_data is not a dict: {type(insights_data)}", data)
                    return
                
                missing_fields = [field for field in required_fields if field not in insights_data]
                
                if missing_fields:
                    self.log_result("Performance Insights Endpoint", False, 
                                  f"Missing fields: {missing_fields}", insights_data)
                    return
                
                # Validate data types
                numeric_fields = ["weekly_average", "streak", "success_rate", "total_notes", "estimated_minutes_saved"]
                for field in numeric_fields:
                    if not isinstance(insights_data[field], (int, float)):
                        self.log_result("Performance Insights Endpoint", False, 
                                      f"Field '{field}' is not numeric: {type(insights_data[field])}", insights_data)
                        return
                
                if not isinstance(insights_data["peak_day"], str):
                    self.log_result("Performance Insights Endpoint", False, 
                                  f"peak_day is not a string: {type(insights_data['peak_day'])}", insights_data)
                    return
                
                self.log_result("Performance Insights Endpoint", True, 
                              "Performance insights data structure valid", 
                              {"weekly_average": insights_data["weekly_average"],
                               "peak_day": insights_data["peak_day"],
                               "success_rate": insights_data["success_rate"],
                               "total_notes": insights_data["total_notes"]})
                
            elif response.status_code == 401:
                self.log_result("Performance Insights Endpoint", False, "Authentication failed")
            else:
                self.log_result("Performance Insights Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Performance Insights Endpoint", False, f"Test error: {str(e)}")

    def test_authentication_protection(self):
        """Test that all analytics endpoints require authentication"""
        try:
            # Remove auth header temporarily
            original_headers = self.session.headers.copy()
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            endpoints = [
                "/analytics/weekly-usage",
                "/analytics/monthly-overview", 
                "/analytics/daily-activity",
                "/analytics/performance-insights"
            ]
            
            all_protected = True
            results = []
            
            for endpoint in endpoints:
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                if response.status_code in [401, 403]:
                    results.append(f"✅ {endpoint}: Protected (HTTP {response.status_code})")
                else:
                    results.append(f"❌ {endpoint}: Not protected (HTTP {response.status_code})")
                    all_protected = False
            
            # Restore headers
            self.session.headers.update(original_headers)
            
            if all_protected:
                self.log_result("Authentication Protection", True, 
                              "All analytics endpoints require authentication", {"results": results})
            else:
                self.log_result("Authentication Protection", False, 
                              "Some endpoints don't require authentication", {"results": results})
                
        except Exception as e:
            self.log_result("Authentication Protection", False, f"Test error: {str(e)}")

    def create_sample_data(self):
        """Create sample notes to test analytics with real data"""
        try:
            test_notes = [
                {"title": "Sample Meeting Notes", "kind": "text", "text_content": "Meeting with client about project requirements and timeline."},
                {"title": "Project Planning", "kind": "text", "text_content": "Planning phase for the new analytics dashboard implementation."},
                {"title": "Daily Standup", "kind": "text", "text_content": "Team standup notes covering progress and blockers."}
            ]
            
            created_count = 0
            for note_data in test_notes:
                response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
                if response.status_code == 200:
                    created_count += 1
                    time.sleep(0.5)  # Small delay
            
            self.log_result("Sample Data Creation", True, f"Created {created_count} sample notes")
            
        except Exception as e:
            self.log_result("Sample Data Creation", False, f"Failed to create sample data: {str(e)}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE ANALYTICS ENDPOINTS TEST SUMMARY")
        print("=" * 80)
        
        passed = [r for r in self.test_results if r["success"]]
        failed = [r for r in self.test_results if not r["success"]]
        
        print(f"✅ PASSED: {len(passed)}")
        print(f"❌ FAILED: {len(failed)}")
        print(f"📈 SUCCESS RATE: {len(passed)}/{len(self.test_results)} ({len(passed)/len(self.test_results)*100:.1f}%)")
        
        if failed:
            print("\n❌ FAILED TESTS:")
            for test in failed:
                print(f"   • {test['test']}: {test['message']}")
        
        print("\n✅ PASSED TESTS:")
        for test in passed:
            print(f"   • {test['test']}: {test['message']}")
        
        print("\n" + "=" * 80)

    def run_comprehensive_tests(self):
        """Run all comprehensive analytics tests"""
        print("📊 Starting Comprehensive Analytics Endpoints Testing")
        print(f"🎯 Target: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Create sample data
        self.create_sample_data()
        time.sleep(2)  # Allow data to be processed
        
        # Run tests
        print("\n📊 Testing Analytics Endpoints...")
        self.test_weekly_usage_endpoint()
        self.test_monthly_overview_endpoint()
        self.test_daily_activity_endpoint()
        self.test_performance_insights_endpoint()
        self.test_authentication_protection()
        
        # Summary
        self.print_summary()

if __name__ == "__main__":
    tester = ComprehensiveAnalyticsTester()
    tester.run_comprehensive_tests()