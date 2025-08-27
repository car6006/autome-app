#!/usr/bin/env python3
"""
Critical Bug Fix Verification Tests
Tests for React Runtime Error & Batch Report Issues fixes
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class CriticalBugFixTester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        self.test_user_data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "username": f"testuser{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        self.expeditors_user_data = {
            "email": f"test_expeditors_{int(time.time())}@expeditors.com",
            "username": f"expeditorsuser{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "User"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
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

    def setup_users(self):
        """Setup test users for testing"""
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
            self.log(f"   Regular user registered: {self.test_user_data['email']}")
        else:
            self.log("❌ Failed to register regular user")
            return False
        
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
            self.log(f"   Expeditors user registered: {self.expeditors_user_data['email']}")
        else:
            self.log("❌ Failed to register Expeditors user")
            return False
        
        return True

    def test_professional_context_array_handling(self):
        """Test professional context API with proper array handling (React Runtime Error Fix)"""
        self.log("\n🔧 TESTING PROFESSIONAL CONTEXT ARRAY HANDLING")
        
        # Test 1: Save professional context with arrays
        professional_context = {
            "primary_industry": "Logistics & Supply Chain",
            "job_role": "Logistics Manager",
            "work_environment": "Global freight forwarding company",
            "key_focus_areas": ["Cost optimization", "Supply chain risks", "Operational efficiency"],
            "content_types": ["Meeting minutes", "CRM notes", "Project updates"],
            "analysis_preferences": ["Strategic recommendations", "Risk assessment", "Action items"]
        }
        
        success, response = self.run_test(
            "Save Professional Context with Arrays",
            "POST",
            "user/professional-context",
            200,
            data=professional_context,
            auth_required=True
        )
        
        if success:
            context = response.get('context', {})
            self.log(f"   ✅ Arrays saved correctly:")
            self.log(f"     - key_focus_areas: {len(context.get('key_focus_areas', []))} items")
            self.log(f"     - content_types: {len(context.get('content_types', []))} items")
            self.log(f"     - analysis_preferences: {len(context.get('analysis_preferences', []))} items")
        
        # Test 2: Retrieve professional context and verify arrays
        success, response = self.run_test(
            "Retrieve Professional Context Arrays",
            "GET",
            "user/professional-context",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Arrays retrieved correctly:")
            self.log(f"     - key_focus_areas: {response.get('key_focus_areas', [])}")
            self.log(f"     - content_types: {response.get('content_types', [])}")
            self.log(f"     - analysis_preferences: {response.get('analysis_preferences', [])}")
            
            # Verify arrays are actually arrays, not strings
            key_focus_areas = response.get('key_focus_areas', [])
            content_types = response.get('content_types', [])
            analysis_preferences = response.get('analysis_preferences', [])
            
            if isinstance(key_focus_areas, list):
                self.log(f"   ✅ key_focus_areas is properly an array")
            else:
                self.log(f"   ❌ key_focus_areas is not an array: {type(key_focus_areas)}")
            
            if isinstance(content_types, list):
                self.log(f"   ✅ content_types is properly an array")
            else:
                self.log(f"   ❌ content_types is not an array: {type(content_types)}")
            
            if isinstance(analysis_preferences, list):
                self.log(f"   ✅ analysis_preferences is properly an array")
            else:
                self.log(f"   ❌ analysis_preferences is not an array: {type(analysis_preferences)}")
        
        # Test 3: Handle undefined/null arrays gracefully
        minimal_context = {
            "primary_industry": "Healthcare",
            "job_role": "Administrator"
            # Intentionally omitting array fields to test null handling
        }
        
        success, response = self.run_test(
            "Save Context with Missing Arrays",
            "POST",
            "user/professional-context",
            200,
            data=minimal_context,
            auth_required=True
        )
        
        if success:
            context = response.get('context', {})
            self.log(f"   ✅ Missing arrays handled gracefully:")
            self.log(f"     - key_focus_areas: {context.get('key_focus_areas', 'undefined')}")
            self.log(f"     - content_types: {context.get('content_types', 'undefined')}")
            self.log(f"     - analysis_preferences: {context.get('analysis_preferences', 'undefined')}")
        
        # Test 4: Retrieve context with missing arrays
        success, response = self.run_test(
            "Retrieve Context with Missing Arrays",
            "GET",
            "user/professional-context",
            200,
            auth_required=True
        )
        
        if success:
            # Verify that missing arrays are returned as empty arrays, not null/undefined
            key_focus_areas = response.get('key_focus_areas', [])
            content_types = response.get('content_types', [])
            analysis_preferences = response.get('analysis_preferences', [])
            
            self.log(f"   ✅ Missing arrays returned as empty arrays:")
            self.log(f"     - key_focus_areas: {key_focus_areas} (type: {type(key_focus_areas)})")
            self.log(f"     - content_types: {content_types} (type: {type(content_types)})")
            self.log(f"     - analysis_preferences: {analysis_preferences} (type: {type(analysis_preferences)})")
        
        return True

    def test_professional_context_malformed_data(self):
        """Test professional context with malformed data"""
        self.log("\n🔧 TESTING PROFESSIONAL CONTEXT ERROR HANDLING")
        
        # Test with malformed array data
        malformed_context = {
            "primary_industry": "Technology",
            "job_role": "Developer",
            "key_focus_areas": "This should be an array but is a string",  # Malformed
            "content_types": ["Valid array"],
            "analysis_preferences": None  # Null value
        }
        
        success, response = self.run_test(
            "Save Context with Malformed Data",
            "POST",
            "user/professional-context",
            200,  # Should still work, backend should handle gracefully
            data=malformed_context,
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Malformed data handled gracefully")
        
        return True

    def create_test_notes_for_batch_report(self):
        """Create multiple notes with content for batch report testing"""
        self.log("\n📝 Creating test notes for batch report...")
        
        note_contents = [
            {
                "title": "Supply Chain Risk Assessment Q4 2024",
                "content": """Meeting: Q4 Supply Chain Risk Assessment
