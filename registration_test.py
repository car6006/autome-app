#!/usr/bin/env python3
"""
URGENT: Registration Failure Investigation
Focused testing for the registration endpoint and authentication system
"""

import requests
import sys
import json
import time
from datetime import datetime
import traceback

class RegistrationTester:
    def __init__(self, base_url="https://voice2text-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        
    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def test_registration_scenario(self, name, user_data, expected_status=200):
        """Test a specific registration scenario"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            url = f"{self.api_url}/auth/register"
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(url, json=user_data, headers=headers, timeout=30)
            
            self.log(f"   Request URL: {url}")
            self.log(f"   Request Data: {json.dumps(user_data, indent=2)}")
            self.log(f"   Response Status: {response.status_code}")
            
            try:
                response_data = response.json()
                self.log(f"   Response Data: {json.dumps(response_data, indent=2)}")
            except:
                self.log(f"   Response Text: {response.text}")
                response_data = {}
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - SUCCESS")
                
                # Check token generation if successful registration
                if expected_status == 200:
                    access_token = response_data.get('access_token')
                    user_info = response_data.get('user', {})
                    
                    if access_token:
                        self.log(f"   ✅ Access token generated: {access_token[:20]}...")
                    else:
                        self.log(f"   ❌ No access token in response")
                    
                    if user_info.get('id'):
                        self.log(f"   ✅ User ID created: {user_info['id']}")
                    else:
                        self.log(f"   ❌ No user ID in response")
                    
                    if user_info.get('email'):
                        self.log(f"   ✅ Email stored: {user_info['email']}")
                    else:
                        self.log(f"   ❌ No email in user data")
                
                return True, response_data
            else:
                self.log(f"❌ {name} - FAILED")
                self.log(f"   Expected status: {expected_status}, Got: {response.status_code}")
                
                # Capture failure details
                failure_info = {
                    'test_name': name,
                    'expected_status': expected_status,
                    'actual_status': response.status_code,
                    'request_data': user_data,
                    'response_data': response_data,
                    'response_text': response.text
                }
                self.failures.append(failure_info)
                
                return False, response_data
                
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}")
            self.log(f"   Exception details: {traceback.format_exc()}")
            
            failure_info = {
                'test_name': name,
                'expected_status': expected_status,
                'actual_status': 'EXCEPTION',
                'request_data': user_data,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.failures.append(failure_info)
            
            return False, {}

    def test_database_connectivity(self):
        """Test if the database is accessible by checking API health"""
        self.log("🔍 Testing Database Connectivity...")
        
        try:
            url = f"{self.api_url}/"
            response = requests.get(url, timeout=10)
            
            self.log(f"   API Health Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log(f"   API Response: {data}")
                    self.log("   ✅ API is responding correctly")
                    return True
                except:
                    self.log(f"   ⚠️  API responding but no JSON: {response.text}")
                    return True
            else:
                self.log(f"   ❌ API health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Database connectivity error: {str(e)}")
            return False

    def test_authentication_system(self, email, password):
        """Test the authentication system with login"""
        self.log("🔍 Testing Authentication System...")
        
        try:
            url = f"{self.api_url}/auth/login"
            headers = {'Content-Type': 'application/json'}
            login_data = {"email": email, "password": password}
            
            response = requests.post(url, json=login_data, headers=headers, timeout=30)
            
            self.log(f"   Login Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    token = data.get('access_token')
                    user = data.get('user', {})
                    
                    if token:
                        self.log(f"   ✅ Login successful, token: {token[:20]}...")
                        self.log(f"   ✅ User data: {user.get('email')} (ID: {user.get('id')})")
                        return True, token
                    else:
                        self.log(f"   ❌ Login response missing token")
                        return False, None
                except:
                    self.log(f"   ❌ Login response not JSON: {response.text}")
                    return False, None
            else:
                try:
                    error_data = response.json()
                    self.log(f"   ❌ Login failed: {error_data}")
                except:
                    self.log(f"   ❌ Login failed: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"   ❌ Authentication system error: {str(e)}")
            return False, None

    def test_user_profile_access(self, token):
        """Test accessing user profile with token"""
        self.log("🔍 Testing User Profile Access...")
        
        try:
            url = f"{self.api_url}/auth/me"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.log(f"   Profile Access Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    profile_data = response.json()
                    self.log(f"   ✅ Profile access successful")
                    self.log(f"   ✅ Profile data: {json.dumps(profile_data, indent=2)}")
                    return True
                except:
                    self.log(f"   ❌ Profile response not JSON: {response.text}")
                    return False
            else:
                try:
                    error_data = response.json()
                    self.log(f"   ❌ Profile access failed: {error_data}")
                except:
                    self.log(f"   ❌ Profile access failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Profile access error: {str(e)}")
            return False

    def run_comprehensive_registration_tests(self):
        """Run comprehensive registration failure investigation"""
        self.log("🚨 URGENT: Registration Failure Investigation")
        self.log("="*60)
        
        # Test 1: Database connectivity
        if not self.test_database_connectivity():
            self.log("❌ CRITICAL: Database connectivity failed - stopping tests")
            return False
        
        # Test 2: Valid registration with all required fields
        timestamp = int(time.time())
        valid_user = {
            "email": f"test_user_{timestamp}@example.com",
            "username": f"testuser_{timestamp}",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        success, response_data = self.test_registration_scenario(
            "Valid Registration - All Fields", 
            valid_user, 
            200
        )
        
        if success:
            # Test authentication system with the registered user
            auth_success, token = self.test_authentication_system(
                valid_user["email"], 
                valid_user["password"]
            )
            
            if auth_success and token:
                # Test profile access
                self.test_user_profile_access(token)
        
        # Test 3: Registration with different email formats
        email_formats = [
            f"user.with.dots_{timestamp}@example.com",
            f"user+tag_{timestamp}@example.com", 
            f"user_{timestamp}@subdomain.example.com",
            f"expeditors_user_{timestamp}@expeditors.com"
        ]
        
        for i, email in enumerate(email_formats):
            user_data = {
                "email": email,
                "username": f"emailtest_{timestamp}_{i}",
                "password": "TestPassword123!",
                "first_name": "Email",
                "last_name": "Test"
            }
            self.test_registration_scenario(
                f"Email Format Test - {email}", 
                user_data, 
                200
            )
        
        # Test 4: Password validation
        password_tests = [
            ("Short Password", "123", 422),
            ("No Uppercase", "lowercase123!", 422),
            ("No Lowercase", "UPPERCASE123!", 422),
            ("No Numbers", "NoNumbers!", 422),
            ("No Special Chars", "NoSpecialChars123", 422),
            ("Valid Complex", "ValidPassword123!", 200)
        ]
        
        for test_name, password, expected_status in password_tests:
            user_data = {
                "email": f"pwd_test_{timestamp}_{test_name.replace(' ', '_').lower()}@example.com",
                "username": f"pwdtest_{timestamp}_{test_name.replace(' ', '_').lower()}",
                "password": password,
                "first_name": "Password",
                "last_name": "Test"
            }
            self.test_registration_scenario(
                f"Password Validation - {test_name}", 
                user_data, 
                expected_status
            )
        
        # Test 5: Missing required fields
        missing_field_tests = [
            ("Missing Email", {"username": f"noemail_{timestamp}", "password": "Test123!", "first_name": "No", "last_name": "Email"}),
            ("Missing Username", {"email": f"nousername_{timestamp}@example.com", "password": "Test123!", "first_name": "No", "last_name": "Username"}),
            ("Missing Password", {"email": f"nopassword_{timestamp}@example.com", "username": f"nopassword_{timestamp}", "first_name": "No", "last_name": "Password"}),
            ("Missing First Name", {"email": f"nofirst_{timestamp}@example.com", "username": f"nofirst_{timestamp}", "password": "Test123!"}),
            ("Missing Last Name", {"email": f"nolast_{timestamp}@example.com", "username": f"nolast_{timestamp}", "password": "Test123!", "first_name": "No"}),
            ("Empty Fields", {"email": "", "username": "", "password": "", "first_name": "", "last_name": ""})
        ]
        
        for test_name, user_data in missing_field_tests:
            self.test_registration_scenario(
                f"Missing Fields - {test_name}", 
                user_data, 
                422
            )
        
        # Test 6: Duplicate email/username handling
        if success:  # If first registration succeeded
            # Try to register with same email
            duplicate_email_user = valid_user.copy()
            duplicate_email_user["username"] = f"different_username_{timestamp}"
            
            self.test_registration_scenario(
                "Duplicate Email Test", 
                duplicate_email_user, 
                400
            )
            
            # Try to register with same username
            duplicate_username_user = valid_user.copy()
            duplicate_username_user["email"] = f"different_email_{timestamp}@example.com"
            
            self.test_registration_scenario(
                "Duplicate Username Test", 
                duplicate_username_user, 
                400
            )
        
        # Test 7: Professional information fields (optional)
        professional_user = {
            "email": f"professional_{timestamp}@example.com",
            "username": f"professional_{timestamp}",
            "password": "Professional123!",
            "first_name": "Professional",
            "last_name": "User",
            "company": "Test Company Inc.",
            "job_title": "Senior Developer",
            "industry": "Technology",
            "interests": ["AI", "Machine Learning", "Web Development"]
        }
        
        self.test_registration_scenario(
            "Professional Fields Registration", 
            professional_user, 
            200
        )
        
        # Test 8: Invalid email formats
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user..double.dot@example.com",
            "user@.example.com",
            "user@example.",
            "user name@example.com"  # space in email
        ]
        
        for i, invalid_email in enumerate(invalid_emails):
            user_data = {
                "email": invalid_email,
                "username": f"invalidemail_{timestamp}_{i}",
                "password": "ValidPassword123!",
                "first_name": "Invalid",
                "last_name": "Email"
            }
            self.test_registration_scenario(
                f"Invalid Email Format - {invalid_email}", 
                user_data, 
                422
            )
        
        return True

    def print_detailed_failure_analysis(self):
        """Print detailed analysis of all failures"""
        if not self.failures:
            self.log("✅ No failures to analyze!")
            return
        
        self.log("\n" + "="*60)
        self.log("🔍 DETAILED FAILURE ANALYSIS")
        self.log("="*60)
        
        for i, failure in enumerate(self.failures, 1):
            self.log(f"\nFAILURE #{i}: {failure['test_name']}")
            self.log("-" * 40)
            self.log(f"Expected Status: {failure['expected_status']}")
            self.log(f"Actual Status: {failure['actual_status']}")
            
            if 'request_data' in failure:
                self.log(f"Request Data: {json.dumps(failure['request_data'], indent=2)}")
            
            if 'response_data' in failure and failure['response_data']:
                self.log(f"Response Data: {json.dumps(failure['response_data'], indent=2)}")
            
            if 'response_text' in failure:
                self.log(f"Response Text: {failure['response_text']}")
            
            if 'error' in failure:
                self.log(f"Error: {failure['error']}")
            
            if 'traceback' in failure:
                self.log(f"Traceback: {failure['traceback']}")

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 REGISTRATION TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failures:
            self.log(f"\n❌ CRITICAL ISSUES FOUND: {len(self.failures)} failures")
            self.log("Root causes of registration failures:")
            
            # Analyze common failure patterns
            status_codes = {}
            for failure in self.failures:
                status = failure['actual_status']
                if status not in status_codes:
                    status_codes[status] = []
                status_codes[status].append(failure['test_name'])
            
            for status, tests in status_codes.items():
                self.log(f"  - Status {status}: {len(tests)} tests")
                for test in tests[:3]:  # Show first 3 examples
                    self.log(f"    • {test}")
                if len(tests) > 3:
                    self.log(f"    • ... and {len(tests) - 3} more")
        else:
            self.log("\n✅ NO CRITICAL ISSUES FOUND")
            self.log("Registration system appears to be working correctly")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = RegistrationTester()
    
    try:
        tester.log("🚨 STARTING URGENT REGISTRATION FAILURE INVESTIGATION")
        tester.log(f"Target API: {tester.api_url}")
        
        success = tester.run_comprehensive_registration_tests()
        
        # Print detailed failure analysis
        tester.print_detailed_failure_analysis()
        
        # Print summary
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All registration tests passed! No issues found.")
            return 0
        else:
            print(f"\n⚠️  Registration failures detected. Check detailed analysis above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())