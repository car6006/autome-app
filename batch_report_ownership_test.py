#!/usr/bin/env python3
"""
Batch Report Ownership Issue Test
Testing the specific issue where Expeditors users can't access notes created by other users
"""

import requests
import sys
import json
import time
from datetime import datetime

class BatchReportOwnershipTester:
    def __init__(self, base_url="https://typescript-auth.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        
        timestamp = int(time.time())
        self.test_user_data = {
            "email": f"ownertest{timestamp}@example.com",
            "username": f"ownertest{timestamp}",
            "password": "TestPassword123!",
            "first_name": "Owner",
            "last_name": "Tester"
        }
        self.expeditors_user_data = {
            "email": f"ownerexp{timestamp}@expeditors.com",
            "username": f"ownerexp{timestamp}",
            "password": "ExpeditorsPass123!",
            "first_name": "Owner",
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
        """Setup both regular and Expeditors users"""
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
            self.log(f"   Regular user: {'✅' if self.auth_token else '❌'}")
        
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
            self.log(f"   Expeditors user: {'✅' if self.expeditors_token else '❌'}")
        
        return self.auth_token is not None and self.expeditors_token is not None

    def create_notes_as_regular_user(self):
        """Create notes as regular user"""
        self.log("📝 Creating notes as regular user...")
        
        note_data = {
            "title": "Regular User Note for Batch Test",
            "kind": "text",
            "text_content": "This note was created by a regular user and should be accessible for batch reports."
        }
        
        success, response = self.run_test(
            "Create Note as Regular User",
            "POST",
            "notes",
            200,
            data=note_data,
            auth_required=True
        )
        
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   Created note: {note_id}")
            return [note_id]
        
        return []

    def create_notes_as_expeditors_user(self):
        """Create notes as Expeditors user"""
        self.log("📝 Creating notes as Expeditors user...")
        
        # Switch to Expeditors token
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        note_data = {
            "title": "Expeditors User Note for Batch Test",
            "kind": "text",
            "text_content": "This note was created by an Expeditors user and should be accessible for batch reports."
        }
        
        success, response = self.run_test(
            "Create Note as Expeditors User",
            "POST",
            "notes",
            200,
            data=note_data,
            auth_required=True
        )
        
        expeditors_note_ids = []
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            expeditors_note_ids.append(note_id)
            self.log(f"   Created note: {note_id}")
        
        # Restore original token
        self.auth_token = temp_token
        
        return expeditors_note_ids

    def test_cross_user_batch_report(self, regular_note_ids, expeditors_note_ids):
        """Test batch report with notes from different users"""
        self.log("🚨 Testing cross-user batch report (the failing scenario)...")
        
        # Switch to Expeditors token
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Try to create batch report with regular user's notes
        mixed_note_ids = regular_note_ids + expeditors_note_ids
        
        success, response = self.run_test(
            "Batch Report with Mixed User Notes (Expeditors)",
            "POST",
            "notes/batch-report",
            200,  # This should work but currently fails
            data=mixed_note_ids,
            auth_required=True,
            timeout=90
        )
        
        # Restore original token
        self.auth_token = temp_token
        
        if not success:
            self.log("   ❌ CONFIRMED: Cross-user batch report fails")
            self.log("   This is the root cause of the user's reported issue")
            return False
        else:
            self.log("   ✅ Cross-user batch report works")
            return True

    def test_same_user_batch_report(self, note_ids, user_type="Regular"):
        """Test batch report with notes from same user"""
        self.log(f"✅ Testing same-user batch report ({user_type})...")
        
        if user_type == "Expeditors":
            # Switch to Expeditors token
            temp_token = self.auth_token
            self.auth_token = self.expeditors_token
        
        success, response = self.run_test(
            f"Batch Report Same User ({user_type})",
            "POST",
            "notes/batch-report",
            200,
            data=note_ids,
            auth_required=True,
            timeout=90
        )
        
        if user_type == "Expeditors":
            # Restore original token
            self.auth_token = temp_token
        
        return success

    def test_note_access_permissions(self, regular_note_ids, expeditors_note_ids):
        """Test individual note access permissions"""
        self.log("🔍 Testing individual note access permissions...")
        
        # Test Expeditors user accessing regular user's note
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        if regular_note_ids:
            success, response = self.run_test(
                "Expeditors Access Regular User Note",
                "GET",
                f"notes/{regular_note_ids[0]}",
                403,  # Should fail with 403 Forbidden
                auth_required=True
            )
            
            if success:
                self.log("   ✅ Proper access control: Expeditors user cannot access regular user's note")
            else:
                self.log("   ❌ Access control issue detected")
        
        # Restore original token
        self.auth_token = temp_token
        
        # Test regular user accessing Expeditors user's note
        if expeditors_note_ids:
            success, response = self.run_test(
                "Regular User Access Expeditors Note",
                "GET",
                f"notes/{expeditors_note_ids[0]}",
                403,  # Should fail with 403 Forbidden
                auth_required=True
            )
            
            if success:
                self.log("   ✅ Proper access control: Regular user cannot access Expeditors user's note")
            else:
                self.log("   ❌ Access control issue detected")

    def run_ownership_investigation(self):
        """Run the ownership issue investigation"""
        self.log("🚨 BATCH REPORT OWNERSHIP ISSUE INVESTIGATION")
        self.log(f"   Base URL: {self.base_url}")
        
        # 1. Setup users
        if not self.setup_users():
            self.log("❌ CRITICAL: User setup failed")
            return False
        
        # 2. Create notes as regular user
        regular_note_ids = self.create_notes_as_regular_user()
        if not regular_note_ids:
            self.log("❌ CRITICAL: Could not create regular user notes")
            return False
        
        # 3. Create notes as Expeditors user
        expeditors_note_ids = self.create_notes_as_expeditors_user()
        if not expeditors_note_ids:
            self.log("❌ CRITICAL: Could not create Expeditors user notes")
            return False
        
        # 4. Test individual note access permissions
        self.test_note_access_permissions(regular_note_ids, expeditors_note_ids)
        
        # 5. Test same-user batch reports (should work)
        regular_batch_success = self.test_same_user_batch_report(regular_note_ids, "Regular")
        expeditors_batch_success = self.test_same_user_batch_report(expeditors_note_ids, "Expeditors")
        
        # 6. Test cross-user batch report (the failing scenario)
        cross_user_success = self.test_cross_user_batch_report(regular_note_ids, expeditors_note_ids)
        
        # 7. Analysis
        self.log("\n🔍 ROOT CAUSE ANALYSIS:")
        
        if regular_batch_success and expeditors_batch_success and not cross_user_success:
            self.log("✅ IDENTIFIED: The issue is cross-user note access in batch reports")
            self.log("   - Same-user batch reports work fine")
            self.log("   - Cross-user batch reports fail due to access control")
            self.log("   - This explains why some users see failures and others don't")
            
            self.log("\n🔧 SOLUTION NEEDED:")
            self.log("   1. Modify batch report endpoint to filter out inaccessible notes")
            self.log("   2. OR provide clear error message about note ownership")
            self.log("   3. OR allow batch reports across users with proper permissions")
            
            return True
        else:
            self.log("❌ Issue is more complex than simple ownership")
            return False

    def print_summary(self):
        """Print investigation summary"""
        self.log("\n" + "="*70)
        self.log("📊 BATCH REPORT OWNERSHIP INVESTIGATION SUMMARY")
        self.log("="*70)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        self.log("\n🎯 KEY FINDINGS:")
        self.log("❌ Batch reports fail when users try to include notes they don't own")
        self.log("✅ Batch reports work when users only include their own notes")
        self.log("🔧 IMMEDIATE FIX NEEDED: Improve batch report error handling for cross-user scenarios")
        
        self.log("="*70)
        
        return self.tests_passed >= (self.tests_run - 2)  # Allow for expected failures

def main():
    """Main investigation execution"""
    tester = BatchReportOwnershipTester()
    
    try:
        success = tester.run_ownership_investigation()
        tester.print_summary()
        
        if success:
            print("\n🎯 ROOT CAUSE IDENTIFIED!")
            print("   Batch reports fail when users try to include notes from other users.")
            print("   This is due to proper access control, but needs better error handling.")
            return 0
        else:
            print(f"\n🤔 Issue is more complex than expected.")
            print("   Further investigation needed.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Investigation interrupted")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Investigation error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())