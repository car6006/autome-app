#!/usr/bin/env python3
"""
Security Headers and Exception Handler Testing
Comprehensive test for security headers and exception handling
"""

import requests
import json
import time

class SecurityHeadersTester:
    def __init__(self, base_url="https://audio-pipeline-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_results = []

    def log(self, message):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def check_security_headers(self, response, endpoint_name):
        """Check for required security headers"""
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': 'default-src \'self\''
        }
        
        missing_headers = []
        incorrect_headers = []
        
        for header, expected_value in required_headers.items():
            if header not in response.headers:
                missing_headers.append(header)
            elif response.headers[header] != expected_value:
                incorrect_headers.append(f"{header}: got '{response.headers[header]}', expected '{expected_value}'")
        
        result = {
            'endpoint': endpoint_name,
            'status_code': response.status_code,
            'missing_headers': missing_headers,
            'incorrect_headers': incorrect_headers,
            'all_headers_present': len(missing_headers) == 0 and len(incorrect_headers) == 0
        }
        
        self.test_results.append(result)
        
        if result['all_headers_present']:
            self.log(f"✅ {endpoint_name} - All security headers present and correct")
        else:
            self.log(f"❌ {endpoint_name} - Security header issues:")
            for header in missing_headers:
                self.log(f"   Missing: {header}")
            for header in incorrect_headers:
                self.log(f"   Incorrect: {header}")
        
        return result['all_headers_present']

    def test_security_headers_comprehensive(self):
        """Test security headers across all major endpoints"""
        self.log("🛡️ Testing Security Headers Across All Endpoints")
        
        # Test endpoints that should have security headers
        endpoints_to_test = [
            ("GET", "", "Root API"),
            ("GET", "notes", "Notes List"),
            ("POST", "auth/login", "Authentication", {"email": "test@example.com", "password": "test"}),
            ("GET", "metrics", "Metrics"),
            ("GET", "notes/invalid-id", "Invalid Note ID"),
            ("POST", "notes", "Create Note", {"title": "Test", "kind": "text"}),
            ("POST", "upload-file", "File Upload (Invalid)", None, True),  # Will be invalid without file
        ]
        
        for test_data in endpoints_to_test:
            try:
                method, endpoint, name = test_data[0], test_data[1], test_data[2]
                data = test_data[3] if len(test_data) > 3 else None
                is_file_upload = test_data[4] if len(test_data) > 4 else False
                
                url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
                
                if method == "GET":
                    response = requests.get(url, timeout=30)
                elif method == "POST":
                    if is_file_upload:  # File upload test
                        response = requests.post(url, timeout=30)  # No files, should error
                    else:
                        response = requests.post(url, json=data, timeout=30)
                
                self.check_security_headers(response, name)
                
            except Exception as e:
                self.log(f"❌ {name} - Request failed: {e}")

    def test_exception_handlers(self):
        """Test that exception handlers don't expose sensitive information"""
        self.log("\n🚨 Testing Global Exception Handlers")
        
        # Test various ways to trigger exceptions
        exception_tests = [
            # Invalid JSON that might cause parsing errors
            ("POST", "notes", "Invalid JSON", "not valid json"),
            # Extremely large payload that might cause memory errors
            ("POST", "notes", "Large Payload", {"title": "x" * 100000, "kind": "text"}),
            # Invalid content types
            ("POST", "notes", "Invalid Content-Type", {"title": "test"}, {"Content-Type": "text/plain"}),
        ]
        
        for method, endpoint, name, data, *extra in exception_tests:
            try:
                url = f"{self.api_url}/{endpoint}"
                headers = extra[0] if extra else {'Content-Type': 'application/json'}
                
                if isinstance(data, str):
                    # Send raw string data
                    response = requests.post(url, data=data, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
                
                # Check that response doesn't contain stack traces
                response_text = response.text.lower()
                
                # Look for stack trace indicators
                stack_trace_indicators = [
                    'traceback', 'file "/', '/app/backend/', 
                    'line ', 'raise ', 'exception in',
                    'internal server error:', 'unhandled exception:'
                ]
                
                has_stack_trace = any(indicator in response_text for indicator in stack_trace_indicators)
                
                if has_stack_trace:
                    self.log(f"❌ {name} - Stack trace detected in response")
                    # Print first 200 chars of response for debugging
                    self.log(f"   Response preview: {response.text[:200]}...")
                else:
                    self.log(f"✅ {name} - No stack trace in error response")
                
                # Also check security headers
                self.check_security_headers(response, f"{name} (Exception Test)")
                
            except Exception as e:
                self.log(f"❌ {name} - Test failed: {e}")

    def test_cors_and_security_middleware(self):
        """Test CORS and security middleware functionality"""
        self.log("\n🌐 Testing CORS and Security Middleware")
        
        # Test CORS headers
        try:
            response = requests.options(f"{self.api_url}/", 
                                      headers={'Origin': 'https://example.com'}, 
                                      timeout=30)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods', 
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = any(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log("✅ CORS headers detected")
            else:
                self.log("ℹ️  CORS headers not present (may be configured differently)")
            
            # Check security headers on OPTIONS request
            self.check_security_headers(response, "CORS OPTIONS Request")
            
        except Exception as e:
            self.log(f"❌ CORS test failed: {e}")

    def run_security_headers_tests(self):
        """Run all security header tests"""
        self.log("🔒 Starting Comprehensive Security Headers Testing")
        
        self.test_security_headers_comprehensive()
        self.test_exception_handlers()
        self.test_cors_and_security_middleware()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("🛡️ SECURITY HEADERS TEST SUMMARY")
        self.log("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['all_headers_present'])
        failed_tests = total_tests - passed_tests
        
        self.log(f"Total header tests: {total_tests}")
        self.log(f"Tests with all headers: {passed_tests}")
        self.log(f"Tests with missing headers: {failed_tests}")
        
        if failed_tests > 0:
            self.log(f"\n🚨 ENDPOINTS WITH MISSING SECURITY HEADERS:")
            for result in self.test_results:
                if not result['all_headers_present']:
                    self.log(f"  ❌ {result['endpoint']} (Status: {result['status_code']})")
                    for header in result['missing_headers']:
                        self.log(f"     Missing: {header}")
                    for header in result['incorrect_headers']:
                        self.log(f"     Incorrect: {header}")
        else:
            self.log(f"\n✅ ALL ENDPOINTS HAVE PROPER SECURITY HEADERS")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        self.log(f"\nSecurity headers success rate: {success_rate:.1f}%")
        self.log("="*60)
        
        return failed_tests == 0

def main():
    tester = SecurityHeadersTester()
    
    try:
        success = tester.run_security_headers_tests()
        
        if success:
            print("\n🎉 All security header tests passed!")
            print("✅ Security headers are properly configured across all endpoints")
            return 0
        else:
            print("\n⚠️  Some endpoints are missing security headers")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted")
        return 1
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())