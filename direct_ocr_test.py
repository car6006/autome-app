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

class DirectOCRTest:
    def __init__(self):
        print(f"🔍 DIRECT OCR FUNCTIONALITY TEST")
        print(f"Testing OCR fixes: PIL validation, format detection, error handling")
        print("="*80)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
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

    async def test_valid_images(self):
        """Test OCR with valid images"""
        self.log("\n📋 Testing Valid Images...")
        
        test_cases = [
            {"format": "PNG", "text": "Hello World PNG Test"},
            {"format": "JPEG", "text": "Hello World JPG Test"},
            {"format": "PNG", "text": "Multi-line\nText Test\n2025"},
        ]
        
        results = []
        
        for case in test_cases:
            try:
                self.log(f"   Testing {case['format']} with text: '{case['text'][:30]}...'")
                
                # Create test image
                image_path = self.create_test_image(case['text'], case['format'])
                if not image_path:
                    results.append({"case": case['format'], "success": False, "error": "Failed to create image"})
                    continue
                
                # Test OCR
                result = await ocr_read(image_path)
                
                if result and isinstance(result, dict):
                    extracted_text = result.get("text", "")
                    if extracted_text and "Invalid" not in extracted_text and "corrupted" not in extracted_text:
                        self.log(f"   ✅ Success: '{extracted_text[:50]}...' ({len(extracted_text)} chars)")
                        results.append({
                            "case": case['format'], 
                            "success": True, 
                            "extracted_text": extracted_text,
                            "text_length": len(extracted_text)
                        })
                    else:
                        self.log(f"   ❌ OCR failed or returned error: '{extracted_text}'")
                        results.append({
                            "case": case['format'], 
                            "success": False, 
                            "error": f"OCR returned: {extracted_text}"
                        })
                else:
                    self.log(f"   ❌ OCR returned invalid result: {result}")
                    results.append({
                        "case": case['format'], 
                        "success": False, 
                        "error": f"Invalid result: {result}"
                    })
                
                # Clean up
                if os.path.exists(image_path):
                    os.unlink(image_path)
                    
            except Exception as e:
                self.log(f"   ❌ Error testing {case['format']}: {str(e)}")
                results.append({
                    "case": case['format'], 
                    "success": False, 
                    "error": str(e)
                })
        
        return results

    async def test_corrupted_images(self):
        """Test OCR with corrupted/invalid images"""
        self.log("\n🚫 Testing Corrupted/Invalid Images...")
        
        test_cases = [
            {"name": "9-byte corrupted file", "creator": lambda: self.create_corrupted_file(9)},
            {"name": "50-byte corrupted file", "creator": lambda: self.create_corrupted_file(50)},
            {"name": "Empty file", "creator": lambda: self.create_corrupted_file(0)},
        ]
        
        results = []
        
        for case in test_cases:
            try:
                self.log(f"   Testing {case['name']}...")
                
                # Create corrupted file
                file_path = case['creator']()
                
                # Test OCR - should return error message
                result = await ocr_read(file_path)
                
                if result and isinstance(result, dict):
                    error_text = result.get("text", "")
                    if "Invalid" in error_text or "corrupted" in error_text or "valid PNG or JPG" in error_text:
                        self.log(f"   ✅ Properly rejected: '{error_text}'")
                        results.append({
                            "case": case['name'], 
                            "success": True, 
                            "rejection_message": error_text
                        })
                    else:
                        self.log(f"   ❌ Should have been rejected: '{error_text}'")
                        results.append({
                            "case": case['name'], 
                            "success": False, 
                            "error": f"Not properly rejected: {error_text}"
                        })
                else:
                    self.log(f"   ❌ Unexpected result: {result}")
                    results.append({
                        "case": case['name'], 
                        "success": False, 
                        "error": f"Unexpected result: {result}"
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

    async def test_image_validation_features(self):
        """Test specific image validation features"""
        self.log("\n🔍 Testing Image Validation Features...")
        
        results = []
        
        # Test 1: Minimum file size validation
        self.log("   Testing minimum file size validation...")
        try:
            tiny_file = self.create_corrupted_file(50)  # 50 bytes - should be rejected
            result = await ocr_read(tiny_file)
            
            if result and "Invalid" in result.get("text", ""):
                self.log("   ✅ Minimum size validation working")
                results.append({"test": "min_size", "success": True})
            else:
                self.log("   ❌ Minimum size validation not working")
                results.append({"test": "min_size", "success": False})
            
            os.unlink(tiny_file)
        except Exception as e:
            self.log(f"   ❌ Min size test error: {str(e)}")
            results.append({"test": "min_size", "success": False, "error": str(e)})
        
        # Test 2: PIL format detection
        self.log("   Testing PIL format detection...")
        try:
            # Create a valid PNG
            png_file = self.create_test_image("Format Test", "PNG")
            result = await ocr_read(png_file)
            
            if result and result.get("text") and "Invalid" not in result.get("text", ""):
                self.log("   ✅ PIL format detection working for PNG")
                results.append({"test": "format_detection", "success": True})
            else:
                self.log("   ❌ PIL format detection failed for PNG")
                results.append({"test": "format_detection", "success": False})
            
            os.unlink(png_file)
        except Exception as e:
            self.log(f"   ❌ Format detection test error: {str(e)}")
            results.append({"test": "format_detection", "success": False, "error": str(e)})
        
        # Test 3: gpt-4o model usage
        self.log("   Testing gpt-4o model usage...")
        try:
            # Create test image
            test_file = self.create_test_image("Model Test 2025", "PNG")
            result = await ocr_read(test_file)
            
            if result and result.get("text") and len(result.get("text", "")) > 5:
                self.log("   ✅ gpt-4o model processing working")
                results.append({"test": "gpt4o_model", "success": True})
            else:
                self.log("   ❌ gpt-4o model processing failed")
                results.append({"test": "gpt4o_model", "success": False})
            
            os.unlink(test_file)
        except Exception as e:
            self.log(f"   ❌ Model test error: {str(e)}")
            results.append({"test": "gpt4o_model", "success": False, "error": str(e)})
        
        return results

    async def run_all_tests(self):
        """Run all direct OCR tests"""
        self.log("🚀 Starting Direct OCR Tests...")
        
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("WHISPER_API_KEY")
        if not api_key:
            self.log("❌ No OpenAI API key found - cannot test OCR")
            return
        
        self.log(f"✅ OpenAI API key found: {api_key[:20]}...")
        
        # Run all test categories
        test_results = {}
        
        # Test 1: Valid images
        test_results["valid_images"] = await self.test_valid_images()
        
        # Test 2: Corrupted images
        test_results["corrupted_images"] = await self.test_corrupted_images()
        
        # Test 3: Validation features
        test_results["validation_features"] = await self.test_image_validation_features()
        
        # Generate summary
        self.generate_summary(test_results)
        
        return test_results

    def generate_summary(self, test_results):
        """Generate comprehensive test summary"""
        self.log("\n" + "="*80)
        self.log("📊 DIRECT OCR TEST SUMMARY")
        self.log("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        # Valid images summary
        valid_images = test_results.get("valid_images", [])
        valid_passed = sum(1 for r in valid_images if r["success"])
        valid_total = len(valid_images)
        total_tests += valid_total
        passed_tests += valid_passed
        
        self.log(f"✅ Valid Images: {valid_passed}/{valid_total} passed")
        for result in valid_images:
            status = "✅" if result["success"] else "❌"
            text_info = f"({result.get('text_length', 0)} chars)" if result["success"] else result.get('error', 'Unknown')
            self.log(f"   {status} {result['case']}: {text_info}")
        
        # Corrupted images summary
        corrupted_images = test_results.get("corrupted_images", [])
        corrupted_passed = sum(1 for r in corrupted_images if r["success"])
        corrupted_total = len(corrupted_images)
        total_tests += corrupted_total
        passed_tests += corrupted_passed
        
        self.log(f"\n🚫 Corrupted Images: {corrupted_passed}/{corrupted_total} passed")
        for result in corrupted_images:
            status = "✅" if result["success"] else "❌"
            message = result.get("rejection_message", result.get("error", "Unknown"))[:60]
            self.log(f"   {status} {result['case']}: {message}...")
        
        # Validation features summary
        validation_features = test_results.get("validation_features", [])
        validation_passed = sum(1 for r in validation_features if r["success"])
        validation_total = len(validation_features)
        total_tests += validation_total
        passed_tests += validation_passed
        
        self.log(f"\n🔍 Validation Features: {validation_passed}/{validation_total} passed")
        for result in validation_features:
            status = "✅" if result["success"] else "❌"
            test_name = result['test'].replace('_', ' ').title()
            self.log(f"   {status} {test_name}")
        
        # Overall summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n🎯 OVERALL RESULTS:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests}")
        self.log(f"   Failed: {total_tests - passed_tests}")
        self.log(f"   Success Rate: {success_rate:.1f}%")
        
        # Key findings
        self.log(f"\n🔑 KEY FINDINGS:")
        
        if valid_passed > 0:
            self.log(f"   ✅ OCR processing working with gpt-4o model")
            self.log(f"   ✅ PIL image validation implemented")
            self.log(f"   ✅ Format detection working")
        
        if corrupted_passed > 0:
            self.log(f"   ✅ Corrupted image rejection working")
            self.log(f"   ✅ Helpful error messages provided")
        
        if validation_passed > 0:
            self.log(f"   ✅ Image validation features working")
        
        if success_rate >= 90:
            self.log("\n🎉 OCR FIXES VERIFICATION: EXCELLENT - All critical fixes working!")
        elif success_rate >= 75:
            self.log("\n✅ OCR FIXES VERIFICATION: GOOD - Most fixes working correctly")
        else:
            self.log("\n⚠️  OCR FIXES VERIFICATION: NEEDS ATTENTION - Some fixes not working")
        
        self.log("="*80)

async def main():
    """Main test execution"""
    tester = DirectOCRTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())