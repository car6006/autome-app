#!/usr/bin/env python3
"""
OCR Error Handling Fix Verification Test
Testing the specific fix where error messages are no longer stored as successful OCR results.
"""

import asyncio
import httpx
import json
import os
import time
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OCRErrorHandlingTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.auth_token = None
        self.test_user_email = f"ocr_error_test_{int(time.time())}@example.com"
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
    
    async def authenticate(self):
        """Authenticate test user"""
        try:
            register_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "username": f"ocrerrortest{int(time.time())}",
                "name": "OCR Error Test User"
            }
            
            response = await self.client.post(f"{API_BASE}/auth/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Test user authenticated: {self.test_user_email}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def create_valid_image(self, text="Valid OCR Test 2025"):
        """Create a valid test image with text"""
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Center the text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (400 - text_width) // 2
        y = (200 - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    def create_corrupted_image(self, size=50):
        """Create a corrupted image file"""
        return b"corrupted_image_data_not_valid" + b"\x00" * (size - 26)
    
    def create_empty_file(self):
        """Create an empty file"""
        return b""
    
    def create_tiny_file(self):
        """Create a very small file (likely corrupted)"""
        return b"tiny"
    
    async def test_valid_image_success(self):
        """Test 1: Valid images should extract text correctly (not error messages)"""
        print("\n🧪 Test 1: Valid Image OCR - Should Extract Text Successfully")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create valid image
            image_data = self.create_valid_image("Success Test Document 2025")
            
            # Create note
            note_data = {
                "title": "Valid Image OCR Test",
                "kind": "photo"
            }
            
            response = await self.client.post(f"{API_BASE}/notes", headers=headers, json=note_data)
            if response.status_code != 200:
                print(f"   ❌ Failed to create note: {response.status_code}")
                return False
                
            note_id = response.json()["id"]
            self.created_notes.append(note_id)
            
            # Upload image
            files = {"file": ("valid_test.png", image_data, "image/png")}
            response = await self.client.post(f"{API_BASE}/notes/{note_id}/upload", headers=headers, files=files)
            
            if response.status_code != 200:
                print(f"   ❌ Failed to upload image: {response.status_code}")
                return False
            
            # Wait for processing
            print("   ⏳ Waiting for OCR processing...")
            await asyncio.sleep(8)
            
            # Check result
            response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
            if response.status_code != 200:
                print(f"   ❌ Failed to get note: {response.status_code}")
                return False
                
            note = response.json()
            status = note.get("status")
            artifacts = note.get("artifacts", {})
            
            if status == "ready":
                extracted_text = artifacts.get("text", "")
                error_field = artifacts.get("error", "")
                
                # Verify text is extracted, not error message
                if extracted_text and "error" not in extracted_text.lower() and "failed" not in extracted_text.lower():
                    print(f"   ✅ Valid image processed successfully")
                    print(f"   📝 Extracted text: '{extracted_text}'")
                    print(f"   🔍 Status: {status}")
                    print(f"   🔍 Error field: {error_field or 'None'}")
                    return True
                else:
                    print(f"   ❌ Valid image extracted error-like text: '{extracted_text}'")
                    return False
            elif status == "failed":
                error_msg = artifacts.get("error", "")
                print(f"   ❌ Valid image failed unexpectedly: {error_msg}")
                return False
            else:
                print(f"   ⏳ OCR still processing: Status={status}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception in valid image test: {str(e)}")
            return False
    
    async def test_invalid_image_proper_failure(self):
        """Test 2: Invalid images should fail with proper error status (not ready with error text)"""
        print("\n🧪 Test 2: Invalid Image OCR - Should Fail with Proper Error Status")
        
        test_cases = [
            ("corrupted_50_bytes", self.create_corrupted_image(50)),
            ("empty_file", self.create_empty_file()),
            ("tiny_file", self.create_tiny_file()),
        ]
        
        results = []
        
        for test_name, file_data in test_cases:
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Create note
                note_data = {
                    "title": f"Invalid Image Test - {test_name}",
                    "kind": "photo"
                }
                
                response = await self.client.post(f"{API_BASE}/notes", headers=headers, json=note_data)
                if response.status_code != 200:
                    results.append(f"   ❌ Failed to create note for {test_name}")
                    continue
                    
                note_id = response.json()["id"]
                self.created_notes.append(note_id)
                
                # Upload invalid image
                files = {"file": (f"{test_name}.png", file_data, "image/png")}
                response = await self.client.post(f"{API_BASE}/notes/{note_id}/upload", headers=headers, files=files)
                
                if response.status_code != 200:
                    results.append(f"   ❌ Failed to upload {test_name}")
                    continue
                
                # Wait for processing
                await asyncio.sleep(5)
                
                # Check result
                response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                if response.status_code != 200:
                    results.append(f"   ❌ Failed to get note for {test_name}")
                    continue
                    
                note = response.json()
                status = note.get("status")
                artifacts = note.get("artifacts", {})
                
                if status == "failed":
                    error_msg = artifacts.get("error", "")
                    text_field = artifacts.get("text", "")
                    
                    # CRITICAL: Verify error is in error field, NOT in text field
                    if error_msg and not text_field:
                        results.append(f"   ✅ {test_name}: Properly failed with error in error field")
                        results.append(f"      Error: '{error_msg}'")
                        results.append(f"      Text field: Empty (correct)")
                    elif text_field and ("error" in text_field.lower() or "failed" in text_field.lower()):
                        results.append(f"   ❌ {test_name}: ERROR IN TEXT FIELD (should be in error field)")
                        results.append(f"      Text field: '{text_field}'")
                        results.append(f"      Error field: '{error_msg}'")
                    else:
                        results.append(f"   ⚠️ {test_name}: Failed but with unexpected structure")
                        results.append(f"      Error: '{error_msg}'")
                        results.append(f"      Text: '{text_field}'")
                        
                elif status == "ready":
                    extracted_text = artifacts.get("text", "")
                    # This is the OLD BUG - error messages stored as successful OCR results
                    if "error" in extracted_text.lower() or "failed" in extracted_text.lower():
                        results.append(f"   ❌ {test_name}: OLD BUG DETECTED - Error message stored as OCR text!")
                        results.append(f"      Status: ready (should be failed)")
                        results.append(f"      Text: '{extracted_text}'")
                    else:
                        results.append(f"   ❌ {test_name}: Invalid image processed as successful")
                        results.append(f"      Text: '{extracted_text}'")
                else:
                    results.append(f"   ⏳ {test_name}: Still processing")
                    
            except Exception as e:
                results.append(f"   ❌ Exception in {test_name}: {str(e)}")
        
        for result in results:
            print(result)
            
        # Check if all invalid images properly failed
        success_count = sum(1 for r in results if "✅" in r)
        total_tests = len(test_cases)
        
        return success_count >= total_tests  # All should succeed
    
    async def test_error_field_vs_text_field(self):
        """Test 3: Verify errors go to error field, successful text goes to text field"""
        print("\n🧪 Test 3: Error Field vs Text Field Separation")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with corrupted image that should fail
            corrupted_data = self.create_corrupted_image(30)
            
            note_data = {
                "title": "Error Field Test",
                "kind": "photo"
            }
            
            response = await self.client.post(f"{API_BASE}/notes", headers=headers, json=note_data)
            if response.status_code != 200:
                print(f"   ❌ Failed to create note: {response.status_code}")
                return False
                
            note_id = response.json()["id"]
            self.created_notes.append(note_id)
            
            # Upload corrupted image
            files = {"file": ("error_field_test.png", corrupted_data, "image/png")}
            response = await self.client.post(f"{API_BASE}/notes/{note_id}/upload", headers=headers, files=files)
            
            if response.status_code != 200:
                print(f"   ❌ Failed to upload image: {response.status_code}")
                return False
            
            # Wait for processing
            await asyncio.sleep(5)
            
            # Check result
            response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
            if response.status_code != 200:
                print(f"   ❌ Failed to get note: {response.status_code}")
                return False
                
            note = response.json()
            status = note.get("status")
            artifacts = note.get("artifacts", {})
            
            error_field = artifacts.get("error", "")
            text_field = artifacts.get("text", "")
            
            print(f"   📊 Results:")
            print(f"      Status: {status}")
            print(f"      Error field: '{error_field}'")
            print(f"      Text field: '{text_field}'")
            
            if status == "failed" and error_field and not text_field:
                print(f"   ✅ Perfect separation: Error in error field, text field empty")
                return True
            elif status == "ready" and text_field and ("error" in text_field.lower() or "failed" in text_field.lower()):
                print(f"   ❌ OLD BUG DETECTED: Error message in text field with ready status!")
                return False
            elif status == "failed" and text_field and ("error" in text_field.lower() or "failed" in text_field.lower()):
                print(f"   ❌ Error message in text field (should be in error field)")
                return False
            else:
                print(f"   ⚠️ Unexpected result structure")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception in error field test: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all OCR error handling tests"""
        print("🚀 OCR ERROR HANDLING FIX VERIFICATION")
        print("=" * 60)
        print("Testing the fix where error messages are no longer stored as successful OCR results")
        print("=" * 60)
        
        if not await self.authenticate():
            print("❌ Cannot proceed without authentication")
            return False
        
        test_results = []
        
        # Test 1: Valid images should work correctly
        valid_success = await self.test_valid_image_success()
        test_results.append(("Valid Image OCR Success", valid_success))
        
        # Test 2: Invalid images should fail properly
        invalid_success = await self.test_invalid_image_proper_failure()
        test_results.append(("Invalid Image Proper Failure", invalid_success))
        
        # Test 3: Error field vs text field separation
        separation_success = await self.test_error_field_vs_text_field()
        test_results.append(("Error Field vs Text Field Separation", separation_success))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 OCR ERROR HANDLING FIX VERIFICATION RESULTS")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1
        
        print(f"\n📈 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 OCR ERROR HANDLING FIX VERIFICATION: SUCCESS!")
            print("✅ Error messages are no longer stored as successful OCR results")
            print("✅ Failed notes show 'failed' status with errors in error field")
            print("✅ Successful OCR results contain actual extracted text")
            print("✅ Complete workflow: upload → validation → OCR → proper status works correctly")
            return True
        else:
            print("\n❌ OCR ERROR HANDLING FIX VERIFICATION: ISSUES DETECTED!")
            print("Some aspects of the error handling fix may not be working correctly")
            return False

async def main():
    """Main test execution"""
    tester = OCRErrorHandlingTester()
    
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)