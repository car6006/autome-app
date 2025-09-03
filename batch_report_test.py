#!/usr/bin/env python3

"""
Enhanced Batch Report Export Functionality Testing
Testing the /api/notes/batch-report endpoint with Word and PDF support
Focus on AI-powered comprehensive business analysis and professional formatting
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BatchReportExportTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_user_email = f"batchtest_{uuid.uuid4().hex[:8]}@testdomain.com"
        self.test_user_password = "TestPass123!"
        self.test_notes = []
        self.results = []
        
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = httpx.AsyncClient(timeout=60.0)
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.aclose()
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            response = await self.session.post(f"{API_BASE}/auth/register", json={
                "email": self.test_user_email,
                "username": f"batchuser_{uuid.uuid4().hex[:8]}",
                "password": self.test_user_password,
                "name": "Batch Test User"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Test user registered: {self.test_user_email}")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ User registration error: {e}")
            return False
    
    async def create_test_notes(self):
        """Create multiple test notes with different content types"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test note 1: Meeting transcript
        note1_data = {
            "title": "Q4 Strategy Meeting - Sales Performance Review",
            "kind": "text",
            "text_content": """
            Meeting Date: January 27, 2025
            Attendees: Sarah Johnson (VP Sales), Mike Chen (Regional Manager), Lisa Rodriguez (Analytics Lead)
            
            AGENDA ITEMS DISCUSSED:
            
            1. Q4 Sales Performance Analysis
            - Total revenue: $2.4M (8% above target)
            - New customer acquisition: 145 accounts
            - Customer retention rate: 94%
            - Top performing regions: West Coast, Northeast
            
            2. Market Expansion Opportunities
            - Identified potential in healthcare sector
            - Competitor analysis shows 15% market share opportunity
            - Recommended investment in specialized sales team
            
            3. Technology Integration Initiatives
            - CRM system upgrade scheduled for Q1 2025
            - Sales automation tools showing 20% efficiency gains
            - Mobile app adoption at 78% among field sales team
            
            ACTION ITEMS:
            - Sarah to prepare healthcare sector proposal by Feb 15
            - Mike to coordinate CRM training sessions
            - Lisa to develop performance metrics dashboard
            
            NEXT MEETING: February 10, 2025
            """
        }
        
        # Test note 2: Project status update
        note2_data = {
            "title": "Digital Transformation Project Update - Phase 2",
            "kind": "text", 
            "text_content": """
            Project Status Report - January 27, 2025
            Project Manager: David Kim
            Phase: 2 of 4 (Implementation)
            
            CURRENT STATUS:
            - Overall progress: 65% complete
            - Budget utilization: $1.8M of $2.5M allocated
            - Timeline: On track for March 2025 completion
            
            COMPLETED MILESTONES:
            1. Infrastructure Setup (100%)
            - Cloud migration completed
            - Security protocols implemented
            - Backup systems operational
            
            2. User Training Program (85%)
            - 340 employees trained across 5 departments
            - Training materials localized for 3 regions
            - Feedback scores averaging 4.2/5.0
            
            CURRENT CHALLENGES:
            - Integration delays with legacy accounting system
            - Resource constraints in IT support team
            - Change management resistance in operations department
            
            RISK MITIGATION:
            - Hired 2 additional integration specialists
            - Implemented phased rollout approach
            - Enhanced communication strategy for stakeholder buy-in
            
            UPCOMING DELIVERABLES:
            - System integration testing (Week 1-2 Feb)
            - User acceptance testing (Week 3-4 Feb)
            - Go-live preparation (Week 1 Mar)
            """
        }
        
        # Test note 3: Customer feedback analysis
        note3_data = {
            "title": "Customer Satisfaction Survey Results - Q4 2024",
            "kind": "text",
            "text_content": """
            Survey Period: October - December 2024
            Response Rate: 68% (2,040 responses from 3,000 customers)
            Analysis Date: January 25, 2025
            
            OVERALL SATISFACTION METRICS:
            - Net Promoter Score (NPS): 72 (+8 from Q3)
            - Customer Satisfaction Score (CSAT): 4.3/5.0
            - Customer Effort Score (CES): 3.8/5.0
            
            KEY FINDINGS BY CATEGORY:
            
            1. Product Quality (4.5/5.0)
            - 89% rate product reliability as excellent
            - Feature completeness scores improved 12%
            - Innovation perception increased significantly
            
            2. Customer Service (4.1/5.0)
            - Response time satisfaction: 85%
            - Issue resolution rate: 92%
            - Agent knowledge scores: 4.2/5.0
            
            3. Value for Money (3.9/5.0)
            - Pricing competitiveness concerns noted
            - 76% see clear ROI from our solutions
            - Upgrade path clarity needs improvement
            
            CUSTOMER SEGMENTS ANALYSIS:
            - Enterprise clients: Highest satisfaction (4.6/5.0)
            - Mid-market: Strong performance (4.2/5.0)
            - Small business: Room for improvement (3.8/5.0)
            
            IMPROVEMENT OPPORTUNITIES:
            - Streamline onboarding process for small businesses
            - Enhance self-service portal capabilities
            - Develop more flexible pricing options
            - Improve documentation and training resources
            
            RECOMMENDED ACTIONS:
            1. Launch small business success program
            2. Invest in customer portal enhancements
            3. Review pricing strategy for competitive positioning
            4. Expand knowledge base and tutorial content
            """
        }
        
        test_notes_data = [note1_data, note2_data, note3_data]
        
        for i, note_data in enumerate(test_notes_data, 1):
            try:
                response = await self.session.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code == 200:
                    note_info = response.json()
                    self.test_notes.append(note_info["id"])
                    print(f"✅ Test note {i} created: {note_data['title'][:50]}...")
                else:
                    print(f"❌ Failed to create test note {i}: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error creating test note {i}: {e}")
                return False
        
        return len(self.test_notes) == 3
    
    async def test_batch_report_txt_format(self):
        """Test batch report generation in TXT format"""
        print("\n🔍 Testing Batch Report TXT Format...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = {
            "note_ids": self.test_notes,
            "title": "Q4 Business Analysis Report - TXT Format",
            "format": "txt"
        }
        
        try:
            response = await self.session.post(f"{API_BASE}/notes/batch-report", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Verify TXT format requirements
                checks = {
                    "Has content": len(content) > 1000,
                    "Contains source notes": "SOURCE NOTES:" in content,
                    "Has all note titles": all(title in content for title in ["Q4 Strategy Meeting", "Digital Transformation", "Customer Satisfaction"]),
                    "Clean formatting": "**" not in content and "###" not in content,
                    "Proper structure": "Generated:" in content and "Notes included:" in content
                }
                
                success = all(checks.values())
                self.results.append({
                    "test": "Batch Report TXT Format",
                    "success": success,
                    "details": f"Content length: {len(content)} chars, Checks: {checks}",
                    "file_size": len(content.encode('utf-8'))
                })
                
                if success:
                    print(f"✅ TXT format test passed - {len(content)} characters generated")
                else:
                    print(f"❌ TXT format test failed - Checks: {checks}")
                
                return success
            else:
                print(f"❌ TXT format request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ TXT format test error: {e}")
            return False
    
    async def test_batch_report_rtf_format(self):
        """Test batch report generation in RTF format"""
        print("\n🔍 Testing Batch Report RTF Format...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = {
            "note_ids": self.test_notes,
            "title": "Q4 Business Analysis Report - RTF Format", 
            "format": "rtf"
        }
        
        try:
            response = await self.session.post(f"{API_BASE}/notes/batch-report", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                
                # Verify RTF format requirements
                checks = {
                    "RTF header present": content.startswith("{\\rtf1"),
                    "RTF footer present": content.endswith("}"),
                    "Contains source notes": "SOURCE NOTES:" in content,
                    "Has RTF formatting": "\\par" in content and "\\bullet" in content,
                    "Proper structure": "Generated:" in content
                }
                
                success = all(checks.values())
                self.results.append({
                    "test": "Batch Report RTF Format",
                    "success": success,
                    "details": f"Content length: {len(content)} chars, Checks: {checks}",
                    "file_size": len(content.encode('utf-8'))
                })
                
                if success:
                    print(f"✅ RTF format test passed - {len(content)} characters generated")
                else:
                    print(f"❌ RTF format test failed - Checks: {checks}")
                
                return success
            else:
                print(f"❌ RTF format request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ RTF format test error: {e}")
            return False
    
    async def test_batch_report_pdf_format(self):
        """Test batch report generation in PDF format with AI analysis"""
        print("\n🔍 Testing Batch Report PDF Format with AI Analysis...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = {
            "note_ids": self.test_notes,
            "title": "Q4 Business Analysis Report - PDF Format",
            "format": "pdf"
        }
        
        try:
            response = await self.session.post(f"{API_BASE}/notes/batch-report", json=payload, headers=headers)
            
            if response.status_code == 200:
                content = response.content
                headers_dict = dict(response.headers)
                
                # Verify PDF format requirements
                checks = {
                    "PDF binary data": content.startswith(b'%PDF'),
                    "Proper content type": headers_dict.get("content-type") == "application/pdf",
                    "Content disposition": "attachment" in headers_dict.get("content-disposition", ""),
                    "Substantial content": len(content) > 5000,  # AI analysis should create substantial PDF
                    "File extension": ".pdf" in headers_dict.get("content-disposition", "")
                }
                
                success = all(checks.values())
                self.results.append({
                    "test": "Batch Report PDF Format with AI Analysis",
                    "success": success,
                    "details": f"PDF size: {len(content)} bytes, Headers: {headers_dict.get('content-type')}, Checks: {checks}",
                    "file_size": len(content)
                })
                
                if success:
                    print(f"✅ PDF format test passed - {len(content)} bytes generated with AI analysis")
                    print(f"   📄 Content-Type: {headers_dict.get('content-type')}")
                    print(f"   📎 Content-Disposition: {headers_dict.get('content-disposition')}")
                else:
                    print(f"❌ PDF format test failed - Checks: {checks}")
                
                return success
            else:
                print(f"❌ PDF format request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ PDF format test error: {e}")
            return False
    
    async def test_batch_report_docx_format(self):
        """Test batch report generation in DOCX format with AI analysis"""
        print("\n🔍 Testing Batch Report DOCX Format with AI Analysis...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = {
            "note_ids": self.test_notes,
            "title": "Q4 Business Analysis Report - DOCX Format",
            "format": "docx"
        }
        
        try:
            response = await self.session.post(f"{API_BASE}/notes/batch-report", json=payload, headers=headers)
            
            if response.status_code == 200:
                content = response.content
                headers_dict = dict(response.headers)
                
                # Verify DOCX format requirements
                checks = {
                    "DOCX binary data": content.startswith(b'PK'),  # DOCX files start with PK (ZIP format)
                    "Proper content type": headers_dict.get("content-type") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "Content disposition": "attachment" in headers_dict.get("content-disposition", ""),
                    "Substantial content": len(content) > 10000,  # AI analysis should create substantial DOCX
                    "File extension": ".docx" in headers_dict.get("content-disposition", "")
                }
                
                success = all(checks.values())
                self.results.append({
                    "test": "Batch Report DOCX Format with AI Analysis",
                    "success": success,
                    "details": f"DOCX size: {len(content)} bytes, Headers: {headers_dict.get('content-type')}, Checks: {checks}",
                    "file_size": len(content)
                })
                
                if success:
                    print(f"✅ DOCX format test passed - {len(content)} bytes generated with AI analysis")
                    print(f"   📄 Content-Type: {headers_dict.get('content-type')}")
                    print(f"   📎 Content-Disposition: {headers_dict.get('content-disposition')}")
                else:
                    print(f"❌ DOCX format test failed - Checks: {checks}")
                
                return success
            else:
                print(f"❌ DOCX format request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ DOCX format test error: {e}")
            return False
    
    async def test_expeditors_branding(self):
        """Test Expeditors branding for @expeditors.com users"""
        print("\n🔍 Testing Expeditors Branding...")
        
        # Create Expeditors test user
        expeditors_email = f"expeditorstest_{uuid.uuid4().hex[:8]}@expeditors.com"
        expeditors_password = "ExpTest123!"
        
        try:
            # Register Expeditors user
            response = await self.session.post(f"{API_BASE}/auth/register", json={
                "email": expeditors_email,
                "username": f"expuser_{uuid.uuid4().hex[:8]}",
                "password": expeditors_password,
                "name": "Expeditors Test User"
            })
            
            if response.status_code != 200:
                print(f"❌ Expeditors user registration failed: {response.status_code}")
                return False
            
            expeditors_token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {expeditors_token}"}
            
            # Create a test note for Expeditors user
            note_data = {
                "title": "Expeditors Logistics Analysis",
                "kind": "text",
                "text_content": "Supply chain optimization analysis for Q4 2024 freight operations."
            }
            
            note_response = await self.session.post(f"{API_BASE}/notes", json=note_data, headers=headers)
            if note_response.status_code != 200:
                print(f"❌ Failed to create Expeditors test note")
                return False
            
            expeditors_note_id = note_response.json()["id"]
            
            # Test PDF with Expeditors branding
            payload = {
                "note_ids": [expeditors_note_id],
                "title": "Expeditors Business Analysis",
                "format": "pdf"
            }
            
            response = await self.session.post(f"{API_BASE}/notes/batch-report", json=payload, headers=headers)
            
            if response.status_code == 200:
                content = response.content
                
                # Expeditors PDFs should be larger due to branding
                checks = {
                    "PDF generated": content.startswith(b'%PDF'),
                    "Enhanced size": len(content) > 8000,  # Branding should increase file size
                    "Proper headers": response.headers.get("content-type") == "application/pdf"
                }
                
                success = all(checks.values())
                self.results.append({
                    "test": "Expeditors Branding (PDF)",
                    "success": success,
                    "details": f"Expeditors PDF size: {len(content)} bytes, Checks: {checks}",
                    "file_size": len(content)
                })
                
                if success:
                    print(f"✅ Expeditors branding test passed - Enhanced PDF with {len(content)} bytes")
                else:
                    print(f"❌ Expeditors branding test failed - Checks: {checks}")
                
                return success
            else:
                print(f"❌ Expeditors PDF generation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Expeditors branding test error: {e}")
            return False
    
    async def test_ai_content_quality(self):
        """Test AI-powered content quality and business analysis"""
        print("\n🔍 Testing AI Content Quality and Business Analysis...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = {
            "note_ids": self.test_notes,
            "title": "AI Quality Analysis Test",
            "format": "professional"  # This should return the AI analysis content
        }
        
        try:
            response = await self.session.post(f"{API_BASE}/notes/batch-report", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                report_content = data.get("report", "")
                
                # Check AI content quality indicators
                business_terms = [
                    "strategic", "analysis", "recommendation", "insight", "executive",
                    "performance", "opportunity", "risk", "implementation", "business"
                ]
                
                strategic_indicators = [
                    "EXECUTIVE SUMMARY", "KEY INSIGHTS", "RECOMMENDATIONS", 
                    "ACTION ITEMS", "STRATEGIC", "ANALYSIS"
                ]
                
                checks = {
                    "Substantial content": len(report_content) > 2000,
                    "Business language": sum(1 for term in business_terms if term.lower() in report_content.lower()) >= 5,
                    "Strategic structure": sum(1 for indicator in strategic_indicators if indicator in report_content.upper()) >= 3,
                    "Executive level": any(phrase in report_content.lower() for phrase in ["executive", "strategic", "c-level", "leadership"]),
                    "Actionable insights": any(phrase in report_content.lower() for phrase in ["recommend", "action", "implement", "strategy"]),
                    "Cross-document synthesis": "multiple" in report_content.lower() or "across" in report_content.lower()
                }
                
                success = all(checks.values())
                self.results.append({
                    "test": "AI Content Quality and Business Analysis",
                    "success": success,
                    "details": f"Content length: {len(report_content)} chars, Business terms: {sum(1 for term in business_terms if term.lower() in report_content.lower())}, Checks: {checks}",
                    "content_sample": report_content[:200] + "..." if len(report_content) > 200 else report_content
                })
                
                if success:
                    print(f"✅ AI content quality test passed - {len(report_content)} characters of strategic analysis")
                    print(f"   📊 Business terms found: {sum(1 for term in business_terms if term.lower() in report_content.lower())}")
                    print(f"   🎯 Strategic indicators: {sum(1 for indicator in strategic_indicators if indicator in report_content.upper())}")
                else:
                    print(f"❌ AI content quality test failed - Checks: {checks}")
                
                return success
            else:
                print(f"❌ AI content quality request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ AI content quality test error: {e}")
            return False
    
    async def test_complete_workflow(self):
        """Test complete workflow: Create notes → Generate batch reports → Verify completion"""
        print("\n🔍 Testing Complete Workflow...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test all formats in sequence
        formats_to_test = ["txt", "rtf", "pdf", "docx"]
        workflow_results = []
        
        for format_type in formats_to_test:
            try:
                payload = {
                    "note_ids": self.test_notes,
                    "title": f"Complete Workflow Test - {format_type.upper()}",
                    "format": format_type
                }
                
                response = await self.session.post(f"{API_BASE}/notes/batch-report", json=payload, headers=headers)
                
                if response.status_code == 200:
                    if format_type in ["pdf", "docx"]:
                        # Binary formats
                        content_size = len(response.content)
                        success = content_size > 5000
                    else:
                        # Text formats
                        data = response.json()
                        content = data.get("content", "")
                        success = len(content) > 1000
                    
                    workflow_results.append(success)
                    print(f"   ✅ {format_type.upper()} format: {'PASS' if success else 'FAIL'}")
                else:
                    workflow_results.append(False)
                    print(f"   ❌ {format_type.upper()} format: FAIL ({response.status_code})")
                    
            except Exception as e:
                workflow_results.append(False)
                print(f"   ❌ {format_type.upper()} format: ERROR ({e})")
        
        # Check if notes are marked as completed
        notes_completed = []
        for note_id in self.test_notes:
            try:
                response = await self.session.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                if response.status_code == 200:
                    note_data = response.json()
                    status = note_data.get("status", "")
                    notes_completed.append(status == "completed")
                else:
                    notes_completed.append(False)
            except:
                notes_completed.append(False)
        
        overall_success = all(workflow_results) and all(notes_completed)
        
        self.results.append({
            "test": "Complete Workflow (All Formats + Note Completion)",
            "success": overall_success,
            "details": f"Format results: {dict(zip(formats_to_test, workflow_results))}, Notes completed: {all(notes_completed)}",
            "formats_passed": sum(workflow_results),
            "notes_completed": sum(notes_completed)
        })
        
        if overall_success:
            print(f"✅ Complete workflow test passed - All {len(formats_to_test)} formats working, {sum(notes_completed)}/{len(self.test_notes)} notes marked completed")
        else:
            print(f"❌ Complete workflow test failed - Formats: {sum(workflow_results)}/{len(formats_to_test)}, Completed: {sum(notes_completed)}/{len(self.test_notes)}")
        
        return overall_success
    
    async def run_all_tests(self):
        """Run all batch report export tests"""
        print("🚀 Starting Enhanced Batch Report Export Functionality Testing")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"📧 Test User: {self.test_user_email}")
        print("="*80)
        
        try:
            await self.setup_session()
            
            # Setup phase
            if not await self.register_test_user():
                print("❌ Failed to register test user")
                return False
            
            if not await self.create_test_notes():
                print("❌ Failed to create test notes")
                return False
            
            print(f"\n✅ Setup completed - {len(self.test_notes)} test notes created")
            
            # Run all tests
            test_methods = [
                self.test_batch_report_txt_format,
                self.test_batch_report_rtf_format,
                self.test_batch_report_pdf_format,
                self.test_batch_report_docx_format,
                self.test_expeditors_branding,
                self.test_ai_content_quality,
                self.test_complete_workflow
            ]
            
            for test_method in test_methods:
                try:
                    await test_method()
                except Exception as e:
                    print(f"❌ Test {test_method.__name__} failed with error: {e}")
                    self.results.append({
                        "test": test_method.__name__,
                        "success": False,
                        "details": f"Exception: {str(e)}"
                    })
            
            # Print summary
            self.print_test_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
        finally:
            await self.cleanup_session()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 ENHANCED BATCH REPORT EXPORT TESTING SUMMARY")
        print("="*80)
        
        passed_tests = [r for r in self.results if r["success"]]
        failed_tests = [r for r in self.results if not r["success"]]
        
        print(f"✅ Tests Passed: {len(passed_tests)}/{len(self.results)}")
        print(f"❌ Tests Failed: {len(failed_tests)}/{len(self.results)}")
        print(f"📈 Success Rate: {len(passed_tests)/len(self.results)*100:.1f}%")
        
        if passed_tests:
            print(f"\n🎉 SUCCESSFUL TESTS:")
            for result in passed_tests:
                print(f"   ✅ {result['test']}")
                if 'file_size' in result:
                    print(f"      📁 File Size: {result['file_size']} bytes")
        
        if failed_tests:
            print(f"\n🚨 FAILED TESTS:")
            for result in failed_tests:
                print(f"   ❌ {result['test']}")
                print(f"      📝 Details: {result['details']}")
        
        print("\n" + "="*80)
        print("🔍 KEY FINDINGS:")
        
        # Analyze results for key insights
        format_tests = [r for r in self.results if "Format" in r["test"]]
        ai_tests = [r for r in self.results if "AI" in r["test"]]
        workflow_tests = [r for r in self.results if "Workflow" in r["test"]]
        
        if format_tests:
            format_success = sum(1 for r in format_tests if r["success"])
            print(f"   📄 Format Support: {format_success}/{len(format_tests)} formats working")
        
        if ai_tests:
            ai_success = sum(1 for r in ai_tests if r["success"])
            print(f"   🤖 AI Analysis: {ai_success}/{len(ai_tests)} AI features working")
        
        if workflow_tests:
            workflow_success = sum(1 for r in workflow_tests if r["success"])
            print(f"   🔄 Workflow: {workflow_success}/{len(workflow_tests)} end-to-end workflows working")
        
        # Overall assessment
        overall_success_rate = len(passed_tests)/len(self.results)*100
        if overall_success_rate >= 85:
            print(f"\n🎯 OVERALL ASSESSMENT: EXCELLENT - {overall_success_rate:.1f}% success rate")
            print("   The enhanced batch report export functionality is working perfectly!")
        elif overall_success_rate >= 70:
            print(f"\n⚠️  OVERALL ASSESSMENT: GOOD - {overall_success_rate:.1f}% success rate")
            print("   Most functionality working with minor issues to address.")
        else:
            print(f"\n🚨 OVERALL ASSESSMENT: NEEDS ATTENTION - {overall_success_rate:.1f}% success rate")
            print("   Significant issues found that require immediate attention.")

async def main():
    """Main test execution"""
    tester = BatchReportExportTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 Enhanced Batch Report Export Testing Completed Successfully!")
    else:
        print("\n❌ Enhanced Batch Report Export Testing Failed!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())