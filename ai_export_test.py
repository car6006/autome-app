#!/usr/bin/env python3
"""
AI Conversations Export Functionality Test
Tests the specific export functionality that the user reported as not working
"""

import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class AIExportTester:
    def __init__(self, base_url="https://voice-capture-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"export_test_{int(time.time())}@example.com",
            "username": f"exportuser{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Export",
            "last_name": "Tester"
        }
        self.expeditors_token = None
        self.test_note_id = None

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
                    return True, {"message": "Success but no JSON response", "content": response.content, "headers": dict(response.headers)}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:500]}")
                return False, {"status_code": response.status_code, "content": response.content, "headers": dict(response.headers)}

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
            self.log(f"   ✅ User registered and logged in")
            return True
        else:
            self.log(f"   ❌ User registration failed")
            return False

    def setup_expeditors_user(self):
        """Setup Expeditors user for branding tests"""
        expeditors_data = {
            "email": f"export_test_{int(time.time())}@expeditors.com",
            "username": f"expeditorsexport{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "Tester"
        }
        
        success, response = self.run_test(
            "Expeditors User Registration",
            "POST",
            "auth/register",
            200,
            data=expeditors_data
        )
        
        if success:
            self.expeditors_token = response.get('access_token')
            self.log(f"   ✅ Expeditors user registered")
            return True
        else:
            self.log(f"   ❌ Expeditors user registration failed")
            return False

    def create_note_with_ai_content(self):
        """Create a note with AI conversations for export testing"""
        self.log("📝 Creating note with AI content...")
        
        # Create a text note with substantial content
        note_data = {
            "title": "Export Test Meeting - Supply Chain Analysis",
            "kind": "text",
            "text_content": """Meeting: Q4 Supply Chain Strategy Session
Date: December 19, 2024
Attendees: Supply Chain Director, Logistics Manager, Operations Lead

EXECUTIVE SUMMARY
This quarterly strategy session focused on optimizing our global supply chain operations for 2025. Key discussions centered around cost reduction initiatives, risk mitigation strategies, and technology investments to improve operational efficiency.

KEY DISCUSSION POINTS

Supply Chain Performance Review
Current performance metrics show 94% on-time delivery across all regions, with Asia-Pacific leading at 97% and Europe trailing at 91%. Transportation costs have increased 12% year-over-year due to fuel price volatility and capacity constraints.

Risk Assessment and Mitigation
Identified three critical risk areas: port congestion in major Asian hubs, potential labor strikes in European logistics centers, and currency fluctuation impacts on procurement costs. Developed contingency plans for each scenario.

Technology Investment Priorities
Approved implementation of advanced tracking systems, AI-powered demand forecasting, and automated inventory management. Expected ROI of 15% within 18 months through reduced operational costs and improved efficiency.

Carrier Relationship Management
Reviewed performance of top 10 carriers, renegotiated contracts with 3 underperforming partners, and established preferred partner agreements with 2 new regional carriers to improve coverage and reduce costs.

DECISIONS AND RESOLUTIONS
- Increase safety stock levels by 20% for critical SKUs
- Implement new carrier performance scorecards
- Establish quarterly business reviews with key partners
- Invest $2.5M in supply chain technology upgrades

ACTION ITEMS
1. Finalize carrier contract negotiations by January 15, 2025
2. Deploy new tracking system across all facilities by March 1
3. Complete risk assessment for alternative shipping routes
4. Establish monthly performance review meetings
5. Implement cost reduction initiatives targeting 8% savings

RISK FACTORS
- Port congestion may impact Q1 delivery schedules
- Currency volatility affecting procurement budgets
- Potential capacity constraints during peak season
- Technology integration challenges with legacy systems

NEXT STEPS
Follow-up meeting scheduled for January 30, 2025 to review implementation progress and address any emerging challenges. Weekly status updates will be provided via email to all stakeholders."""
        }
        
        success, response = self.run_test(
            "Create Text Note with Content",
            "POST",
            "notes",
            200,
            data=note_data,
            auth_required=True
        )
        
        if success and 'id' in response:
            self.test_note_id = response['id']
            self.log(f"   ✅ Created note ID: {self.test_note_id}")
            return True
        else:
            self.log(f"   ❌ Failed to create note")
            return False

    def add_ai_conversations(self):
        """Add AI conversations to the note"""
        self.log("🤖 Adding AI conversations...")
        
        test_questions = [
            "What are the key supply chain risks identified in this meeting?",
            "Summarize the main action items and their deadlines",
            "Analyze the financial impact of the proposed technology investments",
            "What are the performance metrics mentioned and how can they be improved?",
            "Provide strategic recommendations based on the carrier relationship review"
        ]
        
        conversations_added = 0
        
        for i, question in enumerate(test_questions):
            success, response = self.run_test(
                f"AI Chat Question {i+1}",
                "POST",
                f"notes/{self.test_note_id}/ai-chat",
                200,
                data={"question": question},
                auth_required=True,
                timeout=60
            )
            
            if success:
                conversations_added += 1
                ai_response = response.get('response', '')
                self.log(f"   ✅ Added conversation {i+1}: {len(ai_response)} chars")
            else:
                self.log(f"   ❌ Failed to add conversation {i+1}")
                # Continue with other questions even if one fails
        
        self.log(f"   📊 Total conversations added: {conversations_added}/{len(test_questions)}")
        return conversations_added > 0

    def test_export_format(self, format_type, is_expeditors=False):
        """Test a specific export format"""
        # Switch to appropriate user token
        original_token = self.auth_token
        if is_expeditors and self.expeditors_token:
            self.auth_token = self.expeditors_token
        
        try:
            url = f"{self.api_url}/notes/{self.test_note_id}/ai-conversations/export?format={format_type}"
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            self.log(f"🔍 Testing {format_type.upper()} export {'(Expeditors)' if is_expeditors else '(Regular)'}...")
            
            response = requests.get(url, headers=headers, timeout=120)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                self.log(f"✅ {format_type.upper()} Export - Status: {response.status_code}")
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                expected_types = {
                    'pdf': 'application/pdf',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'txt': 'text/plain',
                    'rtf': 'application/rtf'
                }
                
                expected_type = expected_types.get(format_type, '')
                if expected_type in content_type:
                    self.log(f"   ✅ Correct Content-Type: {content_type}")
                else:
                    self.log(f"   ⚠️  Unexpected Content-Type: {content_type} (expected: {expected_type})")
                
                # Check content disposition for filename
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    self.log(f"   ✅ Proper file attachment header")
                    
                    # Check for branding in filename
                    if is_expeditors and 'Expeditors' in content_disposition:
                        self.log(f"   ✅ Expeditors branding in filename detected")
                    elif not is_expeditors and 'AI_Analysis' in content_disposition:
                        self.log(f"   ✅ Standard filename format detected")
                    
                    # Check file extension
                    if f'.{format_type}' in content_disposition:
                        self.log(f"   ✅ Correct .{format_type} file extension")
                else:
                    self.log(f"   ❌ Missing or incorrect Content-Disposition header")
                
                # Check content size
                content_length = len(response.content)
                min_sizes = {'pdf': 2000, 'docx': 3000, 'txt': 500, 'rtf': 1000}
                min_size = min_sizes.get(format_type, 500)
                
                if content_length > min_size:
                    self.log(f"   ✅ File size: {content_length} bytes (substantial content)")
                else:
                    self.log(f"   ⚠️  File size: {content_length} bytes (may be too small)")
                
                # Check format-specific headers
                if format_type == 'pdf' and response.content.startswith(b'%PDF'):
                    self.log(f"   ✅ Valid PDF header detected")
                elif format_type == 'docx' and response.content.startswith(b'PK'):
                    self.log(f"   ✅ Valid DOCX header detected (ZIP format)")
                elif format_type in ['txt', 'rtf']:
                    # Check for clean formatting (no markdown symbols)
                    try:
                        content_text = response.content.decode('utf-8')
                        has_markdown = any(symbol in content_text for symbol in ['###', '**', '*', '```'])
                        if not has_markdown:
                            self.log(f"   ✅ Clean formatting (no markdown symbols)")
                        else:
                            self.log(f"   ⚠️  Markdown symbols found in content")
                    except:
                        pass
                
                # Test download functionality by saving to temp file
                try:
                    with tempfile.NamedTemporaryFile(suffix=f'.{format_type}', delete=False) as tmp_file:
                        tmp_file.write(response.content)
                        tmp_file.flush()
                        
                        # Verify file was written correctly
                        if os.path.getsize(tmp_file.name) == content_length:
                            self.log(f"   ✅ File download simulation successful")
                        else:
                            self.log(f"   ⚠️  File download simulation issue")
                        
                        os.unlink(tmp_file.name)
                except Exception as e:
                    self.log(f"   ⚠️  File download simulation failed: {str(e)}")
                
            else:
                self.log(f"❌ {format_type.upper()} Export - Expected 200, got {response.status_code}")
                
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get('detail', 'Unknown error')
                        self.log(f"   Error: {error_detail}")
                        
                        # Check if it's the expected "no AI conversations" error
                        if 'AI analysis' in error_detail or 'conversations' in error_detail:
                            self.log(f"   ℹ️  This may be expected if no AI conversations exist")
                    except:
                        self.log(f"   Response text: {response.text[:200]}")
                
                elif response.status_code == 500:
                    self.log(f"   ❌ CRITICAL: Internal server error - export functionality broken")
                    try:
                        error_data = response.json()
                        self.log(f"   Server error: {error_data.get('detail', 'Unknown server error')}")
                    except:
                        self.log(f"   Raw error response: {response.text[:200]}")
                
                elif response.status_code == 404:
                    self.log(f"   ❌ Note not found or endpoint not available")
                
                elif response.status_code == 403:
                    self.log(f"   ❌ Authentication/authorization issue")
            
            self.tests_run += 1
            return success
            
        except requests.exceptions.Timeout:
            self.log(f"❌ {format_type.upper()} Export - Request timeout")
            self.tests_run += 1
            return False
        except Exception as e:
            self.log(f"❌ {format_type.upper()} Export - Error: {str(e)}")
            self.tests_run += 1
            return False
        finally:
            # Restore original token
            self.auth_token = original_token

    def test_export_error_scenarios(self):
        """Test various error scenarios for export functionality"""
        self.log("🚨 Testing export error scenarios...")
        
        # Test 1: Invalid format
        success1, _ = self.run_test(
            "Export Invalid Format",
            "GET",
            f"notes/{self.test_note_id}/ai-conversations/export?format=invalid",
            422,  # Validation error
            auth_required=True
        )
        
        # Test 2: Non-existent note
        success2, _ = self.run_test(
            "Export Non-existent Note",
            "GET",
            "notes/non-existent-id/ai-conversations/export?format=pdf",
            404,  # Not found
            auth_required=True
        )
        
        # Test 3: No authentication
        temp_token = self.auth_token
        self.auth_token = None
        success3, _ = self.run_test(
            "Export Without Authentication",
            "GET",
            f"notes/{self.test_note_id}/ai-conversations/export?format=pdf",
            403,  # Forbidden
            auth_required=True
        )
        self.auth_token = temp_token
        
        # Test 4: Missing format parameter
        success4, _ = self.run_test(
            "Export Without Format Parameter",
            "GET",
            f"notes/{self.test_note_id}/ai-conversations/export",
            200,  # Should default to PDF
            auth_required=True
        )
        
        return success1 and success2 and success3

    def test_dependency_check(self):
        """Test if required dependencies are available"""
        self.log("🔧 Checking export dependencies...")
        
        # Test health endpoint to see if system is running
        success, response = self.run_test(
            "System Health Check",
            "GET",
            "health",
            200
        )
        
        if success:
            self.log("   ✅ Backend system is running")
            return True
        else:
            self.log("   ❌ Backend system health check failed")
            return False

    def run_comprehensive_export_test(self):
        """Run comprehensive AI export functionality test"""
        self.log("🚀 STARTING AI CONVERSATIONS EXPORT FUNCTIONALITY TEST")
        self.log("=" * 60)
        
        # Step 1: Check system health
        if not self.test_dependency_check():
            self.log("❌ System health check failed - aborting tests")
            return False
        
        # Step 2: Setup test users
        if not self.setup_test_user():
            self.log("❌ Test user setup failed - aborting tests")
            return False
        
        # Step 3: Setup Expeditors user for branding tests
        expeditors_available = self.setup_expeditors_user()
        
        # Step 4: Create note with content
        if not self.create_note_with_ai_content():
            self.log("❌ Note creation failed - aborting tests")
            return False
        
        # Step 5: Add AI conversations
        if not self.add_ai_conversations():
            self.log("❌ AI conversations setup failed - aborting tests")
            return False
        
        # Step 6: Test all export formats
        self.log("\n📄 TESTING EXPORT FORMATS")
        self.log("-" * 30)
        
        formats_to_test = ['pdf', 'docx', 'txt', 'rtf']
        format_results = {}
        
        # Test regular user exports
        for format_type in formats_to_test:
            format_results[f'{format_type}_regular'] = self.test_export_format(format_type, is_expeditors=False)
        
        # Test Expeditors user exports (if available)
        if expeditors_available:
            self.log("\n🏢 TESTING EXPEDITORS BRANDING")
            self.log("-" * 30)
            for format_type in formats_to_test:
                format_results[f'{format_type}_expeditors'] = self.test_export_format(format_type, is_expeditors=True)
        
        # Step 7: Test error scenarios
        self.log("\n🚨 TESTING ERROR SCENARIOS")
        self.log("-" * 30)
        error_tests_passed = self.test_export_error_scenarios()
        
        # Step 8: Generate summary report
        self.log("\n📊 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        total_tests = self.tests_run
        passed_tests = self.tests_passed
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total Tests Run: {total_tests}")
        self.log(f"Tests Passed: {passed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed format results
        self.log("\nFORMAT-SPECIFIC RESULTS:")
        for format_name, result in format_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {format_name.upper()}: {status}")
        
        # Critical issues identification
        critical_issues = []
        
        # Check if any format completely failed
        regular_formats = [k for k in format_results.keys() if 'regular' in k]
        failed_formats = [k for k, v in format_results.items() if not v and 'regular' in k]
        
        if failed_formats:
            critical_issues.append(f"Export formats not working: {', '.join([f.replace('_regular', '') for f in failed_formats])}")
        
        if not error_tests_passed:
            critical_issues.append("Error handling not working properly")
        
        if success_rate < 70:
            critical_issues.append(f"Low overall success rate: {success_rate:.1f}%")
        
        # Final assessment
        if critical_issues:
            self.log("\n🚨 CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                self.log(f"  ❌ {issue}")
            
            self.log("\n💡 RECOMMENDED ACTIONS:")
            if any('pdf' in issue or 'docx' in issue for issue in critical_issues):
                self.log("  • Check if reportlab and python-docx dependencies are installed")
                self.log("  • Verify logo file path exists for Expeditors branding")
                self.log("  • Check server logs for import errors or missing dependencies")
            
            if 'txt' in str(critical_issues) or 'rtf' in str(critical_issues):
                self.log("  • Check text processing and RTF generation logic")
                self.log("  • Verify content cleaning functions are working")
            
            self.log("  • Check backend server logs for detailed error messages")
            self.log("  • Verify all export endpoint routes are properly registered")
            self.log("  • Test with different note content types")
            
            return False
        else:
            self.log("\n🎉 ALL TESTS PASSED!")
            self.log("AI Conversations Export functionality is working correctly!")
            return True

def main():
    """Main test execution"""
    tester = AIExportTester()
    
    try:
        success = tester.run_comprehensive_export_test()
        
        if success:
            print("\n✅ AI EXPORT FUNCTIONALITY TEST COMPLETED SUCCESSFULLY")
            sys.exit(0)
        else:
            print("\n❌ AI EXPORT FUNCTIONALITY TEST FAILED")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()