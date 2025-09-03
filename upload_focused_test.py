#!/usr/bin/env python3
"""
Focused Upload Investigation - Testing Direct Upload and Concurrent Upload Issues
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

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class FocusedUploadTester:
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
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            register_data = {
                "email": f"focustest{timestamp}@test.com",
                "username": f"focustest{timestamp}",
                "password": "TestPass123!",
                "first_name": "Focus",
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
                    await self.log_result("User Registration", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("User Registration", False, f"Error: {str(e)}")
            return False
    
    def create_test_image(self, size_mb=1, format='PNG'):
        """Create a test image of specified size"""
        target_bytes = size_mb * 1024 * 1024
        pixels_needed = target_bytes // 3
        width = int(pixels_needed ** 0.5)
        height = width
        
        img = Image.new('RGB', (width, height), color='blue')
        
        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), f"Test {size_mb}MB", fill='white')
        except:
            pass
        
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()
    
    async def test_direct_upload_endpoint(self):
        """Test the /api/upload-file endpoint directly"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create test image
            image_data = self.create_test_image(size_mb=2)
            
            async with httpx.AsyncClient(timeout=60) as client:
                # Test direct upload
                files = {"file": ("direct_test.png", image_data, "image/png")}
                form_data = {"title": "Direct Upload Test"}
                
                start_time = time.time()
                response = await client.post(f"{API_BASE}/upload-file", 
                                           files=files, data=form_data, headers=headers)
                
                upload_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    note_id = data.get("id")
                    status = data.get("status", "unknown")
                    
                    # Monitor processing
                    max_wait = 30
                    wait_time = 0
                    final_status = status
                    
                    while wait_time < max_wait and final_status == "processing":
                        await asyncio.sleep(2)
                        wait_time += 2
                        
                        # Check note status
                        status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                        if status_response.status_code == 200:
                            note_data = status_response.json()
                            final_status = note_data.get("status", "unknown")
                            
                            if final_status in ["ready", "failed"]:
                                break
                    
                    success = final_status == "ready"
                    details = f"Upload time: {upload_time:.2f}s, Processing time: {wait_time}s, Final status: {final_status}"
                    await self.log_result("Direct Upload Endpoint", success, details)
                    
                    # Store for cleanup
                    if note_id:
                        self.test_notes.append(note_id)
                    
                    return success
                else:
                    await self.log_result("Direct Upload Endpoint", False, f"Upload failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Direct Upload Endpoint", False, f"Error: {str(e)}")
            return False
    
    async def test_concurrent_upload_detailed(self):
        """Detailed test of concurrent uploads to identify stuck issues"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create 5 notes for concurrent testing
            note_ids = []
            
            async with httpx.AsyncClient(timeout=60) as client:
                for i in range(5):
                    note_data = {
                        "title": f"Concurrent Test Note {i+1}",
                        "kind": "photo"
                    }
                    
                    response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                    if response.status_code == 200:
                        note_info = response.json()
                        note_ids.append(note_info["id"])
                
                if len(note_ids) < 5:
                    await self.log_result("Concurrent Upload Setup", False, f"Only created {len(note_ids)}/5 notes")
                    return False
                
                # Upload files concurrently with different sizes
                async def upload_and_monitor(note_id, file_num, size_mb):
                    try:
                        image_data = self.create_test_image(size_mb=size_mb)
                        files = {"file": (f"concurrent_{file_num}.png", image_data, "image/png")}
                        
                        # Upload
                        start_time = time.time()
                        response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                                   files=files, headers=headers)
                        upload_time = time.time() - start_time
                        
                        if response.status_code != 200:
                            return {"success": False, "upload_time": upload_time, "error": f"Upload failed: {response.status_code}"}
                        
                        # Monitor processing
                        max_wait = 45
                        wait_time = 0
                        final_status = "processing"
                        
                        while wait_time < max_wait:
                            await asyncio.sleep(2)
                            wait_time += 2
                            
                            status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                            if status_response.status_code == 200:
                                note_data = status_response.json()
                                final_status = note_data.get("status", "unknown")
                                
                                if final_status in ["ready", "failed"]:
                                    break
                        
                        return {
                            "success": final_status == "ready",
                            "upload_time": upload_time,
                            "processing_time": wait_time,
                            "final_status": final_status,
                            "stuck": final_status == "processing"
                        }
                        
                    except Exception as e:
                        return {"success": False, "error": str(e)}
                
                # Execute concurrent uploads with different file sizes
                print("   Starting concurrent uploads...")
                results = await asyncio.gather(
                    upload_and_monitor(note_ids[0], 1, 1),   # 1MB
                    upload_and_monitor(note_ids[1], 2, 2),   # 2MB
                    upload_and_monitor(note_ids[2], 3, 3),   # 3MB
                    upload_and_monitor(note_ids[3], 4, 1),   # 1MB
                    upload_and_monitor(note_ids[4], 5, 2),   # 2MB
                    return_exceptions=True
                )
                
                # Analyze results
                successful = 0
                stuck_count = 0
                failed_count = 0
                processing_times = []
                
                for i, result in enumerate(results):
                    if isinstance(result, dict):
                        if result.get("success"):
                            successful += 1
                            processing_times.append(result.get("processing_time", 0))
                        elif result.get("stuck"):
                            stuck_count += 1
                        else:
                            failed_count += 1
                        
                        print(f"   Upload {i+1}: {result}")
                    else:
                        failed_count += 1
                        print(f"   Upload {i+1}: Exception - {result}")
                
                # Store note IDs for cleanup
                self.test_notes.extend(note_ids)
                
                # Determine success
                success = stuck_count == 0 and successful >= 3  # At least 3/5 should succeed without getting stuck
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
                
                details = f"Successful: {successful}/5, Stuck: {stuck_count}, Failed: {failed_count}, Avg processing: {avg_processing_time:.1f}s"
                await self.log_result("Concurrent Upload Detailed", success, details)
                
                if stuck_count > 0:
                    await self.log_result("Stuck Upload Detection", False, f"{stuck_count} uploads stuck in processing state")
                
                return success
                
        except Exception as e:
            await self.log_result("Concurrent Upload Detailed", False, f"Error: {str(e)}")
            return False
    
    async def test_upload_cancellation(self):
        """Test if stuck uploads can be cancelled/retried"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create note
            note_data = {
                "title": "Upload Cancellation Test",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Upload Cancellation - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                
                # Upload large file that might get stuck
                large_image_data = self.create_test_image(size_mb=10)
                files = {"file": ("cancel_test.png", large_image_data, "image/png")}
                
                # Start upload
                response = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                           files=files, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Upload Cancellation", False, f"Upload failed: {response.status_code}")
                    return False
                
                # Wait a bit then check if we can "cancel" by deleting the note
                await asyncio.sleep(5)
                
                # Try to delete the note (simulating cancellation)
                delete_response = await client.delete(f"{API_BASE}/notes/{note_id}", headers=headers)
                
                if delete_response.status_code == 200:
                    # Verify note is deleted
                    await asyncio.sleep(2)
                    check_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                    
                    success = check_response.status_code == 404
                    details = f"Delete response: {delete_response.status_code}, Verification: {check_response.status_code}"
                    await self.log_result("Upload Cancellation", success, details)
                    return success
                else:
                    await self.log_result("Upload Cancellation", False, f"Could not delete note: {delete_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Upload Cancellation", False, f"Error: {str(e)}")
            return False
    
    async def test_upload_retry_mechanism(self):
        """Test retry mechanism for failed uploads"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create note
            note_data = {
                "title": "Upload Retry Test",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(f"{API_BASE}/notes", json=note_data, headers=headers)
                
                if response.status_code != 200:
                    await self.log_result("Upload Retry - Note Creation", False, f"Status: {response.status_code}")
                    return False
                
                note_info = response.json()
                note_id = note_info["id"]
                
                # First, try with invalid file
                invalid_data = b"This is not a valid image"
                files = {"file": ("invalid.png", invalid_data, "image/png")}
                
                response1 = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                            files=files, headers=headers)
                
                # Wait for processing
                await asyncio.sleep(3)
                
                # Check status
                status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                if status_response.status_code == 200:
                    note_data = status_response.json()
                    status_after_invalid = note_data.get("status", "unknown")
                
                # Now try with valid file (retry)
                valid_image_data = self.create_test_image(size_mb=1)
                files = {"file": ("valid_retry.png", valid_image_data, "image/png")}
                
                response2 = await client.post(f"{API_BASE}/notes/{note_id}/upload", 
                                            files=files, headers=headers)
                
                if response2.status_code == 200:
                    # Wait for processing
                    max_wait = 20
                    wait_time = 0
                    final_status = None
                    
                    while wait_time < max_wait:
                        await asyncio.sleep(2)
                        wait_time += 2
                        
                        status_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                        if status_response.status_code == 200:
                            note_data = status_response.json()
                            final_status = note_data.get("status", "unknown")
                            
                            if final_status in ["ready", "failed"]:
                                break
                    
                    success = final_status == "ready"
                    details = f"After invalid: {status_after_invalid}, After retry: {final_status}, Retry response: {response2.status_code}"
                    await self.log_result("Upload Retry Mechanism", success, details)
                    
                    # Store for cleanup
                    self.test_notes.append(note_id)
                    return success
                else:
                    await self.log_result("Upload Retry Mechanism", False, f"Retry upload failed: {response2.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_result("Upload Retry Mechanism", False, f"Error: {str(e)}")
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
                    pass
    
    async def run_all_tests(self):
        """Run all focused upload tests"""
        print("🔍 FOCUSED UPLOAD INVESTIGATION - DETAILED TESTING")
        print("=" * 60)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Could not setup test user, aborting tests")
            return
        
        # Run tests
        test_methods = [
            self.test_direct_upload_endpoint,
            self.test_concurrent_upload_detailed,
            self.test_upload_cancellation,
            self.test_upload_retry_mechanism
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
        print("📊 FOCUSED UPLOAD TEST SUMMARY")
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
        
        return success_rate >= 75

async def main():
    """Main test execution"""
    tester = FocusedUploadTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 FOCUSED UPLOAD INVESTIGATION COMPLETED")
    else:
        print("\n⚠️  UPLOAD ISSUES DETECTED")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())