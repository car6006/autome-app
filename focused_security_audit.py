#!/usr/bin/env python3
"""
AUTO-ME PWA Backend Focused Security Audit
Critical security testing for production readiness
"""

import requests
import sys
import json
import time
from datetime import datetime
from urllib.parse import quote

class FocusedSecurityAuditor:
    def __init__(self, base_url="https://voice-capture-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_issues = []
        self.warnings = []
        self.auth_token = None

    def log(self, message):
        """Log audit messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def test_critical_security_areas(self):
        """Test the most critical security areas"""
        self.log("🔒 FOCUSED SECURITY AUDIT - CRITICAL AREAS")
        
        # 1. URL Traversal Protection
        self._test_url_traversal()
        
        # 2. Admin/Debug Endpoint Exposure
        self._test_admin_endpoints()
        
        # 3. Authentication Bypass
        self._test_auth_bypass()
        
        # 4. File Access Security
        self._test_file_access()
        
        # 5. System File Protection
        self._test_system_files()
        
        # 6. Information Disclosure
        self._test_info_disclosure()

    def _test_url_traversal(self):
        """Test URL traversal protection"""
        self.log("\n🔍 Testing URL Traversal Protection...")
        
        traversal_tests = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc//passwd",
            "../app/backend/.env",
            "../../backend/server.py",
        ]
        
        for payload in traversal_tests:
            self.tests_run += 1
            try:
                # Test in URL path
                response = requests.get(f"{self.api_url}/notes/{payload}", timeout=10)
                
                if response.status_code in [400, 404]:
                    self.tests_passed += 1
                    self.log(f"   ✅ Blocked traversal: {payload[:30]}...")
                else:
                    # Check if system files are exposed
                    if self._check_system_content(response.text):
                        self.critical_issues.append(f"URL Traversal vulnerability: {payload}")
                        self.log(f"   ❌ CRITICAL: System file exposed via {payload}")
                    else:
                        self.tests_passed += 1
                        
            except Exception as e:
                if "400" in str(e) or "Invalid URL" in str(e):
                    self.tests_passed += 1
                    self.log(f"   ✅ Blocked by middleware: {payload[:30]}...")
                else:
                    self.warnings.append(f"Traversal test error: {str(e)}")

    def _test_admin_endpoints(self):
        """Test for exposed admin/debug endpoints"""
        self.log("\n🚨 Testing Admin/Debug Endpoint Exposure...")
        
        admin_endpoints = [
            "admin", "debug", "test", "dev", "config", "status", 
            "info", "logs", "metrics", "health", "swagger", "docs"
        ]
        
        for endpoint in admin_endpoints:
            self.tests_run += 1
            try:
                response = requests.get(f"{self.base_url}/{endpoint}", timeout=10)
                
                if response.status_code == 404:
                    self.tests_passed += 1
                    self.log(f"   ✅ Endpoint not exposed: /{endpoint}")
                elif response.status_code == 200:
                    # Check if it reveals sensitive information
                    if self._check_admin_content(response.text):
                        self.critical_issues.append(f"Exposed admin endpoint: /{endpoint}")
                        self.log(f"   ❌ CRITICAL: Admin endpoint exposed: /{endpoint}")
                    else:
                        self.tests_passed += 1
                        self.log(f"   ✅ Safe endpoint: /{endpoint}")
                else:
                    self.tests_passed += 1
                    self.log(f"   ✅ Protected endpoint: /{endpoint} (Status: {response.status_code})")
                    
            except Exception as e:
                if "404" in str(e):
                    self.tests_passed += 1
                else:
                    self.warnings.append(f"Admin endpoint test error: {str(e)}")

    def _test_auth_bypass(self):
        """Test authentication bypass vulnerabilities"""
        self.log("\n🔐 Testing Authentication Bypass...")
        
        # Create test user first
        self._create_test_user()
        
        protected_endpoints = [
            ("GET", "auth/me"),
            ("POST", "user/professional-context"),
            ("GET", "user/professional-context"),
        ]
        
        for method, endpoint in protected_endpoints:
            self.tests_run += 1
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_url}/{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.api_url}/{endpoint}", json={}, timeout=10)
                
                if response.status_code in [401, 403]:
                    self.tests_passed += 1
                    self.log(f"   ✅ Auth required: {method} {endpoint}")
                else:
                    self.critical_issues.append(f"Auth bypass: {method} {endpoint} (Status: {response.status_code})")
                    self.log(f"   ❌ CRITICAL: Auth bypass: {method} {endpoint}")
                    
            except Exception as e:
                self.warnings.append(f"Auth test error: {str(e)}")

    def _test_file_access(self):
        """Test file access security"""
        self.log("\n📁 Testing File Access Security...")
        
        # Test access to sensitive files
        sensitive_files = [
            ".env",
            "backend/.env", 
            "server.py",
            "requirements.txt",
            "package.json",
            ".git/config",
        ]
        
        for file_path in sensitive_files:
            self.tests_run += 1
            try:
                response = requests.get(f"{self.base_url}/{file_path}", timeout=10)
                
                if response.status_code in [404, 403]:
                    self.tests_passed += 1
                    self.log(f"   ✅ File protected: {file_path}")
                elif response.status_code == 200:
                    if self._check_system_content(response.text):
                        self.critical_issues.append(f"Sensitive file exposed: {file_path}")
                        self.log(f"   ❌ CRITICAL: File exposed: {file_path}")
                    else:
                        self.tests_passed += 1
                        self.log(f"   ✅ File safe: {file_path}")
                else:
                    self.tests_passed += 1
                    
            except Exception as e:
                if "404" in str(e) or "403" in str(e):
                    self.tests_passed += 1
                else:
                    self.warnings.append(f"File access test error: {str(e)}")

    def _test_system_files(self):
        """Test system file protection"""
        self.log("\n🛡️ Testing System File Protection...")
        
        system_paths = [
            "/etc/passwd",
            "/etc/shadow", 
            "/proc/version",
            "/app/backend/.env",
            "/usr/local/lib/python3.9/site-packages/",
        ]
        
        for path in system_paths:
            self.tests_run += 1
            try:
                # Try direct access
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                
                if response.status_code in [404, 403, 400]:
                    self.tests_passed += 1
                    self.log(f"   ✅ System path protected: {path}")
                else:
                    if self._check_system_content(response.text):
                        self.critical_issues.append(f"System file accessible: {path}")
                        self.log(f"   ❌ CRITICAL: System file exposed: {path}")
                    else:
                        self.tests_passed += 1
                        
            except Exception as e:
                if "404" in str(e) or "403" in str(e):
                    self.tests_passed += 1
                else:
                    self.warnings.append(f"System file test error: {str(e)}")

    def _test_info_disclosure(self):
        """Test information disclosure in errors"""
        self.log("\n🔍 Testing Information Disclosure...")
        
        # Test error responses for sensitive info
        error_tests = [
            ("GET", "notes/invalid-id-12345"),
            ("POST", "auth/login", {"email": "invalid", "password": "invalid"}),
            ("POST", "notes", {"invalid": "data"}),
        ]
        
        for method, endpoint, data in error_tests:
            self.tests_run += 1
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_url}/{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.api_url}/{endpoint}", json=data or {}, timeout=10)
                
                if self._check_error_disclosure(response.text):
                    self.tests_passed += 1
                    self.log(f"   ✅ Safe error response: {endpoint}")
                else:
                    self.critical_issues.append(f"Information disclosure: {endpoint}")
                    self.log(f"   ❌ CRITICAL: Info disclosure: {endpoint}")
                    
            except Exception as e:
                self.warnings.append(f"Info disclosure test error: {str(e)}")

    def _check_system_content(self, content):
        """Check if content contains system file information"""
        content_lower = content.lower()
        system_indicators = [
            "root:x:",  # /etc/passwd
            "mongo_url=",  # .env file
            "fastapi",  # server.py
            "import ",  # Python files
            "def ",  # Python functions
            "class ",  # Python classes
            "#!/bin/",  # Shell scripts
            "[core]",  # Git config
            "dependencies",  # package.json
        ]
        
        return any(indicator in content_lower for indicator in system_indicators)

    def _check_admin_content(self, content):
        """Check if content reveals admin/debug information"""
        content_lower = content.lower()
        admin_indicators = [
            "admin panel",
            "debug mode",
            "development mode",
            "system information",
            "server status",
            "configuration",
            "database connection",
            "environment variables",
        ]
        
        return any(indicator in content_lower for indicator in admin_indicators)

    def _check_error_disclosure(self, content):
        """Check if error response discloses sensitive information"""
        content_lower = content.lower()
        disclosure_patterns = [
            "traceback",
            "file \"/",
            "line \\d+ in",
            "mongo_url",
            "internal server error:",
            "unhandled exception:",
            "/app/backend/",
            "fastapi",
            "uvicorn",
        ]
        
        import re
        for pattern in disclosure_patterns:
            if re.search(pattern, content_lower):
                return False
        return True

    def _create_test_user(self):
        """Create test user for authentication tests"""
        if self.auth_token:
            return True
        
        test_user = {
            "email": f"sectest_{int(time.time())}@example.com",
            "username": f"sectest_{int(time.time())}",
            "password": "SecurePass123!",
            "first_name": "Security",
            "last_name": "Test"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=test_user, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                return True
        except Exception as e:
            self.warnings.append(f"Failed to create test user: {str(e)}")
        
        return False

    def run_audit(self):
        """Run the focused security audit"""
        self.log("🔒 Starting Focused Security Audit")
        self.log(f"   Target: {self.base_url}")
        
        self.test_critical_security_areas()
        
        return len(self.critical_issues) == 0

    def print_summary(self):
        """Print audit summary"""
        self.log("\n" + "="*60)
        self.log("🔒 SECURITY AUDIT RESULTS")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Critical issues: {len(self.critical_issues)}")
        self.log(f"Warnings: {len(self.warnings)}")
        
        if self.critical_issues:
            self.log("\n🚨 CRITICAL SECURITY ISSUES:")
            for i, issue in enumerate(self.critical_issues, 1):
                self.log(f"  {i}. {issue}")
        
        if self.warnings:
            self.log("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                self.log(f"  {i}. {warning}")
        
        if not self.critical_issues:
            self.log("\n✅ NO CRITICAL SECURITY ISSUES FOUND")
            self.log("   Backend security appears adequate for production")
        
        success_rate = (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0
        self.log(f"\nSuccess rate: {success_rate:.1f}%")
        self.log("="*60)
        
        return len(self.critical_issues) == 0

def main():
    """Main execution"""
    auditor = FocusedSecurityAuditor()
    
    try:
        audit_passed = auditor.run_audit()
        summary_clean = auditor.print_summary()
        
        if audit_passed and summary_clean:
            print("\n🎉 Security audit passed!")
            return 0
        else:
            print("\n⚠️  Security issues found - review required")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Audit interrupted")
        return 1
    except Exception as e:
        print(f"\n💥 Audit error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())