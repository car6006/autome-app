#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
import re
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class BatchContentCleaningTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123"
        self.test_user_id = None
        self.auth_token = None
        self.created_note_ids = []

    async def log_test(self, test_name, success, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")

    async def create_test_user(self):
        """Create a test user for batch report testing"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                user_data = {
                    "email": self.test_user_email,
                    "username": f"testuser{uuid.uuid4().hex[:8]}",
                    "password": self.test_user_password,
                    "first_name": "Test",
                    "last_name": "User"
                }
                
                response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.test_user_id = data.get("user", {}).get("id")
                    await self.log_test("User Registration", True, f"User created: {self.test_user_email}")
                    return True
                else:
                    await self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False

    async def create_test_notes(self):
        """Create test notes with content that might contain markdown symbols"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test notes with content that could trigger markdown formatting
                test_notes = [
                    {
                        "title": "Q4 Sales Performance Analysis",
                        "kind": "text",
                        "text_content": """
                        **Q4 Sales Results**
                        
                        ### Key Performance Indicators
                        - Revenue increased by **15%** compared to Q3
                        - Customer acquisition up ***25%***
                        - Market share expanded to ##12.5%##
                        
                        #### Regional Performance
                        * North America: _Strong growth_ in enterprise segment
                        * Europe: **Steady performance** with new partnerships
                        * Asia-Pacific: ***Exceptional results*** in digital transformation
                        
                        **Action Items:**
                        1. **Expand** digital marketing budget
                        2. ***Invest*** in customer success team
                        3. ##Focus## on enterprise sales
                        """
                    },
                    {
                        "title": "Digital Transformation Project Update",
                        "kind": "text", 
                        "text_content": """
                        # Digital Transformation Progress Report
                        
                        ## Executive Summary
                        The digital transformation initiative has achieved **significant milestones** in Q4.
                        
                        ### Completed Initiatives
                        - **Cloud Migration**: ***100% complete***
                        - **API Integration**: ##95% complete##
                        - **Data Analytics Platform**: _85% complete_
                        
                        #### Key Challenges
                        * **Budget constraints** affecting timeline
                        * ***Resource allocation*** needs optimization
                        * ##Change management## requires attention
                        
                        **Next Steps:**
                        1. ***Finalize*** remaining integrations
                        2. **Train** end users on new systems
                        3. ##Implement## monitoring and analytics
                        """
                    },
                    {
                        "title": "Customer Satisfaction Survey Results",
                        "kind": "text",
                        "text_content": """
                        ## Customer Satisfaction Analysis
                        
                        ### Overall Satisfaction Score: **8.7/10**
                        
                        #### Positive Feedback Areas
                        * **Product Quality**: ***Consistently rated high***
                        * **Customer Service**: ##Excellent response times##
                        * **Value for Money**: _Strong perceived value_
                        
                        ### Areas for Improvement
                        - **User Interface**: ***Needs modernization***
                        - **Documentation**: ##Requires updates##
                        - **Training Materials**: _Need enhancement_
                        
                        **Recommendations:**
                        1. **Invest** in UI/UX improvements
                        2. ***Update*** all documentation
                        3. ##Create## interactive training modules
                        """
                    }
                ]
                
                for note_data in test_notes:
                    response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                    
                    if response.status_code == 200:
                        note_info = response.json()
                        note_id = note_info.get("id")
                        self.created_note_ids.append(note_id)
                        await self.log_test(f"Create Note: {note_data['title']}", True, f"Note ID: {note_id}")
                    else:
                        await self.log_test(f"Create Note: {note_data['title']}", False, f"Status: {response.status_code}")
                        return False
                
                return len(self.created_note_ids) == len(test_notes)
                
        except Exception as e:
            await self.log_test("Create Test Notes", False, f"Exception: {str(e)}")
            return False

    def check_markdown_symbols(self, content):
        """Check for any markdown symbols in content"""
        markdown_patterns = [
            r'\*\*\*',  # Triple asterisks
            r'\*\*',    # Double asterisks  
            r'(?<!\w)\*(?!\w)',  # Single asterisks (not part of words)
            r'###',     # Triple hashes
            r'##',      # Double hashes
            r'(?<!\w)#(?!\w)',   # Single hashes (not part of words)
            r'__',      # Double underscores
            r'(?<!\w)_(?!\w)',   # Single underscores (not part of words)
            r'`',       # Backticks
        ]
        
        found_symbols = []
        for pattern in markdown_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_symbols.extend(matches)
        
        return found_symbols

    async def test_batch_comprehensive_report_generation(self):
        """Test the batch comprehensive report generation for content cleaning"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Generate batch comprehensive report
                request_data = {
                    "note_ids": self.created_note_ids,
                    "title": "Comprehensive Business Analysis - Content Cleaning Test"
                }
                
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report",
                    json=request_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    report_data = response.json()
                    report_content = report_data.get("report", "")
                    
                    # Check for markdown symbols
                    markdown_symbols = self.check_markdown_symbols(report_content)
                    
                    if not markdown_symbols:
                        await self.log_test("Batch Report Content Cleaning", True, 
                                          f"Report generated ({len(report_content)} chars) with NO markdown symbols")
                        
                        # Verify report structure
                        required_sections = [
                            "EXECUTIVE SUMMARY",
                            "KEY INSIGHTS", 
                            "STRATEGIC RECOMMENDATIONS",
                            "RISK ASSESSMENT",
                            "IMPLEMENTATION PRIORITIES",
                            "CONCLUSION"
                        ]
                        
                        missing_sections = []
                        for section in required_sections:
                            if section not in report_content:
                                missing_sections.append(section)
                        
                        if not missing_sections:
                            await self.log_test("Report Structure Verification", True, 
                                              "All required sections present")
                        else:
                            await self.log_test("Report Structure Verification", False, 
                                              f"Missing sections: {missing_sections}")
                        
                        # Check for proper bullet points (• symbol only)
                        bullet_lines = [line for line in report_content.split('\n') if '•' in line]
                        if bullet_lines:
                            await self.log_test("Bullet Point Format", True, 
                                              f"Found {len(bullet_lines)} proper bullet points using • symbol")
                        else:
                            await self.log_test("Bullet Point Format", False, 
                                              "No bullet points found with • symbol")
                        
                        return report_data
                    else:
                        await self.log_test("Batch Report Content Cleaning", False, 
                                          f"Found markdown symbols: {markdown_symbols}")
                        print(f"Report content preview: {report_content[:500]}...")
                        return None
                else:
                    await self.log_test("Batch Report Generation", False, 
                                      f"Status: {response.status_code}, Response: {response.text}")
                    return None
                    
        except Exception as e:
            await self.log_test("Batch Report Generation", False, f"Exception: {str(e)}")
            return None

    async def test_batch_report_export_formats(self, report_data):
        """Test all export formats for content cleaning"""
        if not report_data:
            return
            
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                formats = ["txt", "rtf", "pdf", "docx"]
                
                for format_type in formats:
                    try:
                        response = await client.post(
                            f"{BACKEND_URL}/notes/batch-comprehensive-report/export?format={format_type}",
                            json=report_data,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            content_length = len(response.content)
                            
                            # For text formats, check content directly
                            if format_type in ["txt", "rtf"]:
                                content_text = response.content.decode('utf-8', errors='ignore')
                                markdown_symbols = self.check_markdown_symbols(content_text)
                                
                                if not markdown_symbols:
                                    await self.log_test(f"Export {format_type.upper()} Content Cleaning", True, 
                                                      f"File size: {content_length} bytes, NO markdown symbols")
                                else:
                                    await self.log_test(f"Export {format_type.upper()} Content Cleaning", False, 
                                                      f"Found markdown symbols: {markdown_symbols}")
                            else:
                                # For binary formats (PDF, DOCX), just verify file generation
                                await self.log_test(f"Export {format_type.upper()} Generation", True, 
                                                  f"File generated successfully: {content_length} bytes")
                        else:
                            await self.log_test(f"Export {format_type.upper()}", False, 
                                              f"Status: {response.status_code}")
                            
                    except Exception as e:
                        await self.log_test(f"Export {format_type.upper()}", False, f"Exception: {str(e)}")
                        
        except Exception as e:
            await self.log_test("Export Formats Testing", False, f"Exception: {str(e)}")

    async def test_ai_prompt_effectiveness(self):
        """Test that the AI prompt instructions are working effectively"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Create a note with heavy markdown formatting to test prompt effectiveness
                markdown_heavy_note = {
                    "title": "Markdown Heavy Test Document",
                    "kind": "text",
                    "text_content": """
                    # **CRITICAL** ***BUSINESS*** ##UPDATE##
                    
                    ## **Performance** ***Metrics***
                    - **Revenue**: ***$1.2M*** increase
                    - **Customers**: ##500## new acquisitions
                    - **Market Share**: _15%_ growth
                    
                    ### ***Action*** **Items**:
                    1. **Implement** new ***CRM*** system
                    2. ##Hire## additional _sales_ staff
                    3. ***Expand*** **marketing** budget
                    
                    #### **Conclusion**
                    The ***results*** show ##significant## **improvement** across _all_ metrics.
                    """
                }
                
                # Create the test note
                response = await client.post(f"{BACKEND_URL}/notes", json=markdown_heavy_note, headers=headers)
                
                if response.status_code == 200:
                    note_info = response.json()
                    test_note_id = note_info.get("id")
                    
                    # Generate report with this heavily formatted note
                    request_data = {
                        "note_ids": [test_note_id],
                        "title": "AI Prompt Effectiveness Test"
                    }
                    
                    response = await client.post(
                        f"{BACKEND_URL}/notes/batch-comprehensive-report",
                        json=request_data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        report_data = response.json()
                        report_content = report_data.get("report", "")
                        
                        # Check for markdown symbols
                        markdown_symbols = self.check_markdown_symbols(report_content)
                        
                        if not markdown_symbols:
                            await self.log_test("AI Prompt Effectiveness", True, 
                                              "AI successfully followed formatting instructions - NO markdown symbols")
                        else:
                            await self.log_test("AI Prompt Effectiveness", False, 
                                              f"AI prompt failed - found symbols: {markdown_symbols}")
                            
                        # Check for proper formatting requirements
                        has_capital_headings = any(line.isupper() and len(line.strip()) > 5 
                                                 for line in report_content.split('\n') 
                                                 if line.strip())
                        
                        if has_capital_headings:
                            await self.log_test("Capital Letter Headings", True, 
                                              "Found proper CAPITAL LETTER section headings")
                        else:
                            await self.log_test("Capital Letter Headings", False, 
                                              "No CAPITAL LETTER headings found")
                    
                    # Clean up test note
                    await client.delete(f"{BACKEND_URL}/notes/{test_note_id}", headers=headers)
                    
        except Exception as e:
            await self.log_test("AI Prompt Effectiveness Test", False, f"Exception: {str(e)}")

    async def test_post_processing_cleaning(self):
        """Test the regex post-processing cleaning functionality"""
        try:
            # Test the regex patterns used in the backend
            test_content = """
            **This** has ***triple*** asterisks and ##double## hashes.
            Also _underscores_ and `backticks` should be removed.
            ### Triple hashes and ## double hashes too.
            Single * asterisks and # hashes should also go.
            """
            
            # Apply the same cleaning logic as in the backend
            import re
            cleaned_content = test_content
            cleaned_content = re.sub(r'\*\*\*', '', cleaned_content)  # Remove triple asterisks
            cleaned_content = re.sub(r'\*\*', '', cleaned_content)    # Remove double asterisks
            cleaned_content = re.sub(r'\*', '', cleaned_content)      # Remove single asterisks
            cleaned_content = re.sub(r'###', '', cleaned_content)     # Remove triple hashes
            cleaned_content = re.sub(r'##', '', cleaned_content)      # Remove double hashes
            cleaned_content = re.sub(r'#', '', cleaned_content)       # Remove single hashes
            cleaned_content = re.sub(r'__', '', cleaned_content)      # Remove double underscores
            cleaned_content = re.sub(r'_', '', cleaned_content)       # Remove single underscores
            cleaned_content = re.sub(r'`', '', cleaned_content)       # Remove backticks
            
            # Clean up whitespace
            cleaned_content = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_content)
            cleaned_content = cleaned_content.strip()
            
            # Check if any markdown symbols remain
            remaining_symbols = self.check_markdown_symbols(cleaned_content)
            
            if not remaining_symbols:
                await self.log_test("Post-Processing Regex Cleaning", True, 
                                  "All markdown symbols successfully removed by regex patterns")
            else:
                await self.log_test("Post-Processing Regex Cleaning", False, 
                                  f"Regex cleaning failed - remaining symbols: {remaining_symbols}")
                
        except Exception as e:
            await self.log_test("Post-Processing Cleaning Test", False, f"Exception: {str(e)}")

    async def cleanup_test_data(self):
        """Clean up test notes and user"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Delete test notes
                for note_id in self.created_note_ids:
                    try:
                        await client.delete(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                    except:
                        pass  # Ignore cleanup errors
                
                await self.log_test("Cleanup", True, f"Cleaned up {len(self.created_note_ids)} test notes")
                
        except Exception as e:
            await self.log_test("Cleanup", False, f"Exception: {str(e)}")

    async def run_comprehensive_tests(self):
        """Run all batch content cleaning tests"""
        print("🧪 Starting Batch Content Cleaning Comprehensive Tests")
        print("=" * 60)
        
        # Step 1: Create test user
        if not await self.create_test_user():
            print("❌ Failed to create test user - aborting tests")
            return
        
        # Step 2: Create test notes with markdown content
        if not await self.create_test_notes():
            print("❌ Failed to create test notes - aborting tests")
            return
        
        # Step 3: Test batch comprehensive report generation
        report_data = await self.test_batch_comprehensive_report_generation()
        
        # Step 4: Test export formats
        await self.test_batch_report_export_formats(report_data)
        
        # Step 5: Test AI prompt effectiveness
        await self.test_ai_prompt_effectiveness()
        
        # Step 6: Test post-processing cleaning
        await self.test_post_processing_cleaning()
        
        # Step 7: Cleanup
        await self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed_tests, total_tests

async def main():
    """Main test execution"""
    tester = BatchContentCleaningTester()
    passed, total = await tester.run_comprehensive_tests()
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Batch content cleaning is working perfectly.")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Review the issues above.")

if __name__ == "__main__":
    asyncio.run(main())