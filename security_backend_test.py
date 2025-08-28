#!/usr/bin/env python3
"""
AUTO-ME Security Testing - Backend API Security Verification
Tests for stack trace exposure, sensitive information leakage, and security headers
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os
import re

class SecurityTester:
    def __init__(self, base_url="https://whisper-async-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.security_issues = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"security_test_{int(time.time())}@example.com",
            "username": f"sectest_{int(time.time())}",
            "password": "SecurePass123!",
            "first_name": "Security",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def check_for_sensitive_info(self, response_text, response_headers, test_name):
        """Check response for sensitive information exposure"""
        issues = []
        
        # Check for stack traces
        stack_trace_patterns = [
            r'Traceback \(most recent call last\)',
            r'File ".*\.py", line \d+',
            r'raise \w+Error',
            r'Exception in thread',
            r'at .*\.py:\d+',
            r'File "/.*\.py"',
            r'line \d+ in \w+',
            r'^\s*File ".*", line \d+, in .*$',
            r'Error: .*\.py:\d+',
            r'^\s*\w+Error: .*$'
        ]
        
        for pattern in stack_trace_patterns:
            if re.search(pattern, response_text, re.MULTILINE | re.IGNORECASE):
                issues.append(f"Stack trace pattern found: {pattern}")
        
        # Check for file paths
        file_path_patterns = [
            r'/app/backend/.*\.py',
            r'/usr/local/.*\.py',
            r'/opt/.*\.py',
            r'C:\\.*\.py',
            r'__file__',
            r'__name__',
            r'__main__'
        ]
        
        for pattern in file_path_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                issues.append(f"File path exposure: {pattern}")
        
        # Check for database connection strings
        db_patterns = [
            r'mongodb://.*',
            r'postgres://.*',
            r'mysql://.*',
            r'MONGO_URL',
            r'DATABASE_URL',
            r'connection string',
            r'localhost:27017',
            r'localhost:5432'
        ]
        
        for pattern in db_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                issues.append(f"Database connection info exposure: {pattern}")
        
        # Check for API keys and tokens
        api_key_patterns = [
            r'sk-[a-zA-Z0-9]{48,}',  # OpenAI API keys
            r'SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}',  # SendGrid API keys
            r'WHISPER_API_KEY',
            r'OPENAI_API_KEY',
            r'SENDGRID_API_KEY',
            r'JWT_SECRET_KEY',
            r'Bearer [a-zA-Z0-9_-]+',
            r'Authorization: Bearer',
            r'api[_-]?key',
            r'secret[_-]?key'
        ]
        
        for pattern in api_key_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                issues.append(f"API key/token exposure: {pattern}")
        
        # Check for internal error details
        internal_error_patterns = [
            r'Internal server error:.*',
            r'Unhandled exception:.*',
            r'DEBUG:.*',
            r'ERROR:.*\.py:.*',
            r'WARNING:.*\.py:.*',
            r'INFO:.*\.py:.*'
        ]
        
        for pattern in internal_error_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                issues.append(f"Internal error detail exposure: {pattern}")
        
        # Check for environment variables
        env_patterns = [
            r'os\.environ',
            r'getenv\(',
            r'ENV\[',
            r'process\.env',
            r'CORS_ORIGINS',
            r'DB_NAME'
        ]
        
        for pattern in env_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                issues.append(f"Environment variable exposure: {pattern}")
        
        if issues:
            self.security_issues.extend([f"{test_name}: {issue}" for issue in issues])
            return False
        return True

    def check_security_headers(self, response_headers, test_name):
        """Check for required security headers"""
        required_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': 'default-src \'self\''
        }
        
        missing_headers = []
        for header, expected_value in required_headers.items():
            if header not in response_headers:
                missing_headers.append(f"Missing header: {header}")
            elif response_headers[header] != expected_value:
                missing_headers.append(f"Incorrect header value for {header}: got '{response_headers[header]}', expected '{expected_value}'")
        
        if missing_headers:
            self.security_issues.extend([f"{test_name}: {issue}" for issue in missing_headers])
            return False
        return True

    def run_security_test(self, name, method, endpoint, data=None, files=None, expected_status=None, auth_required=False):
        """Run a security-focused test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔒 Security Testing: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            # Check response for sensitive information
            response_text = response.text
            sensitive_info_clean = self.check_for_sensitive_info(response_text, response.headers, name)
            
            # Check security headers
            security_headers_present = self.check_security_headers(response.headers, name)
            
            # Check if error messages are generic
            generic_error = True
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    
                    # Check if error message is too detailed
                    detailed_error_patterns = [
                        r'line \d+',
                        r'File ".*"',
                        r'function \w+',
                        r'module \w+',
                        r'class \w+',
                        r'method \w+',
                        r'variable \w+',
                        r'attribute \w+'
                    ]
                    
                    for pattern in detailed_error_patterns:
                        if re.search(pattern, error_detail, re.IGNORECASE):
                            self.security_issues.append(f"{name}: Detailed error message: {error_detail}")
                            generic_error = False
                            break
                            
                except:
                    pass
            
            # Test passes if no sensitive info found, security headers present, and errors are generic
            test_passed = sensitive_info_clean and security_headers_present and generic_error
            
            if test_passed:
                self.tests_passed += 1
                self.log(f"✅ {name} - Security check passed")
            else:
                self.log(f"❌ {name} - Security issues found")
                
            return test_passed, response
            
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            # Check if the exception message contains sensitive info
            self.check_for_sensitive_info(str(e), {}, f"{name} (Exception)")
            return False, None

    def setup_test_user(self):
        """Create a test user for authenticated tests"""
        success, response = self.run_security_test(
            "User Registration for Security Tests",
            "POST",
            "auth/register",
            data=self.test_user_data,
            expected_status=200
        )
        
        if success and response:
            try:
                response_data = response.json()
                self.auth_token = response_data.get('access_token')
                self.log(f"   Test user created successfully")
                return True
            except:
                pass
        
        self.log(f"   Failed to create test user")
        return False

    def test_error_response_security(self):
        """Test various error conditions for sensitive information exposure"""
        self.log("\n🚨 ERROR RESPONSE SECURITY TESTS")
        
        # Test 1: Non-existent endpoint
        self.run_security_test(
            "Non-existent Endpoint Error",
            "GET",
            "non-existent-endpoint",
            expected_status=404
        )
        
        # Test 2: Invalid JSON payload
        self.run_security_test(
            "Invalid JSON Payload Error",
            "POST",
            "notes",
            data="invalid json string"
        )
        
        # Test 3: Missing required fields
        self.run_security_test(
            "Missing Required Fields Error",
            "POST",
            "notes",
            data={}
        )
        
        # Test 4: Invalid note ID
        self.run_security_test(
            "Invalid Note ID Error",
            "GET",
            "notes/invalid-note-id-12345"
        )
        
        # Test 5: Malformed file upload
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b'malformed file content')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('malformed.exe', f, 'application/octet-stream')}
                self.run_security_test(
                    "Malformed File Upload Error",
                    "POST",
                    "upload-file",
                    files=files
                )
            
            os.unlink(tmp_file.name)
        
        # Test 6: Oversized request (simulate)
        large_data = {"title": "x" * 10000, "kind": "text", "text_content": "y" * 100000}
        self.run_security_test(
            "Oversized Request Error",
            "POST",
            "notes",
            data=large_data
        )

    def test_authentication_error_security(self):
        """Test authentication error scenarios for sensitive information"""
        self.log("\n🔐 AUTHENTICATION ERROR SECURITY TESTS")
        
        # Test 1: Invalid credentials
        self.run_security_test(
            "Invalid Login Credentials Error",
            "POST",
            "auth/login",
            data={"email": "nonexistent@example.com", "password": "wrongpassword"}
        )
        
        # Test 2: Malformed email
        self.run_security_test(
            "Malformed Email Error",
            "POST",
            "auth/login",
            data={"email": "not-an-email", "password": "password123"}
        )
        
        # Test 3: Missing password
        self.run_security_test(
            "Missing Password Error",
            "POST",
            "auth/login",
            data={"email": "test@example.com"}
        )
        
        # Test 4: Invalid token format
        headers = {'Authorization': 'Bearer invalid-token-format'}
        try:
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=30)
            self.check_for_sensitive_info(response.text, response.headers, "Invalid Token Format Error")
            self.check_security_headers(response.headers, "Invalid Token Format Error")
        except Exception as e:
            self.check_for_sensitive_info(str(e), {}, "Invalid Token Format Error (Exception)")
        
        # Test 5: Expired/malformed JWT
        headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature'}
        try:
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=30)
            self.check_for_sensitive_info(response.text, response.headers, "Malformed JWT Error")
            self.check_security_headers(response.headers, "Malformed JWT Error")
        except Exception as e:
            self.check_for_sensitive_info(str(e), {}, "Malformed JWT Error (Exception)")

    def test_ai_features_error_security(self):
        """Test AI features with invalid data for error security"""
        self.log("\n🤖 AI FEATURES ERROR SECURITY TESTS")
        
        if not self.auth_token:
            self.log("   Skipping AI tests - no auth token available")
            return
        
        # Create a test note first
        success, response = self.run_security_test(
            "Create Note for AI Testing",
            "POST",
            "notes",
            data={"title": "AI Security Test Note", "kind": "text", "text_content": "Test content for AI analysis"},
            auth_required=True
        )
        
        note_id = None
        if success and response:
            try:
                note_data = response.json()
                note_id = note_data.get('id')
            except:
                pass
        
        if not note_id:
            self.log("   Failed to create test note for AI testing")
            return
        
        # Test 1: AI chat with empty question
        self.run_security_test(
            "AI Chat Empty Question Error",
            "POST",
            f"notes/{note_id}/ai-chat",
            data={"question": ""},
            auth_required=True
        )
        
        # Test 2: AI chat with missing question
        self.run_security_test(
            "AI Chat Missing Question Error",
            "POST",
            f"notes/{note_id}/ai-chat",
            data={},
            auth_required=True
        )
        
        # Test 3: AI chat with malformed request
        self.run_security_test(
            "AI Chat Malformed Request Error",
            "POST",
            f"notes/{note_id}/ai-chat",
            data={"invalid_field": "test"},
            auth_required=True
        )
        
        # Test 4: Generate report for non-existent note
        self.run_security_test(
            "Generate Report Non-existent Note Error",
            "POST",
            "notes/non-existent-id/generate-report",
            auth_required=True
        )
        
        # Test 5: Batch report with empty list
        self.run_security_test(
            "Batch Report Empty List Error",
            "POST",
            "notes/batch-report",
            data=[],
            auth_required=True
        )
        
        # Test 6: Export with invalid format
        self.run_security_test(
            "Export Invalid Format Error",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=invalid",
            auth_required=True
        )

    def test_file_processing_error_security(self):
        """Test file processing errors for sensitive information"""
        self.log("\n📁 FILE PROCESSING ERROR SECURITY TESTS")
        
        if not self.auth_token:
            self.log("   Skipping file processing tests - no auth token available")
            return
        
        # Create a test note
        success, response = self.run_security_test(
            "Create Note for File Processing",
            "POST",
            "notes",
            data={"title": "File Processing Test", "kind": "audio"},
            auth_required=True
        )
        
        note_id = None
        if success and response:
            try:
                note_data = response.json()
                note_id = note_data.get('id')
            except:
                pass
        
        if not note_id:
            self.log("   Failed to create test note for file processing")
            return
        
        # Test 1: Upload corrupted audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'corrupted audio data that is not valid mp3')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('corrupted.mp3', f, 'audio/mp3')}
                self.run_security_test(
                    "Upload Corrupted Audio File Error",
                    "POST",
                    f"notes/{note_id}/upload",
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
        
        # Test 2: Upload file with malicious filename
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'some audio data')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('../../etc/passwd.mp3', f, 'audio/mp3')}
                self.run_security_test(
                    "Upload File with Malicious Filename Error",
                    "POST",
                    f"notes/{note_id}/upload",
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)
        
        # Test 3: Upload extremely large file (simulate)
        # Note: We'll create a small file but with a large Content-Length header simulation
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(b'fake large audio file content')
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('large_file.wav', f, 'audio/wav')}
                self.run_security_test(
                    "Upload Large File Error",
                    "POST",
                    f"notes/{note_id}/upload",
                    files=files,
                    auth_required=True
                )
            
            os.unlink(tmp_file.name)

    def test_input_validation_security(self):
        """Test input validation for security issues"""
        self.log("\n✅ INPUT VALIDATION SECURITY TESTS")
        
        # Test 1: SQL injection attempts (even though we use MongoDB)
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_injection_payloads:
            self.run_security_test(
                f"SQL Injection Test: {payload[:20]}...",
                "POST",
                "auth/login",
                data={"email": payload, "password": "test"}
            )
        
        # Test 2: XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            self.run_security_test(
                f"XSS Test: {payload[:20]}...",
                "POST",
                "notes",
                data={"title": payload, "kind": "text", "text_content": payload}
            )
        
        # Test 3: Path traversal attempts
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in path_traversal_payloads:
            self.run_security_test(
                f"Path Traversal Test: {payload[:20]}...",
                "GET",
                f"notes/{payload}"
            )
        
        # Test 4: Command injection attempts
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(whoami)"
        ]
        
        for payload in command_injection_payloads:
            self.run_security_test(
                f"Command Injection Test: {payload[:20]}...",
                "POST",
                "notes",
                data={"title": payload, "kind": "text"}
            )

    def test_network_diagram_security(self):
        """Test network diagram feature security (Expeditors only)"""
        self.log("\n🌐 NETWORK DIAGRAM SECURITY TESTS")
        
        # Test access without authentication
        self.run_security_test(
            "Network Diagram Unauthenticated Access",
            "POST",
            "network/process",
            data={"input_type": "text_description", "content": "test network"}
        )
        
        # Test access with non-Expeditors user
        if self.auth_token:
            self.run_security_test(
                "Network Diagram Non-Expeditors Access",
                "POST",
                "network/process",
                data={"input_type": "text_description", "content": "test network"},
                auth_required=True
            )
        
        # Test malformed network input
        if self.auth_token:
            malformed_inputs = [
                {"input_type": "invalid_type", "content": "test"},
                {"input_type": "", "content": "test"},
                {"content": "test"},  # missing input_type
                {"input_type": "text_description"},  # missing content
                {"input_type": "text_description", "content": ""},  # empty content
            ]
            
            for malformed_input in malformed_inputs:
                self.run_security_test(
                    f"Network Diagram Malformed Input: {str(malformed_input)[:30]}...",
                    "POST",
                    "network/process",
                    data=malformed_input,
                    auth_required=True
                )

    def test_security_headers_comprehensive(self):
        """Comprehensive security headers testing across different endpoints"""
        self.log("\n🛡️ COMPREHENSIVE SECURITY HEADERS TESTS")
        
        # Test security headers on various endpoints
        endpoints_to_test = [
            ("GET", ""),  # Root endpoint
            ("GET", "notes"),  # Notes listing
            ("POST", "auth/login"),  # Authentication
            ("GET", "metrics"),  # Metrics
        ]
        
        for method, endpoint in endpoints_to_test:
            self.run_security_test(
                f"Security Headers Check: {method} /{endpoint}",
                method,
                endpoint,
                data={"email": "test@example.com", "password": "test"} if endpoint == "auth/login" else None
            )

    def run_comprehensive_security_tests(self):
        """Run all security tests"""
        self.log("🔒 Starting AUTO-ME Security Testing Suite")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup test user for authenticated tests
        self.setup_test_user()
        
        # Run all security test categories
        self.test_error_response_security()
        self.test_authentication_error_security()
        self.test_ai_features_error_security()
        self.test_file_processing_error_security()
        self.test_input_validation_security()
        self.test_network_diagram_security()
        self.test_security_headers_comprehensive()
        
        return len(self.security_issues) == 0

    def print_security_summary(self):
        """Print security test summary"""
        self.log("\n" + "="*60)
        self.log("🔒 SECURITY TEST SUMMARY")
        self.log("="*60)
        self.log(f"Security tests run: {self.tests_run}")
        self.log(f"Security tests passed: {self.tests_passed}")
        self.log(f"Security tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Security issues found: {len(self.security_issues)}")
        
        if self.security_issues:
            self.log("\n🚨 SECURITY ISSUES DETECTED:")
            for i, issue in enumerate(self.security_issues, 1):
                self.log(f"  {i}. {issue}")
        else:
            self.log("\n✅ NO SECURITY ISSUES DETECTED")
        
        success_rate = (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0
        self.log(f"\nSecurity success rate: {success_rate:.1f}%")
        self.log("="*60)
        
        return len(self.security_issues) == 0

def main():
    """Main security test execution"""
    tester = SecurityTester()
    
    try:
        security_clean = tester.run_comprehensive_security_tests()
        summary_clean = tester.print_security_summary()
        
        if security_clean and summary_clean:
            print("\n🎉 All security tests passed! No sensitive information exposure detected.")
            return 0
        else:
            print(f"\n⚠️  Security issues detected. Check the logs above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Security tests interrupted by user")
        tester.print_security_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during security testing: {str(e)}")
        tester.print_security_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())