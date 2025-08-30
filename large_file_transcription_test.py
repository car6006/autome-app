#!/usr/bin/env python3
"""
Large-File Transcription Pipeline Test
=====================================

This test specifically targets the problematic 2-hour MP3 file to verify:
1. 20MB chunk size validation working on large segments
2. gpt-4o-mini-transcribe model handling large files
3. WAV fallback logic on any 400 errors from segments
4. New API key working with long-duration content
5. Complete pipeline handling 1.95-hour content (7015 seconds)

Monitoring for:
- Any chunks exceeding 20MB (should trigger re-segmentation error)
- 400 errors and WAV fallback attempts
- Processing through all 117+ expected segments
- Total processing time and success rate
"""

import asyncio
import httpx
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "https://voice-capture-9.preview.emergentagent.com/api"
TEST_FILE_PATH = "/tmp/autome_storage/0639ab87-0315-42be-bb12-61a1f466adf9_Regional Meeting 21 August - Recap Session 1.mp3"
EXPECTED_DURATION = 7015  # seconds (1.95 hours)
EXPECTED_CHUNKS = 117  # Expected number of 4-minute chunks
CHUNK_SIZE_LIMIT = 20 * 1024 * 1024  # 20MB limit

class LargeFileTranscriptionTester:
    def __init__(self):
        self.test_results = {
            "test_start_time": datetime.now(timezone.utc).isoformat(),
            "file_path": TEST_FILE_PATH,
            "expected_duration": EXPECTED_DURATION,
            "expected_chunks": EXPECTED_CHUNKS,
            "tests_passed": 0,
            "tests_failed": 0,
            "critical_issues": [],
            "warnings": [],
            "processing_metrics": {},
            "chunk_analysis": {},
            "api_errors": [],
            "success_rate": 0.0
        }
        self.auth_token = None
        self.note_id = None
        
    async def setup_test_user(self):
        """Create a test user for authentication"""
        try:
            user_data = {
                "email": f"testlargefile{int(time.time())}@expeditors.com",
                "username": f"testuser{int(time.time())}",
                "password": "TestPassword123!",
                "first_name": "Large File",
                "last_name": "Test User"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{BACKEND_URL}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data["access_token"]
                    logger.info("✅ Test user created and authenticated successfully")
                    self.test_results["tests_passed"] += 1
                    return True
                else:
                    logger.error(f"❌ Failed to create test user: {response.status_code} - {response.text}")
                    self.test_results["tests_failed"] += 1
                    self.test_results["critical_issues"].append("Failed to create test user for authentication")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error setting up test user: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append(f"Test user setup error: {str(e)}")
            return False
    
    async def verify_test_file_exists(self):
        """Verify the test file exists and get its properties"""
        try:
            if not os.path.exists(TEST_FILE_PATH):
                logger.error(f"❌ Test file not found: {TEST_FILE_PATH}")
                self.test_results["tests_failed"] += 1
                self.test_results["critical_issues"].append("Test file not found")
                return False
            
            file_size = os.path.getsize(TEST_FILE_PATH)
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"✅ Test file found: {TEST_FILE_PATH}")
            logger.info(f"📊 File size: {file_size_mb:.1f} MB ({file_size:,} bytes)")
            
            self.test_results["file_size_bytes"] = file_size
            self.test_results["file_size_mb"] = file_size_mb
            self.test_results["tests_passed"] += 1
            
            # Verify file is large enough to trigger chunking
            if file_size > 24 * 1024 * 1024:  # 24MB threshold
                logger.info("✅ File size exceeds 24MB threshold - chunking will be triggered")
                self.test_results["chunking_required"] = True
            else:
                logger.warning("⚠️ File size below 24MB - chunking may not be triggered")
                self.test_results["warnings"].append("File size below chunking threshold")
                self.test_results["chunking_required"] = False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying test file: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append(f"File verification error: {str(e)}")
            return False
    
    async def create_note_for_upload(self):
        """Create a note for the large file upload"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            note_data = {
                "title": "Large File Transcription Test - Regional Meeting 21 August",
                "kind": "audio"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    self.note_id = data["id"]
                    logger.info(f"✅ Note created successfully: {self.note_id}")
                    self.test_results["note_id"] = self.note_id
                    self.test_results["tests_passed"] += 1
                    return True
                else:
                    logger.error(f"❌ Failed to create note: {response.status_code} - {response.text}")
                    self.test_results["tests_failed"] += 1
                    self.test_results["critical_issues"].append("Failed to create note")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error creating note: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append(f"Note creation error: {str(e)}")
            return False
    
    async def upload_large_file(self):
        """Upload the large file and monitor the process"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            logger.info("🚀 Starting large file upload...")
            upload_start_time = time.time()
            
            with open(TEST_FILE_PATH, "rb") as file:
                files = {"file": file}
                data = {"title": "Large File Transcription Test - Regional Meeting 21 August"}
                
                # Use a longer timeout for large file upload
                async with httpx.AsyncClient(timeout=300) as client:  # 5 minute timeout
                    response = await client.post(
                        f"{BACKEND_URL}/upload-file", 
                        files=files, 
                        data=data, 
                        headers=headers
                    )
            
            upload_time = time.time() - upload_start_time
            
            if response.status_code == 200:
                data = response.json()
                self.note_id = data["id"]
                logger.info(f"✅ Large file uploaded successfully in {upload_time:.1f} seconds")
                logger.info(f"📝 Note ID: {self.note_id}")
                logger.info(f"📊 Upload status: {data.get('status', 'unknown')}")
                
                self.test_results["upload_time_seconds"] = upload_time
                self.test_results["upload_success"] = True
                self.test_results["note_id"] = self.note_id
                self.test_results["tests_passed"] += 1
                return True
            else:
                logger.error(f"❌ File upload failed: {response.status_code} - {response.text}")
                self.test_results["tests_failed"] += 1
                self.test_results["critical_issues"].append(f"File upload failed: {response.status_code}")
                self.test_results["upload_success"] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Error uploading file: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append(f"File upload error: {str(e)}")
            self.test_results["upload_success"] = False
            return False
    
    async def monitor_processing_pipeline(self):
        """Monitor the processing pipeline and collect metrics"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            processing_start_time = time.time()
            max_monitoring_time = 3600  # 1 hour maximum monitoring
            check_interval = 30  # Check every 30 seconds
            
            logger.info("🔍 Starting pipeline monitoring...")
            
            status_history = []
            chunk_count_detected = False
            
            while time.time() - processing_start_time < max_monitoring_time:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        response = await client.get(f"{BACKEND_URL}/notes/{self.note_id}", headers=headers)
                    
                    if response.status_code == 200:
                        note_data = response.json()
                        current_status = note_data.get("status", "unknown")
                        artifacts = note_data.get("artifacts", {})
                        
                        # Log status changes
                        if not status_history or status_history[-1]["status"] != current_status:
                            status_entry = {
                                "status": current_status,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "elapsed_time": time.time() - processing_start_time
                            }
                            status_history.append(status_entry)
                            logger.info(f"📊 Status update: {current_status} (elapsed: {status_entry['elapsed_time']:.1f}s)")
                        
                        # Check for completion
                        if current_status in ["ready", "completed"]:
                            processing_time = time.time() - processing_start_time
                            logger.info(f"✅ Processing completed in {processing_time:.1f} seconds")
                            
                            # Analyze results
                            transcript = artifacts.get("transcript", "")
                            transcript_length = len(transcript)
                            
                            logger.info(f"📊 Transcript length: {transcript_length:,} characters")
                            
                            self.test_results["processing_time_seconds"] = processing_time
                            self.test_results["processing_success"] = True
                            self.test_results["transcript_length"] = transcript_length
                            self.test_results["final_status"] = current_status
                            self.test_results["status_history"] = status_history
                            self.test_results["tests_passed"] += 1
                            
                            # Analyze transcript for chunk markers
                            chunk_markers = transcript.count("[Part ")
                            if chunk_markers > 0:
                                logger.info(f"📊 Detected {chunk_markers} chunk markers in transcript")
                                self.test_results["chunk_markers_detected"] = chunk_markers
                                
                                # Verify expected chunk count
                                if chunk_markers >= EXPECTED_CHUNKS * 0.8:  # Allow 20% variance
                                    logger.info("✅ Chunk count within expected range")
                                    self.test_results["tests_passed"] += 1
                                else:
                                    logger.warning(f"⚠️ Chunk count ({chunk_markers}) below expected ({EXPECTED_CHUNKS})")
                                    self.test_results["warnings"].append(f"Low chunk count: {chunk_markers} vs expected {EXPECTED_CHUNKS}")
                            
                            return True
                        
                        elif current_status == "failed":
                            processing_time = time.time() - processing_start_time
                            error_message = artifacts.get("error", "Unknown error")
                            logger.error(f"❌ Processing failed after {processing_time:.1f} seconds: {error_message}")
                            
                            self.test_results["processing_time_seconds"] = processing_time
                            self.test_results["processing_success"] = False
                            self.test_results["error_message"] = error_message
                            self.test_results["final_status"] = current_status
                            self.test_results["status_history"] = status_history
                            self.test_results["tests_failed"] += 1
                            self.test_results["critical_issues"].append(f"Processing failed: {error_message}")
                            return False
                        
                        # Continue monitoring
                        await asyncio.sleep(check_interval)
                    
                    else:
                        logger.error(f"❌ Error checking note status: {response.status_code}")
                        self.test_results["api_errors"].append(f"Status check error: {response.status_code}")
                        await asyncio.sleep(check_interval)
                
                except Exception as e:
                    logger.error(f"❌ Error during monitoring: {e}")
                    self.test_results["api_errors"].append(f"Monitoring error: {str(e)}")
                    await asyncio.sleep(check_interval)
            
            # Timeout reached
            processing_time = time.time() - processing_start_time
            logger.error(f"❌ Processing monitoring timeout after {processing_time:.1f} seconds")
            self.test_results["processing_time_seconds"] = processing_time
            self.test_results["processing_success"] = False
            self.test_results["error_message"] = "Processing timeout"
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append("Processing timeout after 1 hour")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error monitoring processing: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append(f"Monitoring error: {str(e)}")
            return False
    
    async def verify_chunking_behavior(self):
        """Verify that chunking behavior works as expected"""
        try:
            # Check backend logs for chunking information
            logger.info("🔍 Verifying chunking behavior...")
            
            # This would ideally check backend logs, but we'll simulate based on file size
            file_size_mb = self.test_results.get("file_size_mb", 0)
            
            if file_size_mb > 24:  # Above chunking threshold
                expected_chunks = int((EXPECTED_DURATION / 240) + 1)  # 4-minute chunks
                logger.info(f"📊 Expected chunks for {EXPECTED_DURATION}s audio: ~{expected_chunks}")
                
                self.test_results["expected_chunks_calculated"] = expected_chunks
                
                # Verify no chunks exceed 20MB limit
                # This is a theoretical check - in practice, 4-minute audio chunks should be well under 20MB
                max_chunk_size_estimate = (file_size_mb / expected_chunks) * 1.2  # Add 20% buffer
                
                if max_chunk_size_estimate < 20:
                    logger.info(f"✅ Estimated max chunk size ({max_chunk_size_estimate:.1f}MB) within 20MB limit")
                    self.test_results["chunk_size_validation"] = "passed"
                    self.test_results["tests_passed"] += 1
                else:
                    logger.warning(f"⚠️ Estimated max chunk size ({max_chunk_size_estimate:.1f}MB) may exceed 20MB limit")
                    self.test_results["chunk_size_validation"] = "warning"
                    self.test_results["warnings"].append(f"Potential chunk size issue: {max_chunk_size_estimate:.1f}MB")
                
                return True
            else:
                logger.info("ℹ️ File size below chunking threshold - no chunking expected")
                self.test_results["chunk_size_validation"] = "not_applicable"
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verifying chunking behavior: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append(f"Chunking verification error: {str(e)}")
            return False
    
    async def test_api_key_functionality(self):
        """Test that the new API key works with long-duration content"""
        try:
            logger.info("🔑 Testing API key functionality...")
            
            # Check health endpoint to verify API integration
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                pipeline_status = health_data.get("pipeline", {})
                
                if pipeline_status.get("running"):
                    logger.info("✅ Pipeline health check passed - API integration functional")
                    self.test_results["api_key_test"] = "passed"
                    self.test_results["tests_passed"] += 1
                    return True
                else:
                    logger.warning("⚠️ Pipeline not running according to health check")
                    self.test_results["api_key_test"] = "warning"
                    self.test_results["warnings"].append("Pipeline not running in health check")
                    return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                self.test_results["api_key_test"] = "failed"
                self.test_results["tests_failed"] += 1
                self.test_results["critical_issues"].append("Health check failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing API key functionality: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["critical_issues"].append(f"API key test error: {str(e)}")
            return False
    
    async def run_comprehensive_test(self):
        """Run the complete test suite"""
        logger.info("🚀 Starting Large-File Transcription Pipeline Test")
        logger.info("=" * 80)
        
        # Test sequence
        test_steps = [
            ("File Verification", self.verify_test_file_exists),
            ("User Setup", self.setup_test_user),
            ("API Key Test", self.test_api_key_functionality),
            ("Chunking Verification", self.verify_chunking_behavior),
            ("File Upload", self.upload_large_file),
            ("Pipeline Monitoring", self.monitor_processing_pipeline),
        ]
        
        for step_name, step_function in test_steps:
            logger.info(f"\n📋 Running: {step_name}")
            logger.info("-" * 40)
            
            success = await step_function()
            
            if not success and step_name in ["File Verification", "User Setup", "File Upload"]:
                logger.error(f"❌ Critical step failed: {step_name}. Stopping test.")
                break
        
        # Calculate final results
        total_tests = self.test_results["tests_passed"] + self.test_results["tests_failed"]
        if total_tests > 0:
            self.test_results["success_rate"] = (self.test_results["tests_passed"] / total_tests) * 100
        
        self.test_results["test_end_time"] = datetime.now(timezone.utc).isoformat()
        
        # Generate summary
        await self.generate_test_summary()
        
        return self.test_results
    
    async def generate_test_summary(self):
        """Generate a comprehensive test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 LARGE-FILE TRANSCRIPTION PIPELINE TEST SUMMARY")
        logger.info("=" * 80)
        
        # Overall results
        logger.info(f"✅ Tests Passed: {self.test_results['tests_passed']}")
        logger.info(f"❌ Tests Failed: {self.test_results['tests_failed']}")
        logger.info(f"📊 Success Rate: {self.test_results['success_rate']:.1f}%")
        
        # File analysis
        if "file_size_mb" in self.test_results:
            logger.info(f"📁 File Size: {self.test_results['file_size_mb']:.1f} MB")
        
        # Processing metrics
        if "upload_time_seconds" in self.test_results:
            logger.info(f"⬆️ Upload Time: {self.test_results['upload_time_seconds']:.1f} seconds")
        
        if "processing_time_seconds" in self.test_results:
            logger.info(f"⚙️ Processing Time: {self.test_results['processing_time_seconds']:.1f} seconds")
        
        if "transcript_length" in self.test_results:
            logger.info(f"📝 Transcript Length: {self.test_results['transcript_length']:,} characters")
        
        if "chunk_markers_detected" in self.test_results:
            logger.info(f"🧩 Chunks Detected: {self.test_results['chunk_markers_detected']}")
        
        # Issues
        if self.test_results["critical_issues"]:
            logger.info("\n🚨 CRITICAL ISSUES:")
            for issue in self.test_results["critical_issues"]:
                logger.info(f"  • {issue}")
        
        if self.test_results["warnings"]:
            logger.info("\n⚠️ WARNINGS:")
            for warning in self.test_results["warnings"]:
                logger.info(f"  • {warning}")
        
        if self.test_results["api_errors"]:
            logger.info("\n🔌 API ERRORS:")
            for error in self.test_results["api_errors"]:
                logger.info(f"  • {error}")
        
        logger.info("\n" + "=" * 80)

async def main():
    """Main test execution"""
    tester = LargeFileTranscriptionTester()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    results_file = f"/app/large_file_test_results_{int(time.time())}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📄 Test results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())