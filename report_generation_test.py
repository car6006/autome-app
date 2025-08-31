#!/usr/bin/env python3
"""
Professional Report Generation Testing - Critical User Issue
Tests the report generation functionality that users are reporting as failing
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class ReportGenerationTester:
    def __init__(self, base_url="https://typescript-auth.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.created_notes = []
        self.test_user_data = {
            "email": f"report_test_user_{int(time.time())}@example.com",
            "username": f"reportuser{int(time.time())}",  # No underscore for validation
            "password": "ReportTest123!",
            "first_name": "Report",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

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
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def setup_auth(self):
        """Setup authentication with proper error handling"""
        self.log("🔐 Setting up authentication...")
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Registered user ID: {user_data.get('id')}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
            return True
        else:
            self.log("❌ Authentication setup failed - cannot proceed with tests")
            return False

    def create_note_with_content_via_db(self, title, content):
        """Create a note and manually add content to test report generation"""
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Create note
        response = requests.post(
            f"{self.api_url}/notes",
            json={"title": title, "kind": "photo"},
            headers=headers
        )
        
        if response.status_code != 200:
            self.log(f"❌ Failed to create note: {response.status_code}")
            return None
        
        note_data = response.json()
        note_id = note_data['id']
        self.created_notes.append(note_id)
        
        self.log(f"✅ Created note {note_id[:8]}... with title: {title}")
        
        # For testing purposes, we'll try to use the existing notes from the database
        # that might already have content from previous processing
        return note_id

    def get_existing_notes_with_content(self):
        """Get existing notes that might have content"""
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        response = requests.get(f"{self.api_url}/notes?limit=50", headers=headers)
        if response.status_code != 200:
            return []
        
        notes = response.json()
        notes_with_content = []
        
        for note in notes:
            artifacts = note.get('artifacts', {})
            if artifacts.get('transcript') or artifacts.get('text'):
                notes_with_content.append(note)
                self.log(f"Found note with content: {note['id'][:8]}... - {note['title']}")
        
        return notes_with_content

    def test_report_generation_with_existing_content(self):
        """Test report generation using existing notes with content"""
        # Get notes with content
        notes_with_content = self.get_existing_notes_with_content()
        
        if not notes_with_content:
            self.log("❌ No existing notes with content found")
            return False
        
        # Test single note report generation
        test_note = notes_with_content[0]
        note_id = test_note['id']
        
        self.log(f"🔍 Testing report generation for note: {test_note['title']}")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = requests.post(
            f"{self.api_url}/notes/{note_id}/generate-report",
            headers=headers,
            timeout=90
        )
        
        self.tests_run += 1
        if response.status_code == 200:
            self.tests_passed += 1
            data = response.json()
            self.log(f"✅ Single note report generated successfully")
            self.log(f"   Report length: {len(data.get('report', ''))} characters")
            
            # Check for expected sections
            report = data.get('report', '')
            sections = ['EXECUTIVE SUMMARY', 'KEY INSIGHTS', 'ACTION ITEMS', 'PRIORITIES', 'RECOMMENDATIONS']
            found_sections = [s for s in sections if s.lower() in report.lower()]
            self.log(f"   Found sections: {', '.join(found_sections)}")
            
            return True
        else:
            self.log(f"❌ Single note report generation failed: {response.status_code}")
            try:
                error = response.json()
                self.log(f"   Error: {error}")
            except:
                self.log(f"   Response: {response.text[:200]}")
            return False

    def test_batch_report_generation_with_existing_content(self):
        """Test batch report generation using existing notes with content"""
        notes_with_content = self.get_existing_notes_with_content()
        
        if len(notes_with_content) < 2:
            self.log("❌ Need at least 2 notes with content for batch report test")
            return False
        
        # Use first 3 notes (or all if less than 3)
        test_notes = notes_with_content[:3]
        note_ids = [note['id'] for note in test_notes]
        
        self.log(f"🔍 Testing batch report generation with {len(note_ids)} notes")
        for note in test_notes:
            self.log(f"   - {note['title']}")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = requests.post(
            f"{self.api_url}/notes/batch-report",
            json=note_ids,
            headers=headers,
            timeout=120
        )
        
        self.tests_run += 1
        if response.status_code == 200:
            self.tests_passed += 1
            data = response.json()
            self.log(f"✅ Batch report generated successfully")
            self.log(f"   Report length: {len(data.get('report', ''))} characters")
            self.log(f"   Source notes: {data.get('note_count', 0)}")
            
            # Check for expected sections
            report = data.get('report', '')
            sections = ['EXECUTIVE SUMMARY', 'COMPREHENSIVE ANALYSIS', 'STRATEGIC RECOMMENDATIONS', 'ACTION PLAN']
            found_sections = [s for s in sections if s.lower() in report.lower()]
            self.log(f"   Found sections: {', '.join(found_sections)}")
            
            return True
        else:
            self.log(f"❌ Batch report generation failed: {response.status_code}")
            try:
                error = response.json()
                self.log(f"   Error: {error}")
            except:
                self.log(f"   Response: {response.text[:200]}")
            return False

    def test_api_key_configuration(self):
        """Test if OpenAI API key is properly configured"""
        # This is indirect - we'll try to generate a report and see if we get API key errors
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Create a simple note first
        response = requests.post(
            f"{self.api_url}/notes",
            json={"title": "API Key Test", "kind": "photo"},
            headers=headers
        )
        
        if response.status_code != 200:
            return False
        
        note_id = response.json()['id']
        self.created_notes.append(note_id)
        
        # Try to generate report (should fail with "No content available" not API key error)
        response = requests.post(
            f"{self.api_url}/notes/{note_id}/generate-report",
            headers=headers
        )
        
        self.tests_run += 1
        if response.status_code == 400:
            error = response.json()
            if "No content available" in error.get('detail', ''):
                self.tests_passed += 1
                self.log(f"✅ API key appears to be configured (got expected 'no content' error)")
                return True
            elif "AI service not configured" in error.get('detail', ''):
                self.log(f"❌ OpenAI API key not configured")
                return False
        elif response.status_code == 500:
            error = response.json()
            if "AI service not configured" in error.get('detail', ''):
                self.log(f"❌ OpenAI API key not configured")
                return False
        
        self.log(f"⚠️  Unexpected response for API key test: {response.status_code}")
        return False

    def run_tests(self):
        """Run all report generation tests"""
        self.log("🚀 Starting Professional Report Generation Tests")
        
        if not self.setup_auth():
            return False
        
        # Test API key configuration
        self.log("\n🔑 Testing API Key Configuration")
        self.test_api_key_configuration()
        
        # Test with existing content
        self.log("\n📊 Testing Report Generation with Existing Content")
        self.test_report_generation_with_existing_content()
        
        self.log("\n📋 Testing Batch Report Generation with Existing Content")
        self.test_batch_report_generation_with_existing_content()
        
        # Print summary
        self.log(f"\n📊 REPORT GENERATION TEST SUMMARY")
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ReportGenerationTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())