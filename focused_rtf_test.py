#!/usr/bin/env python3
"""
Focused RTF Export Test using existing notes with AI conversations
Tests the improved professional RTF and TXT export formatting
"""

import requests
import sys
import json
import time
from datetime import datetime
import re

class FocusedRTFTester:
    def __init__(self, base_url="https://autome-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"focused_rtf_test_{int(time.time())}@example.com",
            "username": f"focusedrtf_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Focused",
            "last_name": "RTF Tester"
        }
        self.expeditors_user_data = {
            "email": f"focused_expeditors_{int(time.time())}@expeditors.com",
            "username": f"focusedexp_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "Focused Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json(), response
                except:
                    return True, {"message": "Success but no JSON response"}, response
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}, response

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}, None

    def register_user(self, user_data, user_type="regular"):
        """Register a user and get auth token"""
        success, response, _ = self.run_test(
            f"{user_type.title()} User Registration",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        if success:
            token = response.get('access_token')
            user_info = response.get('user', {})
            self.log(f"   Registered {user_type} user ID: {user_info.get('id')}")
            return token, user_info.get('id')
        return None, None

    def find_notes_with_ai_conversations(self):
        """Find existing notes with AI conversations"""
        success, response, _ = self.run_test(
            "Find Notes with AI Conversations",
            "GET",
            "notes?limit=20",
            200
        )
        
        if not success:
            return []
        
        notes_with_conversations = []
        for note in response:
            artifacts = note.get('artifacts', {})
            if 'ai_conversations' in artifacts and len(artifacts['ai_conversations']) > 0:
                conversations_count = len(artifacts['ai_conversations'])
                self.log(f"   Found note {note['id'][:8]}... with {conversations_count} AI conversations")
                notes_with_conversations.append({
                    'id': note['id'],
                    'title': note['title'],
                    'conversations_count': conversations_count,
                    'user_id': note.get('user_id')
                })
        
        return notes_with_conversations

    def test_rtf_export_professional_formatting(self, note_id, user_type="regular"):
        """Test RTF export for professional formatting improvements"""
        success, response, http_response = self.run_test(
            f"RTF Export Professional Formatting - {user_type.title()} User",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=rtf",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        # Get the RTF content from the response
        rtf_content = http_response.text if http_response else ""
        
        if not rtf_content:
            self.log(f"❌ No RTF content received")
            return False
        
        self.log(f"   RTF content length: {len(rtf_content)} characters")
        
        # Test specific improvements mentioned in the review request
        improvements_check = {
            # Professional RTF Structure
            "RTF Header Structure": rtf_content.startswith(r"{\rtf1\ansi\deff0"),
            "Professional Font Tables": r"{\fonttbl{\f0 Times New Roman;}{\f1 Arial;}{\f2 Calibri;}" in rtf_content,
            "Professional Color Tables": r"{\colortbl;\red0\green0\blue0;\red234\green10\blue42;" in rtf_content,
            
            # Expeditors Branding
            "Expeditors Branding Header": ("EXPEDITORS INTERNATIONAL" in rtf_content) == (user_type == "expeditors"),
            "Professional Logo Placeholder": (r"\cf2 EXPEDITORS INTERNATIONAL" in rtf_content) == (user_type == "expeditors"),
            "Global Logistics Branding": ("Global Logistics & Freight Forwarding" in rtf_content) == (user_type == "expeditors"),
            
            # Clean Professional Structure
            "Professional Report Title": "AI CONTENT ANALYSIS REPORT" in rtf_content,
            "Clean Section Divisions": "─" in rtf_content,  # Professional separator lines
            "Professional Section Headers": "ANALYSIS SECTION" in rtf_content,
            
            # Improved Bullet Point Formatting
            "Professional Bullet Points": r"\bullet\tab" in rtf_content,
            "No Messy Dots": not rtf_content.count("...") > 5,  # Should not have messy dots
            "Clean List Formatting": r"\li360" in rtf_content or r"\li480" in rtf_content,  # Proper indentation
            
            # Professional Typography and Spacing
            "Professional Fonts": all(font in rtf_content for font in [r"\f0", r"\f1", r"\f2"]),
            "Professional Colors": all(color in rtf_content for color in [r"\cf1", r"\cf2", r"\cf3"]),
            "Professional Spacing": r"\par\par" in rtf_content,  # Proper paragraph spacing
            
            # Clean Headers and Structure
            "Clean Header Formatting": r"\fs32\b\cf2" in rtf_content if user_type == "expeditors" else r"\fs28\b\cf1" in rtf_content,
            "Professional Footer": "This document contains confidential" in rtf_content if user_type == "expeditors" else "AI-Generated Content Analysis Report" in rtf_content,
            
            # No Markdown Symbols (Clean formatting)
            "No Markdown Headers": "###" not in rtf_content,
            "No Markdown Bold": "**" not in rtf_content,
            "No Markdown Code": "```" not in rtf_content,
            
            # Proper RTF Structure
            "Proper RTF Closing": rtf_content.endswith("}"),
            "Professional Content Length": len(rtf_content) > 5000,  # Should be substantial
        }
        
        passed_checks = 0
        total_checks = len(improvements_check)
        
        self.log(f"   🔍 PROFESSIONAL RTF FORMATTING VERIFICATION:")
        for check_name, check_result in improvements_check.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        # Check Content-Type and filename
        content_type = http_response.headers.get('Content-Type', '') if http_response else ''
        content_disposition = http_response.headers.get('Content-Disposition', '') if http_response else ''
        
        self.log(f"   Content-Type: {content_type}")
        self.log(f"   Content-Disposition: {content_disposition}")
        
        # Verify descriptive filename generation
        filename_checks = {
            "Correct Content-Type": content_type == "application/rtf",
            "Has Content-Disposition": "attachment" in content_disposition,
            "Descriptive Filename": ("Expeditors_AI_Analysis_" in content_disposition) if user_type == "expeditors" else ("AI_Analysis_" in content_disposition),
            "RTF Extension": ".rtf" in content_disposition
        }
        
        for check_name, check_result in filename_checks.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        total_checks += len(filename_checks)
        
        success_rate = (passed_checks / total_checks) * 100
        self.log(f"   📊 RTF Professional Formatting: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        return success_rate >= 85  # 85% pass rate required for professional formatting

    def test_txt_export_professional_formatting(self, note_id, user_type="regular"):
        """Test TXT export for professional formatting improvements"""
        success, response, http_response = self.run_test(
            f"TXT Export Professional Formatting - {user_type.title()} User",
            "GET",
            f"notes/{note_id}/ai-conversations/export?format=txt",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        # Get the TXT content from the response
        txt_content = http_response.text if http_response else ""
        
        if not txt_content:
            self.log(f"❌ No TXT content received")
            return False
        
        self.log(f"   TXT content length: {len(txt_content)} characters")
        
        # Test specific TXT improvements
        txt_improvements = {
            # Professional Structure
            "Professional Header Lines": "=" * 70 in txt_content or "=" * 50 in txt_content,
            "Expeditors Branding": ("EXPEDITORS INTERNATIONAL" in txt_content) == (user_type == "expeditors"),
            "Professional Report Title": "AI CONTENT ANALYSIS REPORT" in txt_content,
            
            # Clean Headers and Footers
            "Professional Headers": "EXECUTIVE SUMMARY" in txt_content,
            "Clean Section Headers": "ANALYSIS SECTION" in txt_content,
            "Professional Separators": "-" * 20 in txt_content or "-" * 40 in txt_content,
            
            # Improved Formatting
            "Clean Bullet Points": "•" in txt_content,
            "No Markdown Symbols": not any(symbol in txt_content for symbol in ["###", "**", "```"]),
            "Professional Spacing": "\n\n" in txt_content,
            
            # Descriptive Content
            "Document Information": "Document:" in txt_content and "Generated:" in txt_content,
            "Professional Footer": ("EXPEDITORS INTERNATIONAL" in txt_content) if user_type == "expeditors" else ("AI-Generated Content Analysis Report" in txt_content),
            
            # Content Quality
            "Substantial Content": len(txt_content) > 1000,
            "Professional Language": "Analysis Sections:" in txt_content
        }
        
        passed_checks = 0
        total_checks = len(txt_improvements)
        
        self.log(f"   🔍 PROFESSIONAL TXT FORMATTING VERIFICATION:")
        for check_name, check_result in txt_improvements.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        # Check headers
        content_type = http_response.headers.get('Content-Type', '') if http_response else ''
        content_disposition = http_response.headers.get('Content-Disposition', '') if http_response else ''
        
        filename_checks = {
            "Correct Content-Type": content_type == "text/plain",
            "Has Content-Disposition": "attachment" in content_disposition,
            "Descriptive Filename": ("Expeditors_AI_Analysis_" in content_disposition) if user_type == "expeditors" else ("AI_Analysis_" in content_disposition),
            "TXT Extension": ".txt" in content_disposition
        }
        
        for check_name, check_result in filename_checks.items():
            if check_result:
                passed_checks += 1
                self.log(f"   ✅ {check_name}: PASS")
            else:
                self.log(f"   ❌ {check_name}: FAIL")
        
        total_checks += len(filename_checks)
        
        success_rate = (passed_checks / total_checks) * 100
        self.log(f"   📊 TXT Professional Formatting: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        return success_rate >= 85  # 85% pass rate required

    def run_focused_rtf_test(self):
        """Run focused RTF export tests using existing notes"""
        self.log("🚀 Starting Focused RTF Export Tests")
        self.log(f"   Testing improved professional RTF and TXT export formatting")
        self.log(f"   Base URL: {self.base_url}")
        
        # Find notes with AI conversations
        self.log("\n🔍 FINDING NOTES WITH AI CONVERSATIONS")
        notes_with_conversations = self.find_notes_with_ai_conversations()
        
        if not notes_with_conversations:
            self.log("❌ No notes with AI conversations found - cannot test export functionality")
            return False
        
        # Register regular user
        self.log("\n👤 REGULAR USER SETUP")
        self.auth_token, user_id = self.register_user(self.test_user_data, "regular")
        if not self.auth_token:
            self.log("❌ Regular user registration failed - stopping tests")
            return False
        
        # Register Expeditors user
        self.log("\n👑 EXPEDITORS USER SETUP")
        self.expeditors_token, expeditors_user_id = self.register_user(self.expeditors_user_data, "expeditors")
        if not self.expeditors_token:
            self.log("❌ Expeditors user registration failed - continuing with regular user only")
        
        # Test with the first available note (as regular user)
        test_note = notes_with_conversations[0]
        self.log(f"\n📄 TESTING WITH NOTE: {test_note['title']}")
        self.log(f"   Note ID: {test_note['id']}")
        self.log(f"   AI Conversations: {test_note['conversations_count']}")
        
        # === RTF EXPORT TESTS ===
        self.log("\n📋 RTF EXPORT PROFESSIONAL FORMATTING TESTS")
        
        # Test RTF export as regular user
        rtf_regular_success = self.test_rtf_export_professional_formatting(test_note['id'], "regular")
        
        # Test TXT export as regular user
        txt_regular_success = self.test_txt_export_professional_formatting(test_note['id'], "regular")
        
        # === EXPEDITORS USER TESTS ===
        rtf_expeditors_success = True
        txt_expeditors_success = True
        
        if self.expeditors_token:
            self.log("\n👑 EXPEDITORS USER EXPORT TESTS")
            
            # Switch to Expeditors user
            temp_token = self.auth_token
            self.auth_token = self.expeditors_token
            
            # Test RTF export as Expeditors user
            rtf_expeditors_success = self.test_rtf_export_professional_formatting(test_note['id'], "expeditors")
            
            # Test TXT export as Expeditors user
            txt_expeditors_success = self.test_txt_export_professional_formatting(test_note['id'], "expeditors")
            
            # Restore regular user token
            self.auth_token = temp_token
        
        # === ADDITIONAL VERIFICATION TESTS ===
        self.log("\n🔧 ADDITIONAL VERIFICATION TESTS")
        
        # Test error handling
        success_error1, _, _ = self.run_test(
            "Invalid Format Export (Should Fail)",
            "GET",
            f"notes/{test_note['id']}/ai-conversations/export?format=invalid",
            422,
            auth_required=True
        )
        
        success_error2, _, _ = self.run_test(
            "Non-existent Note Export (Should Fail)",
            "GET",
            "notes/invalid-id/ai-conversations/export?format=rtf",
            404,
            auth_required=True
        )
        
        # Calculate overall success
        all_tests_passed = (
            rtf_regular_success and 
            txt_regular_success and 
            rtf_expeditors_success and 
            txt_expeditors_success and
            success_error1 and
            success_error2
        )
        
        return all_tests_passed

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*70)
        self.log("📊 FOCUSED RTF EXPORT TEST SUMMARY")
        self.log("="*70)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        self.log("="*70)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FocusedRTFTester()
    
    try:
        success = tester.run_focused_rtf_test()
        tester.print_summary()
        
        if success:
            print("\n🎉 All focused RTF export tests passed!")
            print("✅ Professional RTF formatting is working correctly")
            print("✅ Professional TXT formatting is working correctly") 
            print("✅ Expeditors branding integration is working")
            print("✅ Descriptive filename generation is working")
            print("✅ Clean, professional structure verified")
            return 0
        else:
            print(f"\n⚠️  Some RTF export tests failed. Check the logs above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())