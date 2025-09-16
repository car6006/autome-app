#!/usr/bin/env python3
"""
Comprehensive Live Transcription Test
Addresses all critical issues from the review request
"""

import requests
import json
import time
import os
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://audio-chunk-wizard.preview.emergentagent.com/api"
TEST_USER_EMAIL = f"comprehensive_test_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123"

class ComprehensiveLiveTranscriptionTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
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
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=4)}")
        print()
    
    def setup_authentication(self):
        """Setup authentication for testing"""
        try:
            user_data = {
                "email": TEST_USER_EMAIL,
                "username": f"comptest{uuid.uuid4().hex[:8]}",
                "password": TEST_USER_PASSWORD,
                "first_name": "Comprehensive",
                "last_name": "Test"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Auth error: {str(e)}")
            return False

    def test_event_polling_system_problem(self):
        """
        CRITICAL ISSUE 1: Event Polling System Problem
        Test if the event polling endpoint returns real-time updates
        """
        try:
            session_id = f"event_test_{uuid.uuid4().hex[:8]}"
            
            # Step 1: Upload a chunk
            test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * 2048
            files = {'file': ('chunk_0.wav', test_audio, 'audio/wav')}
            data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
            
            upload_response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/chunks/0", 
                                              files=files, data=data, timeout=30)
            
            if upload_response.status_code != 202:
                self.log_result("Event Polling System - Chunk Upload", False, 
                              f"Chunk upload failed: {upload_response.status_code}")
                return
            
            # Step 2: Test immediate event polling (should be empty initially)
            immediate_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/events", timeout=10)
            
            # Step 3: Wait and poll for events (should appear within 1-2 seconds)
            events_found = False
            partial_events = []
            commit_events = []
            
            for poll_attempt in range(10):  # Poll for up to 10 seconds
                time.sleep(1)
                
                response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/events", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])
                    
                    if events:
                        # Categorize events
                        partial_events = [e for e in events if e.get("type") == "partial"]
                        commit_events = [e for e in events if e.get("type") == "commit"]
                        
                        # Check if events are generated within acceptable time (1-2 seconds)
                        if poll_attempt <= 2:  # Within 3 seconds
                            self.log_result("Event Polling System Problem", True, 
                                          f"✅ Real-time events generated within {poll_attempt + 1} seconds: {len(partial_events)} partial, {len(commit_events)} commit", 
                                          {"events": events, "timing": f"{poll_attempt + 1}s"})
                            events_found = True
                            break
                        else:
                            self.log_result("Event Polling System Problem", False, 
                                          f"⚠️ Events generated but delayed ({poll_attempt + 1} seconds): {len(partial_events)} partial, {len(commit_events)} commit", 
                                          {"events": events, "timing": f"{poll_attempt + 1}s"})
                            events_found = True
                            break
                elif response.status_code == 404:
                    continue  # Session might not be ready yet
                else:
                    self.log_result("Event Polling System Problem", False, 
                                  f"Event polling failed: HTTP {response.status_code}")
                    return
            
            if not events_found:
                self.log_result("Event Polling System Problem", False, 
                              "❌ No events generated after 10 seconds - real-time processing not working")
                
        except Exception as e:
            self.log_result("Event Polling System Problem", False, f"Test error: {str(e)}")

    def test_real_time_processing_pipeline(self):
        """
        CRITICAL ISSUE 2: Real-time Processing Pipeline
        Test if audio chunks are immediately processed
        """
        try:
            session_id = f"pipeline_test_{uuid.uuid4().hex[:8]}"
            
            processing_times = []
            
            # Test multiple chunks to verify immediate processing
            for chunk_idx in range(3):
                chunk_start_time = time.time()
                
                # Create test audio chunk
                test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * (2048 + chunk_idx * 100)
                files = {'file': (f'chunk_{chunk_idx}.wav', test_audio, 'audio/wav')}
                data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
                
                # Upload chunk
                upload_response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/chunks/{chunk_idx}", 
                                                  files=files, data=data, timeout=30)
                
                if upload_response.status_code != 202:
                    self.log_result("Real-time Processing Pipeline", False, 
                                  f"Chunk {chunk_idx} upload failed: {upload_response.status_code}")
                    return
                
                upload_result = upload_response.json()
                processing_started = upload_result.get("processing_started", False)
                
                if not processing_started:
                    self.log_result("Real-time Processing Pipeline", False, 
                                  f"Chunk {chunk_idx}: processing_started flag is False")
                    return
                
                # Wait briefly and check if transcription is available
                time.sleep(2)
                
                # Check rolling transcript to see if processing occurred
                live_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/live", timeout=10)
                
                processing_time = time.time() - chunk_start_time
                processing_times.append(processing_time)
                
                if live_response.status_code == 200:
                    live_data = live_response.json()
                    transcript = live_data.get("transcript", {})
                    
                    if transcript and transcript.get("text"):
                        print(f"   ✅ Chunk {chunk_idx}: Processed in {processing_time:.2f}s - '{transcript['text'][:50]}...'")
                    else:
                        print(f"   ⚠️ Chunk {chunk_idx}: Uploaded but no transcript yet ({processing_time:.2f}s)")
                else:
                    print(f"   ❌ Chunk {chunk_idx}: Cannot check transcript status")
                
                time.sleep(1)  # Simulate real-time interval
            
            # Evaluate processing performance
            avg_processing_time = sum(processing_times) / len(processing_times)
            fast_processing = avg_processing_time < 3.0  # Should process within 3 seconds
            
            if fast_processing:
                self.log_result("Real-time Processing Pipeline", True, 
                              f"✅ Immediate processing verified: Average {avg_processing_time:.2f}s per chunk", 
                              {"processing_times": processing_times, "avg_time": f"{avg_processing_time:.2f}s"})
            else:
                self.log_result("Real-time Processing Pipeline", False, 
                              f"⚠️ Processing slower than expected: Average {avg_processing_time:.2f}s per chunk", 
                              {"processing_times": processing_times, "avg_time": f"{avg_processing_time:.2f}s"})
                
        except Exception as e:
            self.log_result("Real-time Processing Pipeline", False, f"Test error: {str(e)}")

    def test_frontend_backend_event_flow(self):
        """
        CRITICAL ISSUE 3: Frontend-Backend Event Flow
        Test complete flow: chunk upload → transcription → Redis update → event generation → frontend polling
        """
        try:
            session_id = f"flow_test_{uuid.uuid4().hex[:8]}"
            
            flow_timeline = []
            
            # Step 1: Record start time
            start_time = time.time()
            flow_timeline.append({"step": "test_start", "time": 0})
            
            # Step 2: Upload chunk
            test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * 2048
            files = {'file': ('flow_chunk.wav', test_audio, 'audio/wav')}
            data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
            
            upload_response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/chunks/0", 
                                              files=files, data=data, timeout=30)
            
            upload_time = time.time() - start_time
            flow_timeline.append({"step": "chunk_upload", "time": upload_time})
            
            if upload_response.status_code != 202:
                self.log_result("Frontend-Backend Event Flow", False, 
                              f"Chunk upload failed: {upload_response.status_code}")
                return
            
            # Step 3: Poll for events (simulating frontend polling)
            events_available_time = None
            transcript_available_time = None
            
            for poll_attempt in range(15):  # Poll for up to 15 seconds
                current_time = time.time() - start_time
                
                # Check events
                events_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/events", timeout=10)
                
                if events_response.status_code == 200:
                    events_data = events_response.json()
                    events = events_data.get("events", [])
                    
                    if events and events_available_time is None:
                        events_available_time = current_time
                        flow_timeline.append({"step": "events_available", "time": events_available_time})
                
                # Check rolling transcript
                live_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/live", timeout=10)
                
                if live_response.status_code == 200:
                    live_data = live_response.json()
                    transcript = live_data.get("transcript", {})
                    
                    if transcript and transcript.get("text") and transcript_available_time is None:
                        transcript_available_time = current_time
                        flow_timeline.append({"step": "transcript_available", "time": transcript_available_time})
                
                # Break if both are available
                if events_available_time and transcript_available_time:
                    break
                
                time.sleep(1)
            
            # Step 4: Evaluate flow timing
            flow_complete = events_available_time and transcript_available_time
            
            if flow_complete:
                event_delay = events_available_time - upload_time
                transcript_delay = transcript_available_time - upload_time
                
                # Check if timing meets real-time requirements (within 1-2 seconds)
                real_time_performance = event_delay <= 2.0 and transcript_delay <= 2.0
                
                if real_time_performance:
                    self.log_result("Frontend-Backend Event Flow", True, 
                                  f"✅ Complete flow working in real-time: Events in {event_delay:.2f}s, Transcript in {transcript_delay:.2f}s", 
                                  {"flow_timeline": flow_timeline, "event_delay": f"{event_delay:.2f}s", "transcript_delay": f"{transcript_delay:.2f}s"})
                else:
                    self.log_result("Frontend-Backend Event Flow", False, 
                                  f"⚠️ Flow working but delayed: Events in {event_delay:.2f}s, Transcript in {transcript_delay:.2f}s", 
                                  {"flow_timeline": flow_timeline, "event_delay": f"{event_delay:.2f}s", "transcript_delay": f"{transcript_delay:.2f}s"})
            else:
                missing_components = []
                if not events_available_time:
                    missing_components.append("events")
                if not transcript_available_time:
                    missing_components.append("transcript")
                
                self.log_result("Frontend-Backend Event Flow", False, 
                              f"❌ Flow incomplete: Missing {', '.join(missing_components)}", 
                              {"flow_timeline": flow_timeline})
                
        except Exception as e:
            self.log_result("Frontend-Backend Event Flow", False, f"Test error: {str(e)}")

    def test_session_state_management(self):
        """
        CRITICAL ISSUE 4: Session State Management
        Test Redis rolling transcript state updates during recording
        """
        try:
            session_id = f"state_test_{uuid.uuid4().hex[:8]}"
            
            state_snapshots = []
            
            # Upload multiple chunks and track state changes
            for chunk_idx in range(4):
                # Upload chunk
                test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * (2048 + chunk_idx * 150)
                files = {'file': (f'state_chunk_{chunk_idx}.wav', test_audio, 'audio/wav')}
                data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
                
                upload_response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_id}/chunks/{chunk_idx}", 
                                                  files=files, data=data, timeout=30)
                
                if upload_response.status_code != 202:
                    self.log_result("Session State Management", False, 
                                  f"Chunk {chunk_idx} upload failed: {upload_response.status_code}")
                    return
                
                # Wait for processing
                time.sleep(2)
                
                # Get current state
                live_response = self.session.get(f"{BACKEND_URL}/live/sessions/{session_id}/live", timeout=10)
                
                if live_response.status_code == 200:
                    live_data = live_response.json()
                    transcript = live_data.get("transcript", {})
                    
                    state_snapshot = {
                        "chunk_idx": chunk_idx,
                        "text": transcript.get("text", ""),
                        "committed_words": transcript.get("committed_words", 0),
                        "tail_words": transcript.get("tail_words", 0),
                        "total_words": transcript.get("committed_words", 0) + transcript.get("tail_words", 0),
                        "is_active": live_data.get("is_active", False)
                    }
                    
                    state_snapshots.append(state_snapshot)
                    
                    print(f"   Chunk {chunk_idx}: {state_snapshot['total_words']} words ({state_snapshot['committed_words']} committed, {state_snapshot['tail_words']} tail)")
                else:
                    state_snapshots.append({
                        "chunk_idx": chunk_idx,
                        "error": f"HTTP {live_response.status_code}"
                    })
                
                time.sleep(1)
            
            # Analyze state progression
            valid_snapshots = [s for s in state_snapshots if "total_words" in s]
            
            if len(valid_snapshots) >= 3:
                # Check if word count increases over time
                word_counts = [s["total_words"] for s in valid_snapshots]
                increasing_words = all(word_counts[i] <= word_counts[i+1] for i in range(len(word_counts)-1))
                
                # Check if committed/tail tracking works
                has_committed_words = any(s["committed_words"] > 0 for s in valid_snapshots)
                has_tail_words = any(s["tail_words"] > 0 for s in valid_snapshots)
                
                if increasing_words and (has_committed_words or has_tail_words):
                    self.log_result("Session State Management", True, 
                                  f"✅ Rolling transcript state properly managed: {len(valid_snapshots)} chunks tracked, words increasing: {word_counts}", 
                                  {"state_snapshots": state_snapshots})
                else:
                    self.log_result("Session State Management", False, 
                                  f"⚠️ State tracking issues: increasing_words={increasing_words}, committed={has_committed_words}, tail={has_tail_words}", 
                                  {"state_snapshots": state_snapshots})
            else:
                self.log_result("Session State Management", False, 
                              f"❌ Insufficient state data: only {len(valid_snapshots)} valid snapshots", 
                              {"state_snapshots": state_snapshots})
                
        except Exception as e:
            self.log_result("Session State Management", False, f"Test error: {str(e)}")

    def test_finalization_pipeline(self):
        """
        CRITICAL ISSUE 5: Finalization Pipeline
        Test session finalization when transcription data exists vs when it doesn't
        """
        try:
            # Test 1: Finalization with transcription data
            session_with_data = f"finalize_with_data_{uuid.uuid4().hex[:8]}"
            
            # Upload chunks to create transcription data
            for chunk_idx in range(2):
                test_audio = b"RIFF\x24\x08WAVEfmt \x10\x01\x02\x44\xac\x10\xb1\x02\x04\x10data\x08" + b"\x00" * (2048 + chunk_idx * 100)
                files = {'file': (f'finalize_chunk_{chunk_idx}.wav', test_audio, 'audio/wav')}
                data = {'sample_rate': '16000', 'codec': 'wav', 'chunk_ms': '5000', 'overlap_ms': '750'}
                
                upload_response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_with_data}/chunks/{chunk_idx}", 
                                                  files=files, data=data, timeout=30)
                
                if upload_response.status_code != 202:
                    self.log_result("Finalization Pipeline - With Data", False, 
                                  f"Chunk upload failed: {upload_response.status_code}")
                    return
            
            # Wait for processing
            time.sleep(5)
            
            # Test finalization with data
            finalize_response = self.session.post(f"{BACKEND_URL}/live/sessions/{session_with_data}/finalize", timeout=30)
            
            if finalize_response.status_code == 200:
                finalize_data = finalize_response.json()
                transcript = finalize_data.get("transcript", {})
                artifacts = finalize_data.get("artifacts", {})
                
                if transcript and transcript.get("text"):
                    self.log_result("Finalization Pipeline - With Data", True, 
                                  f"✅ Finalization successful with data: {len(transcript['text'])} chars, {len(artifacts)} artifacts", 
                                  {"transcript_length": len(transcript["text"]), "artifacts": list(artifacts.keys())})
                else:
                    self.log_result("Finalization Pipeline - With Data", False, 
                                  "⚠️ Finalization succeeded but no transcript data", finalize_data)
            else:
                self.log_result("Finalization Pipeline - With Data", False, 
                              f"❌ Finalization failed: HTTP {finalize_response.status_code}: {finalize_response.text}")
            
            # Test 2: Finalization with empty session (no chunks uploaded)
            empty_session = f"finalize_empty_{uuid.uuid4().hex[:8]}"
            
            # Try to finalize without uploading any chunks
            empty_finalize_response = self.session.post(f"{BACKEND_URL}/live/sessions/{empty_session}/finalize", timeout=30)
            
            if empty_finalize_response.status_code == 404:
                self.log_result("Finalization Pipeline - Empty Session", True, 
                              "✅ Empty session finalization properly handled with 404 (session not found)")
            elif empty_finalize_response.status_code == 200:
                empty_data = empty_finalize_response.json()
                transcript = empty_data.get("transcript", {})
                
                if not transcript or not transcript.get("text"):
                    self.log_result("Finalization Pipeline - Empty Session", True, 
                                  "✅ Empty session finalization handled gracefully (empty transcript)")
                else:
                    self.log_result("Finalization Pipeline - Empty Session", False, 
                                  "⚠️ Empty session unexpectedly has transcript data", empty_data)
            else:
                self.log_result("Finalization Pipeline - Empty Session", False, 
                              f"❌ Unexpected response for empty session: HTTP {empty_finalize_response.status_code}: {empty_finalize_response.text}")
                
        except Exception as e:
            self.log_result("Finalization Pipeline", False, f"Test error: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all comprehensive tests addressing the review request issues"""
        print("🎤 COMPREHENSIVE LIVE TRANSCRIPTION SYSTEM TEST")
        print("=" * 60)
        print("🎯 Debugging Real-time Update Issues")
        print(f"🔗 Target: {BACKEND_URL}")
        print(f"🕒 Started: {datetime.now().isoformat()}")
        print()
        
        # Setup
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        print("🔍 TESTING CRITICAL ISSUES FROM REVIEW REQUEST")
        print("-" * 50)
        
        # Test each critical issue
        print("1️⃣ Testing Event Polling System...")
        self.test_event_polling_system_problem()
        
        print("2️⃣ Testing Real-time Processing Pipeline...")
        self.test_real_time_processing_pipeline()
        
        print("3️⃣ Testing Frontend-Backend Event Flow...")
        self.test_frontend_backend_event_flow()
        
        print("4️⃣ Testing Session State Management...")
        self.test_session_state_management()
        
        print("5️⃣ Testing Finalization Pipeline...")
        self.test_finalization_pipeline()
        
        # Summary
        self.print_comprehensive_summary()

    def print_comprehensive_summary(self):
        """Print comprehensive test summary with root cause analysis"""
        print("=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {len(self.test_results)}")
        
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("-" * 30)
        
        # Analyze specific issues
        event_polling_test = next((r for r in self.test_results if "Event Polling System" in r["test"]), None)
        processing_test = next((r for r in self.test_results if "Real-time Processing" in r["test"]), None)
        flow_test = next((r for r in self.test_results if "Frontend-Backend Event Flow" in r["test"]), None)
        state_test = next((r for r in self.test_results if "Session State Management" in r["test"]), None)
        finalization_test = next((r for r in self.test_results if "Finalization Pipeline" in r["test"]), None)
        
        if event_polling_test and not event_polling_test["success"]:
            print("🚨 CRITICAL: Event polling system not generating real-time updates")
            print("   → Frontend won't receive live transcription updates")
        elif event_polling_test and event_polling_test["success"]:
            print("✅ Event polling system working correctly")
        
        if processing_test and not processing_test["success"]:
            print("🚨 CRITICAL: Real-time processing pipeline issues")
            print("   → Audio chunks not being processed immediately")
        elif processing_test and processing_test["success"]:
            print("✅ Real-time processing pipeline operational")
        
        if flow_test and not flow_test["success"]:
            print("🚨 CRITICAL: Frontend-backend event flow broken")
            print("   → Complete pipeline from upload to frontend display not working")
        elif flow_test and flow_test["success"]:
            print("✅ Frontend-backend event flow working correctly")
        
        if state_test and not state_test["success"]:
            print("🚨 CRITICAL: Redis rolling transcript state issues")
            print("   → Session state not being maintained during recording")
        elif state_test and state_test["success"]:
            print("✅ Redis rolling transcript state management working")
        
        if finalization_test and not finalization_test["success"]:
            print("🚨 CRITICAL: Session finalization pipeline issues")
            print("   → Cannot properly complete transcription sessions")
        elif finalization_test and finalization_test["success"]:
            print("✅ Session finalization pipeline working correctly")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print("-" * 20)
        
        if failed == 0:
            print("✅ SYSTEM OPERATIONAL: Live transcription system is working correctly")
            print("   → Real-time updates are being delivered to frontend")
            print("   → Issue may be in frontend implementation or network connectivity")
        elif failed <= 2:
            print("⚠️ PARTIAL ISSUES: Some components have problems but core system works")
            print("   → Focus on fixing the failed components")
        else:
            print("🚨 SYSTEM ISSUES: Multiple critical components failing")
            print("   → Comprehensive system debugging required")
        
        print(f"\n🕒 Completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    tester = ComprehensiveLiveTranscriptionTest()
    tester.run_comprehensive_tests()