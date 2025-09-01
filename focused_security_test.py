#!/usr/bin/env python3
"""
Focused Security Test - Stack Trace and Sensitive Information Exposure
Tests specifically for the security enhancements mentioned in the review request
"""

import requests
import json
import time
import tempfile
import os

class FocusedSecurityTester:
    def __init__(self, base_url="https://pwa-integration-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.auth_token = None
        self.test_results = []

    def log(self, message):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def setup_auth(self):
        """Setup authentication for tests"""
        user_data = {
            "email": f"security_test_{int(time.time())}@example.com",
            "username": f"sectest_{int(time.time())}",
            "password": "SecurePass123!",
            "first_name": "Security",
            "last_name": "Tester"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=user_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.log(f"✅ Authentication setup successful")
                return True
        except Exception as e:
            self.log(f"❌ Authentication setup failed: {e}")
        return False

    def check_response_security(self, response, test_name):
        """Check response for security issues"""
        issues = []
        response_text = response.text.lower()
        
        # Check for stack traces
        stack_trace_indicators = [
            'traceback (most recent call last)',
            'file "/', 'line ', ' in ',
            'error:', 'exception:',
            '/app/backend/', '/usr/local/',
            '__file__', '__name__',
            'raise ', 'except ',
            '.py", line',
            'internal server error:',
            'unhandled exception:'
        ]
        
        for indicator in stack_trace_indicators:
            if indicator in response_text:
                issues.append(f"Stack trace indicator found: {indicator}")
        
        # Check for sensitive paths
        sensitive_paths = [
            '/app/backend',
            '/usr/local',
            '/opt/',
            'c:\\',
            'mongodb://',
            'postgres://',
            'mysql://'
        ]
        
        for path in sensitive_paths:
            if path in response_text:
                issues.append(f"Sensitive path exposed: {path}")
        
        # Check for API keys
        api_key_patterns = [
            'sk-', 'sg.', 'whisper_api_key', 'openai_api_key',
            'sendgrid_api_key', 'jwt_secret_key', 'bearer '
        ]
        
        for pattern in api_key_patterns:
            if pattern in response_text:
                issues.append(f"API key pattern found: {pattern}")
        
        # Check for database info
        db_patterns = [
            'mongo_url', 'database_url', 'localhost:27017',
            'localhost:5432', 'connection string'
        ]
        
        for pattern in db_patterns:
            if pattern in response_text:
                issues.append(f"Database info exposed: {pattern}")
        
        result = {
            'test_name': test_name,
            'status_code': response.status_code,
            'secure': len(issues) == 0,
            'issues': issues,
            'response_length': len(response.text)
        }
        
        self.test_results.append(result)
        
        if result['secure']:
            self.log(f"✅ {test_name} - No security issues detected")
        else:
            self.log(f"❌ {test_name} - Security issues found:")
            for issue in issues:
                self.log(f"   - {issue}")
        
        return result['secure']

    def test_error_conditions(self):
        """Test various error conditions for stack trace exposure"""
        self.log("\n🔍 Testing Error Conditions for Stack Trace Exposure")
        
        # Test 1: Invalid JSON
        try:
            response = requests.post(f"{self.api_url}/notes", 
                                   data="invalid json", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=30)
            self.check_response_security(response, "Invalid JSON Error")
        except Exception as e:
            self.log(f"❌ Invalid JSON test failed: {e}")
        
        # Test 2: Non-existent note
        try:
            response = requests.get(f"{self.api_url}/notes/non-existent-note-id-12345", timeout=30)
            self.check_response_security(response, "Non-existent Note Error")
        except Exception as e:
            self.log(f"❌ Non-existent note test failed: {e}")
        
        # Test 3: Invalid authentication
        try:
            headers = {'Authorization': 'Bearer invalid-token-format-12345'}
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=30)
            self.check_response_security(response, "Invalid Auth Token Error")
        except Exception as e:
            self.log(f"❌ Invalid auth test failed: {e}")
        
        # Test 4: Malformed file upload
        try:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
                tmp_file.write(b'malformed content')
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('malformed.exe', f, 'application/octet-stream')}
                    response = requests.post(f"{self.api_url}/upload-file", files=files, timeout=30)
                    self.check_response_security(response, "Malformed File Upload Error")
                
                os.unlink(tmp_file.name)
        except Exception as e:
            self.log(f"❌ Malformed file upload test failed: {e}")
        
        # Test 5: Missing required fields
        try:
            response = requests.post(f"{self.api_url}/notes", json={}, timeout=30)
            self.check_response_security(response, "Missing Required Fields Error")
        except Exception as e:
            self.log(f"❌ Missing fields test failed: {e}")

    def test_ai_feature_errors(self):
        """Test AI feature error conditions"""
        self.log("\n🤖 Testing AI Feature Error Conditions")
        
        if not self.auth_token:
            self.log("   Skipping AI tests - no auth token")
            return
        
        # Create a test note first
        try:
            note_data = {"title": "Security Test Note", "kind": "text", "text_content": "Test content"}
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = requests.post(f"{self.api_url}/notes", json=note_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                note_id = response.json().get('id')
                
                # Test AI chat with empty question
                try:
                    response = requests.post(f"{self.api_url}/notes/{note_id}/ai-chat",
                                           json={"question": ""},
                                           headers=headers, timeout=30)
                    self.check_response_security(response, "AI Chat Empty Question Error")
                except Exception as e:
                    self.log(f"❌ AI chat empty question test failed: {e}")
                
                # Test AI chat with missing question
                try:
                    response = requests.post(f"{self.api_url}/notes/{note_id}/ai-chat",
                                           json={},
                                           headers=headers, timeout=30)
                    self.check_response_security(response, "AI Chat Missing Question Error")
                except Exception as e:
                    self.log(f"❌ AI chat missing question test failed: {e}")
                
                # Test report generation for note without content
                try:
                    empty_note_data = {"title": "Empty Note", "kind": "audio"}
                    response = requests.post(f"{self.api_url}/notes", json=empty_note_data, headers=headers, timeout=30)
                    if response.status_code == 200:
                        empty_note_id = response.json().get('id')
                        response = requests.post(f"{self.api_url}/notes/{empty_note_id}/generate-report",
                                               headers=headers, timeout=30)
                        self.check_response_security(response, "Generate Report No Content Error")
                except Exception as e:
                    self.log(f"❌ Generate report test failed: {e}")
                
                # Test export with invalid format
                try:
                    response = requests.get(f"{self.api_url}/notes/{note_id}/ai-conversations/export?format=invalid",
                                          headers=headers, timeout=30)
                    self.check_response_security(response, "Export Invalid Format Error")
                except Exception as e:
                    self.log(f"❌ Export invalid format test failed: {e}")
                
        except Exception as e:
            self.log(f"❌ AI feature tests setup failed: {e}")

    def test_file_processing_errors(self):
        """Test file processing error conditions"""
        self.log("\n📁 Testing File Processing Error Conditions")
        
        if not self.auth_token:
            self.log("   Skipping file processing tests - no auth token")
            return
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Create a test note
        try:
            note_data = {"title": "File Processing Test", "kind": "audio"}
            response = requests.post(f"{self.api_url}/notes", json=note_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                note_id = response.json().get('id')
                
                # Test corrupted audio file
                try:
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                        tmp_file.write(b'corrupted audio data not valid mp3 format')
                        tmp_file.flush()
                        
                        with open(tmp_file.name, 'rb') as f:
                            files = {'file': ('corrupted.mp3', f, 'audio/mp3')}
                            response = requests.post(f"{self.api_url}/notes/{note_id}/upload",
                                                   files=files, headers=headers, timeout=30)
                            self.check_response_security(response, "Corrupted Audio Upload Error")
                        
                        os.unlink(tmp_file.name)
                except Exception as e:
                    self.log(f"❌ Corrupted audio test failed: {e}")
                
                # Test file with malicious filename
                try:
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                        tmp_file.write(b'some audio data')
                        tmp_file.flush()
                        
                        with open(tmp_file.name, 'rb') as f:
                            files = {'file': ('../../etc/passwd.mp3', f, 'audio/mp3')}
                            response = requests.post(f"{self.api_url}/notes/{note_id}/upload",
                                                   files=files, headers=headers, timeout=30)
                            self.check_response_security(response, "Malicious Filename Upload Error")
                        
                        os.unlink(tmp_file.name)
                except Exception as e:
                    self.log(f"❌ Malicious filename test failed: {e}")
                
        except Exception as e:
            self.log(f"❌ File processing tests setup failed: {e}")

    def test_network_diagram_errors(self):
        """Test network diagram feature error conditions"""
        self.log("\n🌐 Testing Network Diagram Error Conditions")
        
        # Test without authentication
        try:
            response = requests.post(f"{self.api_url}/network/process",
                                   json={"input_type": "text_description", "content": "test"},
                                   timeout=30)
            self.check_response_security(response, "Network Diagram Unauthenticated Error")
        except Exception as e:
            self.log(f"❌ Network diagram unauth test failed: {e}")
        
        if not self.auth_token:
            return
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test with non-Expeditors user (should get 403)
        try:
            response = requests.post(f"{self.api_url}/network/process",
                                   json={"input_type": "text_description", "content": "test"},
                                   headers=headers, timeout=30)
            self.check_response_security(response, "Network Diagram Non-Expeditors Error")
        except Exception as e:
            self.log(f"❌ Network diagram non-expeditors test failed: {e}")
        
        # Test with malformed input
        malformed_inputs = [
            {"input_type": "invalid_type", "content": "test"},
            {"input_type": "", "content": "test"},
            {"content": "test"},  # missing input_type
            {"input_type": "text_description"},  # missing content
        ]
        
        for i, malformed_input in enumerate(malformed_inputs):
            try:
                response = requests.post(f"{self.api_url}/network/process",
                                       json=malformed_input,
                                       headers=headers, timeout=30)
                self.check_response_security(response, f"Network Diagram Malformed Input {i+1} Error")
            except Exception as e:
                self.log(f"❌ Network diagram malformed input {i+1} test failed: {e}")

    def test_input_validation_errors(self):
        """Test input validation error conditions"""
        self.log("\n✅ Testing Input Validation Error Conditions")
        
        # Test SQL injection attempts
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--"
        ]
        
        for payload in sql_payloads:
            try:
                response = requests.post(f"{self.api_url}/auth/login",
                                       json={"email": payload, "password": "test"},
                                       timeout=30)
                self.check_response_security(response, f"SQL Injection Test: {payload[:20]}...")
            except Exception as e:
                self.log(f"❌ SQL injection test failed: {e}")
        
        # Test XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            try:
                response = requests.post(f"{self.api_url}/notes",
                                       json={"title": payload, "kind": "text", "text_content": payload},
                                       timeout=30)
                self.check_response_security(response, f"XSS Test: {payload[:20]}...")
            except Exception as e:
                self.log(f"❌ XSS test failed: {e}")

    def run_focused_security_tests(self):
        """Run all focused security tests"""
        self.log("🔒 Starting Focused Security Tests for Stack Trace & Sensitive Info Exposure")
        self.log(f"   Target: {self.base_url}")
        
        # Setup authentication
        self.setup_auth()
        
        # Run all test categories
        self.test_error_conditions()
        self.test_ai_feature_errors()
        self.test_file_processing_errors()
        self.test_network_diagram_errors()
        self.test_input_validation_errors()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("🔒 FOCUSED SECURITY TEST SUMMARY")
        self.log("="*60)
        
        total_tests = len(self.test_results)
        secure_tests = sum(1 for result in self.test_results if result['secure'])
        failed_tests = total_tests - secure_tests
        
        self.log(f"Total security tests: {total_tests}")
        self.log(f"Secure responses: {secure_tests}")
        self.log(f"Insecure responses: {failed_tests}")
        
        if failed_tests > 0:
            self.log(f"\n🚨 SECURITY ISSUES FOUND:")
            for result in self.test_results:
                if not result['secure']:
                    self.log(f"  ❌ {result['test_name']} (Status: {result['status_code']})")
                    for issue in result['issues']:
                        self.log(f"     - {issue}")
        else:
            self.log(f"\n✅ NO SECURITY ISSUES DETECTED")
            self.log(f"   All error responses are properly sanitized")
            self.log(f"   No stack traces or sensitive information exposed")
        
        success_rate = (secure_tests / total_tests * 100) if total_tests > 0 else 0
        self.log(f"\nSecurity success rate: {success_rate:.1f}%")
        self.log("="*60)
        
        return failed_tests == 0

def main():
    tester = FocusedSecurityTester()
    
    try:
        success = tester.run_focused_security_tests()
        
        if success:
            print("\n🎉 All focused security tests passed!")
            print("✅ Stack traces and sensitive information have been successfully removed")
            return 0
        else:
            print("\n⚠️  Security issues detected in error responses")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted")
        return 1
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())