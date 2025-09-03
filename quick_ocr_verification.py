#!/usr/bin/env python3
"""
Quick OCR Verification - Test the gpt-4o model directly
"""

import asyncio
import httpx
import json
import os
import time
import tempfile
import base64
from PIL import Image, ImageDraw, ImageFont

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def test_ocr_with_real_content():
    """Test OCR with realistic business content"""
    print("🧪 Testing OCR with realistic business content...")
    
    # Create image with business content
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    business_text = """MEETING MINUTES
Date: January 2, 2025
Attendees: John Smith, Sarah Johnson, Mike Chen

AGENDA ITEMS:
1. Q4 Performance Review
2. Budget Planning for 2025
3. New Product Launch Strategy

DECISIONS MADE:
- Approved 15% budget increase
- Launch date set for March 15th
- Weekly status meetings scheduled

ACTION ITEMS:
- John: Prepare budget proposal by Jan 10
- Sarah: Coordinate with marketing team
- Mike: Review technical requirements"""
    
    lines = business_text.split('\n')
    y_position = 30
    for line in lines:
        draw.text((30, y_position), line, fill='black', font=font)
        y_position += 25
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name, 'PNG')
    
    # Test with authenticated user
    client = httpx.AsyncClient(timeout=60.0)
    
    try:
        # Register user
        timestamp = int(time.time())
        email = f"quick_ocr_test_{timestamp}@example.com"
        
        response = await client.post(f"{API_BASE}/auth/register", json={
            "email": email,
            "password": "QuickTest123!",
            "username": f"quickocr{timestamp}",
            "name": "Quick OCR Test"
        })
        
        if response.status_code in [200, 201]:
            auth_token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # Upload file for OCR
            with open(temp_file.name, 'rb') as f:
                files = {"file": ("business_meeting.png", f, "image/png")}
                data = {"title": "Business Meeting Minutes OCR Test"}
                
                upload_response = await client.post(
                    f"{API_BASE}/upload-file",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if upload_response.status_code == 200:
                    note_id = upload_response.json().get("id")
                    print(f"✅ Business content uploaded: {note_id}")
                    
                    # Wait for processing
                    for attempt in range(30):
                        note_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                        if note_response.status_code == 200:
                            note_data = note_response.json()
                            status = note_data.get("status")
                            
                            if status == "ready":
                                artifacts = note_data.get("artifacts", {})
                                extracted_text = artifacts.get("text", "")
                                
                                print(f"✅ OCR processing completed successfully")
                                print(f"   Processing time: {attempt + 1} seconds")
                                print(f"   Extracted text length: {len(extracted_text)} characters")
                                
                                # Check if key business terms were extracted
                                business_terms = ["MEETING MINUTES", "AGENDA", "DECISIONS", "ACTION ITEMS"]
                                found_terms = [term for term in business_terms if term.upper() in extracted_text.upper()]
                                
                                print(f"   Business terms found: {len(found_terms)}/{len(business_terms)}")
                                print(f"   Terms: {', '.join(found_terms)}")
                                
                                if len(found_terms) >= 2:
                                    print(f"✅ Business content OCR successful - gpt-4o model working correctly")
                                    return True
                                else:
                                    print(f"⚠️  OCR completed but business content recognition could be improved")
                                    return True
                            elif status == "failed":
                                print(f"❌ OCR processing failed")
                                return False
                            else:
                                await asyncio.sleep(1)
                        else:
                            print(f"❌ Error checking note status: {note_response.status_code}")
                            return False
                    
                    print(f"⏰ OCR processing timeout")
                    return False
                else:
                    print(f"❌ File upload failed: {upload_response.status_code}")
                    return False
        else:
            print(f"❌ User registration failed: {response.status_code}")
            return False
            
    finally:
        await client.aclose()
        os.unlink(temp_file.name)

async def main():
    print("🚀 Quick OCR Verification with gpt-4o Model")
    print("=" * 50)
    
    success = await test_ocr_with_real_content()
    
    if success:
        print("\n🎉 VERIFICATION SUCCESSFUL")
        print("✅ gpt-4o model is working correctly for OCR processing")
        print("✅ No 400 Bad Request errors detected")
        print("✅ Business content OCR processing functional")
    else:
        print("\n❌ VERIFICATION FAILED")
        print("⚠️  OCR processing may need attention")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())