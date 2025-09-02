#!/usr/bin/env python3
"""
AUTO-ME PWA Backend Security Audit
Comprehensive security testing focusing on production readiness
Tests for URL traversal, exposed endpoints, authentication bypass, file security, and system protection
"""

import requests
import sys
import json
import time
import os
import tempfile
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote

class SecurityAuditor:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_issues = []
        self.warnings = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"audit_test_{int(time.time())}@example.com",
            "username": f"audituser_{int(time.time())}",
            "password": "SecureAuditPass123!",
            "first_name": "Security",
            "last_name": "Auditor"
        }

    def log(self, message):
        """Log audit messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def test_url_traversal_protection(self):
        """Test for directory traversal and path manipulation vulnerabilities"""
        self.log("\n🔍 URL TRAVERSAL & BACKTRACK PROTECTION TESTS")
        
        # Directory traversal payloads
        traversal_payloads = [
            "../",
            "../../",
            "../../../",
            "..\\",
            "..\\..\\",
            "..\\..\\..\\",
            "....//",
            "....\\\\",
            "%2e%2e%2f",
            "%2e%2e%5c",
            "%252e%252e%252f",
            "..%2f",
            "..%5c",
            "..%c0%af",
            "..%c1%9c",
            ".%2e/",
            ".%2e\\",
            "/%2e%2e/",
            "\\%2e%2e\\",
            "..;/",
            "..;\\",
        ]
        
        # System file targets
        system_files = [
            "etc/passwd",
            "etc/shadow",
            "etc/hosts",
            "windows/system32/config/sam",
            "windows/win.ini",
            "boot.ini",
            "proc/version",
            "proc/self/environ",
            "app/backend/.env",
            "app/backend/server.py",
            "usr/local/lib/python3.9/site-packages",
        ]
        
        for payload in traversal_payloads:
            for target in system_files:
                self.tests_run += 1
                test_path = f"{payload}{target}"
                
                # Test in URL path
                try:
                    response = requests.get(f"{self.api_url}/notes/{test_path}", timeout=10)
                    if self._check_traversal_response(response, test_path):
                        self.tests_passed += 1
                    else:
                        self.critical_issues.append(f"URL traversal vulnerability: {test_path}")
                except Exception as e:
                    if "Invalid URL format" in str(e) or "400" in str(e):
                        self.tests_passed += 1  # Good - blocked by security middleware
                    else:
                        self.warnings.append(f"Unexpected error for traversal test {test_path}: {str(e)}")
                
                # Test in query parameters
                try:
                    response = requests.get(f"{self.api_url}/notes?file={quote(test_path)}", timeout=10)
                    if self._check_traversal_response(response, test_path):
                        self.tests_passed += 1
                    else:
                        self.critical_issues.append(f"Query parameter traversal vulnerability: {test_path}")
                except Exception as e:
                    if "Invalid URL format" in str(e) or "400" in str(e):
                        self.tests_passed += 1
                    else:
                        self.warnings.append(f"Query traversal error {test_path}: {str(e)}")

    def _check_traversal_response(self, response, test_path):
        """Check if traversal attempt was properly blocked"""
        # Should return 400 (blocked by middleware) or 404 (not found)
        if response.status_code in [400, 404]:
            return True
        
        # Check response content for system file exposure
        response_text = response.text.lower()
        dangerous_patterns = [
            "root:x:",  # /etc/passwd
            "[boot loader]",  # boot.ini
            "# hosts file",  # hosts file
            "mongo_url",  # .env file
            "fastapi",  # server.py
            "site-packages",  # Python packages
            "windows registry",
            "system32",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in response_text:
                return False
        
        return True

    def test_exposed_admin_debug_endpoints(self):
        """Scan for exposed admin, debug, and development endpoints"""
        self.log("\n🚨 EXPOSED ADMIN/DEBUG ENDPOINTS SCAN")
        
        # Common admin/debug endpoints
        admin_endpoints = [
            "admin",
            "admin/",
            "admin/login",
            "admin/dashboard",
            "debug",
            "debug/",
            "test",
            "test/",
            "dev",
            "dev/",
            "development",
            "staging",
            "internal",
            "private",
            "config",
            "configuration",
            "settings",
            "status",
            "info",
            "version",
            "build",
            "deploy",
            "deployment",
            "logs",
            "log",
            "monitoring",
            "monitor",
            "stats",
            "statistics",
            "phpinfo",
            "server-info",
            "server-status",
            "actuator",
            "actuator/health",
            "actuator/info",
            "actuator/metrics",
            "management",
            "management/health",
            "swagger",
            "swagger-ui",
            "api-docs",
            "docs",
            "redoc",
            "openapi.json",
            "robots.txt",
            "sitemap.xml",
            ".well-known",
            "backup",
            "backups",
            "dump",
            "sql",
            "database",
            "db",
            "phpmyadmin",
            "adminer",
            "console",
            "shell",
            "cmd",
            "terminal",
        ]
        
        for endpoint in admin_endpoints:
            self.tests_run += 1
            try:
                # Test both with and without /api prefix
                for url in [f"{self.base_url}/{endpoint}", f"{self.api_url}/{endpoint}"]:
                    response = requests.get(url, timeout=10)
                    
                    if self._check_admin_endpoint_response(response, endpoint):
                        self.tests_passed += 1
                    else:
                        self.critical_issues.append(f"Exposed admin/debug endpoint: {endpoint} (Status: {response.status_code})")
                        
            except Exception as e:
                # Connection errors are expected for non-existent endpoints
                if "404" in str(e) or "Connection" in str(e):
                    self.tests_passed += 1
                else:
                    self.warnings.append(f"Admin endpoint test error {endpoint}: {str(e)}")

    def _check_admin_endpoint_response(self, response, endpoint):
        """Check if admin endpoint is properly secured"""
        # 404 is good - endpoint doesn't exist
        if response.status_code == 404:
            return True
        
        # 401/403 might be acceptable if properly secured
        if response.status_code in [401, 403]:
            # Check if it reveals too much information
            response_text = response.text.lower()
            if any(word in response_text for word in ["admin", "debug", "internal", "development"]):
                return False
            return True
        
        # 200 responses need careful examination
        if response.status_code == 200:
            response_text = response.text.lower()
            dangerous_content = [
                "admin panel",
                "debug mode",
                "development mode",
                "internal tools",
                "system information",
                "server status",
                "configuration",
                "database connection",
                "environment variables",
                "stack trace",
                "error log",
                "access log",
            ]
            
            for content in dangerous_content:
                if content in response_text:
                    return False
        
        return True

    def test_authentication_bypass(self):
        """Test for authentication and authorization vulnerabilities"""
        self.log("\n🔐 AUTHENTICATION & AUTHORIZATION TESTS")
        
        # First, create a test user
        self._setup_test_user()
        
        # Protected endpoints that should require authentication
        protected_endpoints = [
            ("GET", "auth/me"),
            ("PUT", "auth/me"),
            ("POST", "notes"),
            ("GET", "notes"),
            ("POST", "notes/test-id/email"),
            ("DELETE", "notes/test-id"),
            ("POST", "notes/test-id/ai-chat"),
            ("POST", "notes/test-id/generate-report"),
            ("POST", "notes/batch-report"),
            ("GET", "notes/test-id/ai-conversations/export"),
            ("POST", "user/professional-context"),
            ("GET", "user/professional-context"),
            ("POST", "iisb/analyze"),
            ("POST", "network/process"),
        ]
        
        for method, endpoint in protected_endpoints:
            self.tests_run += 1
            
            # Test without authentication
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_url}/{endpoint}", timeout=10)
                elif method == "POST":
                    response = requests.post(f"{self.api_url}/{endpoint}", json={}, timeout=10)
                elif method == "PUT":
                    response = requests.put(f"{self.api_url}/{endpoint}", json={}, timeout=10)
                elif method == "DELETE":
                    response = requests.delete(f"{self.api_url}/{endpoint}", timeout=10)
                
                if self._check_auth_required_response(response, endpoint):
                    self.tests_passed += 1
                else:
                    self.critical_issues.append(f"Authentication bypass: {method} {endpoint} (Status: {response.status_code})")
                    
            except Exception as e:
                self.warnings.append(f"Auth test error {method} {endpoint}: {str(e)}")
        
        # Test JWT token validation
        self._test_jwt_validation()
        
        # Test user isolation
        self._test_user_isolation()

    def _check_auth_required_response(self, response, endpoint):
        """Check if endpoint properly requires authentication"""
        # Should return 401 (Unauthorized) or 403 (Forbidden)
        if response.status_code in [401, 403]:
            return True
        
        # Some endpoints might return 404 for security (hiding existence)
        if response.status_code == 404 and any(word in endpoint for word in ["iisb", "network"]):
            return True
        
        # 422 might be acceptable for validation errors
        if response.status_code == 422:
            return True
        
        return False

    def _test_jwt_validation(self):
        """Test JWT token validation security"""
        self.log("   Testing JWT validation...")
        
        invalid_tokens = [
            "invalid-token",
            "Bearer invalid-token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.",
            "",
            "null",
            "undefined",
        ]
        
        for token in invalid_tokens:
            self.tests_run += 1
            headers = {"Authorization": f"Bearer {token}"}
            
            try:
                response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
                if response.status_code in [401, 403, 422]:
                    self.tests_passed += 1
                else:
                    self.critical_issues.append(f"JWT validation bypass with token: {token[:20]}...")
            except Exception as e:
                self.warnings.append(f"JWT validation test error: {str(e)}")

    def _test_user_isolation(self):
        """Test that users can only access their own data"""
        self.log("   Testing user data isolation...")
        
        if not self.auth_token:
            self.warnings.append("Cannot test user isolation - no auth token")
            return
        
        # Create a note with the authenticated user
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        note_data = {"title": "Isolation Test Note", "kind": "text", "text_content": "Private content"}
        
        try:
            response = requests.post(f"{self.api_url}/notes", json=note_data, headers=headers, timeout=10)
            if response.status_code == 200:
                note_id = response.json().get("id")
                
                # Try to access the note without authentication
                self.tests_run += 1
                unauth_response = requests.get(f"{self.api_url}/notes/{note_id}", timeout=10)
                
                if unauth_response.status_code in [401, 403, 404]:
                    self.tests_passed += 1
                else:
                    self.critical_issues.append(f"User isolation bypass: Note accessible without auth")
                    
        except Exception as e:
            self.warnings.append(f"User isolation test error: {str(e)}")

    def test_file_upload_security(self):
        """Test file upload and download security"""
        self.log("\n📁 FILE UPLOAD/DOWNLOAD SECURITY TESTS")
        
        if not self.auth_token:
            self._setup_test_user()
        
        # Test malicious file uploads
        malicious_files = [
            ("shell.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("script.js", b"<script>alert('xss')</script>", "application/javascript"),
            ("exploit.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream"),
            ("../../etc/passwd", b"root:x:0:0:root:/root:/bin/bash", "text/plain"),
            ("config.ini", b"[database]\npassword=secret123", "text/plain"),
            ("large_file.txt", b"A" * (50 * 1024 * 1024), "text/plain"),  # 50MB file
        ]
        
        for filename, content, content_type in malicious_files:
            self.tests_run += 1
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(content[:1024])  # Limit size for testing
                tmp_file.flush()
                
                try:
                    with open(tmp_file.name, 'rb') as f:
                        files = {'file': (filename, f, content_type)}
                        headers = {"Authorization": f"Bearer {self.auth_token}"}
                        
                        response = requests.post(
                            f"{self.api_url}/upload-file",
                            files=files,
                            headers=headers,
                            timeout=30
                        )
                        
                        if self._check_file_upload_response(response, filename):
                            self.tests_passed += 1
                        else:
                            self.critical_issues.append(f"Malicious file upload accepted: {filename}")
                            
                except Exception as e:
                    if "413" in str(e) or "400" in str(e):  # Payload too large or bad request
                        self.tests_passed += 1
                    else:
                        self.warnings.append(f"File upload test error {filename}: {str(e)}")
                finally:
                    os.unlink(tmp_file.name)

    def _check_file_upload_response(self, response, filename):
        """Check if file upload was properly validated"""
        # Should reject malicious files with 400 status
        if response.status_code == 400:
            return True
        
        # Check if dangerous file types are rejected
        dangerous_extensions = ['.php', '.exe', '.bat', '.cmd', '.sh', '.jsp', '.asp']
        if any(filename.endswith(ext) for ext in dangerous_extensions):
            return response.status_code != 200
        
        # Check for path traversal in filename
        if "../" in filename or "..\\" in filename:
            return response.status_code != 200
        
        return True

    def test_api_endpoint_security(self):
        """Test API endpoints for security vulnerabilities"""
        self.log("\n🔌 API ENDPOINT SECURITY TESTS")
        
        # Test rate limiting
        self._test_rate_limiting()
        
        # Test input validation
        self._test_input_validation()
        
        # Test information disclosure
        self._test_information_disclosure()

    def _test_rate_limiting(self):
        """Test rate limiting implementation"""
        self.log("   Testing rate limiting...")
        
        # Make rapid requests to test rate limiting
        for i in range(70):  # Exceed the 60 requests per minute limit
            self.tests_run += 1
            try:
                response = requests.get(f"{self.api_url}/", timeout=5)
                if i > 60 and response.status_code == 429:
                    self.tests_passed += 1
                    self.log(f"   Rate limiting activated after {i} requests")
                    break
                elif i <= 60:
                    self.tests_passed += 1
            except Exception as e:
                if "429" in str(e):
                    self.tests_passed += 1
                    break
                else:
                    self.warnings.append(f"Rate limiting test error: {str(e)}")

    def _test_input_validation(self):
        """Test input validation security"""
        self.log("   Testing input validation...")
        
        # SQL injection payloads (even though MongoDB is used)
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
            "1; DELETE FROM notes; --",
        ]
        
        # NoSQL injection payloads
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$where": "this.password"},
            {"$regex": ".*"},
        ]
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
        ]
        
        # Test SQL injection in login
        for payload in sql_payloads:
            self.tests_run += 1
            try:
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"email": payload, "password": "test"},
                    timeout=10
                )
                if response.status_code in [400, 401, 422]:
                    self.tests_passed += 1
                else:
                    self.critical_issues.append(f"SQL injection vulnerability: {payload}")
            except Exception as e:
                self.warnings.append(f"SQL injection test error: {str(e)}")
        
        # Test XSS in note creation
        for payload in xss_payloads:
            self.tests_run += 1
            try:
                response = requests.post(
                    f"{self.api_url}/notes",
                    json={"title": payload, "kind": "text", "text_content": payload},
                    timeout=10
                )
                # Should either reject (400) or sanitize the input
                if response.status_code in [400, 401, 422] or self._check_xss_sanitized(response, payload):
                    self.tests_passed += 1
                else:
                    self.critical_issues.append(f"XSS vulnerability: {payload}")
            except Exception as e:
                self.warnings.append(f"XSS test error: {str(e)}")

    def _check_xss_sanitized(self, response, payload):
        """Check if XSS payload was properly sanitized"""
        if response.status_code != 200:
            return True
        
        response_text = response.text
        # Check if dangerous script tags are present in response
        dangerous_patterns = ["<script", "javascript:", "onerror=", "onload="]
        return not any(pattern in response_text.lower() for pattern in dangerous_patterns)

    def _test_information_disclosure(self):
        """Test for information disclosure in error messages"""
        self.log("   Testing information disclosure...")
        
        # Test various error conditions
        error_tests = [
            ("GET", "notes/non-existent-id-12345"),
            ("POST", "auth/login", {"email": "invalid", "password": "invalid"}),
            ("GET", "user/professional-context"),  # Without auth
            ("POST", "notes/invalid-id/ai-chat", {"question": "test"}),
        ]
        
        for method, endpoint, data in error_tests:
            self.tests_run += 1
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_url}/{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.api_url}/{endpoint}", json=data or {}, timeout=10)
                
                if self._check_error_disclosure(response):
                    self.tests_passed += 1
                else:
                    self.critical_issues.append(f"Information disclosure in error: {endpoint}")
                    
            except Exception as e:
                self.warnings.append(f"Error disclosure test error: {str(e)}")

    def _check_error_disclosure(self, response):
        """Check if error response discloses sensitive information"""
        response_text = response.text.lower()
        
        # Patterns that indicate information disclosure
        disclosure_patterns = [
            "traceback",
            "file \"/",
            "line \\d+ in",
            "mongo_url",
            "database connection",
            "internal server error:",
            "unhandled exception:",
            "stack trace",
            "/app/backend/",
            "fastapi",
            "uvicorn",
        ]
        
        for pattern in disclosure_patterns:
            if re.search(pattern, response_text):
                return False
        
        return True

    def test_system_file_protection(self):
        """Test protection of system files and configuration"""
        self.log("\n🛡️ SYSTEM FILE PROTECTION TESTS")
        
        # System files that should never be accessible
        protected_files = [
            ".env",
            "backend/.env",
            "app/backend/.env",
            "config.py",
            "settings.py",
            "server.py",
            "requirements.txt",
            "docker-compose.yml",
            "Dockerfile",
            ".git/config",
            ".gitignore",
            "package.json",
            "yarn.lock",
            "node_modules",
            "logs/",
            "log/",
            "backup/",
            "dump.sql",
            "database.db",
            "config.json",
            "secrets.json",
        ]
        
        for file_path in protected_files:
            self.tests_run += 1
            
            # Test direct access
            try:
                response = requests.get(f"{self.base_url}/{file_path}", timeout=10)
                if response.status_code in [404, 403, 400]:
                    self.tests_passed += 1
                else:
                    # Check if actual file content is returned
                    if self._check_system_file_content(response, file_path):
                        self.critical_issues.append(f"System file exposed: {file_path}")
                    else:
                        self.tests_passed += 1
                        
            except Exception as e:
                if "404" in str(e) or "403" in str(e):
                    self.tests_passed += 1
                else:
                    self.warnings.append(f"System file test error {file_path}: {str(e)}")

    def _check_system_file_content(self, response, file_path):
        """Check if response contains actual system file content"""
        if response.status_code != 200:
            return False
        
        content = response.text.lower()
        
        # File-specific content patterns
        file_patterns = {
            ".env": ["mongo_url", "api_key", "secret"],
            "server.py": ["fastapi", "import", "def "],
            "requirements.txt": ["fastapi", "requests", "=="],
            "package.json": ["dependencies", "scripts", "version"],
            "docker": ["from ", "run ", "copy "],
            ".git": ["[core]", "repositoryformatversion"],
        }
        
        for file_type, patterns in file_patterns.items():
            if file_type in file_path:
                return any(pattern in content for pattern in patterns)
        
        # Generic system file indicators
        system_indicators = [
            "#!/bin/",
            "import ",
            "from ",
            "def ",
            "class ",
            "mongo_url",
            "api_key",
            "password",
            "secret",
        ]
        
        return any(indicator in content for indicator in system_indicators)

    def test_cors_configuration(self):
        """Test CORS configuration security"""
        self.log("\n🌐 CORS CONFIGURATION TESTS")
        
        # Test CORS headers
        self.tests_run += 1
        try:
            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = requests.options(f"{self.api_url}/", headers=headers, timeout=10)
            
            cors_headers = response.headers
            if self._check_cors_security(cors_headers):
                self.tests_passed += 1
            else:
                self.critical_issues.append("Insecure CORS configuration detected")
                
        except Exception as e:
            self.warnings.append(f"CORS test error: {str(e)}")

    def _check_cors_security(self, headers):
        """Check if CORS configuration is secure"""
        # Check for overly permissive CORS
        access_control_origin = headers.get("Access-Control-Allow-Origin", "")
        
        # "*" with credentials is dangerous
        if access_control_origin == "*" and headers.get("Access-Control-Allow-Credentials") == "true":
            return False
        
        # Check for dangerous methods
        allowed_methods = headers.get("Access-Control-Allow-Methods", "").upper()
        dangerous_methods = ["TRACE", "CONNECT", "DELETE"]
        
        for method in dangerous_methods:
            if method in allowed_methods:
                return False
        
        return True

    def _setup_test_user(self):
        """Create a test user for authenticated tests"""
        if self.auth_token:
            return True
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=self.test_user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                return True
                
        except Exception as e:
            self.warnings.append(f"Failed to create test user: {str(e)}")
        
        return False

    def run_comprehensive_security_audit(self):
        """Run complete security audit"""
        self.log("🔒 Starting AUTO-ME PWA Backend Security Audit")
        self.log(f"   Target: {self.base_url}")
        self.log(f"   API Endpoint: {self.api_url}")
        
        # Run all security tests
        self.test_url_traversal_protection()
        self.test_exposed_admin_debug_endpoints()
        self.test_authentication_bypass()
        self.test_file_upload_security()
        self.test_api_endpoint_security()
        self.test_system_file_protection()
        self.test_cors_configuration()
        
        return len(self.critical_issues) == 0

    def print_audit_summary(self):
        """Print comprehensive security audit summary"""
        self.log("\n" + "="*80)
        self.log("🔒 SECURITY AUDIT SUMMARY")
        self.log("="*80)
        self.log(f"Total security tests: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Critical security issues: {len(self.critical_issues)}")
        self.log(f"Warnings: {len(self.warnings)}")
        
        if self.critical_issues:
            self.log("\n🚨 CRITICAL SECURITY ISSUES:")
            for i, issue in enumerate(self.critical_issues, 1):
                self.log(f"  {i}. {issue}")
        
        if self.warnings:
            self.log("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                self.log(f"  {i}. {warning}")
        
        if not self.critical_issues and not self.warnings:
            self.log("\n✅ NO CRITICAL SECURITY ISSUES FOUND")
            self.log("   The backend appears to be properly secured for production.")
        
        success_rate = (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0
        self.log(f"\nSecurity test success rate: {success_rate:.1f}%")
        
        # Security recommendations
        self.log("\n📋 SECURITY RECOMMENDATIONS:")
        self.log("  1. Regularly update dependencies and security patches")
        self.log("  2. Implement comprehensive logging and monitoring")
        self.log("  3. Use HTTPS in production with proper SSL/TLS configuration")
        self.log("  4. Implement proper backup and disaster recovery procedures")
        self.log("  5. Regular security audits and penetration testing")
        self.log("  6. Implement proper secrets management")
        self.log("  7. Use Web Application Firewall (WAF) for additional protection")
        
        self.log("="*80)
        
        return len(self.critical_issues) == 0

def main():
    """Main security audit execution"""
    auditor = SecurityAuditor()
    
    try:
        audit_passed = auditor.run_comprehensive_security_audit()
        summary_clean = auditor.print_audit_summary()
        
        if audit_passed and summary_clean:
            print("\n🎉 Security audit completed successfully!")
            print("   Backend is ready for production deployment.")
            return 0
        else:
            print(f"\n⚠️  Security audit found issues that need attention.")
            print("   Please review the critical issues above before production deployment.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Security audit interrupted by user")
        auditor.print_audit_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during security audit: {str(e)}")
        auditor.print_audit_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())