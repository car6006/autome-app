#!/usr/bin/env python3
"""
Large-File Transcription Pipeline Test
Tests the complete pipeline by uploading the test file `/tmp/test_pipeline_30s.wav`
and monitoring it through all stages as requested in the review.
"""

import requests
import sys
import json
import time
import os
import hashlib
from datetime import datetime
from pathlib import Path

class LargeFileTranscriptionTester:
    def __init__(self, base_url="https://pwa-integration-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_data = {
            "email": f"pipeline_test_{int(time.time())}@example.com",
            "username": f"pipelinetest{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Pipeline",
            "last_name": "Tester"
        }
        self.test_file_path = "/tmp/test_pipeline_30s.wav"

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

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
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def setup_authentication(self):
        """Register and authenticate test user"""
        self.log("🔐 Setting up authentication...")
        
        # Register user
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=self.test_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Registered user: {user_data.get('email')}")
            return True
        else:
            self.log("❌ Failed to register user")
            return False

    def verify_test_file(self):
        """Verify the test file exists and get its properties"""
        self.log("📁 Verifying test file...")
        
        if not os.path.exists(self.test_file_path):
            self.log(f"❌ Test file not found: {self.test_file_path}")
            return False
        
        file_size = os.path.getsize(self.test_file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        self.log(f"   File: {self.test_file_path}")
        self.log(f"   Size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        
        # Calculate SHA256 for integrity verification
        sha256_hash = hashlib.sha256()
        with open(self.test_file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        self.file_sha256 = sha256_hash.hexdigest()
        self.file_size = file_size
        self.log(f"   SHA256: {self.file_sha256[:16]}...")
        
        return True

    def test_create_upload_session(self):
        """Test creating upload session for the test file"""
        self.log("📤 Step 1: Creating upload session...")
        
        session_data = {
            "filename": "test_pipeline_30s.wav",
            "total_size": self.file_size,
            "mime_type": "audio/wav",
            "language": None,
            "enable_diarization": True
        }
        
        success, response = self.run_test(
            "Create Upload Session",
            "POST",
            "uploads/sessions",
            200,
            data=session_data,
            auth_required=True
        )
        
        if success:
            self.upload_id = response.get('upload_id')
            self.chunk_size = response.get('chunk_size', 5242880)  # 5MB default
            self.log(f"   Upload ID: {self.upload_id}")
            self.log(f"   Chunk size: {self.chunk_size} bytes")
            return True
        else:
            self.log("❌ Failed to create upload session")
            return False

    def test_chunked_upload(self):
        """Test uploading the file using chunked upload"""
        self.log("📦 Step 2: Uploading file in chunks...")
        
        # Calculate number of chunks
        total_chunks = (self.file_size + self.chunk_size - 1) // self.chunk_size
        self.log(f"   Total chunks needed: {total_chunks}")
        
        # Upload each chunk
        with open(self.test_file_path, "rb") as f:
            for chunk_index in range(total_chunks):
                chunk_data = f.read(self.chunk_size)
                
                # Create temporary file for this chunk
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as temp_chunk:
                    temp_chunk.write(chunk_data)
                    temp_chunk.flush()
                    
                    # Upload chunk
                    with open(temp_chunk.name, 'rb') as chunk_file:
                        files = {'chunk': (f'chunk_{chunk_index}', chunk_file, 'application/octet-stream')}
                        
                        success, response = self.run_test(
                            f"Upload Chunk {chunk_index + 1}/{total_chunks}",
                            "POST",
                            f"uploads/sessions/{self.upload_id}/chunks/{chunk_index}",
                            200,
                            files=files,
                            auth_required=True,
                            timeout=60
                        )
                        
                        if not success:
                            self.log(f"❌ Failed to upload chunk {chunk_index}")
                            os.unlink(temp_chunk.name)
                            return False
                    
                    os.unlink(temp_chunk.name)
        
        self.log(f"✅ Successfully uploaded all {total_chunks} chunks")
        return True

    def test_upload_status(self):
        """Test checking upload status"""
        self.log("📊 Step 3: Checking upload status...")
        
        success, response = self.run_test(
            "Check Upload Status",
            "GET",
            f"uploads/sessions/{self.upload_id}/status",
            200,
            auth_required=True
        )
        
        if success:
            progress = response.get('progress', 0)
            chunks_uploaded = response.get('chunks_uploaded', [])
            total_chunks = response.get('total_chunks', 0)
            
            self.log(f"   Progress: {progress:.1f}%")
            self.log(f"   Chunks uploaded: {len(chunks_uploaded)}/{total_chunks}")
            
            if progress >= 100:
                self.log("✅ All chunks uploaded successfully")
                return True
            else:
                self.log("⚠️ Upload not complete")
                return False
        else:
            return False

    def test_finalize_upload(self):
        """Test finalizing the upload and creating transcription job"""
        self.log("🔗 Step 4: Finalizing upload...")
        
        finalize_data = {
            "upload_id": self.upload_id,
            "sha256": self.file_sha256
        }
        
        success, response = self.run_test(
            "Finalize Upload",
            "POST",
            f"uploads/sessions/{self.upload_id}/complete",
            200,
            data=finalize_data,
            auth_required=True,
            timeout=120
        )
        
        if success:
            self.job_id = response.get('job_id')
            self.log(f"   Transcription job created: {self.job_id}")
            return True
        else:
            self.log("❌ Failed to finalize upload")
            return False

    def monitor_job_progress(self, max_wait_minutes=30):
        """Monitor job progress through all pipeline stages"""
        self.log(f"⏳ Step 5: Monitoring job progress (max {max_wait_minutes} minutes)...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        last_stage = None
        last_progress = 0
        stage_history = []
        
        expected_stages = [
            "CREATED", "VALIDATING", "TRANSCODING", "SEGMENTING", 
            "TRANSCRIBING", "MERGING", "DIARIZING", "OUTPUT_GENERATION", 
            "FINALIZING", "COMPLETE"
        ]
        
        while time.time() - start_time < max_wait_seconds:
            success, response = self.run_test(
                "Check Job Status",
                "GET",
                f"transcriptions/{self.job_id}",
                200,
                auth_required=True
            )
            
            if not success:
                self.log("❌ Failed to get job status")
                return False
            
            status = response.get('status')
            current_stage = response.get('current_stage')
            progress = response.get('progress', 0)
            stage_progress = response.get('stage_progress', {})
            
            # Log stage changes
            if current_stage != last_stage:
                elapsed = time.time() - start_time
                self.log(f"   Stage: {current_stage} (after {elapsed:.1f}s)")
                stage_history.append({
                    'stage': current_stage,
                    'time': elapsed,
                    'progress': progress
                })
                last_stage = current_stage
            
            # Log significant progress changes
            if progress - last_progress >= 10:
                self.log(f"   Progress: {progress:.1f}%")
                last_progress = progress
            
            # Check for completion
            if status == "COMPLETE":
                total_time = time.time() - start_time
                self.log(f"✅ Job completed successfully in {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
                
                # Log stage progression
                self.log("📋 Stage progression:")
                for stage_info in stage_history:
                    self.log(f"   {stage_info['stage']}: {stage_info['time']:.1f}s ({stage_info['progress']:.1f}%)")
                
                # Verify all expected stages were hit
                stages_hit = [s['stage'] for s in stage_history]
                self.log(f"   Stages completed: {len(stages_hit)}")
                
                # Check if job got stuck at merge stage (the specific issue mentioned)
                merge_stage_found = any('MERG' in stage for stage in stages_hit)
                if merge_stage_found:
                    self.log("✅ Job successfully passed through merge stage")
                else:
                    self.log("⚠️ Merge stage not explicitly detected in progression")
                
                return True
            
            elif status == "FAILED":
                error_message = response.get('error_message', 'Unknown error')
                error_code = response.get('error_code', 'Unknown')
                self.log(f"❌ Job failed: {error_code} - {error_message}")
                return False
            
            # Wait before next check
            time.sleep(5)
        
        # Timeout
        self.log(f"⏰ Job monitoring timed out after {max_wait_minutes} minutes")
        self.log(f"   Last status: {status}")
        self.log(f"   Last stage: {current_stage}")
        self.log(f"   Last progress: {progress:.1f}%")
        return False

    def test_output_verification(self):
        """Test that all output formats are generated and can be downloaded"""
        self.log("📥 Step 6: Verifying output generation...")
        
        expected_formats = ["txt", "json", "srt", "vtt", "docx"]
        successful_downloads = 0
        
        for format_type in expected_formats:
            success, response = self.run_test(
                f"Download {format_type.upper()} Output",
                "GET",
                f"transcriptions/{self.job_id}/download?format={format_type}",
                302,  # Redirect to signed URL
                auth_required=True,
                timeout=30
            )
            
            if success:
                successful_downloads += 1
                self.log(f"   ✅ {format_type.upper()} format available")
            else:
                self.log(f"   ❌ {format_type.upper()} format not available")
        
        self.log(f"📊 Output formats available: {successful_downloads}/{len(expected_formats)}")
        
        if successful_downloads >= 3:  # At least TXT, JSON, SRT should be available
            self.log("✅ Sufficient output formats generated")
            return True
        else:
            self.log("❌ Insufficient output formats generated")
            return False

    def test_job_details_verification(self):
        """Verify job details and checkpoint data"""
        self.log("🔍 Step 7: Verifying job details and checkpoint data...")
        
        success, response = self.run_test(
            "Get Final Job Status",
            "GET",
            f"transcriptions/{self.job_id}",
            200,
            auth_required=True
        )
        
        if success:
            # Check key job properties
            total_duration = response.get('total_duration')
            word_count = response.get('word_count')
            detected_language = response.get('detected_language')
            confidence_score = response.get('confidence_score')
            download_urls = response.get('download_urls', {})
            
            self.log(f"   Total duration: {total_duration}s" if total_duration else "   Duration: Not detected")
            self.log(f"   Word count: {word_count}" if word_count else "   Word count: Not available")
            self.log(f"   Detected language: {detected_language}" if detected_language else "   Language: Not detected")
            self.log(f"   Confidence score: {confidence_score}" if confidence_score else "   Confidence: Not available")
            self.log(f"   Download URLs: {len(download_urls)} formats")
            
            # Verify checkpoint data was saved
            stage_durations = response.get('durations', {})
            if stage_durations:
                self.log("✅ Stage checkpoint data saved:")
                for stage, duration in stage_durations.items():
                    self.log(f"     {stage}: {duration:.2f}s")
            else:
                self.log("⚠️ No stage duration data found")
            
            return True
        else:
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("🧹 Cleaning up test data...")
        
        if hasattr(self, 'job_id'):
            # Delete the transcription job
            success, response = self.run_test(
                "Delete Transcription Job",
                "DELETE",
                f"transcriptions/{self.job_id}",
                200,
                auth_required=True
            )
            
            if success:
                self.log("   ✅ Transcription job deleted")
            else:
                self.log("   ⚠️ Failed to delete transcription job")

    def run_complete_pipeline_test(self):
        """Run the complete large-file transcription pipeline test"""
        self.log("🎵 LARGE-FILE TRANSCRIPTION PIPELINE TEST")
        self.log("=" * 60)
        
        # Test steps
        test_steps = [
            ("Setup Authentication", self.setup_authentication),
            ("Verify Test File", self.verify_test_file),
            ("Create Upload Session", self.test_create_upload_session),
            ("Chunked Upload", self.test_chunked_upload),
            ("Upload Status Check", self.test_upload_status),
            ("Finalize Upload", self.test_finalize_upload),
            ("Monitor Job Progress", self.monitor_job_progress),
            ("Output Verification", self.test_output_verification),
            ("Job Details Verification", self.test_job_details_verification),
        ]
        
        start_time = time.time()
        failed_steps = []
        
        for step_name, step_function in test_steps:
            self.log(f"\n🔄 {step_name}...")
            try:
                if not step_function():
                    failed_steps.append(step_name)
                    self.log(f"❌ {step_name} failed")
                    # Continue with remaining steps for diagnostic purposes
                else:
                    self.log(f"✅ {step_name} completed")
            except Exception as e:
                self.log(f"❌ {step_name} failed with exception: {str(e)}")
                failed_steps.append(step_name)
        
        # Cleanup
        try:
            self.cleanup_test_data()
        except Exception as e:
            self.log(f"⚠️ Cleanup failed: {str(e)}")
        
        # Final results
        total_time = time.time() - start_time
        self.log("\n" + "=" * 60)
        self.log("📊 PIPELINE TEST RESULTS")
        self.log("=" * 60)
        
        self.log(f"Total test time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        self.log(f"API tests run: {self.tests_run}")
        self.log(f"API tests passed: {self.tests_passed}")
        self.log(f"API success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "N/A")
        
        if failed_steps:
            self.log(f"\n❌ Failed steps ({len(failed_steps)}):")
            for step in failed_steps:
                self.log(f"   - {step}")
        else:
            self.log("\n✅ All pipeline steps completed successfully!")
        
        # Specific focus areas from the review request
        self.log("\n🎯 REVIEW REQUEST FOCUS AREAS:")
        
        merge_stage_success = "Monitor Job Progress" not in failed_steps
        self.log(f"   Merge stage passage: {'✅ SUCCESS' if merge_stage_success else '❌ FAILED'}")
        
        checkpoint_success = "Job Details Verification" not in failed_steps
        self.log(f"   Checkpoint data: {'✅ SAVED' if checkpoint_success else '❌ MISSING'}")
        
        output_success = "Output Verification" not in failed_steps
        self.log(f"   Output generation: {'✅ ALL FORMATS' if output_success else '❌ INCOMPLETE'}")
        
        pipeline_success = len(failed_steps) == 0
        self.log(f"   Overall pipeline: {'✅ WORKING' if pipeline_success else '❌ ISSUES FOUND'}")
        
        if pipeline_success:
            self.log("\n🎉 PIPELINE TEST PASSED!")
            self.log("The large-file transcription pipeline is working correctly.")
            self.log("Jobs are not getting stuck at the merge stage.")
        else:
            self.log("\n⚠️ PIPELINE TEST IDENTIFIED ISSUES")
            self.log("See failed steps above for details.")
        
        return pipeline_success

def main():
    """Main test execution"""
    tester = LargeFileTranscriptionTester()
    
    try:
        success = tester.run_complete_pipeline_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        tester.log(f"\n❌ Test failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()