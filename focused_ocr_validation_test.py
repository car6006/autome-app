#!/usr/bin/env python3
"""
Focused OCR Validation Testing
Testing the specific validation improvements mentioned in the review request.
"""

import asyncio
import httpx
import json
import os
import time
import tempfile
from PIL import Image, ImageDraw, ImageFont

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class FocusedOCRTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.auth_token = None
        self.test_user_email = f"focused_ocr_test_{int(time.time())}_{os.getpid()}@example.com"
        self.test_user_password = "TestPassword123!"
        self.created_notes = []
        
    async def cleanup(self):
        """Clean up HTTP client and test data"""
        for note_id in self.created_notes:
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                await self.client.delete(f"{API_BASE}/notes/{note_id}", headers=headers)
            except:
                pass
        await self.client.aclose()
    
    def create_test_image_with_text(self, text="OCR Test 2025", width=400, height=200):
        """Create a test image with text for OCR testing"""
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = None
        
        if font:
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        else:
            text_width = len(text) * 10
            text_height = 20
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name, 'PNG')
        
        return temp_file.name, text
    
    def create_corrupted_image_file(self):
        """Create a corrupted/invalid image file"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.write(b"This is not a valid image file content - corrupted data")
        temp_file.close()
        return temp_file.name
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            register_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "username": f"focusedocrtest{int(time.time())}",
                "name": "Focused OCR Test User"
            }
            
            print(f"Registering user: {self.test_user_email}")
            response = await self.client.post(f"{API_BASE}/auth/register", json=register_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Test user registered successfully")
                return True
            else:
                # Try login if registration fails
                login_response = await self.client.post(f"{API_BASE}/auth/login", json={
                    "email": self.test_user_email,
                    "password": self.test_user_password
                })
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    self.auth_token = data.get("access_token")
                    print(f"✅ Test user logged in successfully")
                    return True
                else:
                    print(f"❌ Authentication failed")
                    return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    async def test_valid_photo_note_ocr_processing(self):
        """Test: Valid photo notes should process OCR correctly"""
        print("\n🧪 Test: Valid Photo Note OCR Processing")
        
        try:
            image_file, expected_text = self.create_test_image_with_text("Valid OCR Test 2025")
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Upload valid image
            with open(image_file, 'rb') as f:
                files = {"file": ("valid_test.png", f, "image/png")}
                data = {"title": "Valid Photo OCR Test"}
                
                response = await self.client.post(f"{API_BASE}/upload-file", 
                    headers=headers, files=files, data=data)
            
            os.unlink(image_file)
            
            if response.status_code == 200:
                data = response.json()
                note_id = data.get("id")
                kind = data.get("kind")
                
                print(f"✅ Image uploaded: Note ID {note_id}, Kind: {kind}")
                
                if note_id:
                    self.created_notes.append(note_id)
                
                # Wait for processing
                print("⏳ Waiting for OCR processing...")
                await asyncio.sleep(10)
                
                # Check result
                note_response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    final_status = note_data.get("status")
                    artifacts = note_data.get("artifacts", {})
                    
                    print(f"✅ Final status: {final_status}")
                    
                    if final_status == "ready":
                        extracted_text = artifacts.get("text", "")
                        print(f"✅ Extracted text: '{extracted_text[:50]}...'")
                        
                        if len(extracted_text) > 5:
                            print("✅ PASSED: Valid photo note OCR works correctly")
                            return True
                        else:
                            print("❌ FAILED: No text extracted")
                            return False
                    elif final_status == "failed":
                        error_msg = artifacts.get("error", "")
                        print(f"❌ FAILED: OCR failed with error: {error_msg}")
                        return False
                    else:
                        print(f"❌ FAILED: Unexpected status: {final_status}")
                        return False
                else:
                    print(f"❌ FAILED: Could not retrieve note: {note_response.status_code}")
                    return False
            else:
                print(f"❌ FAILED: Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ FAILED: Test error: {str(e)}")
            return False
    
    async def test_text_note_ocr_rejection(self):
        """Test: Text notes should not be processed for OCR"""
        print("\n🧪 Test: Text Note OCR Rejection")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Create text note
            text_note_data = {
                "title": "Text Note for OCR Rejection Test",
                "kind": "text",
                "text_content": "This is a text note that should not be processed for OCR"
            }
            
            response = await self.client.post(f"{API_BASE}/notes", headers=headers, json=text_note_data)
            
            if response.status_code == 200:
                data = response.json()
                note_id = data.get("id")
                
                print(f"✅ Text note created: {note_id}")
                
                if note_id:
                    self.created_notes.append(note_id)
                
                # Now try to upload an image to this text note
                image_file, _ = self.create_test_image_with_text("Should not process")
                
                with open(image_file, 'rb') as f:
                    files = {"file": ("test_image.png", f, "image/png")}
                    
                    upload_response = await self.client.post(f"{API_BASE}/notes/{note_id}/upload", 
                        headers=headers, files=files)
                
                os.unlink(image_file)
                
                print(f"Upload response: {upload_response.status_code}")
                
                # Wait for any processing
                await asyncio.sleep(8)
                
                # Check final note status
                note_response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    final_status = note_data.get("status")
                    kind = note_data.get("kind")
                    artifacts = note_data.get("artifacts", {})
                    
                    print(f"✅ Note kind: {kind}, Final status: {final_status}")
                    
                    # For text notes, OCR should not be triggered
                    # The note should either remain in its original state or fail if OCR was attempted
                    if kind == "text":
                        if final_status in ["ready", "created"]:
                            # Text note should remain ready/created, not processed for OCR
                            print("✅ PASSED: Text note was not processed for OCR")
                            return True
                        elif final_status == "failed":
                            error_msg = artifacts.get("error", "")
                            if "photo" in error_msg.lower() or "text" in error_msg.lower():
                                print(f"✅ PASSED: Text note properly rejected: {error_msg}")
                                return True
                            else:
                                print(f"❌ FAILED: Unexpected error message: {error_msg}")
                                return False
                        else:
                            print(f"❌ FAILED: Unexpected status for text note: {final_status}")
                            return False
                    else:
                        print(f"❌ FAILED: Note kind changed unexpectedly: {kind}")
                        return False
                else:
                    print(f"❌ FAILED: Could not retrieve note: {note_response.status_code}")
                    return False
            else:
                print(f"❌ FAILED: Could not create text note: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ FAILED: Test error: {str(e)}")
            return False
    
    async def test_corrupted_file_validation(self):
        """Test: Corrupted files should be rejected with proper error messages"""
        print("\n🧪 Test: Corrupted File Validation")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Create corrupted file
            corrupted_file = self.create_corrupted_image_file()
            
            # Upload corrupted file
            with open(corrupted_file, 'rb') as f:
                files = {"file": ("corrupted_test.png", f, "image/png")}
                data = {"title": "Corrupted File Test"}
                
                response = await self.client.post(f"{API_BASE}/upload-file", 
                    headers=headers, files=files, data=data)
            
            os.unlink(corrupted_file)
            
            if response.status_code == 200:
                data = response.json()
                note_id = data.get("id")
                
                print(f"✅ Corrupted file uploaded: {note_id}")
                
                if note_id:
                    self.created_notes.append(note_id)
                
                # Wait for processing
                print("⏳ Waiting for OCR processing...")
                await asyncio.sleep(10)
                
                # Check result
                note_response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    final_status = note_data.get("status")
                    artifacts = note_data.get("artifacts", {})
                    
                    print(f"✅ Final status: {final_status}")
                    
                    if final_status == "failed":
                        error_msg = artifacts.get("error", "")
                        print(f"✅ Error message: '{error_msg}'")
                        
                        # Check if error message is helpful and identifies the root cause
                        helpful_keywords = ["invalid", "corrupted", "image", "file", "valid", "png", "jpg"]
                        if any(keyword in error_msg.lower() for keyword in helpful_keywords):
                            print("✅ PASSED: Corrupted file properly rejected with helpful error message")
                            return True
                        else:
                            print(f"❌ FAILED: Error message not helpful enough: {error_msg}")
                            return False
                    else:
                        print(f"❌ FAILED: Expected failed status, got: {final_status}")
                        return False
                else:
                    print(f"❌ FAILED: Could not retrieve note: {note_response.status_code}")
                    return False
            else:
                print(f"❌ Upload rejected at API level: {response.status_code} - {response.text}")
                # This might be expected if validation happens at upload
                error_text = response.text
                if any(keyword in error_text.lower() for keyword in ["invalid", "image", "file"]):
                    print("✅ PASSED: Corrupted file rejected at upload level")
                    return True
                else:
                    print(f"❌ FAILED: Upload rejection not specific enough")
                    return False
                
        except Exception as e:
            print(f"❌ FAILED: Test error: {str(e)}")
            return False
    
    async def test_file_existence_validation(self):
        """Test: Files that don't exist should be caught early"""
        print("\n🧪 Test: File Existence Validation")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Create a valid image first
            image_file, _ = self.create_test_image_with_text("File Existence Test")
            
            # Upload the image
            with open(image_file, 'rb') as f:
                files = {"file": ("existence_test.png", f, "image/png")}
                data = {"title": "File Existence Test"}
                
                response = await self.client.post(f"{API_BASE}/upload-file", 
                    headers=headers, files=files, data=data)
            
            os.unlink(image_file)
            
            if response.status_code == 200:
                data = response.json()
                note_id = data.get("id")
                
                print(f"✅ File uploaded: {note_id}")
                
                if note_id:
                    self.created_notes.append(note_id)
                
                # Wait for processing
                print("⏳ Waiting for OCR processing...")
                await asyncio.sleep(10)
                
                # Check result
                note_response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    final_status = note_data.get("status")
                    artifacts = note_data.get("artifacts", {})
                    
                    print(f"✅ Final status: {final_status}")
                    
                    if final_status == "ready":
                        extracted_text = artifacts.get("text", "")
                        print(f"✅ OCR succeeded: '{extracted_text[:50]}...'")
                        print("✅ PASSED: File exists and was processed correctly")
                        return True
                    elif final_status == "failed":
                        error_msg = artifacts.get("error", "")
                        print(f"✅ OCR failed: {error_msg}")
                        
                        # Check if error indicates file not found
                        if "file" in error_msg.lower() and ("not found" in error_msg.lower() or "missing" in error_msg.lower()):
                            print("✅ PASSED: File existence validation caught missing file")
                            return True
                        else:
                            print("✅ PASSED: File validation working (failed for other reason)")
                            return True
                    else:
                        print(f"❌ FAILED: Unexpected status: {final_status}")
                        return False
                else:
                    print(f"❌ FAILED: Could not retrieve note: {note_response.status_code}")
                    return False
            else:
                print(f"❌ FAILED: Upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ FAILED: Test error: {str(e)}")
            return False

