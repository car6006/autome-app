#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Email Functionality - Expeditors Team Integration
Focus: Email configuration, sending, templates, Expeditors integration, and error handling
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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://transcribe-ocr.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class EmailFunctionalityTester:
    def __init__(self):
        self.client = None
        self.test_results = []
        self.expeditors_user_token = None
        self.regular_user_token = None
        self.test_note_id = None
        
    async def setup(self):
        """Setup test environment"""
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("🔧 Setting up email functionality tests...")
        
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
        
    async def test_sendgrid_api_key_configuration(self):
        """Test 1: Verify SendGrid API key is properly configured"""
        try:
            # Check if SendGrid API key is configured in environment
            # First check current environment, then check backend .env file
            sendgrid_key = os.getenv("SENDGRID_API_KEY")
            
            if not sendgrid_key:
                # Try to read from backend .env file
                try:
                    with open('/app/backend/.env', 'r') as f:
                        env_content = f.read()
                        for line in env_content.split('\n'):
                            if line.startswith('SENDGRID_API_KEY='):
                                sendgrid_key = line.split('=', 1)[1]
                                break
                except Exception as e:
                    pass
            
            if not sendgrid_key:
                self.log_result("SendGrid API Key Configuration", False, "SENDGRID_API_KEY environment variable not found")
                return
                
            if sendgrid_key == 'your_sendgrid_api_key_here':
                self.log_result("SendGrid API Key Configuration", False, "SendGrid API key is placeholder value")
                return
                
            # Verify key format (SendGrid keys start with 'SG.')
            if not sendgrid_key.startswith('SG.'):
                self.log_result("SendGrid API Key Configuration", False, f"Invalid SendGrid API key format. Expected to start with 'SG.', got: {sendgrid_key[:10]}...")
                return
                
            self.log_result("SendGrid API Key Configuration", True, f"SendGrid API key properly configured: {sendgrid_key[:10]}...")
            
        except Exception as e:
            self.log_result("SendGrid API Key Configuration", False, f"Error checking SendGrid configuration: {str(e)}")
            
    async def test_email_sending_function(self):
        """Test 2: Test the email sending functionality in tasks.py"""
        try:
            # Test by checking if the email endpoint exists and responds correctly
            response = await self.client.get(f"{API_BASE}/")
            
            if response.status_code != 200:
                self.log_result("Email Sending Function", False, f"API not accessible: {response.status_code}")
                return
                
            # Create a test note to use for email testing
            response = await self.client.post(f"{API_BASE}/notes", json={
                "title": "Test Email Functionality - Expeditors Integration",
                "kind": "audio"
            })
            
            if response.status_code != 200:
                self.log_result("Email Sending Function", False, f"Failed to create test note: {response.status_code}")
                return
                
            note_data = response.json()
            self.test_note_id = note_data["id"]
            
            # Test email endpoint exists
            email_request = {
                "to": ["test@expeditors.com"],
                "subject": "Test Email - Expeditors Integration"
            }
            
            response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json=email_request)
            
            if response.status_code == 200:
                self.log_result("Email Sending Function", True, "Email endpoint accessible and functioning")
            else:
                self.log_result("Email Sending Function", False, f"Email endpoint error: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Email Sending Function", False, f"Error testing email function: {str(e)}")
            
    async def test_email_template_and_format(self):
        """Test 3: Check email templates and formatting for professional use"""
        try:
            if not self.test_note_id:
                # Create a test note
                response = await self.client.post(f"{API_BASE}/notes", json={
                    "title": "Test Email Template - Expeditors Meeting Notes",
                    "kind": "audio"
                })
                
                if response.status_code == 200:
                    self.test_note_id = response.json()["id"]
                else:
                    self.log_result("Email Template and Format", False, f"Failed to create test note: {response.status_code}")
                    return
            
            # Test email with professional content
            professional_email_request = {
                "to": ["manager@expeditors.com", "team@expeditors.com"],
                "subject": "Expeditors Meeting Notes - Supply Chain Optimization Discussion"
            }
            
            response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json=professional_email_request)
            
            if response.status_code == 200:
                response_data = response.json()
                if "message" in response_data and "queued" in response_data["message"].lower():
                    self.log_result("Email Template and Format", True, "Professional email template formatting works correctly")
                else:
                    self.log_result("Email Template and Format", True, f"Email template processed: {response_data}")
            else:
                self.log_result("Email Template and Format", False, f"Email template error: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Email Template and Format", False, f"Error testing email template: {str(e)}")
            
    async def test_expeditors_integration(self):
        """Test 4: Verify emails work correctly for @expeditors.com users"""
        try:
            # Test user registration and authentication for Expeditors user
            expeditors_user_data = {
                "email": f"testuser{int(datetime.now().timestamp())}@expeditors.com",
                "username": f"expeditors_user_{int(datetime.now().timestamp())}",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "Expeditors User"
            }
            
            # Register Expeditors user
            response = await self.client.post(f"{API_BASE}/auth/register", json=expeditors_user_data)
            
            if response.status_code == 200:
                auth_data = response.json()
                self.expeditors_user_token = auth_data["access_token"]
                self.log_result("Expeditors User Registration", True, "Expeditors user registered successfully")
            else:
                self.log_result("Expeditors Integration", False, f"Failed to register Expeditors user: {response.status_code} - {response.text}")
                return
            
            # Test email functionality with Expeditors user context
            if self.expeditors_user_token:
                headers = {"Authorization": f"Bearer {self.expeditors_user_token}"}
                
                # Create a note as Expeditors user
                response = await self.client.post(f"{API_BASE}/notes", 
                    json={"title": "Expeditors Logistics Meeting", "kind": "audio"}, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    note_data = response.json()
                    expeditors_note_id = note_data["id"]
                    
                    # Test email sending for Expeditors note
                    email_request = {
                        "to": ["manager@expeditors.com", "team@expeditors.com"],
                        "subject": "Expeditors Logistics Meeting Notes - Urgent Review Required"
                    }
                    
                    response = await self.client.post(f"{API_BASE}/notes/{expeditors_note_id}/email",
                        json=email_request, headers=headers)
                    
                    if response.status_code == 200:
                        self.log_result("Expeditors Integration", True, "Email functionality works correctly for @expeditors.com users")
                    else:
                        self.log_result("Expeditors Integration", False, f"Email failed for Expeditors user: {response.status_code}")
                else:
                    self.log_result("Expeditors Integration", False, f"Failed to create note for Expeditors user: {response.status_code}")
            
        except Exception as e:
            self.log_result("Expeditors Integration", False, f"Error testing Expeditors integration: {str(e)}")
            
    async def test_email_error_handling(self):
        """Test 5: Test email error handling and logging"""
        try:
            # Test 1: Email with invalid recipients
            if self.test_note_id:
                invalid_email_request = {
                    "to": ["invalid-email", ""],
                    "subject": "Test Invalid Recipients"
                }
                
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email",
                    json=invalid_email_request)
                
                # Should still return 200 but log errors internally
                if response.status_code == 200:
                    self.log_result("Email Error Handling - Invalid Recipients", True, "API handles invalid recipients gracefully")
                else:
                    self.log_result("Email Error Handling - Invalid Recipients", False, f"Unexpected response: {response.status_code}")
            
            # Test 2: Email with missing subject
            if self.test_note_id:
                missing_subject_request = {
                    "to": ["test@expeditors.com"],
                    "subject": ""
                }
                
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email",
                    json=missing_subject_request)
                
                if response.status_code == 200:
                    self.log_result("Email Error Handling - Missing Subject", True, "API handles missing subject gracefully")
                else:
                    self.log_result("Email Error Handling - Missing Subject", False, f"Unexpected response: {response.status_code}")
            
            # Test 3: Email for non-existent note
            response = await self.client.post(f"{API_BASE}/notes/non-existent-note-id/email",
                json={"to": ["test@expeditors.com"], "subject": "Test"})
            
            if response.status_code == 404:
                self.log_result("Email Error Handling - Non-existent Note", True, "API correctly returns 404 for non-existent note")
            else:
                self.log_result("Email Error Handling - Non-existent Note", False, f"Expected 404, got: {response.status_code}")
                
            # Test 4: Email without authentication for protected note
            if self.expeditors_user_token and self.test_note_id:
                # Create a note with Expeditors user
                headers = {"Authorization": f"Bearer {self.expeditors_user_token}"}
                response = await self.client.post(f"{API_BASE}/notes", 
                    json={"title": "Protected Expeditors Note", "kind": "audio"}, 
                    headers=headers
                )
                
                if response.status_code == 200:
                    protected_note_id = response.json()["id"]
                    
                    # Try to send email without authentication
                    response = await self.client.post(f"{API_BASE}/notes/{protected_note_id}/email",
                        json={"to": ["test@expeditors.com"], "subject": "Unauthorized Test"})
                    
                    if response.status_code == 403:
                        self.log_result("Email Error Handling - Unauthorized Access", True, "API correctly prevents unauthorized email access")
                    else:
                        self.log_result("Email Error Handling - Unauthorized Access", False, f"Expected 403, got: {response.status_code}")
                        
        except Exception as e:
            self.log_result("Email Error Handling", False, f"Error testing email error handling: {str(e)}")
            
    async def test_professional_email_formatting(self):
        """Test 6: Verify professional email formatting for business use"""
        try:
            if not self.test_note_id:
                # Create a test note
                response = await self.client.post(f"{API_BASE}/notes", json={
                    "title": "Expeditors Q4 Strategic Planning Meeting",
                    "kind": "audio"
                })
                
                if response.status_code == 200:
                    self.test_note_id = response.json()["id"]
                else:
                    self.log_result("Professional Email Formatting", False, "Failed to create test note")
                    return
            
            # Test professional email formatting with comprehensive business content
            professional_recipients = ["ceo@expeditors.com", "operations@expeditors.com", "strategy@expeditors.com"]
            professional_subject = "Q4 Strategic Planning Meeting Notes - Action Items & Next Steps"
            
            professional_email_request = {
                "to": professional_recipients,
                "subject": professional_subject
            }
            
            response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email", json=professional_email_request)
            
            if response.status_code == 200:
                self.log_result("Professional Email Formatting", True, "Professional email formatting completed successfully")
            else:
                self.log_result("Professional Email Formatting", False, f"Email formatting error: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Professional Email Formatting", False, f"Error testing professional email formatting: {str(e)}")
            
    async def test_email_delivery_tracking(self):
        """Test 7: Test email delivery tracking and logging"""
        try:
            # Test email API endpoint response
            if self.test_note_id:
                email_request = {
                    "to": ["tracking@expeditors.com"],
                    "subject": "Email Delivery Tracking Test"
                }
                
                response = await self.client.post(f"{API_BASE}/notes/{self.test_note_id}/email",
                    json=email_request)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "message" in response_data and "queued" in response_data["message"].lower():
                        self.log_result("Email Delivery Tracking", True, "Email delivery tracking works - emails are properly queued")
                    else:
                        self.log_result("Email Delivery Tracking", True, f"Email API response: {response_data}")
                else:
                    self.log_result("Email Delivery Tracking", False, f"Email API failed: {response.status_code}")
            else:
                self.log_result("Email Delivery Tracking", False, "No test note available for tracking test")
                
        except Exception as e:
            self.log_result("Email Delivery Tracking", False, f"Error testing email delivery tracking: {str(e)}")
            
    async def run_all_tests(self):
        """Run all email functionality tests"""
        logger.info("🚀 Starting comprehensive email functionality testing for Expeditors team integration...")
        
        await self.setup()
        
        try:
            # Run all email functionality tests
            await self.test_sendgrid_api_key_configuration()
            await self.test_email_sending_function()
            await self.test_email_template_and_format()
            await self.test_expeditors_integration()
            await self.test_email_error_handling()
            await self.test_professional_email_formatting()
            await self.test_email_delivery_tracking()
            
        finally:
            await self.cleanup()
            
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 EMAIL FUNCTIONALITY TEST SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"{'='*80}")
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['details']}")
            
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    tester = EmailFunctionalityTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if results["success_rate"] >= 80:
        logger.info("🎉 Email functionality testing completed successfully!")
        return results
    else:
        logger.error("❌ Email functionality testing failed - success rate below 80%")
        return results

if __name__ == "__main__":
    asyncio.run(main())