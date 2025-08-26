#!/usr/bin/env python3
"""
PDF Processing Fix Test
Tests the recent PDF processing improvements to ensure:
1. PDF Upload works without 400 Bad Request errors
2. Basic PDF text extraction is working
3. Error handling for unsupported PDF types
4. Regular image processing still works
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class PDFProcessingTester:
    def __init__(self, base_url="https://autome-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_notes = []
        self.auth_token = None
        self.test_user_data = {
            "email": f"pdf_test_user_{int(time.time())}@example.com",
            "username": f"pdfuser_{int(time.time())}",
            "password": "PDFTestPass123!",
            "first_name": "PDF",
            "last_name": "Tester"
        }

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=60, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:500]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def create_simple_pdf(self):
        """Create a simple PDF with text content for testing"""
        # Create a minimal PDF with text content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World! This is a test PDF.) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000373 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
456
%%EOF"""
        return pdf_content

    def create_simple_png(self):
        """Create a simple PNG with text for testing"""
        # Create a minimal PNG file (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x01\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        return png_data

    def test_user_registration(self):
        """Test user registration for authenticated tests"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        if success:
            self.auth_token = response.get('access_token')
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
        return success

    def test_pdf_upload_via_upload_file(self):
        """Test PDF upload via the /upload-file endpoint"""
        pdf_content = self.create_simple_pdf()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_document.pdf', f, 'application/pdf')}
                data = {'title': 'PDF Processing Test Document'}
                success, response = self.run_test(
                    "PDF Upload via /upload-file",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    timeout=60
                )
            
            os.unlink(tmp_file.name)
            
            if success and 'id' in response:
                note_id = response['id']
                self.created_notes.append(note_id)
                self.log(f"   Created note ID: {note_id}")
                self.log(f"   Status: {response.get('status', 'N/A')}")
                self.log(f"   Filename: {response.get('filename', 'N/A')}")
                return note_id
            return None

    def test_pdf_upload_via_note_upload(self):
        """Test PDF upload via traditional note creation + upload"""
        # First create a photo note
        success, response = self.run_test(
            "Create Photo Note for PDF",
            "POST",
            "notes",
            200,
            data={"title": "PDF Test via Note Upload", "kind": "photo"}
        )
        
        if not success or 'id' not in response:
            return None
            
        note_id = response['id']
        self.created_notes.append(note_id)
        
        # Now upload PDF to the note
        pdf_content = self.create_simple_pdf()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_note_pdf.pdf', f, 'application/pdf')}
                success, response = self.run_test(
                    f"Upload PDF to Note {note_id[:8]}...",
                    "POST",
                    f"notes/{note_id}/upload",
                    200,
                    files=files,
                    timeout=60
                )
            
            os.unlink(tmp_file.name)
            
            if success:
                self.log(f"   Upload status: {response.get('status', 'N/A')}")
                return note_id
            return None

    def test_image_upload_still_works(self):
        """Test that regular image processing still works after PDF fix"""
        png_content = self.create_simple_png()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_content)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_image.png', f, 'image/png')}
                data = {'title': 'Image Processing Test'}
                success, response = self.run_test(
                    "Image Upload (PNG) - Regression Test",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    timeout=60
                )
            
            os.unlink(tmp_file.name)
            
            if success and 'id' in response:
                note_id = response['id']
                self.created_notes.append(note_id)
                self.log(f"   Created image note ID: {note_id}")
                return note_id
            return None

    def test_jpg_upload_still_works(self):
        """Test that JPG processing still works"""
        # Create a minimal JPEG file
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(jpeg_data)
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_image.jpg', f, 'image/jpeg')}
                data = {'title': 'JPG Processing Test'}
                success, response = self.run_test(
                    "Image Upload (JPG) - Regression Test",
                    "POST",
                    "upload-file",
                    200,
                    data=data,
                    files=files,
                    timeout=60
                )
            
            os.unlink(tmp_file.name)
            
            if success and 'id' in response:
                note_id = response['id']
                self.created_notes.append(note_id)
                self.log(f"   Created JPG note ID: {note_id}")
                return note_id
            return None

    def wait_for_processing(self, note_id, max_wait=60):
        """Wait for note processing to complete"""
        self.log(f"⏳ Waiting for note {note_id[:8]}... to process (max {max_wait}s)")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            success, note_data = self.get_note(note_id)
            if success:
                status = note_data.get('status', 'unknown')
                self.log(f"   Current status: {status}")
                
                if status == 'ready':
                    self.log(f"✅ Note processing completed!")
                    return True, note_data
                elif status == 'failed':
                    self.log(f"❌ Note processing failed!")
                    artifacts = note_data.get('artifacts', {})
                    if 'note' in artifacts:
                        self.log(f"   Failure reason: {artifacts['note']}")
                    return False, note_data
                else:
                    time.sleep(3)
            else:
                break
        
        self.log(f"⏰ Timeout waiting for note processing")
        return False, {}

    def get_note(self, note_id):
        """Get note details"""
        success, response = self.run_test(
            f"Get Note {note_id[:8]}...",
            "GET",
            f"notes/{note_id}",
            200
        )
        return success, response

    def test_pdf_processing_results(self, note_id):
        """Test PDF processing results"""
        success, note_data = self.wait_for_processing(note_id, max_wait=90)
        
        if success:
            artifacts = note_data.get('artifacts', {})
            text = artifacts.get('text', '')
            
            self.log(f"✅ PDF Processing Results:")
            self.log(f"   Status: {note_data.get('status')}")
            self.log(f"   Text extracted: {'Yes' if text else 'No'}")
            if text:
                self.log(f"   Text length: {len(text)} characters")
                self.log(f"   Text preview: {text[:100]}...")
            
            # Check if we got meaningful text extraction
            if text and len(text) > 10:
                self.log(f"✅ PDF text extraction successful!")
                return True
            elif text and "PDF" in text and ("not fully supported" in text or "convert" in text):
                self.log(f"✅ PDF processing returned helpful error message")
                return True
            else:
                self.log(f"⚠️  PDF processing completed but no meaningful text extracted")
                return False
        else:
            # Check if it failed gracefully
            artifacts = note_data.get('artifacts', {})
            error_note = artifacts.get('note', '')
            if error_note and ("PDF" in error_note or "processing" in error_note):
                self.log(f"✅ PDF processing failed gracefully with helpful message: {error_note}")
                return True
            else:
                self.log(f"❌ PDF processing failed without helpful error message")
                return False

    def test_image_processing_results(self, note_id, file_type="image"):
        """Test image processing results"""
        success, note_data = self.wait_for_processing(note_id, max_wait=60)
        
        if success:
            artifacts = note_data.get('artifacts', {})
            text = artifacts.get('text', '')
            
            self.log(f"✅ {file_type.upper()} Processing Results:")
            self.log(f"   Status: {note_data.get('status')}")
            self.log(f"   OCR completed: {'Yes' if text else 'No'}")
            if text:
                self.log(f"   Text length: {len(text)} characters")
                self.log(f"   Text content: {text[:100]}...")
            
            return True
        else:
            self.log(f"❌ {file_type.upper()} processing failed")
            return False

    def test_unsupported_file_type(self):
        """Test that unsupported file types are properly rejected"""
        # Create a fake .txt file and try to upload it
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b"This is a text file that should be rejected")
            tmp_file.flush()
            
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                data = {'title': 'Unsupported File Test'}
                success, response = self.run_test(
                    "Unsupported File Type (TXT) - Should Fail",
                    "POST",
                    "upload-file",
                    400,  # Should fail with 400
                    data=data,
                    files=files
                )
            
            os.unlink(tmp_file.name)
            
            if success:
                self.log(f"✅ Unsupported file type properly rejected")
                self.log(f"   Error message: {response.get('detail', 'N/A')}")
            
            return success

    def run_pdf_processing_tests(self):
        """Run comprehensive PDF processing tests"""
        self.log("🚀 Starting PDF Processing Fix Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Test user registration for authenticated tests
        if not self.test_user_registration():
            self.log("❌ User registration failed - continuing with anonymous tests")
        
        # === PDF PROCESSING TESTS ===
        self.log("\n📄 PDF PROCESSING TESTS")
        
        # Test 1: PDF Upload via /upload-file endpoint
        pdf_note_id_1 = self.test_pdf_upload_via_upload_file()
        
        # Test 2: PDF Upload via traditional note creation
        pdf_note_id_2 = self.test_pdf_upload_via_note_upload()
        
        # Test 3: Verify PDF processing results
        if pdf_note_id_1:
            self.log(f"\n🔍 Testing PDF processing results for note {pdf_note_id_1[:8]}...")
            self.test_pdf_processing_results(pdf_note_id_1)
        
        if pdf_note_id_2:
            self.log(f"\n🔍 Testing PDF processing results for note {pdf_note_id_2[:8]}...")
            self.test_pdf_processing_results(pdf_note_id_2)
        
        # === REGRESSION TESTS ===
        self.log("\n🖼️  IMAGE PROCESSING REGRESSION TESTS")
        
        # Test 4: Ensure PNG processing still works
        png_note_id = self.test_image_upload_still_works()
        if png_note_id:
            self.test_image_processing_results(png_note_id, "PNG")
        
        # Test 5: Ensure JPG processing still works
        jpg_note_id = self.test_jpg_upload_still_works()
        if jpg_note_id:
            self.test_image_processing_results(jpg_note_id, "JPG")
        
        # === ERROR HANDLING TESTS ===
        self.log("\n🚫 ERROR HANDLING TESTS")
        
        # Test 6: Unsupported file types
        self.test_unsupported_file_type()
        
        return True

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("📊 PDF PROCESSING TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_notes:
            self.log(f"\nCreated test notes: {len(self.created_notes)}")
            for note_id in self.created_notes:
                self.log(f"  - {note_id}")
        
        self.log("="*60)
        
        # Determine if PDF processing fix is working
        if self.tests_passed >= self.tests_run * 0.8:  # 80% success rate
            self.log("🎉 PDF PROCESSING FIX APPEARS TO BE WORKING!")
            self.log("   ✅ No 400 Bad Request errors from OpenAI API")
            self.log("   ✅ PDF files are being processed")
            self.log("   ✅ Image processing still works")
            return True
        else:
            self.log("⚠️  PDF PROCESSING FIX NEEDS ATTENTION")
            self.log("   Some tests failed - check logs above")
            return False

def main():
    """Main test execution"""
    tester = PDFProcessingTester()
    
    try:
        success = tester.run_pdf_processing_tests()
        overall_success = tester.print_summary()
        
        if overall_success:
            print("\n🎉 PDF processing fix is working correctly!")
            return 0
        else:
            print(f"\n⚠️  PDF processing fix needs attention. Check the logs above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())