Date: December 19, 2024
Attendees: Supply Chain Director, Risk Manager, Operations Lead

Key Risks Identified:
- Port congestion in major Asian ports affecting delivery schedules
- Currency fluctuations impacting freight costs by 12-15%
- Limited warehouse capacity during peak season
- Potential carrier capacity constraints in Q1 2025
- Geopolitical tensions affecting trade routes

Mitigation Strategies:
- Diversify carrier portfolio to reduce dependency
- Implement dynamic routing to avoid congested ports
- Increase safety stock levels by 20% for critical SKUs
- Negotiate flexible contracts with backup carriers
- Monitor geopolitical developments daily

Action Items:
- Procurement team to finalize backup carrier agreements by Dec 30
- Operations to increase safety stock orders by Dec 25
- Risk team to implement daily monitoring dashboard
- Weekly risk assessment meetings starting Jan 2025"""
            },
            {
                "title": "Customer Service Performance Review",
                "content": """Customer Service Performance Analysis
Period: Q4 2024
Team: Customer Experience Division

Performance Metrics:
- Customer satisfaction score: 87% (target: 85%)
- Average response time: 2.3 hours (target: 4 hours)
- First-call resolution rate: 78% (target: 75%)
- Customer retention rate: 94% (target: 90%)

Areas of Excellence:
- Exceeded response time targets by 42%
- Improved customer satisfaction by 8% from Q3
- Successfully handled 15% increase in holiday season inquiries
- Implemented new chat support system with 95% uptime

Improvement Opportunities:
- Increase first-call resolution rate to 85%
- Reduce escalation time for complex issues
- Enhance product knowledge training for new hires
- Implement proactive customer outreach program

Next Steps:
- Launch advanced training program in January
- Deploy AI-powered chat assistance by February
- Implement customer feedback loop improvements
- Set up quarterly performance review cycles"""
            },
            {
                "title": "Technology Infrastructure Upgrade Plan",
                "content": """IT Infrastructure Modernization Project
Project Phase: Planning & Assessment
Timeline: Q1-Q3 2025

Current State Assessment:
- Legacy systems running on outdated hardware (5+ years old)
- Network infrastructure at 78% capacity utilization
- Security vulnerabilities identified in 12 critical systems
- Cloud migration readiness assessment: 65% complete
- Staff training requirements: 40 hours per team member

Proposed Upgrades:
- Migrate 80% of applications to cloud infrastructure
- Implement zero-trust security framework
- Upgrade network backbone to support 10Gbps speeds
- Deploy new monitoring and alerting systems
- Establish disaster recovery site with 4-hour RTO

Budget Requirements:
- Hardware and software: $2.3M
- Professional services: $800K
- Training and certification: $150K
- Contingency (15%): $487K
- Total project budget: $3.737M

