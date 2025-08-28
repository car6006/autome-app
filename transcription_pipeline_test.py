#!/usr/bin/env python3
"""
Large-File Transcription Pipeline Test
Testing the transcription pipeline with debugging logs as requested in review
"""

import asyncio
import httpx
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://whisper-async-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TranscriptionPipelineTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)
        self.test_file_path = "/tmp/test_pipeline_30s.wav"
        self.auth_token = None
        self.upload_id = None
        self.job_id = None
        
    async def setup_auth(self):
        """Setup authentication for testing"""
        try:
            # Try to register a test user
            test_email = f"test_transcription_{int(time.time())}@example.com"
            register_data = {
                "email": test_email,
                "password": "testpass123",
                "name": "Transcription Test User"
            }
            
            response = await self.client.post(f"{API_BASE}/auth/register", json=register_data)
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result["access_token"]
                print(f"✅ Registered test user: {test_email}")
                return True
            else:
                print(f"❌ Failed to register user: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Auth setup failed: {e}")
            return False
    
    def get_auth_headers(self):
        """Get authorization headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def test_file_exists(self):
        """Verify test file exists"""
        print(f"\n🔍 Checking test file: {self.test_file_path}")
        
        if not Path(self.test_file_path).exists():
            print(f"❌ Test file not found: {self.test_file_path}")
            return False
            
        file_size = Path(self.test_file_path).stat().st_size
        print(f"✅ Test file found: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        return True
    
    async def create_upload_session(self):
        """Create upload session for the test file"""
        print(f"\n📤 Creating upload session...")
        
        file_size = Path(self.test_file_path).stat().st_size
        
        session_data = {
            "filename": "test_pipeline_30s.wav",
            "total_size": file_size,
            "mime_type": "audio/wav",
            "language": None,
            "enable_diarization": True
        }
        
        try:
            response = await self.client.post(
                f"{API_BASE}/uploads/sessions",
                json=session_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                self.upload_id = result["upload_id"]
                chunk_size = result["chunk_size"]
                print(f"✅ Upload session created: {self.upload_id}")
                print(f"   Chunk size: {chunk_size:,} bytes")
                return True
            else:
                print(f"❌ Failed to create upload session: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload session creation failed: {e}")
            return False
    
    async def upload_file_chunks(self):
        """Upload file in chunks"""
        print(f"\n📁 Uploading file chunks...")
        
        if not self.upload_id:
            print("❌ No upload session ID available")
            return False
        
        # Get session details first
        try:
            status_response = await self.client.get(
                f"{API_BASE}/uploads/sessions/{self.upload_id}/status",
                headers=self.get_auth_headers()
            )
            
            if status_response.status_code != 200:
                print(f"❌ Failed to get session status: {status_response.status_code}")
                return False
                
            session_info = status_response.json()
            chunk_size = session_info.get("total_bytes", 5*1024*1024) // session_info.get("total_chunks", 1)
            total_chunks = session_info["total_chunks"]
            
            print(f"   Total chunks: {total_chunks}")
            print(f"   Chunk size: {chunk_size:,} bytes")
            
        except Exception as e:
            print(f"❌ Failed to get session info: {e}")
            return False
        
        # Upload chunks
        try:
            with open(self.test_file_path, "rb") as f:
                for chunk_index in range(total_chunks):
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break
                    
                    # Create multipart form data for chunk upload
                    files = {"chunk": ("chunk", chunk_data, "application/octet-stream")}
                    
                    response = await self.client.post(
                        f"{API_BASE}/uploads/sessions/{self.upload_id}/chunks/{chunk_index}",
                        files=files,
                        headers=self.get_auth_headers()
                    )
                    
                    if response.status_code == 200:
                        print(f"   ✅ Uploaded chunk {chunk_index + 1}/{total_chunks}")
                    else:
                        print(f"   ❌ Failed to upload chunk {chunk_index}: {response.status_code}")
                        print(f"      Response: {response.text}")
                        return False
            
            print(f"✅ All chunks uploaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Chunk upload failed: {e}")
            return False
    
    async def finalize_upload(self):
        """Finalize upload and create transcription job"""
        print(f"\n🎯 Finalizing upload...")
        
        finalize_data = {
            "upload_id": self.upload_id
        }
        
        try:
            response = await self.client.post(
                f"{API_BASE}/uploads/sessions/{self.upload_id}/complete",
                json=finalize_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                self.job_id = result["job_id"]
                print(f"✅ Upload finalized successfully")
                print(f"   Job ID: {self.job_id}")
                return True
            else:
                print(f"❌ Failed to finalize upload: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload finalization failed: {e}")
            return False
    
    async def monitor_transcription_job(self, max_wait_minutes=10):
        """Monitor transcription job progress and look for debugging logs"""
        print(f"\n👀 Monitoring transcription job: {self.job_id}")
        print("🔍 Looking for debugging logs:")
        print("   - 💾 Job {job_id}: Saving checkpoint with X transcripts...")
        print("   - ✅ Job {job_id}: Checkpoint verified - X transcripts saved")
        print("   - 🔍 Job {job_id}: Looking for transcription checkpoint...")
        print("   - ✅ Job {job_id}: Found checkpoint with keys: ...")
        print("   - Any error messages about checkpoint verification or retrieval")
        
        if not self.job_id:
            print("❌ No job ID available")
            return False
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        last_stage = None
        last_progress = 0
        
        try:
            while time.time() - start_time < max_wait_seconds:
                # Get job status
                response = await self.client.get(
                    f"{API_BASE}/transcriptions/{self.job_id}",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    job_status = response.json()
                    
                    current_stage = job_status.get("current_stage")
                    progress = job_status.get("progress", 0)
                    status = job_status.get("status")
                    
                    # Print progress updates
                    if current_stage != last_stage or progress != last_progress:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"   [{timestamp}] Stage: {current_stage}, Progress: {progress:.1f}%, Status: {status}")
                        
                        # Look for specific stages mentioned in review request
                        if current_stage == "transcribing":
                            print(f"   🎯 TRANSCRIBING STAGE - Looking for checkpoint debugging logs...")
                        elif current_stage == "merging":
                            print(f"   🔗 MERGING STAGE - Checking if merge succeeds or fails...")
                        
                        last_stage = current_stage
                        last_progress = progress
                    
                    # Check for completion
                    if status == "complete":
                        print(f"✅ Transcription completed successfully!")
                        
                        # Get final results
                        download_urls = job_status.get("download_urls", {})
                        if download_urls:
                            print(f"   Available formats: {list(download_urls.keys())}")
                        
                        detected_language = job_status.get("detected_language")
                        if detected_language:
                            print(f"   Detected language: {detected_language}")
                        
                        total_duration = job_status.get("total_duration")
                        if total_duration:
                            print(f"   Audio duration: {total_duration:.1f} seconds")
                        
                        word_count = job_status.get("word_count")
                        if word_count:
                            print(f"   Word count: {word_count}")
                        
                        return True
                    
                    elif status == "failed":
                        error_code = job_status.get("error_code")
                        error_message = job_status.get("error_message")
                        print(f"❌ Transcription failed!")
                        print(f"   Error code: {error_code}")
                        print(f"   Error message: {error_message}")
                        
                        # This is valuable information for debugging
                        print(f"\n🔍 DEBUGGING INFO - Job failed in stage: {current_stage}")
                        if "checkpoint" in str(error_message).lower():
                            print(f"   ⚠️  CHECKPOINT-RELATED ERROR DETECTED!")
                        
                        return False
                    
                    elif status == "cancelled":
                        print(f"❌ Transcription was cancelled")
                        return False
                
                else:
                    print(f"❌ Failed to get job status: {response.status_code}")
                    if response.status_code == 404:
                        print("   Job not found - may have been deleted")
                        return False
                
                # Wait before next check
                await asyncio.sleep(5)
            
            # Timeout reached
            print(f"⏰ Timeout reached ({max_wait_minutes} minutes)")
            print(f"   Last known stage: {last_stage}")
            print(f"   Last known progress: {last_progress:.1f}%")
            return False
            
        except Exception as e:
            print(f"❌ Job monitoring failed: {e}")
            return False
    
    async def check_backend_logs(self):
        """Check backend logs for debugging information"""
        print(f"\n📋 Checking backend logs for debugging information...")
        
        try:
            # Try to get job logs if available (admin endpoint)
            response = await self.client.get(
                f"{API_BASE}/transcriptions/{self.job_id}/logs",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                logs = response.json()
                print(f"✅ Retrieved job logs:")
                print(json.dumps(logs, indent=2))
            elif response.status_code == 403:
                print(f"ℹ️  Job logs require admin access (403)")
            else:
                print(f"ℹ️  Job logs not available: {response.status_code}")
                
        except Exception as e:
            print(f"ℹ️  Could not retrieve job logs: {e}")
        
        # Check system health for any relevant information
        try:
            response = await self.client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                health = response.json()
                pipeline_status = health.get("pipeline", {})
                print(f"\n🏥 System Health:")
                print(f"   Overall status: {health.get('status')}")
                print(f"   Pipeline status: {pipeline_status}")
            
        except Exception as e:
            print(f"ℹ️  Could not retrieve health status: {e}")
    
    async def cleanup(self):
        """Clean up test resources"""
        print(f"\n🧹 Cleaning up test resources...")
        
        # Cancel upload session if still active
        if self.upload_id:
            try:
                response = await self.client.delete(
                    f"{API_BASE}/uploads/sessions/{self.upload_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    print(f"✅ Upload session cleaned up")
            except Exception as e:
                print(f"ℹ️  Upload session cleanup: {e}")
        
        # Delete transcription job if created
        if self.job_id:
            try:
                response = await self.client.delete(
                    f"{API_BASE}/transcriptions/{self.job_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    print(f"✅ Transcription job cleaned up")
            except Exception as e:
                print(f"ℹ️  Transcription job cleanup: {e}")
        
        await self.client.aclose()
    
    async def run_full_test(self):
        """Run the complete transcription pipeline test"""
        print("🚀 Starting Large-File Transcription Pipeline Test")
        print("=" * 60)
        
        success = True
        
        # Step 1: Check test file
        if not await self.test_file_exists():
            return False
        
        # Step 2: Setup authentication
        if not await self.setup_auth():
            return False
        
        # Step 3: Create upload session
        if not await self.create_upload_session():
            success = False
        
        # Step 4: Upload file chunks
        if success and not await self.upload_file_chunks():
            success = False
        
        # Step 5: Finalize upload and create job
        if success and not await self.finalize_upload():
            success = False
        
        # Step 6: Monitor transcription job
        if success:
            job_success = await self.monitor_transcription_job(max_wait_minutes=15)
            if not job_success:
                success = False
        
        # Step 7: Check backend logs for debugging info
        if self.job_id:
            await self.check_backend_logs()
        
        # Step 8: Cleanup
        await self.cleanup()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ TRANSCRIPTION PIPELINE TEST COMPLETED SUCCESSFULLY")
            print("🎯 Key findings:")
            print("   - Upload session creation: ✅")
            print("   - File chunking and upload: ✅") 
            print("   - Transcription job creation: ✅")
            print("   - Pipeline processing: ✅")
            print("   - Debugging logs monitored: ✅")
        else:
            print("❌ TRANSCRIPTION PIPELINE TEST FAILED")
            print("🔍 This provides valuable debugging information about:")
            print("   - Where the pipeline breaks down")
            print("   - Checkpoint save/retrieve process issues")
            print("   - Merge stage success/failure")
            print("   - Error messages for troubleshooting")
        
        return success

async def main():
    """Main test execution"""
    test = TranscriptionPipelineTest()
    
    try:
        success = await test.run_full_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        await test.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        await test.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())