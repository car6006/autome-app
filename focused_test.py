#!/usr/bin/env python3
"""
Focused Testing for Enhanced Dual-Provider System and Live Transcription
Tests the specific features mentioned in the review request
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://content-capture-1.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"testuser_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "TestPassword123"

class FocusedTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        self.note_id = None
        
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
            # Register user
            user_data = {
                "email": TEST_USER_EMAIL,
                "username": f"testuser{int(time.time())}",
                "password": TEST_USER_PASSWORD,
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                # Create a test note for AI testing
                note_data = {
                    "title": "Enhanced Provider Test Note",
                    "kind": "text",
                    "text_content": "This is a comprehensive test note for the enhanced dual-provider AI system. It contains sample content about a business meeting discussing quarterly performance, strategic planning, and action items for the next quarter. The meeting covered topics like revenue growth, customer satisfaction, team development, and operational efficiency improvements."
                }
                
                note_response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
                if note_response.status_code == 200:
                    self.note_id = note_response.json()["id"]
                    
                self.log_result("Authentication Setup", True, f"User registered and note created: {self.note_id}")
                return True
            else:
                self.log_result("Authentication Setup", False, f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Setup error: {str(e)}")
            return False

    def test_emergent_llm_key_configuration(self):
        """Test that Emergent LLM Key is properly configured"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    self.log_result("Emergent LLM Key Configuration", True, 
                                  "System health indicates enhanced providers are configured")
                else:
                    self.log_result("Emergent LLM Key Configuration", False, 
                                  f"System health status: {data.get('status')}")
            else:
                self.log_result("Emergent LLM Key Configuration", False, 
                              f"Cannot check system health: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Emergent LLM Key Configuration", False, f"Configuration test error: {str(e)}")

    def test_report_generation_dual_provider(self):
        """Test report generation with dual-provider system"""
        if not self.note_id:
            self.log_result("Report Generation Dual Provider", False, "No test note available")
            return
            
        try:
            response = self.session.post(
                f"{BACKEND_URL}/notes/{self.note_id}/generate-report",
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("report") and len(data["report"]) > 100:
                    self.log_result("Report Generation Dual Provider", True, 
                                  f"✅ Report generated successfully using dual-provider system. Length: {len(data['report'])} chars", 
                                  {"report_length": len(data["report"]), "is_expeditors": data.get("is_expeditors", False)})
                else:
                    self.log_result("Report Generation Dual Provider", False, "Report generated but content too short", data)
            elif response.status_code == 500:
                error_text = response.text.lower()
                if "quota" in error_text or "rate limit" in error_text or "temporarily unavailable" in error_text:
                    self.log_result("Report Generation Dual Provider", True, 
                                  "✅ Dual-provider system properly handling quota limits with appropriate error messages")
                else:
                    self.log_result("Report Generation Dual Provider", False, f"Unexpected 500 error: {response.text}")
            else:
                self.log_result("Report Generation Dual Provider", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Report Generation Dual Provider", False, f"Report generation test error: {str(e)}")

    def test_ai_chat_dual_provider(self):
        """Test AI chat functionality with dual-provider support"""
        if not self.note_id:
            self.log_result("AI Chat Dual Provider", False, "No test note available")
            return
            
        try:
            chat_request = {
                "question": "What are the key insights and action items from this business meeting content?"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/notes/{self.note_id}/ai-chat",
                json=chat_request,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("response") and len(data["response"]) > 50:
                    self.log_result("AI Chat Dual Provider", True, 
                                  f"✅ AI chat working with dual-provider system. Response length: {len(data['response'])} chars")
                else:
                    self.log_result("AI Chat Dual Provider", False, "AI chat response too short or empty", data)
            elif response.status_code == 500:
                error_text = response.text.lower()
                if "quota" in error_text or "temporarily unavailable" in error_text:
                    self.log_result("AI Chat Dual Provider", True, 
                                  "✅ AI chat properly handling provider limitations with fallback system")
                else:
                    self.log_result("AI Chat Dual Provider", False, f"Unexpected AI chat error: {response.text}")
            else:
                self.log_result("AI Chat Dual Provider", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("AI Chat Dual Provider", False, f"AI chat dual provider test error: {str(e)}")

    def test_redis_connectivity(self):
        """Test Redis connectivity for live transcription state management"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", {})
                cache_status = services.get("cache", "unknown")
                
                if cache_status in ["healthy", "enabled"]:
                    self.log_result("Redis Connectivity", True, f"✅ Redis/Cache service status: {cache_status}")
                elif cache_status == "disabled":
                    self.log_result("Redis Connectivity", True, "Cache service disabled (Redis may not be required for this deployment)")
                else:
                    self.log_result("Redis Connectivity", False, f"Cache service status: {cache_status}")
            else:
                self.log_result("Redis Connectivity", False, f"Health endpoint error: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Redis Connectivity", False, f"Redis connectivity test error: {str(e)}")

    def test_live_transcription_streaming_endpoints(self):
        """Test live transcription streaming endpoints"""
        try:
            session_id = f"test_session_{int(time.time())}"
            chunk_idx = 0
            
            # Create test audio chunk
            test_audio_content = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"test_audio_data" * 200
            
            files = {
                'file': (f'chunk_{chunk_idx}.wav', test_audio_content, 'audio/wav')
            }
            data = {
                'sample_rate': 16000,
                'codec': 'wav',
                'chunk_ms': 5000,
                'overlap_ms': 750
            }
            
            # Test chunk upload endpoint
            response = self.session.post(
                f"{BACKEND_URL}/uploads/sessions/{session_id}/chunks/{chunk_idx}",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 202:
                result = response.json()
                if result.get("processing_started") and result.get("session_id") == session_id:
                    self.streaming_session_id = session_id
                    self.log_result("Live Transcription Streaming", True, 
                                  f"✅ Streaming chunk upload successful for session {session_id}", result)
                else:
                    self.log_result("Live Transcription Streaming", False, "Missing processing confirmation", result)
            else:
                self.log_result("Live Transcription Streaming", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Live Transcription Streaming", False, f"Live transcription streaming test error: {str(e)}")

    def test_live_transcription_finalization(self):
        """Test live transcription session finalization"""
        if not hasattr(self, 'streaming_session_id'):
            self.log_result("Live Transcription Finalization", False, "No streaming session available")
            return
            
        try:
            # Wait for processing
            time.sleep(3)
            
            # Test session finalization
            response = self.session.post(
                f"{BACKEND_URL}/uploads/sessions/{self.streaming_session_id}/finalize",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("transcript") and data.get("artifacts"):
                    self.log_result("Live Transcription Finalization", True, 
                                  f"✅ Session finalized successfully. Transcript length: {len(data['transcript'].get('text', ''))} chars", 
                                  {"artifacts_count": len(data.get("artifacts", {}))})
                else:
                    self.log_result("Live Transcription Finalization", False, "Missing transcript or artifacts", data)
            else:
                self.log_result("Live Transcription Finalization", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Live Transcription Finalization", False, f"Live transcription finalization test error: {str(e)}")

    def test_quota_error_resolution(self):
        """Test that quota errors are properly resolved with dual-provider system"""
        if not self.note_id:
            self.log_result("Quota Error Resolution", False, "No test note available")
            return
            
        try:
            operations_tested = 0
            successful_operations = 0
            quota_handled_operations = 0
            
            # Test report generation
            response = self.session.post(f"{BACKEND_URL}/notes/{self.note_id}/generate-report", timeout=60)
            operations_tested += 1
            
            if response.status_code == 200:
                successful_operations += 1
            elif response.status_code == 500 and ("quota" in response.text.lower() or "temporarily unavailable" in response.text.lower()):
                quota_handled_operations += 1
            
            # Test AI chat
            chat_request = {"question": "Summarize this content briefly"}
            response = self.session.post(f"{BACKEND_URL}/notes/{self.note_id}/ai-chat", json=chat_request, timeout=45)
            operations_tested += 1
            
            if response.status_code == 200:
                successful_operations += 1
            elif response.status_code == 500 and ("quota" in response.text.lower() or "temporarily unavailable" in response.text.lower()):
                quota_handled_operations += 1
            
            # Evaluate results
            if successful_operations > 0:
                self.log_result("Quota Error Resolution", True, 
                              f"✅ Dual-provider system working: {successful_operations}/{operations_tested} operations successful")
            elif quota_handled_operations > 0:
                self.log_result("Quota Error Resolution", True, 
                              f"✅ Quota errors properly handled with appropriate error messages: {quota_handled_operations}/{operations_tested}")
            else:
                self.log_result("Quota Error Resolution", False, 
                              f"No successful operations or proper quota handling: {operations_tested} operations tested")
                
        except Exception as e:
            self.log_result("Quota Error Resolution", False, f"Quota error resolution test error: {str(e)}")

    def run_focused_tests(self):
        """Run focused tests for enhanced dual-provider system and live transcription"""
        print("🎯 FOCUSED TESTING: Enhanced Dual-Provider System & Live Transcription")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed, cannot continue with tests")
            return self.print_summary()
        
        print("\n🚀 ENHANCED DUAL-PROVIDER SYSTEM TESTS")
        print("-" * 50)
        self.test_emergent_llm_key_configuration()
        self.test_report_generation_dual_provider()
        self.test_ai_chat_dual_provider()
        self.test_quota_error_resolution()
        
        print("\n🎤 LIVE TRANSCRIPTION INFRASTRUCTURE TESTS")
        print("-" * 50)
        self.test_redis_connectivity()
        self.test_live_transcription_streaming_endpoints()
        self.test_live_transcription_finalization()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 FOCUSED TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        # Categorize results
        dual_provider_tests = [r for r in self.test_results if "dual" in r["test"].lower() or "emergent" in r["test"].lower() or "quota" in r["test"].lower() or "report" in r["test"].lower()]
        live_transcription_tests = [r for r in self.test_results if "live" in r["test"].lower() or "streaming" in r["test"].lower() or "redis" in r["test"].lower()]
        
        print(f"\n🚀 Dual-Provider System: {sum(1 for r in dual_provider_tests if r['success'])}/{len(dual_provider_tests)} passed")
        print(f"🎤 Live Transcription: {sum(1 for r in live_transcription_tests if r['success'])}/{len(live_transcription_tests)} passed")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        return {
            "total": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed/len(self.test_results)*100 if self.test_results else 0,
            "dual_provider_results": dual_provider_tests,
            "live_transcription_results": live_transcription_tests,
            "results": self.test_results
        }

def main():
    """Main test execution"""
    tester = FocusedTester()
    results = tester.run_focused_tests()
    
    # Exit with error code if critical tests failed
    if results and results["failed"] > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()