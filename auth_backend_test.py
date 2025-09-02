#!/usr/bin/env python3
"""
AUTO-ME PWA Authentication Backend API Tests
Comprehensive testing of authentication endpoints after React runtime error fix
"""

import requests
import sys
import json
import time
from datetime import datetime
import uuid

class AuthenticationTester:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_id = None
        
        # Generate unique test data
        timestamp = int(time.time())
        self.test_user_data = {
            "email": f"auth_test_{timestamp}@example.com",
            "username": f"authtest{timestamp}",
            "password": "AuthTest123!",
            "first_name": "Authentication",
            "last_name": "Tester",
            "profession": "Software Engineer",
            "industry": "Technology",
            "interests": "API Testing, Authentication, Security"
        }
        
        # Test user for forgot password flow
        self.forgot_password_user = {
            "email": f"forgot_test_{timestamp}@example.com", 
            "username": f"forgottest{timestamp}",
            "password": "ForgotTest123!",
            "first_name": "Forgot",
            "last_name": "Password"
        }

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

    def test_user_registration_with_professional_fields(self):
        """Test user registration with all professional fields"""
        success, response = self.run_test(
            "User Registration with Professional Fields",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.test_user_id = user_data.get('id')
            self.log(f"   Registered user ID: {self.test_user_id}")
            self.log(f"   Email: {user_data.get('email')}")
            self.log(f"   First Name: {user_data.get('profile', {}).get('first_name')}")
            self.log(f"   Last Name: {user_data.get('profile', {}).get('last_name')}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
            
            # Validate JWT token format
            if self.auth_token:
                token_parts = self.auth_token.split('.')
                if len(token_parts) == 3:
                    self.log(f"   JWT token format: Valid (3 parts)")
                else:
                    self.log(f"   JWT token format: Invalid ({len(token_parts)} parts)")
        return success

    def test_user_login(self):
        """Test user login with valid credentials"""
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        if success:
            token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Login successful for: {user_data.get('email')}")
            self.log(f"   User ID: {user_data.get('id')}")
            self.log(f"   Token type: {response.get('token_type')}")
            
            # Validate token is different or same as registration token
            if token and self.auth_token:
                if token == self.auth_token:
                    self.log(f"   Token consistency: Same as registration token")
                else:
                    self.log(f"   Token consistency: New token generated")
                    self.auth_token = token  # Update to new token
        return success

    def test_get_current_user_profile(self):
        """Test GET /api/auth/me endpoint"""
        success, response = self.run_test(
            "Get Current User Profile",
            "GET",
            "auth/me",
            200,
            auth_required=True
        )
        if success:
            self.log(f"   Profile email: {response.get('email')}")
            self.log(f"   Profile ID: {response.get('id')}")
            profile = response.get('profile', {})
            self.log(f"   First name: {profile.get('first_name')}")
            self.log(f"   Last name: {profile.get('last_name')}")
            self.log(f"   Notes count: {response.get('notes_count', 0)}")
            self.log(f"   Created at: {response.get('created_at')}")
        return success

    def test_invalid_login_credentials(self):
        """Test login with invalid credentials"""
        invalid_login = {
            "email": self.test_user_data["email"],
            "password": "WrongPassword123!"
        }
        success, response = self.run_test(
            "Invalid Login Credentials",
            "POST",
            "auth/login",
            401,
            data=invalid_login
        )
        if success:
            self.log(f"   Error message: {response.get('detail', 'No error message')}")
        return success

    def test_login_missing_fields(self):
        """Test login with missing required fields"""
        # Test missing email
        success1, _ = self.run_test(
            "Login Missing Email",
            "POST",
            "auth/login",
            422,  # Validation error
            data={"password": "TestPassword123!"}
        )
        
        # Test missing password
        success2, _ = self.run_test(
            "Login Missing Password",
            "POST",
            "auth/login",
            422,  # Validation error
            data={"email": "test@example.com"}
        )
        
        return success1 and success2

    def test_registration_missing_fields(self):
        """Test registration with missing required fields"""
        # Test missing email
        incomplete_data = self.test_user_data.copy()
        del incomplete_data['email']
        
        success1, _ = self.run_test(
            "Registration Missing Email",
            "POST",
            "auth/register",
            422,  # Validation error
            data=incomplete_data
        )
        
        # Test missing password
        incomplete_data2 = self.test_user_data.copy()
        del incomplete_data2['password']
        
        success2, _ = self.run_test(
            "Registration Missing Password",
            "POST",
            "auth/register",
            422,  # Validation error
            data=incomplete_data2
        )
        
        return success1 and success2

    def test_duplicate_user_registration(self):
        """Test registration with duplicate email"""
        success, response = self.run_test(
            "Duplicate User Registration",
            "POST",
            "auth/register",
            400,  # Should fail with 400
            data=self.test_user_data
        )
        if success:
            self.log(f"   Error message: {response.get('detail', 'No error message')}")
        return success

    def test_invalid_email_format(self):
        """Test registration with invalid email format"""
        invalid_email_data = self.test_user_data.copy()
        invalid_email_data['email'] = "invalid-email-format"
        invalid_email_data['username'] = f"invalidemail{int(time.time())}"
        
        success, response = self.run_test(
            "Invalid Email Format",
            "POST",
            "auth/register",
            422,  # Validation error
            data=invalid_email_data
        )
        return success

    def test_weak_password(self):
        """Test registration with weak password"""
        weak_password_data = self.test_user_data.copy()
        weak_password_data['password'] = "123"  # Too short and weak
        weak_password_data['email'] = f"weak_pass_{int(time.time())}@example.com"
        weak_password_data['username'] = f"weakpass{int(time.time())}"
        
        success, response = self.run_test(
            "Weak Password Registration",
            "POST",
            "auth/register",
            422,  # Validation error
            data=weak_password_data
        )
        return success

    def test_unauthorized_access_to_protected_endpoint(self):
        """Test accessing protected endpoint without authentication"""
        # Temporarily clear token
        temp_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Unauthorized Access to /auth/me",
            "GET",
            "auth/me",
            401,  # Should fail with 401
            auth_required=True
        )
        
        # Restore token
        self.auth_token = temp_token
        return success

    def test_invalid_jwt_token(self):
        """Test using invalid JWT token"""
        # Temporarily set invalid token
        temp_token = self.auth_token
        self.auth_token = "invalid.jwt.token"
        
        success, response = self.run_test(
            "Invalid JWT Token",
            "GET",
            "auth/me",
            401,  # Should fail with 401
            auth_required=True
        )
        
        # Restore valid token
        self.auth_token = temp_token
        return success

    def test_expired_jwt_token(self):
        """Test using expired JWT token (simulated)"""
        # Use a token that looks valid but is expired
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        temp_token = self.auth_token
        self.auth_token = expired_token
        
        success, response = self.run_test(
            "Expired JWT Token",
            "GET",
            "auth/me",
            401,  # Should fail with 401
            auth_required=True
        )
        
        # Restore valid token
        self.auth_token = temp_token
        return success

    def test_setup_forgot_password_user(self):
        """Setup a user for forgot password testing"""
        success, response = self.run_test(
            "Setup Forgot Password User",
            "POST",
            "auth/register",
            200,
            data=self.forgot_password_user
        )
        if success:
            self.log(f"   Forgot password test user created: {self.forgot_password_user['email']}")
        return success

    def test_verify_user_exists(self):
        """Test POST /api/auth/verify-user endpoint"""
        success, response = self.run_test(
            "Verify User Exists",
            "POST",
            "auth/verify-user",
            200,
            data={"email": self.forgot_password_user["email"]}
        )
        if success:
            self.log(f"   User exists: {response.get('exists', False)}")
            self.log(f"   Message: {response.get('message', 'No message')}")
        return success

    def test_verify_user_not_exists(self):
        """Test verify-user with non-existent email"""
        success, response = self.run_test(
            "Verify Non-existent User",
            "POST",
            "auth/verify-user",
            404,
            data={"email": f"nonexistent_{int(time.time())}@example.com"}
        )
        if success:
            self.log(f"   Error message: {response.get('detail', 'No error message')}")
        return success

    def test_verify_user_missing_email(self):
        """Test verify-user with missing email"""
        success, response = self.run_test(
            "Verify User Missing Email",
            "POST",
            "auth/verify-user",
            400,
            data={}
        )
        return success

    def test_reset_password(self):
        """Test POST /api/auth/reset-password endpoint"""
        new_password = "NewPassword123!"
        success, response = self.run_test(
            "Reset Password",
            "POST",
            "auth/reset-password",
            200,
            data={
                "email": self.forgot_password_user["email"],
                "newPassword": new_password
            }
        )
        if success:
            self.log(f"   Reset message: {response.get('message', 'No message')}")
            # Update the password for future tests
            self.forgot_password_user["password"] = new_password
        return success

    def test_reset_password_nonexistent_user(self):
        """Test reset password for non-existent user"""
        success, response = self.run_test(
            "Reset Password Non-existent User",
            "POST",
            "auth/reset-password",
            404,
            data={
                "email": f"nonexistent_{int(time.time())}@example.com",
                "newPassword": "NewPassword123!"
            }
        )
        return success

    def test_reset_password_weak_password(self):
        """Test reset password with weak password"""
        success, response = self.run_test(
            "Reset Password Weak Password",
            "POST",
            "auth/reset-password",
            400,
            data={
                "email": self.forgot_password_user["email"],
                "newPassword": "123"  # Too short
            }
        )
        return success

    def test_reset_password_missing_fields(self):
        """Test reset password with missing fields"""
        # Missing email
        success1, _ = self.run_test(
            "Reset Password Missing Email",
            "POST",
            "auth/reset-password",
            400,
            data={"newPassword": "NewPassword123!"}
        )
        
        # Missing password
        success2, _ = self.run_test(
            "Reset Password Missing Password",
            "POST",
            "auth/reset-password",
            400,
            data={"email": self.forgot_password_user["email"]}
        )
        
        return success1 and success2

    def test_login_with_reset_password(self):
        """Test login with the new reset password"""
        login_data = {
            "email": self.forgot_password_user["email"],
            "password": self.forgot_password_user["password"]  # Updated password
        }
        success, response = self.run_test(
            "Login with Reset Password",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        if success:
            self.log(f"   Login successful with reset password")
            self.log(f"   User: {response.get('user', {}).get('email')}")
        return success

    def test_jwt_token_validation_flow(self):
        """Test complete JWT token validation flow"""
        # 1. Register new user
        jwt_test_user = {
            "email": f"jwt_test_{int(time.time())}@example.com",
            "username": f"jwttest{int(time.time())}",
            "password": "JWTTest123!",
            "first_name": "JWT",
            "last_name": "Tester"
        }
        
        success1, response1 = self.run_test(
            "JWT Flow - Register User",
            "POST",
            "auth/register",
            200,
            data=jwt_test_user
        )
        
        if not success1:
            return False
            
        jwt_token = response1.get('access_token')
        if not jwt_token:
            self.log("   ❌ No JWT token received")
            return False
            
        # 2. Use token to access protected endpoint
        temp_token = self.auth_token
        self.auth_token = jwt_token
        
        success2, response2 = self.run_test(
            "JWT Flow - Use Token",
            "GET",
            "auth/me",
            200,
            auth_required=True
        )
        
        # 3. Verify token gives access to user's own data
        if success2:
            profile_email = response2.get('email')
            if profile_email == jwt_test_user['email']:
                self.log(f"   ✅ JWT token correctly identifies user: {profile_email}")
                success3 = True
            else:
                self.log(f"   ❌ JWT token mismatch: expected {jwt_test_user['email']}, got {profile_email}")
                success3 = False
        else:
            success3 = False
            
        # Restore original token
        self.auth_token = temp_token
        
        return success1 and success2 and success3

    def run_all_tests(self):
        """Run all authentication tests"""
        self.log("🚀 Starting Comprehensive Authentication Tests")
        self.log("=" * 60)
        
        # Core Authentication Tests
        self.log("\n📝 REGISTRATION TESTS")
        self.test_user_registration_with_professional_fields()
        self.test_duplicate_user_registration()
        self.test_registration_missing_fields()
        self.test_invalid_email_format()
        self.test_weak_password()
        
        self.log("\n🔐 LOGIN TESTS")
        self.test_user_login()
        self.test_invalid_login_credentials()
        self.test_login_missing_fields()
        
        self.log("\n👤 USER PROFILE TESTS")
        self.test_get_current_user_profile()
        
        self.log("\n🛡️ SECURITY TESTS")
        self.test_unauthorized_access_to_protected_endpoint()
        self.test_invalid_jwt_token()
        self.test_expired_jwt_token()
        
        self.log("\n🔄 FORGOT PASSWORD FLOW TESTS")
        self.test_setup_forgot_password_user()
        self.test_verify_user_exists()
        self.test_verify_user_not_exists()
        self.test_verify_user_missing_email()
        self.test_reset_password()
        self.test_reset_password_nonexistent_user()
        self.test_reset_password_weak_password()
        self.test_reset_password_missing_fields()
        self.test_login_with_reset_password()
        
        self.log("\n🎫 JWT TOKEN VALIDATION TESTS")
        self.test_jwt_token_validation_flow()
        
        # Final Results
        self.log("\n" + "=" * 60)
        self.log("🏁 AUTHENTICATION TESTING COMPLETE")
        self.log(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            self.log("🎉 EXCELLENT: Authentication system is working properly!")
        elif success_rate >= 75:
            self.log("✅ GOOD: Authentication system is mostly functional")
        elif success_rate >= 50:
            self.log("⚠️ WARNING: Authentication system has significant issues")
        else:
            self.log("🚨 CRITICAL: Authentication system is severely broken")
            
        return success_rate >= 75

if __name__ == "__main__":
    tester = AuthenticationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)