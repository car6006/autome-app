#!/usr/bin/env python3
"""
Comprehensive Premium Features Test
Tests both multi-file upload and professional report generation with real content
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class ComprehensivePremiumTester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.created_notes = []

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, expected_result=True):
        """Decorator-like function to track test results"""
        self.tests_run += 1
        if expected_result:
            self.tests_passed += 1
            self.log(f"✅ {name}")
        else:
            self.log(f"❌ {name}")
        return expected_result

    def setup_auth(self):
        """Setup authentication"""
        user_data = {
            "email": f"comprehensive_test_{int(time.time())}@example.com",
            "username": f"compuser_{int(time.time())}",
            "password": "CompTest123!",
            "first_name": "Comprehensive",
            "last_name": "Tester"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=user_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                return self.run_test("Authentication Setup", True)
            else:
                return self.run_test(f"Authentication Setup (Status: {response.status_code})", False)
        except Exception as e:
            return self.run_test(f"Authentication Setup (Error: {str(e)})", False)

    def test_openai_api_direct(self):
        """Test OpenAI API directly to verify configuration"""
        try:
            # Get API key from environment (same way the server does)
            import os
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
            
            if not api_key:
                return self.run_test("OpenAI API Key Check - No key found", False)
            
            # Test a simple API call
            headers = {"Authorization": f"Bearer {api_key}"}
            test_data = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Say 'API test successful'"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=test_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return self.run_test(f"OpenAI API Direct Test - Response: {content[:50]}...", True)
            else:
                return self.run_test(f"OpenAI API Direct Test - Status: {response.status_code}", False)
                
        except Exception as e:
            return self.run_test(f"OpenAI API Direct Test - Error: {str(e)}", False)

    def create_image_with_text(self):
        """Create a more realistic image file that might contain text"""
        # Create a simple PNG with some basic structure
        # This is still a minimal PNG but with more realistic dimensions
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.write(png_data)
        temp_file.flush()
        temp_file.close()
        return temp_file.name

    def test_multi_file_upload_workflow(self):
        """Test the complete multi-file upload workflow"""
        self.log("\n📁 TESTING MULTI-FILE UPLOAD WORKFLOW")
        
        # Test 1: Single file upload
        image_file = self.create_image_with_text()
        try:
            with open(image_file, 'rb') as f:
                files = {'file': ('business_meeting_notes.png', f, 'image/png')}
                data = {'title': 'Business Meeting Notes - Page 1'}
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                
                response = requests.post(
                    f"{self.api_url}/upload-file",
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    note_id = result.get('id')
                    if note_id:
                        self.created_notes.append(note_id)
                    self.run_test(f"Single File Upload - Created note {note_id[:8] if note_id else 'None'}...", True)
                    return note_id
                else:
                    self.run_test(f"Single File Upload - Status: {response.status_code}", False)
                    return None
        except Exception as e:
            self.run_test(f"Single File Upload - Error: {str(e)}", False)
            return None
        finally:
            os.unlink(image_file)

    def test_batch_file_upload(self):
        """Test uploading multiple files in sequence (simulating batch upload)"""
        note_ids = []
        
        file_configs = [
            ("Meeting Notes - Page 1", "meeting_p1.png"),
            ("Meeting Notes - Page 2", "meeting_p2.png"),
            ("Project Sketch", "project.png"),
            ("Action Items", "actions.png")
        ]
        
        for title, filename in file_configs:
            image_file = self.create_image_with_text()
            try:
                with open(image_file, 'rb') as f:
                    files = {'file': (filename, f, 'image/png')}
                    data = {'title': title}
                    headers = {'Authorization': f'Bearer {self.auth_token}'}
                    
                    response = requests.post(
                        f"{self.api_url}/upload-file",
                        data=data,
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        note_id = result.get('id')
                        if note_id:
                            note_ids.append(note_id)
                            self.created_notes.append(note_id)
                        self.run_test(f"Batch Upload: {title}", True)
                    else:
                        self.run_test(f"Batch Upload: {title} - Status: {response.status_code}", False)
            except Exception as e:
                self.run_test(f"Batch Upload: {title} - Error: {str(e)}", False)
            finally:
                os.unlink(image_file)
        
        return note_ids

    def manually_add_content_to_note(self, note_id, content):
        """Manually add content to a note for testing report generation"""
        # This simulates what would happen after successful OCR processing
        # In a real scenario, this would be done by the processing pipeline
        
        # We'll use the MongoDB connection to add content directly
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            import os
            
            async def add_content():
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                client = AsyncIOMotorClient(mongo_url)
                db = client[os.environ.get('DB_NAME', 'auto_me_db')]
                
                # Update the note with content
                result = await db["notes"].update_one(
                    {"id": note_id},
                    {
                        "$set": {
                            "artifacts.text": content,
                            "status": "ready"
                        }
                    }
                )
                
                client.close()
                return result.modified_count > 0
            
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(add_content())
            loop.close()
            
            return self.run_test(f"Manually Add Content to Note {note_id[:8]}...", success)
            
        except Exception as e:
            return self.run_test(f"Manually Add Content to Note {note_id[:8]}... - Error: {str(e)}", False)

    def test_professional_report_generation(self):
        """Test professional report generation with actual content"""
        self.log("\n📊 TESTING PROFESSIONAL REPORT GENERATION")
        
        # Create a note with business content
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # Create note
            response = requests.post(
                f"{self.api_url}/notes",
                json={"title": "Q4 Strategy Meeting", "kind": "photo"},
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                return self.run_test(f"Create Note for Report - Status: {response.status_code}", False)
            
            note_id = response.json()['id']
            self.created_notes.append(note_id)
            
            # Add realistic business content
            business_content = """
            Q4 Strategy Meeting - October 2024
            
            Key Discussion Points:
            - Revenue target: $2.5M for Q4 (15% increase from Q3)
            - New product launch delayed to November due to supply chain issues
            - Marketing budget increased by 20% for holiday campaign
            - Need to hire 3 additional sales representatives
            - Customer retention rate improved to 85%
            
            Action Items:
            1. Sarah Johnson - Finalize product launch timeline by Oct 25
            2. Mike Chen - Complete hiring process for sales team by Nov 1
            3. Lisa Rodriguez - Launch holiday marketing campaign by Nov 15
            4. David Kim - Implement customer feedback system by Dec 1
            
            Risks and Mitigation:
            - Supply chain delays: Diversify supplier base
            - Holiday season competition: Increase marketing spend
            - Staff capacity: Prioritize high-impact activities
            
            Next Steps:
            - Weekly progress reviews every Tuesday
            - Budget review meeting scheduled for Nov 5
            - Customer survey launch planned for Nov 10
            """
            
            # Add content to note
            if not self.manually_add_content_to_note(note_id, business_content):
                return self.run_test("Add Business Content to Note", False)
            
            # Wait a moment for the update to propagate
            time.sleep(2)
            
            # Test single note report generation
            response = requests.post(
                f"{self.api_url}/notes/{note_id}/generate-report",
                headers=headers,
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                report = result.get('report', '')
                
                # Check for expected sections
                expected_sections = ['EXECUTIVE SUMMARY', 'KEY INSIGHTS', 'ACTION ITEMS', 'PRIORITIES', 'RECOMMENDATIONS']
                found_sections = [s for s in expected_sections if s.lower() in report.lower()]
                
                success = len(found_sections) >= 3  # At least 3 sections should be present
                self.run_test(f"Professional Report Generation - Found {len(found_sections)}/5 sections", success)
                
                if success:
                    self.log(f"   Report length: {len(report)} characters")
                    self.log(f"   Sections found: {', '.join(found_sections)}")
                
                return note_id if success else None
            else:
                try:
                    error = response.json()
                    self.run_test(f"Professional Report Generation - Error: {error.get('detail', 'Unknown')}", False)
                except:
                    self.run_test(f"Professional Report Generation - Status: {response.status_code}", False)
                return None
                
        except Exception as e:
            self.run_test(f"Professional Report Generation - Exception: {str(e)}", False)
            return None

    def test_batch_report_generation(self):
        """Test batch report generation with multiple notes"""
        self.log("\n📋 TESTING BATCH REPORT GENERATION")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        note_ids = []
        
        # Create multiple notes with different business content
        business_scenarios = [
            ("Sales Team Meeting", """
            Sales Team Meeting - October 2024
            Current Performance: Q3 sales exceeded target by 12%
            Top performers: Alice (150% of quota), Bob (135% of quota)
            Challenges: Lead quality declining, conversion rate down 5%
            Action Items: Implement new lead scoring system, provide additional training
            """),
            ("Product Development Review", """
            Product Development Review - October 2024
            Feature Development: 3 major features completed, 2 in testing
            User Feedback: 4.2/5 average rating, requests for mobile improvements
            Technical Debt: Need to refactor authentication system
            Timeline: Next release scheduled for December 1st
            """),
            ("Customer Success Analysis", """
            Customer Success Analysis - October 2024
            Customer Satisfaction: 87% satisfaction rate (up from 82%)
            Churn Rate: Reduced to 3.2% monthly (target: 3.0%)
            Support Tickets: Average resolution time 4.5 hours
            Expansion Revenue: 25% of customers upgraded plans
            """)
        ]
        
        # Create notes with content
        for title, content in business_scenarios:
            try:
                # Create note
                response = requests.post(
                    f"{self.api_url}/notes",
                    json={"title": title, "kind": "photo"},
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    note_id = response.json()['id']
                    self.created_notes.append(note_id)
                    
                    # Add content
                    if self.manually_add_content_to_note(note_id, content):
                        note_ids.append(note_id)
                        self.run_test(f"Create Note for Batch Report: {title}", True)
                    else:
                        self.run_test(f"Create Note for Batch Report: {title} - Content Add Failed", False)
                else:
                    self.run_test(f"Create Note for Batch Report: {title} - Status: {response.status_code}", False)
                    
            except Exception as e:
                self.run_test(f"Create Note for Batch Report: {title} - Error: {str(e)}", False)
        
        if len(note_ids) < 2:
            return self.run_test("Batch Report Generation - Insufficient notes with content", False)
        
        # Wait for updates to propagate
        time.sleep(3)
        
        # Test batch report generation
        try:
            response = requests.post(
                f"{self.api_url}/notes/batch-report",
                json=note_ids,
                headers=headers,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                report = result.get('report', '')
                
                # Check for expected batch report sections
                expected_sections = ['EXECUTIVE SUMMARY', 'COMPREHENSIVE ANALYSIS', 'STRATEGIC RECOMMENDATIONS', 'ACTION PLAN']
                found_sections = [s for s in expected_sections if s.lower() in report.lower()]
                
                success = len(found_sections) >= 2  # At least 2 sections should be present
                self.run_test(f"Batch Report Generation - Found {len(found_sections)}/4 sections", success)
                
                if success:
                    self.log(f"   Report length: {len(report)} characters")
                    self.log(f"   Source notes: {result.get('note_count', 0)}")
                    self.log(f"   Sections found: {', '.join(found_sections)}")
                
                return success
            else:
                try:
                    error = response.json()
                    self.run_test(f"Batch Report Generation - Error: {error.get('detail', 'Unknown')}", False)
                except:
                    self.run_test(f"Batch Report Generation - Status: {response.status_code}", False)
                return False
                
        except Exception as e:
            self.run_test(f"Batch Report Generation - Exception: {str(e)}", False)
            return False

    def run_comprehensive_tests(self):
        """Run all comprehensive premium feature tests"""
        self.log("🚀 Starting Comprehensive Premium Features Tests")
        self.log(f"   Base URL: {self.base_url}")
        
        # Setup
        if not self.setup_auth():
            return False
        
        # Test OpenAI API configuration
        self.log("\n🔑 TESTING OPENAI API CONFIGURATION")
        self.test_openai_api_direct()
        
        # Test multi-file upload
        self.log("\n📁 TESTING MULTI-FILE UPLOAD FEATURES")
        single_note_id = self.test_multi_file_upload_workflow()
        batch_note_ids = self.test_batch_file_upload()
        
        # Test professional report generation
        report_note_id = self.test_professional_report_generation()
        
        # Test batch report generation
        self.test_batch_report_generation()
        
        # Print final summary
        self.log(f"\n📊 COMPREHENSIVE TEST SUMMARY")
        self.log(f"=" * 50)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated {len(self.created_notes)} test notes")
        
        self.log("=" * 50)
        
        return self.tests_passed >= (self.tests_run * 0.8)  # 80% success rate threshold

def main():
    tester = ComprehensivePremiumTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())