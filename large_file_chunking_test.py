#!/usr/bin/env python3
"""
Large File Chunking Test
Tests the chunking system for files over 24MB
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://typescript-auth.preview.emergentagent.com/api"
LARGE_FILE_PATH = "/tmp/autome_storage/2b3bb42e-04c6-446d-8c8f-6f34fd5b5061_0639ab87-0315-42be-bb12-61a1f466adf9_Regional Meeting 21 August - Recap Session 1.mp3"

class LargeFileChunkingTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_large_file_chunking(self):
        """Test chunking system with large file"""
        try:
            if not os.path.exists(LARGE_FILE_PATH):
                self.log_result("Large File Chunking Test", False, f"Large test file not found: {LARGE_FILE_PATH}")
                return None
            
            # Get file size
            file_size = os.path.getsize(LARGE_FILE_PATH)
            file_size_mb = file_size / (1024*1024)
            self.log_result("Large File Size Check", True, f"Test file size: {file_size_mb:.1f} MB")
            
            # Verify file is over chunking threshold (24MB)
            if file_size_mb < 24:
                self.log_result("Chunking Threshold Check", False, f"File too small for chunking test: {file_size_mb:.1f} MB")
                return None
            else:
                self.log_result("Chunking Threshold Check", True, f"File exceeds 24MB threshold: {file_size_mb:.1f} MB")
            
            # Upload the large file
            with open(LARGE_FILE_PATH, 'rb') as f:
                files = {'file': ('large_meeting.mp3', f, 'audio/mp3')}
                data = {'title': 'Large File Chunking Test - 41MB Meeting'}
                
                print("Uploading large file... (this may take a moment)")
                response = self.session.post(f"{BACKEND_URL}/upload-file", files=files, data=data)
                
                if response.status_code == 200:
                    upload_result = response.json()
                    note_id = upload_result.get("id")
                    status = upload_result.get("status")
                    
                    self.log_result("Large File Upload", True, 
                                  f"Note ID: {note_id}, Status: {status}")
                    return note_id
                else:
                    self.log_result("Large File Upload", False, 
                                  f"HTTP {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            self.log_result("Large File Upload", False, f"Exception: {str(e)}")
            return None
    
    def test_chunking_processing(self, note_id):
        """Test that chunking processing works correctly"""
        if not note_id:
            return False
        
        try:
            # Monitor processing with extended timeout for large files
            max_wait_time = 900  # 15 minutes for large file
            check_interval = 30  # 30 seconds
            start_time = time.time()
            
            status_progression = []
            
            print(f"Monitoring chunking processing (max {max_wait_time//60} minutes)...")
            
            while time.time() - start_time < max_wait_time:
                response = self.session.get(f"{BACKEND_URL}/notes/{note_id}")
                if response.status_code == 200:
                    note_data = response.json()
                    current_status = note_data.get("status")
                    
                    if not status_progression or current_status != status_progression[-1]:
                        status_progression.append(current_status)
                        elapsed = int(time.time() - start_time)
                        self.log_result(f"Chunking Status Update ({elapsed}s)", True, 
                                      f"Status: {current_status}")
                    
                    if current_status in ["ready", "failed"]:
                        break
                
                time.sleep(check_interval)
            
            final_status = status_progression[-1] if status_progression else "unknown"
            total_time = int(time.time() - start_time)
            
            if final_status == "ready":
                self.log_result("Chunking Processing Complete", True, 
                              f"Completed in {total_time}s, Progression: {' -> '.join(status_progression)}")
                return True
            elif final_status == "failed":
                self.log_result("Chunking Processing Failed", False, 
                              f"Failed after {total_time}s, Progression: {' -> '.join(status_progression)}")
                return False
            else:
                self.log_result("Chunking Processing Timeout", False, 
                              f"Timed out after {total_time}s, Final status: {final_status}")
                return False
                
        except Exception as e:
            self.log_result("Chunking Processing", False, f"Exception: {str(e)}")
            return False
    
    def test_chunked_transcript_quality(self, note_id):
        """Test quality of transcript from chunked processing"""
        if not note_id:
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/notes/{note_id}")
            if response.status_code != 200:
                self.log_result("Chunked Transcript Quality", False, f"HTTP {response.status_code}")
                return False
            
            note_data = response.json()
            artifacts = note_data.get("artifacts", {})
            transcript = artifacts.get("transcript", "")
            
            if not transcript:
                self.log_result("Chunked Transcript Quality", False, "No transcript found")
                return False
            
            # Analyze transcript quality
            transcript_length = len(transcript)
            word_count = len(transcript.split())
            
            # Check for chunk markers (should be present for chunked files)
            chunk_markers = transcript.count("[Part ")
            
            # Quality checks
            quality_checks = []
            
            if transcript_length > 1000:
                quality_checks.append(f"Length: {transcript_length} chars")
            else:
                self.log_result("Chunked Transcript Quality", False, f"Transcript too short: {transcript_length} chars")
                return False
            
            if word_count > 100:
                quality_checks.append(f"Words: {word_count}")
            
            if chunk_markers > 0:
                quality_checks.append(f"Chunk markers: {chunk_markers}")
            
            self.log_result("Chunked Transcript Quality", True, 
                          f"Quality metrics: {', '.join(quality_checks)}")
            
            return True
            
        except Exception as e:
            self.log_result("Chunked Transcript Quality", False, f"Exception: {str(e)}")
            return False
    
    def run_chunking_test(self):
        """Run the complete chunking test"""
        print("="*80)
        print("LARGE FILE CHUNKING SYSTEM TEST")
        print("="*80)
        
        # Test chunking upload
        note_id = self.test_large_file_chunking()
        if not note_id:
            print("❌ Large file upload failed - cannot continue")
            return False
        
        # Test chunking processing
        if not self.test_chunking_processing(note_id):
            print("❌ Chunking processing failed")
            return False
        
        # Test transcript quality
        if not self.test_chunked_transcript_quality(note_id):
            print("❌ Chunked transcript quality check failed")
            return False
        
        # Summary
        print("\n" + "="*80)
        print("CHUNKING TEST SUMMARY")
        print("="*80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"Overall Result: {'✅ PASS' if success_rate >= 80 else '❌ FAIL'}")
        
        # Detailed results
        print(f"\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = LargeFileChunkingTester()
    success = tester.run_chunking_test()
    
    if success:
        print("\n🎉 LARGE FILE CHUNKING TEST PASSED!")
        exit(0)
    else:
        print("\n💥 LARGE FILE CHUNKING TEST FAILED!")
        exit(1)

if __name__ == "__main__":
    main()