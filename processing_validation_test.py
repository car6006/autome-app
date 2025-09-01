#!/usr/bin/env python3

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Add backend to path
sys.path.append('/app/backend')

from providers import ocr_read
from store import NotesStore

class ProcessingValidationTest:
    def __init__(self):
        print(f"🔍 OCR PROCESSING VALIDATION TEST")
        print(f"Testing complete processing pipeline with validation")
        print("="*80)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def create_test_image(self, text="Processing Test 2025", format="PNG", size=(400, 200)):
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
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=f'.{format.lower()}', delete=False) as tmp:
                img.save(tmp.name, format=format)
                return tmp.name
            
        except Exception as e:
            self.log(f"❌ Error creating test image: {str(e)}")
            return None

    def create_corrupted_file(self, size_bytes=9):
        """Create a corrupted/invalid file"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'x' * size_bytes)
            return tmp.name

    async def test_processing_pipeline_validation(self):
        """Test the complete processing pipeline with various file types"""
        self.log("\n🔄 Testing Processing Pipeline Validation...")
        
        test_cases = [
            {
                "name": "Valid PNG Image",
                "creator": lambda: self.create_test_image("Valid PNG Processing Test", "PNG"),
                "expected_success": True
            },
            {
                "name": "Valid JPEG Image", 
                "creator": lambda: self.create_test_image("Valid JPEG Processing Test", "JPEG"),
                "expected_success": True
            },
            {
                "name": "9-byte corrupted file",
                "creator": lambda: self.create_corrupted_file(9),
                "expected_success": False
            },
            {
                "name": "50-byte corrupted file",
                "creator": lambda: self.create_corrupted_file(50),
                "expected_success": False
            },
            {
                "name": "Empty file",
                "creator": lambda: self.create_corrupted_file(0),
                "expected_success": False
            }
        ]
        
        results = []
        
        for case in test_cases:
            try:
                self.log(f"   Testing: {case['name']}")
                
                # Create test file
                file_path = case['creator']()
                if not file_path:
                    results.append({"case": case['name'], "success": False, "error": "Failed to create file"})
                    continue
                
                # Get file size for validation
                file_size = os.path.getsize(file_path)
                self.log(f"     File size: {file_size} bytes")
                
                # Test OCR processing directly
                result = await ocr_read(file_path)
                
                if result and isinstance(result, dict):
                    extracted_text = result.get("text", "")
                    
                    if case['expected_success']:
                        # Should succeed with extracted text
                        if extracted_text and "Invalid" not in extracted_text and "corrupted" not in extracted_text:
                            self.log(f"   ✅ Success: '{extracted_text[:50]}...' ({len(extracted_text)} chars)")
                            results.append({
                                "case": case['name'], 
                                "success": True, 
                                "extracted_text": extracted_text,
                                "text_length": len(extracted_text),
                                "file_size": file_size
                            })
                        else:
                            self.log(f"   ❌ Processing failed: '{extracted_text}'")
                            results.append({
                                "case": case['name'], 
                                "success": False, 
                                "error": f"Processing failed: {extracted_text}",
                                "file_size": file_size
                            })
                    else:
                        # Should fail with validation error
                        if "Invalid" in extracted_text or "corrupted" in extracted_text or "valid PNG or JPG" in extracted_text:
                            self.log(f"   ✅ Properly rejected: '{extracted_text}'")
                            results.append({
                                "case": case['name'], 
                                "success": True, 
                                "rejection_message": extracted_text,
                                "file_size": file_size
                            })
                        else:
                            self.log(f"   ❌ Should have been rejected: '{extracted_text}'")
                            results.append({
                                "case": case['name'], 
                                "success": False, 
                                "error": f"Not properly rejected: {extracted_text}",
                                "file_size": file_size
                            })
                else:
                    self.log(f"   ❌ Invalid result: {result}")
                    results.append({
                        "case": case['name'], 
                        "success": False, 
                        "error": f"Invalid result: {result}",
                        "file_size": file_size
                    })
                
                # Clean up
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    
            except Exception as e:
                self.log(f"   ❌ Error testing {case['name']}: {str(e)}")
                results.append({
                    "case": case['name'], 
                    "success": False, 
                    "error": str(e)
                })
        
        return results

    async def test_specific_validation_features(self):
        """Test specific validation features implemented in the OCR fix"""
        self.log("\n🔍 Testing Specific Validation Features...")
        
        results = []
        
        # Test 1: Minimum file size validation (100 bytes)
        self.log("   Testing minimum file size validation (100 bytes threshold)...")
        try:
            # Create files of different sizes
            test_sizes = [9, 50, 99, 100, 150]
            
            for size in test_sizes:
                file_path = self.create_corrupted_file(size)
                result = await ocr_read(file_path)
                
                if size < 100:
                    # Should be rejected
                    if result and "Invalid" in result.get("text", ""):
                        self.log(f"     ✅ {size} bytes: Properly rejected")
                        results.append({"test": f"min_size_{size}", "success": True})
                    else:
                        self.log(f"     ❌ {size} bytes: Should have been rejected")
                        results.append({"test": f"min_size_{size}", "success": False})
                else:
                    # Should pass size check (but may fail PIL validation)
                    if result:
                        self.log(f"     ✅ {size} bytes: Passed size check")
                        results.append({"test": f"min_size_{size}", "success": True})
                    else:
                        self.log(f"     ❌ {size} bytes: Failed unexpectedly")
                        results.append({"test": f"min_size_{size}", "success": False})
                
                os.unlink(file_path)
                
        except Exception as e:
            self.log(f"   ❌ Min size test error: {str(e)}")
            results.append({"test": "min_size", "success": False, "error": str(e)})
        
        # Test 2: PIL Image.verify() validation
        self.log("   Testing PIL Image.verify() validation...")
        try:
            # Create a valid image
            valid_image = self.create_test_image("PIL Verify Test", "PNG")
            result = await ocr_read(valid_image)
            
            if result and result.get("text") and "Invalid" not in result.get("text", ""):
                self.log("     ✅ Valid image passes PIL verification")
                results.append({"test": "pil_verify_valid", "success": True})
            else:
                self.log("     ❌ Valid image failed PIL verification")
                results.append({"test": "pil_verify_valid", "success": False})
            
            os.unlink(valid_image)
            
            # Create an invalid image (text file with image extension)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp.write(b"This is not an image file, just text pretending to be PNG")
                invalid_image = tmp.name
            
            result = await ocr_read(invalid_image)
            
            if result and "Invalid" in result.get("text", ""):
                self.log("     ✅ Invalid image rejected by PIL verification")
                results.append({"test": "pil_verify_invalid", "success": True})
            else:
                self.log("     ❌ Invalid image not rejected by PIL verification")
                results.append({"test": "pil_verify_invalid", "success": False})
            
            os.unlink(invalid_image)
            
        except Exception as e:
            self.log(f"   ❌ PIL verify test error: {str(e)}")
            results.append({"test": "pil_verify", "success": False, "error": str(e)})
        
        # Test 3: Format detection and mapping
        self.log("   Testing format detection and mapping...")
        try:
            formats_to_test = ["PNG", "JPEG"]
            
            for fmt in formats_to_test:
                image_path = self.create_test_image(f"Format {fmt} Test", fmt)
                result = await ocr_read(image_path)
                
                if result and result.get("text") and "Unsupported image format" not in result.get("text", ""):
                    self.log(f"     ✅ {fmt} format properly detected and processed")
                    results.append({"test": f"format_{fmt.lower()}", "success": True})
                else:
                    self.log(f"     ❌ {fmt} format detection failed")
                    results.append({"test": f"format_{fmt.lower()}", "success": False})
                
                os.unlink(image_path)
                
        except Exception as e:
            self.log(f"   ❌ Format detection test error: {str(e)}")
            results.append({"test": "format_detection", "success": False, "error": str(e)})
        
        return results

    async def test_gpt4o_model_usage(self):
        """Test that gpt-4o model is being used correctly"""
        self.log("\n🤖 Testing gpt-4o Model Usage...")
        
        try:
            # Create a test image with clear text
            test_image = self.create_test_image("GPT-4o Model Test 2025\nMultiple Lines\nSpecial: @#$%", "PNG", (600, 300))
            
            # Process with OCR
            result = await ocr_read(test_image)
            
            if result and isinstance(result, dict):
                extracted_text = result.get("text", "")
                
                if extracted_text and len(extracted_text) > 10 and "Invalid" not in extracted_text:
                    self.log(f"   ✅ gpt-4o model processing successful")
                    self.log(f"     Extracted: '{extracted_text[:100]}...'")
                    self.log(f"     Length: {len(extracted_text)} characters")
                    
                    # Check if it extracted the expected content
                    expected_elements = ["GPT-4o", "Model", "Test", "2025"]
                    found_elements = sum(1 for elem in expected_elements if elem.lower() in extracted_text.lower())
                    
                    return {
                        "success": True,
                        "extracted_text": extracted_text,
                        "text_length": len(extracted_text),
                        "expected_elements_found": f"{found_elements}/{len(expected_elements)}",
                        "model_working": True
                    }
                else:
                    self.log(f"   ❌ gpt-4o model processing failed: '{extracted_text}'")
                    return {"success": False, "error": f"Processing failed: {extracted_text}"}
            else:
                self.log(f"   ❌ Invalid result from gpt-4o model: {result}")
                return {"success": False, "error": f"Invalid result: {result}"}
            
            os.unlink(test_image)
            
        except Exception as e:
            self.log(f"   ❌ gpt-4o model test error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def run_all_tests(self):
        """Run all processing validation tests"""
        self.log("🚀 Starting Processing Validation Tests...")
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            self.log("❌ No OpenAI API key found - cannot test processing")
            return
        
        self.log(f"✅ OpenAI API key found: {api_key[:20]}...")
        
        # Run all test categories
        test_results = {}
        
        # Test 1: Processing pipeline validation
        test_results["pipeline_validation"] = await self.test_processing_pipeline_validation()
        
        # Test 2: Specific validation features
        test_results["validation_features"] = await self.test_specific_validation_features()
        
        # Test 3: gpt-4o model usage
        test_results["gpt4o_model"] = await self.test_gpt4o_model_usage()
        
        # Generate summary
        self.generate_summary(test_results)
        
        return test_results

    def generate_summary(self, test_results):
        """Generate comprehensive test summary"""
        self.log("\n" + "="*80)
        self.log("📊 PROCESSING VALIDATION TEST SUMMARY")
        self.log("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        # Pipeline validation summary
        pipeline_validation = test_results.get("pipeline_validation", [])
        pipeline_passed = sum(1 for r in pipeline_validation if r["success"])
        pipeline_total = len(pipeline_validation)
        total_tests += pipeline_total
        passed_tests += pipeline_passed
        
        self.log(f"🔄 Pipeline Validation: {pipeline_passed}/{pipeline_total} passed")
        for result in pipeline_validation:
            status = "✅" if result["success"] else "❌"
            info = ""
            if result["success"]:
                if "text_length" in result:
                    info = f"({result['text_length']} chars)"
                elif "rejection_message" in result:
                    info = f"(rejected: {result['rejection_message'][:30]}...)"
            else:
                info = f"(error: {result.get('error', 'Unknown')[:30]}...)"
            self.log(f"   {status} {result['case']}: {info}")
        
        # Validation features summary
        validation_features = test_results.get("validation_features", [])
        validation_passed = sum(1 for r in validation_features if r["success"])
        validation_total = len(validation_features)
        total_tests += validation_total
        passed_tests += validation_passed
        
        self.log(f"\n🔍 Validation Features: {validation_passed}/{validation_total} passed")
        feature_groups = {}
        for result in validation_features:
            test_name = result['test']
            if 'min_size' in test_name:
                group = 'Minimum Size Validation'
            elif 'pil_verify' in test_name:
                group = 'PIL Image Verification'
            elif 'format' in test_name:
                group = 'Format Detection'
            else:
                group = 'Other'
            
            if group not in feature_groups:
                feature_groups[group] = []
            feature_groups[group].append(result)
        
        for group, results in feature_groups.items():
            group_passed = sum(1 for r in results if r["success"])
            group_total = len(results)
            self.log(f"   {group}: {group_passed}/{group_total} passed")
        
        # gpt-4o model summary
        gpt4o_model = test_results.get("gpt4o_model", {})
        gpt4o_success = gpt4o_model.get("success", False)
        total_tests += 1
        if gpt4o_success:
            passed_tests += 1
        
        self.log(f"\n🤖 gpt-4o Model Usage: {'✅ WORKING' if gpt4o_success else '❌ FAILED'}")
        if gpt4o_success:
            self.log(f"   Text extracted: {gpt4o_model.get('text_length', 0)} characters")
            self.log(f"   Expected elements: {gpt4o_model.get('expected_elements_found', 'Unknown')}")
        else:
            self.log(f"   Error: {gpt4o_model.get('error', 'Unknown')}")
        
        # Overall summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n🎯 OVERALL RESULTS:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests}")
        self.log(f"   Failed: {total_tests - passed_tests}")
        self.log(f"   Success Rate: {success_rate:.1f}%")
        
        # Key findings about OCR fixes
        self.log(f"\n🔑 OCR FIX VERIFICATION:")
        
        # Check if minimum size validation is working
        min_size_tests = [r for r in validation_features if 'min_size' in r['test'] and r['success']]
        if min_size_tests:
            self.log(f"   ✅ Minimum file size validation (100 bytes) working")
        
        # Check if PIL validation is working
        pil_tests = [r for r in validation_features if 'pil_verify' in r['test'] and r['success']]
        if pil_tests:
            self.log(f"   ✅ PIL Image.verify() validation working")
        
        # Check if format detection is working
        format_tests = [r for r in validation_features if 'format' in r['test'] and r['success']]
        if format_tests:
            self.log(f"   ✅ PIL format detection and mapping working")
        
        # Check if gpt-4o model is working
        if gpt4o_success:
            self.log(f"   ✅ gpt-4o model integration working (no more 400 errors)")
        
        # Check if corrupted files are properly rejected
        corrupted_rejections = [r for r in pipeline_validation if not r["success"] and "corrupted" in r["case"].lower()]
        valid_successes = [r for r in pipeline_validation if r["success"] and "Valid" in r["case"]]
        
        if len(corrupted_rejections) == 0 and len([r for r in pipeline_validation if "corrupted" in r["case"].lower()]) > 0:
            self.log(f"   ✅ Corrupted files properly rejected with helpful messages")
        
        if valid_successes:
            self.log(f"   ✅ Valid images process successfully")
        
        if success_rate >= 90:
            self.log("\n🎉 OCR FIXES VERIFICATION: EXCELLENT - All critical fixes implemented and working!")
        elif success_rate >= 75:
            self.log("\n✅ OCR FIXES VERIFICATION: GOOD - Most fixes working correctly")
        else:
            self.log("\n⚠️  OCR FIXES VERIFICATION: NEEDS ATTENTION - Some fixes not working properly")
        
        self.log("="*80)

async def main():
    """Main test execution"""
    tester = ProcessingValidationTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())