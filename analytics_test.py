#!/usr/bin/env python3
"""
Analytics Endpoints Testing Suite
Tests the new analytics endpoints for the AUTO-ME Productivity API
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://insight-api.preview.emergentagent.com/api"
TEST_USER_EMAIL = "analytics_testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123"
TEST_USER_NAME = "Analytics Test User"
TEST_USERNAME = "analyticsuser123"

class AnalyticsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        
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
            print(f"   Details: {details}")
    
    def setup_authentication(self):
        """Set up authentication for testing"""
        try:
            # Generate unique email and username for this test
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"analytics_testuser_{unique_id}@example.com"
            unique_username = f"analyticsuser{unique_id}"
            
            user_data = {
                "email": unique_email,
                "username": unique_username,
                "password": TEST_USER_PASSWORD,
                "first_name": "Analytics",
                "last_name": "TestUser"
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
                    self.log_result("Authentication Setup", True, "User registered and authenticated successfully", {
                        "user_id": self.user_id,
                        "email": unique_email,
                        "username": unique_username
                    })
                    return True
                else:
                    self.log_result("Authentication Setup", False, "Missing token or user data", data)
                    return False
            else:
                self.log_result("Authentication Setup", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Authentication setup error: {str(e)}")
            return False

    def test_analytics_weekly_usage(self):
        """Test weekly usage analytics endpoint"""
        if not self.auth_token:
            self.log_result("Analytics Weekly Usage", False, "Skipped - no authentication token")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/weekly-usage", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    weekly_data = data["data"]
                    if isinstance(weekly_data, list):
                        if len(weekly_data) > 0:
                            # Check data structure
                            first_week = weekly_data[0]
                            required_fields = ["week", "notes", "minutes"]
                            has_required_fields = all(field in first_week for field in required_fields)
                            
                            if has_required_fields:
                                self.log_result("Analytics Weekly Usage", True, 
                                              f"Weekly analytics data retrieved successfully: {len(weekly_data)} weeks", 
                                              {"weeks_count": len(weekly_data), "sample_data": first_week})
                            else:
                                self.log_result("Analytics Weekly Usage", False, 
                                              f"Missing required fields in weekly data: {first_week}")
                        else:
                            self.log_result("Analytics Weekly Usage", True, 
                                          "Weekly analytics endpoint working (no data yet for new user)")
                    else:
                        self.log_result("Analytics Weekly Usage", False, "Weekly data is not a list", data)
                else:
                    self.log_result("Analytics Weekly Usage", False, "Invalid response structure", data)
            elif response.status_code == 401:
                self.log_result("Analytics Weekly Usage", False, "Authentication failed - check token")
            else:
                self.log_result("Analytics Weekly Usage", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Analytics Weekly Usage", False, f"Weekly analytics test error: {str(e)}")

    def test_analytics_monthly_overview(self):
        """Test monthly overview analytics endpoint"""
        if not self.auth_token:
            self.log_result("Analytics Monthly Overview", False, "Skipped - no authentication token")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/monthly-overview", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    monthly_data = data["data"]
                    if isinstance(monthly_data, list):
                        if len(monthly_data) > 0:
                            # Check data structure
                            first_month = monthly_data[0]
                            required_fields = ["month", "notes"]
                            has_required_fields = all(field in first_month for field in required_fields)
                            
                            if has_required_fields:
                                self.log_result("Analytics Monthly Overview", True, 
                                              f"Monthly analytics data retrieved successfully: {len(monthly_data)} months", 
                                              {"months_count": len(monthly_data), "sample_data": first_month})
                            else:
                                self.log_result("Analytics Monthly Overview", False, 
                                              f"Missing required fields in monthly data: {first_month}")
                        else:
                            self.log_result("Analytics Monthly Overview", True, 
                                          "Monthly analytics endpoint working (no data yet for new user)")
                    else:
                        self.log_result("Analytics Monthly Overview", False, "Monthly data is not a list", data)
                else:
                    self.log_result("Analytics Monthly Overview", False, "Invalid response structure", data)
            elif response.status_code == 401:
                self.log_result("Analytics Monthly Overview", False, "Authentication failed - check token")
            else:
                self.log_result("Analytics Monthly Overview", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Analytics Monthly Overview", False, f"Monthly analytics test error: {str(e)}")

    def test_analytics_daily_activity(self):
        """Test daily activity heatmap analytics endpoint"""
        if not self.auth_token:
            self.log_result("Analytics Daily Activity", False, "Skipped - no authentication token")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/daily-activity", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    heatmap_data = data["data"]
                    required_fields = ["activity_data", "hours", "days"]
                    has_required_fields = all(field in heatmap_data for field in required_fields)
                    
                    if has_required_fields:
                        activity_data = heatmap_data["activity_data"]
                        hours = heatmap_data["hours"]
                        days = heatmap_data["days"]
                        
                        # Validate structure
                        if isinstance(activity_data, dict) and isinstance(hours, list) and isinstance(days, list):
                            self.log_result("Analytics Daily Activity", True, 
                                          f"Daily activity heatmap data retrieved successfully", 
                                          {"days_count": len(days), "hours_count": len(hours), 
                                           "has_activity_data": len(activity_data) > 0})
                        else:
                            self.log_result("Analytics Daily Activity", False, 
                                          "Invalid heatmap data structure", heatmap_data)
                    else:
                        self.log_result("Analytics Daily Activity", False, 
                                      f"Missing required fields in heatmap data: {list(heatmap_data.keys())}")
                else:
                    self.log_result("Analytics Daily Activity", False, "Invalid response structure", data)
            elif response.status_code == 401:
                self.log_result("Analytics Daily Activity", False, "Authentication failed - check token")
            else:
                self.log_result("Analytics Daily Activity", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Analytics Daily Activity", False, f"Daily activity analytics test error: {str(e)}")

    def test_analytics_performance_insights(self):
        """Test performance insights analytics endpoint"""
        if not self.auth_token:
            self.log_result("Analytics Performance Insights", False, "Skipped - no authentication token")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/analytics/performance-insights", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    insights_data = data["data"]
                    required_fields = ["weekly_average", "peak_day", "streak", "success_rate", 
                                     "total_notes", "estimated_minutes_saved"]
                    has_required_fields = all(field in insights_data for field in required_fields)
                    
                    if has_required_fields:
                        self.log_result("Analytics Performance Insights", True, 
                                      f"Performance insights retrieved successfully", 
                                      {"weekly_average": insights_data.get("weekly_average"),
                                       "peak_day": insights_data.get("peak_day"),
                                       "success_rate": insights_data.get("success_rate"),
                                       "total_notes": insights_data.get("total_notes")})
                    else:
                        missing_fields = [field for field in required_fields if field not in insights_data]
                        self.log_result("Analytics Performance Insights", False, 
                                      f"Missing required fields: {missing_fields}", insights_data)
                else:
                    self.log_result("Analytics Performance Insights", False, "Invalid response structure", data)
            elif response.status_code == 401:
                self.log_result("Analytics Performance Insights", False, "Authentication failed - check token")
            else:
                self.log_result("Analytics Performance Insights", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Analytics Performance Insights", False, f"Performance insights test error: {str(e)}")

    def test_analytics_authentication_required(self):
        """Test that analytics endpoints require authentication"""
        try:
            # Temporarily remove auth header
            original_headers = self.session.headers.copy()
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            endpoints_to_test = [
                "/analytics/weekly-usage",
                "/analytics/monthly-overview", 
                "/analytics/daily-activity",
                "/analytics/performance-insights"
            ]
            
            all_protected = True
            results = []
            
            for endpoint in endpoints_to_test:
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                if response.status_code in [401, 403]:
                    results.append(f"✅ {endpoint}: Protected")
                else:
                    results.append(f"❌ {endpoint}: Not protected (HTTP {response.status_code})")
                    all_protected = False
            
            # Restore headers
            self.session.headers.update(original_headers)
            
            if all_protected:
                self.log_result("Analytics Authentication Required", True, 
                              "All analytics endpoints correctly require authentication", 
                              {"results": results})
            else:
                self.log_result("Analytics Authentication Required", False, 
                              "Some analytics endpoints don't require authentication", 
                              {"results": results})
                
        except Exception as e:
            self.log_result("Analytics Authentication Required", False, f"Analytics auth test error: {str(e)}")

    def create_test_data(self):
        """Create some test notes to generate analytics data"""
        if not self.auth_token:
            return
            
        try:
            # Create a few test notes to generate some analytics data
            test_notes = [
                {"title": "Analytics Test Note 1", "kind": "text", "text_content": "This is test content for analytics"},
                {"title": "Analytics Test Note 2", "kind": "text", "text_content": "Another test note for analytics data"},
                {"title": "Analytics Test Note 3", "kind": "text", "text_content": "Third test note for comprehensive analytics"}
            ]
            
            created_notes = 0
            for note_data in test_notes:
                response = self.session.post(
                    f"{BACKEND_URL}/notes",
                    json=note_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    created_notes += 1
                    time.sleep(0.5)  # Small delay between creations
            
            self.log_result("Test Data Creation", True, f"Created {created_notes} test notes for analytics data")
            
        except Exception as e:
            self.log_result("Test Data Creation", False, f"Failed to create test data: {str(e)}")

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 ANALYTICS ENDPOINTS TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = [r for r in self.test_results if r["success"]]
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        print(f"📈 SUCCESS RATE: {len(passed_tests)}/{len(self.test_results)} ({len(passed_tests)/len(self.test_results)*100:.1f}%)")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        if passed_tests:
            print("\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        print("\n" + "=" * 80)

    def run_analytics_tests(self):
        """Run all analytics endpoint tests"""
        print("📊 Starting Analytics Endpoints Testing Suite")
        print(f"🎯 Target URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Failed to set up authentication. Cannot proceed with analytics tests.")
            return
        
        # Create some test data for more meaningful analytics
        self.create_test_data()
        
        # Wait a moment for data to be processed
        time.sleep(2)
        
        # Run analytics tests
        print("\n📊 Testing Analytics Endpoints...")
        self.test_analytics_weekly_usage()
        self.test_analytics_monthly_overview()
        self.test_analytics_daily_activity()
        self.test_analytics_performance_insights()
        self.test_analytics_authentication_required()
        
        # Print summary
        self.print_test_summary()

if __name__ == "__main__":
    tester = AnalyticsTester()
    tester.run_analytics_tests()