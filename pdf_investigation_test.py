#!/usr/bin/env python3

import asyncio
import httpx
import json
import uuid
from datetime import datetime

# Backend URL from frontend environment
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

class PDFInvestigationTester:
    def __init__(self):
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123"
        self.auth_token = None

    async def setup_and_investigate(self):
        """Setup test and investigate PDF content"""
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
                    print(f"❌ User creation failed: {response.status_code}")
                    return
                
                data = response.json()
                self.auth_token = data.get("access_token")
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Create note
                note_data = {
                    "title": "PDF Investigation Test Note",
                    "kind": "text",
                    "text_content": "This is a test meeting about supply chain optimization and digital transformation initiatives."
                }
                
                note_response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                
                if note_response.status_code != 200:
                    print(f"❌ Note creation failed: {note_response.status_code}")
                    return
                
                note_id = note_response.json().get("id")
                print(f"✅ Created note with ID: {note_id}")
                
                # Add AI conversation
                question = "What are the key insights from this meeting?"
                chat_response = await client.post(
                    f"{BACKEND_URL}/notes/{note_id}/ai-chat",
                    json={"question": question},
                    headers=headers
                )
                
                if chat_response.status_code == 200:
                    print(f"✅ Added AI conversation successfully")
                    chat_data = chat_response.json()
                    print(f"   AI Response length: {len(chat_data.get('response', ''))}")
                else:
                    print(f"❌ AI conversation failed: {chat_response.status_code}")
                    return
                
                # Get note to check AI conversations
                note_check = await client.get(f"{BACKEND_URL}/notes/{note_id}", headers=headers)
                if note_check.status_code == 200:
                    note_data = note_check.json()
                    ai_conversations = note_data.get("artifacts", {}).get("ai_conversations", [])
                    print(f"✅ Note has {len(ai_conversations)} AI conversations")
                    
                    if ai_conversations:
                        first_conv = ai_conversations[0]
                        print(f"   Question: {first_conv.get('question', '')[:100]}...")
                        print(f"   Response length: {len(first_conv.get('response', ''))}")
                        print(f"   Response preview: {first_conv.get('response', '')[:200]}...")
                
                # Test all export formats
                formats = ["txt", "rtf", "pdf", "docx"]
                format_results = {}
                
                for format_type in formats:
                    try:
                        export_response = await client.get(
                            f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format={format_type}",
                            headers=headers
                        )
                        
                        if export_response.status_code == 200:
                            content_size = len(export_response.content)
                            content_type = export_response.headers.get("content-type", "")
                            format_results[format_type] = {
                                "size": content_size,
                                "content_type": content_type,
                                "success": True
                            }
                            print(f"✅ {format_type.upper()} export: {content_size} bytes, type: {content_type}")
                        else:
                            format_results[format_type] = {
                                "size": 0,
                                "content_type": "",
                                "success": False,
                                "error": export_response.status_code
                            }
                            print(f"❌ {format_type.upper()} export failed: {export_response.status_code}")
                            print(f"   Error: {export_response.text}")
                    except Exception as e:
                        print(f"❌ {format_type.upper()} export exception: {e}")
                
                # Analyze PDF content if available
                if format_results.get("pdf", {}).get("success"):
                    pdf_response = await client.get(
                        f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=pdf",
                        headers=headers
                    )
                    
                    if pdf_response.status_code == 200:
                        pdf_content = pdf_response.content
                        print(f"\n📄 PDF Content Analysis:")
                        print(f"   Size: {len(pdf_content)} bytes")
                        print(f"   Starts with PDF header: {pdf_content.startswith(b'%PDF')}")
                        
                        # Check for specific content
                        content_checks = {
                            "Question text": b'Question' in pdf_content,
                            "Analysis text": b'Analysis' in pdf_content,
                            "Helvetica font": b'Helvetica' in pdf_content,
                            "Font references": pdf_content.count(b'/Font'),
                            "Page references": pdf_content.count(b'/Page'),
                            "Text blocks": pdf_content.count(b'/BT') + pdf_content.count(b'/ET'),
                            "Content streams": pdf_content.count(b'/Contents'),
                        }
                        
                        for check, result in content_checks.items():
                            if isinstance(result, bool):
                                print(f"   {check}: {'✅' if result else '❌'}")
                            else:
                                print(f"   {check}: {result}")
                        
                        # Save PDF for manual inspection
                        with open("/tmp/test_export.pdf", "wb") as f:
                            f.write(pdf_content)
                        print(f"   PDF saved to /tmp/test_export.pdf for manual inspection")
                
                # Compare format sizes
                print(f"\n📊 Format Size Comparison:")
                for format_type, result in format_results.items():
                    if result.get("success"):
                        print(f"   {format_type.upper()}: {result['size']} bytes")
                
                # Check if PDF is substantially larger than TXT (indicating formatting)
                txt_size = format_results.get("txt", {}).get("size", 0)
                pdf_size = format_results.get("pdf", {}).get("size", 0)
                
                if txt_size > 0 and pdf_size > 0:
                    ratio = pdf_size / txt_size
                    print(f"\n📈 PDF to TXT size ratio: {ratio:.2f}x")
                    if ratio > 1.5:
                        print("✅ PDF appears to have substantial formatting (good)")
                    else:
                        print("⚠️ PDF may have minimal formatting")
                        
        except Exception as e:
            print(f"❌ Investigation failed: {e}")

async def main():
    """Main investigation runner"""
    print("🔍 Starting PDF Export Investigation...")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    tester = PDFInvestigationTester()
    await tester.setup_and_investigate()
    
    print("\n" + "=" * 80)
    print("🎯 Investigation Complete")

if __name__ == "__main__":
    asyncio.run(main())