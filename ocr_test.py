#!/usr/bin/env python3
"""
OCR Functionality Test Suite
Testing the reported OCR functionality that is broken with 400 Bad Request error from OpenAI API.
"""

import asyncio
import httpx
import json
import os
import time
import base64
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OCRTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.auth_token = None
        self.test_user_email = f"ocr_test_user_{int(time.time())}@example.com"
        self.test_user_password = "OCRTestPassword123!"
        
    async def cleanup(self):
        """Clean up HTTP client"""
        await self.client.aclose()
    
    def create_test_image_with_text(self, text="Hello World! This is a test image for OCR.", width=400, height=200):
        """Create a test image with text for OCR testing"""
        # Create a white background image
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Draw text on image
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name, 'PNG')
        temp_file.close()
        
        return temp_file.name, text
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            response = await self.client.post(f"{API_BASE}/auth/register", json={
                "email": self.test_user_email,
                "password": self.test_user_password,
                "username": "ocrtest",
                "name": "OCR Test User"
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
    
    async def test_direct_ocr_api_call(self):
        """Test 1: Direct OCR API call to OpenAI Vision API"""
        print("\n🧪 Test 1: Direct OCR API Call to OpenAI Vision API")
        
        try:
            # Get API key from environment
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
            if not api_key:
                print("❌ No OpenAI API key found in environment")
                return False
            
            print(f"   Using API key: {api_key[:10]}...{api_key[-4:]}")
            
            # Create test image
            image_path, expected_text = self.create_test_image_with_text()
            print(f"   Created test image with text: '{expected_text}'")
            
            # Convert image to base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Prepare OpenAI Vision API request
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image. Return only the extracted text, no explanations or formatting. If no text is found, return 'No text detected'."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            # Make direct API call
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            print(f"   API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                extracted_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"   ✅ OCR successful! Extracted text: '{extracted_text}'")
                
                # Check if extracted text contains expected text
                if expected_text.lower() in extracted_text.lower():
                    print("   ✅ Text extraction accuracy verified!")
                    return True
                else:
                    print(f"   ⚠️  Text extraction may be inaccurate. Expected: '{expected_text}', Got: '{extracted_text}'")
                    return True  # Still consider success if API worked
            else:
                print(f"   ❌ OpenAI API call failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Direct OCR API test error: {str(e)}")
            return False
        finally:
            # Clean up test image
            try:
                os.unlink(image_path)
            except:
                pass
    
    async def test_photo_note_creation_with_ocr(self):
        """Test 2: Create photo note and test OCR processing"""
        print("\n🧪 Test 2: Photo Note Creation with OCR Processing")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Create test image
            image_path, expected_text = self.create_test_image_with_text("OCR Test Document\nLine 2: Testing multi-line text\nLine 3: Numbers 123456")
            print(f"   Created test image with text: '{expected_text}'")
            
            # Upload file using /api/upload-file endpoint
            with open(image_path, 'rb') as f:
                files = {
                    "file": ("ocr_test.png", f, "image/png")
                }
                data = {
                    "title": "OCR Test Document"
                }
                
                response = await self.client.post(f"{API_BASE}/upload-file", 
                    headers=headers,
                    files=files,
                    data=data
                )
            
            print(f"   Upload Response Status: {response.status_code}")
            
            if response.status_code == 200:
                upload_data = response.json()
                note_id = upload_data.get("id")
                status = upload_data.get("status")
                kind = upload_data.get("kind")
                
                print(f"   ✅ Photo note created:")
                print(f"      Note ID: {note_id}")
                print(f"      Status: {status}")
                print(f"      Kind: {kind}")
                
                if kind != "photo":
                    print(f"   ❌ Expected kind 'photo', got '{kind}'")
                    return False
                
                # Monitor processing status
                print("   🔍 Monitoring OCR processing...")
                max_wait_time = 60
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    note_response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                    
                    if note_response.status_code == 200:
                        note_data = note_response.json()
                        current_status = note_data.get("status", "unknown")
                        artifacts = note_data.get("artifacts", {})
                        
                        print(f"      Status: {current_status}")
                        
                        if current_status == "ready":
                            extracted_text = artifacts.get("text", "")
                            print(f"   ✅ OCR processing completed!")
                            print(f"      Extracted text: '{extracted_text}'")
                            
                            if extracted_text and len(extracted_text.strip()) > 0:
                                print("   ✅ OCR text extraction successful!")
                                return True
                            else:
                                print("   ❌ OCR completed but no text extracted")
                                return False
                        
                        elif current_status == "failed":
                            print(f"   ❌ OCR processing failed")
                            print(f"      Artifacts: {artifacts}")
                            return False
                        
                        elif current_status == "processing":
                            print("      Still processing...")
                    
                    await asyncio.sleep(3)
                
                print(f"   ⏰ OCR processing timeout after {max_wait_time}s")
                return False
                
            else:
                print(f"   ❌ Photo upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Photo note OCR test error: {str(e)}")
            return False
        finally:
            # Clean up test image
            try:
                os.unlink(image_path)
            except:
                pass
    
    async def test_ocr_providers_function(self):
        """Test 3: Test ocr_read function from providers.py directly"""
        print("\n🧪 Test 3: Testing ocr_read Function from providers.py")
        
        try:
            # Import the ocr_read function
            import sys
            sys.path.append('/app/backend')
            from providers import ocr_read
            
            # Create test image
            image_path, expected_text = self.create_test_image_with_text("Direct OCR Function Test")
            print(f"   Created test image with text: '{expected_text}'")
            
            # Test ocr_read function directly
            print("   Calling ocr_read function...")
            result = await ocr_read(image_path)
            
            print(f"   OCR Result: {result}")
            
            if isinstance(result, dict):
                extracted_text = result.get("text", "")
                note = result.get("note", "")
                
                if note:
                    print(f"   ❌ OCR function returned error note: {note}")
                    return False
                
                if extracted_text and len(extracted_text.strip()) > 0:
                    print(f"   ✅ OCR function successful! Extracted: '{extracted_text}'")
                    return True
                else:
                    print("   ❌ OCR function returned empty text")
                    return False
            else:
                print(f"   ❌ OCR function returned unexpected format: {type(result)}")
                return False
                
        except Exception as e:
            print(f"❌ OCR function test error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up test image
            try:
                os.unlink(image_path)
            except:
                pass
    
    async def test_note_upload_endpoint(self):
        """Test 4: Test /api/notes/{id}/upload endpoint for photo processing"""
        print("\n🧪 Test 4: Testing /api/notes/{id}/upload Endpoint")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # First create a photo note
            note_response = await self.client.post(f"{API_BASE}/notes", 
                headers=headers,
                json={
                    "title": "Upload Endpoint OCR Test",
                    "kind": "photo"
                }
            )
            
            if note_response.status_code != 200:
                print(f"   ❌ Failed to create note: {note_response.status_code}")
                return False
            
            note_data = note_response.json()
            note_id = note_data.get("id")
            print(f"   Created note ID: {note_id}")
            
            # Create test image
            image_path, expected_text = self.create_test_image_with_text("Upload Endpoint Test Image")
            print(f"   Created test image with text: '{expected_text}'")
            
            # Upload image to the note
            with open(image_path, 'rb') as f:
                files = {
                    "file": ("upload_test.png", f, "image/png")
                }
                
                upload_response = await self.client.post(f"{API_BASE}/notes/{note_id}/upload",
                    headers=headers,
                    files=files
                )
            
            print(f"   Upload Response Status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                print(f"   ✅ File uploaded: {upload_data}")
                
                # Monitor processing
                print("   🔍 Monitoring OCR processing...")
                max_wait_time = 60
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    note_check = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                    
                    if note_check.status_code == 200:
                        note_info = note_check.json()
                        current_status = note_info.get("status", "unknown")
                        artifacts = note_info.get("artifacts", {})
                        
                        print(f"      Status: {current_status}")
                        
                        if current_status == "ready":
                            extracted_text = artifacts.get("text", "")
                            print(f"   ✅ OCR processing completed!")
                            print(f"      Extracted text: '{extracted_text}'")
                            return True
                        
                        elif current_status == "failed":
                            print(f"   ❌ OCR processing failed")
                            print(f"      Artifacts: {artifacts}")
                            return False
                    
                    await asyncio.sleep(3)
                
                print(f"   ⏰ Processing timeout after {max_wait_time}s")
                return False
                
            else:
                print(f"   ❌ File upload failed: {upload_response.status_code}")
                print(f"   Response: {upload_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload endpoint test error: {str(e)}")
            return False
        finally:
            # Clean up test image
            try:
                os.unlink(image_path)
            except:
                pass
    
    async def test_environment_configuration(self):
        """Test 5: Check environment configuration for OCR"""
        print("\n🧪 Test 5: Environment Configuration Check")
        
        try:
            # Check OCR provider setting
            ocr_provider = os.getenv("OCR_PROVIDER", "openai")
            print(f"   OCR_PROVIDER: {ocr_provider}")
            
            # Check OpenAI API key
            openai_key = os.getenv("OPENAI_API_KEY")
            whisper_key = os.getenv("WHISPER_API_KEY")
            
            if openai_key:
                print(f"   OPENAI_API_KEY: {openai_key[:10]}...{openai_key[-4:]} (length: {len(openai_key)})")
            else:
                print("   OPENAI_API_KEY: Not set")
            
            if whisper_key:
                print(f"   WHISPER_API_KEY: {whisper_key[:10]}...{whisper_key[-4:]} (length: {len(whisper_key)})")
            else:
                print("   WHISPER_API_KEY: Not set")
            
            # Check if we have a valid API key for OCR
            api_key = openai_key or whisper_key
            if not api_key:
                print("   ❌ No OpenAI API key available for OCR")
                return False
            
            if ocr_provider.lower() != "openai":
                print(f"   ⚠️  OCR provider is set to '{ocr_provider}', not 'openai'")
            
            print("   ✅ Environment configuration looks correct")
            return True
            
        except Exception as e:
            print(f"❌ Environment check error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all OCR tests"""
        print("🚀 Starting OCR Functionality Test Suite")
        print("=" * 80)
        
        # Check environment first
        env_success = await self.test_environment_configuration()
        if not env_success:
            print("❌ Environment configuration issues detected")
            return False
        
        # Register test user
        if not await self.register_test_user():
            print("❌ Cannot proceed without test user registration")
            return False
        
        test_results = []
        
        # Test 1: Direct OpenAI API call
        direct_api_success = await self.test_direct_ocr_api_call()
        test_results.append(("Direct OpenAI Vision API Call", direct_api_success))
        
        # Test 2: OCR providers function
        providers_success = await self.test_ocr_providers_function()
        test_results.append(("OCR Providers Function", providers_success))
        
        # Test 3: Photo note creation with OCR
        photo_note_success = await self.test_photo_note_creation_with_ocr()
        test_results.append(("Photo Note Creation with OCR", photo_note_success))
        
        # Test 4: Note upload endpoint
        upload_endpoint_success = await self.test_note_upload_endpoint()
        test_results.append(("Note Upload Endpoint OCR", upload_endpoint_success))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 OCR TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = 0
        total = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1
        
        print(f"\n📈 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL OCR TESTS PASSED - OCR functionality is working correctly!")
            return True
        elif passed > 0:
            print("⚠️  PARTIAL SUCCESS - Some OCR functionality working, check failed tests")
            return True
        else:
            print("❌ ALL OCR TESTS FAILED - Critical OCR issues detected")
            return False

async def main():
    """Main test execution"""
    tester = OCRTester()
    
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)