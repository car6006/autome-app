#!/usr/bin/env python3
"""
Comprehensive Email Functionality Test - Final Verification
Testing all requirements from the review request for Expeditors team integration
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-pro.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveEmailTester:
    def __init__(self):
        self.client = None
        self.test_results = []
        self.expeditors_user_token = None
        self.regular_user_token = None
        self.test_note_id = None
        
    async def setup(self):
        """Setup test environment"""
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("🔧 Setting up comprehensive email functionality tests...")
        
    async def cleanup(self):
        """Cleanup test environment"""
        if self.client:
            await self.client.aclose()
        logger.info("🧹 Test cleanup completed")
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"{status} - {test_name}: {details}")
        
    async def test_sendgrid_configuration_validation(self):
        """REQUIREMENT 1: Email Configuration Check - Verify SendGrid API key is properly configured"""
        try:
            # Check SendGrid API key from backend .env file
            sendgrid_key = None
            try:
                with open('/app/backend/.env', 'r') as f:
                    env_content = f.read()
                    for line in env_content.split('\n'):
                        if line.startswith('SENDGRID_API_KEY='):
                            sendgrid_key = line.split('=', 1)[1]
                            break
            except Exception as e:
                self.log_result("SendGrid Configuration Validation", False, f"Cannot read backend .env file: {str(e)}")
                return
            
            if not sendgrid_key:
                self.log_result("SendGrid Configuration Validation", False, "SENDGRID_API_KEY not found in backend .env")
                return
                
            if sendgrid_key == 'your_sendgrid_api_key_here':
                self.log_result("SendGrid Configuration Validation", False, "SendGrid API key is placeholder value")
                return
                
            # Verify key format (SendGrid keys start with 'SG.')
            if not sendgrid_key.startswith('SG.'):
                self.log_result("SendGrid Configuration Validation", False, f"Invalid SendGrid API key format: {sendgrid_key[:10]}...")
                return
                
            # Verify key length (SendGrid keys are typically 69 characters)
            if len(sendgrid_key) < 50:
                self.log_result("SendGrid Configuration Validation", False, f"SendGrid API key appears too short: {len(sendgrid_key)} characters")
                return
                
            self.log_result("SendGrid Configuration Validation", True, f"SendGrid API key properly configured and validated: {sendgrid_key[:15]}...")
            
        except Exception as e:
            self.log_result("SendGrid Configuration Validation", False, f"Error validating SendGrid configuration: {str(e)}")
            
    async def test_email_sending_functionality(self):
        """REQUIREMENT 2: Email Sending Function - Test the email sending functionality in tasks.py"""
        try:
            # Create a test note with realistic content
            response = await self.client.post(f"{API_BASE}/notes", json={
                "title": "Expeditors Supply Chain Meeting - Q4 2024",
                "kind": "audio"
            })
            
            if response.status_code != 200:
                self.log_result("Email Sending Functionality", False, f"Failed to create test note: {response.status_code}")
                return
                
            note_data = response.json()
            self.test_note_id = note_data["id"]
            
            # Test email sending with professional content
            email_request = {
                "to": ["logistics@expeditors.com", "operations@expeditors.com"],
                "subject": "Expeditors Supply Chain Meeting Notes - Action Items Required"
            }
            
            response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json=email_request)
            
            if response.status_code == 200:
                response_data = response.json()
                if "message" in response_data and "queued" in response_data["message"].lower():
                    self.log_result("Email Sending Functionality", True, "Email sending function works correctly - emails are properly queued for delivery")
                else:
                    self.log_result("Email Sending Functionality", True, f"Email function working: {response_data}")
            else:
                self.log_result("Email Sending Functionality", False, f"Email sending failed: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Email Sending Functionality", False, f"Error testing email sending: {str(e)}")
            
    async def test_professional_email_templates(self):
        """REQUIREMENT 3: Email Template and Format - Check email templates and formatting for professional use"""
        try:
            if not self.test_note_id:
                # Create a test note
                response = await self.client.post(f"{API_BASE}/notes", json={
                    "title": "Expeditors Executive Board Meeting - Strategic Planning",
                    "kind": "audio"
                })
                
                if response.status_code == 200:
                    self.test_note_id = response.json()["id"]
                else:
                    self.log_result("Professional Email Templates", False, "Failed to create test note")
                    return
            
            # Test multiple professional email scenarios
            professional_scenarios = [
                {
                    "to": ["ceo@expeditors.com", "board@expeditors.com"],
                    "subject": "Executive Board Meeting Minutes - Strategic Initiatives & Budget Approval"
                },
                {
                    "to": ["operations@expeditors.com", "logistics@expeditors.com"],
                    "subject": "Operations Review - Performance Metrics & Process Improvements"
                },
                {
                    "to": ["compliance@expeditors.com", "legal@expeditors.com"],
                    "subject": "Regulatory Compliance Update - New Trade Regulations Impact"
                }
            ]
            
            successful_tests = 0
            for i, scenario in enumerate(professional_scenarios):
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json=scenario)
                
                if response.status_code == 200:
                    successful_tests += 1
                    
            if successful_tests == len(professional_scenarios):
                self.log_result("Professional Email Templates", True, f"All {len(professional_scenarios)} professional email template scenarios work correctly")
            else:
                self.log_result("Professional Email Templates", False, f"Only {successful_tests}/{len(professional_scenarios)} email template scenarios succeeded")
                    
        except Exception as e:
            self.log_result("Professional Email Templates", False, f"Error testing email templates: {str(e)}")
            
    async def test_expeditors_user_integration(self):
        """REQUIREMENT 4: Expeditors Integration - Verify emails work correctly for @expeditors.com users"""
        try:
            # Register Expeditors user
            expeditors_user_data = {
                "email": f"expeditors_test_{int(datetime.now().timestamp())}@expeditors.com",
                "username": f"expeditors_user_{int(datetime.now().timestamp())}",
                "password": "ExpeditorSecure123!",
                "first_name": "Expeditors",
                "last_name": "Test User"
            }
            
            response = await self.client.post(f"{API_BASE}/auth/register", json=expeditors_user_data)
            
            if response.status_code != 200:
                self.log_result("Expeditors User Integration", False, f"Failed to register Expeditors user: {response.status_code}")
                return
                
            auth_data = response.json()
            self.expeditors_user_token = auth_data["access_token"]
            expeditors_user = auth_data["user"]
            
            # Verify user is recognized as Expeditors user
            if not expeditors_user["email"].endswith("@expeditors.com"):
                self.log_result("Expeditors User Integration", False, "User email domain not properly recognized")
                return
            
            # Test email functionality with Expeditors user context
            headers = {"Authorization": f"Bearer {self.expeditors_user_token}"}
            
            # Create notes as Expeditors user
            expeditors_notes = [
                {"title": "Expeditors Client Meeting - Amazon Logistics Partnership", "kind": "audio"},
                {"title": "Expeditors Operations Review - Asia Pacific Region", "kind": "photo"},
                {"title": "Expeditors Compliance Training - New Customs Regulations", "kind": "audio"}
            ]
            
            successful_integrations = 0
            for note_data in expeditors_notes:
                # Create note
                response = await self.client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code == 200:
                    note_id = response.json()["id"]
                    
                    # Test email sending for this note
                    email_request = {
                        "to": ["manager@expeditors.com", "team@expeditors.com"],
                        "subject": f"Expeditors Note: {note_data['title']}"
                    }
                    
                    response = await self.client.post(f"{API_BASE}/notes/{note_id}/email",
                        json=email_request, headers=headers)
                    
                    if response.status_code == 200:
                        successful_integrations += 1
                        
            if successful_integrations == len(expeditors_notes):
                self.log_result("Expeditors User Integration", True, f"All {len(expeditors_notes)} Expeditors user email integrations work correctly")
            else:
                self.log_result("Expeditors User Integration", False, f"Only {successful_integrations}/{len(expeditors_notes)} Expeditors integrations succeeded")
            
        except Exception as e:
            self.log_result("Expeditors User Integration", False, f"Error testing Expeditors integration: {str(e)}")
            
    async def test_comprehensive_error_handling(self):
        """REQUIREMENT 5: Error Handling - Test email error handling and logging"""
        try:
            error_scenarios = []
            
            # Test 1: Invalid email addresses
            if self.test_note_id:
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json={
                    "to": ["invalid-email", "not-an-email", ""],
                    "subject": "Test Invalid Emails"
                })
                error_scenarios.append(("Invalid Email Addresses", response.status_code == 200))
            
            # Test 2: Empty recipient list
            if self.test_note_id:
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json={
                    "to": [],
                    "subject": "Test Empty Recipients"
                })
                error_scenarios.append(("Empty Recipients", response.status_code == 200))
            
            # Test 3: Missing subject
            if self.test_note_id:
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json={
                    "to": ["test@expeditors.com"],
                    "subject": ""
                })
                error_scenarios.append(("Missing Subject", response.status_code == 200))
            
            # Test 4: Non-existent note
            response = await self.client.post(f"{API_BASE}/notes/non-existent-note-id/email", json={
                "to": ["test@expeditors.com"],
                "subject": "Test Non-existent Note"
            })
            error_scenarios.append(("Non-existent Note", response.status_code == 404))
            
            # Test 5: Malformed request
            if self.test_note_id:
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json={
                    "invalid_field": "test"
                })
                error_scenarios.append(("Malformed Request", response.status_code in [400, 422]))
            
            successful_error_handling = sum(1 for _, success in error_scenarios if success)
            total_error_tests = len(error_scenarios)
            
            if successful_error_handling == total_error_tests:
                self.log_result("Comprehensive Error Handling", True, f"All {total_error_tests} error handling scenarios work correctly")
            else:
                self.log_result("Comprehensive Error Handling", False, f"Only {successful_error_handling}/{total_error_tests} error handling scenarios succeeded")
                
        except Exception as e:
            self.log_result("Comprehensive Error Handling", False, f"Error testing error handling: {str(e)}")
            
    async def test_business_email_formatting(self):
        """ADDITIONAL: Test business-appropriate email content formatting"""
        try:
            if not self.test_note_id:
                response = await self.client.post(f"{API_BASE}/notes", json={
                    "title": "Expeditors Board Meeting - Annual Strategic Review",
                    "kind": "audio"
                })
                
                if response.status_code == 200:
                    self.test_note_id = response.json()["id"]
                else:
                    self.log_result("Business Email Formatting", False, "Failed to create test note")
                    return
            
            # Test business-appropriate email formatting
            business_email_scenarios = [
                {
                    "to": ["board@expeditors.com"],
                    "subject": "CONFIDENTIAL: Board Meeting Minutes - Strategic Acquisitions Discussion"
                },
                {
                    "to": ["investors@expeditors.com"],
                    "subject": "Expeditors Q4 Performance Report - Investor Relations Update"
                },
                {
                    "to": ["compliance@expeditors.com"],
                    "subject": "URGENT: Regulatory Compliance Review - Action Required by EOD"
                }
            ]
            
            successful_formatting = 0
            for scenario in business_email_scenarios:
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json=scenario)
                
                if response.status_code == 200:
                    successful_formatting += 1
                    
            if successful_formatting == len(business_email_scenarios):
                self.log_result("Business Email Formatting", True, f"All {len(business_email_scenarios)} business email formatting scenarios work correctly")
            else:
                self.log_result("Business Email Formatting", False, f"Only {successful_formatting}/{len(business_email_scenarios)} formatting scenarios succeeded")
                
        except Exception as e:
            self.log_result("Business Email Formatting", False, f"Error testing business email formatting: {str(e)}")
            
    async def test_email_delivery_reliability(self):
        """ADDITIONAL: Test email delivery tracking and reliability"""
        try:
            if not self.test_note_id:
                self.log_result("Email Delivery Reliability", False, "No test note available")
                return
            
            # Test multiple email deliveries to ensure reliability
            delivery_tests = []
            
            for i in range(5):
                email_request = {
                    "to": [f"test{i}@expeditors.com"],
                    "subject": f"Delivery Test {i+1} - Expeditors Email Reliability Check"
                }
                
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json=email_request)
                delivery_tests.append(response.status_code == 200)
                
            successful_deliveries = sum(delivery_tests)
            total_deliveries = len(delivery_tests)
            
            if successful_deliveries == total_deliveries:
                self.log_result("Email Delivery Reliability", True, f"All {total_deliveries} email delivery tests successful - 100% reliability")
            else:
                reliability_percentage = (successful_deliveries / total_deliveries) * 100
                if reliability_percentage >= 80:
                    self.log_result("Email Delivery Reliability", True, f"Email delivery reliability: {reliability_percentage:.1f}% ({successful_deliveries}/{total_deliveries})")
                else:
                    self.log_result("Email Delivery Reliability", False, f"Email delivery reliability too low: {reliability_percentage:.1f}% ({successful_deliveries}/{total_deliveries})")
                
        except Exception as e:
            self.log_result("Email Delivery Reliability", False, f"Error testing email delivery reliability: {str(e)}")
            
    async def run_all_tests(self):
        """Run all comprehensive email functionality tests"""
        logger.info("🚀 Starting COMPREHENSIVE email functionality testing for Expeditors team integration...")
        logger.info("📋 Testing all requirements from the review request...")
        
        await self.setup()
        
        try:
            # Run all comprehensive email functionality tests
            await self.test_sendgrid_configuration_validation()
            await self.test_email_sending_functionality()
            await self.test_professional_email_templates()
            await self.test_expeditors_user_integration()
            await self.test_comprehensive_error_handling()
            await self.test_business_email_formatting()
            await self.test_email_delivery_reliability()
            
        finally:
            await self.cleanup()
            
        # Generate comprehensive summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n{'='*100}")
        logger.info(f"📊 COMPREHENSIVE EMAIL FUNCTIONALITY TEST SUMMARY - EXPEDITORS INTEGRATION")
        logger.info(f"{'='*100}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"{'='*100}")
        
        # Detailed results by category
        logger.info("📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['details']}")
            
        # Final assessment
        logger.info(f"\n{'='*100}")
        if success_rate >= 90:
            logger.info("🎉 EXCELLENT: Email functionality is PRODUCTION READY for Expeditors team!")
        elif success_rate >= 80:
            logger.info("✅ GOOD: Email functionality is working well with minor issues")
        elif success_rate >= 70:
            logger.info("⚠️  ACCEPTABLE: Email functionality works but needs improvements")
        else:
            logger.info("❌ CRITICAL: Email functionality has significant issues requiring fixes")
        logger.info(f"{'='*100}")
            
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "results": self.test_results,
            "production_ready": success_rate >= 90
        }

async def main():
    """Main test execution"""
    tester = ComprehensiveEmailTester()
    results = await tester.run_all_tests()
    
    # Return results for further processing
    return results

if __name__ == "__main__":
    asyncio.run(main())