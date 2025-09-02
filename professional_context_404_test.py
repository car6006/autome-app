#!/usr/bin/env python3
"""
URGENT: Professional Context API 404 Error Investigation
Focused testing for the professional context endpoints to diagnose the 404 error
"""

import requests
import sys
import json
import time
from datetime import datetime

class ProfessionalContextTester:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"context_test_{int(time.time())}@example.com",
            "username": f"contextuser{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Context",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_required=False):
        """Run a single API test with detailed logging"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        self.log(f"   URL: {url}")
        self.log(f"   Method: {method}")
        self.log(f"   Headers: {headers}")
        if data:
            self.log(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            self.log(f"   Response Status: {response.status_code}")
            self.log(f"   Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                self.log(f"   Response Body: {json.dumps(response_json, indent=2)}")
            except:
                self.log(f"   Response Text: {response.text[:500]}")

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
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_api_health(self):
        """Test basic API connectivity"""
        self.log("\n🏥 TESTING API HEALTH")
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        if success:
            self.log(f"   API Message: {response.get('message', 'N/A')}")
        return success

    def test_user_registration_and_login(self):
        """Register and login a test user for authentication"""
        self.log("\n🔐 SETTING UP AUTHENTICATION")
        
        # Register user
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
            self.log(f"   Token (first 20 chars): {self.auth_token[:20] if self.auth_token else 'None'}...")
            return True
        else:
            self.log("❌ Registration failed - cannot proceed with authenticated tests")
            return False

    def test_endpoint_existence(self):
        """Test if the professional context endpoints exist in the API"""
        self.log("\n🔍 TESTING ENDPOINT EXISTENCE")
        
        # Test POST endpoint without auth (should get 403, not 404)
        success, response = self.run_test(
            "POST /api/user/professional-context (No Auth - Should get 403, not 404)",
            "POST",
            "user/professional-context",
            403,  # Should be 403 Forbidden, not 404 Not Found
            data={"primary_industry": "Test"}
        )
        
        if not success:
            # If we get 404, the endpoint doesn't exist
            self.log("⚠️  Got 404 instead of 403 - endpoint may not be registered!")
        
        # Test GET endpoint without auth (should get 403, not 404)
        success2, response2 = self.run_test(
            "GET /api/user/professional-context (No Auth - Should get 403, not 404)",
            "GET",
            "user/professional-context",
            403  # Should be 403 Forbidden, not 404 Not Found
        )
        
        if not success2:
            self.log("⚠️  Got 404 instead of 403 - endpoint may not be registered!")
        
        return success and success2

    def test_professional_context_with_auth(self):
        """Test professional context endpoints with proper authentication"""
        self.log("\n🎯 TESTING PROFESSIONAL CONTEXT WITH AUTHENTICATION")
        
        if not self.auth_token:
            self.log("❌ No auth token available - skipping authenticated tests")
            return False
        
        # Test POST endpoint with auth
        professional_context = {
            "primary_industry": "Logistics & Supply Chain",
            "job_role": "Logistics Manager",
            "work_environment": "Global freight forwarding company",
            "key_focus_areas": ["Cost optimization", "Supply chain risks", "Operational efficiency"],
            "content_types": ["Meeting minutes", "CRM notes", "Project updates"],
            "analysis_preferences": ["Strategic recommendations", "Risk assessment", "Action items"]
        }
        
        success, response = self.run_test(
            "POST /api/user/professional-context (With Auth)",
            "POST",
            "user/professional-context",
            200,
            data=professional_context,
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Professional context saved successfully")
            context = response.get('context', {})
            self.log(f"   Industry: {context.get('primary_industry', 'N/A')}")
            self.log(f"   Role: {context.get('job_role', 'N/A')}")
        else:
            self.log(f"   ❌ Failed to save professional context")
            return False
        
        # Test GET endpoint with auth
        success2, response2 = self.run_test(
            "GET /api/user/professional-context (With Auth)",
            "GET",
            "user/professional-context",
            200,
            auth_required=True
        )
        
        if success2:
            self.log(f"   ✅ Professional context retrieved successfully")
            self.log(f"   Industry: {response2.get('primary_industry', 'N/A')}")
            self.log(f"   Role: {response2.get('job_role', 'N/A')}")
            self.log(f"   Focus areas: {response2.get('key_focus_areas', [])}")
        else:
            self.log(f"   ❌ Failed to retrieve professional context")
        
        return success and success2

    def test_route_variations(self):
        """Test different variations of the route to identify routing issues"""
        self.log("\n🛣️  TESTING ROUTE VARIATIONS")
        
        route_variations = [
            "user/professional-context",
            "user/professional-context/",
            "/user/professional-context",
            "/user/professional-context/",
            "users/professional-context",
            "user/professional_context",  # Without hyphen
            "user/professional-contexts",  # Plural
        ]
        
        for route in route_variations:
            self.log(f"\n   Testing route: {route}")
            success, response = self.run_test(
                f"GET {route}",
                "GET",
                route,
                200,  # We expect 200 for the correct route, others will fail
                auth_required=True
            )
            
            if success:
                self.log(f"   ✅ Route {route} works!")
            else:
                self.log(f"   ❌ Route {route} failed")

    def test_server_logs_check(self):
        """Check if we can get any server-side information"""
        self.log("\n📋 CHECKING SERVER RESPONSE DETAILS")
        
        # Make a request and analyze the response headers for clues
        try:
            url = f"{self.api_url}/user/professional-context"
            headers = {'Content-Type': 'application/json'}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.log(f"   Response Status: {response.status_code}")
            self.log(f"   Server Header: {response.headers.get('server', 'Not provided')}")
            self.log(f"   Content-Type: {response.headers.get('content-type', 'Not provided')}")
            self.log(f"   Content-Length: {response.headers.get('content-length', 'Not provided')}")
            
            # Check if it's a FastAPI error response
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    self.log(f"   Error Detail: {error_data.get('detail', 'No detail provided')}")
                    
                    # Check if it's a FastAPI 404 vs nginx/proxy 404
                    if 'detail' in error_data:
                        self.log("   ✅ This is a FastAPI 404 (endpoint exists but route not found)")
                    else:
                        self.log("   ⚠️  This might be a proxy/nginx 404 (endpoint doesn't exist)")
                except:
                    self.log("   ⚠️  404 response is not JSON - might be proxy/nginx error")
                    self.log(f"   Raw response: {response.text[:200]}")
            
        except Exception as e:
            self.log(f"   Error during server check: {str(e)}")

    def test_api_documentation_check(self):
        """Check if the endpoint appears in API documentation"""
        self.log("\n📚 CHECKING API DOCUMENTATION")
        
        # Try to access FastAPI docs
        docs_endpoints = [
            "docs",
            "redoc", 
            "openapi.json"
        ]
        
        for endpoint in docs_endpoints:
            try:
                url = f"{self.api_url}/../{endpoint}"  # Go up one level from /api
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.log(f"   ✅ {endpoint} accessible at {url}")
                    
                    if endpoint == "openapi.json":
                        try:
                            openapi_data = response.json()
                            paths = openapi_data.get('paths', {})
                            
                            # Look for professional context endpoints
                            context_endpoints = [path for path in paths.keys() if 'professional-context' in path]
                            
                            if context_endpoints:
                                self.log(f"   ✅ Found professional context endpoints in OpenAPI: {context_endpoints}")
                            else:
                                self.log(f"   ❌ No professional context endpoints found in OpenAPI spec")
                                self.log(f"   Available endpoints: {list(paths.keys())[:10]}...")  # Show first 10
                        except:
                            self.log(f"   ⚠️  Could not parse OpenAPI JSON")
                else:
                    self.log(f"   ❌ {endpoint} not accessible (status: {response.status_code})")
                    
            except Exception as e:
                self.log(f"   ❌ Error accessing {endpoint}: {str(e)}")

    def test_authentication_validation(self):
        """Test if authentication is working properly"""
        self.log("\n🔑 TESTING AUTHENTICATION VALIDATION")
        
        # Test with invalid token
        invalid_token = "invalid_token_12345"
        
        try:
            url = f"{self.api_url}/user/professional-context"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {invalid_token}'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.log(f"   Invalid token response: {response.status_code}")
            
            if response.status_code == 401:
                self.log("   ✅ Invalid token correctly rejected with 401")
            elif response.status_code == 403:
                self.log("   ✅ Invalid token correctly rejected with 403")
            elif response.status_code == 404:
                self.log("   ❌ Got 404 with invalid token - endpoint might not exist")
            else:
                self.log(f"   ⚠️  Unexpected status code: {response.status_code}")
                
        except Exception as e:
            self.log(f"   Error testing invalid token: {str(e)}")
        
        # Test with malformed token
        try:
            url = f"{self.api_url}/user/professional-context"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer'  # Malformed
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            self.log(f"   Malformed token response: {response.status_code}")
            
        except Exception as e:
            self.log(f"   Error testing malformed token: {str(e)}")

    def run_investigation(self):
        """Run the complete 404 error investigation"""
        self.log("🚨 STARTING PROFESSIONAL CONTEXT API 404 ERROR INVESTIGATION")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        self.log(f"   Target Endpoints:")
        self.log(f"     - POST /api/user/professional-context")
        self.log(f"     - GET /api/user/professional-context")
        
        # Step 1: Test basic API connectivity
        if not self.test_api_health():
            self.log("❌ API is not accessible - stopping investigation")
            return False
        
        # Step 2: Test endpoint existence (without auth)
        self.test_endpoint_existence()
        
        # Step 3: Set up authentication
        auth_success = self.test_user_registration_and_login()
        
        # Step 4: Test with proper authentication
        if auth_success:
            self.test_professional_context_with_auth()
        
        # Step 5: Test route variations
        if auth_success:
            self.test_route_variations()
        
        # Step 6: Check server response details
        self.test_server_logs_check()
        
        # Step 7: Check API documentation
        self.test_api_documentation_check()
        
        # Step 8: Test authentication validation
        if auth_success:
            self.test_authentication_validation()
        
        return True

    def print_investigation_summary(self):
        """Print investigation summary with diagnosis"""
        self.log("\n" + "="*60)
        self.log("🔍 PROFESSIONAL CONTEXT API 404 ERROR INVESTIGATION SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        self.log("\n📋 DIAGNOSIS:")
        
        if self.tests_passed == 0:
            self.log("❌ CRITICAL: No tests passed - API may be completely inaccessible")
        elif self.tests_passed < self.tests_run * 0.5:
            self.log("⚠️  MAJOR ISSUES: Less than 50% of tests passed")
            self.log("   Possible causes:")
            self.log("   - Professional context endpoints not registered in FastAPI router")
            self.log("   - Incorrect route path in server.py")
            self.log("   - Authentication middleware blocking requests")
            self.log("   - Server configuration issues")
        else:
            self.log("✅ MINOR ISSUES: Most tests passed - specific endpoint problems")
        
        self.log("\n🔧 RECOMMENDED ACTIONS:")
        self.log("1. Check if endpoints are properly registered in server.py")
        self.log("2. Verify route paths match exactly: /api/user/professional-context")
        self.log("3. Check authentication dependency configuration")
        self.log("4. Review server logs for routing errors")
        self.log("5. Verify FastAPI router includes the professional context routes")
        
        self.log("="*60)

def main():
    """Main investigation execution"""
    tester = ProfessionalContextTester()
    
    try:
        success = tester.run_investigation()
        tester.print_investigation_summary()
        
        if success:
            print("\n🔍 Investigation completed. Check the diagnosis above for findings.")
            return 0
        else:
            print(f"\n⚠️  Investigation encountered critical errors.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Investigation interrupted by user")
        tester.print_investigation_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during investigation: {str(e)}")
        tester.print_investigation_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())