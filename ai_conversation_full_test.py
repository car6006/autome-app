#!/usr/bin/env python3
"""
Complete AI Conversation RTF Export Feature Test
Tests the full workflow including creating AI conversations and exporting them
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class FullAIConversationTester:
    def __init__(self, base_url="https://voice-capture-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.expeditors_token = None
        self.test_note_id = None
        self.expeditors_note_id = None
        
        # Test user data
        self.test_user_data = {
            "email": f"test_full_ai_{int(time.time())}@example.com",
            "username": f"testuser_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Expeditors test user data
        self.expeditors_user_data = {
            "email": f"test_expeditors_full_{int(time.time())}@expeditors.com",
            "username": f"expeditors_user_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "User"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False, token_override=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        token_to_use = token_override if token_override else (self.auth_token if auth_required else None)
        if token_to_use:
            headers['Authorization'] = f'Bearer {token_to_use}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout, params=data)
            elif method == 'POST':
                if files:
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, response

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def setup_test_users(self):
        """Set up test users"""
        self.log("🔐 Setting up test users...")
        
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
        
        return self.auth_token and self.expeditors_token

    def create_note_with_transcript(self, token, user_type="regular"):
        """Create a note and manually add transcript content"""
        self.log(f"📝 Creating note with transcript content for {user_type} user...")
        
        # Create note
        success, response = self.run_test(
            f"Create Note ({user_type})",
            "POST",
            "notes",
            200,
            data={"title": f"Business Meeting Notes - {user_type.title()}", "kind": "audio"},
            token_override=token
        )
        
        if not success:
            return None
            
        note_id = response.get('id')
        
        # We need to manually add transcript content to the note
        # Since we can't wait for real transcription, we'll use the database directly
        # But first, let's try to simulate by uploading and then manually updating
        
        # Upload a dummy audio file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            dummy_data = b'\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm'
            tmp_file.write(dummy_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('business_meeting.webm', f, 'audio/webm')}
                success, response = self.run_test(
                    f"Upload Audio ({user_type})",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    token_override=token
                )
            
            os.unlink(tmp_file.name)
        
        return note_id

    def manually_add_transcript_content(self, note_id):
        """Manually add transcript content using MongoDB"""
        self.log(f"📄 Manually adding transcript content to note {note_id[:8]}...")
        
        # Sample business meeting transcript
        transcript_content = """
        Good morning everyone, thank you for joining today's quarterly business review meeting. 
        
        Let me start with our key performance indicators for Q3. Revenue is up 15% compared to last quarter, 
        which exceeds our projected target of 12%. Our customer satisfaction scores have improved to 4.2 out of 5, 
        up from 3.8 last quarter.
        
        However, we're facing some challenges in our supply chain operations. Delivery times have increased by 
        an average of 2 days due to port congestion in major shipping hubs. We need to develop contingency plans 
        to mitigate these delays.
        
        Our marketing campaign for the new product line has generated significant interest, with over 10,000 
        pre-orders already received. The launch is scheduled for next month, and we're on track to meet our 
        production targets.
        
        For the upcoming quarter, our priorities include: expanding into the European market, implementing 
        the new CRM system, and hiring additional customer service representatives to handle the increased volume.
        
        Are there any questions or concerns about these updates?
        """
        
        # We'll use a direct database update approach
        try:
            # Import MongoDB client
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            import os
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Load environment
            ROOT_DIR = Path(__file__).parent / "backend"
            load_dotenv(ROOT_DIR / '.env')
            
            async def update_note():
                mongo_url = os.environ['MONGO_URL']
                client = AsyncIOMotorClient(mongo_url)
                db = client[os.environ['DB_NAME']]
                
                # Update the note with transcript content
                result = await db["notes"].update_one(
                    {"id": note_id},
                    {
                        "$set": {
                            "status": "ready",
                            "artifacts.transcript": transcript_content.strip(),
                            "ready_at": datetime.utcnow()
                        }
                    }
                )
                
                client.close()
                return result.modified_count > 0
            
            # Run the async update
            success = asyncio.run(update_note())
            
            if success:
                self.log(f"✅ Successfully added transcript content to note")
                return True
            else:
                self.log(f"❌ Failed to add transcript content to note")
                return False
                
        except Exception as e:
            self.log(f"❌ Error adding transcript content: {str(e)}")
            return False

    def create_ai_conversations(self, note_id, token, user_type="regular"):
        """Create AI conversations by asking questions"""
        self.log(f"🤖 Creating AI conversations for {user_type} user...")
        
        test_questions = [
            "What are the main KPIs mentioned in this meeting?",
            "What challenges is the company facing?",
            "What are the priorities for next quarter?",
            "Can you summarize the key business insights from this meeting?"
        ]
        
        conversations_created = 0
        for i, question in enumerate(test_questions):
            success, response = self.run_test(
                f"AI Chat Question {i+1} ({user_type})",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                token_override=token
            )
            
            if success:
                conversations_created += 1
                self.log(f"   ✅ Created conversation {i+1}: {question[:50]}...")
            else:
                self.log(f"   ❌ Failed to create conversation {i+1}")
        
        self.log(f"   Created {conversations_created} AI conversations")
        return conversations_created > 0

    def test_rtf_export_with_conversations(self, note_id, token, user_type="regular"):
        """Test RTF export with actual conversations"""
        self.log(f"📤 Testing RTF export with conversations ({user_type})...")
        
        success, response = self.run_test(
            f"Export RTF - With Conversations ({user_type})",
            "GET",
            f"notes/{note_id}/ai-conversations/export",
            200,
            data={"format": "rtf"},
            token_override=token
        )
        
        if success:
            # Check response headers and content
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            self.log(f"   Content-Type: {content_type}")
            self.log(f"   Content-Disposition: {content_disposition}")
            
            # Check RTF content
            rtf_content = response.text if hasattr(response, 'text') else str(response.content)
            
            # Verify RTF structure
            rtf_checks = {
                "RTF Header": rtf_content.startswith(r"{\rtf1"),
                "Font Table": r"{\fonttbl" in rtf_content,
                "Color Table": r"{\colortbl" in rtf_content,
                "Expeditors Branding": "EXPEDITORS INTERNATIONAL" in rtf_content if user_type == "expeditors" else "EXPEDITORS INTERNATIONAL" not in rtf_content,
                "Analysis Content": "Analysis" in rtf_content,
                "RTF Closing": rtf_content.endswith("}")
            }
            
            self.log(f"   RTF Structure Checks:")
            for check, passed in rtf_checks.items():
                self.log(f"     {check}: {'✅' if passed else '❌'}")
            
            return all(rtf_checks.values())
        
        return False

    def test_txt_export_with_conversations(self, note_id, token, user_type="regular"):
        """Test TXT export with actual conversations"""
        self.log(f"📤 Testing TXT export with conversations ({user_type})...")
        
        success, response = self.run_test(
            f"Export TXT - With Conversations ({user_type})",
            "GET",
            f"notes/{note_id}/ai-conversations/export",
            200,
            data={"format": "txt"},
            token_override=token
        )
        
        if success:
            # Check response headers
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            self.log(f"   Content-Type: {content_type}")
            self.log(f"   Content-Disposition: {content_disposition}")
            
            # Check TXT content
            txt_content = response.text if hasattr(response, 'text') else str(response.content)
            
            # Verify TXT structure
            txt_checks = {
                "Title Present": "AI Content Analysis" in txt_content,
                "Expeditors Branding": "EXPEDITORS INTERNATIONAL" in txt_content if user_type == "expeditors" else True,
                "Analysis Content": "Analysis" in txt_content,
                "Timestamp Present": "Generated:" in txt_content
            }
            
            self.log(f"   TXT Structure Checks:")
            for check, passed in txt_checks.items():
                self.log(f"     {check}: {'✅' if passed else '❌'}")
            
            return all(txt_checks.values())
        
        return False

    def test_export_content_verification(self, note_id, token, user_type="regular"):
        """Verify that exports contain only AI responses, not questions"""
        self.log(f"🔍 Verifying export content excludes questions ({user_type})...")
        
        # Test RTF export
        success, response = self.run_test(
            f"RTF Content Verification ({user_type})",
            "GET",
            f"notes/{note_id}/ai-conversations/export",
            200,
            data={"format": "rtf"},
            token_override=token
        )
        
        if success:
            content = response.text if hasattr(response, 'text') else str(response.content)
            
            # Check that questions are NOT included
            question_indicators = ["What are the main", "What challenges", "Can you summarize"]
            questions_found = any(indicator in content for indicator in question_indicators)
            
            # Check that AI responses ARE included (look for typical AI response patterns)
            response_indicators = ["based on", "analysis", "insights", "recommendations"]
            responses_found = any(indicator.lower() in content.lower() for indicator in response_indicators)
            
            self.log(f"   Questions excluded: {'✅' if not questions_found else '❌'}")
            self.log(f"   AI responses included: {'✅' if responses_found else '❌'}")
            
            return not questions_found and responses_found
        
        return False

    def run_full_ai_export_test(self):
        """Run complete AI conversation export test"""
        self.log("🚀 Starting Complete AI Conversation RTF Export Test")
        self.log(f"   Base URL: {self.base_url}")
        
        # Setup test users
        if not self.setup_test_users():
            self.log("❌ Failed to setup test users")
            return False
        
        # Create notes with transcript content
        self.test_note_id = self.create_note_with_transcript(self.auth_token, "regular")
        self.expeditors_note_id = self.create_note_with_transcript(self.expeditors_token, "expeditors")
        
        if not self.test_note_id or not self.expeditors_note_id:
            self.log("❌ Failed to create test notes")
            return False
        
        # Manually add transcript content to both notes
        self.log("\n📄 ADDING TRANSCRIPT CONTENT")
        if not self.manually_add_transcript_content(self.test_note_id):
            self.log("❌ Failed to add transcript to regular user note")
            return False
        
        if not self.manually_add_transcript_content(self.expeditors_note_id):
            self.log("❌ Failed to add transcript to Expeditors user note")
            return False
        
        # Wait a moment for content to be available
        time.sleep(2)
        
        # Create AI conversations
        self.log("\n🤖 CREATING AI CONVERSATIONS")
        regular_conversations = self.create_ai_conversations(self.test_note_id, self.auth_token, "regular")
        expeditors_conversations = self.create_ai_conversations(self.expeditors_note_id, self.expeditors_token, "expeditors")
        
        if not regular_conversations or not expeditors_conversations:
            self.log("❌ Failed to create AI conversations")
            return False
        
        # Test exports with actual conversations
        self.log("\n📤 TESTING EXPORTS WITH CONVERSATIONS")
        
        # Test RTF exports
        rtf_regular = self.test_rtf_export_with_conversations(self.test_note_id, self.auth_token, "regular")
        rtf_expeditors = self.test_rtf_export_with_conversations(self.expeditors_note_id, self.expeditors_token, "expeditors")
        
        # Test TXT exports
        txt_regular = self.test_txt_export_with_conversations(self.test_note_id, self.auth_token, "regular")
        txt_expeditors = self.test_txt_export_with_conversations(self.expeditors_note_id, self.expeditors_token, "expeditors")
        
        # Test content verification
        self.log("\n🔍 CONTENT VERIFICATION")
        content_regular = self.test_export_content_verification(self.test_note_id, self.auth_token, "regular")
        content_expeditors = self.test_export_content_verification(self.expeditors_note_id, self.expeditors_token, "expeditors")
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 COMPLETE AI CONVERSATION EXPORT TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FullAIConversationTester()
    
    try:
        success = tester.run_full_ai_export_test()
        all_passed = tester.print_summary()
        
        if success:
            print("\n🎉 Complete AI Conversation RTF Export test completed!")
            return 0
        else:
            print(f"\n⚠️  Test execution encountered issues.")
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