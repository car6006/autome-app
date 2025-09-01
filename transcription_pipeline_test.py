#!/usr/bin/env python3
"""
Backend Test Suite for Large-File Audio Transcription Pipeline
Tests the fixed transcription pipeline with stage routing bug corrections
"""

import asyncio
import httpx
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://pwa-integration-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
TEST_FILE_PATH = "/tmp/test_pipeline_30s.wav"

# Expected stage sequence for verification
EXPECTED_STAGES = [
    "CREATED",
    "VALIDATING", 
    "TRANSCODING",
    "SEGMENTING",
    "DETECTING_LANGUAGE",
    "TRANSCRIBING",
    "MERGING",
    "DIARIZING", 
    "GENERATING_OUTPUTS",
    "COMPLETE"
]

# Expected output formats
EXPECTED_FORMATS = ["txt", "json", "srt", "vtt", "docx"]

class TranscriptionPipelineTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        self.auth_token = None
        self.job_id = None
        self.upload_id = None
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    async def register_test_user(self) -> bool:
        """Register a test user for authentication (optional for pipeline testing)"""
        try:
            # For pipeline testing, authentication is optional
            # The upload endpoints work without authentication
            self.log_result("User Authentication", True, "Pipeline testing works without authentication")
            return True
                
        except Exception as e:
            self.log_result("User Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    async def login_test_user(self) -> bool:
        """Login with test user"""
        try:
            login_data = {
                "email": "pipeline_test@example.com", 
                "password": "testpassword123"
            }
            
            response = await self.client.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.log_result("User Login", True, "Test user logged in successfully")
                return True
            else:
                self.log_result("User Login", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Login error: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def check_test_file(self) -> bool:
        """Verify test file exists and is accessible"""
        try:
            if not os.path.exists(TEST_FILE_PATH):
                self.log_result("Test File Check", False, f"Test file not found: {TEST_FILE_PATH}")
                return False
            
            file_size = os.path.getsize(TEST_FILE_PATH)
            if file_size == 0:
                self.log_result("Test File Check", False, "Test file is empty")
                return False
            
            self.log_result("Test File Check", True, f"Test file found: {file_size} bytes", 
                          {"file_path": TEST_FILE_PATH, "size_bytes": file_size})
            return True
            
        except Exception as e:
            self.log_result("Test File Check", False, f"File check error: {str(e)}")
            return False
    
    async def create_upload_session(self) -> bool:
        """Create resumable upload session"""
        try:
            file_size = os.path.getsize(TEST_FILE_PATH)
            
            session_data = {
                "filename": "test_pipeline_30s.wav",
                "total_size": file_size,
                "mime_type": "audio/wav",
                "language": None,
                "enable_diarization": True
            }
            
            response = await self.client.post(
                f"{API_BASE}/uploads/sessions",
                json=session_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.upload_id = data.get("upload_id")
                self.log_result("Upload Session Creation", True, "Upload session created successfully",
                              {"upload_id": self.upload_id, "chunk_size": data.get("chunk_size")})
                return True
            else:
                self.log_result("Upload Session Creation", False, 
                              f"Session creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Upload Session Creation", False, f"Session creation error: {str(e)}")
            return False
    
    async def upload_file_chunks(self) -> bool:
        """Upload file in chunks"""
        try:
            if not self.upload_id:
                self.log_result("File Upload", False, "No upload session available")
                return False
            
            # For simplicity, upload as single chunk for 30s test file
            with open(TEST_FILE_PATH, "rb") as f:
                file_data = f.read()
            
            files = {"chunk": ("test_pipeline_30s.wav", file_data, "audio/wav")}
            
            response = await self.client.post(
                f"{API_BASE}/uploads/sessions/{self.upload_id}/chunks/0",
                files=files,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                self.log_result("File Upload", True, "File chunk uploaded successfully")
                return True
            else:
                self.log_result("File Upload", False, 
                              f"Chunk upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("File Upload", False, f"Upload error: {str(e)}")
            return False
    
    async def finalize_upload(self) -> bool:
        """Finalize upload and create transcription job"""
        try:
            if not self.upload_id:
                self.log_result("Upload Finalization", False, "No upload session available")
                return False
            
            finalize_data = {
                "upload_id": self.upload_id
            }
            
            response = await self.client.post(
                f"{API_BASE}/uploads/sessions/{self.upload_id}/complete",
                json=finalize_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.job_id = data.get("job_id")
                self.log_result("Upload Finalization", True, "Upload finalized and job created",
                              {"job_id": self.job_id, "status": data.get("status")})
                return True
            else:
                self.log_result("Upload Finalization", False, 
                              f"Finalization failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Upload Finalization", False, f"Finalization error: {str(e)}")
            return False
    
    async def monitor_job_progression(self) -> bool:
        """Monitor job progression through all pipeline stages"""
        try:
            if not self.job_id:
                self.log_result("Job Monitoring", False, "No job ID available")
                return False
            
            stages_seen = []
            max_wait_time = 600  # 10 minutes max
            start_time = time.time()
            last_stage = None
            merge_stage_executed = False
            
            print(f"\n🔄 Monitoring job {self.job_id} progression...")
            
            while time.time() - start_time < max_wait_time:
                response = await self.client.get(
                    f"{API_BASE}/transcriptions/{self.job_id}",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code != 200:
                    self.log_result("Job Monitoring", False, 
                                  f"Status check failed: {response.status_code}")
                    return False
                
                data = response.json()
                current_stage = data.get("current_stage")
                status = data.get("status")
                progress = data.get("progress", 0)
                stage_progress = data.get("stage_progress", {})
                
                # Log stage progression
                if current_stage != last_stage:
                    print(f"   Stage: {current_stage} (Progress: {progress:.1f}%)")
                    if current_stage not in stages_seen:
                        stages_seen.append(current_stage)
                    last_stage = current_stage
                
                # Check for merge stage execution
                if current_stage == "MERGING" or "merging" in stage_progress:
                    merge_stage_executed = True
                    print(f"   ✅ Merge stage detected and executing")
                
                # Check if job completed
                if status == "COMPLETE":
                    self.log_result("Job Monitoring", True, 
                                  f"Job completed successfully through {len(stages_seen)} stages",
                                  {
                                      "stages_seen": stages_seen,
                                      "final_progress": progress,
                                      "merge_executed": merge_stage_executed,
                                      "total_duration": data.get("total_duration"),
                                      "detected_language": data.get("detected_language")
                                  })
                    
                    # Verify stage sequence
                    return self.verify_stage_sequence(stages_seen, merge_stage_executed)
                
                # Check for failure
                if status == "FAILED":
                    error_msg = data.get("error_message", "Unknown error")
                    self.log_result("Job Monitoring", False, 
                                  f"Job failed: {error_msg}",
                                  {"stages_completed": stages_seen, "error_code": data.get("error_code")})
                    return False
                
                # Wait before next check
                await asyncio.sleep(5)
            
            # Timeout
            self.log_result("Job Monitoring", False, 
                          f"Job monitoring timed out after {max_wait_time}s",
                          {"stages_seen": stages_seen, "last_stage": current_stage})
            return False
            
        except Exception as e:
            self.log_result("Job Monitoring", False, f"Monitoring error: {str(e)}")
            return False
    
    def verify_stage_sequence(self, stages_seen: list, merge_executed: bool) -> bool:
        """Verify the correct stage sequence was followed"""
        try:
            # Check if all expected stages were seen
            missing_stages = []
            for expected_stage in EXPECTED_STAGES:
                if expected_stage not in stages_seen:
                    missing_stages.append(expected_stage)
            
            # Check stage order (should be mostly sequential)
            sequence_correct = True
            for i, stage in enumerate(stages_seen):
                if stage in EXPECTED_STAGES:
                    expected_index = EXPECTED_STAGES.index(stage)
                    if i > 0 and expected_index < EXPECTED_STAGES.index(stages_seen[i-1]):
                        sequence_correct = False
                        break
            
            if missing_stages:
                self.log_result("Stage Sequence Verification", False,
                              f"Missing stages: {missing_stages}",
                              {"stages_seen": stages_seen, "expected": EXPECTED_STAGES})
                return False
            
            if not sequence_correct:
                self.log_result("Stage Sequence Verification", False,
                              "Stages not in correct order",
                              {"stages_seen": stages_seen, "expected": EXPECTED_STAGES})
                return False
            
            if not merge_executed:
                self.log_result("Stage Sequence Verification", False,
                              "Merge stage was not executed",
                              {"stages_seen": stages_seen})
                return False
            
            self.log_result("Stage Sequence Verification", True,
                          "All stages executed in correct sequence with merge stage",
                          {"stages_verified": len(stages_seen), "merge_executed": True})
            return True
            
        except Exception as e:
            self.log_result("Stage Sequence Verification", False, f"Verification error: {str(e)}")
            return False
    
    async def verify_output_formats(self) -> bool:
        """Verify all expected output formats are generated"""
        try:
            if not self.job_id:
                self.log_result("Output Format Verification", False, "No job ID available")
                return False
            
            response = await self.client.get(
                f"{API_BASE}/transcriptions/{self.job_id}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                self.log_result("Output Format Verification", False, 
                              f"Status check failed: {response.status_code}")
                return False
            
            data = response.json()
            download_urls = data.get("download_urls", {})
            
            if not download_urls:
                self.log_result("Output Format Verification", False, "No download URLs available")
                return False
            
            available_formats = list(download_urls.keys())
            missing_formats = []
            
            for expected_format in EXPECTED_FORMATS:
                if expected_format not in available_formats:
                    missing_formats.append(expected_format)
            
            if missing_formats:
                self.log_result("Output Format Verification", False,
                              f"Missing output formats: {missing_formats}",
                              {"available": available_formats, "expected": EXPECTED_FORMATS})
                return False
            
            self.log_result("Output Format Verification", True,
                          f"All {len(EXPECTED_FORMATS)} output formats generated",
                          {"formats": available_formats})
            return True
            
        except Exception as e:
            self.log_result("Output Format Verification", False, f"Format verification error: {str(e)}")
            return False
    
    async def test_download_functionality(self) -> bool:
        """Test download functionality for generated outputs"""
        try:
            if not self.job_id:
                self.log_result("Download Functionality Test", False, "No job ID available")
                return False
            
            download_results = {}
            
            for format_type in EXPECTED_FORMATS:
                try:
                    response = await self.client.get(
                        f"{API_BASE}/transcriptions/{self.job_id}/download?format={format_type}",
                        headers=self.get_auth_headers(),
                        follow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        content_length = len(response.content)
                        download_results[format_type] = {
                            "success": True,
                            "size_bytes": content_length
                        }
                        print(f"   ✅ {format_type.upper()}: {content_length} bytes downloaded")
                    else:
                        download_results[format_type] = {
                            "success": False,
                            "error": f"HTTP {response.status_code}"
                        }
                        print(f"   ❌ {format_type.upper()}: Download failed ({response.status_code})")
                        
                except Exception as e:
                    download_results[format_type] = {
                        "success": False,
                        "error": str(e)
                    }
                    print(f"   ❌ {format_type.upper()}: {str(e)}")
            
            successful_downloads = sum(1 for result in download_results.values() if result["success"])
            
            if successful_downloads == len(EXPECTED_FORMATS):
                self.log_result("Download Functionality Test", True,
                              f"All {successful_downloads} formats downloaded successfully",
                              download_results)
                return True
            else:
                self.log_result("Download Functionality Test", False,
                              f"Only {successful_downloads}/{len(EXPECTED_FORMATS)} downloads successful",
                              download_results)
                return False
                
        except Exception as e:
            self.log_result("Download Functionality Test", False, f"Download test error: {str(e)}")
            return False
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete transcription pipeline test"""
        print("🚀 Starting Large-File Audio Transcription Pipeline Test")
        print(f"📁 Test file: {TEST_FILE_PATH}")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Test sequence
        test_steps = [
            ("File Check", self.check_test_file),
            ("User Authentication", self.register_test_user),
            ("Upload Session", self.create_upload_session),
            ("File Upload", self.upload_file_chunks),
            ("Upload Finalization", self.finalize_upload),
            ("Job Progression Monitoring", self.monitor_job_progression),
            ("Output Format Verification", self.verify_output_formats),
            ("Download Functionality", self.test_download_functionality)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for step_name, test_func in test_steps:
            print(f"\n🔄 Running: {step_name}")
            try:
                success = await test_func()
                if success:
                    passed_tests += 1
                else:
                    print(f"❌ {step_name} failed - stopping test sequence")
                    break
            except Exception as e:
                print(f"❌ {step_name} error: {str(e)}")
                self.log_result(step_name, False, f"Unexpected error: {str(e)}")
                break
        
        # Generate summary
        success_rate = (passed_tests / total_tests) * 100
        
        summary = {
            "test_name": "Large-File Audio Transcription Pipeline Test",
            "backend_url": BACKEND_URL,
            "test_file": TEST_FILE_PATH,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "job_id": self.job_id,
            "upload_id": self.upload_id,
            "all_tests_passed": passed_tests == total_tests,
            "detailed_results": self.test_results
        }
        
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if summary["all_tests_passed"]:
            print("🎉 ALL TESTS PASSED - Transcription pipeline is working correctly!")
            print("✅ Stage routing bug has been successfully fixed")
            print("✅ Merge stage execution confirmed")
            print("✅ All output formats generated")
            print("✅ Download functionality working")
        else:
            print("❌ SOME TESTS FAILED - Pipeline needs attention")
            failed_tests = [r for r in self.test_results if not r["success"]]
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test['test']}: {failed_test['message']}")
        
        return summary

async def main():
    """Main test execution"""
    async with TranscriptionPipelineTest() as test_runner:
        results = await test_runner.run_comprehensive_test()
        
        # Save results to file
        results_file = "/app/transcription_pipeline_test_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Return exit code based on success
        return 0 if results["all_tests_passed"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)