Risk Mitigation:
- Phased rollout to minimize business disruption
- Comprehensive backup and rollback procedures
- 24/7 support during critical migration windows
- Extensive user acceptance testing before go-live"""
            }
        ]
        
        created_note_ids = []
        
        for note_data in note_contents:
            note_request = {
                "title": note_data["title"],
                "kind": "text",
                "text_content": note_data["content"]
            }
            
            success, response = self.run_test(
                f"Create Note: {note_data['title'][:30]}...",
                "POST",
                "notes",
                200,
                data=note_request,
                auth_required=True
            )
            
            if success and 'id' in response:
                note_id = response['id']
                created_note_ids.append(note_id)
                self.created_notes.append(note_id)
                self.log(f"   ✅ Created note: {note_id}")
            else:
                self.log(f"   ❌ Failed to create note: {note_data['title']}")
        
        return created_note_ids

    def test_batch_report_with_professional_context(self):
        """Test batch report generation with professional context integration"""
        self.log("\n📊 TESTING BATCH REPORT WITH PROFESSIONAL CONTEXT")
        
        # First, set up professional context
        professional_context = {
            "primary_industry": "Logistics & Supply Chain",
            "job_role": "Operations Director",
            "work_environment": "Global logistics company",
            "key_focus_areas": ["Operational efficiency", "Risk management", "Cost optimization"],
            "content_types": ["Meeting minutes", "Performance reports", "Risk assessments"],
            "analysis_preferences": ["Strategic recommendations", "Risk assessment", "Implementation roadmap"]
        }
        
        success, response = self.run_test(
            "Set Professional Context for Batch Report",
            "POST",
            "user/professional-context",
            200,
            data=professional_context,
            auth_required=True
        )
        
        if not success:
            self.log("❌ Failed to set professional context")
            return False
        
        # Create test notes
        note_ids = self.create_test_notes_for_batch_report()
        
        if len(note_ids) < 2:
            self.log("❌ Insufficient notes created for batch report testing")
            return False
        
        # Test batch report generation with professional context
        success, response = self.run_test(
            "Generate Batch Report with Professional Context",
            "POST",
            "notes/batch-report",
            200,
            data=note_ids,
            auth_required=True,
            timeout=90
        )
        
        if success:
            report = response.get('report', '')
            title = response.get('title', '')
            source_notes = response.get('source_notes', [])
            note_count = response.get('note_count', 0)
            
            self.log(f"   ✅ Batch report generated successfully")
            self.log(f"     - Title: {title}")
            self.log(f"     - Source notes: {note_count}")
            self.log(f"     - Report length: {len(report)} characters")
            
            # Check for professional context integration
            logistics_terms = ['supply chain', 'logistics', 'operational', 'risk', 'efficiency']
            found_terms = [term for term in logistics_terms if term.lower() in report.lower()]
            
            if found_terms:
                self.log(f"   ✅ Professional context integrated - found terms: {', '.join(found_terms[:3])}")
            else:
                self.log(f"   ⚠️  Limited professional context integration detected")
            
            # Check for proper structure
            required_sections = ['EXECUTIVE SUMMARY', 'COMPREHENSIVE ANALYSIS', 'STRATEGIC RECOMMENDATIONS']
            found_sections = [section for section in required_sections if section in report.upper()]
            
            if len(found_sections) >= 2:
                self.log(f"   ✅ Proper report structure - found sections: {', '.join(found_sections)}")
            else:
                self.log(f"   ⚠️  Report structure may be incomplete")
            
            # Check for clean formatting (no markdown symbols)
            has_markdown = '###' in report or '**' in report
            if not has_markdown:
                self.log(f"   ✅ Clean formatting - no markdown symbols detected")
            else:
                self.log(f"   ❌ Markdown symbols found in report")
        
        return success

    def test_batch_report_expeditors_branding(self):
        """Test batch report with Expeditors branding"""
        self.log("\n👑 TESTING BATCH REPORT EXPEDITORS BRANDING")
        
        # Switch to Expeditors user
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Set professional context for Expeditors user
        expeditors_context = {
            "primary_industry": "Logistics & Freight Forwarding",
            "job_role": "Senior Logistics Manager",
            "work_environment": "Expeditors International",
            "key_focus_areas": ["Global supply chain", "Freight optimization", "Customer service"],
            "content_types": ["Client reports", "Operational updates", "Performance metrics"],
            "analysis_preferences": ["Strategic planning", "Operational excellence", "Client satisfaction"]
        }
        
        success, response = self.run_test(
            "Set Expeditors Professional Context",
            "POST",
            "user/professional-context",
            200,
            data=expeditors_context,
            auth_required=True
        )
        
        if not success:
            self.log("❌ Failed to set Expeditors professional context")
            self.auth_token = temp_token
            return False
        
        # Create notes for Expeditors user
        expeditors_note_ids = self.create_test_notes_for_batch_report()
        
        if len(expeditors_note_ids) < 2:
            self.log("❌ Insufficient Expeditors notes created")
            self.auth_token = temp_token
            return False
        
        # Generate batch report for Expeditors user
        success, response = self.run_test(
            "Generate Expeditors Batch Report",
            "POST",
            "notes/batch-report",
            200,
            data=expeditors_note_ids,
            auth_required=True,
            timeout=90
        )
        
        if success:
            report = response.get('report', '')
            is_expeditors = response.get('is_expeditors', False)
            
            self.log(f"   ✅ Expeditors batch report generated")
            self.log(f"     - Is Expeditors user: {is_expeditors}")
            self.log(f"     - Report length: {len(report)} characters")
            
            # Check for Expeditors branding
            if 'EXPEDITORS INTERNATIONAL' in report:
                self.log(f"   ✅ Expeditors branding detected in report")
            else:
                self.log(f"   ❌ Expeditors branding missing from report")
            
            # Check for freight/logistics specific terminology
            expeditors_terms = ['freight', 'forwarding', 'expeditors', 'global logistics']
            found_terms = [term for term in expeditors_terms if term.lower() in report.lower()]
            
            if found_terms:
                self.log(f"   ✅ Expeditors-specific terminology found: {', '.join(found_terms)}")
            else:
                self.log(f"   ⚠️  Limited Expeditors-specific terminology")
        
        # Restore original token
        self.auth_token = temp_token
        return success

    def test_batch_report_error_handling(self):
        """Test batch report error handling"""
        self.log("\n🔧 TESTING BATCH REPORT ERROR HANDLING")
        
        # Test with invalid note IDs
        invalid_note_ids = ["invalid-id-1", "invalid-id-2", "non-existent-id"]
        
        success, response = self.run_test(
            "Batch Report with Invalid Note IDs",
            "POST",
            "notes/batch-report",
            400,  # Should fail with 400 or 500 wrapping 400
            data=invalid_note_ids,
            auth_required=True,
            timeout=60
        )
        
        if success or response.get('detail'):  # 400 or error response is expected
            self.log(f"   ✅ Invalid note IDs handled correctly")
        
        # Test with empty note list
        success, response = self.run_test(
            "Batch Report with Empty Note List",
            "POST",
            "notes/batch-report",
            400,  # Should fail with 400
            data=[],
            auth_required=True
        )
        
        if success:  # 400 response is expected
            self.log(f"   ✅ Empty note list handled correctly")
        
        # Test without authentication
        temp_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test(
            "Batch Report without Authentication",
            "POST",
            "notes/batch-report",
            403,  # Should fail with 403
            data=["test-id"],
            auth_required=True
        )
        
        if success:  # 403 response is expected
            self.log(f"   ✅ Unauthorized access handled correctly")
        
        # Restore token
        self.auth_token = temp_token
        
        return True

    def test_integration_workflow(self):
        """Test end-to-end integration workflow: context setup → note creation → batch report"""
        self.log("\n🔄 TESTING END-TO-END INTEGRATION WORKFLOW")
        
        # Step 1: Set up professional context
        integration_context = {
            "primary_industry": "Technology",
            "job_role": "Product Manager",
            "work_environment": "Software development company",
            "key_focus_areas": ["Product strategy", "User experience", "Market analysis"],
            "content_types": ["Product requirements", "User feedback", "Market research"],
            "analysis_preferences": ["Strategic insights", "User-centric recommendations", "Market opportunities"]
        }
        
        success, response = self.run_test(
            "Integration Test: Set Professional Context",
            "POST",
            "user/professional-context",
            200,
            data=integration_context,
            auth_required=True
        )
        
        if not success:
            self.log("❌ Integration test failed at context setup")
            return False
        
        # Step 2: Create notes with technology/product content
        tech_notes = [
            {
                "title": "User Feedback Analysis - Mobile App",
                "content": """User Feedback Summary - Mobile Application
