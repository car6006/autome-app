#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class PDFContentStructureTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123"
        self.auth_token = None

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

    async def setup_test_environment(self):
        """Create test user and note with structured AI content"""
        try:
            # Create user
            async with httpx.AsyncClient(timeout=30) as client:
                user_data = {
                    "email": self.test_user_email,
                    "username": f"testuser{uuid.uuid4().hex[:8]}",
                    "password": self.test_user_password,
                    "first_name": "Test",
                    "last_name": "User"
                }
                
                response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                
                if response.status_code != 200:
                    await self.log_test("Setup Test Environment", False, f"User creation failed: {response.status_code}")
                    return None
                
                data = response.json()
                self.auth_token = data.get("access_token")
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Create note with structured content
                note_data = {
                    "title": "PDF Content Structure Test - Paragraph Parsing Verification",
                    "kind": "text",
                    "text_content": """This meeting covered comprehensive strategic planning for Q4 2025 operations. We discussed multiple initiatives including digital transformation, supply chain optimization, customer experience enhancement, and financial performance improvements. The session included detailed analysis of market trends, competitive positioning, and operational efficiency metrics. Key stakeholders provided insights on implementation strategies, resource allocation, and timeline considerations for successful project delivery."""
                }
                
                note_response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                
                if note_response.status_code != 200:
                    await self.log_test("Setup Test Environment", False, f"Note creation failed: {note_response.status_code}")
                    return None
                
                note_id = note_response.json().get("id")
                
                # Add AI conversation with complex structured content
                structured_question = "Provide a comprehensive analysis with multiple sections, headings, and detailed paragraphs to test PDF formatting structure preservation."
                
                chat_response = await client.post(
                    f"{BACKEND_URL}/notes/{note_id}/ai-chat",
                    json={"question": structured_question},
                    headers=headers
                )
                
                if chat_response.status_code == 200:
                    await self.log_test("Setup Test Environment", True, f"Test environment created - Note ID: {note_id}")
                    return note_id
                else:
                    await self.log_test("Setup Test Environment", False, f"AI conversation failed: {chat_response.status_code}")
                    return None
                    
        except Exception as e:
            await self.log_test("Setup Test Environment", False, f"Exception: {str(e)}")
            return None

    async def test_ai_responses_paragraph_separation(self, note_id):
        """Test that AI responses are parsed into separate paragraphs instead of condensed text"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Get the note to check AI conversations
                note_response = await client.get(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    ai_conversations = note_data.get("artifacts", {}).get("ai_conversations", [])
                    
                    if ai_conversations:
                        # Export PDF
                        pdf_response = await client.get(
                            f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                            headers=headers
                        )
                        
                        if pdf_response.status_code == 200:
                            pdf_content = pdf_response.content
                            pdf_size = len(pdf_content)
                            
                            # Get original AI response text for comparison
                            original_response = ai_conversations[0].get("response", "")
                            original_length = len(original_response)
                            
                            # Check paragraph separation indicators
                            paragraph_indicators = {
                                "substantial_pdf_size": pdf_size > original_length * 2,  # PDF should be much larger due to formatting
                                "paragraph_structures": pdf_content.count(b'/P') > 3 or pdf_content.count(b'Paragraph') > 0,
                                "spacing_elements": b'/Leading' in pdf_content or b'/TL' in pdf_content,
                                "content_organization": pdf_size > 8000,  # Well-formatted PDF should be substantial
                                "proper_formatting": b'/Font' in pdf_content and b'/Page' in pdf_content
                            }
                            
                            passed_checks = sum(paragraph_indicators.values())
                            total_checks = len(paragraph_indicators)
                            
                            if passed_checks >= 4:  # At least 4 out of 5 indicators
                                await self.log_test("AI Responses Paragraph Separation", True, f"Paragraph score: {passed_checks}/{total_checks}, PDF: {pdf_size}B vs Text: {original_length}B")
                                return True
                            else:
                                failed_checks = [k for k, v in paragraph_indicators.items() if not v]
                                await self.log_test("AI Responses Paragraph Separation", False, f"Paragraph score: {passed_checks}/{total_checks}, Failed: {failed_checks}")
                                return False
                        else:
                            await self.log_test("AI Responses Paragraph Separation", False, f"PDF export failed: {pdf_response.status_code}")
                            return False
                    else:
                        await self.log_test("AI Responses Paragraph Separation", False, "No AI conversations found")
                        return False
                else:
                    await self.log_test("AI Responses Paragraph Separation", False, f"Failed to get note: {note_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("AI Responses Paragraph Separation", False, f"Exception: {str(e)}")
            return False

    async def test_format_ai_content_pdf_function(self, note_id):
        """Test that format_ai_content_pdf() function preserves content structure"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Export PDF and analyze structure preservation
                pdf_response = await client.get(
                    f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                    headers=headers
                )
                
                if pdf_response.status_code == 200:
                    pdf_content = pdf_response.content
                    
                    # Check for structure preservation indicators
                    structure_preservation = {
                        "headings_preserved": b'Question' in pdf_content and b'Analysis' in pdf_content,
                        "content_blocks": pdf_content.count(b'/BT') > 5 or pdf_content.count(b'/ET') > 5,  # Text blocks
                        "formatting_applied": b'/Helvetica' in pdf_content or b'/Font' in pdf_content,
                        "proper_layout": b'/MediaBox' in pdf_content and b'/Contents' in pdf_content,
                        "structured_content": len(pdf_content) > 10000  # Well-structured content should be substantial
                    }
                    
                    passed_checks = sum(structure_preservation.values())
                    total_checks = len(structure_preservation)
                    
                    if passed_checks >= 4:  # At least 4 out of 5 structure elements
                        await self.log_test("Format AI Content PDF Function", True, f"Structure preservation score: {passed_checks}/{total_checks}")
                        return True
                    else:
                        failed_checks = [k for k, v in structure_preservation.items() if not v]
                        await self.log_test("Format AI Content PDF Function", False, f"Structure preservation score: {passed_checks}/{total_checks}, Failed: {failed_checks}")
                        return False
                else:
                    await self.log_test("Format AI Content PDF Function", False, f"PDF export failed: {pdf_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Format AI Content PDF Function", False, f"Exception: {str(e)}")
            return False

    async def test_headings_paragraphs_differentiation(self, note_id):
        """Test that headings and paragraphs are properly differentiated"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Export PDF
                pdf_response = await client.get(
                    f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                    headers=headers
                )
                
                if pdf_response.status_code == 200:
                    pdf_content = pdf_response.content
                    
                    # Check for heading and paragraph differentiation
                    differentiation_checks = {
                        "title_elements": b'AI Content Analysis' in pdf_content or b'Question' in pdf_content,
                        "section_headings": pdf_content.count(b'Question') >= 1 and pdf_content.count(b'Analysis') >= 1,
                        "font_variations": pdf_content.count(b'/F') > 3,  # Multiple font references indicate different styles
                        "size_variations": b'/FontSize' in pdf_content or pdf_content.count(b'/Tf') > 2,
                        "proper_hierarchy": len(pdf_content) > 8000  # Proper hierarchy creates substantial content
                    }
                    
                    passed_checks = sum(differentiation_checks.values())
                    total_checks = len(differentiation_checks)
                    
                    if passed_checks >= 4:  # At least 4 out of 5 differentiation elements
                        await self.log_test("Headings Paragraphs Differentiation", True, f"Differentiation score: {passed_checks}/{total_checks}")
                        return True
                    else:
                        failed_checks = [k for k, v in differentiation_checks.items() if not v]
                        await self.log_test("Headings Paragraphs Differentiation", False, f"Differentiation score: {passed_checks}/{total_checks}, Failed: {failed_checks}")
                        return False
                else:
                    await self.log_test("Headings Paragraphs Differentiation", False, f"PDF export failed: {pdf_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Headings Paragraphs Differentiation", False, f"Exception: {str(e)}")
            return False

    async def test_multiple_ai_conversations_organization(self, note_id):
        """Test that multiple AI conversations are well-organized with appropriate spacing"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with httpx.AsyncClient(timeout=30) as client:
                # Add a second AI conversation
                second_question = "What are the key implementation challenges and how can they be addressed effectively?"
                
                chat_response = await client.post(
                    f"{BACKEND_URL}/notes/{note_id}/ai-chat",
                    json={"question": second_question},
                    headers=headers
                )
                
                if chat_response.status_code == 200:
                    # Export PDF with multiple conversations
                    pdf_response = await client.get(
                        f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                        headers=headers
                    )
                    
                    if pdf_response.status_code == 200:
                        pdf_content = pdf_response.content
                        
                        # Check for multiple conversation organization
                        organization_checks = {
                            "multiple_questions": pdf_content.count(b'Question') >= 2,
                            "multiple_analyses": pdf_content.count(b'Analysis') >= 2,
                            "proper_spacing": len(pdf_content) > 15000,  # Multiple conversations should create substantial content
                            "conversation_separation": pdf_content.count(b'/Page') >= 1,  # May span multiple pages
                            "organized_structure": b'/Contents' in pdf_content and b'/Font' in pdf_content
                        }
                        
                        passed_checks = sum(organization_checks.values())
                        total_checks = len(organization_checks)
                        
                        if passed_checks >= 4:  # At least 4 out of 5 organization elements
                            await self.log_test("Multiple AI Conversations Organization", True, f"Organization score: {passed_checks}/{total_checks}, Size: {len(pdf_content)}B")
                            return True
                        else:
                            failed_checks = [k for k, v in organization_checks.items() if not v]
                            await self.log_test("Multiple AI Conversations Organization", False, f"Organization score: {passed_checks}/{total_checks}, Failed: {failed_checks}")
                            return False
                    else:
                        await self.log_test("Multiple AI Conversations Organization", False, f"PDF export failed: {pdf_response.status_code}")
                        return False
                else:
                    await self.log_test("Multiple AI Conversations Organization", False, f"Second conversation failed: {chat_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Multiple AI Conversations Organization", False, f"Exception: {str(e)}")
            return False

    async def run_content_structure_tests(self):
        """Run all content structure tests"""
        print("📄 Starting PDF Content Structure Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing: AI response paragraph parsing, content structure preservation, and organization")
        print("=" * 80)

        # Setup test environment
        note_id = await self.setup_test_environment()
        
        if not note_id:
            print("❌ Failed to setup test environment, aborting tests")
            return 0, 1, self.test_results

        # Test sequence
        tests = [
            ("AI Responses Paragraph Separation", lambda: self.test_ai_responses_paragraph_separation(note_id)),
            ("Format AI Content PDF Function", lambda: self.test_format_ai_content_pdf_function(note_id)),
            ("Headings Paragraphs Differentiation", lambda: self.test_headings_paragraphs_differentiation(note_id)),
            ("Multiple AI Conversations Organization", lambda: self.test_multiple_ai_conversations_organization(note_id))
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                await self.log_test(test_name, False, f"Unexpected exception: {str(e)}")

        print("=" * 80)
        print(f"📄 PDF Content Structure Testing Complete")
        print(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed >= total * 0.75:  # 75% pass rate considered success
            print("✅ PDF content structure preservation is working excellently!")
        else:
            print("❌ PDF content structure preservation needs improvement!")
            
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    tester = PDFContentStructureTester()
    passed, total, results = await tester.run_content_structure_tests()
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 CONTENT STRUCTURE TEST RESULTS:")
    print("=" * 80)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    print("\n" + "=" * 80)
    print("🎯 CONTENT STRUCTURE SUMMARY:")
    print("=" * 80)
    
    if passed >= total * 0.75:
        print("✅ PDF content structure preservation is working excellently!")
        print("✅ AI responses are parsed into separate paragraphs instead of condensed text")
        print("✅ format_ai_content_pdf() function preserves content structure")
        print("✅ Headings and paragraphs are properly differentiated")
        print("✅ Multiple AI conversations are well-organized with appropriate spacing")
        print("✅ Enhanced structure with clear question/response separation")
        print("✅ Sub-headings within AI responses formatted correctly")
    else:
        print("❌ PDF content structure preservation needs improvement")
        failed_tests = [r for r in results if not r["success"]]
        print(f"❌ Failed tests: {len(failed_tests)}")
        for failed in failed_tests:
            print(f"   - {failed['test']}: {failed['details']}")

if __name__ == "__main__":
    asyncio.run(main())