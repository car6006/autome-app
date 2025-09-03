#!/usr/bin/env python3
"""
Transcription Job Loading System Test Suite
Testing the transcription jobs listing endpoint to investigate "Error loading jobs" 
and "Could not fetch your transcription jobs" issues with 50% failure rate.

Focus Areas:
1. Test the transcription jobs listing endpoint `/api/transcriptions/`
2. Check authentication requirements and error responses
3. Test any existing transcription jobs and their status
4. Verify the database connectivity for transcription jobs
5. Test job creation and status endpoints
6. Check for any stuck jobs or processing issues
7. Verify the cleanup endpoint functionality
8. Test with both authenticated and unauthenticated requests
"""

import asyncio
import httpx
import json
import os
import time
import tempfile
import wave
import struct
import math
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TranscriptionTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.auth_token = None
        self.test_user_email = f"transcription_test_{int(time.time())}_{os.getpid()}@example.com"
        self.test_user_password = "TestPassword123!"
        self.created_jobs = []  # Track created jobs for cleanup
        
    async def cleanup(self):
        """Clean up HTTP client and test data"""
        # Clean up created jobs
        for job_id in self.created_jobs:
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                await self.client.delete(f"{API_BASE}/transcriptions/{job_id}", headers=headers)
            except:
                pass  # Ignore cleanup errors
        await self.client.aclose()
    
    def create_test_audio_file(self, duration_seconds=5, sample_rate=44100):
        """Create a test WAV file with sine wave"""
        frames = []
        for i in range(int(duration_seconds * sample_rate)):
            # Generate sine wave at 440 Hz (A note)
            value = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
            frames.append(struct.pack('<h', value))
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(frames))
        
        return temp_file.name
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            # Try to register first
            register_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "username": f"transcriptiontest{int(time.time())}",
                "name": "Test Transcription User"
            }
            
            print(f"Attempting to register user: {self.test_user_email}")
            response = await self.client.post(f"{API_BASE}/auth/register", json=register_data)
            
            print(f"Registration response: {response.status_code}")
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Test user registered: {self.test_user_email}")
                return True
            else:
                print(f"Registration failed: {response.status_code} - {response.text}")
                # If registration fails, try to login (user might already exist)
                print(f"Trying login...")
                login_response = await self.client.post(f"{API_BASE}/auth/login", json={
                    "email": self.test_user_email,
                    "password": self.test_user_password
                })
                
                print(f"Login response: {login_response.status_code}")
                if login_response.status_code == 200:
                    data = login_response.json()
                    self.auth_token = data.get("access_token")
                    print(f"✅ Test user logged in: {self.test_user_email}")
                    return True
                else:
                    print(f"❌ Both registration and login failed: {login_response.status_code} - {login_response.text}")
                    return False
                
        except Exception as e:
            print(f"❌ User authentication error: {str(e)}")
            return False
    
    async def test_transcriptions_endpoint_unauthenticated(self):
        """Test 1: Transcriptions endpoint without authentication"""
        print("\n🧪 Test 1: Transcriptions Endpoint - Unauthenticated Access")
        
        try:
            # Test without authentication
            response = await self.client.get(f"{API_BASE}/transcriptions/")
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 401:
                print("   ✅ Unauthenticated access properly rejected with 401")
                try:
                    error_data = response.json()
                    print(f"   📝 Error message: {error_data.get('detail', 'No detail provided')}")
                except:
                    print(f"   📝 Response text: {response.text}")
                return True
            elif response.status_code == 403:
                print("   ✅ Unauthenticated access properly rejected with 403")
                try:
                    error_data = response.json()
                    print(f"   📝 Error message: {error_data.get('detail', 'No detail provided')}")
                except:
                    print(f"   📝 Response text: {response.text}")
                return True
            else:
                print(f"   ❌ Expected 401/403 for unauthenticated access, got: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Unauthenticated test error: {str(e)}")
            return False
    
    async def test_transcriptions_endpoint_authenticated(self):
        """Test 2: Transcriptions endpoint with authentication"""
        print("\n🧪 Test 2: Transcriptions Endpoint - Authenticated Access")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(f"{API_BASE}/transcriptions/", headers=headers)
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Authenticated access successful")
                    print(f"   📊 Response structure: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
                    
                    if isinstance(data, dict):
                        jobs = data.get("jobs", [])
                        total = data.get("total", 0)
                        print(f"   📝 Jobs found: {total}")
                        print(f"   📝 Jobs list length: {len(jobs)}")
                        
                        if jobs:
                            print(f"   📝 Sample job keys: {list(jobs[0].keys()) if jobs else 'No jobs'}")
                    
                    return True
                except Exception as json_error:
                    print(f"   ❌ JSON parsing error: {json_error}")
                    print(f"   📝 Raw response: {response.text}")
                    return False
            else:
                print(f"   ❌ Authenticated access failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📝 Error details: {error_data}")
                except:
                    print(f"   📝 Response text: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authenticated test error: {str(e)}")
            return False
    
    async def test_transcriptions_endpoint_with_filters(self):
        """Test 3: Transcriptions endpoint with status filters"""
        print("\n🧪 Test 3: Transcriptions Endpoint - Status Filters")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test different status filters
            statuses = ["created", "processing", "complete", "failed", "cancelled"]
            results = {}
            
            for status in statuses:
                print(f"   🔍 Testing filter: status={status}")
                response = await self.client.get(f"{API_BASE}/transcriptions/?status={status}", headers=headers)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        job_count = data.get("total", 0) if isinstance(data, dict) else len(data)
                        results[status] = job_count
                        print(f"      ✅ Status '{status}': {job_count} jobs")
                    except:
                        results[status] = "JSON_ERROR"
                        print(f"      ❌ Status '{status}': JSON parsing error")
                else:
                    results[status] = f"HTTP_{response.status_code}"
                    print(f"      ❌ Status '{status}': HTTP {response.status_code}")
            
            # Test invalid status
            print(f"   🔍 Testing invalid status filter")
            response = await self.client.get(f"{API_BASE}/transcriptions/?status=invalid", headers=headers)
            
            if response.status_code == 422:
                print(f"      ✅ Invalid status properly rejected with 422")
            else:
                print(f"      ⚠️  Invalid status returned: {response.status_code}")
            
            print(f"   📊 Filter results summary: {results}")
            return True
                
        except Exception as e:
            print(f"❌ Filter test error: {str(e)}")
            return False
    
    async def test_database_connectivity(self):
        """Test 4: Database connectivity for transcription jobs"""
        print("\n🧪 Test 4: Database Connectivity Test")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test multiple requests to check for database connection issues
            print("   🔍 Testing database stability with multiple requests...")
            
            success_count = 0
            total_requests = 5
            response_times = []
            
            for i in range(total_requests):
                start_time = time.time()
                response = await self.client.get(f"{API_BASE}/transcriptions/", headers=headers)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"      Request {i+1}: ✅ Success ({response_time:.2f}s)")
                else:
                    print(f"      Request {i+1}: ❌ Failed {response.status_code} ({response_time:.2f}s)")
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            avg_response_time = sum(response_times) / len(response_times)
            success_rate = (success_count / total_requests) * 100
            
            print(f"   📊 Database connectivity results:")
            print(f"      Success rate: {success_rate}% ({success_count}/{total_requests})")
            print(f"      Average response time: {avg_response_time:.2f}s")
            print(f"      Response time range: {min(response_times):.2f}s - {max(response_times):.2f}s")
            
            if success_rate >= 80:
                print("   ✅ Database connectivity is stable")
                return True
            else:
                print("   ❌ Database connectivity issues detected")
                return False
                
        except Exception as e:
            print(f"❌ Database connectivity test error: {str(e)}")
            return False
    
    async def test_job_creation_and_status(self):
        """Test 5: Job creation and status tracking"""
        print("\n🧪 Test 5: Job Creation and Status Tracking")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create a test audio file
            print("   📁 Creating test audio file...")
            audio_file = self.create_test_audio_file(duration_seconds=3)
            file_size = os.path.getsize(audio_file)
            print(f"      Created audio file: {file_size} bytes")
            
            # Test 1: Old system - Upload via /api/upload-file
            print("   📤 Testing old system: /api/upload-file...")
            with open(audio_file, 'rb') as f:
                files = {
                    "file": ("test_transcription_old.wav", f, "audio/wav")
                }
                data = {
                    "title": "Old System Transcription Test"
                }
                
                response = await self.client.post(f"{API_BASE}/upload-file", 
                    headers=headers,
                    files=files,
                    data=data
                )
            
            if response.status_code == 200:
                upload_data = response.json()
                note_id = upload_data.get("id")
                print(f"      ✅ Old system upload successful: {note_id}")
            else:
                print(f"      ❌ Old system upload failed: {response.status_code}")
            
            # Test 2: New system - Large file transcription pipeline
            print("   📤 Testing new system: Large-file transcription pipeline...")
            
            # Step 1: Create upload session
            session_request = {
                "filename": "test_transcription_new.wav",
                "total_size": file_size,
                "mime_type": "audio/wav"
            }
            
            session_response = await self.client.post(f"{API_BASE}/uploads/sessions", 
                headers=headers,
                json=session_request
            )
            
            if session_response.status_code == 200:
                session_data = session_response.json()
                upload_id = session_data.get("upload_id")
                chunk_size = session_data.get("chunk_size")
                print(f"      ✅ Upload session created: {upload_id}")
                print(f"      📝 Chunk size: {chunk_size}")
                
                # Step 2: Upload file as chunks
                with open(audio_file, 'rb') as f:
                    file_content = f.read()
                
                chunks_needed = (file_size + chunk_size - 1) // chunk_size
                print(f"      📦 Uploading {chunks_needed} chunks...")
                
                for chunk_index in range(chunks_needed):
                    start = chunk_index * chunk_size
                    end = min(start + chunk_size, file_size)
                    chunk_data = file_content[start:end]
                    
                    # Create a temporary file for this chunk
                    chunk_file = tempfile.NamedTemporaryFile(delete=False)
                    chunk_file.write(chunk_data)
                    chunk_file.close()
                    
                    try:
                        with open(chunk_file.name, 'rb') as cf:
                            files = {
                                "chunk": (f"chunk_{chunk_index}", cf, "application/octet-stream")
                            }
                            
                            chunk_response = await self.client.post(
                                f"{API_BASE}/uploads/sessions/{upload_id}/chunks/{chunk_index}",
                                headers=headers,
                                files=files
                            )
                        
                        if chunk_response.status_code == 200:
                            print(f"         Chunk {chunk_index + 1}/{chunks_needed}: ✅")
                        else:
                            print(f"         Chunk {chunk_index + 1}/{chunks_needed}: ❌ {chunk_response.status_code}")
                    finally:
                        os.unlink(chunk_file.name)
                
                # Step 3: Finalize upload
                finalize_request = {
                    "upload_id": upload_id,
                    "sha256": None  # Optional
                }
                
                finalize_response = await self.client.post(
                    f"{API_BASE}/uploads/sessions/{upload_id}/complete",
                    headers=headers,
                    json=finalize_request
                )
                
                if finalize_response.status_code == 200:
                    finalize_data = finalize_response.json()
                    job_id = finalize_data.get("job_id")
                    print(f"      ✅ Upload finalized, job created: {job_id}")
                    
                    if job_id:
                        self.created_jobs.append(job_id)
                    
                    # Wait a moment for job to appear in listings
                    await asyncio.sleep(2)
                    
                    # Check if transcription jobs were created
                    print("   🔍 Checking for created transcription jobs...")
                    jobs_response = await self.client.get(f"{API_BASE}/transcriptions/", headers=headers)
                    
                    if jobs_response.status_code == 200:
                        jobs_data = jobs_response.json()
                        jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else jobs_data
                        
                        print(f"      📊 Found {len(jobs)} transcription jobs")
                        
                        if jobs:
                            # Check the most recent job
                            latest_job = jobs[0] if jobs else None
                            if latest_job:
                                found_job_id = latest_job.get("job_id")
                                status = latest_job.get("status")
                                filename = latest_job.get("filename")
                                
                                print(f"      📝 Latest job: {found_job_id}")
                                print(f"      📝 Status: {status}")
                                print(f"      📝 Filename: {filename}")
                                
                                # Test individual job status endpoint
                                print("   🔍 Testing individual job status...")
                                job_response = await self.client.get(f"{API_BASE}/transcriptions/{found_job_id}", headers=headers)
                                
                                if job_response.status_code == 200:
                                    job_details = job_response.json()
                                    print(f"      ✅ Job details retrieved successfully")
                                    print(f"      📝 Job status: {job_details.get('status')}")
                                    print(f"      📝 Progress: {job_details.get('progress', 0)}%")
                                    print(f"      📝 Current stage: {job_details.get('current_stage')}")
                                    
                                    os.unlink(audio_file)
                                    return True
                                else:
                                    print(f"      ❌ Failed to get job details: {job_response.status_code}")
                                    os.unlink(audio_file)
                                    return False
                        else:
                            print("      ⚠️  No transcription jobs found after new system upload")
                            os.unlink(audio_file)
                            return False  # This is concerning for the new system
                    else:
                        print(f"      ❌ Failed to list jobs: {jobs_response.status_code}")
                        os.unlink(audio_file)
                        return False
                else:
                    print(f"      ❌ Upload finalization failed: {finalize_response.status_code}")
                    print(f"      📝 Response: {finalize_response.text}")
                    os.unlink(audio_file)
                    return False
            else:
                print(f"      ❌ Upload session creation failed: {session_response.status_code}")
                print(f"      📝 Response: {session_response.text}")
                os.unlink(audio_file)
                return False
                
        except Exception as e:
            print(f"❌ Job creation test error: {str(e)}")
            if 'audio_file' in locals():
                try:
                    os.unlink(audio_file)
                except:
                    pass
            return False
    
    async def test_stuck_jobs_detection(self):
        """Test 6: Stuck jobs detection and cleanup"""
        print("\n🧪 Test 6: Stuck Jobs Detection and Cleanup")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # First, check for any existing stuck jobs
            print("   🔍 Checking for stuck jobs...")
            
            # Get all jobs
            response = await self.client.get(f"{API_BASE}/transcriptions/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", []) if isinstance(data, dict) else data
                
                stuck_jobs = []
                processing_jobs = []
                
                for job in jobs:
                    status = job.get("status")
                    created_at = job.get("created_at")
                    
                    if status == "processing":
                        processing_jobs.append(job)
                        
                        # Check if job has been processing for too long
                        if created_at:
                            # This is a simplified check - in real implementation, 
                            # we'd parse the timestamp and check duration
                            print(f"      📝 Processing job found: {job.get('job_id')} (created: {created_at})")
                
                print(f"   📊 Found {len(processing_jobs)} jobs in processing state")
                
                # Test cleanup endpoint
                print("   🧹 Testing cleanup endpoint...")
                cleanup_response = await self.client.post(f"{API_BASE}/transcriptions/cleanup", headers=headers)
                
                if cleanup_response.status_code == 200:
                    cleanup_data = cleanup_response.json()
                    fixed_count = cleanup_data.get("fixed_count", 0)
                    message = cleanup_data.get("message", "")
                    
                    print(f"      ✅ Cleanup endpoint working: {message}")
                    print(f"      📝 Fixed jobs count: {fixed_count}")
                    return True
                else:
                    print(f"      ❌ Cleanup endpoint failed: {cleanup_response.status_code}")
                    try:
                        error_data = cleanup_response.json()
                        print(f"      📝 Error: {error_data}")
                    except:
                        print(f"      📝 Response: {cleanup_response.text}")
                    return False
            else:
                print(f"   ❌ Failed to list jobs for stuck job detection: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Stuck jobs test error: {str(e)}")
            return False
    
    async def test_error_handling_and_edge_cases(self):
        """Test 7: Error handling and edge cases"""
        print("\n🧪 Test 7: Error Handling and Edge Cases")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: Non-existent job ID
            print("   🔍 Testing non-existent job ID...")
            fake_job_id = "non-existent-job-id-12345"
            response = await self.client.get(f"{API_BASE}/transcriptions/{fake_job_id}", headers=headers)
            
            if response.status_code == 404:
                print("      ✅ Non-existent job properly returns 404")
            else:
                print(f"      ❌ Expected 404 for non-existent job, got: {response.status_code}")
            
            # Test 2: Invalid status filter
            print("   🔍 Testing invalid status filter...")
            response = await self.client.get(f"{API_BASE}/transcriptions/?status=invalid_status", headers=headers)
            
            if response.status_code in [400, 422]:
                print("      ✅ Invalid status filter properly rejected")
            else:
                print(f"      ⚠️  Invalid status filter returned: {response.status_code}")
            
            # Test 3: Large limit parameter
            print("   🔍 Testing large limit parameter...")
            response = await self.client.get(f"{API_BASE}/transcriptions/?limit=1000", headers=headers)
            
            if response.status_code in [200, 400, 422]:
                print("      ✅ Large limit parameter handled appropriately")
            else:
                print(f"      ❌ Unexpected response for large limit: {response.status_code}")
            
            # Test 4: Malformed requests
            print("   🔍 Testing malformed requests...")
            
            # Test with invalid JSON in POST request (if applicable)
            try:
                request_headers = {**headers, "Content-Type": "application/json"}
                response = await self.client.post(f"{API_BASE}/transcriptions/cleanup", 
                    headers=request_headers,
                    content="invalid json content"
                )
                
                if response.status_code in [400, 422]:
                    print("      ✅ Malformed JSON properly rejected")
                else:
                    print(f"      ⚠️  Malformed JSON returned: {response.status_code}")
            except:
                print("      ✅ Malformed request handled by client/server")
            
            print("   📊 Error handling tests completed")
            return True
                
        except Exception as e:
            print(f"❌ Error handling test error: {str(e)}")
            return False
    
    async def test_concurrent_requests(self):
        """Test 8: Concurrent requests to detect race conditions"""
        print("\n🧪 Test 8: Concurrent Requests Test")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            print("   🔍 Testing concurrent requests to transcriptions endpoint...")
            
            # Create multiple concurrent requests
            async def make_request(request_id):
                try:
                    response = await self.client.get(f"{API_BASE}/transcriptions/", headers=headers)
                    return {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "response_time": time.time()
                    }
                except Exception as e:
                    return {
                        "request_id": request_id,
                        "status_code": None,
                        "success": False,
                        "error": str(e),
                        "response_time": time.time()
                    }
            
            # Launch 10 concurrent requests
            concurrent_count = 10
            start_time = time.time()
            
            tasks = [make_request(i) for i in range(concurrent_count)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze results
            successful_requests = sum(1 for r in results if r["success"])
            failed_requests = concurrent_count - successful_requests
            success_rate = (successful_requests / concurrent_count) * 100
            
            print(f"   📊 Concurrent requests results:")
            print(f"      Total requests: {concurrent_count}")
            print(f"      Successful: {successful_requests}")
            print(f"      Failed: {failed_requests}")
            print(f"      Success rate: {success_rate}%")
            print(f"      Total time: {total_time:.2f}s")
            print(f"      Average time per request: {total_time/concurrent_count:.2f}s")
            
            # Check for any errors
            errors = [r for r in results if not r["success"]]
            if errors:
                print(f"   ⚠️  Errors detected:")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      Request {error['request_id']}: {error.get('error', 'Unknown error')}")
            
            if success_rate >= 80:
                print("   ✅ Concurrent requests handled well")
                return True
            else:
                print("   ❌ High failure rate in concurrent requests")
                return False
                
        except Exception as e:
            print(f"❌ Concurrent requests test error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all transcription job loading tests"""
        print("🚀 Starting Transcription Job Loading System Test Suite")
        print("=" * 80)
        print("🎯 Focus: Investigating 'Error loading jobs' and 'Could not fetch your transcription jobs' issues")
        print("📊 Target: Identify root cause of 50% failure rate")
        print("=" * 80)
        
        # Register test user
        if not await self.register_test_user():
            print("❌ Cannot proceed without test user registration")
            return False
        
        test_results = []
        
        # Test 1: Unauthenticated access
        unauth_success = await self.test_transcriptions_endpoint_unauthenticated()
        test_results.append(("Unauthenticated Access Handling", unauth_success))
        
        # Test 2: Authenticated access
        auth_success = await self.test_transcriptions_endpoint_authenticated()
        test_results.append(("Authenticated Access", auth_success))
        
        # Test 3: Status filters
        filter_success = await self.test_transcriptions_endpoint_with_filters()
        test_results.append(("Status Filters", filter_success))
        
        # Test 4: Database connectivity
        db_success = await self.test_database_connectivity()
        test_results.append(("Database Connectivity", db_success))
        
        # Test 5: Job creation and status
        job_success = await self.test_job_creation_and_status()
        test_results.append(("Job Creation and Status", job_success))
        
        # Test 6: Stuck jobs detection
        stuck_success = await self.test_stuck_jobs_detection()
        test_results.append(("Stuck Jobs Detection and Cleanup", stuck_success))
        
        # Test 7: Error handling
        error_success = await self.test_error_handling_and_edge_cases()
        test_results.append(("Error Handling and Edge Cases", error_success))
        
        # Test 8: Concurrent requests
        concurrent_success = await self.test_concurrent_requests()
        test_results.append(("Concurrent Requests", concurrent_success))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TRANSCRIPTION JOB LOADING TEST RESULTS")
        print("=" * 80)
        
        passed = 0
        total = len(test_results)
        critical_failures = []
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1
            else:
                # Identify critical failures
                if test_name in ["Authenticated Access", "Database Connectivity"]:
                    critical_failures.append(test_name)
        
        success_rate = (passed / total) * 100
        print(f"\n📈 Overall Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        # Analysis and recommendations
        print("\n🔍 ANALYSIS:")
        if success_rate >= 90:
            print("✅ EXCELLENT: Transcription job loading system is working correctly")
            print("   The reported 50% failure rate may be due to:")
            print("   - Intermittent network issues")
            print("   - Frontend caching problems")
            print("   - User-specific authentication issues")
        elif success_rate >= 70:
            print("⚠️  MODERATE ISSUES: Some problems detected but core functionality works")
            if critical_failures:
                print(f"   Critical issues in: {', '.join(critical_failures)}")
        else:
            print("❌ SIGNIFICANT ISSUES: Multiple critical failures detected")
            print("   This could explain the 50% failure rate reported by users")
            if critical_failures:
                print(f"   Critical failures: {', '.join(critical_failures)}")
        
        print("\n💡 RECOMMENDATIONS:")
        if "Database Connectivity" in critical_failures:
            print("   - Check MongoDB connection stability")
            print("   - Review database connection pooling settings")
            print("   - Monitor database performance metrics")
        
        if "Authenticated Access" in critical_failures:
            print("   - Verify JWT token validation logic")
            print("   - Check authentication middleware")
            print("   - Review user session management")
        
        if success_rate < 80:
            print("   - Implement retry logic in frontend")
            print("   - Add comprehensive error logging")
            print("   - Consider circuit breaker pattern")
            print("   - Monitor API response times")
        
        return success_rate >= 70

async def main():
    """Main test execution"""
    tester = TranscriptionTester()
    
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)