#!/usr/bin/env python3
"""
OCR Fix Verification Test Suite
Testing the critical fix where OCR model was changed from "gpt-4o-mini" to "gpt-4o" in providers.py line 320
"""

import asyncio
import httpx
import json
import os
import time
import tempfile
import base64
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OCRFixTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.auth_token = None
        timestamp = int(time.time())
        self.test_user_email = f"ocr_fix_test_{timestamp}@example.com"
        self.test_user_password = "OCRTestPassword123!"
        self.username = f"ocrfixtest{timestamp}"
        
    async def cleanup(self):
        """Clean up HTTP client"""
        await self.client.aclose()
    
    def create_test_image_with_text(self, text="OCR Test Document\nThis is a test image for OCR processing.\nModel: gpt-4o verification"):
        """Create a test image with readable text"""
        # Create a white image
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a better font if available
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Draw text on image
        lines = text.split('\n')
        y_position = 50
        for line in lines:
            draw.text((50, y_position), line, fill='black', font=font)
            y_position += 40
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name, 'PNG')
        return temp_file.name
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            response = await self.client.post(f"{API_BASE}/auth/register", json={
                "email": self.test_user_email,
                "password": self.test_user_password,
                "username": self.username,
                "name": "OCR Fix Test User"
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Test user registered: {self.test_user_email}")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ User registration error: {str(e)}")
            return False
    
    async def test_photo_note_creation_with_ocr(self):
        """Test 1: Create photo note and upload image for OCR processing"""
        print("\n🧪 Test 1: Photo Note Creation with OCR Processing")
        
        try:
            # Create test image
            image_file = self.create_test_image_with_text()
            
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Create photo note
            response = await self.client.post(f"{API_BASE}/notes", 
                headers=headers,
                json={
                    "title": "OCR Test Note - gpt-4o Model Verification",
                    "kind": "photo"
                }
            )
            
            if response.status_code in [200, 201]:
                note_data = response.json()
                note_id = note_data.get("id")
                print(f"✅ Photo note created: {note_id}")
                
                # Upload image for OCR processing
                with open(image_file, 'rb') as f:
                    files = {"file": ("test_ocr.png", f, "image/png")}
                    
                    upload_response = await self.client.post(
                        f"{API_BASE}/notes/{note_id}/upload",
                        headers=headers,
                        files=files
                    )
                    
                    if upload_response.status_code == 200:
                        print(f"✅ Image uploaded successfully for OCR processing")
                        
                        # Wait for processing and check status
                        await self.wait_for_processing_completion(note_id, headers)
                        
                        # Verify OCR results
                        final_note = await self.get_note_details(note_id, headers)
                        if final_note:
                            artifacts = final_note.get("artifacts", {})
                            extracted_text = artifacts.get("text", "")
                            
                            if extracted_text and len(extracted_text) > 10:
                                print(f"✅ OCR processing successful with gpt-4o model")
                                print(f"   Extracted text length: {len(extracted_text)} characters")
                                print(f"   Sample text: {extracted_text[:100]}...")
                                
                                # Clean up
                                os.unlink(image_file)
                                return True, note_id, extracted_text
                            else:
                                print(f"❌ OCR processing failed - no text extracted")
                                os.unlink(image_file)
                                return False, note_id, ""
                        else:
                            print(f"❌ Could not retrieve note details after processing")
                            os.unlink(image_file)
                            return False, note_id, ""
                    else:
                        print(f"❌ Image upload failed: {upload_response.status_code} - {upload_response.text}")
                        os.unlink(image_file)
                        return False, note_id, ""
            else:
                print(f"❌ Photo note creation failed: {response.status_code} - {response.text}")
                os.unlink(image_file)
                return False, None, ""
                
        except Exception as e:
            print(f"❌ Photo note OCR test error: {str(e)}")
            return False, None, ""
    
    async def test_direct_file_upload_ocr(self):
        """Test 2: Direct file upload for OCR processing"""
        print("\n🧪 Test 2: Direct File Upload OCR Processing")
        
        try:
            # Create test image with different text
            image_file = self.create_test_image_with_text("Direct Upload OCR Test\nVerifying gpt-4o model fix\nNo more 400 Bad Request errors!")
            
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Direct file upload
            with open(image_file, 'rb') as f:
                files = {"file": ("direct_ocr_test.png", f, "image/png")}
                data = {"title": "Direct Upload OCR Test - gpt-4o"}
                
                response = await self.client.post(
                    f"{API_BASE}/upload-file",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    upload_data = response.json()
                    note_id = upload_data.get("id")
                    print(f"✅ Direct file upload successful: {note_id}")
                    
                    # Wait for processing
                    await self.wait_for_processing_completion(note_id, headers)
                    
                    # Verify OCR results
                    final_note = await self.get_note_details(note_id, headers)
                    if final_note:
                        artifacts = final_note.get("artifacts", {})
                        extracted_text = artifacts.get("text", "")
                        
                        if extracted_text and len(extracted_text) > 10:
                            print(f"✅ Direct upload OCR processing successful")
                            print(f"   Extracted text length: {len(extracted_text)} characters")
                            print(f"   Sample text: {extracted_text[:100]}...")
                            
                            # Clean up
                            os.unlink(image_file)
                            return True, note_id, extracted_text
                        else:
                            print(f"❌ Direct upload OCR failed - no text extracted")
                            os.unlink(image_file)
                            return False, note_id, ""
                    else:
                        print(f"❌ Could not retrieve note details after direct upload processing")
                        os.unlink(image_file)
                        return False, note_id, ""
                else:
                    print(f"❌ Direct file upload failed: {response.status_code} - {response.text}")
                    os.unlink(image_file)
                    return False, None, ""
                    
        except Exception as e:
            print(f"❌ Direct upload OCR test error: {str(e)}")
            return False, None, ""
    
    async def test_multiple_image_formats(self):
        """Test 3: Test OCR with different image formats"""
        print("\n🧪 Test 3: Multiple Image Formats OCR Test")
        
        formats_tested = []
        successful_formats = []
        
        # Test PNG format
        try:
            png_file = self.create_test_image_with_text("PNG Format Test\ngpt-4o model verification")
            success = await self.test_single_format_ocr(png_file, "PNG", "image/png")
            formats_tested.append("PNG")
            if success:
                successful_formats.append("PNG")
            os.unlink(png_file)
        except Exception as e:
            print(f"❌ PNG format test error: {str(e)}")
        
        # Test JPG format
        try:
            # Create JPG version
            png_file = self.create_test_image_with_text("JPG Format Test\ngpt-4o model verification")
            img = Image.open(png_file)
            jpg_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            img.convert('RGB').save(jpg_file.name, 'JPEG')
            os.unlink(png_file)
            
            success = await self.test_single_format_ocr(jpg_file.name, "JPG", "image/jpeg")
            formats_tested.append("JPG")
            if success:
                successful_formats.append("JPG")
            os.unlink(jpg_file.name)
        except Exception as e:
            print(f"❌ JPG format test error: {str(e)}")
        
        print(f"✅ Format testing complete: {len(successful_formats)}/{len(formats_tested)} formats successful")
        print(f"   Tested: {', '.join(formats_tested)}")
        print(f"   Successful: {', '.join(successful_formats)}")
        
        return len(successful_formats) > 0, successful_formats
    
    async def test_single_format_ocr(self, image_file, format_name, mime_type):
        """Helper method to test OCR with a single image format"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            with open(image_file, 'rb') as f:
                files = {"file": (f"test_ocr.{format_name.lower()}", f, mime_type)}
                data = {"title": f"{format_name} OCR Test"}
                
                response = await self.client.post(
                    f"{API_BASE}/upload-file",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    upload_data = response.json()
                    note_id = upload_data.get("id")
                    
                    # Wait for processing
                    await self.wait_for_processing_completion(note_id, headers)
                    
                    # Check results
                    final_note = await self.get_note_details(note_id, headers)
                    if final_note:
                        artifacts = final_note.get("artifacts", {})
                        extracted_text = artifacts.get("text", "")
                        
                        if extracted_text and len(extracted_text) > 5:
                            print(f"✅ {format_name} format OCR successful")
                            return True
                        else:
                            print(f"❌ {format_name} format OCR failed - no text extracted")
                            return False
                    else:
                        print(f"❌ {format_name} format - could not retrieve note details")
                        return False
                else:
                    print(f"❌ {format_name} format upload failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ {format_name} format test error: {str(e)}")
            return False
    
    async def wait_for_processing_completion(self, note_id, headers, max_wait=60):
        """Wait for note processing to complete"""
        print(f"   Waiting for OCR processing to complete...")
        
        for attempt in range(max_wait):
            try:
                response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                if response.status_code == 200:
                    note_data = response.json()
                    status = note_data.get("status", "")
                    
                    if status == "ready":
                        print(f"   ✅ Processing completed in {attempt + 1} seconds")
                        return True
                    elif status == "failed":
                        print(f"   ❌ Processing failed after {attempt + 1} seconds")
                        return False
                    elif status in ["processing", "uploading"]:
                        await asyncio.sleep(1)
                        continue
                    else:
                        print(f"   ⚠️  Unknown status: {status}")
                        await asyncio.sleep(1)
                        continue
                else:
                    print(f"   ❌ Error checking status: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error waiting for processing: {str(e)}")
                return False
        
        print(f"   ⏰ Processing timeout after {max_wait} seconds")
        return False
    
    async def get_note_details(self, note_id, headers):
        """Get detailed note information"""
        try:
            response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error getting note details: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error retrieving note details: {str(e)}")
            return None
    
    async def test_error_handling(self):
        """Test 4: Error handling for invalid files"""
        print("\n🧪 Test 4: OCR Error Handling Test")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Test with invalid file type (text file)
            invalid_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
            invalid_file.write(b"This is not an image file")
            invalid_file.close()
            
            with open(invalid_file.name, 'rb') as f:
                files = {"file": ("invalid.txt", f, "text/plain")}
                data = {"title": "Invalid File Test"}
                
                response = await self.client.post(
                    f"{API_BASE}/upload-file",
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 400:
                    print(f"✅ Invalid file type properly rejected with 400 status")
                    os.unlink(invalid_file.name)
                    return True
                else:
                    print(f"❌ Invalid file type not properly handled: {response.status_code}")
                    os.unlink(invalid_file.name)
                    return False
                    
        except Exception as e:
            print(f"❌ Error handling test error: {str(e)}")
            return False

async def main():
    """Main test execution"""
    print("🚀 Starting OCR Fix Verification Tests")
    print("=" * 60)
    print("Testing the critical fix: gpt-4o-mini → gpt-4o model change")
    print("=" * 60)
    
    tester = OCRFixTester()
    
    try:
        # Register test user
        if not await tester.register_test_user():
            print("❌ Failed to register test user. Exiting.")
            return
        
        # Test results tracking
        test_results = []
        
        # Test 1: Photo note creation with OCR
        success1, note_id1, text1 = await tester.test_photo_note_creation_with_ocr()
        test_results.append(("Photo Note OCR", success1))
        
        # Test 2: Direct file upload OCR
        success2, note_id2, text2 = await tester.test_direct_file_upload_ocr()
        test_results.append(("Direct Upload OCR", success2))
        
        # Test 3: Multiple image formats
        success3, formats = await tester.test_multiple_image_formats()
        test_results.append(("Multiple Formats OCR", success3))
        
        # Test 4: Error handling
        success4 = await tester.test_error_handling()
        test_results.append(("Error Handling", success4))
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 OCR FIX VERIFICATION RESULTS")
        print("=" * 60)
        
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - OCR fix with gpt-4o model is working correctly!")
            print("✅ No more 400 Bad Request errors from OpenAI API")
            print("✅ OCR processing completes successfully")
            print("✅ Complete workflow: upload → processing → ready → extracted text")
        else:
            print("⚠️  Some tests failed - OCR fix may need additional attention")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test execution error: {str(e)}")
    
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())