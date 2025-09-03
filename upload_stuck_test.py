#!/usr/bin/env python3
"""
Upload Stuck Issue Investigation - Backend Testing
Testing upload timeout handling, session management, progress tracking, file size limits, and cleanup
"""

import asyncio
import httpx
import json
import os
import sys
import time
import io
from datetime import datetime
from PIL import Image
import tempfile

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class UploadStuckTester:
    def __init__(self):
        self.auth_token = None
        self.user_id = None
        self.test_notes = []
        self.results = []
        
    async def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    async def setup_test_user(self):
        """Create and authenticate a test user"""
        try:
            # Register test user
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            register_data = {
                "email": f"uploadtest{timestamp}@test.com",
                "username": f"uploadtest{timestamp}",
                "password": "TestPass123!",
                "first_name": "Upload",
                "last_name": "Tester"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{API_BASE}/auth/register", json=register_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    await self.log_result("User Registration", True, f"User ID: {self.user_id}")
                    return True
                else:
                    error_text = ""
                    try:
                        error_data = response.json()
                        error_text = str(error_data)
                    except:
                        error_text = response.text
                    await self.log_result("User Registration", False, f"Status: {response.status_code}, Error: {error_text}")
                    return False
                    
        except Exception as e:
            await self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    def create_test_image(self, size_mb=1, format='PNG'):
        """Create a test image of specified size"""
        # Calculate dimensions for target file size
        target_bytes = size_mb * 1024 * 1024
        # Rough estimation: PNG with RGB takes about 3 bytes per pixel
        pixels_needed = target_bytes // 3
        width = int(pixels_needed ** 0.5)
        height = width
        
        # Create image
        img = Image.new('RGB', (width, height), color='red')
        
        # Add some text to make it realistic
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), f"Test Upload Image {size_mb}MB", fill='white')
        except:
            pass  # Font not available, skip text
        
        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()
    
    def create_test_audio(self, duration_seconds=10):
        """Create a simple test audio file"""
        # Create a simple WAV file header + silence
        sample_rate = 44100
        samples = duration_seconds * sample_rate
        
        # WAV header (44 bytes)
        wav_header = b'RIFF'
        wav_header += (36 + samples * 2).to_bytes(4, 'little')  # File size
        wav_header += b'WAVE'
        wav_header += b'fmt '
        wav_header += (16).to_bytes(4, 'little')  # Subchunk1Size
        wav_header += (1).to_bytes(2, 'little')   # AudioFormat (PCM)
        wav_header += (1).to_bytes(2, 'little')   # NumChannels (mono)
        wav_header += sample_rate.to_bytes(4, 'little')  # SampleRate
        wav_header += (sample_rate * 2).to_bytes(4, 'little')  # ByteRate
        wav_header += (2).to_bytes(2, 'little')   # BlockAlign
        wav_header += (16).to_bytes(2, 'little')  # BitsPerSample
        wav_header += b'data'
        wav_header += (samples * 2).to_bytes(4, 'little')  # Subchunk2Size
        
        # Add silence (zeros)
        audio_data = wav_header + b'\x00' * (samples * 2)
        return audio_data
    
    async def test_small_file_upload_success(self):
        """Test that small files upload successfully without getting stuck"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create small test image (100KB)
            image_data = self.create_test_image(size_mb=0.1)
            
            # Create note first
            note_data = {
                "title": "Small File Upload Test",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Create note
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Small File Upload - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                
                # Upload file
                files = {"file": ("test_small.png", image_data, "image/png")}
                start_time = time.time()
                
                response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                           files=files, headers=headers)
                
                upload_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Wait for processing to complete
                    max_wait = 30  # 30 seconds max
                    wait_time = 0
                    final_status = None
                    
                    while wait_time < max_wait:
                        await asyncio.sleep(2)
                        wait_time += 2
                        
                        # Check note status
                        status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                        if status_response.status_code == 200:
                            note_data = status_response.json()
                            status = note_data.get("status", "unknown")
                            final_status = status
                            
                            if status in ["ready", "failed"]:
                                break
                    
                    success = final_status == "ready"
                    details = f"Upload time: {upload_time:.2f}s, Processing time: {wait_time}s, Final status: {final_status}"
                    await self.log_result("Small File Upload Success", success, details)
                    
                    # Store for cleanup
                    self.test_notes.append(note_id)
                    return success
                else:
                    await self.log_result("Small File Upload Success", False, f"Upload failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Small File Upload Success", False, f"Error: {str(e)}")
            return False
    
    async def test_large_file_size_limits(self):
        """Test file size limits and behavior with large files"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test with 25MB file (should exceed typical limits)
            large_image_data = self.create_test_image(size_mb=25)
            
            # Create note first
            note_data = {
                "title": "Large File Size Limit Test",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                # Create note
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Large File Size Limit - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                
                # Try to upload large file
                files = {"file": ("test_large.png", large_image_data, "image/png")}
                start_time = time.time()
                
                try:
                    response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                               files=files, headers=headers)
                    
                    upload_time = time.time() - start_time
                    
                    # Check if it was rejected appropriately or processed
                    if response.status_code == 413:  # Payload too large
                        await self.log_result("Large File Size Limit", True, f"Properly rejected large file (413), Upload time: {upload_time:.2f}s")
                        return True
                    elif response.status_code == 400:  # Bad request (size validation)
                        response_text = response.text
                        if "size" in response_text.lower() or "large" in response_text.lower():
                            await self.log_result("Large File Size Limit", True, f"Properly rejected large file (400), Upload time: {upload_time:.2f}s")
                            return True
                    elif response.status_code == 200:
                        # File was accepted - check if it gets stuck in processing
                        max_wait = 60  # 1 minute max
                        wait_time = 0
                        final_status = None
                        
                        while wait_time < max_wait:
                            await asyncio.sleep(5)
                            wait_time += 5
                            
                            # Check note status
                            status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                            if status_response.status_code == 200:
                                note_data = status_response.json()
                                status = note_data.get("status", "unknown")
                                final_status = status
                                
                                if status in ["ready", "failed"]:
                                    break
                        
                        if final_status == "processing":
                            await self.log_result("Large File Size Limit", False, f"File stuck in processing after {wait_time}s - this is the bug!")
                            return False
                        else:
                            await self.log_result("Large File Size Limit", True, f"Large file processed successfully: {final_status}")
                            return True
                    else:
                        await self.log_result("Large File Size Limit", False, f"Unexpected response: {response.status_code}")
                        return False
                        
                except httpx.TimeoutException:
                    await self.log_result("Large File Size Limit", False, "Upload timed out - potential stuck upload issue")
                    return False
                    
        except Exception as e:
            await self.log_result("Large File Size Limit", False, f"Error: {str(e)}")
            return False
    
    async def test_upload_timeout_handling(self):
        """Test upload timeout scenarios"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create medium-sized file
            medium_image_data = self.create_test_image(size_mb=5)
            
            # Create note first
            note_data = {
                "title": "Upload Timeout Test",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:  # Short timeout to test timeout handling
                # Create note
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Upload Timeout - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                
                # Try to upload with short timeout
                files = {"file": ("test_timeout.png", medium_image_data, "image/png")}
                
                try:
                    response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                               files=files, headers=headers)
                    
                    # If it succeeds despite short timeout, that's also good
                    if response.status_code == 200:
                        await self.log_result("Upload Timeout Handling", True, "Upload completed within timeout")
                        return True
                    else:
                        await self.log_result("Upload Timeout Handling", False, f"Upload failed: {response.status_code}")
                        return False
                        
                except httpx.TimeoutException:
                    # Now check if the note is stuck in uploading state
                    async with httpx.AsyncClient(timeout=30) as check_client:
                        await asyncio.sleep(2)  # Give it a moment
                        
                        status_response = await check_client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                        if status_response.status_code == 200:
                            note_data = status_response.json()
                            status = note_data.get("status", "unknown")
                            
                            if status == "uploading":
                                await self.log_result("Upload Timeout Handling", False, "Note stuck in 'uploading' state after timeout - this is the bug!")
                                return False
                            else:
                                await self.log_result("Upload Timeout Handling", True, f"Note properly handled timeout, status: {status}")
                                return True
                        else:
                            await self.log_result("Upload Timeout Handling", False, "Could not check note status after timeout")
                            return False
                    
        except Exception as e:
            await self.log_result("Upload Timeout Handling", False, f"Error: {str(e)}")
            return False
    
    async def test_upload_progress_tracking(self):
        """Test upload progress tracking mechanisms"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create note first
            note_data = {
                "title": "Upload Progress Tracking Test",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Create note
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Upload Progress - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                initial_status = note_info.get("status", "unknown")
                
                # Check initial status
                if initial_status != "created":
                    await self.log_result("Upload Progress Tracking", False, f"Unexpected initial status: {initial_status}")
                    return False
                
                # Create test image
                image_data = self.create_test_image(size_mb=2)
                files = {"file": ("test_progress.png", image_data, "image/png")}
                
                # Upload file
                response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                           files=files, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Upload Progress Tracking", False, f"Upload failed: {response.status_code}")
                    return False
                
                # Track status changes
                status_changes = []
                max_wait = 30
                wait_time = 0
                
                while wait_time < max_wait:
                    await asyncio.sleep(1)
                    wait_time += 1
                    
                    # Check note status
                    status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                    if status_response.status_code == 200:
                        note_data = status_response.json()
                        status = note_data.get("status", "unknown")
                        
                        if not status_changes or status_changes[-1] != status:
                            status_changes.append(status)
                        
                        if status in ["ready", "failed"]:
                            break
                
                # Analyze status progression
                expected_progression = ["processing", "ready"]  # or ["processing", "failed"]
                
                has_processing = "processing" in status_changes
                ends_properly = status_changes[-1] in ["ready", "failed"] if status_changes else False
                no_stuck_uploading = "uploading" not in status_changes  # Should not get stuck in uploading
                
                success = has_processing and ends_properly and no_stuck_uploading
                details = f"Status progression: {' -> '.join(status_changes)}, Processing time: {wait_time}s"
                
                await self.log_result("Upload Progress Tracking", success, details)
                return success
                
        except Exception as e:
            await self.log_result("Upload Progress Tracking", False, f"Error: {str(e)}")
            return False
    
    async def test_upload_session_management(self):
        """Test upload session management and expiration"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test multiple concurrent uploads to check session handling
            upload_tasks = []
            note_ids = []
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Create multiple notes
                for i in range(3):
                    note_data = {
                        "title": f"Session Test Note {i+1}",
                        "kind": "photo"
                    }
                    
                    response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                    if response.status_code == 200:
                        note_info = response.json()
                        note_ids.append(note_info["id"])
                
                if len(note_ids) < 3:
                    await self.log_result("Upload Session Management", False, "Could not create test notes")
                    return False
                
                # Start concurrent uploads
                async def upload_file(note_id, file_num):
                    try:
                        image_data = self.create_test_image(size_mb=1)
                        files = {"file": (f"test_session_{file_num}.png", image_data, "image/png")}
                        
                        response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                                   files=files, headers=headers)
                        return response.status_code == 200
                    except Exception:
                        return False
                
                # Execute concurrent uploads
                results = await asyncio.gather(
                    upload_file(note_ids[0], 1),
                    upload_file(note_ids[1], 2),
                    upload_file(note_ids[2], 3),
                    return_exceptions=True
                )
                
                successful_uploads = sum(1 for r in results if r is True)
                
                # Check final status of all notes
                final_statuses = []
                await asyncio.sleep(10)  # Wait for processing
                
                for note_id in note_ids:
                    status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                    if status_response.status_code == 200:
                        note_data = status_response.json()
                        status = note_data.get("status", "unknown")
                        final_statuses.append(status)
                
                # Check for stuck uploads
                stuck_uploads = sum(1 for status in final_statuses if status in ["uploading", "processing"])
                completed_uploads = sum(1 for status in final_statuses if status in ["ready", "failed"])
                
                success = successful_uploads >= 2 and stuck_uploads == 0
                details = f"Successful uploads: {successful_uploads}/3, Final statuses: {final_statuses}, Stuck: {stuck_uploads}"
                
                await self.log_result("Upload Session Management", success, details)
                return success
                
        except Exception as e:
            await self.log_result("Upload Session Management", False, f"Error: {str(e)}")
            return False
    
    async def test_upload_cleanup_mechanisms(self):
        """Test upload cleanup for failed uploads"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create note
            note_data = {
                "title": "Upload Cleanup Test",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Upload Cleanup - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                
                # Try to upload invalid file (should fail and cleanup)
                invalid_data = b"This is not a valid image file"
                files = {"file": ("invalid.png", invalid_data, "image/png")}
                
                response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                           files=files, headers=headers)
                
                # Wait a moment for any cleanup
                await asyncio.sleep(3)
                
                # Check note status
                status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                if status_response.status_code == 200:
                    note_data = status_response.json()
                    status = note_data.get("status", "unknown")
                    
                    # Should either be failed or back to created (cleaned up)
                    proper_cleanup = status in ["failed", "created"]
                    not_stuck = status != "uploading"
                    
                    success = proper_cleanup and not_stuck
                    details = f"Upload response: {response.status_code}, Final status: {status}"
                    
                    await self.log_result("Upload Cleanup Mechanisms", success, details)
                    return success
                else:
                    await self.log_result("Upload Cleanup Mechanisms", False, "Could not check note status")
                    return False
                    
        except Exception as e:
            await self.log_result("Upload Cleanup Mechanisms", False, f"Error: {str(e)}")
            return False
    
    async def test_audio_upload_stuck_issue(self):
        """Test audio upload for stuck issues"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create audio note
            note_data = {
                "title": "Audio Upload Stuck Test",
                "kind": "audio"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Audio Upload - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                
                # Create test audio file
                audio_data = self.create_test_audio(duration_seconds=30)  # 30 second audio
                files = {"file": ("test_audio.wav", audio_data, "audio/wav")}
                
                start_time = time.time()
                response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                           files=files, headers=headers)
                
                upload_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Monitor processing
                    max_wait = 60  # 1 minute max for audio processing
                    wait_time = 0
                    final_status = None
                    
                    while wait_time < max_wait:
                        await asyncio.sleep(3)
                        wait_time += 3
                        
                        # Check note status
                        status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                        if status_response.status_code == 200:
                            note_data = status_response.json()
                            status = note_data.get("status", "unknown")
                            final_status = status
                            
                            if status in ["ready", "failed"]:
                                break
                    
                    not_stuck = final_status != "processing"
                    success = final_status == "ready"
                    
                    details = f"Upload time: {upload_time:.2f}s, Processing time: {wait_time}s, Final status: {final_status}"
                    await self.log_result("Audio Upload Stuck Issue", success, details)
                    
                    if final_status == "processing":
                        await self.log_result("Audio Upload Stuck Detection", False, "Audio upload stuck in processing - this is the bug!")
                    
                    return success
                else:
                    await self.log_result("Audio Upload Stuck Issue", False, f"Upload failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Audio Upload Stuck Issue", False, f"Error: {str(e)}")
            return False
    
    async def cleanup_test_notes(self):
        """Clean up test notes"""
        if not self.test_notes or not self.auth_token:
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with httpx.AsyncClient(timeout=30) as client:
            for note_id in self.test_notes:
                try:
                    await client.delete(f"{API_BASE}/notes/{note_id}", headers=headers)
                except:
                    pass  # Ignore cleanup errors
    
    async def run_all_tests(self):
        """Run all upload stuck issue tests"""
        print("🔍 UPLOAD STUCK ISSUE INVESTIGATION - BACKEND TESTING")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Could not setup test user, aborting tests")
            return
        
        # Run tests
        test_methods = [
            self.test_small_file_upload_success,
            self.test_large_file_size_limits,
            self.test_upload_timeout_handling,
            self.test_upload_progress_tracking,
            self.test_upload_session_management,
            self.test_upload_cleanup_mechanisms,
            self.test_audio_upload_stuck_issue
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                await self.log_result(test_method.__name__, False, f"Test exception: {str(e)}")
        
        # Cleanup
        await self.cleanup_test_notes()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 UPLOAD STUCK ISSUE TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Identify stuck upload issues
        stuck_issues = []
        for result in self.results:
            if not result['success'] and 'stuck' in result['details'].lower():
                stuck_issues.append(result['test'])
        
        if stuck_issues:
            print(f"\n🚨 STUCK UPLOAD ISSUES IDENTIFIED:")
            for issue in stuck_issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ NO STUCK UPLOAD ISSUES DETECTED")
        
        return success_rate >= 70  # Consider 70%+ success rate as acceptable

async def main():
    """Main test execution"""
    tester = UploadStuckTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 UPLOAD STUCK ISSUE INVESTIGATION COMPLETED SUCCESSFULLY")
    else:
        print("\n⚠️  UPLOAD STUCK ISSUES DETECTED - REQUIRES ATTENTION")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())