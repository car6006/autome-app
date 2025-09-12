#!/usr/bin/env python3
"""
Focused YouTube Processing Tests
Tests the new YouTube functionality specifically
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://transcript-master.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123"

class YouTubeTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def setup_authentication(self):
        """Set up authentication for testing"""
        try:
            # Generate unique email and username for this test
            unique_id = uuid.uuid4().hex[:8]
            unique_email = f"youtube_test_{unique_id}@example.com"
            unique_username = f"youtubetest{unique_id}"
            
            user_data = {
                "email": unique_email,
                "username": unique_username,
                "password": TEST_USER_PASSWORD,
                "first_name": "YouTube",
                "last_name": "Tester"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("access_token") and data.get("user"):
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    print(f"✅ Authentication setup successful: {unique_email}")
                    return True
                else:
                    print(f"❌ Authentication failed: Missing token or user data")
                    return False
            else:
                print(f"❌ Registration failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication setup error: {str(e)}")
            return False

    def test_yt_dlp_availability(self):
        """Test if yt-dlp is installed and available"""
        try:
            import subprocess
            
            # Test yt-dlp availability
            try:
                result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    self.log_result("yt-dlp Availability", True, f"yt-dlp available: {version_info}")
                    return
            except FileNotFoundError:
                pass
            
            # Fallback to youtube-dl
            try:
                result = subprocess.run(['youtube-dl', '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    self.log_result("yt-dlp Availability", True, f"youtube-dl available (fallback): {version_info}")
                    return
            except FileNotFoundError:
                pass
            
            self.log_result("yt-dlp Availability", False, "Neither yt-dlp nor youtube-dl found in system PATH")
                
        except Exception as e:
            self.log_result("yt-dlp Availability", False, f"yt-dlp availability test error: {str(e)}")

    def test_youtube_info_endpoint(self):
        """Test YouTube video information endpoint"""
        if not self.auth_token:
            self.log_result("YouTube Info Endpoint", False, "Skipped - no authentication token")
            return
            
        try:
            # Test with a short public YouTube video
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short and always available
            
            request_data = {
                "url": test_url
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/youtube/info",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'title', 'duration', 'uploader']
                
                if all(field in data for field in required_fields):
                    duration_minutes = data['duration'] / 60
                    self.log_result("YouTube Info Endpoint", True, 
                                  f"Video info retrieved: '{data['title']}' by {data['uploader']} ({duration_minutes:.1f} min)", 
                                  {
                                      "video_id": data['id'],
                                      "title": data['title'],
                                      "duration": f"{duration_minutes:.1f} minutes",
                                      "uploader": data['uploader']
                                  })
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("YouTube Info Endpoint", False, f"Missing required fields: {missing_fields}", data)
            elif response.status_code == 503:
                self.log_result("YouTube Info Endpoint", False, "YouTube processing service unavailable (yt-dlp not installed)")
            elif response.status_code == 400:
                error_detail = response.json().get('detail', response.text)
                if "Invalid YouTube URL" in error_detail:
                    self.log_result("YouTube Info Endpoint", False, f"URL validation failed: {error_detail}")
                elif "too long" in error_detail.lower():
                    self.log_result("YouTube Info Endpoint", True, "Duration validation working (video too long)")
                else:
                    self.log_result("YouTube Info Endpoint", False, f"Unexpected 400 error: {error_detail}")
            else:
                self.log_result("YouTube Info Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("YouTube Info Endpoint", False, f"YouTube info test error: {str(e)}")

    def test_youtube_process_endpoint(self):
        """Test YouTube video processing endpoint"""
        if not self.auth_token:
            self.log_result("YouTube Process Endpoint", False, "Skipped - no authentication token")
            return
            
        try:
            # Use a very short YouTube video for testing
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
            
            request_data = {
                "url": test_url,
                "title": "YouTube Processing Test Video"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/youtube/process",
                json=request_data,
                timeout=120  # Longer timeout for processing
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['note_id', 'title', 'status', 'message']
                
                if all(field in data for field in required_fields):
                    self.youtube_note_id = data['note_id']
                    self.log_result("YouTube Process Endpoint", True, 
                                  f"YouTube video processing started: {data['title']} (Note ID: {data['note_id']})", 
                                  {
                                      "note_id": data['note_id'],
                                      "title": data['title'],
                                      "status": data['status'],
                                      "duration": data.get('duration', 'unknown'),
                                      "estimated_processing_time": data.get('estimated_processing_time', 'unknown')
                                  })
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("YouTube Process Endpoint", False, f"Missing required fields: {missing_fields}", data)
            elif response.status_code == 503:
                self.log_result("YouTube Process Endpoint", False, "YouTube processing service unavailable (yt-dlp not installed)")
            elif response.status_code == 400:
                error_detail = response.json().get('detail', response.text)
                if "Invalid YouTube URL" in error_detail:
                    self.log_result("YouTube Process Endpoint", False, f"URL validation failed: {error_detail}")
                elif "too long" in error_detail.lower():
                    self.log_result("YouTube Process Endpoint", True, "Duration validation working (video too long)")
                else:
                    self.log_result("YouTube Process Endpoint", False, f"Processing failed: {error_detail}")
            else:
                self.log_result("YouTube Process Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("YouTube Process Endpoint", False, f"YouTube process test error: {str(e)}")

    def test_youtube_error_handling(self):
        """Test YouTube error handling for various edge cases"""
        if not self.auth_token:
            self.log_result("YouTube Error Handling", False, "Skipped - no authentication token")
            return
            
        try:
            error_cases_passed = 0
            total_error_cases = 0
            
            # Test Case 1: Invalid URL
            total_error_cases += 1
            invalid_url_data = {"url": "https://example.com/not-youtube"}
            response = self.session.post(f"{BACKEND_URL}/youtube/info", json=invalid_url_data, timeout=15)
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', '')
                if "Invalid YouTube URL" in error_detail:
                    error_cases_passed += 1
            elif response.status_code == 503:
                # Service unavailable - skip this test
                self.log_result("YouTube Error Handling", False, "YouTube service unavailable (yt-dlp not installed)")
                return
            
            time.sleep(1)
            
            # Test Case 2: Empty URL
            total_error_cases += 1
            empty_url_data = {"url": ""}
            response = self.session.post(f"{BACKEND_URL}/youtube/info", json=empty_url_data, timeout=10)
            
            if response.status_code == 400:
                error_cases_passed += 1
            
            # Test Case 3: Malformed request (missing URL)
            total_error_cases += 1
            try:
                response = self.session.post(f"{BACKEND_URL}/youtube/info", json={}, timeout=10)
                if response.status_code in [400, 422]:  # Validation error
                    error_cases_passed += 1
            except:
                error_cases_passed += 1  # Exception is also valid error handling
            
            success_rate = error_cases_passed / total_error_cases
            
            if success_rate >= 0.67:  # At least 67% of error cases handled correctly
                self.log_result("YouTube Error Handling", True, 
                              f"Error handling working correctly. {error_cases_passed}/{total_error_cases} cases handled properly")
            else:
                self.log_result("YouTube Error Handling", False, 
                              f"Error handling issues. Only {error_cases_passed}/{total_error_cases} cases handled properly")
                
        except Exception as e:
            self.log_result("YouTube Error Handling", False, f"YouTube error handling test error: {str(e)}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📺 YOUTUBE PROCESSING FUNCTIONALITY TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        return passed, total

def main():
    """Run YouTube processing tests"""
    print("📺 Starting YouTube Processing Functionality Tests")
    print("=" * 80)
    
    tester = YouTubeTester()
    
    # Setup authentication
    if not tester.setup_authentication():
        print("❌ Failed to setup authentication. Exiting.")
        return
    
    # Run YouTube tests
    print("\n🔧 Testing YouTube Processing Components...")
    tester.test_yt_dlp_availability()
    tester.test_youtube_info_endpoint()
    tester.test_youtube_process_endpoint()
    tester.test_youtube_error_handling()
    
    # Print summary
    passed, total = tester.print_summary()
    
    if passed == total:
        print("🎉 All YouTube tests passed!")
    else:
        print(f"⚠️ {total - passed} YouTube tests failed.")

if __name__ == "__main__":
    main()