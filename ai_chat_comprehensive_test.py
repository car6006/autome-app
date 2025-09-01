#!/usr/bin/env python3
"""
AI Chat Comprehensive Test - Review Request
Tests the AI Chat endpoint stability after background task error propagation fix
Includes manual content setup to properly test AI functionality
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

class AIChatComprehensiveTester:
    def __init__(self, base_url="https://pwa-integration-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"ai_chat_test_{int(time.time())}@example.com",
            "username": f"aichatuser_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "AI",
            "last_name": "ChatTester"
        }
        # MongoDB connection for direct content insertion
        self.mongo_client = None
        self.db = None

    async def setup_db_connection(self):
        """Setup direct MongoDB connection for content insertion"""
        try:
            self.mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
            self.db = self.mongo_client["auto_me_db"]
            self.log("✅ Database connection established")
            return True
        except Exception as e:
            self.log(f"❌ Failed to connect to database: {str(e)}")
            return False

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

    def setup_test_user(self):
        """Register and login test user"""
        self.log("🔐 Setting up test user...")
        
        # Register user
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   User registered and authenticated")
            return True
        return False

    async def create_note_with_content(self):
        """Create a note and manually add transcribed content for AI chat testing"""
        self.log("📝 Creating note with transcribed content...")
        
        # Create audio note
        success, response = self.run_test(
            "Create Audio Note for AI Chat",
            "POST",
            "notes",
            200,
            data={"title": "AI Chat Test Meeting - Risk Analysis", "kind": "audio"},
            auth_required=True
        )
        
        if not success or 'id' not in response:
            return None
            
        note_id = response['id']
        self.created_notes.append(note_id)
        self.log(f"   Created note ID: {note_id}")
        
        # Manually add comprehensive transcript content directly to database
        test_transcript = """
        Good morning everyone, thank you for joining today's quarterly business review meeting. 
        
        Let me start with our key performance indicators for Q3. Revenue is up 15% compared to last quarter, 
        which is excellent news. However, we're seeing some challenges in our supply chain operations, 
        particularly with shipping delays from our Asian suppliers.
        
        Our customer satisfaction scores have improved to 4.2 out of 5, but we still have room for improvement 
        in our response times. The average response time is currently 24 hours, and we want to get that down to 12 hours.
        
        From a risk perspective, we need to be aware of several critical factors:
        
        1. FINANCIAL RISKS:
        - Currency fluctuations affecting our international operations, particularly with the Euro and Yen
        - Rising interest rates impacting our debt servicing costs
        - Inflation pressures on operational expenses and supplier costs
        
        2. OPERATIONAL RISKS:
        - Potential supply chain disruptions due to geopolitical tensions in Eastern Europe and Asia
        - Cybersecurity threats that could affect our digital infrastructure and customer data
        - Key personnel dependency in critical roles without adequate succession planning
        
        3. MARKET RISKS:
        - Increased competition in our core markets from both established players and new entrants
        - Changing customer preferences toward more sustainable and digital solutions
        - Economic recession concerns affecting customer spending patterns
        
        4. REGULATORY RISKS:
        - New data privacy regulations in multiple jurisdictions that may impact our operations
        - Environmental compliance requirements becoming more stringent
        - Trade policy changes affecting our international business
        
        5. TECHNOLOGY RISKS:
        - Legacy system vulnerabilities and the need for digital transformation
        - Potential disruption from AI and automation in our industry
        - Data security and privacy concerns with increasing digital footprint
        
        For the next quarter, our priorities are:
        - Diversifying our supplier base to reduce dependency and mitigate supply chain risks
        - Implementing new customer service automation tools to improve response times
        - Expanding into two new geographic markets to reduce concentration risk
        - Strengthening our cybersecurity posture with additional security measures
        - Developing comprehensive risk management frameworks for all identified risk areas
        
        We also need to focus on building resilience across all business functions and creating contingency plans 
        for various risk scenarios. This includes establishing alternative supply chains, improving our financial 
        reserves, and enhancing our crisis management capabilities.
        
        I'd like to open the floor for questions and discussion about these points, particularly around our 
        risk mitigation strategies and how we can better prepare for potential challenges ahead.
        """
        
        # Update the note with transcript content and set status to ready
        try:
            await self.db["notes"].update_one(
                {"id": note_id},
                {
                    "$set": {
                        "artifacts": {"transcript": test_transcript},
                        "status": "ready",
                        "ready_at": datetime.now()
                    }
                }
            )
            self.log("   ✅ Transcript content added to note")
            self.log("   ✅ Note status set to 'ready'")
            return note_id
        except Exception as e:
            self.log(f"   ❌ Failed to add content to note: {str(e)}")
            return None

    def test_ai_chat_endpoint_stability(self, note_id):
        """Test AI Chat endpoint for consistent responses without 500 errors"""
        self.log("🤖 Testing AI Chat endpoint stability...")
        
        # Test multiple questions to ensure stability
        test_questions = [
            "Provide comprehensive risks to the notes",  # The specific question from review request
            "What are the key performance indicators mentioned?",
            "Summarize the main challenges discussed in the meeting",
            "What are the priorities for next quarter?",
            "Analyze the customer satisfaction metrics and improvement areas"
        ]
        
        successful_responses = 0
        
        for i, question in enumerate(test_questions, 1):
            self.log(f"   Question {i}: {question}")
            
            success, response = self.run_test(
                f"AI Chat Question {i}",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True,
                timeout=60  # Longer timeout for AI processing
            )
            
            if success:
                successful_responses += 1
                ai_response = response.get('response', '')
                self.log(f"   ✅ AI Response length: {len(ai_response)} characters")
                self.log(f"   Response preview: {ai_response[:150]}...")
                
                # Verify response contains relevant content
                if len(ai_response) > 100:  # Reasonable response length
                    self.log(f"   ✅ Response appears comprehensive")
                else:
                    self.log(f"   ⚠️  Response seems short")
                    
                # Check for no 500 errors (which was the main issue being fixed)
                if response.get('response') and not response.get('error'):
                    self.log(f"   ✅ No 500 error - background task fix working")
                    
            else:
                self.log(f"   ❌ Failed to get AI response")
            
            # Small delay between requests
            time.sleep(1)
        
        success_rate = (successful_responses / len(test_questions)) * 100
        self.log(f"   AI Chat Success Rate: {success_rate:.1f}% ({successful_responses}/{len(test_questions)})")
        
        return successful_responses == len(test_questions)

    def test_specific_risk_analysis_question(self, note_id):
        """Test the specific question mentioned in the review request"""
        self.log("🎯 Testing specific risk analysis question...")
        
        success, response = self.run_test(
            "Specific Risk Analysis Question",
            "POST",
            f"notes/{note_id}/ai-chat",
            200,
            data={"question": "Provide comprehensive risks to the notes"},
            auth_required=True,
            timeout=60
        )
        
        if success:
            ai_response = response.get('response', '')
            self.log(f"   ✅ Risk analysis response received")
            self.log(f"   Response length: {len(ai_response)} characters")
            
            # Check if response contains risk-related keywords
            risk_keywords = ['risk', 'threat', 'challenge', 'concern', 'vulnerability', 'impact', 'financial', 'operational', 'market', 'regulatory', 'technology']
            found_keywords = [keyword for keyword in risk_keywords if keyword.lower() in ai_response.lower()]
            
            self.log(f"   Risk keywords found: {', '.join(found_keywords[:5])}{'...' if len(found_keywords) > 5 else ''}")
            
            if len(found_keywords) >= 3:
                self.log(f"   ✅ Response appears to address comprehensive risk analysis")
                return True
            else:
                self.log(f"   ⚠️  Response may not fully address risk analysis")
                return False
        
        return False

    def test_consecutive_questions(self, note_id):
        """Test multiple consecutive questions to ensure no error propagation"""
        self.log("🔄 Testing consecutive questions for error propagation...")
        
        consecutive_questions = [
            "What is the revenue growth mentioned?",
            "What are the supply chain challenges?",
            "How can we improve customer satisfaction?",
            "What are the cybersecurity concerns?",
            "Summarize the meeting priorities",
            "What financial risks were discussed?",
            "How should we address operational risks?"
        ]
        
        all_successful = True
        consecutive_success_count = 0
        
        for i, question in enumerate(consecutive_questions, 1):
            success, response = self.run_test(
                f"Consecutive Question {i}",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True,
                timeout=60
            )
            
            if not success:
                all_successful = False
                self.log(f"   ❌ Consecutive question {i} failed")
            else:
                consecutive_success_count += 1
                self.log(f"   ✅ Consecutive question {i} succeeded")
                
                # Verify no 500 errors in consecutive calls
                if response.get('response'):
                    self.log(f"   ✅ No error propagation detected")
        
        self.log(f"   Consecutive Questions Success Rate: {(consecutive_success_count/len(consecutive_questions)*100):.1f}%")
        return all_successful

    def test_error_handling(self, note_id):
        """Test error handling scenarios"""
        self.log("🚨 Testing error handling scenarios...")
        
        # Test empty question
        success, response = self.run_test(
            "Empty Question (Should Fail)",
            "POST",
            f"notes/{note_id}/ai-chat",
            400,
            data={"question": ""},
            auth_required=True
        )
        
        # Test missing question parameter
        success2, response2 = self.run_test(
            "Missing Question Parameter (Should Fail)",
            "POST",
            f"notes/{note_id}/ai-chat",
            400,
            data={},
            auth_required=True
        )
        
        # Test non-existent note
        success3, response3 = self.run_test(
            "Non-existent Note (Should Fail)",
            "POST",
            "notes/invalid-note-id/ai-chat",
            404,
            data={"question": "Test question"},
            auth_required=True
        )
        
        return success and success2 and success3

    def test_background_task_error_isolation(self, note_id):
        """Test that background task errors don't affect AI chat responses"""
        self.log("🔧 Testing background task error isolation...")
        
        # Test multiple rapid-fire questions to stress test error isolation
        rapid_questions = [
            "Quick analysis of risks",
            "Brief summary of KPIs", 
            "Main challenges overview",
            "Priority actions list"
        ]
        
        all_successful = True
        
        for i, question in enumerate(rapid_questions, 1):
            success, response = self.run_test(
                f"Rapid Question {i}",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True,
                timeout=45
            )
            
            if success:
                # Check that we get actual AI response, not error
                ai_response = response.get('response', '')
                if len(ai_response) > 20 and 'error' not in ai_response.lower():
                    self.log(f"   ✅ Rapid question {i} - Clean AI response received")
                else:
                    self.log(f"   ⚠️  Rapid question {i} - Response may contain errors")
                    all_successful = False
            else:
                self.log(f"   ❌ Rapid question {i} failed")
                all_successful = False
        
        return all_successful

    async def run_ai_chat_tests(self):
        """Run comprehensive AI Chat tests"""
        self.log("🚀 Starting AI Chat Functionality Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup database connection
        if not await self.setup_db_connection():
            self.log("❌ Failed to setup database connection - stopping tests")
            return False
        
        # Setup test user
        if not self.setup_test_user():
            self.log("❌ Failed to setup test user - stopping tests")
            return False
        
        # Create note with content
        note_id = await self.create_note_with_content()
        if not note_id:
            self.log("❌ Failed to create note with content - stopping tests")
            return False
        
        # Wait a moment for database consistency
        time.sleep(1)
        
        # Test AI Chat endpoint stability
        stability_success = self.test_ai_chat_endpoint_stability(note_id)
        
        # Test specific risk analysis question
        risk_analysis_success = self.test_specific_risk_analysis_question(note_id)
        
        # Test consecutive questions
        consecutive_success = self.test_consecutive_questions(note_id)
        
        # Test error handling
        error_handling_success = self.test_error_handling(note_id)
        
        # Test background task error isolation
        isolation_success = self.test_background_task_error_isolation(note_id)
        
        return stability_success and risk_analysis_success and consecutive_success and error_handling_success and isolation_success

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 AI CHAT COMPREHENSIVE TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

    async def cleanup(self):
        """Cleanup database connections"""
        if self.mongo_client:
            self.mongo_client.close()

async def main():
    """Main test execution"""
    tester = AIChatComprehensiveTester()
    
    try:
        success = await tester.run_ai_chat_tests()
        tester.print_summary()
        
        if success:
            print("\n🎉 All AI Chat tests passed! Endpoint is stable and working correctly.")
            print("✅ Background task error propagation fix is working properly.")
            return 0
        else:
            print(f"\n⚠️  Some AI Chat tests failed. Check the logs above for details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))