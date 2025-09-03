#!/usr/bin/env python3
"""
DEBUG TEST: /api/auth/verify-user Endpoint
Specific testing and debugging for the verify-user endpoint returning 404 errors
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class VerifyUserDebugTester:
    def __init__(self, base_url="https://autome-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_users = []
        
    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_1_api_endpoint_availability(self):
        """Test 1: Verify /api/auth/verify-user endpoint is properly registered and accessible"""
        self.log("\n🔍 TEST 1: API ENDPOINT AVAILABILITY")
        
        # First, test if the endpoint exists by sending a request without email (should get 400, not 404)
        success, response = self.run_test(
            "Verify-User Endpoint Exists (No Email)",
            "POST",
            "auth/verify-user",
            400,  # Should get 400 for missing email, not 404 for missing endpoint
            data={}
        )
        
        if not success:
            self.log("❌ CRITICAL: /api/auth/verify-user endpoint appears to be missing or not registered!")
            return False
        
        self.log("✅ Endpoint exists and is accessible")
        
        # Test with invalid data format
        success2, response2 = self.run_test(
            "Verify-User Endpoint with Invalid Data",
            "POST", 
            "auth/verify-user",
            400,  # Should get 400 for invalid data
            data={"invalid": "data"}
        )
        
        return success and success2

    def test_2_create_test_users(self):
        """Test 2: Create test users for verification testing"""
        self.log("\n🔍 TEST 2: CREATE TEST USERS FOR VERIFICATION")
        
        # Create multiple test users
        test_user_data = [
            {
                "email": f"verify_test_user1_{int(time.time())}@example.com",
                "username": f"verifyuser1{int(time.time())}",
                "password": "TestPassword123!",
                "first_name": "Verify",
                "last_name": "User1"
            },
            {
                "email": f"verify_test_user2_{int(time.time())}@example.com", 
                "username": f"verifyuser2{int(time.time())}",
                "password": "TestPassword123!",
                "first_name": "Verify",
                "last_name": "User2"
            },
            {
                "email": f"verify_expeditors_{int(time.time())}@expeditors.com",
                "username": f"verifyexp{int(time.time())}",
                "password": "TestPassword123!",
                "first_name": "Verify",
                "last_name": "Expeditors"
            }
        ]
        
        created_users = 0
        for i, user_data in enumerate(test_user_data):
            success, response = self.run_test(
                f"Create Test User {i+1}",
                "POST",
                "auth/register",
                200,
                data=user_data
            )
            
            if success:
                created_users += 1
                self.test_users.append(user_data["email"])
                self.log(f"   Created user: {user_data['email']}")
                
                # Store first user's token for authenticated tests
                if i == 0:
                    self.auth_token = response.get('access_token')
                    self.log(f"   Stored auth token for testing")
            else:
                self.log(f"   Failed to create user: {user_data['email']}")
        
        self.log(f"✅ Created {created_users} test users for verification testing")
        return created_users > 0

    def test_3_user_verification_logic_valid_emails(self):
        """Test 3: Test user verification logic with valid existing emails"""
        self.log("\n🔍 TEST 3: USER VERIFICATION LOGIC - VALID EMAILS")
        
        successful_verifications = 0
        
        for email in self.test_users:
            success, response = self.run_test(
                f"Verify Existing User: {email}",
                "POST",
                "auth/verify-user",
                200,  # Should return 200 for existing users
                data={"email": email}
            )
            
            if success:
                successful_verifications += 1
                self.log(f"   ✅ User exists: {response.get('exists', False)}")
                self.log(f"   Message: {response.get('message', 'N/A')}")
            else:
                self.log(f"   ❌ Failed to verify existing user: {email}")
        
        return successful_verifications > 0

    def test_4_user_verification_logic_invalid_emails(self):
        """Test 4: Test user verification logic with invalid/non-existing emails"""
        self.log("\n🔍 TEST 4: USER VERIFICATION LOGIC - INVALID EMAILS")
        
        invalid_emails = [
            f"nonexistent_{int(time.time())}@example.com",
            f"fake_user_{int(time.time())}@test.com",
            "invalid.email@nowhere.invalid"
        ]
        
        successful_rejections = 0
        
        for email in invalid_emails:
            success, response = self.run_test(
                f"Verify Non-existing User: {email}",
                "POST",
                "auth/verify-user",
                404,  # Should return 404 for non-existing users
                data={"email": email}
            )
            
            if success:
                successful_rejections += 1
                self.log(f"   ✅ Correctly returned 404 for non-existing user")
                self.log(f"   Error: {response.get('detail', 'N/A')}")
            else:
                self.log(f"   ❌ Unexpected response for non-existing user: {email}")
        
        return successful_rejections > 0

    def test_5_database_connectivity_debug(self):
        """Test 5: Debug database connectivity and user collection"""
        self.log("\n🔍 TEST 5: DATABASE CONNECTIVITY DEBUG")
        
        # Test if we can access user data through other endpoints
        if not self.auth_token:
            self.log("❌ No auth token available for database connectivity test")
            return False
        
        # Test getting current user profile (this uses the same database)
        success, response = self.run_test(
            "Get Current User Profile (DB Test)",
            "GET",
            "auth/me",
            200,
            auth_required=True
        )
        
        if success:
            self.log("✅ Database connectivity working - can retrieve user profiles")
            self.log(f"   User email: {response.get('email', 'N/A')}")
            self.log(f"   User ID: {response.get('id', 'N/A')}")
            return True
        else:
            self.log("❌ Database connectivity issue - cannot retrieve user profiles")
            return False

    def test_6_complete_authentication_flow(self):
        """Test 6: Test complete authentication flow to verify system integrity"""
        self.log("\n🔍 TEST 6: COMPLETE AUTHENTICATION FLOW")
        
        if not self.test_users:
            self.log("❌ No test users available for authentication flow test")
            return False
        
        test_email = self.test_users[0]
        
        # Test login with existing user
        login_data = {
            "email": test_email,
            "password": "TestPassword123!"
        }
        
        success, response = self.run_test(
            "Login with Test User",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            self.log("✅ Authentication flow working correctly")
            self.log(f"   Login successful for: {response.get('user', {}).get('email', 'N/A')}")
            return True
        else:
            self.log("❌ Authentication flow broken")
            return False

    def test_7_verify_user_endpoint_detailed_debug(self):
        """Test 7: Detailed debugging of verify-user endpoint behavior"""
        self.log("\n🔍 TEST 7: DETAILED VERIFY-USER ENDPOINT DEBUG")
        
        if not self.test_users:
            self.log("❌ No test users available for detailed debugging")
            return False
        
        test_email = self.test_users[0]
        
        # Test with different request formats
        test_cases = [
            {
                "name": "Standard Request Format",
                "data": {"email": test_email},
                "expected": 200
            },
            {
                "name": "Email with Extra Whitespace",
                "data": {"email": f" {test_email} "},
                "expected": 200
            },
            {
                "name": "Uppercase Email",
                "data": {"email": test_email.upper()},
                "expected": 200  # Should still work as emails are case-insensitive
            },
            {
                "name": "Empty Email String",
                "data": {"email": ""},
                "expected": 400
            },
            {
                "name": "Null Email",
                "data": {"email": None},
                "expected": 400
            },
            {
                "name": "Missing Email Field",
                "data": {},
                "expected": 400
            }
        ]
        
        successful_tests = 0
        
        for test_case in test_cases:
            success, response = self.run_test(
                f"Verify-User: {test_case['name']}",
                "POST",
                "auth/verify-user",
                test_case["expected"],
                data=test_case["data"]
            )
            
            if success:
                successful_tests += 1
                self.log(f"   ✅ {test_case['name']} behaved as expected")
            else:
                self.log(f"   ❌ {test_case['name']} did not behave as expected")
        
        return successful_tests > 0

    def test_8_network_and_routing_debug(self):
        """Test 8: Debug network routing and endpoint registration"""
        self.log("\n🔍 TEST 8: NETWORK AND ROUTING DEBUG")
        
        # Test different HTTP methods on the endpoint
        methods_to_test = [
            ("GET", 405),    # Should return Method Not Allowed
            ("PUT", 405),    # Should return Method Not Allowed  
            ("DELETE", 405), # Should return Method Not Allowed
        ]
        
        successful_routing_tests = 0
        
        for method, expected_status in methods_to_test:
            try:
                url = f"{self.api_url}/auth/verify-user"
                headers = {'Content-Type': 'application/json'}
                
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                elif method == "PUT":
                    response = requests.put(url, json={"email": "test@example.com"}, headers=headers, timeout=10)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=10)
                
                if response.status_code == expected_status:
                    successful_routing_tests += 1
                    self.log(f"   ✅ {method} method correctly returns {response.status_code}")
                elif response.status_code == 404:
                    self.log(f"   ❌ {method} method returns 404 - endpoint routing issue!")
                else:
                    self.log(f"   ⚠️  {method} method returns {response.status_code} (expected {expected_status})")
                    
            except Exception as e:
                self.log(f"   ❌ {method} method test failed: {str(e)}")
        
        # Test if the endpoint is accessible via different URL variations
        url_variations = [
            "auth/verify-user",
            "auth/verify-user/",
            "/auth/verify-user",
            "/auth/verify-user/"
        ]
        
        for url_variation in url_variations:
            try:
                full_url = f"{self.api_url}/{url_variation}".replace("//", "/")
                response = requests.post(
                    full_url, 
                    json={"email": "test@example.com"}, 
                    headers={'Content-Type': 'application/json'}, 
                    timeout=10
                )
                
                if response.status_code != 404:
                    self.log(f"   ✅ URL variation '{url_variation}' accessible (status: {response.status_code})")
                else:
                    self.log(f"   ❌ URL variation '{url_variation}' returns 404")
                    
            except Exception as e:
                self.log(f"   ❌ URL variation '{url_variation}' test failed: {str(e)}")
        
        return successful_routing_tests > 0

    def test_9_server_logs_and_error_analysis(self):
        """Test 9: Analyze server behavior and error patterns"""
        self.log("\n🔍 TEST 9: SERVER BEHAVIOR AND ERROR ANALYSIS")
        
        # Test rapid requests to see if there are any rate limiting or server issues
        rapid_test_results = []
        
        for i in range(5):
            start_time = time.time()
            success, response = self.run_test(
                f"Rapid Request {i+1}",
                "POST",
                "auth/verify-user",
                400,  # Expect 400 for empty request
                data={}
            )
            end_time = time.time()
            
            rapid_test_results.append({
                "success": success,
                "response_time": end_time - start_time,
                "status_code": response.get("status_code", "unknown")
            })
        
        # Analyze results
        successful_rapid = sum(1 for r in rapid_test_results if r["success"])
        avg_response_time = sum(r["response_time"] for r in rapid_test_results) / len(rapid_test_results)
        
        self.log(f"   Rapid requests: {successful_rapid}/5 successful")
        self.log(f"   Average response time: {avg_response_time:.3f}s")
        
        if successful_rapid >= 4:
            self.log("   ✅ Server responding consistently")
        else:
            self.log("   ❌ Server showing inconsistent behavior")
        
        return successful_rapid >= 4

    def test_10_fix_verification_and_final_test(self):
        """Test 10: Final comprehensive test after identifying issues"""
        self.log("\n🔍 TEST 10: COMPREHENSIVE FINAL VERIFICATION")
        
        if not self.test_users:
            self.log("❌ No test users available for final verification")
            return False
        
        # Test the complete verify-user workflow
        test_scenarios = [
            {
                "email": self.test_users[0],
                "expected_status": 200,
                "expected_exists": True,
                "description": "Existing User Verification"
            },
            {
                "email": f"definitely_nonexistent_{int(time.time())}@nowhere.invalid",
                "expected_status": 404,
                "expected_exists": False,
                "description": "Non-existing User Verification"
            }
        ]
        
        successful_scenarios = 0
        
        for scenario in test_scenarios:
            success, response = self.run_test(
                scenario["description"],
                "POST",
                "auth/verify-user",
                scenario["expected_status"],
                data={"email": scenario["email"]}
            )
            
            if success:
                if scenario["expected_status"] == 200:
                    exists = response.get("exists", False)
                    if exists == scenario["expected_exists"]:
                        successful_scenarios += 1
                        self.log(f"   ✅ {scenario['description']} - Correct response")
                    else:
                        self.log(f"   ❌ {scenario['description']} - Wrong exists value: {exists}")
                else:
                    successful_scenarios += 1
                    self.log(f"   ✅ {scenario['description']} - Correct 404 response")
            else:
                self.log(f"   ❌ {scenario['description']} - Unexpected response")
        
        return successful_scenarios == len(test_scenarios)

    def run_all_tests(self):
        """Run all debugging tests"""
        self.log("🚀 STARTING /api/auth/verify-user ENDPOINT DEBUG TESTS")
        self.log("="*80)
        
        test_results = []
        
        # Run all tests in sequence
        test_methods = [
            self.test_1_api_endpoint_availability,
            self.test_2_create_test_users,
            self.test_3_user_verification_logic_valid_emails,
            self.test_4_user_verification_logic_invalid_emails,
            self.test_5_database_connectivity_debug,
            self.test_6_complete_authentication_flow,
            self.test_7_verify_user_endpoint_detailed_debug,
            self.test_8_network_and_routing_debug,
            self.test_9_server_logs_and_error_analysis,
            self.test_10_fix_verification_and_final_test
        ]
        
        for test_method in test_methods:
            try:
                result = test_method()
                test_results.append(result)
            except Exception as e:
                self.log(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
                test_results.append(False)
        
        # Summary
        self.log("\n" + "="*80)
        self.log("🏁 DEBUG TEST SUMMARY")
        self.log("="*80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        self.log(f"📊 Overall Results: {self.tests_passed}/{self.tests_run} individual tests passed")
        self.log(f"📊 Test Categories: {passed_tests}/{total_tests} categories passed")
        self.log(f"📊 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL DEBUG TESTS PASSED - /api/auth/verify-user endpoint is working correctly!")
        elif passed_tests >= total_tests * 0.8:
            self.log("⚠️  MOST TESTS PASSED - Minor issues detected, see details above")
        else:
            self.log("❌ SIGNIFICANT ISSUES DETECTED - /api/auth/verify-user endpoint needs attention")
        
        # Specific recommendations
        self.log("\n🔧 RECOMMENDATIONS:")
        
        if not test_results[0]:  # Endpoint availability
            self.log("   🚨 CRITICAL: Verify endpoint is properly registered in FastAPI router")
            self.log("   🚨 Check server.py for correct route definition")
        
        if not test_results[4]:  # Database connectivity
            self.log("   🚨 CRITICAL: Database connectivity issues detected")
            self.log("   🚨 Check MongoDB connection and user collection")
        
        if not test_results[2] or not test_results[3]:  # User verification logic
            self.log("   ⚠️  User verification logic needs review")
            self.log("   ⚠️  Check AuthService.get_user_by_email() implementation")
        
        if test_results[0] and test_results[4] and (not test_results[2] or not test_results[3]):
            self.log("   💡 Endpoint exists and DB works, but verification logic has issues")
            self.log("   💡 Focus on the verify-user endpoint implementation in server.py")
        
        return passed_tests >= total_tests * 0.8

if __name__ == "__main__":
    tester = VerifyUserDebugTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)