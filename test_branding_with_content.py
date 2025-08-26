#!/usr/bin/env python3
"""
Test Expeditors branding with actual note content
"""

import requests
import json
import time
from datetime import datetime

class BrandingContentTester:
    def __init__(self, base_url="https://transcribe-ocr.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.expeditors_token = None
        self.regular_token = None
        self.created_notes = []

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def setup_users(self):
        """Setup test users"""
        # Register Expeditors user
        expeditors_data = {
            "email": f"test_expeditors_{int(time.time())}@expeditors.com",
            "username": f"expeditors_user_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "User"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=expeditors_data)
        if response.status_code == 200:
            self.expeditors_token = response.json().get('access_token')
            self.log(f"✅ Expeditors user registered: {expeditors_data['email']}")
        
        # Register regular user
        regular_data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "username": f"testuser_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=regular_data)
        if response.status_code == 200:
            self.regular_token = response.json().get('access_token')
            self.log(f"✅ Regular user registered: {regular_data['email']}")
        
        return self.expeditors_token and self.regular_token

    def create_note_with_content_simulation(self, title, token, is_expeditors=False):
        """Create a note and simulate content by directly updating the database"""
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # Create note
        response = requests.post(f"{self.api_url}/notes", 
                               json={"title": title, "kind": "audio"}, 
                               headers=headers)
        
        if response.status_code != 200:
            return None
        
        note_id = response.json().get('id')
        self.created_notes.append(note_id)
        self.log(f"   Created note: {note_id}")
        
        # For testing, we'll simulate content by using the MongoDB directly
        # But first, let's try to add content through the API
        
        # Let's check if we can get the note and see its current state
        response = requests.get(f"{self.api_url}/notes/{note_id}", headers=headers)
        if response.status_code == 200:
            note_data = response.json()
            self.log(f"   Note status: {note_data.get('status', 'unknown')}")
            self.log(f"   Note artifacts: {bool(note_data.get('artifacts', {}))}")
        
        return note_id

    def manually_add_content_to_note(self, note_id, token):
        """Manually add content to note using MongoDB connection"""
        try:
            # Import MongoDB client
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            import os
            
            # Get MongoDB connection details
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'auto_me_db')
            
            async def update_note():
                client = AsyncIOMotorClient(mongo_url)
                db = client[db_name]
                
                # Add mock transcript content
                mock_content = """
                This is a business strategy meeting discussing our Q4 supply chain operations. 
                We need to optimize our logistics network and improve delivery times. 
                Key action items include reviewing vendor contracts, implementing new tracking systems, 
                and expanding our warehouse capacity in key markets. 
                The team discussed budget allocations and resource planning for the next quarter.
                """
                
                # Update the note with mock content
                result = await db.notes.update_one(
                    {"id": note_id},
                    {
                        "$set": {
                            "status": "ready",
                            "artifacts.transcript": mock_content.strip(),
                            "ready_at": datetime.utcnow()
                        }
                    }
                )
                
                client.close()
                return result.modified_count > 0
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(update_note())
            loop.close()
            
            if success:
                self.log(f"   ✅ Added mock content to note {note_id[:8]}...")
                return True
            else:
                self.log(f"   ❌ Failed to add content to note {note_id[:8]}...")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error adding content: {str(e)}")
            return False

    def test_expeditors_report_with_content(self):
        """Test Expeditors report generation with actual content"""
        self.log("\n📊 Testing Expeditors Report with Content")
        
        note_id = self.create_note_with_content_simulation(
            "Expeditors Supply Chain Strategy Meeting", 
            self.expeditors_token, 
            is_expeditors=True
        )
        
        if not note_id:
            self.log("❌ Failed to create note")
            return False
        
        # Add content to the note
        if not self.manually_add_content_to_note(note_id, self.expeditors_token):
            self.log("❌ Failed to add content to note")
            return False
        
        # Wait a moment
        time.sleep(2)
        
        # Verify note has content
        headers = {'Authorization': f'Bearer {self.expeditors_token}'}
        response = requests.get(f"{self.api_url}/notes/{note_id}", headers=headers)
        if response.status_code == 200:
            note_data = response.json()
            artifacts = note_data.get('artifacts', {})
            if artifacts.get('transcript'):
                self.log(f"   ✅ Note has transcript content ({len(artifacts['transcript'])} chars)")
            else:
                self.log(f"   ❌ Note still missing content")
                return False
        
        # Now generate the report
        headers = {'Authorization': f'Bearer {self.expeditors_token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}/notes/{note_id}/generate-report", headers=headers)
        
        self.log(f"   Report generation response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            report = data.get('report', '')
            is_expeditors = data.get('is_expeditors', False)
            
            self.log(f"   Report length: {len(report)} characters")
            self.log(f"   Is Expeditors user: {is_expeditors}")
            
            # Check for Expeditors branding
            if 'EXPEDITORS INTERNATIONAL' in report:
                self.log(f"   ✅ EXPEDITORS INTERNATIONAL branding found!")
                
                if 'Professional Business Report' in report:
                    self.log(f"   ✅ Professional Business Report header found!")
                
                # Check for report sections
                sections = ['EXECUTIVE SUMMARY', 'KEY INSIGHTS', 'STRATEGIC RECOMMENDATIONS', 'ACTION ITEMS']
                found_sections = [s for s in sections if s in report]
                self.log(f"   ✅ Report sections found: {len(found_sections)}/{len(sections)}")
                
                # Show a preview of the report
                self.log(f"   Report preview (first 300 chars):")
                self.log(f"   {report[:300]}...")
                
                return True
            else:
                self.log(f"   ❌ Expeditors branding missing!")
                self.log(f"   Report preview: {report[:200]}...")
                return False
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            self.log(f"   ❌ Report generation failed: {error_data.get('detail', 'Unknown error')}")
            return False

    def test_regular_user_report_with_content(self):
        """Test regular user report generation (should not have Expeditors branding)"""
        self.log("\n📊 Testing Regular User Report with Content")
        
        note_id = self.create_note_with_content_simulation(
            "Business Strategy Meeting", 
            self.regular_token, 
            is_expeditors=False
        )
        
        if not note_id:
            self.log("❌ Failed to create note")
            return False
        
        # Add content to the note
        if not self.manually_add_content_to_note(note_id, self.regular_token):
            self.log("❌ Failed to add content to note")
            return False
        
        time.sleep(2)
        
        # Generate the report
        headers = {'Authorization': f'Bearer {self.regular_token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}/notes/{note_id}/generate-report", headers=headers)
        
        self.log(f"   Report generation response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            report = data.get('report', '')
            is_expeditors = data.get('is_expeditors', False)
            
            self.log(f"   Report length: {len(report)} characters")
            self.log(f"   Is Expeditors user: {is_expeditors}")
            
            # Check that regular user does NOT get Expeditors branding
            if 'EXPEDITORS INTERNATIONAL' not in report:
                self.log(f"   ✅ No Expeditors branding for regular user (correct)")
                
                # Check for standard report sections
                sections = ['EXECUTIVE SUMMARY', 'KEY INSIGHTS', 'STRATEGIC RECOMMENDATIONS', 'ACTION ITEMS']
                found_sections = [s for s in sections if s in report]
                self.log(f"   ✅ Report sections found: {len(found_sections)}/{len(sections)}")
                
                return True
            else:
                self.log(f"   ❌ Unexpected Expeditors branding found for regular user!")
                return False
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            self.log(f"   ❌ Report generation failed: {error_data.get('detail', 'Unknown error')}")
            return False

    def run_tests(self):
        """Run all branding tests with content"""
        self.log("🚀 Starting Expeditors Branding Tests with Content")
        
        if not self.setup_users():
            self.log("❌ Failed to setup users")
            return False
        
        results = []
        results.append(self.test_expeditors_report_with_content())
        results.append(self.test_regular_user_report_with_content())
        
        passed = sum(results)
        total = len(results)
        
        self.log(f"\n📊 BRANDING TEST RESULTS WITH CONTENT")
        self.log(f"   Tests passed: {passed}/{total}")
        self.log(f"   Success rate: {(passed/total*100):.1f}%")
        
        if self.created_notes:
            self.log(f"   Created notes: {len(self.created_notes)}")
        
        return passed == total

if __name__ == "__main__":
    tester = BrandingContentTester()
    success = tester.run_tests()
    
    if success:
        print("\n🎉 All branding tests with content passed!")
    else:
        print("\n⚠️  Some branding tests failed.")