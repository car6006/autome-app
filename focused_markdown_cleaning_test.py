#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
import re
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class FocusedMarkdownCleaningTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123"
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

    async def setup_test_user(self):
        """Create test user and authenticate"""
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
                    await self.log_test("User Setup", True, f"User authenticated: {self.test_user_email}")
                    return True
                else:
                    await self.log_test("User Setup", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("User Setup", False, f"Exception: {str(e)}")
            return False

    def detect_specific_markdown_symbols(self, content):
        """Detect specific markdown symbols mentioned in the review request"""
        symbols_found = {}
        
        # Check for specific symbols mentioned in the review
        patterns = {
            "triple_asterisks": r'\*\*\*',
            "double_asterisks": r'\*\*',
            "single_asterisks": r'(?<!\w)\*(?!\w)',
            "triple_hashes": r'###',
            "double_hashes": r'##',
            "single_hashes": r'(?<!\w)#(?!\w)',
            "double_underscores": r'__',
            "single_underscores": r'(?<!\w)_(?!\w)',
            "backticks": r'`'
        }
        
        for symbol_name, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                symbols_found[symbol_name] = len(matches)
        
        return symbols_found

    async def test_extreme_markdown_content(self):
        """Test with extremely heavy markdown content to stress-test the cleaning"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Create note with extreme markdown formatting
                extreme_markdown_note = {
                    "title": "Extreme Markdown Test Document",
                    "kind": "text",
                    "text_content": """
                    # ***CRITICAL*** **BUSINESS** ##ALERT##
                    
                    ## **Q4** ***PERFORMANCE*** ###REVIEW###
                    
                    ### ***Revenue*** **Analysis**:
                    - **Total Revenue**: ***$2.5M*** (##15%## increase)
                    - **New Customers**: ***1,250*** (##25%## growth)
                    - **Market Share**: **12.8%** (###3.2%### expansion)
                    
                    #### **Key** ***Achievements***:
                    1. ***Launched*** **new product** ##successfully##
                    2. **Expanded** ***team*** by ##30%##
                    3. ###Improved### **customer** ***satisfaction*** to ##9.2/10##
                    
                    ##### ***Strategic*** **Initiatives**:
                    - **Digital** ***transformation*** ##completed##
                    - ***Cloud*** **migration** ###finished###
                    - **API** ***integration*** ##deployed##
                    
                    ###### **Next** ***Quarter*** ##Goals##:
                    1. ***Increase*** **revenue** by ##20%##
                    2. **Launch** ***mobile app***
                    3. ###Expand### **internationally**
                    
                    **_Important Notes_**:
                    - ***All*** **metrics** ##exceeded## _expectations_
                    - **Team** ***performance*** was ##outstanding##
                    - ***Customer*** **feedback** ###extremely### _positive_
                    """
                }
                
                # Create the test note
                response = await client.post(f"{BACKEND_URL}/notes", json=extreme_markdown_note, headers=headers)
                
                if response.status_code == 200:
                    note_info = response.json()
                    test_note_id = note_info.get("id")
                    self.created_note_ids.append(test_note_id)
                    
                    # Generate batch report
                    request_data = {
                        "note_ids": [test_note_id],
                        "title": "Extreme Markdown Cleaning Test"
                    }
                    
                    response = await client.post(
                        f"{BACKEND_URL}/notes/batch-comprehensive-report",
                        json=request_data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        report_data = response.json()
                        report_content = report_data.get("report", "")
                        
                        # Check for specific markdown symbols
                        symbols_found = self.detect_specific_markdown_symbols(report_content)
                        
                        if not symbols_found:
                            await self.log_test("Extreme Markdown Content Cleaning", True, 
                                              f"Successfully cleaned extreme markdown content ({len(report_content)} chars)")
                        else:
                            await self.log_test("Extreme Markdown Content Cleaning", False, 
                                              f"Found symbols: {symbols_found}")
                            print(f"Report preview: {report_content[:300]}...")
                        
                        return report_content
                    else:
                        await self.log_test("Extreme Markdown Test", False, 
                                          f"Report generation failed: {response.status_code}")
                        return None
                else:
                    await self.log_test("Extreme Markdown Test", False, 
                                      f"Note creation failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            await self.log_test("Extreme Markdown Test", False, f"Exception: {str(e)}")
            return None

    async def test_specific_symbol_combinations(self):
        """Test specific symbol combinations mentioned in the review request"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test each specific symbol combination
                symbol_tests = [
                    {
                        "name": "Triple Asterisks (***)",
                        "content": "This has ***bold italic*** text and ***multiple*** ***instances*** of triple asterisks."
                    },
                    {
                        "name": "Double Asterisks (**)",
                        "content": "This has **bold** text and **multiple** **bold** **words** throughout."
                    },
                    {
                        "name": "Single Asterisks (*)",
                        "content": "This has *italic* text and *multiple* *italic* *words* in the content."
                    },
                    {
                        "name": "Triple Hashes (###)",
                        "content": "### This is a heading\n### Another heading\n### Third heading with ###symbols###"
                    },
                    {
                        "name": "Double Hashes (##)",
                        "content": "## Main heading\n## Second heading\nText with ##embedded## symbols"
                    },
                    {
                        "name": "Single Hashes (#)",
                        "content": "# Top level heading\nText with #hashtag and #another #symbol"
                    },
                    {
                        "name": "Double Underscores (__)",
                        "content": "This has __underlined__ text and __multiple__ __instances__ of underscores."
                    },
                    {
                        "name": "Single Underscores (_)",
                        "content": "This has _italic_ text and _multiple_ _italic_ _words_ with underscores."
                    },
                    {
                        "name": "Backticks (`)",
                        "content": "This has `code` snippets and `multiple` `code` `blocks` throughout."
                    }
                ]
                
                for test_case in symbol_tests:
                    # Create note with specific symbol type
                    note_data = {
                        "title": f"Symbol Test: {test_case['name']}",
                        "kind": "text",
                        "text_content": test_case['content']
                    }
                    
                    response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                    
                    if response.status_code == 200:
                        note_info = response.json()
                        test_note_id = note_info.get("id")
                        self.created_note_ids.append(test_note_id)
                        
                        # Generate report for this specific symbol test
                        request_data = {
                            "note_ids": [test_note_id],
                            "title": f"Symbol Cleaning Test: {test_case['name']}"
                        }
                        
                        response = await client.post(
                            f"{BACKEND_URL}/notes/batch-comprehensive-report",
                            json=request_data,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            report_data = response.json()
                            report_content = report_data.get("report", "")
                            
                            # Check for the specific symbols this test targets
                            symbols_found = self.detect_specific_markdown_symbols(report_content)
                            
                            if not symbols_found:
                                await self.log_test(f"Clean {test_case['name']}", True, 
                                                  "All symbols successfully removed")
                            else:
                                await self.log_test(f"Clean {test_case['name']}", False, 
                                                  f"Found symbols: {symbols_found}")
                        else:
                            await self.log_test(f"Clean {test_case['name']}", False, 
                                              f"Report generation failed: {response.status_code}")
                    else:
                        await self.log_test(f"Clean {test_case['name']}", False, 
                                          f"Note creation failed: {response.status_code}")
                        
        except Exception as e:
            await self.log_test("Specific Symbol Tests", False, f"Exception: {str(e)}")

    async def test_modal_display_content(self):
        """Test that content displayed in modal has no markdown symbols"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Create notes for batch report
                if not self.created_note_ids:
                    # Create a simple test note if none exist
                    note_data = {
                        "title": "Modal Display Test",
                        "kind": "text",
                        "text_content": "**Test** content with ***markdown*** symbols for ##modal## display testing."
                    }
                    
                    response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                    if response.status_code == 200:
                        note_info = response.json()
                        self.created_note_ids.append(note_info.get("id"))
                
                # Generate batch report
                request_data = {
                    "note_ids": self.created_note_ids[:1],  # Use first note
                    "title": "Modal Display Content Test"
                }
                
                response = await client.post(
                    f"{BACKEND_URL}/notes/batch-comprehensive-report",
                    json=request_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    report_data = response.json()
                    report_content = report_data.get("report", "")
                    
                    # This simulates what would be displayed in the modal
                    symbols_found = self.detect_specific_markdown_symbols(report_content)
                    
                    if not symbols_found:
                        await self.log_test("Modal Display Content", True, 
                                          "Content ready for modal display - NO markdown symbols")
                    else:
                        await self.log_test("Modal Display Content", False, 
                                          f"Modal would display markdown symbols: {symbols_found}")
                        
                    # Test export formats that might be displayed
                    for format_type in ["txt", "rtf"]:
                        export_response = await client.post(
                            f"{BACKEND_URL}/notes/batch-comprehensive-report/export?format={format_type}",
                            json=report_data,
                            headers=headers
                        )
                        
                        if export_response.status_code == 200:
                            export_content = export_response.content.decode('utf-8', errors='ignore')
                            export_symbols = self.detect_specific_markdown_symbols(export_content)
                            
                            if not export_symbols:
                                await self.log_test(f"Export {format_type.upper()} for Modal", True, 
                                                  "Export content clean for modal display")
                            else:
                                await self.log_test(f"Export {format_type.upper()} for Modal", False, 
                                                  f"Export contains symbols: {export_symbols}")
                        
        except Exception as e:
            await self.log_test("Modal Display Test", False, f"Exception: {str(e)}")

    async def verify_business_report_structure(self):
        """Verify the business report structure requirements"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                if self.created_note_ids:
                    # Generate a comprehensive report
                    request_data = {
                        "note_ids": self.created_note_ids,
                        "title": "Business Structure Verification Test"
                    }
                    
                    response = await client.post(
                        f"{BACKEND_URL}/notes/batch-comprehensive-report",
                        json=request_data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        report_data = response.json()
                        report_content = report_data.get("report", "")
                        
                        # Check for required business report sections
                        required_sections = [
                            "EXECUTIVE SUMMARY",
                            "KEY INSIGHTS", 
                            "STRATEGIC RECOMMENDATIONS",
                            "RISK ASSESSMENT",
                            "IMPLEMENTATION PRIORITIES",
                            "CONCLUSION"
                        ]
                        
                        sections_found = []
                        for section in required_sections:
                            if section in report_content:
                                sections_found.append(section)
                        
                        if len(sections_found) == len(required_sections):
                            await self.log_test("Business Report Structure", True, 
                                              f"All {len(required_sections)} required sections present")
                        else:
                            missing = set(required_sections) - set(sections_found)
                            await self.log_test("Business Report Structure", False, 
                                              f"Missing sections: {missing}")
                        
                        # Check for proper bullet points (• symbol only)
                        bullet_lines = [line.strip() for line in report_content.split('\n') if line.strip().startswith('•')]
                        if bullet_lines:
                            await self.log_test("Proper Bullet Points", True, 
                                              f"Found {len(bullet_lines)} bullet points using • symbol")
                        else:
                            await self.log_test("Proper Bullet Points", False, 
                                              "No proper bullet points found")
                        
                        # Check for CAPITAL LETTERS headings (no markdown headers)
                        capital_headings = [line.strip() for line in report_content.split('\n') 
                                          if line.strip() and line.strip().isupper() and len(line.strip()) > 5]
                        
                        if capital_headings:
                            await self.log_test("Capital Letter Headings", True, 
                                              f"Found {len(capital_headings)} CAPITAL LETTER headings")
                        else:
                            await self.log_test("Capital Letter Headings", False, 
                                              "No CAPITAL LETTER headings found")
                        
        except Exception as e:
            await self.log_test("Business Structure Verification", False, f"Exception: {str(e)}")

    async def cleanup_test_data(self):
        """Clean up test data"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                for note_id in self.created_note_ids:
                    try:
                        await client.delete(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                    except:
                        pass
                
                await self.log_test("Cleanup", True, f"Cleaned up {len(self.created_note_ids)} test notes")
                
        except Exception as e:
            await self.log_test("Cleanup", False, f"Exception: {str(e)}")

    async def run_focused_tests(self):
        """Run focused markdown cleaning tests"""
        print("🎯 Starting Focused Markdown Cleaning Tests")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user - aborting tests")
            return
        
        # Run focused tests
        await self.test_extreme_markdown_content()
        await self.test_specific_symbol_combinations()
        await self.test_modal_display_content()
        await self.verify_business_report_structure()
        
        # Cleanup
        await self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
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
    tester = FocusedMarkdownCleaningTester()
    passed, total = await tester.run_focused_tests()
    
    if passed == total:
        print("\n🎉 ALL FOCUSED TESTS PASSED! Markdown cleaning is working perfectly.")
    else:
        print(f"\n⚠️  {total - passed} focused tests failed. Review the issues above.")

if __name__ == "__main__":
    asyncio.run(main())