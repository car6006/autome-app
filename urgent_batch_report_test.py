#!/usr/bin/env python3
"""
URGENT: Batch Report Generation Failure Investigation
Focused test for the specific batch report issue reported by the user
"""

import requests
import sys
import json
import time
from datetime import datetime

class UrgentBatchReportTester:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.expeditors_token = None
        
        # Fixed username format (no underscores)
        timestamp = int(time.time())
        self.test_user_data = {
            "email": f"batchtest{timestamp}@example.com",
            "username": f"batchuser{timestamp}",
            "password": "TestPassword123!",
            "first_name": "Batch",
            "last_name": "Tester"
        }
        self.expeditors_user_data = {
            "email": f"batchexp{timestamp}@expeditors.com",
            "username": f"batchexp{timestamp}",
            "password": "ExpeditorsPass123!",
            "first_name": "Batch",
            "last_name": "Expeditors"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=120, auth_required=False):
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

    def setup_authentication(self):
        """Setup authentication"""
        self.log("🔐 Setting up authentication...")
        
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
            self.log(f"   Regular user registered: {'✅' if self.auth_token else '❌'}")
        
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
            self.log(f"   Expeditors user registered: {'✅' if self.expeditors_token else '❌'}")
        
        return self.auth_token is not None

    def create_notes_with_content(self):
        """Create multiple notes with content for batch testing"""
        self.log("📝 Creating notes with content...")
        
        notes_data = [
            {
                "title": "Supply Chain Meeting Minutes",
                "kind": "text",
                "text_content": """Meeting: Q4 Supply Chain Planning
Date: December 19, 2024
Attendees: Supply Chain Director, Logistics Manager, Operations Lead

Key Discussion Points:
- Reviewed freight cost increases from Asia-Pacific routes (15% YoY)
- Analyzed carrier performance metrics for Q3 (98.2% on-time delivery)
- Discussed peak season capacity constraints and mitigation strategies
- Evaluated new distribution center locations in Memphis and Atlanta

Strategic Decisions:
- Implement dynamic routing optimization to reduce costs by 8-12%
- Negotiate long-term contracts with top 3 carriers for rate stability
- Increase safety stock levels by 20% for critical components
- Deploy real-time tracking system across all shipments by Q1 2025

Action Items:
- Procurement team to finalize carrier contracts by December 30, 2024
- Operations to coordinate Memphis DC setup by February 2025
- IT department to deploy tracking system by January 15, 2025

Risk Assessment:
- Port congestion may impact delivery schedules (High probability)
- Currency fluctuations affecting freight rates (Medium impact)
- Limited warehouse capacity during peak season (High impact)

Financial Impact:
- Expected cost savings: $2.3M annually from optimization initiatives
- Investment required: $850K for technology and infrastructure
- ROI timeline: 8-10 months payback period"""
            },
            {
                "title": "Client Issue Analysis Report",
                "kind": "text",
                "text_content": """Client: Global Electronics Manufacturer
Issue Category: Supply Chain Disruption
Severity: Critical
Date Reported: December 18, 2024

Problem Summary:
Client experiencing significant delays in component deliveries from Southeast Asia suppliers, impacting production schedules for Q1 2025 product launches.

Root Cause Analysis:
1. Primary supplier in Vietnam experiencing labor shortages (40% capacity reduction)
2. Secondary supplier in Thailand facing raw material shortages
3. Backup supplier in Malaysia has quality control issues (15% rejection rate)
4. Ocean freight capacity reduced due to vessel repositioning

Impact Assessment:
- Production delays: 3-4 weeks for critical components
- Revenue at risk: $12.5M for Q1 product launches
- Customer satisfaction impact: Potential loss of 2 major retail partnerships
- Inventory carrying costs: Additional $800K in safety stock requirements

Immediate Actions Taken:
- Activated emergency air freight for critical components (cost: $450K)
- Negotiated expedited production with alternative suppliers
- Implemented daily status calls with all suppliers and logistics partners
- Coordinated with client's production planning team for schedule adjustments

Recommended Solutions:
1. Diversify supplier base across 4-5 countries to reduce concentration risk
2. Implement supplier performance monitoring with real-time visibility
3. Establish strategic inventory buffers at key distribution points
4. Develop contingency routing plans for critical shipments
5. Create supplier development program to improve capacity and quality"""
            },
            {
                "title": "Operations Performance Dashboard",
                "kind": "text",
                "text_content": """Operations Performance Report - November 2024
Report Period: November 1-30, 2024
Generated: December 19, 2024

Key Performance Indicators:
- On-time delivery rate: 96.8% (Target: 95%)
- Cost per shipment: $847 (Budget: $875)
- Customer satisfaction score: 4.6/5.0 (Target: 4.5)
- Damage rate: 0.12% (Target: <0.15%)
- Invoice accuracy: 99.4% (Target: 99%)

Volume Metrics:
- Total shipments processed: 15,847 units
- Air freight: 3,245 shipments (20.5%)
- Ocean freight: 9,876 shipments (62.3%)
- Ground transportation: 2,726 shipments (17.2%)
- Average shipment value: $23,450

Operational Highlights:
- Successfully managed Black Friday peak season surge (35% volume increase)
- Implemented new warehouse management system in Chicago facility
- Completed carrier performance reviews and contract renewals
- Launched customer self-service portal with 78% adoption rate

Challenges and Issues:
- Weather-related delays in Northeast region (2.3% of shipments affected)
- Customs clearance delays for electronics imports (average 1.2 days)
- Warehouse capacity constraints during peak periods
- Driver shortage impacting last-mile delivery in rural areas

Financial Performance:
- Revenue: $37.2M (vs. budget $36.8M)
- Operating margin: 12.4% (vs. target 12.0%)
- Cost savings initiatives: $1.8M YTD
- Investment in technology and infrastructure: $2.1M"""
            }
        ]
        
        created_note_ids = []
        
        for i, note_data in enumerate(notes_data, 1):
            success, response = self.run_test(
                f"Create Note {i} with Content",
                "POST",
                "notes",
                200,
                data=note_data,
                auth_required=True
            )
            
            if success and 'id' in response:
                note_id = response['id']
                created_note_ids.append(note_id)
                self.created_notes.append(note_id)
                self.log(f"   Created note {i}: {note_id} (Status: {response.get('status', 'N/A')})")
            else:
                self.log(f"   ❌ Failed to create note {i}")
        
        return created_note_ids

    def test_batch_report_generation(self, note_ids, user_type="Regular"):
        """Test the actual batch report generation that's reportedly failing"""
        self.log(f"🚨 CRITICAL TEST: Batch Report Generation ({user_type} User)")
        self.log(f"   Testing with {len(note_ids)} notes")
        
        # This is the exact endpoint that's reportedly failing
        success, response = self.run_test(
            f"Generate Batch Report ({user_type})",
            "POST",
            "notes/batch-report",
            200,
            data=note_ids,  # List of note IDs
            auth_required=True,
            timeout=120  # Extended timeout for AI processing
        )
        
        if success:
            report_content = response.get('report', '')
            source_notes = response.get('source_notes', [])
            note_count = response.get('note_count', 0)
            is_expeditors = response.get('is_expeditors', False)
            
            self.log(f"   ✅ BATCH REPORT GENERATED SUCCESSFULLY!")
            self.log(f"   Report length: {len(report_content)} characters")
            self.log(f"   Source notes processed: {note_count}")
            self.log(f"   Expeditors branding: {'Yes' if is_expeditors else 'No'}")
            
            # Analyze report quality
            if len(report_content) > 2000:
                self.log(f"   ✅ Substantial report content (>2000 chars)")
            else:
                self.log(f"   ⚠️  Report content may be brief ({len(report_content)} chars)")
            
            # Check for expected sections
            expected_sections = ['EXECUTIVE SUMMARY', 'COMPREHENSIVE ANALYSIS', 'STRATEGIC RECOMMENDATIONS']
            found_sections = [section for section in expected_sections if section in report_content.upper()]
            
            if len(found_sections) >= 2:
                self.log(f"   ✅ Professional structure: {', '.join(found_sections)}")
            else:
                self.log(f"   ⚠️  Limited professional structure detected")
            
            # Check for clean formatting
            has_markdown = any(symbol in report_content for symbol in ['###', '**', '```'])
            if not has_markdown:
                self.log(f"   ✅ Clean formatting (no markdown symbols)")
            else:
                self.log(f"   ⚠️  Markdown symbols detected")
            
            return True, response
        else:
            self.log(f"   ❌ BATCH REPORT GENERATION FAILED!")
            self.log(f"   This confirms the user's report of batch report failures")
            return False, {}

    def test_professional_context_integration(self):
        """Test if professional context integration is causing issues"""
        self.log("🎯 Testing Professional Context Integration...")
        
        # Setup professional context
        context_data = {
            "primary_industry": "Logistics & Supply Chain",
            "job_role": "Supply Chain Manager",
            "work_environment": "Global freight forwarding company",
            "key_focus_areas": ["Cost optimization", "Supply chain risks", "Operational efficiency"],
            "content_types": ["Meeting minutes", "Operational reports"],
            "analysis_preferences": ["Strategic recommendations", "Risk assessment"]
        }
        
        success, response = self.run_test(
            "Setup Professional Context",
            "POST",
            "user/professional-context",
            200,
            data=context_data,
            auth_required=True
        )
        
        if success:
            self.log("   ✅ Professional context setup successful")
            
            # Verify retrieval
            success2, response2 = self.run_test(
                "Retrieve Professional Context",
                "GET",
                "user/professional-context",
                200,
                auth_required=True
            )
            
            if success2:
                self.log("   ✅ Professional context retrieval successful")
                return True
            else:
                self.log("   ❌ Professional context retrieval failed")
                return False
        else:
            self.log("   ❌ Professional context setup failed")
            return False

    def test_ai_integration_health(self):
        """Test if AI integration (OpenAI) is working"""
        self.log("🤖 Testing AI Integration Health...")
        
        # Create a simple note for AI testing
        test_note_data = {
            "title": "AI Integration Test",
            "kind": "text",
            "text_content": "This is a test note to verify AI integration is working properly for batch report generation."
        }
        
        success, response = self.run_test(
            "Create AI Test Note",
            "POST",
            "notes",
            200,
            data=test_note_data,
            auth_required=True
        )
        
        if not success or 'id' not in response:
            self.log("   ❌ Could not create test note")
            return False
        
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Test AI chat functionality
        success, response = self.run_test(
            "Test AI Chat",
            "POST",
            f"notes/{note_id}/ai-chat",
            200,
            data={"question": "Provide a brief summary of this content"},
            auth_required=True,
            timeout=60
        )
        
        if success:
            ai_response = response.get('response', '')
            if len(ai_response) > 50:
                self.log("   ✅ AI integration working properly")
                return True
            else:
                self.log("   ⚠️  AI response too brief - may indicate issues")
                return False
        else:
            self.log("   ❌ AI integration failed - this may be the root cause!")
            return False

    def test_expeditors_batch_reports(self, note_ids):
        """Test batch reports specifically for Expeditors users"""
        if not self.expeditors_token:
            self.log("   ⚠️  No Expeditors token available")
            return False
        
        # Switch to Expeditors token
        temp_token = self.auth_token
        self.auth_token = self.expeditors_token
        
        # Setup Expeditors professional context
        expeditors_context = {
            "primary_industry": "Logistics & Supply Chain",
            "job_role": "Logistics Manager",
            "work_environment": "Expeditors International",
            "key_focus_areas": ["Freight forwarding", "Supply chain optimization", "Client service"],
            "content_types": ["Client communications", "Operational reports", "Meeting minutes"],
            "analysis_preferences": ["Strategic recommendations", "Risk assessment", "Action items"]
        }
        
        success, response = self.run_test(
            "Setup Expeditors Professional Context",
            "POST",
            "user/professional-context",
            200,
            data=expeditors_context,
            auth_required=True
        )
        
        if success:
            # Test batch report with Expeditors context
            success, response = self.test_batch_report_generation(note_ids, "Expeditors")
        
        # Restore original token
        self.auth_token = temp_token
        
        return success

    def run_urgent_investigation(self):
        """Run the urgent batch report failure investigation"""
        self.log("🚨 URGENT: Batch Report Generation Failure Investigation")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # 1. Setup authentication
        if not self.setup_authentication():
            self.log("❌ CRITICAL: Authentication setup failed")
            return False
        
        # 2. Test AI integration health first
        ai_healthy = self.test_ai_integration_health()
        if not ai_healthy:
            self.log("🎯 LIKELY ROOT CAUSE: AI integration issues")
        
        # 3. Test professional context integration
        context_healthy = self.test_professional_context_integration()
        if not context_healthy:
            self.log("🎯 LIKELY ROOT CAUSE: Professional context integration issues")
        
        # 4. Create notes with content
        note_ids = self.create_notes_with_content()
        if len(note_ids) < 2:
            self.log("❌ CRITICAL: Could not create enough notes for batch testing")
            return False
        
        # 5. Test batch report generation (the main issue)
        self.log("\n🚨 TESTING THE REPORTED FAILING FUNCTIONALITY:")
        regular_success, regular_response = self.test_batch_report_generation(note_ids, "Regular")
        
        # 6. Test Expeditors batch reports
        expeditors_success = self.test_expeditors_batch_reports(note_ids)
        
        # 7. Analyze results and provide diagnosis
        self.log("\n🔍 DIAGNOSIS:")
        
        if not regular_success and not expeditors_success:
            self.log("❌ CONFIRMED: Batch report generation is FAILING for ALL users")
            self.log("   This matches the user's report exactly!")
            
            if not ai_healthy:
                self.log("🎯 PRIMARY ROOT CAUSE: AI Integration (OpenAI API) Issues")
                self.log("   - Check OpenAI API key configuration in backend/.env")
                self.log("   - Verify API quota and billing status")
                self.log("   - Check network connectivity to OpenAI services")
            elif not context_healthy:
                self.log("🎯 PRIMARY ROOT CAUSE: Professional Context Integration Issues")
                self.log("   - Recent professional context changes may have broken batch reports")
                self.log("   - Check ai_context_processor.py for errors")
            else:
                self.log("🎯 PRIMARY ROOT CAUSE: Unknown - requires deeper investigation")
                self.log("   - Check server logs for detailed error messages")
                self.log("   - Verify batch report endpoint implementation")
        
        elif regular_success and not expeditors_success:
            self.log("⚠️  Batch reports working for regular users, failing for Expeditors")
            self.log("🎯 ROOT CAUSE: Expeditors-specific processing issues")
        
        elif not regular_success and expeditors_success:
            self.log("⚠️  Batch reports working for Expeditors, failing for regular users")
            self.log("🎯 ROOT CAUSE: Regular user processing issues")
        
        else:
            self.log("✅ Batch reports are working for both user types")
            self.log("🤔 The reported failures may be intermittent or context-specific")
            self.log("   - Check for specific conditions that trigger failures")
            self.log("   - Monitor for intermittent AI API issues")
        
        return regular_success or expeditors_success

    def print_summary(self):
        """Print investigation summary"""
        self.log("\n" + "="*70)
        self.log("📊 URGENT BATCH REPORT FAILURE INVESTIGATION SUMMARY")
        self.log("="*70)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nTest notes created: {len(self.created_notes)}")
        
        self.log("\n🎯 IMMEDIATE ACTION ITEMS:")
        if self.tests_passed < self.tests_run:
            self.log("1. ❌ CRITICAL: Batch report functionality is confirmed broken")
            self.log("2. 🔧 Check OpenAI API key and quota status immediately")
            self.log("3. 🔧 Review recent changes to professional context integration")
            self.log("4. 🔧 Check server logs for detailed error messages")
            self.log("5. 🔧 Verify ai_context_processor.py implementation")
        else:
            self.log("1. ✅ Batch report functionality appears to be working")
            self.log("2. 🔍 Investigate specific conditions that trigger user-reported failures")
            self.log("3. 🔍 Monitor for intermittent issues")
        
        self.log("="*70)
        
        return self.tests_passed == self.tests_run

def main():
    """Main investigation execution"""
    tester = UrgentBatchReportTester()
    
    try:
        success = tester.run_urgent_investigation()
        tester.print_summary()
        
        if success:
            print("\n🎉 Batch report functionality is working!")
            print("   The user's reported issues may be intermittent or context-specific.")
            return 0
        else:
            print(f"\n🚨 CONFIRMED: Batch report generation is FAILING!")
            print("   This matches the user's report of 'Failed to generate batch report' errors.")
            print("   Check the diagnosis above for root cause analysis.")
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