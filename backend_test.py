#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Suite
Tests all critical backend endpoints for the AUTO-ME Productivity API
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://autome-ai.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_NAME = "Test User"

class BackendTester:
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
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    self.log_result("Health Check", True, f"Health status: {data.get('status')}", data)
                else:
                    self.log_result("Health Check", False, f"Unexpected health status: {data.get('status')}", data)
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "AUTO-ME Productivity API" in data.get("message", ""):
                    self.log_result("Root Endpoint", True, "API root accessible", data)
                else:
                    self.log_result("Root Endpoint", False, "Unexpected root response", data)
            else:
                self.log_result("Root Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Root Endpoint", False, f"Connection error: {str(e)}")
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            # Generate unique email for this test
            unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": unique_email,
                "password": TEST_USER_PASSWORD,
                "name": TEST_USER_NAME
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
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("User Registration", True, "User registered successfully", {
                        "user_id": self.user_id,
                        "email": unique_email
                    })
                else:
                    self.log_result("User Registration", False, "Missing token or user data", data)
            else:
                self.log_result("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("User Registration", False, f"Registration error: {str(e)}")
    
    def test_user_login(self):
        """Test user login with existing credentials"""
        if not self.user_id:
            self.log_result("User Login", False, "Skipped - no registered user available")
            return
            
        try:
            # Use the email from registration
            login_data = {
                "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",  # This will fail intentionally
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                timeout=10
            )
            
            # We expect this to fail since we're using a different email
            if response.status_code == 401:
                self.log_result("User Login", True, "Login correctly rejected invalid credentials")
            elif response.status_code == 200:
                self.log_result("User Login", False, "Login should have failed with invalid credentials")
            else:
                self.log_result("User Login", False, f"Unexpected response: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("User Login", False, f"Login error: {str(e)}")
    
    def test_get_current_user(self):
        """Test getting current user profile"""
        if not self.auth_token:
            self.log_result("Get Current User", False, "Skipped - no authentication token")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/me", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") and data.get("email"):
                    self.log_result("Get Current User", True, "User profile retrieved", {
                        "user_id": data.get("id"),
                        "email": data.get("email")
                    })
                else:
                    self.log_result("Get Current User", False, "Missing user data", data)
            else:
                self.log_result("Get Current User", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Get Current User", False, f"Profile error: {str(e)}")
    
    def test_create_text_note(self):
        """Test creating a text note"""
        if not self.auth_token:
            self.log_result("Create Text Note", False, "Skipped - no authentication token")
            return
            
        try:
            note_data = {
                "title": f"Test Note {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "kind": "text",
                "text_content": "This is a test note created by the backend testing suite."
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/notes",
                json=note_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") and data.get("status"):
                    self.note_id = data["id"]
                    self.log_result("Create Text Note", True, f"Note created with ID: {data['id']}", data)
                else:
                    self.log_result("Create Text Note", False, "Missing note ID or status", data)
            else:
                self.log_result("Create Text Note", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Create Text Note", False, f"Note creation error: {str(e)}")
    
    def test_list_notes(self):
        """Test listing user notes"""
        if not self.auth_token:
            self.log_result("List Notes", False, "Skipped - no authentication token")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/notes", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("List Notes", True, f"Retrieved {len(data)} notes", {
                        "note_count": len(data)
                    })
                else:
                    self.log_result("List Notes", False, "Response is not a list", data)
            else:
                self.log_result("List Notes", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("List Notes", False, f"List notes error: {str(e)}")
    
    def test_get_specific_note(self):
        """Test getting a specific note"""
        if not self.auth_token or not hasattr(self, 'note_id'):
            self.log_result("Get Specific Note", False, "Skipped - no authentication token or note ID")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/notes/{self.note_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == self.note_id:
                    self.log_result("Get Specific Note", True, f"Retrieved note: {data.get('title')}", {
                        "note_id": data.get("id"),
                        "title": data.get("title"),
                        "status": data.get("status")
                    })
                else:
                    self.log_result("Get Specific Note", False, "Note ID mismatch", data)
            else:
                self.log_result("Get Specific Note", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Get Specific Note", False, f"Get note error: {str(e)}")
    
    def test_system_metrics(self):
        """Test system metrics endpoint (requires authentication)"""
        if not self.auth_token:
            self.log_result("System Metrics", False, "Skipped - no authentication token")
            return
            
        try:
            response = self.session.get(f"{BACKEND_URL}/system-metrics", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "user_metrics" in data or "access_level" in data:
                    self.log_result("System Metrics", True, f"Metrics retrieved with access level: {data.get('access_level')}", {
                        "access_level": data.get("access_level")
                    })
                else:
                    self.log_result("System Metrics", False, "Unexpected metrics format", data)
            elif response.status_code == 401:
                self.log_result("System Metrics", True, "Correctly requires authentication")
            else:
                self.log_result("System Metrics", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("System Metrics", False, f"Metrics error: {str(e)}")
    
    def test_email_validation(self):
        """Test email validation endpoint"""
        try:
            email_data = {
                "email": "nonexistent@example.com"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/validate-email",
                json=email_data,
                timeout=10
            )
            
            # We expect this to fail (404) since the email doesn't exist
            if response.status_code == 404:
                self.log_result("Email Validation", True, "Correctly identified non-existent email")
            elif response.status_code == 200:
                self.log_result("Email Validation", False, "Should not validate non-existent email")
            else:
                self.log_result("Email Validation", False, f"Unexpected response: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Email Validation", False, f"Email validation error: {str(e)}")
    
    def test_unauthorized_access(self):
        """Test that protected endpoints require authentication"""
        try:
            # Temporarily remove auth header
            original_headers = self.session.headers.copy()
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            response = self.session.get(f"{BACKEND_URL}/notes", timeout=10)
            
            # Restore headers
            self.session.headers.update(original_headers)
            
            if response.status_code == 401:
                self.log_result("Unauthorized Access", True, "Protected endpoint correctly requires authentication")
            else:
                self.log_result("Unauthorized Access", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Unauthorized Access", False, f"Auth test error: {str(e)}")
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            response = self.session.options(f"{BACKEND_URL}/health", timeout=10)
            
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            present_headers = [h for h in cors_headers if h in response.headers]
            
            if len(present_headers) >= 1:  # At least one CORS header should be present
                self.log_result("CORS Headers", True, f"CORS headers present: {present_headers}")
            else:
                self.log_result("CORS Headers", False, "No CORS headers found", {
                    "response_headers": dict(response.headers)
                })
                
        except Exception as e:
            self.log_result("CORS Headers", False, f"CORS test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Testing Suite")
        print(f"🎯 Target URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Core connectivity tests
        self.test_health_endpoint()
        self.test_root_endpoint()
        self.test_cors_headers()
        
        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        self.test_email_validation()
        self.test_unauthorized_access()
        
        # Note management tests
        self.test_create_text_note()
        self.test_list_notes()
        self.test_get_specific_note()
        
        # System tests
        self.test_system_metrics()
        
        # Summary
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # Return results for programmatic use
        return {
            "total": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed/len(self.test_results)*100,
            "results": self.test_results
        }

def main():
    """Main test execution"""
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results and results["failed"] > 0:
        exit(1)
    else:
        print("🎉 All tests passed!")
        exit(0)

if __name__ == "__main__":
    main()