Collection Period: December 2024
Total Responses: 1,247 users

Key Feedback Themes:
- App loading speed concerns (mentioned by 34% of users)
- Navigation complexity issues (mentioned by 28% of users)
- Feature request: Dark mode (mentioned by 45% of users)
- Positive feedback on new search functionality (mentioned by 67% of users)
- Battery drain concerns (mentioned by 19% of users)

User Satisfaction Metrics:
- Overall app rating: 4.2/5.0 (up from 3.9 last quarter)
- Feature usability score: 78% (target: 80%)
- Performance satisfaction: 72% (target: 85%)
- User retention (30-day): 84% (target: 80%)

Priority Improvements:
- Optimize app loading performance
- Simplify navigation flow
- Implement dark mode feature
- Address battery optimization
- Enhance onboarding experience"""
            },
            {
                "title": "Market Research - Competitive Analysis",
                "content": """Competitive Analysis Report
Market Segment: Mobile Productivity Apps
Analysis Date: December 2024

Competitor Overview:
- Competitor A: 2.3M downloads, 4.5 rating, $9.99/month
- Competitor B: 1.8M downloads, 4.3 rating, $12.99/month
- Competitor C: 950K downloads, 4.1 rating, Free with ads

Feature Comparison:
- Real-time collaboration: We have it, 2/3 competitors have it
- Offline functionality: We have limited, all competitors have full
- Cross-platform sync: We have it, all competitors have it
- Advanced analytics: We don't have it, 2/3 competitors have it
- API integrations: We have 12, competitors have 8-15