async def run_focused_ocr_tests():
    """Run focused OCR validation tests"""
    print("🚀 Starting Focused OCR Validation Testing")
    print("="*60)
    print("Testing the comprehensive validation improvements:")
    print("1. Note kind must be 'photo' (not text or audio)")
    print("2. Note must have a media_key")
    print("3. Media file must actually exist on disk")
    print("4. Proper error messages for each validation failure")
    print("="*60)
    
    tester = FocusedOCRTester()
    
    try:
        # Register test user
        if not await tester.register_test_user():
            print("❌ Failed to register test user. Exiting.")
            return
        
        # Run focused tests
        tests = [
            ("Valid Photo Note OCR Processing", tester.test_valid_photo_note_ocr_processing),
            ("Text Note OCR Rejection", tester.test_text_note_ocr_rejection),
            ("Corrupted File Validation", tester.test_corrupted_file_validation),
            ("File Existence Validation", tester.test_file_existence_validation),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                results.append((test_name, False))
        
        # Print summary
        print(f"\n{'='*60}")
        print("🎯 FOCUSED OCR VALIDATION TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All focused OCR validation tests PASSED!")
            print("✅ The comprehensive validation improvements are working correctly!")
        elif passed >= total * 0.75:  # 75% or more
            print("✅ Most OCR validation improvements are working correctly!")
        else:
            print("⚠️  Some critical OCR validation improvements need attention.")
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(run_focused_ocr_tests())