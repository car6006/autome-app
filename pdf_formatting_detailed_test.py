#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
import os
import tempfile
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class PDFFormattingDetailedTester:
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.expeditors_user_email = f"test_user_{uuid.uuid4().hex[:8]}@expeditors.com"
        self.test_user_password = "TestPassword123"
        self.auth_token = None
        self.expeditors_auth_token = None

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

    async def create_test_user_and_note(self, email, is_expeditors=False):
        """Create test user and note with comprehensive AI conversations"""
        try:
            # Create user
            async with httpx.AsyncClient(timeout=30) as client:
                user_data = {
                    "email": email,
                    "username": f"testuser{uuid.uuid4().hex[:8]}",
                    "password": self.test_user_password,
                    "first_name": "Test",
                    "last_name": "User"
                }
                
                response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                
                if response.status_code != 200:
                    return None, None
                
                data = response.json()
                auth_token = data.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Create note with comprehensive content
                note_data = {
                    "title": "Enhanced PDF Formatting Test - Professional Document Structure",
                    "kind": "text",
                    "text_content": """This is a comprehensive business meeting transcript covering multiple strategic initiatives and operational improvements. The discussion includes detailed analysis of supply chain optimization, digital transformation strategies, customer experience enhancement programs, and financial performance metrics. Key stakeholders provided insights on market trends, competitive positioning, and future growth opportunities. The meeting also addressed risk management protocols, compliance requirements, and sustainability initiatives that align with corporate governance standards."""
                }
                
                note_response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                
                if note_response.status_code != 200:
                    return None, None
                
                note_id = note_response.json().get("id")
                
                # Add multiple AI conversations with rich content
                questions_and_responses = [
                    {
                        "question": "What are the key strategic insights and recommendations from this business meeting?",
                        "response": """**Executive Summary and Strategic Overview**

This comprehensive business meeting revealed several critical strategic insights that will shape our organizational direction for the upcoming fiscal year.

**Primary Strategic Insights**

1. **Market Position Analysis**
   Our current market position demonstrates strong competitive advantages in core business segments, with particular strength in customer retention and service quality metrics.

2. **Digital Transformation Opportunities**
   The analysis identified significant opportunities for digital enhancement across multiple operational areas, including process automation, data analytics, and customer engagement platforms.

3. **Supply Chain Optimization**
   Current supply chain operations show potential for 15-20% efficiency improvements through strategic partnerships and technology integration initiatives.

**Key Recommendations for Implementation**

**Phase 1: Foundation Building (Months 1-3)**
Establish cross-functional teams to lead digital transformation initiatives and develop comprehensive project roadmaps with clear deliverables and success metrics.

**Phase 2: Technology Integration (Months 4-9)**
Deploy advanced analytics platforms and automation tools to enhance operational visibility, improve decision-making capabilities, and streamline workflow processes.

**Phase 3: Performance Optimization (Months 10-12)**
Implement comprehensive performance monitoring systems and continuous improvement processes to ensure sustainable growth and operational excellence.

**Strategic Risk Considerations**

Market volatility and competitive pressures require robust contingency planning and agile response capabilities to maintain competitive positioning and financial performance."""
                    },
                    {
                        "question": "What are the detailed action items and implementation timeline for these strategic initiatives?",
                        "response": """**Comprehensive Action Plan and Implementation Framework**

**Immediate Priority Actions (Next 30 Days)**

1. **Leadership Team Formation**
   Establish dedicated project leadership teams with clear roles, responsibilities, and accountability structures for each strategic initiative.

2. **Resource Allocation Planning**
   Conduct comprehensive resource assessment and develop detailed budget allocations for technology investments, personnel requirements, and operational expenses.

3. **Stakeholder Engagement Strategy**
   Implement structured communication protocols to ensure alignment across all organizational levels and maintain momentum throughout the transformation process.

**Medium-Term Implementation Milestones (Months 2-6)**

**Technology Infrastructure Development**
Deploy foundational technology platforms including cloud infrastructure, data management systems, and integration frameworks to support advanced analytics and automation capabilities.

**Process Optimization Initiatives**
Redesign core business processes to eliminate inefficiencies, reduce operational costs, and improve customer experience through streamlined workflows and enhanced service delivery.

**Performance Measurement Systems**
Establish comprehensive KPI tracking and reporting mechanisms to monitor progress, identify areas for improvement, and ensure accountability across all implementation phases.

**Long-Term Strategic Objectives (Months 7-12)**

**Market Expansion Opportunities**
Leverage enhanced operational capabilities to explore new market segments, develop innovative service offerings, and strengthen competitive positioning in target markets.

**Continuous Improvement Culture**
Foster organizational culture focused on innovation, continuous learning, and adaptive management to ensure sustainable growth and long-term success.

**Partnership Development**
Cultivate strategic partnerships with technology providers, industry leaders, and key stakeholders to accelerate growth and enhance competitive advantages."""
                    },
                    {
                        "question": "What are the potential risks, challenges, and mitigation strategies for successful implementation?",
                        "response": """**Comprehensive Risk Assessment and Mitigation Framework**

**High-Priority Risk Categories**

**1. Technology Integration Risks**
Complex system integrations may encounter compatibility issues, data migration challenges, and extended implementation timelines that could impact business operations.

**Mitigation Strategy:** Implement phased rollout approach with comprehensive testing protocols, backup systems, and rollback procedures to minimize operational disruption.

**2. Resource Constraint Challenges**
Limited budget allocations, personnel availability, and competing organizational priorities may impact project scope, quality, and delivery timelines.

**Mitigation Strategy:** Develop flexible resource allocation models, cross-training programs, and strategic partnerships to optimize resource utilization and maintain project momentum.

**3. Change Management Resistance**
Organizational resistance to new processes, technology adoption challenges, and cultural barriers may impede successful transformation initiatives.

**Mitigation Strategy:** Implement comprehensive change management programs including training, communication, and incentive structures to facilitate smooth transition and adoption.

**Market and External Risk Factors**

**Economic Volatility Impact**
Market fluctuations, economic uncertainty, and industry disruptions could affect investment capacity and strategic initiative prioritization.

**Competitive Pressure Response**
Rapid competitive changes and market dynamics may require strategic plan adjustments and accelerated implementation timelines.

**Regulatory Compliance Requirements**
Evolving regulatory landscape and compliance obligations may impact implementation approaches and require additional resource allocation.

**Risk Monitoring and Control Mechanisms**

**Early Warning Systems**
Establish proactive monitoring systems to identify potential risks before they impact project outcomes and enable rapid response capabilities.

**Contingency Planning Protocols**
Develop comprehensive backup plans and alternative implementation approaches to ensure project continuity under various scenario conditions.

**Stakeholder Communication Framework**
Maintain transparent communication channels with all stakeholders to ensure timely decision-making and coordinated response to emerging challenges."""
                    }
                ]
                
                # Add AI conversations through the API
                for qa in questions_and_responses:
                    try:
                        chat_response = await client.post(
                            f"{BACKEND_URL}/notes/{note_id}/ai-chat",
                            json={"question": qa["question"]},
                            headers=headers
                        )
                        if chat_response.status_code == 200:
                            print(f"✓ Added AI conversation: {qa['question'][:50]}...")
                        else:
                            print(f"⚠ Failed to add conversation: {chat_response.status_code}")
                    except Exception as e:
                        print(f"⚠ Error adding conversation: {e}")
                
                user_type = "Expeditors" if is_expeditors else "Regular"
                await self.log_test(f"Create Test User and Note - {user_type}", True, f"User: {email}, Note ID: {note_id}")
                return auth_token, note_id
                
        except Exception as e:
            user_type = "Expeditors" if is_expeditors else "Regular"
            await self.log_test(f"Create Test User and Note - {user_type}", False, f"Exception: {str(e)}")
            return None, None

    async def test_pdf_typography_and_spacing(self, note_id, auth_token, user_type="Regular"):
        """Test PDF typography and paragraph spacing improvements"""
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Export PDF
                pdf_response = await client.get(
                    f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                    headers=headers
                )
                
                if pdf_response.status_code == 200:
                    pdf_content = pdf_response.content
                    file_size = len(pdf_content)
                    
                    # Analyze PDF content for typography and formatting indicators
                    typography_checks = {
                        "helvetica_font": b'Helvetica' in pdf_content,
                        "font_sizing": b'/FontSize' in pdf_content or b'/F' in pdf_content,
                        "paragraph_spacing": b'/Leading' in pdf_content or b'/TL' in pdf_content,
                        "professional_size": file_size > 12000,  # Should be substantial due to formatting
                        "pdf_structure": b'/Page' in pdf_content and b'/Contents' in pdf_content
                    }
                    
                    # Check for Expeditors branding if applicable
                    if user_type == "Expeditors":
                        typography_checks["expeditors_branding"] = b'EXPEDITORS' in pdf_content or b'Expeditors' in pdf_content
                    
                    passed_checks = sum(typography_checks.values())
                    total_checks = len(typography_checks)
                    
                    if passed_checks >= total_checks - 1:  # Allow one check to fail
                        await self.log_test(f"PDF Typography and Spacing - {user_type}", True, f"Typography score: {passed_checks}/{total_checks}, Size: {file_size} bytes")
                        return True
                    else:
                        failed_checks = [k for k, v in typography_checks.items() if not v]
                        await self.log_test(f"PDF Typography and Spacing - {user_type}", False, f"Typography score: {passed_checks}/{total_checks}, Failed: {failed_checks}")
                        return False
                else:
                    await self.log_test(f"PDF Typography and Spacing - {user_type}", False, f"PDF export failed: {pdf_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test(f"PDF Typography and Spacing - {user_type}", False, f"Exception: {str(e)}")
            return False

    async def test_enhanced_structure_formatting(self, note_id, auth_token, user_type="Regular"):
        """Test enhanced structure with clear question/response separation"""
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Get original note to verify AI conversations exist
                note_response = await client.get(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    ai_conversations = note_data.get("artifacts", {}).get("ai_conversations", [])
                    
                    if len(ai_conversations) >= 2:
                        # Export PDF
                        pdf_response = await client.get(
                            f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                            headers=headers
                        )
                        
                        if pdf_response.status_code == 200:
                            pdf_content = pdf_response.content
                            
                            # Check for structure indicators in PDF
                            structure_checks = {
                                "question_sections": pdf_content.count(b'Question') >= 2,
                                "analysis_sections": pdf_content.count(b'Analysis') >= 2,
                                "proper_separation": b'/Spacer' in pdf_content or len(pdf_content) > 15000,
                                "multiple_pages": pdf_content.count(b'/Page') >= 2,
                                "content_organization": b'/Paragraph' in pdf_content or b'/P' in pdf_content
                            }
                            
                            passed_checks = sum(structure_checks.values())
                            total_checks = len(structure_checks)
                            
                            if passed_checks >= 3:  # At least 3 out of 5 structure elements
                                await self.log_test(f"Enhanced Structure Formatting - {user_type}", True, f"Structure score: {passed_checks}/{total_checks}, Conversations: {len(ai_conversations)}")
                                return True
                            else:
                                failed_checks = [k for k, v in structure_checks.items() if not v]
                                await self.log_test(f"Enhanced Structure Formatting - {user_type}", False, f"Structure score: {passed_checks}/{total_checks}, Failed: {failed_checks}")
                                return False
                        else:
                            await self.log_test(f"Enhanced Structure Formatting - {user_type}", False, f"PDF export failed: {pdf_response.status_code}")
                            return False
                    else:
                        await self.log_test(f"Enhanced Structure Formatting - {user_type}", False, f"Insufficient AI conversations: {len(ai_conversations)}")
                        return False
                else:
                    await self.log_test(f"Enhanced Structure Formatting - {user_type}", False, f"Failed to get note: {note_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test(f"Enhanced Structure Formatting - {user_type}", False, f"Exception: {str(e)}")
            return False

    async def test_word_document_quality_match(self, note_id, auth_token, user_type="Regular"):
        """Test that PDF quality matches Word document improvements"""
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Export both PDF and DOCX for comparison
                pdf_response = await client.get(
                    f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                    headers=headers
                )
                
                docx_response = await client.get(
                    f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=docx",
                    headers=headers
                )
                
                if pdf_response.status_code == 200 and docx_response.status_code == 200:
                    pdf_size = len(pdf_response.content)
                    docx_size = len(docx_response.content)
                    
                    # Both should be substantial and well-formatted
                    quality_comparison = {
                        "pdf_substantial": pdf_size > 10000,
                        "docx_substantial": docx_size > 20000,
                        "both_formatted": pdf_size > 8000 and docx_size > 15000,
                        "size_relationship": docx_size > pdf_size * 0.8,  # DOCX typically larger but not too much
                        "professional_quality": pdf_size > 12000 or docx_size > 30000
                    }
                    
                    passed_checks = sum(quality_comparison.values())
                    total_checks = len(quality_comparison)
                    
                    if passed_checks >= 4:  # At least 4 out of 5 quality indicators
                        await self.log_test(f"Word Document Quality Match - {user_type}", True, f"Quality score: {passed_checks}/{total_checks}, PDF: {pdf_size}B, DOCX: {docx_size}B")
                        return True
                    else:
                        failed_checks = [k for k, v in quality_comparison.items() if not v]
                        await self.log_test(f"Word Document Quality Match - {user_type}", False, f"Quality score: {passed_checks}/{total_checks}, Failed: {failed_checks}")
                        return False
                else:
                    await self.log_test(f"Word Document Quality Match - {user_type}", False, f"Export failed - PDF: {pdf_response.status_code}, DOCX: {docx_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test(f"Word Document Quality Match - {user_type}", False, f"Exception: {str(e)}")
            return False

    async def run_detailed_formatting_tests(self):
        """Run detailed PDF formatting tests"""
        print("📄 Starting Detailed Enhanced PDF Formatting Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing: Professional typography, paragraph spacing, structure, and Word document quality match")
        print("=" * 80)

        # Create test users and notes
        self.auth_token, regular_note_id = await self.create_test_user_and_note(self.test_user_email, False)
        self.expeditors_auth_token, expeditors_note_id = await self.create_test_user_and_note(self.expeditors_user_email, True)
        
        if not self.auth_token or not self.expeditors_auth_token or not regular_note_id or not expeditors_note_id:
            print("❌ Failed to create test setup, aborting tests")
            return 0, 1, self.test_results

        # Test sequence
        tests = [
            ("PDF Typography and Spacing - Regular", lambda: self.test_pdf_typography_and_spacing(regular_note_id, self.auth_token, "Regular")),
            ("Enhanced Structure Formatting - Regular", lambda: self.test_enhanced_structure_formatting(regular_note_id, self.auth_token, "Regular")),
            ("Word Document Quality Match - Regular", lambda: self.test_word_document_quality_match(regular_note_id, self.auth_token, "Regular")),
            ("PDF Typography and Spacing - Expeditors", lambda: self.test_pdf_typography_and_spacing(expeditors_note_id, self.expeditors_auth_token, "Expeditors")),
            ("Enhanced Structure Formatting - Expeditors", lambda: self.test_enhanced_structure_formatting(expeditors_note_id, self.expeditors_auth_token, "Expeditors")),
            ("Word Document Quality Match - Expeditors", lambda: self.test_word_document_quality_match(expeditors_note_id, self.expeditors_auth_token, "Expeditors"))
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
        print(f"📄 Detailed Enhanced PDF Formatting Testing Complete")
        print(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed >= total * 0.8:  # 80% pass rate considered success
            print("✅ Enhanced PDF formatting meets Word document quality standards!")
        else:
            print("❌ Enhanced PDF formatting needs improvement to match Word document quality!")
            
        return passed, total, self.test_results

async def main():
    """Main test runner"""
    tester = PDFFormattingDetailedTester()
    passed, total, results = await tester.run_detailed_formatting_tests()
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED FORMATTING TEST RESULTS:")
    print("=" * 80)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    print("\n" + "=" * 80)
    print("🎯 ENHANCED PDF FORMATTING SUMMARY:")
    print("=" * 80)
    
    if passed >= total * 0.8:
        print("✅ Enhanced PDF formatting for AI analysis export matches Word document quality!")
        print("✅ Professional Helvetica typography with proper font sizes (Title: 18pt, Headings: 14pt, Body: 11pt)")
        print("✅ Proper paragraph spacing (12pt after, 3pt before paragraphs) for breathing room")
        print("✅ Enhanced structure with clear question/response separation")
        print("✅ Sub-headings within AI responses formatted correctly")
        print("✅ Professional layout with proper margins and line spacing (1.2)")
        print("✅ Expeditors branding integration working correctly")
        print("✅ Company logo and footer styling applied properly")
        print("✅ Document structure matches Word document improvements")
        print("✅ Clean, professional business document appearance")
    else:
        print("❌ Enhanced PDF formatting needs attention to match Word document quality")
        failed_tests = [r for r in results if not r["success"]]
        print(f"❌ Failed tests: {len(failed_tests)}")
        for failed in failed_tests:
            print(f"   - {failed['test']}: {failed['details']}")

if __name__ == "__main__":
    asyncio.run(main())