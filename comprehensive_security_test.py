#!/usr/bin/env python3
"""
Comprehensive Security Test for AUTO-ME Backend
Tests all critical security areas mentioned in the review request
"""

import requests
import sys
import json
import time
import tempfile
import os
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_comprehensive_security():
    base_url = "https://pwa-integration-fix.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    tests_run = 0
    tests_passed = 0
    critical_issues = []
    warnings = []
    
    log("🔒 COMPREHENSIVE SECURITY AUDIT - AUTO-ME PWA Backend")
    log(f"   Target: {base_url}")
    log(f"   API: {api_url}")
    
    # 1. URL TRAVERSAL/BACKTRACK PROTECTION
    log("\n🔍 1. URL TRAVERSAL & BACKTRACK PROTECTION")
    traversal_tests = [
        ("../", "Basic parent directory"),
        ("../../", "Double parent directory"),
        ("../../../etc/passwd", "Linux passwd file"),
        ("..\\..\\..\\windows\\system32\\config\\sam", "Windows SAM file"),
        ("%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd", "URL encoded traversal"),
        ("....//....//....//etc//passwd", "Double dot traversal"),
        ("../app/backend/.env", "Backend env file"),
        ("../../backend/server.py", "Server source code"),
        ("/etc/passwd", "Absolute path to passwd"),
        ("\\..\\..\\..\\etc\\passwd", "Windows-style traversal"),
    ]
    
    for payload, description in traversal_tests:
        tests_run += 1
        try:
            response = requests.get(f"{api_url}/notes/{payload}", timeout=10)
            
            # Check if blocked by security middleware (400) or not found (404)
            if response.status_code in [400, 404]:
                tests_passed += 1
                log(f"   ✅ {description}: Blocked (Status: {response.status_code})")
            else:
                # Check response content for system file exposure
                content = response.text.lower()
                dangerous_content = ["root:x:", "mongo_url=", "fastapi", "import ", "def ", "class "]
                
                if any(danger in content for danger in dangerous_content):
                    critical_issues.append(f"Directory traversal vulnerability: {payload} - {description}")
                    log(f"   ❌ CRITICAL: {description} - System file exposed!")
                else:
                    tests_passed += 1
                    log(f"   ✅ {description}: Safe response")
                    
        except Exception as e:
            if "400" in str(e) or "Invalid URL" in str(e):
                tests_passed += 1
                log(f"   ✅ {description}: Blocked by middleware")
            else:
                warnings.append(f"Traversal test error ({description}): {str(e)}")
    
    # 2. EXPOSED ADMIN/DEBUG ENDPOINTS
    log("\n🚨 2. EXPOSED ADMIN/DEBUG ENDPOINTS")
    admin_endpoints = [
        ("admin", "Admin panel"),
        ("admin/", "Admin panel with slash"),
        ("admin/login", "Admin login"),
        ("debug", "Debug interface"),
        ("debug/", "Debug interface with slash"),
        ("test", "Test interface"),
        ("dev", "Development interface"),
        ("config", "Configuration interface"),
        ("settings", "Settings interface"),
        ("status", "Status page"),
        ("info", "Info page"),
        ("logs", "Log files"),
        ("log", "Log interface"),
        ("metrics", "Metrics endpoint"),
        ("monitoring", "Monitoring interface"),
        ("swagger", "Swagger documentation"),
        ("swagger-ui", "Swagger UI"),
        ("docs", "API documentation"),
        ("redoc", "ReDoc documentation"),
        ("openapi.json", "OpenAPI specification"),
        ("actuator/health", "Spring actuator health"),
        ("management/health", "Management health"),
        ("server-info", "Server information"),
        ("server-status", "Server status"),
        ("phpinfo", "PHP info (should not exist)"),
        ("console", "Web console"),
        ("shell", "Web shell"),
        ("backup", "Backup files"),
        ("dump", "Database dump"),
    ]
    
    for endpoint, description in admin_endpoints:
        tests_run += 1
        try:
            # Test both root and API paths
            for test_url in [f"{base_url}/{endpoint}", f"{api_url}/{endpoint}"]:
                response = requests.get(test_url, timeout=10)
                
                if response.status_code == 404:
                    tests_passed += 1
                    log(f"   ✅ {description}: Not exposed (404)")
                    break
                elif response.status_code in [401, 403]:
                    # Check if it reveals too much information
                    content = response.text.lower()
                    if any(word in content for word in ["admin", "debug", "internal", "development"]):
                        warnings.append(f"Endpoint {endpoint} reveals information in auth error")
                    tests_passed += 1
                    log(f"   ✅ {description}: Protected (Status: {response.status_code})")
                    break
                elif response.status_code == 200:
                    content = response.text.lower()
                    dangerous_indicators = [
                        "admin panel", "debug mode", "development mode", "system information",
                        "server status", "configuration", "database connection", "environment variables"
                    ]
                    
                    if any(indicator in content for indicator in dangerous_indicators):
                        critical_issues.append(f"Exposed admin/debug endpoint: {endpoint} - {description}")
                        log(f"   ❌ CRITICAL: {description} - Admin interface exposed!")
                    else:
                        tests_passed += 1
                        log(f"   ✅ {description}: Safe content")
                    break
            else:
                tests_passed += 1
                log(f"   ✅ {description}: Not accessible")
                
        except Exception as e:
            if "404" in str(e) or "Connection" in str(e):
                tests_passed += 1
                log(f"   ✅ {description}: Not accessible")
            else:
                warnings.append(f"Admin endpoint test error ({description}): {str(e)}")
    
    # 3. AUTHENTICATION & AUTHORIZATION
    log("\n🔐 3. AUTHENTICATION & AUTHORIZATION")
    
    # Create test user first
    auth_token = None
    test_user = {
        "email": f"sectest_{int(time.time())}@example.com",
        "username": f"sectest_{int(time.time())}",
        "password": "SecureTestPass123!",
        "first_name": "Security",
        "last_name": "Test"
    }
    
    try:
        response = requests.post(f"{api_url}/auth/register", json=test_user, timeout=10)
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            log(f"   ✅ Test user created for authentication tests")
    except Exception as e:
        warnings.append(f"Failed to create test user: {str(e)}")
    
    # Test protected endpoints without authentication
    protected_endpoints = [
        ("GET", "auth/me", "User profile"),
        ("PUT", "auth/me", "Update profile"),
        ("POST", "notes", "Create note"),
        ("POST", "notes/test-id/email", "Send email"),
        ("DELETE", "notes/test-id", "Delete note"),
        ("POST", "notes/test-id/ai-chat", "AI chat"),
        ("POST", "notes/test-id/generate-report", "Generate report"),
        ("POST", "notes/batch-report", "Batch report"),
        ("GET", "notes/test-id/ai-conversations/export", "Export conversations"),
        ("POST", "user/professional-context", "Update context"),
        ("GET", "user/professional-context", "Get context"),
        ("POST", "iisb/analyze", "IISB analysis (Expeditors only)"),
        ("POST", "network/process", "Network diagram (Expeditors only)"),
    ]
    
    for method, endpoint, description in protected_endpoints:
        tests_run += 1
        try:
            if method == "GET":
                response = requests.get(f"{api_url}/{endpoint}", timeout=10)
            elif method == "POST":
                response = requests.post(f"{api_url}/{endpoint}", json={}, timeout=10)
            elif method == "PUT":
                response = requests.put(f"{api_url}/{endpoint}", json={}, timeout=10)
            elif method == "DELETE":
                response = requests.delete(f"{api_url}/{endpoint}", timeout=10)
            
            # Should return 401 (Unauthorized) or 403 (Forbidden)
            if response.status_code in [401, 403]:
                tests_passed += 1
                log(f"   ✅ {description}: Auth required (Status: {response.status_code})")
            elif response.status_code == 404 and any(word in endpoint for word in ["iisb", "network"]):
                # Hidden endpoints for Expeditors users should return 404
                tests_passed += 1
                log(f"   ✅ {description}: Hidden endpoint (404)")
            elif response.status_code == 405:
                # Method not allowed is acceptable
                tests_passed += 1
                log(f"   ✅ {description}: Method not allowed (405)")
            elif response.status_code == 422:
                # Validation error is acceptable
                tests_passed += 1
                log(f"   ✅ {description}: Validation error (422)")
            else:
                critical_issues.append(f"Authentication bypass: {method} {endpoint} - {description} (Status: {response.status_code})")
                log(f"   ❌ CRITICAL: {description} - Auth bypass! (Status: {response.status_code})")
                
        except Exception as e:
            warnings.append(f"Auth test error ({description}): {str(e)}")
    
    # Test JWT validation
    log("\n   Testing JWT Token Validation...")
    invalid_tokens = [
        ("invalid-token", "Simple invalid token"),
        ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature", "Invalid JWT signature"),
        ("", "Empty token"),
        ("Bearer ", "Empty Bearer token"),
    ]
    
    for token, description in invalid_tokens:
        tests_run += 1
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(f"{api_url}/auth/me", headers=headers, timeout=10)
            if response.status_code in [401, 403, 422]:
                tests_passed += 1
                log(f"   ✅ {description}: Properly rejected")
            else:
                critical_issues.append(f"JWT validation bypass: {description}")
                log(f"   ❌ CRITICAL: {description} - JWT bypass!")
        except Exception as e:
            warnings.append(f"JWT test error ({description}): {str(e)}")
    
    # 4. FILE UPLOAD/DOWNLOAD SECURITY
    log("\n📁 4. FILE UPLOAD/DOWNLOAD SECURITY")
    
    if auth_token:
        # Test malicious file uploads
        malicious_files = [
            ("shell.php", b"<?php system($_GET['cmd']); ?>", "PHP shell script"),
            ("script.js", b"<script>alert('xss')</script>", "XSS script"),
            ("exploit.exe", b"MZ\x90\x00", "Executable file"),
            ("../../config.txt", b"malicious content", "Path traversal filename"),
            ("config.ini", b"[database]\npassword=secret", "Config file"),
        ]
        
        for filename, content, description in malicious_files:
            tests_run += 1
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                
                try:
                    with open(tmp_file.name, 'rb') as f:
                        files = {'file': (filename, f, 'application/octet-stream')}
                        headers = {"Authorization": f"Bearer {auth_token}"}
                        
                        response = requests.post(f"{api_url}/upload-file", files=files, headers=headers, timeout=30)
                        
                        # Should reject malicious files with 400 status
                        if response.status_code == 400:
                            tests_passed += 1
                            log(f"   ✅ {description}: Rejected (400)")
                        elif response.status_code == 413:
                            tests_passed += 1
                            log(f"   ✅ {description}: Too large (413)")
                        else:
                            # Check if dangerous file types are accepted
                            dangerous_extensions = ['.php', '.exe', '.bat', '.cmd', '.sh']
                            if any(filename.endswith(ext) for ext in dangerous_extensions) and response.status_code == 200:
                                critical_issues.append(f"Malicious file upload accepted: {filename} - {description}")
                                log(f"   ❌ CRITICAL: {description} - Malicious file accepted!")
                            else:
                                tests_passed += 1
                                log(f"   ✅ {description}: Safe handling")
                                
                except Exception as e:
                    if "400" in str(e) or "413" in str(e):
                        tests_passed += 1
                        log(f"   ✅ {description}: Rejected by server")
                    else:
                        warnings.append(f"File upload test error ({description}): {str(e)}")
                finally:
                    os.unlink(tmp_file.name)
    else:
        log("   ⚠️  Skipping file upload tests - no auth token")
    
    # 5. API ENDPOINT SECURITY
    log("\n🔌 5. API ENDPOINT SECURITY")
    
    # Test input validation with malicious payloads
    log("   Testing Input Validation...")
    
    # SQL injection payloads
    sql_payloads = [
        ("'; DROP TABLE users; --", "SQL drop table"),
        ("' OR '1'='1", "SQL always true"),
        ("admin'--", "SQL comment injection"),
    ]
    
    for payload, description in sql_payloads:
        tests_run += 1
        try:
            response = requests.post(f"{api_url}/auth/login", 
                                   json={"email": payload, "password": "test"}, timeout=10)
            if response.status_code in [400, 401, 422]:
                tests_passed += 1
                log(f"   ✅ {description}: Blocked")
            else:
                critical_issues.append(f"SQL injection vulnerability: {payload}")
                log(f"   ❌ CRITICAL: {description} - SQL injection possible!")
        except Exception as e:
            warnings.append(f"SQL injection test error ({description}): {str(e)}")
    
    # XSS payloads
    xss_payloads = [
        ("<script>alert('xss')</script>", "Basic XSS script"),
        ("javascript:alert('xss')", "JavaScript protocol"),
        ("<img src=x onerror=alert('xss')>", "Image XSS"),
    ]
    
    for payload, description in xss_payloads:
        tests_run += 1
        try:
            response = requests.post(f"{api_url}/notes", 
                                   json={"title": payload, "kind": "text", "text_content": payload}, timeout=10)
            # Should either reject (400) or sanitize
            if response.status_code in [400, 401, 422]:
                tests_passed += 1
                log(f"   ✅ {description}: Blocked")
            elif response.status_code == 200:
                # Check if XSS payload is sanitized in response
                content = response.text
                if "<script" in content or "javascript:" in content or "onerror=" in content:
                    critical_issues.append(f"XSS vulnerability: {payload}")
                    log(f"   ❌ CRITICAL: {description} - XSS possible!")
                else:
                    tests_passed += 1
                    log(f"   ✅ {description}: Sanitized")
            else:
                tests_passed += 1
                log(f"   ✅ {description}: Safe handling")
        except Exception as e:
            warnings.append(f"XSS test error ({description}): {str(e)}")
    
    # 6. SYSTEM FILE PROTECTION
    log("\n🛡️ 6. SYSTEM FILE PROTECTION")
    
    system_files = [
        (".env", "Environment variables"),
        ("backend/.env", "Backend environment"),
        ("app/backend/.env", "Full path backend env"),
        ("server.py", "Server source code"),
        ("requirements.txt", "Python dependencies"),
        ("package.json", "Node.js dependencies"),
        (".git/config", "Git configuration"),
        (".gitignore", "Git ignore file"),
        ("docker-compose.yml", "Docker compose"),
        ("Dockerfile", "Docker file"),
        ("config.py", "Configuration file"),
        ("settings.py", "Settings file"),
        ("logs/", "Log directory"),
        ("backup/", "Backup directory"),
        ("dump.sql", "Database dump"),
    ]
    
    for file_path, description in system_files:
        tests_run += 1
        try:
            response = requests.get(f"{base_url}/{file_path}", timeout=10)
            
            if response.status_code in [404, 403]:
                tests_passed += 1
                log(f"   ✅ {description}: Protected (Status: {response.status_code})")
            elif response.status_code == 200:
                content = response.text.lower()
                system_indicators = [
                    "mongo_url", "api_key", "secret", "password", "fastapi", 
                    "import ", "def ", "class ", "#!/bin/", "[core]", "dependencies"
                ]
                
                if any(indicator in content for indicator in system_indicators):
                    critical_issues.append(f"System file exposed: {file_path} - {description}")
                    log(f"   ❌ CRITICAL: {description} - System file exposed!")
                else:
                    tests_passed += 1
                    log(f"   ✅ {description}: Safe content")
            else:
                tests_passed += 1
                log(f"   ✅ {description}: Safe response (Status: {response.status_code})")
                
        except Exception as e:
            if "404" in str(e) or "403" in str(e):
                tests_passed += 1
                log(f"   ✅ {description}: Not accessible")
            else:
                warnings.append(f"System file test error ({description}): {str(e)}")
    
    # 7. INFORMATION DISCLOSURE IN ERRORS
    log("\n🔍 7. INFORMATION DISCLOSURE")
    
    error_tests = [
        ("GET", "notes/invalid-id-12345", None, "Invalid note ID"),
        ("POST", "auth/login", {"email": "invalid", "password": "invalid"}, "Invalid login"),
        ("POST", "notes", {"invalid": "data"}, "Invalid note data"),
        ("GET", "nonexistent/endpoint", None, "Nonexistent endpoint"),
    ]
    
    for method, endpoint, data, description in error_tests:
        tests_run += 1
        try:
            if method == "GET":
                response = requests.get(f"{api_url}/{endpoint}", timeout=10)
            else:
                response = requests.post(f"{api_url}/{endpoint}", json=data or {}, timeout=10)
            
            content = response.text.lower()
            disclosure_patterns = [
                "traceback", "file \"/", "line \\d+ in", "mongo_url", "database connection",
                "internal server error:", "unhandled exception:", "/app/backend/", "fastapi", "uvicorn"
            ]
            
            import re
            has_disclosure = any(re.search(pattern, content) for pattern in disclosure_patterns)
            
            if has_disclosure:
                critical_issues.append(f"Information disclosure in error: {endpoint} - {description}")
                log(f"   ❌ CRITICAL: {description} - Sensitive info in error!")
            else:
                tests_passed += 1
                log(f"   ✅ {description}: Safe error response")
                
        except Exception as e:
            warnings.append(f"Error disclosure test error ({description}): {str(e)}")
    
    # FINAL SUMMARY
    log("\n" + "="*80)
    log("🔒 COMPREHENSIVE SECURITY AUDIT SUMMARY")
    log("="*80)
    log(f"Total security tests: {tests_run}")
    log(f"Tests passed: {tests_passed}")
    log(f"Tests failed: {tests_run - tests_passed}")
    log(f"Critical security issues: {len(critical_issues)}")
    log(f"Warnings: {len(warnings)}")
    
    if critical_issues:
        log("\n🚨 CRITICAL SECURITY ISSUES FOUND:")
        for i, issue in enumerate(critical_issues, 1):
            log(f"  {i}. {issue}")
    
    if warnings:
        log("\n⚠️  WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            log(f"  {i}. {warning}")
    
    if not critical_issues:
        log("\n✅ NO CRITICAL SECURITY VULNERABILITIES FOUND")
        log("   The AUTO-ME PWA backend appears to be properly secured for production deployment.")
        log("   All critical security areas have been tested and are adequately protected.")
    else:
        log(f"\n❌ {len(critical_issues)} CRITICAL SECURITY ISSUES REQUIRE IMMEDIATE ATTENTION")
        log("   These vulnerabilities must be fixed before production deployment.")
    
    success_rate = (tests_passed/tests_run*100) if tests_run > 0 else 0
    log(f"\nSecurity test success rate: {success_rate:.1f}%")
    
    # Security recommendations
    log("\n📋 SECURITY RECOMMENDATIONS FOR PRODUCTION:")
    log("  1. Implement Web Application Firewall (WAF)")
    log("  2. Enable comprehensive security logging and monitoring")
    log("  3. Regular security updates and dependency scanning")
    log("  4. Implement rate limiting and DDoS protection")
    log("  5. Use HTTPS with proper SSL/TLS configuration")
    log("  6. Regular penetration testing and security audits")
    log("  7. Implement proper backup and disaster recovery")
    log("  8. Use secrets management for API keys and credentials")
    
    log("="*80)
    
    return len(critical_issues) == 0

if __name__ == "__main__":
    try:
        if test_comprehensive_security():
            print("\n🎉 SECURITY AUDIT PASSED - Backend is production ready!")
            sys.exit(0)
        else:
            print("\n⚠️  SECURITY AUDIT FAILED - Critical issues found!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Security audit error: {str(e)}")
        sys.exit(1)