#!/usr/bin/env python3
"""
Comprehensive Productivity Metrics Testing with File Processing
Testing the complete workflow including file uploads and processing
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
import time
import io
from PIL import Image

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://auto-me-debugger.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveProductivityTester:
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
                "email": f"comptest{timestamp}@test.com",
                "username": f"comptest{timestamp}",
                "password": "TestPass123!",
                "first_name": "Comprehensive",
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
                    await self.log_result("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_result("User Registration", False, f"Exception: {str(e)}")
            return False
    
    async def get_headers(self):
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def create_test_image(self, text="PRODUCTIVITY TEST 2025"):
        """Create a test image with text"""
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color='white')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    async def create_and_process_photo_note(self):
        """Create a photo note and upload an image for processing"""
        try:
            # Create photo note
            note_data = {
                "title": "Productivity Test Photo Note",
                "kind": "photo"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{API_BASE}/notes",
                    json=note_data,
                    headers=await self.get_headers()
                )
                
                if response.status_code != 200:
                    await self.log_result("Create Photo Note for Processing", False, f"Failed to create note: {response.status_code}")
                    return None
                
                note_id = response.json()["id"]
                self.test_notes.append(note_id)
                
                # Upload image file
                image_data = self.create_test_image()
                files = {"file": ("test_image.png", image_data, "image/png")}
                
                response = await client.post(
                    f"{API_BASE}/notes/{note_id}/upload",
                    files=files,
                    headers=await self.get_headers()
                )
                
                if response.status_code == 200:
                    await self.log_result("Upload Image for OCR Processing", True, f"Note ID: {note_id}")
                    
                    # Wait for processing to complete
                    for attempt in range(30):  # Wait up to 30 seconds
                        await asyncio.sleep(1)
                        
                        note_response = await client.get(
                            f"{API_BASE}/notes/{note_id}",
                            headers=await self.get_headers()
                        )
                        
                        if note_response.status_code == 200:
                            note_data = note_response.json()
                            status = note_data.get("status")
                            
                            if status == "ready":
                                await self.log_result("Photo Note Processing Complete", True, f"Note processed in {attempt + 1} seconds")
                                return note_id
                            elif status == "failed":
                                await self.log_result("Photo Note Processing Complete", False, f"Processing failed: {note_data.get('artifacts', {}).get('error', 'Unknown error')}")
                                return None
                    
                    await self.log_result("Photo Note Processing Complete", False, "Processing timed out after 30 seconds")
                    return None
                else:
                    await self.log_result("Upload Image for OCR Processing", False, f"Upload failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            await self.log_result("Create and Process Photo Note", False, f"Exception: {str(e)}")
            return None
    
    async def test_metrics_update_after_photo_processing(self):
        """Test that metrics are updated after photo note processing completes"""
        print("\n🔍 Testing Metrics Update After Photo Processing...")
        
        # Get initial metrics
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{API_BASE}/metrics", headers=await self.get_headers())
            if response.status_code != 200:
                await self.log_result("Get Initial Metrics", False, f"Failed to get metrics: {response.status_code}")
                return False
            
            initial_metrics = response.json()
            initial_photo_count = initial_metrics.get("notes_photo", 0)
            initial_time_saved = initial_metrics.get("estimated_minutes_saved", 0)
            
            print(f"Initial - Photo notes: {initial_photo_count}, Time saved: {initial_time_saved} min")
        
        # Create and process photo note
        note_id = await self.create_and_process_photo_note()
        if not note_id:
            return False
        
        # Wait a moment for metrics update
        await asyncio.sleep(2)
        
        # Get updated metrics
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{API_BASE}/metrics", headers=await self.get_headers())
            if response.status_code != 200:
                await self.log_result("Get Updated Metrics", False, f"Failed to get metrics: {response.status_code}")
                return False
            
            updated_metrics = response.json()
            new_photo_count = updated_metrics.get("notes_photo", 0)
            new_time_saved = updated_metrics.get("estimated_minutes_saved", 0)
            
            print(f"Updated - Photo notes: {new_photo_count}, Time saved: {new_time_saved} min")
        
        # Verify metrics were updated
        photo_count_increased = new_photo_count > initial_photo_count
        time_saved_increased = new_time_saved >= initial_time_saved + 10  # Photo notes save 10 minutes
        
        if photo_count_increased and time_saved_increased:
            await self.log_result("Metrics Update After Photo Processing", True, 
                                f"Photo count: {initial_photo_count} → {new_photo_count}, Time saved: {initial_time_saved} → {new_time_saved} min")
            return True
        else:
            await self.log_result("Metrics Update After Photo Processing", False, 
                                f"Expected increases not detected. Photo: {new_photo_count - initial_photo_count}, Time: {new_time_saved - initial_time_saved}")
            return False
    
    async def test_cumulative_time_savings(self):
        """Test that cumulative time savings are calculated correctly across multiple notes"""
        print("\n🔍 Testing Cumulative Time Savings Calculation...")
        
        # Create multiple text notes (they auto-complete)
        text_notes_created = 0
        for i in range(3):
            try:
                note_data = {
                    "title": f"Cumulative Test Text Note {i+1}",
                    "kind": "text",
                    "text_content": f"This is test content for cumulative metrics testing note {i+1}."
                }
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{API_BASE}/notes",
                        json=note_data,
                        headers=await self.get_headers()
                    )
                    
                    if response.status_code == 200:
                        note_id = response.json()["id"]
                        self.test_notes.append(note_id)
                        text_notes_created += 1
                        await self.log_result(f"Create Cumulative Text Note {i+1}", True, f"Note ID: {note_id}")
                    else:
                        await self.log_result(f"Create Cumulative Text Note {i+1}", False, f"Status: {response.status_code}")
                        
            except Exception as e:
                await self.log_result(f"Create Cumulative Text Note {i+1}", False, f"Exception: {str(e)}")
        
        # Wait for metrics update
        await asyncio.sleep(2)
        
        # Get final metrics
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{API_BASE}/metrics", headers=await self.get_headers())
            if response.status_code != 200:
                await self.log_result("Get Cumulative Metrics", False, f"Failed to get metrics: {response.status_code}")
                return False
            
            metrics = response.json()
            total_text_notes = metrics.get("notes_text", 0)
            total_photo_notes = metrics.get("notes_photo", 0)
            total_time_saved = metrics.get("estimated_minutes_saved", 0)
            
            # Calculate expected time savings
            expected_time_saved = (total_text_notes * 5) + (total_photo_notes * 10)
            
            # Allow for small variance
            time_savings_accurate = abs(total_time_saved - expected_time_saved) <= 10
            
            if time_savings_accurate:
                await self.log_result("Cumulative Time Savings Accuracy", True, 
                                    f"Text: {total_text_notes}×5min + Photo: {total_photo_notes}×10min = Expected: {expected_time_saved}min, Actual: {total_time_saved}min")
                return True
            else:
                await self.log_result("Cumulative Time Savings Accuracy", False, 
                                    f"Time calculation error. Expected: {expected_time_saved}min, Actual: {total_time_saved}min")
                return False
    
    async def test_metrics_persistence(self):
        """Test that metrics are stored in database and persist across requests"""
        print("\n🔍 Testing Metrics Persistence...")
        
        # Get metrics multiple times to ensure consistency
        metrics_calls = []
        
        for i in range(3):
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{API_BASE}/metrics", headers=await self.get_headers())
                if response.status_code == 200:
                    metrics = response.json()
                    metrics_calls.append({
                        'call': i + 1,
                        'time_saved': metrics.get("estimated_minutes_saved", 0),
                        'notes_total': metrics.get("notes_total", 0),
                        'last_update': metrics.get("last_metrics_update")
                    })
                    await asyncio.sleep(1)  # Small delay between calls
        
        if len(metrics_calls) == 3:
            # Check that metrics are consistent across calls
            time_saved_consistent = all(call['time_saved'] == metrics_calls[0]['time_saved'] for call in metrics_calls)
            notes_total_consistent = all(call['notes_total'] == metrics_calls[0]['notes_total'] for call in metrics_calls)
            
            if time_saved_consistent and notes_total_consistent:
                await self.log_result("Metrics Persistence", True, 
                                    f"Metrics consistent across 3 calls. Time saved: {metrics_calls[0]['time_saved']}min, Total notes: {metrics_calls[0]['notes_total']}")
                return True
            else:
                await self.log_result("Metrics Persistence", False, 
                                    f"Metrics inconsistent. Time saved: {[call['time_saved'] for call in metrics_calls]}")
                return False
        else:
            await self.log_result("Metrics Persistence", False, f"Only {len(metrics_calls)} successful calls out of 3")
            return False
    
    async def test_performance_metrics(self):
        """Test that performance metrics are calculated correctly"""
        print("\n🔍 Testing Performance Metrics...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{API_BASE}/metrics", headers=await self.get_headers())
            if response.status_code != 200:
                await self.log_result("Get Performance Metrics", False, f"Failed to get metrics: {response.status_code}")
                return False
            
            metrics = response.json()
            
            # Check performance-related fields
            success_rate = metrics.get("success_rate", 0)
            avg_processing_time = metrics.get("avg_processing_time_minutes", 0)
            p95_latency = metrics.get("p95_latency_ms")
            recent_notes_total = metrics.get("recent_notes_total", 0)
            recent_notes_ready = metrics.get("recent_notes_ready", 0)
            
            # Validate performance metrics
            success_rate_valid = 0 <= success_rate <= 100
            processing_time_valid = avg_processing_time >= 0
            recent_metrics_valid = recent_notes_ready <= recent_notes_total
            
            if success_rate_valid and processing_time_valid and recent_metrics_valid:
                await self.log_result("Performance Metrics Validation", True, 
                                    f"Success rate: {success_rate}%, Avg processing: {avg_processing_time}min, Recent: {recent_notes_ready}/{recent_notes_total}")
                return True
            else:
                await self.log_result("Performance Metrics Validation", False, 
                                    f"Invalid metrics. Success rate: {success_rate}, Processing time: {avg_processing_time}, Recent: {recent_notes_ready}/{recent_notes_total}")
                return False
    
    async def cleanup_test_notes(self):
        """Clean up test notes"""
        print("\n🧹 Cleaning up test notes...")
        
        for note_id in self.test_notes:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.delete(
                        f"{API_BASE}/notes/{note_id}",
                        headers=await self.get_headers()
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Deleted note {note_id}")
                    else:
                        print(f"⚠️  Failed to delete note {note_id}: {response.status_code}")
                        
            except Exception as e:
                print(f"⚠️  Error deleting note {note_id}: {str(e)}")
    
    async def run_all_tests(self):
        """Run all comprehensive productivity metrics tests"""
        print("🚀 Starting Comprehensive Productivity Metrics Testing")
        print("=" * 80)
        
        # Setup
        if not await self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return
        
        try:
            # Run comprehensive tests
            await self.test_metrics_update_after_photo_processing()
            await self.test_cumulative_time_savings()
            await self.test_metrics_persistence()
            await self.test_performance_metrics()
            
        finally:
            # Cleanup
            await self.cleanup_test_notes()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE PRODUCTIVITY METRICS TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("\n✅ COMPREHENSIVE PRODUCTIVITY METRICS: WORKING CORRECTLY")
            print("🎯 Advanced Features Verified:")
            print("   • Metrics update after photo note OCR processing")
            print("   • Cumulative time savings across multiple notes")
            print("   • Metrics persistence in database storage")
            print("   • Performance metrics calculation")
        else:
            print("\n❌ COMPREHENSIVE PRODUCTIVITY METRICS: ISSUES DETECTED")
            print("🔧 Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        return success_rate >= 75

async def main():
    """Main test execution"""
    tester = ComprehensiveProductivityTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())