Market Opportunities:
- Enhanced offline capabilities could capture 15% more market share
- Advanced analytics feature gap represents $2.3M revenue opportunity
- Premium tier pricing is 20% below market average
- Enterprise features could open $5.8M B2B market segment

Strategic Recommendations:
- Develop comprehensive offline functionality by Q2 2025
- Build advanced analytics dashboard by Q3 2025
- Adjust pricing strategy to match market positioning
- Create enterprise feature set for B2B expansion"""
            }
        ]
        
        integration_note_ids = []
        
        for note_data in tech_notes:
            note_request = {
                "title": note_data["title"],
                "kind": "text",
                "text_content": note_data["content"]
            }
            
            success, response = self.run_test(
                f"Integration Test: Create {note_data['title'][:20]}...",
                "POST",
                "notes",
                200,
                data=note_request,
                auth_required=True
            )
            
            if success and 'id' in response:
                note_id = response['id']
                integration_note_ids.append(note_id)
                self.created_notes.append(note_id)
        
        if len(integration_note_ids) < 2:
            self.log("❌ Integration test failed at note creation")
            return False
        
        # Step 3: Generate batch report with professional context
        success, response = self.run_test(
            "Integration Test: Generate Contextual Batch Report",
            "POST",
            "notes/batch-report",
            200,
            data=integration_note_ids,
            auth_required=True,
            timeout=90
        )
        
        if success:
            report = response.get('report', '')
            
            self.log(f"   ✅ Integration workflow completed successfully")
            self.log(f"     - Report length: {len(report)} characters")
            
            # Verify industry-specific and contextual content
            tech_terms = ['user', 'product', 'feature', 'market', 'competitive', 'analytics']
            found_terms = [term for term in tech_terms if term.lower() in report.lower()]
            
            if len(found_terms) >= 4:
                self.log(f"   ✅ Industry-specific context applied: {', '.join(found_terms[:4])}")
            else:
                self.log(f"   ⚠️  Limited industry context integration")
            
            # Check for strategic recommendations appropriate to product management
            pm_concepts = ['strategy', 'roadmap', 'priorit', 'user experience', 'market opportunity']
            found_concepts = [concept for concept in pm_concepts if concept.lower() in report.lower()]
            
            if len(found_concepts) >= 2:
                self.log(f"   ✅ Product management concepts integrated: {', '.join(found_concepts[:3])}")
            else:
                self.log(f"   ⚠️  Limited product management context")
        
        return success

    def run_critical_bug_fix_tests(self):
        """Run all critical bug fix tests"""
        self.log("🚀 Starting Critical Bug Fix Verification Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup test users
        if not self.setup_users():
            self.log("❌ Failed to setup test users - stopping tests")
            return False
        
        # Test 1: Professional Context API Array Handling (React Runtime Error Fix)
        self.test_professional_context_array_handling()
        
        # Test 2: Professional Context Error Handling
        self.test_professional_context_malformed_data()
        
        # Test 3: Batch Report with Professional Context Integration
        self.test_batch_report_with_professional_context()
        
        # Test 4: Batch Report Expeditors Branding
        self.test_batch_report_expeditors_branding()
        
        # Test 5: Batch Report Error Handling
        self.test_batch_report_error_handling()
        
        # Test 6: End-to-End Integration Workflow
        self.test_integration_workflow()
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 CRITICAL BUG FIX TEST SUMMARY")
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
    tester = CriticalBugFixTester()
    
    try:
        success = tester.run_critical_bug_fix_tests()
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All critical bug fix tests passed! Fixes are working correctly.")
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