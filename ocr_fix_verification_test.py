#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import sys
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import base64

class OCRFixVerificationTest:
    def __init__(self):
        # Get backend URL from environment
        self.backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://auto-me-debugger.preview.emergentagent.com')
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
        
        self.test_results = []
        self.auth_token = None
        
        print(f"🔍 OCR FIX VERIFICATION TEST")
        print(f"Backend URL: {self.backend_url}")
        print("="*80)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    async def authenticate_user(self):
        """Create test user and authenticate"""
        try:
            # Create test user
            user_data = {
                "email": "ocr.tester@expeditors.com",
                "password": "SecureTest123!",
                "full_name": "OCR Test User"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                # Try to register (might fail if user exists)
                try:
                    response = await client.post(f"{self.backend_url}/auth/register", json=user_data)
                    if response.status_code == 200:
                        self.log("✅ Test user registered successfully")
                        data = response.json()
                        self.auth_token = data.get("access_token")
                        return True
                except:
                    pass
                
                # Try to login
                login_data = {"email": user_data["email"], "password": user_data["password"]}
                response = await client.post(f"{self.backend_url}/auth/login", json=login_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.log("✅ Authentication successful")
                    return True
                else:
                    self.log(f"❌ Authentication failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}")
            return False

    def create_test_image(self, text="OCR Test 2025", format="PNG", size=(400, 200)):
        """Create a test image with text"""
        try:
            # Create image
            img = Image.new('RGB', size, color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a font, fall back to default if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Add text to image
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            
            draw.text((x, y), text, fill='black', font=font)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format=format)
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            self.log(f"❌ Error creating test image: {str(e)}")
            return None

    def create_corrupted_file(self, size_bytes=9):
        """Create a corrupted/invalid file"""
        return b'x' * size_bytes

    async def test_valid_image_formats(self):
        """Test OCR with various valid image formats"""
        self.log("\n📋 Testing Valid Image Formats...")
        
        test_cases = [
            {"format": "PNG", "text": "Hello World PNG Test", "expected_success": True},
            {"format": "JPEG", "text": "Hello World JPG Test", "expected_success": True},
        ]
        
        results = []
        
        for case in test_cases:
            try:
                self.log(f"   Testing {case['format']} format...")
                
                # Create test image
                image_data = self.create_test_image(case['text'], case['format'])
                if not image_data:
                    results.append({"case": case['format'], "success": False, "error": "Failed to create image"})
                    continue
                
                # Upload via /api/upload-file endpoint
                files = {"file": (f"test.{case['format'].lower()}", image_data, f"image/{case['format'].lower()}")}
                data = {"title": f"OCR Test {case['format']}"}
                
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        f"{self.backend_url}/upload-file",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        upload_result = response.json()
                        note_id = upload_result.get("id")
                        
                        self.log(f"   ✅ Upload successful: {note_id}")
                        
                        # Wait for processing and check result
                        await asyncio.sleep(8)  # Give time for OCR processing
                        
                        # Get note to check OCR result
                        note_response = await client.get(
                            f"{self.backend_url}/notes/{note_id}",
                            headers=headers
                        )
                        
                        if note_response.status_code == 200:
                            note_data = note_response.json()
                            status = note_data.get("status")
                            artifacts = note_data.get("artifacts", {})
                            extracted_text = artifacts.get("text", "")
                            
                            if status == "ready" and extracted_text:
                                self.log(f"   ✅ OCR Success: '{extracted_text[:50]}...'")
                                results.append({
                                    "case": case['format'], 
                                    "success": True, 
                                    "extracted_text": extracted_text,
                                    "processing_time": "3-8 seconds"
                                })
                            else:
                                self.log(f"   ❌ OCR Failed: status={status}, text_length={len(extracted_text)}")
                                results.append({
                                    "case": case['format'], 
                                    "success": False, 
                                    "error": f"Processing failed: status={status}"
                                })
                        else:
                            self.log(f"   ❌ Failed to retrieve note: {note_response.status_code}")
                            results.append({
                                "case": case['format'], 
                                "success": False, 
                                "error": f"Note retrieval failed: {note_response.status_code}"
                            })
                    else:
                        self.log(f"   ❌ Upload failed: {response.status_code} - {response.text}")
                        results.append({
                            "case": case['format'], 
                            "success": False, 
                            "error": f"Upload failed: {response.status_code}"
                        })
                        
            except Exception as e:
                self.log(f"   ❌ Error testing {case['format']}: {str(e)}")
                results.append({
                    "case": case['format'], 
                    "success": False, 
                    "error": str(e)
                })
        
        return results

    async def test_corrupted_image_rejection(self):
        """Test that corrupted/invalid images are properly rejected"""
        self.log("\n🚫 Testing Corrupted Image Rejection...")
        
        test_cases = [
            {"name": "9-byte corrupted file", "data": self.create_corrupted_file(9), "filename": "corrupted.jpg"},
            {"name": "50-byte corrupted file", "data": self.create_corrupted_file(50), "filename": "corrupted.png"},
            {"name": "Text file as image", "data": b"This is not an image file", "filename": "fake.jpg"},
            {"name": "Empty file", "data": b"", "filename": "empty.png"},
        ]
        
        results = []
        
        for case in test_cases:
            try:
                self.log(f"   Testing {case['name']}...")
                
                files = {"file": (case['filename'], case['data'], "image/jpeg")}
                data = {"title": f"Corrupted Test: {case['name']}"}
                
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{self.backend_url}/upload-file",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        # Upload succeeded, check if processing properly rejects it
                        upload_result = response.json()
                        note_id = upload_result.get("id")
                        
                        # Wait for processing
                        await asyncio.sleep(5)
                        
                        # Check note status
                        note_response = await client.get(
                            f"{self.backend_url}/notes/{note_id}",
                            headers=headers
                        )
                        
                        if note_response.status_code == 200:
                            note_data = note_response.json()
                            status = note_data.get("status")
                            artifacts = note_data.get("artifacts", {})
                            error_text = artifacts.get("text", "")
                            
                            # Check if it was properly rejected with helpful message
                            if "Invalid" in error_text or "corrupted" in error_text or "valid PNG or JPG" in error_text:
                                self.log(f"   ✅ Properly rejected: '{error_text}'")
                                results.append({
                                    "case": case['name'], 
                                    "success": True, 
                                    "rejection_message": error_text
                                })
                            else:
                                self.log(f"   ❌ Not properly rejected: status={status}, text='{error_text}'")
                                results.append({
                                    "case": case['name'], 
                                    "success": False, 
                                    "error": "Should have been rejected but wasn't"
                                })
                        else:
                            self.log(f"   ❌ Failed to check note: {note_response.status_code}")
                            results.append({
                                "case": case['name'], 
                                "success": False, 
                                "error": "Failed to check processing result"
                            })
                    else:
                        # Upload failed - this might be expected for some cases
                        error_detail = response.text
                        if "Unsupported file type" in error_detail or "Invalid" in error_detail:
                            self.log(f"   ✅ Properly rejected at upload: {error_detail}")
                            results.append({
                                "case": case['name'], 
                                "success": True, 
                                "rejection_message": error_detail
                            })
                        else:
                            self.log(f"   ❌ Unexpected upload failure: {response.status_code} - {error_detail}")
                            results.append({
                                "case": case['name'], 
                                "success": False, 
                                "error": f"Unexpected failure: {response.status_code}"
                            })
                        
            except Exception as e:
                self.log(f"   ❌ Error testing {case['name']}: {str(e)}")
                results.append({
                    "case": case['name'], 
                    "success": False, 
                    "error": str(e)
                })
        
        return results

    async def test_complete_workflow(self):
        """Test the complete OCR workflow end-to-end"""
        self.log("\n🔄 Testing Complete OCR Workflow...")
        
        try:
            # Create a comprehensive test image
            test_text = "OCR Workflow Test 2025\nMultiple Lines\nNumbers: 12345"
            image_data = self.create_test_image(test_text, "PNG", (600, 300))
            
            if not image_data:
                return {"success": False, "error": "Failed to create test image"}
            
            self.log("   Step 1: Upload image...")
            
            # Upload image
            files = {"file": ("workflow_test.png", image_data, "image/png")}
            data = {"title": "Complete Workflow Test"}
            
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            async with httpx.AsyncClient(timeout=60) as client:
                start_time = time.time()
                
                # Upload
                response = await client.post(
                    f"{self.backend_url}/upload-file",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    return {"success": False, "error": f"Upload failed: {response.status_code}"}
                
                upload_result = response.json()
                note_id = upload_result.get("id")
                
                self.log(f"   ✅ Upload successful: {note_id}")
                self.log("   Step 2: Validation...")
                
                # Check initial status
                note_response = await client.get(f"{self.backend_url}/notes/{note_id}", headers=headers)
                if note_response.status_code == 200:
                    note_data = note_response.json()
                    initial_status = note_data.get("status")
                    self.log(f"   ✅ Initial status: {initial_status}")
                
                self.log("   Step 3: OCR Processing...")
                
                # Wait for processing with periodic checks
                max_wait = 30
                check_interval = 3
                
                for i in range(0, max_wait, check_interval):
                    await asyncio.sleep(check_interval)
                    
                    note_response = await client.get(f"{self.backend_url}/notes/{note_id}", headers=headers)
                    if note_response.status_code == 200:
                        note_data = note_response.json()
                        status = note_data.get("status")
                        artifacts = note_data.get("artifacts", {})
                        
                        if status == "ready":
                            processing_time = time.time() - start_time
                            extracted_text = artifacts.get("text", "")
                            
                            self.log(f"   ✅ OCR completed in {processing_time:.1f}s")
                            self.log(f"   ✅ Extracted text ({len(extracted_text)} chars): '{extracted_text[:100]}...'")
                            
                            return {
                                "success": True,
                                "processing_time": f"{processing_time:.1f}s",
                                "extracted_text": extracted_text,
                                "text_length": len(extracted_text),
                                "workflow_steps": ["upload", "validation", "processing", "success"]
                            }
                        elif status == "failed":
                            error_text = artifacts.get("text", "Unknown error")
                            return {"success": False, "error": f"Processing failed: {error_text}"}
                        else:
                            self.log(f"   ⏳ Status: {status} (waiting...)")
                
                return {"success": False, "error": "Processing timeout after 30 seconds"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_no_400_errors(self):
        """Verify no 400 Bad Request errors from OpenAI API"""
        self.log("\n🔍 Testing for 400 Bad Request Errors...")
        
        try:
            # Create multiple test images to stress test
            test_cases = [
                {"text": "Simple Test", "format": "PNG"},
                {"text": "Complex Text\nWith Multiple Lines\nAnd Numbers: 123", "format": "JPEG"},
                {"text": "Special Characters: @#$%^&*()", "format": "PNG"},
            ]
            
            results = []
            
            for i, case in enumerate(test_cases):
                self.log(f"   Test {i+1}: {case['format']} with '{case['text'][:20]}...'")
                
                image_data = self.create_test_image(case['text'], case['format'])
                if not image_data:
                    continue
                
                files = {"file": (f"test_{i}.{case['format'].lower()}", image_data, f"image/{case['format'].lower()}")}
                data = {"title": f"400 Error Test {i+1}"}
                
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        f"{self.backend_url}/upload-file",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        upload_result = response.json()
                        note_id = upload_result.get("id")
                        
                        # Wait for processing
                        await asyncio.sleep(8)
                        
                        # Check result
                        note_response = await client.get(f"{self.backend_url}/notes/{note_id}", headers=headers)
                        if note_response.status_code == 200:
                            note_data = note_response.json()
                            status = note_data.get("status")
                            artifacts = note_data.get("artifacts", {})
                            
                            if status == "ready":
                                extracted_text = artifacts.get("text", "")
                                self.log(f"   ✅ Success: {len(extracted_text)} chars extracted")
                                results.append({"test": i+1, "success": True, "text_length": len(extracted_text)})
                            elif status == "failed":
                                error_text = artifacts.get("text", "")
                                if "400" in error_text or "Bad Request" in error_text:
                                    self.log(f"   ❌ 400 Error detected: {error_text}")
                                    results.append({"test": i+1, "success": False, "error": "400 Bad Request detected"})
                                else:
                                    self.log(f"   ⚠️  Processing failed (not 400): {error_text}")
                                    results.append({"test": i+1, "success": False, "error": "Processing failed (not 400)"})
                            else:
                                self.log(f"   ⏳ Still processing: {status}")
                                results.append({"test": i+1, "success": False, "error": "Processing timeout"})
                    else:
                        self.log(f"   ❌ Upload failed: {response.status_code}")
                        results.append({"test": i+1, "success": False, "error": f"Upload failed: {response.status_code}"})
            
            # Check if any 400 errors were detected
            error_count = sum(1 for r in results if not r["success"] and "400" in r.get("error", ""))
            success_count = sum(1 for r in results if r["success"])
            
            return {
                "total_tests": len(results),
                "successful": success_count,
                "bad_request_errors": error_count,
                "no_400_errors": error_count == 0,
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_all_tests(self):
        """Run all OCR fix verification tests"""
        self.log("🚀 Starting OCR Fix Verification Tests...")
        
        # Try to authenticate (optional for OCR testing)
        auth_success = await self.authenticate_user()
        if not auth_success:
            self.log("⚠️  Authentication failed - proceeding with anonymous testing")
            self.auth_token = None
        
        # Run all test categories
        test_results = {}
        
        # Test 1: Valid image formats
        test_results["valid_formats"] = await self.test_valid_image_formats()
        
        # Test 2: Corrupted image rejection
        test_results["corrupted_rejection"] = await self.test_corrupted_image_rejection()
        
        # Test 3: Complete workflow
        test_results["complete_workflow"] = await self.test_complete_workflow()
        
        # Test 4: No 400 errors
        test_results["no_400_errors"] = await self.test_no_400_errors()
        
        # Generate summary
        self.generate_summary(test_results)
        
        return test_results

    def generate_summary(self, test_results):
        """Generate comprehensive test summary"""
        self.log("\n" + "="*80)
        self.log("📊 OCR FIX VERIFICATION SUMMARY")
        self.log("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        # Valid formats summary
        valid_formats = test_results.get("valid_formats", [])
        format_passed = sum(1 for r in valid_formats if r["success"])
        format_total = len(valid_formats)
        total_tests += format_total
        passed_tests += format_passed
        
        self.log(f"✅ Valid Image Formats: {format_passed}/{format_total} passed")
        for result in valid_formats:
            status = "✅" if result["success"] else "❌"
            self.log(f"   {status} {result['case']}: {result.get('extracted_text', result.get('error', 'Unknown'))[:50]}...")
        
        # Corrupted rejection summary
        corrupted_rejection = test_results.get("corrupted_rejection", [])
        rejection_passed = sum(1 for r in corrupted_rejection if r["success"])
        rejection_total = len(corrupted_rejection)
        total_tests += rejection_total
        passed_tests += rejection_passed
        
        self.log(f"\n🚫 Corrupted Image Rejection: {rejection_passed}/{rejection_total} passed")
        for result in corrupted_rejection:
            status = "✅" if result["success"] else "❌"
            message = result.get("rejection_message", result.get("error", "Unknown"))[:60]
            self.log(f"   {status} {result['case']}: {message}...")
        
        # Complete workflow summary
        workflow = test_results.get("complete_workflow", {})
        workflow_success = workflow.get("success", False)
        total_tests += 1
        if workflow_success:
            passed_tests += 1
        
        self.log(f"\n🔄 Complete Workflow: {'✅ PASSED' if workflow_success else '❌ FAILED'}")
        if workflow_success:
            self.log(f"   Processing time: {workflow.get('processing_time', 'Unknown')}")
            self.log(f"   Text extracted: {workflow.get('text_length', 0)} characters")
        else:
            self.log(f"   Error: {workflow.get('error', 'Unknown')}")
        
        # 400 errors summary
        no_400_errors = test_results.get("no_400_errors", {})
        no_400_success = no_400_errors.get("no_400_errors", False)
        total_tests += no_400_errors.get("total_tests", 0)
        passed_tests += no_400_errors.get("successful", 0)
        
        self.log(f"\n🔍 No 400 Bad Request Errors: {'✅ CONFIRMED' if no_400_success else '❌ DETECTED'}")
        if no_400_success:
            self.log(f"   All {no_400_errors.get('successful', 0)} tests passed without 400 errors")
        else:
            self.log(f"   {no_400_errors.get('bad_request_errors', 0)} 400 errors detected")
        
        # Overall summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n🎯 OVERALL RESULTS:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests}")
        self.log(f"   Failed: {total_tests - passed_tests}")
        self.log(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            self.log("🎉 OCR FIX VERIFICATION: EXCELLENT - All critical fixes working!")
        elif success_rate >= 75:
            self.log("✅ OCR FIX VERIFICATION: GOOD - Most fixes working correctly")
        else:
            self.log("⚠️  OCR FIX VERIFICATION: NEEDS ATTENTION - Some fixes not working")
        
        self.log("="*80)

async def main():
    """Main test execution"""
    tester = OCRFixVerificationTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())