#!/usr/bin/env python3
"""
Registration Validation Testing Script
Tests password and username validation fixes as requested in the review.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class RegistrationValidationTester:
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0
        
    def log_test(self, test_name, expected, actual, passed, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = {
            "test": test_name,
            "status": status,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not passed:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        print()

    async def test_password_validation_failures(self):
        """Test passwords that should FAIL validation"""
        print("🔒 TESTING PASSWORD VALIDATION FAILURES")
        print("=" * 50)
        
        # Test cases that should fail
        invalid_passwords = [
            {
                "password": "123",
                "expected_error": "Password must be at least 8 characters long",
                "test_name": "Password too short (3 chars)"
            },
            {
                "password": "lowercase123",
                "expected_error": "Password must contain at least one uppercase letter",
                "test_name": "Password missing uppercase letter"
            },
            {
                "password": "UPPERCASE123",
                "expected_error": "Password must contain at least one lowercase letter", 
                "test_name": "Password missing lowercase letter"
            },
            {
                "password": "PasswordOnly",
                "expected_error": "Password must contain at least one number",
                "test_name": "Password missing number"
            }
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for test_case in invalid_passwords:
                try:
                    # Create registration payload
                    registration_data = {
                        "email": f"test_{datetime.now().timestamp()}@example.com",
                        "username": f"testuser{int(datetime.now().timestamp())}",
                        "password": test_case["password"],
                        "first_name": "Test",
                        "last_name": "User"
                    }
                    
                    response = await client.post(
                        f"{API_BASE}/auth/register",
                        json=registration_data
                    )
                    
                    # Should return 422 for validation error
                    if response.status_code == 422:
                        response_data = response.json()
                        error_detail = response_data.get("detail", [])
                        
                        # Check if the expected error message is present
                        error_found = False
                        actual_error = ""
                        
                        if isinstance(error_detail, list) and len(error_detail) > 0:
                            for error in error_detail:
                                if isinstance(error, dict) and "msg" in error:
                                    actual_error = error["msg"]
                                    if test_case["expected_error"].lower() in actual_error.lower():
                                        error_found = True
                                        break
                        elif isinstance(error_detail, str):
                            actual_error = error_detail
                            if test_case["expected_error"].lower() in actual_error.lower():
                                error_found = True
                        
                        self.log_test(
                            test_case["test_name"],
                            f"422 status with error: {test_case['expected_error']}",
                            f"422 status with error: {actual_error}",
                            error_found,
                            f"Full response: {response_data}"
                        )
                    else:
                        self.log_test(
                            test_case["test_name"],
                            "422 status code",
                            f"{response.status_code} status code",
                            False,
                            f"Response: {response.text}"
                        )
                        
                except Exception as e:
                    self.log_test(
                        test_case["test_name"],
                        "422 validation error",
                        f"Exception: {str(e)}",
                        False,
                        f"Error during request: {str(e)}"
                    )

    async def test_password_validation_success(self):
        """Test passwords that should PASS validation"""
        print("🔓 TESTING PASSWORD VALIDATION SUCCESS")
        print("=" * 50)
        
        # Test cases that should pass
        valid_passwords = [
            {
                "password": "ValidPass123",
                "test_name": "Valid password with uppercase, lowercase, and number"
            },
            {
                "password": "MySecure123!",
                "test_name": "Complex password with special character"
            }
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for test_case in valid_passwords:
                try:
                    # Create unique registration data
                    timestamp = int(datetime.now().timestamp() * 1000)  # More unique
                    registration_data = {
                        "email": f"validtest_{timestamp}@example.com",
                        "username": f"validuser{timestamp}",
                        "password": test_case["password"],
                        "first_name": "Valid",
                        "last_name": "User"
                    }
                    
                    response = await client.post(
                        f"{API_BASE}/auth/register",
                        json=registration_data
                    )
                    
                    # Should return 200 for successful registration
                    if response.status_code == 200:
                        response_data = response.json()
                        has_token = "access_token" in response_data
                        has_user = "user" in response_data
                        
                        self.log_test(
                            test_case["test_name"],
                            "200 status with access_token and user data",
                            f"200 status, token: {has_token}, user: {has_user}",
                            has_token and has_user,
                            f"User ID: {response_data.get('user', {}).get('id', 'N/A')}"
                        )
                    else:
                        self.log_test(
                            test_case["test_name"],
                            "200 status code",
                            f"{response.status_code} status code",
                            False,
                            f"Response: {response.text}"
                        )
                        
                except Exception as e:
                    self.log_test(
                        test_case["test_name"],
                        "200 successful registration",
                        f"Exception: {str(e)}",
                        False,
                        f"Error during request: {str(e)}"
                    )

    async def test_username_validation(self):
        """Test username validation"""
        print("👤 TESTING USERNAME VALIDATION")
        print("=" * 50)
        
        # Test cases for username validation
        username_tests = [
            {
                "username": "ab",
                "should_pass": False,
                "expected_error": "Username must be at least 3 characters long",
                "test_name": "Username too short (2 chars)"
            },
            {
                "username": "user@123",
                "should_pass": False,
                "expected_error": "Username can only contain letters and numbers",
                "test_name": "Username with invalid characters (@)"
            },
            {
                "username": "validuser123",
                "should_pass": True,
                "expected_error": None,
                "test_name": "Valid username (alphanumeric)"
            }
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for test_case in username_tests:
                try:
                    # Create registration data
                    timestamp = int(datetime.now().timestamp() * 1000)
                    registration_data = {
                        "email": f"usertest_{timestamp}@example.com",
                        "username": test_case["username"],
                        "password": "ValidPass123",  # Use valid password
                        "first_name": "Test",
                        "last_name": "User"
                    }
                    
                    response = await client.post(
                        f"{API_BASE}/auth/register",
                        json=registration_data
                    )
                    
                    if test_case["should_pass"]:
                        # Should succeed
                        if response.status_code == 200:
                            response_data = response.json()
                            has_token = "access_token" in response_data
                            
                            self.log_test(
                                test_case["test_name"],
                                "200 status with access_token",
                                f"200 status, token: {has_token}",
                                has_token,
                                f"Successfully registered user: {test_case['username']}"
                            )
                        else:
                            self.log_test(
                                test_case["test_name"],
                                "200 status code",
                                f"{response.status_code} status code",
                                False,
                                f"Response: {response.text}"
                            )
                    else:
                        # Should fail with 422
                        if response.status_code == 422:
                            response_data = response.json()
                            error_detail = response_data.get("detail", [])
                            
                            # Check if the expected error message is present
                            error_found = False
                            actual_error = ""
                            
                            if isinstance(error_detail, list) and len(error_detail) > 0:
                                for error in error_detail:
                                    if isinstance(error, dict) and "msg" in error:
                                        actual_error = error["msg"]
                                        if test_case["expected_error"].lower() in actual_error.lower():
                                            error_found = True
                                            break
                            elif isinstance(error_detail, str):
                                actual_error = error_detail
                                if test_case["expected_error"].lower() in actual_error.lower():
                                    error_found = True
                            
                            self.log_test(
                                test_case["test_name"],
                                f"422 status with error: {test_case['expected_error']}",
                                f"422 status with error: {actual_error}",
                                error_found,
                                f"Full response: {response_data}"
                            )
                        else:
                            self.log_test(
                                test_case["test_name"],
                                "422 status code",
                                f"{response.status_code} status code",
                                False,
                                f"Response: {response.text}"
                            )
                        
                except Exception as e:
                    self.log_test(
                        test_case["test_name"],
                        "Proper validation response",
                        f"Exception: {str(e)}",
                        False,
                        f"Error during request: {str(e)}"
                    )

    async def test_complete_registration_flow(self):
        """Test complete registration flow with valid data"""
        print("🔄 TESTING COMPLETE REGISTRATION FLOW")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # Create completely valid registration data
                timestamp = int(datetime.now().timestamp() * 1000)
                registration_data = {
                    "email": f"complete_test_{timestamp}@example.com",
                    "username": f"completeuser{timestamp}",
                    "password": "CompleteTest123!",
                    "first_name": "Complete",
                    "last_name": "Test",
                    "profession": "Software Engineer",
                    "industry": "Technology",
                    "interests": "Testing, Development"
                }
                
                # Step 1: Register user
                response = await client.post(
                    f"{API_BASE}/auth/register",
                    json=registration_data
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    access_token = response_data.get("access_token")
                    user_data = response_data.get("user", {})
                    
                    # Verify registration response structure
                    has_token = bool(access_token)
                    has_user_id = bool(user_data.get("id"))
                    has_email = user_data.get("email") == registration_data["email"]
                    has_username = user_data.get("username") == registration_data["username"]
                    
                    registration_success = has_token and has_user_id and has_email and has_username
                    
                    self.log_test(
                        "Complete registration with valid data",
                        "200 status with complete user data and token",
                        f"Token: {has_token}, ID: {has_user_id}, Email: {has_email}, Username: {has_username}",
                        registration_success,
                        f"User ID: {user_data.get('id')}, Email: {user_data.get('email')}"
                    )
                    
                    if registration_success:
                        # Step 2: Test login with registered credentials
                        login_data = {
                            "email": registration_data["email"],
                            "password": registration_data["password"]
                        }
                        
                        login_response = await client.post(
                            f"{API_BASE}/auth/login",
                            json=login_data
                        )
                        
                        if login_response.status_code == 200:
                            login_response_data = login_response.json()
                            login_token = login_response_data.get("access_token")
                            
                            self.log_test(
                                "Login with registered credentials",
                                "200 status with access token",
                                f"200 status, token received: {bool(login_token)}",
                                bool(login_token),
                                f"Login successful for user: {registration_data['email']}"
                            )
                            
                            # Step 3: Test authenticated endpoint access
                            if login_token:
                                headers = {"Authorization": f"Bearer {login_token}"}
                                profile_response = await client.get(
                                    f"{API_BASE}/auth/me",
                                    headers=headers
                                )
                                
                                if profile_response.status_code == 200:
                                    profile_data = profile_response.json()
                                    profile_email = profile_data.get("email")
                                    
                                    self.log_test(
                                        "Access authenticated endpoint",
                                        "200 status with user profile",
                                        f"200 status, correct email: {profile_email == registration_data['email']}",
                                        profile_email == registration_data["email"],
                                        f"Profile retrieved for: {profile_email}"
                                    )
                                else:
                                    self.log_test(
                                        "Access authenticated endpoint",
                                        "200 status",
                                        f"{profile_response.status_code} status",
                                        False,
                                        f"Profile access failed: {profile_response.text}"
                                    )
                        else:
                            self.log_test(
                                "Login with registered credentials",
                                "200 status",
                                f"{login_response.status_code} status",
                                False,
                                f"Login failed: {login_response.text}"
                            )
                else:
                    self.log_test(
                        "Complete registration with valid data",
                        "200 status",
                        f"{response.status_code} status",
                        False,
                        f"Registration failed: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(
                    "Complete registration flow",
                    "Successful end-to-end flow",
                    f"Exception: {str(e)}",
                    False,
                    f"Error during complete flow: {str(e)}"
                )

    async def test_error_message_quality(self):
        """Test that error messages are clear and helpful"""
        print("💬 TESTING ERROR MESSAGE QUALITY")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # Test multiple validation errors at once
                registration_data = {
                    "email": "invalid-email",  # Invalid email format
                    "username": "ab",  # Too short
                    "password": "123",  # Too short, missing uppercase, lowercase
                    "first_name": "Test"
                }
                
                response = await client.post(
                    f"{API_BASE}/auth/register",
                    json=registration_data
                )
                
                if response.status_code == 422:
                    response_data = response.json()
                    error_detail = response_data.get("detail", [])
                    
                    # Count different types of validation errors
                    error_types = {
                        "email": False,
                        "username": False,
                        "password": False
                    }
                    
                    error_messages = []
                    
                    if isinstance(error_detail, list):
                        for error in error_detail:
                            if isinstance(error, dict):
                                msg = error.get("msg", "")
                                field = error.get("loc", [])
                                error_messages.append(f"{field}: {msg}")
                                
                                # Check for specific error types
                                if "email" in str(field).lower() or "email" in msg.lower():
                                    error_types["email"] = True
                                if "username" in str(field).lower() or "username" in msg.lower():
                                    error_types["username"] = True
                                if "password" in str(field).lower() or "password" in msg.lower():
                                    error_types["password"] = True
                    
                    # Check if all expected error types are present
                    all_errors_present = all(error_types.values())
                    error_count = len(error_messages)
                    
                    self.log_test(
                        "Multiple validation errors with clear messages",
                        "422 status with email, username, and password errors",
                        f"422 status with {error_count} errors, all types: {all_errors_present}",
                        all_errors_present and error_count >= 3,
                        f"Error messages: {'; '.join(error_messages)}"
                    )
                else:
                    self.log_test(
                        "Multiple validation errors",
                        "422 status with detailed errors",
                        f"{response.status_code} status",
                        False,
                        f"Response: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(
                    "Error message quality test",
                    "Clear validation error messages",
                    f"Exception: {str(e)}",
                    False,
                    f"Error during test: {str(e)}"
                )

    async def run_all_tests(self):
        """Run all registration validation tests"""
        print("🚀 STARTING REGISTRATION VALIDATION TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        print()
        
        # Run all test categories
        await self.test_password_validation_failures()
        await self.test_password_validation_success()
        await self.test_username_validation()
        await self.test_complete_registration_flow()
        await self.test_error_message_quality()
        
        # Print summary
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests / self.total_tests * 100):.1f}%")
        print()
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test["passed"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}")
                print(f"    Expected: {test['expected']}")
                print(f"    Actual: {test['actual']}")
                if test['details']:
                    print(f"    Details: {test['details']}")
                print()
        else:
            print("🎉 ALL TESTS PASSED!")
        
        return self.passed_tests == self.total_tests

async def main():
    """Main test execution"""
    tester = RegistrationValidationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("✅ REGISTRATION VALIDATION TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("❌ REGISTRATION VALIDATION TESTING COMPLETED WITH FAILURES")
        return 1

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)