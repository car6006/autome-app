#!/usr/bin/env python3
"""
Backend Testing Script for AUTO-ME Batch Report AI Functionality
Focus: Testing the "Failed to load notes" error when clicking "Ask AI" on batch reports
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://auto-me-debugger.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BatchReportAITester:
    def __init__(self):
        self.session = requests.Session()
        self.user_token = None
        self.test_notes = []
        self.batch_report_data = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def register_test_user(self):
        """Register a test user for authentication"""
        try:
            test_email = f"batch_test_{int(time.time())}@example.com"
            user_data = {
                "email": test_email,
                "password": "TestPassword123",
                "username": "BatchTestUser",
                "profile": {
                    "first_name": "Batch",
                    "last_name": "Tester"
                }
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.user_token}'})
                self.log(f"✅ Test user registered: {test_email}")
                return True
            else:
                self.log(f"❌ Failed to register user: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}", "ERROR")
            return False
    
    def create_test_notes(self):
        """Create multiple test notes for batch report generation"""
        try:
            notes_data = [
                {
                    "title": "Meeting Notes - Project Alpha",
                    "kind": "text",
                    "text_content": "Project Alpha meeting discussion. Key points: Budget approval needed for Q2, team expansion planned, client feedback positive. Action items: Schedule follow-up with finance team, prepare presentation for stakeholders, review timeline for deliverables."
                },
                {
                    "title": "Strategy Session - Marketing Campaign",
                    "kind": "text", 
                    "text_content": "Marketing campaign strategy session. Discussed target demographics, budget allocation, and timeline. Key decisions: Focus on digital channels, increase social media presence, partner with influencers. Next steps: Create content calendar, finalize budget, launch pilot campaign."
                },
                {
                    "title": "Client Feedback Review",
                    "kind": "text",
                    "text_content": "Client feedback review meeting. Overall satisfaction high, some concerns about delivery timeline. Positive feedback on quality and communication. Areas for improvement: Faster response times, more frequent updates, clearer documentation. Action plan: Implement weekly check-ins, improve project tracking."
                }
            ]
            
            created_notes = []
            for note_data in notes_data:
                response = self.session.post(f"{API_BASE}/notes", json=note_data)
                
                if response.status_code == 200:
                    note_info = response.json()
                    created_notes.append(note_info['id'])
                    self.log(f"✅ Created note: {note_data['title']} (ID: {note_info['id']})")
                else:
                    self.log(f"❌ Failed to create note: {response.status_code} - {response.text}", "ERROR")
                    return False
            
            self.test_notes = created_notes
            self.log(f"✅ Created {len(created_notes)} test notes for batch processing")
            return True
            
        except Exception as e:
            self.log(f"❌ Note creation error: {str(e)}", "ERROR")
            return False
    
    def test_batch_report_generation(self):
        """Test batch report generation functionality"""
        try:
            self.log("🔄 Testing batch report generation...")
            
            batch_request = {
                "note_ids": self.test_notes,
                "title": "Test Batch Report - AI Functionality",
                "format": "professional"
            }
            
            response = self.session.post(f"{API_BASE}/notes/batch-report", json=batch_request)
            
            if response.status_code == 200:
                self.batch_report_data = response.json()
                self.log("✅ Batch report generated successfully")
                self.log(f"   Report title: {self.batch_report_data.get('title', 'N/A')}")
                self.log(f"   Report length: {len(self.batch_report_data.get('report', ''))} characters")
                self.log(f"   Source notes: {self.batch_report_data.get('note_count', 0)} notes")
                
                # Log source notes for verification
                source_notes = self.batch_report_data.get('source_notes', [])
                if source_notes:
                    self.log(f"   Source note titles: {', '.join(source_notes)}")
                
                return True
            else:
                self.log(f"❌ Batch report generation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Batch report generation error: {str(e)}", "ERROR")
            return False
    
    def test_virtual_note_ai_chat_issue(self):
        """Test the core issue: AI chat with virtual batch note IDs"""
        try:
            self.log("🔄 Testing virtual note AI chat (reproducing the bug)...")
            
            # Simulate what the frontend does - create a virtual note ID
            virtual_note_id = f"batch-{int(time.time() * 1000)}"
            
            ai_question = {
                "question": "Can you provide a summary of the key points from this batch report?"
            }
            
            # This should fail because the virtual note doesn't exist in the database
            response = self.session.post(f"{API_BASE}/notes/{virtual_note_id}/ai-chat", json=ai_question)
            
            if response.status_code == 404:
                self.log("✅ BUG REPRODUCED: Virtual note AI chat returns 404 'Note not found'")
                self.log(f"   Virtual note ID: {virtual_note_id}")
                self.log(f"   Response: {response.json()}")
                return True
            else:
                self.log(f"❌ Unexpected response for virtual note: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Virtual note AI chat test error: {str(e)}", "ERROR")
            return False
    
    def test_real_note_ai_chat(self):
        """Test AI chat with a real note to verify the endpoint works"""
        try:
            self.log("🔄 Testing AI chat with real note...")
            
            if not self.test_notes:
                self.log("❌ No test notes available for AI chat test", "ERROR")
                return False
            
            real_note_id = self.test_notes[0]
            ai_question = {
                "question": "What are the main action items mentioned in this note?"
            }
            
            response = self.session.post(f"{API_BASE}/notes/{real_note_id}/ai-chat", json=ai_question)
            
            if response.status_code == 200:
                ai_response = response.json()
                self.log("✅ AI chat with real note works correctly")
                self.log(f"   Note ID: {real_note_id}")
                self.log(f"   AI response length: {len(ai_response.get('response', ''))} characters")
                self.log(f"   Question: {ai_question['question']}")
                return True
            else:
                self.log(f"❌ AI chat with real note failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Real note AI chat test error: {str(e)}", "ERROR")
            return False
    
    def test_note_loading_after_batch_generation(self):
        """Test if notes can be loaded individually after batch generation"""
        try:
            self.log("🔄 Testing individual note loading after batch generation...")
            
            success_count = 0
            for note_id in self.test_notes:
                response = self.session.get(f"{API_BASE}/notes/{note_id}")
                
                if response.status_code == 200:
                    note_data = response.json()
                    success_count += 1
                    self.log(f"✅ Note loaded successfully: {note_data.get('title', 'N/A')}")
                else:
                    self.log(f"❌ Failed to load note {note_id}: {response.status_code} - {response.text}", "ERROR")
            
            if success_count == len(self.test_notes):
                self.log(f"✅ All {success_count} notes loaded successfully after batch generation")
                return True
            else:
                self.log(f"❌ Only {success_count}/{len(self.test_notes)} notes loaded successfully", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Note loading test error: {str(e)}", "ERROR")
            return False
    
    def test_batch_content_structure(self):
        """Test if batch report content is compatible with AI processing"""
        try:
            self.log("🔄 Testing batch report content structure...")
            
            if not self.batch_report_data:
                self.log("❌ No batch report data available", "ERROR")
                return False
            
            # Check if batch report has the expected structure
            report_content = self.batch_report_data.get('report') or self.batch_report_data.get('content')
            
            if not report_content:
                self.log("❌ Batch report missing content/report field", "ERROR")
                return False
            
            # Verify content length and structure
            content_length = len(report_content)
            has_source_notes = 'source_notes' in self.batch_report_data
            note_count = self.batch_report_data.get('note_count', 0)
            
            self.log(f"✅ Batch report content structure verified:")
            self.log(f"   Content length: {content_length} characters")
            self.log(f"   Has source notes: {has_source_notes}")
            self.log(f"   Note count: {note_count}")
            
            # Check if content contains expected sections
            expected_sections = ['EXECUTIVE SUMMARY', 'KEY INSIGHTS', 'ACTION ITEMS']
            found_sections = [section for section in expected_sections if section in report_content.upper()]
            
            self.log(f"   Found sections: {', '.join(found_sections) if found_sections else 'None'}")
            
            return content_length > 100 and note_count > 0
            
        except Exception as e:
            self.log(f"❌ Batch content structure test error: {str(e)}", "ERROR")
            return False
    
    def test_comprehensive_batch_report(self):
        """Test comprehensive batch report generation"""
        try:
            self.log("🔄 Testing comprehensive batch report generation...")
            
            batch_request = {
                "note_ids": self.test_notes,
                "title": "Comprehensive Test Batch Report",
                "format": "ai"
            }
            
            response = self.session.post(f"{API_BASE}/notes/comprehensive-batch-report", json=batch_request)
            
            if response.status_code == 200:
                comprehensive_data = response.json()
                self.log("✅ Comprehensive batch report generated successfully")
                self.log(f"   Report title: {comprehensive_data.get('title', 'N/A')}")
                
                content = comprehensive_data.get('content') or comprehensive_data.get('report', '')
                self.log(f"   Content length: {len(content)} characters")
                
                return True
            else:
                self.log(f"❌ Comprehensive batch report failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Comprehensive batch report test error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up test notes"""
        try:
            self.log("🔄 Cleaning up test data...")
            
            deleted_count = 0
            for note_id in self.test_notes:
                response = self.session.delete(f"{API_BASE}/notes/{note_id}")
                if response.status_code == 200:
                    deleted_count += 1
            
            self.log(f"✅ Cleaned up {deleted_count}/{len(self.test_notes)} test notes")
            
        except Exception as e:
            self.log(f"❌ Cleanup error: {str(e)}", "ERROR")
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting comprehensive batch report AI functionality testing...")
        self.log("="*80)
        
        test_results = {}
        
        # Test 1: User Registration
        test_results['user_registration'] = self.register_test_user()
        
        if not test_results['user_registration']:
            self.log("❌ Cannot proceed without authentication", "ERROR")
            return test_results
        
        # Test 2: Create Test Notes
        test_results['note_creation'] = self.create_test_notes()
        
        if not test_results['note_creation']:
            self.log("❌ Cannot proceed without test notes", "ERROR")
            return test_results
        
        # Test 3: Batch Report Generation
        test_results['batch_report_generation'] = self.test_batch_report_generation()
        
        # Test 4: Virtual Note AI Chat Issue (Core Bug)
        test_results['virtual_note_ai_chat_bug'] = self.test_virtual_note_ai_chat_issue()
        
        # Test 5: Real Note AI Chat (Verification)
        test_results['real_note_ai_chat'] = self.test_real_note_ai_chat()
        
        # Test 6: Note Loading After Batch
        test_results['note_loading_after_batch'] = self.test_note_loading_after_batch_generation()
        
        # Test 7: Batch Content Structure
        test_results['batch_content_structure'] = self.test_batch_content_structure()
        
        # Test 8: Comprehensive Batch Report
        test_results['comprehensive_batch_report'] = self.test_comprehensive_batch_report()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.log("="*80)
        self.log("📊 TEST RESULTS SUMMARY:")
        self.log("="*80)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status}: {test_name.replace('_', ' ').title()}")
        
        self.log("="*80)
        self.log(f"📈 OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        # Specific findings about the bug
        if test_results.get('virtual_note_ai_chat_bug'):
            self.log("🔍 BUG ANALYSIS:")
            self.log("   ✅ Successfully reproduced the 'Failed to load notes' error")
            self.log("   🐛 Root cause: Frontend creates virtual note IDs for batch reports")
            self.log("   🐛 Backend AI chat endpoint expects real note IDs from database")
            self.log("   🐛 Virtual note IDs return 404 'Note not found' error")
            self.log("   💡 Solution needed: Create endpoint for AI chat with batch content")
        
        return test_results

def main():
    """Main test execution"""
    tester = BatchReportAITester()
    results = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()