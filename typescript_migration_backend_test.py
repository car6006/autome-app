#!/usr/bin/env python3
"""
AUTO-ME PWA Backend Health Check After TypeScript Migration
Tests backend service health and core functionality to ensure no regressions
during frontend TypeScript migration process.
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class TypeScriptMigrationBackendTester:
    def __init__(self, base_url="https://autome-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"ts_migration_test_{int(time.time())}@example.com",
            "username": f"tsmigrationuser{int(time.time())}",
            "password": "TSMigrationTest123!",
            "first_name": "TypeScript",
            "last_name": "Migration"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)

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

    def test_backend_service_health(self):
        """Test 1: Backend service health and startup status"""
        self.log("\n🏥 BACKEND SERVICE HEALTH CHECKS")
        
        # Test basic API root endpoint
        success1, response1 = self.run_test(
            "API Root Endpoint",
            "GET",
            "",
            200
        )
        
        if success1:
            self.log(f"   API Message: {response1.get('message', 'N/A')}")
            self.log(f"   API Status: {response1.get('status', 'N/A')}")
        
        # Test comprehensive health endpoint
        success2, response2 = self.run_test(
            "Health Check Endpoint",
            "GET",
            "health",
            200
        )
        
        if success2:
            self.log(f"   Overall Status: {response2.get('status', 'N/A')}")
            self.log(f"   Version: {response2.get('version', 'N/A')}")
            
            services = response2.get('services', {})
            self.log(f"   Database: {services.get('database', 'N/A')}")
            self.log(f"   API: {services.get('api', 'N/A')}")
            self.log(f"   Pipeline: {services.get('pipeline', 'N/A')}")
            
            # Check if any critical services are unhealthy
            critical_services = ['database', 'api']
            unhealthy_services = [s for s in critical_services if services.get(s) not in ['healthy', 'running']]
            
            if unhealthy_services:
                self.log(f"   ⚠️  Critical services unhealthy: {unhealthy_services}")
            else:
                self.log(f"   ✅ All critical services healthy")
        
        return success1 and success2

    def test_database_connectivity(self):
        """Test 2: Database connectivity verification"""
        self.log("\n🗄️  DATABASE CONNECTIVITY CHECKS")
        
        # Test user registration (requires database)
        success, response = self.run_test(
            "Database Write Test (User Registration)",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   User created with ID: {user_data.get('id', 'N/A')}")
            self.log(f"   Database write successful")
            
            # Test database read
            read_success, read_response = self.run_test(
                "Database Read Test (Get User Profile)",
                "GET",
                "auth/me",
                200,
                auth_required=True
            )
            
            if read_success:
                self.log(f"   User profile retrieved: {read_response.get('email', 'N/A')}")
                self.log(f"   Database read successful")
            
            return read_success
        
        return False

    def test_core_auth_endpoints(self):
        """Test 3: Core authentication endpoints"""
        self.log("\n🔐 AUTHENTICATION ENDPOINTS")
        
        # Test login with created user
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        
        success1, response1 = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success1:
            self.log(f"   Login successful for: {response1.get('user', {}).get('email', 'N/A')}")
            
            # Update token from login
            self.auth_token = response1.get('access_token')
            
            # Test profile access
            success2, response2 = self.run_test(
                "Authenticated Profile Access",
                "GET",
                "auth/me",
                200,
                auth_required=True
            )
            
            if success2:
                self.log(f"   Profile access successful")
                return True
        
        return False

    def test_core_business_logic_endpoints(self):
        """Test 4: Core business logic endpoints"""
        self.log("\n📝 CORE BUSINESS LOGIC ENDPOINTS")
        
        # Test note creation
        success1, response1 = self.run_test(
            "Create Text Note",
            "POST",
            "notes",
            200,
            data={
                "title": "TypeScript Migration Test Note",
                "kind": "text",
                "text_content": "This is a test note created during TypeScript migration testing."
            },
            auth_required=True
        )
        
        note_id = None
        if success1:
            note_id = response1.get('id')
            self.log(f"   Note created with ID: {note_id}")
            self.log(f"   Note status: {response1.get('status', 'N/A')}")
        
        # Test note retrieval
        success2 = False
        if note_id:
            success2, response2 = self.run_test(
                "Retrieve Note",
                "GET",
                f"notes/{note_id}",
                200,
                auth_required=True
            )
            
            if success2:
                self.log(f"   Note retrieved: {response2.get('title', 'N/A')}")
                self.log(f"   Note kind: {response2.get('kind', 'N/A')}")
        
        # Test notes listing
        success3, response3 = self.run_test(
            "List User Notes",
            "GET",
            "notes",
            200,
            auth_required=True
        )
        
        if success3:
            notes_count = len(response3) if isinstance(response3, list) else 0
            self.log(f"   Found {notes_count} notes for user")
        
        return success1 and success2 and success3

    def test_file_upload_functionality(self):
        """Test 5: File upload functionality"""
        self.log("\n📤 FILE UPLOAD FUNCTIONALITY")
        
        # Create a minimal test image
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            tmp_file.flush()
            
            try:
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('test_image.png', f, 'image/png')}
                    data = {'title': 'TypeScript Migration Test Upload'}
                    
                    success, response = self.run_test(
                        "File Upload Test",
                        "POST",
                        "upload-file",
                        200,
                        data=data,
                        files=files,
                        auth_required=True
                    )
                
                if success:
                    self.log(f"   File uploaded successfully")
                    self.log(f"   Note ID: {response.get('id', 'N/A')}")
                    self.log(f"   File kind: {response.get('kind', 'N/A')}")
                    self.log(f"   Status: {response.get('status', 'N/A')}")
                
                return success
                
            finally:
                os.unlink(tmp_file.name)

    def test_ai_features_availability(self):
        """Test 6: AI features availability (without full processing)"""
        self.log("\n🤖 AI FEATURES AVAILABILITY")
        
        # Create a note with content for AI testing
        success1, response1 = self.run_test(
            "Create Note for AI Testing",
            "POST",
            "notes",
            200,
            data={
                "title": "AI Test Note - TypeScript Migration",
                "kind": "text",
                "text_content": "This is test content for AI analysis during TypeScript migration testing. The system should be able to process this content for AI features."
            },
            auth_required=True
        )
        
        if not success1:
            return False
        
        note_id = response1.get('id')
        if not note_id:
            return False
        
        # Test AI chat endpoint availability
        success2, response2 = self.run_test(
            "AI Chat Endpoint Test",
            "POST",
            f"notes/{note_id}/ai-chat",
            200,
            data={"question": "What is the main topic of this content?"},
            auth_required=True,
            timeout=60
        )
        
        if success2:
            self.log(f"   AI chat response received")
            self.log(f"   Response length: {len(response2.get('response', ''))}")
        
        # Test professional context endpoints
        success3, response3 = self.run_test(
            "Professional Context Save Test",
            "POST",
            "user/professional-context",
            200,
            data={
                "primary_industry": "Technology",
                "job_role": "Software Developer",
                "key_focus_areas": ["Code quality", "Performance"]
            },
            auth_required=True
        )
        
        if success3:
            self.log(f"   Professional context saved successfully")
        
        success4, response4 = self.run_test(
            "Professional Context Retrieve Test",
            "GET",
            "user/professional-context",
            200,
            auth_required=True
        )
        
        if success4:
            self.log(f"   Professional context retrieved successfully")
            self.log(f"   Industry: {response4.get('primary_industry', 'N/A')}")
        
        return success2 and success3 and success4

    def test_error_handling_and_security(self):
        """Test 7: Error handling and security features"""
        self.log("\n🛡️  ERROR HANDLING AND SECURITY")
        
        # Test unauthorized access
        temp_token = self.auth_token
        self.auth_token = None
        
        success1, response1 = self.run_test(
            "Unauthorized Access Test",
            "GET",
            "auth/me",
            403,  # Should fail with 403
            auth_required=True
        )
        
        # Restore token
        self.auth_token = temp_token
        
        # Test invalid endpoint
        success2, response2 = self.run_test(
            "Invalid Endpoint Test",
            "GET",
            "nonexistent/endpoint",
            404
        )
        
        # Test malformed request
        success3, response3 = self.run_test(
            "Malformed Request Test",
            "POST",
            "notes",
            422,  # Should fail with validation error
            data={"invalid": "data"},
            auth_required=True
        )
        
        if success1:
            self.log(f"   ✅ Unauthorized access properly blocked")
        if success2:
            self.log(f"   ✅ Invalid endpoints properly handled")
        if success3:
            self.log(f"   ✅ Malformed requests properly validated")
        
        return success1 and success2 and success3

    def test_performance_and_responsiveness(self):
        """Test 8: Basic performance and responsiveness"""
        self.log("\n⚡ PERFORMANCE AND RESPONSIVENESS")
        
        # Test multiple rapid requests
        rapid_test_results = []
        
        for i in range(5):
            start_time = time.time()
            success, response = self.run_test(
                f"Rapid Request {i+1}",
                "GET",
                "health",
                200
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            rapid_test_results.append({
                'success': success,
                'response_time': response_time
            })
            
            if success:
                self.log(f"   Request {i+1}: {response_time:.3f}s")
        
        # Calculate average response time
        successful_requests = [r for r in rapid_test_results if r['success']]
        if successful_requests:
            avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
            self.log(f"   Average response time: {avg_response_time:.3f}s")
            
            # Check if response times are reasonable (under 2 seconds)
            if avg_response_time < 2.0:
                self.log(f"   ✅ Response times are good")
                return True
            else:
                self.log(f"   ⚠️  Response times may be slow")
                return len(successful_requests) >= 3  # At least 3/5 successful
        
        return False

    def run_all_tests(self):
        """Run all TypeScript migration backend verification tests"""
        self.log("🚀 STARTING TYPESCRIPT MIGRATION BACKEND VERIFICATION")
        self.log(f"Testing backend at: {self.base_url}")
        self.log(f"API endpoint: {self.api_url}")
        
        test_results = {}
        
        # Run all test categories
        test_results['service_health'] = self.test_backend_service_health()
        test_results['database_connectivity'] = self.test_database_connectivity()
        test_results['auth_endpoints'] = self.test_core_auth_endpoints()
        test_results['business_logic'] = self.test_core_business_logic_endpoints()
        test_results['file_upload'] = self.test_file_upload_functionality()
        test_results['ai_features'] = self.test_ai_features_availability()
        test_results['security'] = self.test_error_handling_and_security()
        test_results['performance'] = self.test_performance_and_responsiveness()
        
        # Summary
        self.log("\n📊 TYPESCRIPT MIGRATION BACKEND VERIFICATION SUMMARY")
        self.log("=" * 60)
        
        passed_categories = 0
        total_categories = len(test_results)
        
        for category, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            category_name = category.replace('_', ' ').title()
            self.log(f"{status} - {category_name}")
            if passed:
                passed_categories += 1
        
        self.log("=" * 60)
        self.log(f"Individual Tests: {self.tests_passed}/{self.tests_run} passed ({self.tests_passed/self.tests_run*100:.1f}%)")
        self.log(f"Test Categories: {passed_categories}/{total_categories} passed ({passed_categories/total_categories*100:.1f}%)")
        
        # Overall assessment
        if passed_categories == total_categories:
            self.log("\n🎉 EXCELLENT: All backend systems are functioning correctly!")
            self.log("   ✅ No regressions detected from TypeScript migration")
            self.log("   ✅ Backend is ready for continued frontend development")
            return True
        elif passed_categories >= total_categories * 0.75:  # 75% pass rate
            self.log("\n✅ GOOD: Most backend systems are functioning correctly")
            self.log("   ⚠️  Some minor issues detected - see details above")
            self.log("   ✅ Backend is generally stable for continued development")
            return True
        else:
            self.log("\n❌ ISSUES DETECTED: Significant backend problems found")
            self.log("   🚨 TypeScript migration may have caused regressions")
            self.log("   🔧 Backend issues should be addressed before continuing")
            return False

def main():
    """Main test execution"""
    tester = TypeScriptMigrationBackendTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        tester.log(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()