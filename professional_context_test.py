#!/usr/bin/env python3
"""
Professional Context Management and AI Chat Testing
Tests the Enhanced Personalized AI Assistant System features
"""

import requests
import sys
import json
import time
from datetime import datetime

class ProfessionalContextTester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_id = None
        self.created_notes = []
        
        # Test user data
        self.test_user_data = {
            "email": f"contexttest{int(time.time())}@example.com",
            "username": f"contextuser{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Context",
            "last_name": "Tester"
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

    def setup_authentication(self):
        """Set up authentication for testing"""
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
            user_data = response.get('user', {})
            self.test_user_id = user_data.get('id')
            self.log(f"   Registered user ID: {self.test_user_id}")
            return True
        return False

    def test_professional_context_save(self):
        """Test POST /api/user/professional-context - Save professional preferences"""
        professional_contexts = [
            {
                "name": "Logistics Manager",
                "data": {
                    "primary_industry": "Logistics & Supply Chain",
                    "job_role": "Logistics Manager",
                    "work_environment": "Global freight forwarding company",
                    "key_focus_areas": ["Cost optimization", "Supply chain risks", "Operational efficiency"],
                    "content_types": ["Meeting minutes", "CRM notes", "Project updates"],
                    "analysis_preferences": ["Strategic recommendations", "Risk assessment", "Action items"]
                }
            },
            {
                "name": "Healthcare Professional",
                "data": {
                    "primary_industry": "Healthcare",
                    "job_role": "Healthcare Administrator",
                    "work_environment": "Hospital management",
                    "key_focus_areas": ["Patient care quality", "Operational efficiency", "Compliance"],
                    "content_types": ["Patient care notes", "Meeting minutes", "Performance reports"],
                    "analysis_preferences": ["Quality improvement", "Risk management", "Compliance analysis"]
                }
            },
            {
                "name": "Construction Engineer",
                "data": {
                    "primary_industry": "Construction",
                    "job_role": "Construction Project Manager",
                    "work_environment": "Commercial construction projects",
                    "key_focus_areas": ["Project timeline", "Safety compliance", "Cost management"],
                    "content_types": ["Project updates", "Safety reports", "Meeting minutes"],
                    "analysis_preferences": ["Timeline analysis", "Safety assessment", "Budget tracking"]
                }
            },
            {
                "name": "Financial Analyst",
                "data": {
                    "primary_industry": "Financial Services",
                    "job_role": "Senior Financial Analyst",
                    "work_environment": "Investment banking",
                    "key_focus_areas": ["Financial performance", "Risk assessment", "Market analysis"],
                    "content_types": ["Financial reports", "Market analysis", "Client meetings"],
                    "analysis_preferences": ["ROI analysis", "Risk evaluation", "Performance metrics"]
                }
            },
            {
                "name": "Sales Manager",
                "data": {
                    "primary_industry": "Sales & Marketing",
                    "job_role": "Regional Sales Manager",
                    "work_environment": "B2B software sales",
                    "key_focus_areas": ["Pipeline management", "Client relationships", "Revenue growth"],
                    "content_types": ["CRM notes", "Client interactions", "Sales meetings"],
                    "analysis_preferences": ["Pipeline analysis", "Client insights", "Revenue forecasting"]
                }
            }
        ]
        
        successful_saves = 0
        
        for context in professional_contexts:
            success, response = self.run_test(
                f"Save Professional Context - {context['name']}",
                "POST",
                "user/professional-context",
                200,
                data=context['data'],
                auth_required=True
            )
            
            if success:
                successful_saves += 1
                self.log(f"   ✅ Context saved for {context['name']}")
                saved_context = response.get('context', {})
                self.log(f"   Industry: {saved_context.get('primary_industry', 'N/A')}")
                self.log(f"   Role: {saved_context.get('job_role', 'N/A')}")
                self.log(f"   Focus areas: {len(saved_context.get('key_focus_areas', []))} items")
            else:
                self.log(f"   ❌ Failed to save context for {context['name']}")
        
        return successful_saves

    def test_professional_context_retrieve(self):
        """Test GET /api/user/professional-context - Retrieve professional preferences"""
        success, response = self.run_test(
            "Retrieve Professional Context",
            "GET",
            "user/professional-context",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Context retrieved successfully")
            self.log(f"   Industry: {response.get('primary_industry', 'N/A')}")
            self.log(f"   Role: {response.get('job_role', 'N/A')}")
            self.log(f"   Work environment: {response.get('work_environment', 'N/A')}")
            self.log(f"   Focus areas: {response.get('key_focus_areas', [])}")
            self.log(f"   Content types: {response.get('content_types', [])}")
            self.log(f"   Analysis preferences: {response.get('analysis_preferences', [])}")
            return True, response
        
        return False, {}

    def test_professional_context_validation(self):
        """Test professional context validation"""
        test_cases = [
            {
                "name": "Missing Required Fields",
                "data": {},
                "expected_status": 200  # Should work as all fields are optional
            },
            {
                "name": "Minimal Valid Context",
                "data": {"primary_industry": "Technology"},
                "expected_status": 200
            },
            {
                "name": "Invalid Data Types",
                "data": {
                    "primary_industry": 123,  # Should be string
                    "key_focus_areas": "not a list"  # Should be list
                },
                "expected_status": 200  # Backend should handle type conversion
            }
        ]
        
        successful_validations = 0
        
        for test_case in test_cases:
            success, response = self.run_test(
                f"Validation Test - {test_case['name']}",
                "POST",
                "user/professional-context",
                test_case['expected_status'],
                data=test_case['data'],
                auth_required=True
            )
            
            if success:
                successful_validations += 1
                self.log(f"   ✅ Validation test passed: {test_case['name']}")
            else:
                self.log(f"   ❌ Validation test failed: {test_case['name']}")
        
        return successful_validations

    def create_test_note_with_content(self, title, content):
        """Create a text note with specific content for AI chat testing"""
        note_data = {
            "title": title,
            "kind": "text",
            "text_content": content
        }
        
        success, response = self.run_test(
            f"Create Text Note: {title[:30]}...",
            "POST",
            "notes",
            200,
            data=note_data,
            auth_required=True
        )
        
        if success and 'id' in response:
            note_id = response['id']
            self.created_notes.append(note_id)
            self.log(f"   ✅ Created note ID: {note_id}")
            return note_id
        return None

    def test_ai_chat_with_context(self, note_id, questions, context_name):
        """Test AI chat with professional context"""
        successful_chats = 0
        
        for i, question in enumerate(questions):
            success, response = self.run_test(
                f"AI Chat ({context_name}) - Q{i+1}",
                "POST",
                f"notes/{note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True,
                timeout=60
            )
            
            if success:
                successful_chats += 1
                ai_response = response.get('response', '')
                context_summary = response.get('context_summary', {})
                
                self.log(f"   ✅ AI Response length: {len(ai_response)} characters")
                self.log(f"   Context detected: {context_summary.get('profession_detected', 'N/A')}")
                self.log(f"   User industry: {context_summary.get('user_industry', 'N/A')}")
                
                # Check response quality
                if len(ai_response) > 200:
                    self.log(f"   ✅ Comprehensive response")
                else:
                    self.log(f"   ⚠️  Response may be brief")
            else:
                self.log(f"   ❌ AI Chat failed for question {i+1}")
        
        return successful_chats

    def test_industry_specific_responses(self):
        """Test industry-specific AI responses with different professional contexts"""
        
        industry_scenarios = [
            {
                "context": {
                    "primary_industry": "Logistics & Supply Chain",
                    "job_role": "Logistics Manager",
                    "work_environment": "Global freight forwarding",
                    "key_focus_areas": ["Cost optimization", "Supply chain risks"],
                    "content_types": ["Meeting minutes", "CRM notes"],
                    "analysis_preferences": ["Strategic recommendations", "Risk assessment"]
                },
                "content": """Supply Chain Meeting - Q4 Planning
Discussed freight costs from Asia to North America increasing 15%.
Port congestion causing 3-day delays on average.
Carrier capacity constraints during peak season.
Need to evaluate alternative routing options.
Safety stock levels need review for key SKUs.
Warehouse capacity at 85% utilization.""",
                "questions": [
                    "Analyze the supply chain risks mentioned in this meeting",
                    "What cost optimization opportunities do you see?",
                    "Provide strategic recommendations for the logistics challenges"
                ],
                "expected_terms": ["supply chain", "freight", "logistics", "carrier", "inventory"]
            },
            {
                "context": {
                    "primary_industry": "Healthcare",
                    "job_role": "Healthcare Administrator",
                    "work_environment": "Hospital management",
                    "key_focus_areas": ["Patient care quality", "Operational efficiency"],
                    "content_types": ["Patient care notes", "Performance reports"],
                    "analysis_preferences": ["Quality improvement", "Risk management"]
                },
                "content": """Patient Care Review - December 2024
Patient satisfaction scores declined 12% this quarter.
Average wait times increased to 45 minutes.
Staff reported increased workload and overtime.
3 patient safety incidents recorded (all minor).
Bed occupancy rate at 92% capacity.
Need to address staffing levels and process efficiency.""",
                "questions": [
                    "Assess the patient care quality issues identified",
                    "What operational efficiency improvements are needed?",
                    "Provide recommendations for healthcare management"
                ],
                "expected_terms": ["patient", "healthcare", "clinical", "medical", "safety"]
            },
            {
                "context": {
                    "primary_industry": "Construction",
                    "job_role": "Construction Project Manager",
                    "work_environment": "Commercial construction",
                    "key_focus_areas": ["Project timeline", "Safety compliance"],
                    "content_types": ["Project updates", "Safety reports"],
                    "analysis_preferences": ["Timeline analysis", "Safety assessment"]
                },
                "content": """Project Status Update - Office Complex Build
Project is 2 weeks behind original schedule.
Material delays due to supply chain issues.
Weather caused 4 lost work days this month.
Safety inspection found 2 minor violations.
Budget tracking 8% over due to overtime costs.
Subcontractor performance below expectations.""",
                "questions": [
                    "Analyze the project timeline challenges",
                    "What safety compliance issues need attention?",
                    "Provide construction management recommendations"
                ],
                "expected_terms": ["project", "construction", "safety", "schedule", "timeline"]
            }
        ]
        
        successful_scenarios = 0
        
        for i, scenario in enumerate(industry_scenarios):
            self.log(f"\n--- Testing {scenario['context']['primary_industry']} Scenario ---")
            
            # Set professional context
            context_success, _ = self.run_test(
                f"Set Context - {scenario['context']['primary_industry']}",
                "POST",
                "user/professional-context",
                200,
                data=scenario['context'],
                auth_required=True
            )
            
            if not context_success:
                self.log(f"   ❌ Failed to set context for {scenario['context']['primary_industry']}")
                continue
            
            # Create note with industry-specific content
            note_id = self.create_test_note_with_content(
                f"{scenario['context']['primary_industry']} Analysis",
                scenario['content']
            )
            
            if not note_id:
                self.log(f"   ❌ Failed to create note for {scenario['context']['primary_industry']}")
                continue
            
            # Test AI chat with industry-specific questions
            successful_chats = self.test_ai_chat_with_context(
                note_id, 
                scenario['questions'], 
                scenario['context']['primary_industry']
            )
            
            if successful_chats == len(scenario['questions']):
                successful_scenarios += 1
                self.log(f"   ✅ {scenario['context']['primary_industry']} scenario completed successfully")
            else:
                self.log(f"   ⚠️  {scenario['context']['primary_industry']} scenario partially successful ({successful_chats}/{len(scenario['questions'])})")
        
        return successful_scenarios

    def test_content_type_detection(self):
        """Test content type detection accuracy"""
        content_scenarios = [
            {
                "type": "Meeting Minutes",
                "content": """Meeting: Weekly Team Standup
Date: December 19, 2024
Attendees: Project Manager, Development Team, QA Lead

Agenda Items:
1. Sprint progress review
2. Blockers and impediments
3. Next week planning

Decisions Made:
- Extend current sprint by 2 days
- Prioritize bug fixes over new features
- Schedule code review session

Action Items:
- John to fix authentication bug by Friday
- Sarah to update documentation
- Team to attend training session next week""",
                "questions": ["Generate meeting minutes from this content"],
                "expected_format": ["ATTENDEES", "DECISIONS", "ACTION ITEMS"]
            },
            {
                "type": "CRM Notes",
                "content": """Client Call - ABC Corporation
Contact: John Smith, Procurement Director
Date: December 19, 2024

Discussion Points:
- Reviewed Q1 2025 procurement needs
- Discussed pricing for bulk orders
- Addressed delivery timeline concerns
- Explored partnership opportunities

Client Feedback:
- Satisfied with current service quality
- Interested in expanding contract scope
- Requested proposal for additional services

Follow-up Actions:
- Send updated pricing proposal by Dec 22
- Schedule facility tour for January
- Prepare contract amendment draft""",
                "questions": ["Analyze this client interaction and provide CRM insights"],
                "expected_format": ["client", "relationship", "opportunity", "follow-up"]
            },
            {
                "type": "Project Updates",
                "content": """Project Status Report - Q4 2024
Project: Customer Portal Redesign
Timeline: October - December 2024
Budget: $150,000

Progress Summary:
- Design phase: 100% complete
- Development: 75% complete
- Testing: 30% complete
- Deployment: Not started

Key Milestones:
- UI/UX design approved (Nov 15)
- Backend API development (Dec 10)
- User acceptance testing (Dec 30)

Risks and Issues:
- Integration testing delayed by 1 week
- Third-party API changes require updates
- Resource availability during holidays""",
                "questions": ["Provide project status analysis and recommendations"],
                "expected_format": ["project", "milestone", "progress", "timeline"]
            }
        ]
        
        successful_detections = 0
        
        for scenario in content_scenarios:
            self.log(f"\n--- Testing {scenario['type']} Detection ---")
            
            # Create note with specific content type
            note_id = self.create_test_note_with_content(
                f"{scenario['type']} Test",
                scenario['content']
            )
            
            if not note_id:
                continue
            
            # Test AI chat with content type specific questions
            for question in scenario['questions']:
                success, response = self.run_test(
                    f"Content Type Detection - {scenario['type']}",
                    "POST",
                    f"notes/{note_id}/ai-chat",
                    200,
                    data={"question": question},
                    auth_required=True,
                    timeout=60
                )
                
                if success:
                    ai_response = response.get('response', '').lower()
                    
                    # Check for expected format elements
                    format_matches = 0
                    for expected in scenario['expected_format']:
                        if expected.lower() in ai_response:
                            format_matches += 1
                    
                    if format_matches >= len(scenario['expected_format']) // 2:
                        successful_detections += 1
                        self.log(f"   ✅ Content type format detected ({format_matches}/{len(scenario['expected_format'])} elements)")
                    else:
                        self.log(f"   ⚠️  Limited format detection ({format_matches}/{len(scenario['expected_format'])} elements)")
                else:
                    self.log(f"   ❌ Content type detection failed")
        
        return successful_detections

    def test_authentication_requirements(self):
        """Test authentication requirements for professional context endpoints"""
        # Test without authentication
        temp_token = self.auth_token
        self.auth_token = None
        
        # Test saving context without auth (should fail)
        success1, _ = self.run_test(
            "Save Context Without Auth (Should Fail)",
            "POST",
            "user/professional-context",
            403,
            data={"primary_industry": "Test"},
            auth_required=True
        )
        
        # Test retrieving context without auth (should fail)
        success2, _ = self.run_test(
            "Retrieve Context Without Auth (Should Fail)",
            "GET",
            "user/professional-context",
            403,
            auth_required=True
        )
        
        # Restore token
        self.auth_token = temp_token
        
        return success1 and success2

    def run_comprehensive_test(self):
        """Run all professional context and AI chat tests"""
        self.log("🚀 Starting Professional Context Management Tests")
        self.log(f"   Base URL: {self.base_url}")
        
        # Setup authentication
        if not self.setup_authentication():
            self.log("❌ Authentication setup failed - stopping tests")
            return False
        
        # === PROFESSIONAL CONTEXT MANAGEMENT TESTS ===
        self.log("\n🎯 PROFESSIONAL CONTEXT MANAGEMENT TESTS")
        
        # Test saving professional contexts
        successful_saves = self.test_professional_context_save()
        self.log(f"   Professional Context Saves: {successful_saves}/5 successful")
        
        # Test retrieving professional context
        context_success, context_data = self.test_professional_context_retrieve()
        if not context_success:
            self.log("❌ Professional context retrieval failed")
        
        # Test validation
        successful_validations = self.test_professional_context_validation()
        self.log(f"   Validation Tests: {successful_validations}/3 successful")
        
        # Test authentication requirements
        auth_success = self.test_authentication_requirements()
        if auth_success:
            self.log("   ✅ Authentication requirements verified")
        else:
            self.log("   ❌ Authentication requirements test failed")
        
        # === ENHANCED AI CHAT WITH CONTEXT TESTS ===
        self.log("\n🤖 ENHANCED AI CHAT WITH PROFESSIONAL CONTEXT TESTS")
        
        # Test industry-specific responses
        successful_scenarios = self.test_industry_specific_responses()
        self.log(f"   Industry-Specific Scenarios: {successful_scenarios}/3 successful")
        
        # === CONTENT TYPE DETECTION TESTS ===
        self.log("\n📋 CONTENT TYPE DETECTION TESTS")
        
        # Test content type detection
        successful_detections = self.test_content_type_detection()
        self.log(f"   Content Type Detection: {successful_detections}/3 successful")
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 PROFESSIONAL CONTEXT TESTING SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ProfessionalContextTester()
    
    try:
        success = tester.run_comprehensive_test()
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All professional context tests passed!")
            return 0
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
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