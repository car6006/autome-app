#!/usr/bin/env python3
"""
Test AI Chat and Report Generation with actual content
"""

import requests
import json
import time
import tempfile
import os
from datetime import datetime

class AIFeatureTester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.auth_token = None
        self.test_user_data = {
            "email": f"ai_test_{int(time.time())}@example.com",
            "username": f"aitest_{int(time.time())}",
            "password": "AITest123!",
            "first_name": "AI",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def setup_auth(self):
        """Setup authentication"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=self.test_user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.auth_token = response.json().get('access_token')
                self.log("✅ Authentication setup complete")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Auth error: {str(e)}")
            return False

    def create_note_with_content(self):
        """Create a note and manually add content to test AI features"""
        self.log("📝 Creating note with business content...")
        
        # Create note
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        response = requests.post(
            f"{self.api_url}/notes",
            json={"title": "Business Strategy Meeting", "kind": "audio"},
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            self.log(f"❌ Failed to create note: {response.status_code}")
            return None
        
        note_id = response.json().get('id')
        self.log(f"✅ Created note: {note_id}")
        
        # Manually set content using the database (simulating successful transcription)
        # Since we can't directly access the database, let's try to upload a file and wait
        
        # Create a small audio file with business content in the filename
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            # Write MP3 header and some data
            mp3_header = b'\xff\xfb\x90\x00'
            business_data = (
                b'Our quarterly meeting covered revenue growth of 15 percent, '
                b'market expansion into Asia Pacific region, operational efficiency improvements, '
                b'customer satisfaction scores increased to 92 percent, team development initiatives, '
                b'budget allocation for next quarter, risk management strategies, '
                b'competitive analysis showing strong market position, '
                b'action items include hiring two new engineers, implementing new CRM system, '
                b'launching marketing campaign in Q2, conducting customer feedback survey, '
                b'priorities are revenue growth, customer retention, and operational excellence.'
            ) * 100  # Repeat to make it substantial
            
            tmp_file.write(mp3_header + business_data)
            tmp_file.flush()
            
            try:
                # Upload the file
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('business_strategy_meeting.mp3', f, 'audio/mpeg')}
                    response = requests.post(
                        f"{self.api_url}/notes/{note_id}/upload",
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    self.log("✅ File uploaded successfully")
                    
                    # Wait for processing
                    self.log("⏳ Waiting for transcription processing...")
                    for i in range(12):  # Wait up to 2 minutes
                        time.sleep(10)
                        
                        # Check note status
                        response = requests.get(
                            f"{self.api_url}/notes/{note_id}",
                            headers=headers,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            note_data = response.json()
                            status = note_data.get('status', 'unknown')
                            self.log(f"   Status: {status}")
                            
                            if status == 'ready':
                                artifacts = note_data.get('artifacts', {})
                                transcript = artifacts.get('transcript', '')
                                if transcript:
                                    self.log(f"✅ Transcription ready: {len(transcript)} characters")
                                    return note_id
                                else:
                                    self.log("⚠️  Status is ready but no transcript content")
                            elif status == 'failed':
                                self.log("❌ Processing failed")
                                break
                    
                    self.log("⏰ Timeout waiting for transcription")
                    return note_id  # Return anyway to test with empty content
                else:
                    self.log(f"❌ File upload failed: {response.status_code}")
                    return None
                    
            finally:
                os.unlink(tmp_file.name)

    def test_ai_chat_with_note(self, note_id):
        """Test AI chat functionality"""
        self.log(f"🤖 Testing AI Chat with note {note_id[:8]}...")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # First check if note has content
        response = requests.get(
            f"{self.api_url}/notes/{note_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            note_data = response.json()
            artifacts = note_data.get('artifacts', {})
            transcript = artifacts.get('transcript', '')
            self.log(f"   Note has transcript: {len(transcript)} characters")
            
            if not transcript:
                self.log("⚠️  No transcript content - AI Chat will likely fail")
                # Let's try anyway to see the error
        
        # Test AI Chat questions
        questions = [
            "What are the main topics discussed?",
            "Can you provide a summary of key points?",
            "What action items were mentioned?",
            "What are the business priorities?"
        ]
        
        success_count = 0
        for question in questions:
            try:
                response = requests.post(
                    f"{self.api_url}/notes/{note_id}/ai-chat",
                    json={"question": question},
                    headers=headers,
                    timeout=45
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get('response', '')
                    self.log(f"✅ AI Chat success: {len(ai_response)} chars response")
                    self.log(f"   Question: {question}")
                    self.log(f"   Response preview: {ai_response[:100]}...")
                    success_count += 1
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    self.log(f"❌ AI Chat failed: {response.status_code}")
                    self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    
            except Exception as e:
                self.log(f"❌ AI Chat error: {str(e)}")
        
        return success_count > 0

    def test_report_generation(self, note_id):
        """Test professional report generation"""
        self.log(f"📊 Testing Report Generation with note {note_id[:8]}...")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            response = requests.post(
                f"{self.api_url}/notes/{note_id}/generate-report",
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                report = data.get('report', '')
                self.log(f"✅ Report generated: {len(report)} characters")
                
                # Check for required sections
                sections = ['EXECUTIVE SUMMARY', 'KEY INSIGHTS', 'ACTION ITEMS', 'PRIORITIES']
                found_sections = [s for s in sections if s in report]
                self.log(f"   Sections found: {len(found_sections)}/{len(sections)}")
                
                if report:
                    self.log(f"   Report preview: {report[:200]}...")
                
                return True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                self.log(f"❌ Report generation failed: {response.status_code}")
                self.log(f"   Error: {error_data.get('detail', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log(f"❌ Report generation error: {str(e)}")
            return False

    def run_tests(self):
        """Run all AI feature tests"""
        self.log("🚀 Starting AI Features Test")
        
        if not self.setup_auth():
            return False
        
        # Create note with content
        note_id = self.create_note_with_content()
        if not note_id:
            self.log("❌ Failed to create note with content")
            return False
        
        # Test AI Chat
        ai_chat_success = self.test_ai_chat_with_note(note_id)
        
        # Test Report Generation
        report_success = self.test_report_generation(note_id)
        
        # Summary
        self.log("\n" + "="*50)
        self.log("📊 AI FEATURES TEST SUMMARY")
        self.log("="*50)
        self.log(f"AI Chat: {'✅ PASSED' if ai_chat_success else '❌ FAILED'}")
        self.log(f"Report Generation: {'✅ PASSED' if report_success else '❌ FAILED'}")
        self.log(f"Overall: {'✅ PASSED' if (ai_chat_success and report_success) else '❌ FAILED'}")
        self.log("="*50)
        
        return ai_chat_success and report_success

def main():
    tester = AIFeatureTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())