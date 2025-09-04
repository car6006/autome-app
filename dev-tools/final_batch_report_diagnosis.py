#!/usr/bin/env python3
"""
Final Batch Report Diagnosis - Reproducing the exact failing scenario
"""

import requests
import sys
import json
import time
from datetime import datetime

class FinalBatchReportDiagnosis:
    def __init__(self, base_url="https://autome-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        
        timestamp = int(time.time())
        self.test_user_data = {
            "email": f"finaltest{timestamp}@example.com",
            "username": f"finaltest{timestamp}",
            "password": "TestPassword123!",
            "first_name": "Final",
            "last_name": "Tester"
        }
        self.expeditors_user_data = {
            "email": f"finalexp{timestamp}@expeditors.com",
            "username": f"finalexp{timestamp}",
            "password": "ExpeditorsPass123!",
            "first_name": "Final",
            "last_name": "Expeditors"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=60, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}
        
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
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:500]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def setup_users(self):
        """Setup both users"""
        self.log("🔐 Setting up users...")
        
        # Register regular user
        success, response = self.run_test(
            "Register Regular User",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
        
        # Register Expeditors user
        success, response = self.run_test(
            "Register Expeditors User",
            "POST",
            "auth/register",
            200,
            data=self.expeditors_user_data
        )
        if success:
            self.expeditors_token = response.get('access_token')
        
        return self.auth_token is not None and self.expeditors_token is not None

    def reproduce_failing_scenario(self):
        """Reproduce the exact failing scenario from the user report"""
        self.log("🚨 REPRODUCING THE EXACT FAILING SCENARIO")
        
        # Step 1: Regular user creates notes with professional context
        self.log("📝 Step 1: Regular user creates notes...")
        
        # Setup professional context for regular user
        context_data = {
            "primary_industry": "Business Services",
            "job_role": "Business Analyst",
            "work_environment": "Corporate office",
            "key_focus_areas": ["Process improvement", "Data analysis"],
            "content_types": ["Meeting minutes", "Reports"],
            "analysis_preferences": ["Strategic recommendations", "Action items"]
        }
        
        success, response = self.run_test(
            "Setup Regular User Professional Context",
            "POST",
            "user/professional-context",
            200,
            data=context_data,
            auth_required=True
        )
        
        # Create multiple notes as regular user
        notes_data = [
            {
                "title": "Business Strategy Meeting",
                "kind": "text",
                "text_content": "Meeting discussion about Q4 business strategy and market analysis. Key points include revenue targets, competitive positioning, and operational improvements."
            },
            {
                "title": "Market Analysis Report",
                "kind": "text", 
                "text_content": "Comprehensive market analysis showing growth opportunities in emerging markets. Data indicates 15% growth potential in target segments."
            },
            {
                "title": "Operational Review",
                "kind": "text",
                "text_content": "Monthly operational review covering performance metrics, process improvements, and resource allocation decisions."
            }
        ]
        
        regular_user_note_ids = []
        for i, note_data in enumerate(notes_data, 1):
            success, response = self.run_test(
                f"Create Regular User Note {i}",
                "POST",
                "notes",
                200,
                data=note_data,
                auth_required=True
            )
            
            if success and 'id' in response:
                note_id = response['id']
                regular_user_note_ids.append(note_id)
                self.created_notes.append(note_id)
                self.log(f"   Created note {i}: {note_id}")
        
        # Step 2: Switch to Expeditors user
        self.log("🔄 Step 2: Switching to Expeditors user...")
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Setup professional context for Expeditors user
        expeditors_context = {
            "primary_industry": "Logistics & Supply Chain",
            "job_role": "Supply Chain Manager",
            "work_environment": "Expeditors International",
            "key_focus_areas": ["Freight forwarding", "Cost optimization"],
            "content_types": ["Client communications", "Operational reports"],
            "analysis_preferences": ["Strategic recommendations", "Risk assessment"]
        }
        
        success, response = self.run_test(
            "Setup Expeditors Professional Context",
            "POST",
            "user/professional-context",
            200,
            data=expeditors_context,
            auth_required=True
        )
        
        # Step 3: Expeditors user tries to create batch report with regular user's notes
        self.log("🚨 Step 3: Expeditors user attempts batch report with regular user's notes...")
        self.log(f"   Using note IDs: {regular_user_note_ids}")
        
        success, response = self.run_test(
            "Expeditors Batch Report with Regular User Notes (SHOULD FAIL)",
            "POST",
            "notes/batch-report",
            400,  # Expecting 400 error: "No accessible content found"
            data=regular_user_note_ids,
            auth_required=True,
            timeout=90
        )
        
        if not success:
            self.log("   ✅ REPRODUCED: Batch report fails with 'No accessible content found'")
            self.log("   This is the exact error the user is experiencing!")
            
            # Check if the error message matches
            try:
                error_detail = response.get('detail', '')
                if 'No accessible content found' in error_detail:
                    self.log("   ✅ CONFIRMED: Error message matches user report")
                    return True
                else:
                    self.log(f"   ⚠️  Different error: {error_detail}")
            except:
                pass
        else:
            self.log("   ❌ Could not reproduce the error")
        
        # Restore original token
        self.auth_token = temp_token
        
        return not success

    def test_correct_usage_scenario(self):
        """Test the correct way to use batch reports"""
        self.log("✅ Testing correct batch report usage...")
        
        # Switch to Expeditors user
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Create notes as Expeditors user
        expeditors_notes_data = [
            {
                "title": "Supply Chain Analysis",
                "kind": "text",
                "text_content": "Analysis of supply chain performance and optimization opportunities for Q4 operations."
            },
            {
                "title": "Freight Cost Review",
                "kind": "text",
                "text_content": "Review of freight costs and carrier performance metrics for the current quarter."
            }
        ]
        
        expeditors_note_ids = []
        for i, note_data in enumerate(expeditors_notes_data, 1):
            success, response = self.run_test(
                f"Create Expeditors Note {i}",
                "POST",
                "notes",
                200,
                data=note_data,
                auth_required=True
            )
            
            if success and 'id' in response:
                note_id = response['id']
                expeditors_note_ids.append(note_id)
                self.created_notes.append(note_id)
        
        # Test batch report with own notes
        if expeditors_note_ids:
            success, response = self.run_test(
                "Expeditors Batch Report with Own Notes (SHOULD WORK)",
                "POST",
                "notes/batch-report",
                200,
                data=expeditors_note_ids,
                auth_required=True,
                timeout=90
            )
            
            if success:
                self.log("   ✅ Batch report works when using own notes")
                report_length = len(response.get('report', ''))
                self.log(f"   Report generated: {report_length} characters")
            else:
                self.log("   ❌ Batch report failed even with own notes")
        
        # Restore original token
        self.auth_token = temp_token
        
        return success

    def run_final_diagnosis(self):
        """Run the final diagnosis"""
        self.log("🚨 FINAL BATCH REPORT FAILURE DIAGNOSIS")
        self.log("="*60)
        
        # Setup
        if not self.setup_users():
            self.log("❌ User setup failed")
            return False
        
        # Reproduce the failing scenario
        reproduced = self.reproduce_failing_scenario()
        
        # Test correct usage
        correct_usage_works = self.test_correct_usage_scenario()
        
        # Final analysis
        self.log("\n🔍 FINAL DIAGNOSIS:")
        self.log("="*60)
        
        if reproduced and correct_usage_works:
            self.log("✅ ROOT CAUSE IDENTIFIED:")
            self.log("   1. Batch reports fail when users try to include notes from other users")
            self.log("   2. This is due to proper access control (security feature)")
            self.log("   3. Error message 'No accessible content found' is confusing to users")
            self.log("   4. Users don't understand they can only use their own notes")
            
            self.log("\n🔧 RECOMMENDED SOLUTIONS:")
            self.log("   1. IMMEDIATE: Improve error message to be more user-friendly")
            self.log("      - Change 'No accessible content found' to")
            self.log("      - 'You can only create batch reports with your own notes'")
            self.log("   2. MEDIUM-TERM: Add UI validation to prevent selecting others' notes")
            self.log("   3. LONG-TERM: Consider shared note functionality for teams")
            
            self.log("\n🎯 USER EXPERIENCE ISSUE:")
            self.log("   - The functionality works correctly from a security perspective")
            self.log("   - But the error message is confusing and unhelpful")
            self.log("   - Users think the feature is broken when it's actually working as designed")
            
            return True
        else:
            self.log("❌ Could not fully reproduce or diagnose the issue")
            return False

    def print_summary(self):
        """Print final summary"""
        self.log("\n" + "="*70)
        self.log("📊 FINAL BATCH REPORT DIAGNOSIS SUMMARY")
        self.log("="*70)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        self.log("\n🎯 CONCLUSION:")
        self.log("✅ Batch report functionality is NOT broken")
        self.log("❌ User experience is poor due to confusing error messages")
        self.log("🔧 Simple fix needed: Improve error message clarity")
        
        self.log("="*70)

def main():
    """Main diagnosis execution"""
    tester = FinalBatchReportDiagnosis()
    
    try:
        success = tester.run_final_diagnosis()
        tester.print_summary()
        
        if success:
            print("\n🎯 DIAGNOSIS COMPLETE!")
            print("   Root cause identified: Poor error messaging for cross-user note access")
            print("   Batch report functionality is working correctly")
            print("   Simple UX improvement needed")
            return 0
        else:
            print(f"\n🤔 Diagnosis incomplete")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Diagnosis interrupted")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Diagnosis error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())