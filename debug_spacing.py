#!/usr/bin/env python3

import asyncio
import httpx
import tempfile
from docx import Document
from docx.shared import Pt

# Backend URL
BACKEND_URL = "https://autome-fix.preview.emergentagent.com/api"

async def debug_spacing():
    """Debug the actual spacing values in the generated Word document"""
    
    # Use existing test user credentials (from previous test)
    test_email = "test_user_737b0bfe@example.com"
    test_password = "TestPassword123"
    
    try:
        # Login to get token
        async with httpx.AsyncClient(timeout=30) as client:
            login_response = await client.post(
                f"{BACKEND_URL}/auth/login",
                json={"email": test_email, "password": test_password}
            )
            
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.status_code}")
                return
            
            auth_token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # Get the test note ID (from previous test)
            note_id = "65770402-67aa-4ffd-a26a-6caf42558c64"
            
            # Export Word document
            export_response = await client.get(
                f"{BACKEND_URL}/notes/{note_id}/ai-conversations/export?format=docx",
                headers=headers
            )
            
            if export_response.status_code != 200:
                print(f"❌ Export failed: {export_response.status_code}")
                return
            
            # Save and analyze document
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file.write(export_response.content)
                temp_file_path = temp_file.name
            
            doc = Document(temp_file_path)
            
            print("🔍 DEBUGGING PARAGRAPH SPACING:")
            print("=" * 80)
            
            body_text_count = 0
            ai_body_style_count = 0
            
            for i, paragraph in enumerate(doc.paragraphs[:20]):  # Check first 20 paragraphs
                para_format = paragraph.paragraph_format
                
                # Get spacing values
                space_before = para_format.space_before.pt if para_format.space_before else 0
                space_after = para_format.space_after.pt if para_format.space_after else 0
                
                style_name = paragraph.style.name
                text_preview = paragraph.text[:60] + "..." if len(paragraph.text) > 60 else paragraph.text
                
                is_body_text = style_name == 'AI Body Text'
                if is_body_text:
                    ai_body_style_count += 1
                
                # Check if this looks like body text (not heading)
                is_likely_body = (
                    len(paragraph.text.strip()) > 20 and 
                    not any(run.font.bold for run in paragraph.runs if run.font.bold is not None) and
                    not style_name.startswith('Heading')
                )
                
                if is_likely_body:
                    body_text_count += 1
                
                print(f"Para {i:2d}: Style='{style_name}' | Before={space_before:4.1f}pt | After={space_after:4.1f}pt")
                print(f"        Text: {text_preview}")
                print(f"        AI Body Style: {is_body_text} | Likely Body: {is_likely_body}")
                print()
            
            print("=" * 80)
            print(f"📊 SUMMARY:")
            print(f"Total paragraphs analyzed: 20")
            print(f"Paragraphs with 'AI Body Text' style: {ai_body_style_count}")
            print(f"Paragraphs that look like body text: {body_text_count}")
            
            # Check the style definition itself
            styles = doc.styles
            if 'AI Body Text' in [s.name for s in styles]:
                ai_body_style = styles['AI Body Text']
                style_space_before = ai_body_style.paragraph_format.space_before.pt if ai_body_style.paragraph_format.space_before else 0
                style_space_after = ai_body_style.paragraph_format.space_after.pt if ai_body_style.paragraph_format.space_after else 0
                
                print(f"'AI Body Text' style definition:")
                print(f"  - space_before: {style_space_before}pt")
                print(f"  - space_after: {style_space_after}pt")
            else:
                print("❌ 'AI Body Text' style not found in document")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_spacing())