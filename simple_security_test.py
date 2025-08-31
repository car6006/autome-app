#!/usr/bin/env python3
"""
Simple Security Test for AUTO-ME Backend
"""

import requests
import sys
import json
import time
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_security():
    base_url = "https://voice-capture-9.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    tests_run = 0
    tests_passed = 0
    critical_issues = []
    
    log("🔒 AUTO-ME Backend Security Test")
    log(f"   Target: {base_url}")
    
    # 1. Test URL Traversal Protection
    log("\n🔍 Testing URL Traversal Protection...")
    traversal_payloads = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam", 
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "../app/backend/.env",
    ]
    
    for payload in traversal_payloads:
        tests_run += 1
        try:
            response = requests.get(f"{api_url}/notes/{payload}", timeout=10)
            if response.status_code in [400, 404]:
                tests_passed += 1
                log(f"   ✅ Blocked: {payload[:30]}...")
            else:
                content = response.text.lower()
                if any(x in content for x in ["root:x:", "mongo_url", "fastapi"]):
                    critical_issues.append(f"URL Traversal: {payload}")
                    log(f"   ❌ CRITICAL: System file exposed via {payload}")
                else:
                    tests_passed += 1
                    log(f"   ✅ Safe: {payload[:30]}...")
        except Exception as e:
            if "400" in str(e):
                tests_passed += 1
                log(f"   ✅ Blocked by middleware: {payload[:30]}...")
            else:
                log(f"   ⚠️  Error: {str(e)}")
    
    # 2. Test Admin Endpoint Exposure
    log("\n🚨 Testing Admin/Debug Endpoints...")
    admin_endpoints = ["admin", "debug", "test", "config", "logs", "metrics"]
    
    for endpoint in admin_endpoints:
        tests_run += 1
        try:
            response = requests.get(f"{base_url}/{endpoint}", timeout=10)
            if response.status_code == 404:
                tests_passed += 1
                log(f"   ✅ Not exposed: /{endpoint}")
            elif response.status_code == 200:
                content = response.text.lower()
                if any(x in content for x in ["admin panel", "debug mode", "system info"]):
                    critical_issues.append(f"Exposed admin endpoint: /{endpoint}")
                    log(f"   ❌ CRITICAL: Admin endpoint exposed: /{endpoint}")
                else:
                    tests_passed += 1
                    log(f"   ✅ Safe: /{endpoint}")
            else:
                tests_passed += 1
                log(f"   ✅ Protected: /{endpoint} (Status: {response.status_code})")
        except Exception:
            tests_passed += 1
            log(f"   ✅ Not accessible: /{endpoint}")
    
    # 3. Test Authentication Requirements
    log("\n🔐 Testing Authentication...")
    protected_endpoints = [
        "auth/me",
        "user/professional-context", 
        "notes/test/ai-chat"
    ]
    
    for endpoint in protected_endpoints:
        tests_run += 1
        try:
            response = requests.get(f"{api_url}/{endpoint}", timeout=10)
            if response.status_code in [401, 403]:
                tests_passed += 1
                log(f"   ✅ Auth required: {endpoint}")
            else:
                critical_issues.append(f"Auth bypass: {endpoint} (Status: {response.status_code})")
                log(f"   ❌ CRITICAL: Auth bypass: {endpoint}")
        except Exception as e:
            log(f"   ⚠️  Error testing {endpoint}: {str(e)}")
    
    # 4. Test File Access Protection
    log("\n📁 Testing File Access...")
    sensitive_files = [".env", "server.py", "requirements.txt", ".git/config"]
    
    for file_path in sensitive_files:
        tests_run += 1
        try:
            response = requests.get(f"{base_url}/{file_path}", timeout=10)
            if response.status_code in [404, 403]:
                tests_passed += 1
                log(f"   ✅ Protected: {file_path}")
            elif response.status_code == 200:
                content = response.text.lower()
                if any(x in content for x in ["mongo_url", "fastapi", "import ", "[core]"]):
                    critical_issues.append(f"File exposed: {file_path}")
                    log(f"   ❌ CRITICAL: File exposed: {file_path}")
                else:
                    tests_passed += 1
                    log(f"   ✅ Safe: {file_path}")
            else:
                tests_passed += 1
        except Exception:
            tests_passed += 1
            log(f"   ✅ Not accessible: {file_path}")
    
    # 5. Test Error Information Disclosure
    log("\n🔍 Testing Error Disclosure...")
    error_tests = [
        ("GET", "notes/invalid-id-12345"),
        ("POST", "auth/login", {"email": "invalid", "password": "invalid"}),
    ]
    
    for method, endpoint, *data in error_tests:
        tests_run += 1
        try:
            if method == "GET":
                response = requests.get(f"{api_url}/{endpoint}", timeout=10)
            else:
                response = requests.post(f"{api_url}/{endpoint}", json=data[0] if data else {}, timeout=10)
            
            content = response.text.lower()
            if any(x in content for x in ["traceback", "file \"/", "mongo_url", "/app/backend/"]):
                critical_issues.append(f"Info disclosure: {endpoint}")
                log(f"   ❌ CRITICAL: Info disclosure in {endpoint}")
            else:
                tests_passed += 1
                log(f"   ✅ Safe error: {endpoint}")
        except Exception as e:
            log(f"   ⚠️  Error testing {endpoint}: {str(e)}")
    
    # Print Summary
    log("\n" + "="*60)
    log("🔒 SECURITY TEST SUMMARY")
    log("="*60)
    log(f"Tests run: {tests_run}")
    log(f"Tests passed: {tests_passed}")
    log(f"Critical issues: {len(critical_issues)}")
    
    if critical_issues:
        log("\n🚨 CRITICAL SECURITY ISSUES:")
        for i, issue in enumerate(critical_issues, 1):
            log(f"  {i}. {issue}")
    else:
        log("\n✅ NO CRITICAL SECURITY ISSUES FOUND")
    
    success_rate = (tests_passed/tests_run*100) if tests_run > 0 else 0
    log(f"\nSuccess rate: {success_rate:.1f}%")
    log("="*60)
    
    return len(critical_issues) == 0

if __name__ == "__main__":
    try:
        if test_security():
            print("\n🎉 Security test passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Security issues found!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {str(e)}")
        sys.exit(1)