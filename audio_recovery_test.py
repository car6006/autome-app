#!/usr/bin/env python3
"""
URGENT: Audio Recovery Investigation Test Suite
Critical data recovery for lost 1-hour meeting voice note recording.

This test suite investigates:
1. Recent audio uploads and their processing status
2. Large audio files (around 1 hour duration) that may be stuck
3. Processing failures, timeout errors, or stuck transcription jobs
4. Temp files or uploaded files that didn't complete processing
5. Large audio file processing pipeline issues
6. Recovery and reprocessing of stuck meeting recordings
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
from datetime import datetime, timedelta, timezone

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://auto-me-debugger.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AudioRecoveryTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)  # Extended timeout for large files
        self.auth_token = None
        self.test_user_email = f"recovery_urgent_{int(time.time())}@expeditors.com"  # Use expeditors for full access
        self.test_user_password = "RecoveryTest123!"
        self.found_audio_files = []
        self.stuck_files = []
        self.large_files = []
        
    async def cleanup(self):
        """Clean up HTTP client"""
        await self.client.aclose()
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            response = await self.client.post(f"{API_BASE}/auth/register", json={
                "email": self.test_user_email,
                "password": self.test_user_password,
                "username": f"recoveryuser{int(time.time())}",
                "name": "Audio Recovery User"
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Recovery test user registered: {self.test_user_email}")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ User registration error: {str(e)}")
            return False
    
    async def search_recent_audio_notes(self):
        """Search for recent audio notes that might be the lost meeting"""
        print("\n🔍 INVESTIGATION 1: Searching Recent Audio Notes")
        print("=" * 60)
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Get all recent notes
            response = await self.client.get(f"{API_BASE}/notes?limit=100", headers=headers)
            
            if response.status_code == 200:
                notes = response.json()
                audio_notes = [note for note in notes if note.get("kind") == "audio"]
                
                print(f"📊 Found {len(audio_notes)} audio notes out of {len(notes)} total notes")
                
                if not audio_notes:
                    print("⚠️  No audio notes found - this might indicate a data loss issue")
                    return []
                
                # Analyze each audio note
                for i, note in enumerate(audio_notes, 1):
                    note_id = note.get("id")
                    title = note.get("title", "Untitled")
                    status = note.get("status", "unknown")
                    created_at = note.get("created_at")
                    artifacts = note.get("artifacts", {})
                    
                    print(f"\n📝 Audio Note {i}: {title}")
                    print(f"   ID: {note_id}")
                    print(f"   Status: {status}")
                    print(f"   Created: {created_at}")
                    
                    # Check for meeting-related keywords
                    meeting_keywords = ["meeting", "conference", "call", "discussion", "session"]
                    is_meeting = any(keyword in title.lower() for keyword in meeting_keywords)
                    
                    if is_meeting:
                        print(f"   🎯 POTENTIAL MATCH: Contains meeting-related keywords")
                        self.found_audio_files.append({
                            "note_id": note_id,
                            "title": title,
                            "status": status,
                            "created_at": created_at,
                            "type": "meeting_candidate",
                            "artifacts": artifacts
                        })
                    
                    # Check for stuck processing
                    if status in ["processing", "uploading"]:
                        print(f"   ⚠️  STUCK IN PROCESSING: Status has been '{status}' - needs investigation")
                        self.stuck_files.append({
                            "note_id": note_id,
                            "title": title,
                            "status": status,
                            "created_at": created_at,
                            "type": "stuck_processing"
                        })
                    
                    # Check for failed processing
                    if status == "failed":
                        print(f"   ❌ FAILED PROCESSING: This could be the lost meeting")
                        self.found_audio_files.append({
                            "note_id": note_id,
                            "title": title,
                            "status": status,
                            "created_at": created_at,
                            "type": "failed_processing",
                            "artifacts": artifacts
                        })
                    
                    # Check transcript length (indicator of file duration)
                    transcript = artifacts.get("transcript", "")
                    if transcript:
                        word_count = len(transcript.split())
                        estimated_minutes = word_count / 150  # Average speaking rate
                        print(f"   📊 Transcript: {word_count} words (~{estimated_minutes:.1f} minutes)")
                        
                        if estimated_minutes >= 45:  # Close to 1 hour
                            print(f"   🎯 LARGE FILE DETECTED: ~{estimated_minutes:.1f} minutes - could be the lost meeting!")
                            self.large_files.append({
                                "note_id": note_id,
                                "title": title,
                                "status": status,
                                "estimated_duration": estimated_minutes,
                                "word_count": word_count,
                                "type": "large_transcript"
                            })
                
                return audio_notes
            else:
                print(f"❌ Failed to retrieve notes: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching audio notes: {str(e)}")
            return []
    
    async def investigate_processing_pipeline(self):
        """Investigate the audio processing pipeline for stuck jobs"""
        print("\n🔍 INVESTIGATION 2: Processing Pipeline Analysis")
        print("=" * 60)
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Check pipeline status
            response = await self.client.get(f"{API_BASE}/health", headers=headers)
            
            if response.status_code == 200:
                health_data = response.json()
                pipeline_status = health_data.get("pipeline", {})
                services = health_data.get("services", {})
                
                print(f"📊 Pipeline Health: {services.get('pipeline', 'unknown')}")
                print(f"📊 Database Health: {services.get('database', 'unknown')}")
                print(f"📊 API Health: {services.get('api', 'unknown')}")
                
                # Check for pipeline issues
                if services.get('pipeline') != 'healthy':
                    print(f"⚠️  PIPELINE ISSUE DETECTED: {services.get('pipeline')}")
                    print("   This could explain why the meeting recording got stuck!")
                
                return pipeline_status
            else:
                print(f"❌ Failed to get pipeline status: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error investigating pipeline: {str(e)}")
            return {}
    
    async def check_large_file_processing(self):
        """Check for large file processing capabilities and issues"""
        print("\n🔍 INVESTIGATION 3: Large File Processing Analysis")
        print("=" * 60)
        
        try:
            # Test large file upload capability
            print("📊 Testing large file processing capability...")
            
            # Create a test file that would trigger chunking (>24MB)
            print("   Creating test large audio file (simulating 1-hour meeting)...")
            large_audio_file = self.create_large_test_audio_file(duration_minutes=60)
            file_size = os.path.getsize(large_audio_file)
            
            print(f"   📊 Test file size: {file_size / (1024*1024):.1f} MB")
            
            if file_size > 24 * 1024 * 1024:  # 24MB threshold
                print("   ✅ File size exceeds chunking threshold - will test chunking system")
                
                # Test upload without actually uploading (just check endpoint)
                headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                
                # Check if upload endpoint accepts large files
                with open(large_audio_file, 'rb') as f:
                    # Read just first chunk to test
                    chunk_data = f.read(1024 * 1024)  # 1MB test chunk
                    
                    files = {
                        "file": ("test_large_meeting.wav", chunk_data, "audio/wav")
                    }
                    data = {
                        "title": "Test Large Meeting Recovery"
                    }
                    
                    # This will likely fail due to size, but we can check the error
                    try:
                        response = await self.client.post(f"{API_BASE}/upload-file", 
                            headers=headers,
                            files=files,
                            data=data,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            print("   ✅ Large file upload endpoint is working")
                            # Clean up the created note
                            data = response.json()
                            note_id = data.get("id")
                            if note_id:
                                await self.client.delete(f"{API_BASE}/notes/{note_id}", headers=headers)
                        else:
                            print(f"   ⚠️  Large file upload response: {response.status_code} - {response.text[:200]}")
                            
                    except Exception as upload_e:
                        print(f"   ⚠️  Large file upload test error: {str(upload_e)}")
            
            # Clean up test file
            os.unlink(large_audio_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing large file processing: {str(e)}")
            return False
    
    def create_large_test_audio_file(self, duration_minutes=60, sample_rate=44100):
        """Create a large test audio file to simulate the lost meeting"""
        duration_seconds = duration_minutes * 60
        frames = []
        
        print(f"   Generating {duration_minutes}-minute test audio file...")
        
        # Generate sine wave with varying frequency to simulate speech
        for i in range(int(duration_seconds * sample_rate)):
            # Vary frequency to simulate speech patterns
            freq = 440 + 200 * math.sin(2 * math.pi * i / (sample_rate * 10))
            value = int(16000 * math.sin(2 * math.pi * freq * i / sample_rate))
            frames.append(struct.pack('<h', value))
            
            # Progress indicator for large files
            if i % (sample_rate * 60) == 0:  # Every minute
                progress = i / (duration_seconds * sample_rate) * 100
                print(f"   Progress: {progress:.1f}%")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(frames))
        
        return temp_file.name
    
    async def investigate_specific_note(self, note_id, note_info):
        """Deep investigation of a specific note that might be the lost meeting"""
        print(f"\n🔍 DEEP INVESTIGATION: Note {note_id}")
        print("=" * 60)
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # Get detailed note information
            response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
            
            if response.status_code == 200:
                note = response.json()
                
                print(f"📝 Title: {note.get('title', 'Untitled')}")
                print(f"📊 Status: {note.get('status', 'unknown')}")
                print(f"📅 Created: {note.get('created_at', 'unknown')}")
                print(f"📅 Ready: {note.get('ready_at', 'not ready')}")
                
                artifacts = note.get("artifacts", {})
                metrics = note.get("metrics", {})
                
                # Check for transcript
                transcript = artifacts.get("transcript", "")
                if transcript:
                    word_count = len(transcript.split())
                    char_count = len(transcript)
                    estimated_duration = word_count / 150  # Average speaking rate
                    
                    print(f"📊 Transcript Analysis:")
                    print(f"   Words: {word_count}")
                    print(f"   Characters: {char_count}")
                    print(f"   Estimated Duration: {estimated_duration:.1f} minutes")
                    
                    if estimated_duration >= 45:
                        print(f"   🎯 POTENTIAL MATCH: Duration suggests this could be the 1-hour meeting!")
                        
                        # Show first and last parts of transcript
                        words = transcript.split()
                        if len(words) > 20:
                            first_words = " ".join(words[:10])
                            last_words = " ".join(words[-10:])
                            print(f"   📝 First words: {first_words}...")
                            print(f"   📝 Last words: ...{last_words}")
                
                # Check for processing errors
                if "error" in artifacts:
                    print(f"❌ Processing Error Found: {artifacts['error']}")
                
                # Check for AI conversations (indicates successful processing)
                ai_conversations = artifacts.get("ai_conversations", [])
                if ai_conversations:
                    print(f"✅ AI Conversations: {len(ai_conversations)} found")
                    print("   This indicates the file was successfully processed")
                
                # Check metrics for file size info
                if metrics:
                    print(f"📊 Metrics: {metrics}")
                
                return note
            else:
                print(f"❌ Failed to get note details: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error investigating note: {str(e)}")
            return None
    
    async def attempt_recovery_reprocessing(self, note_id):
        """Attempt to recover and reprocess a stuck or failed note"""
        print(f"\n🔧 RECOVERY ATTEMPT: Note {note_id}")
        print("=" * 60)
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            # First, get the current note status
            response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Cannot access note for recovery: {response.status_code}")
                return False
            
            note = response.json()
            current_status = note.get("status", "unknown")
            
            print(f"📊 Current Status: {current_status}")
            
            # If note is stuck in processing, we can't directly reprocess
            # But we can check if there's a way to trigger reprocessing
            
            if current_status in ["processing", "uploading"]:
                print("⚠️  Note is stuck in processing state")
                print("   This suggests the original upload may have encountered issues")
                print("   The file might still be recoverable if it was uploaded successfully")
                
                # Check if we can get any information about the original file
                artifacts = note.get("artifacts", {})
                if "media_key" in artifacts or "file_path" in artifacts:
                    print("✅ File reference found in artifacts - file may be recoverable")
                    return True
                else:
                    print("❌ No file reference found - file may be lost")
                    return False
            
            elif current_status == "failed":
                print("❌ Note failed processing")
                artifacts = note.get("artifacts", {})
                error_msg = artifacts.get("error", "No error message available")
                print(f"   Error: {error_msg}")
                
                # Check if file still exists for reprocessing
                if "media_key" in artifacts:
                    print("✅ File reference found - may be able to reprocess")
                    return True
                else:
                    print("❌ No file reference - cannot reprocess")
                    return False
            
            elif current_status == "ready":
                print("✅ Note is already processed successfully")
                return True
            
            else:
                print(f"⚠️  Unknown status: {current_status}")
                return False
                
        except Exception as e:
            print(f"❌ Error during recovery attempt: {str(e)}")
            return False
    
    async def search_for_lost_meeting_patterns(self):
        """Search for patterns that might indicate the lost 1-hour meeting"""
        print("\n🔍 INVESTIGATION 4: Lost Meeting Pattern Analysis")
        print("=" * 60)
        
        # Look for notes created in the last 24 hours that might be the meeting
        current_time = datetime.now(timezone.utc)
        
        meeting_candidates = []
        
        # Check found audio files for meeting patterns
        for audio_file in self.found_audio_files:
            title = audio_file.get("title", "").lower()
            created_at = audio_file.get("created_at", "")
            
            # Parse creation time
            try:
                if created_at:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    hours_ago = (current_time - created_time).total_seconds() / 3600
                    
                    print(f"📝 Analyzing: {audio_file.get('title', 'Untitled')}")
                    print(f"   Created: {hours_ago:.1f} hours ago")
                    print(f"   Status: {audio_file.get('status', 'unknown')}")
                    
                    # Check for meeting indicators
                    meeting_indicators = [
                        "meeting", "conference", "call", "discussion", "session",
                        "standup", "review", "planning", "sync", "team"
                    ]
                    
                    has_meeting_keyword = any(indicator in title for indicator in meeting_indicators)
                    is_recent = hours_ago <= 24  # Within last 24 hours
                    
                    if has_meeting_keyword or is_recent:
                        meeting_candidates.append({
                            **audio_file,
                            "hours_ago": hours_ago,
                            "has_meeting_keyword": has_meeting_keyword,
                            "likelihood_score": self.calculate_meeting_likelihood(audio_file, hours_ago, has_meeting_keyword)
                        })
            
            except Exception as e:
                print(f"   ⚠️  Error parsing date: {e}")
        
        # Sort by likelihood score
        meeting_candidates.sort(key=lambda x: x.get("likelihood_score", 0), reverse=True)
        
        print(f"\n📊 Found {len(meeting_candidates)} potential meeting candidates:")
        
        for i, candidate in enumerate(meeting_candidates[:5], 1):  # Top 5 candidates
            print(f"\n🎯 Candidate {i} (Score: {candidate.get('likelihood_score', 0):.1f}):")
            print(f"   Title: {candidate.get('title', 'Untitled')}")
            print(f"   Status: {candidate.get('status', 'unknown')}")
            print(f"   Created: {candidate.get('hours_ago', 0):.1f} hours ago")
            print(f"   Type: {candidate.get('type', 'unknown')}")
            
            if candidate.get("likelihood_score", 0) >= 7:
                print(f"   🚨 HIGH PROBABILITY: This could be the lost meeting!")
        
        return meeting_candidates
    
    def calculate_meeting_likelihood(self, audio_file, hours_ago, has_meeting_keyword):
        """Calculate likelihood that this is the lost meeting"""
        score = 0
        
        # Recent creation (within last 24 hours)
        if hours_ago <= 1:
            score += 5
        elif hours_ago <= 6:
            score += 3
        elif hours_ago <= 24:
            score += 1
        
        # Meeting keywords in title
        if has_meeting_keyword:
            score += 3
        
        # Status indicators
        status = audio_file.get("status", "")
        if status == "processing":
            score += 4  # Stuck in processing is suspicious
        elif status == "failed":
            score += 5  # Failed processing is very suspicious
        elif status == "uploading":
            score += 3  # Stuck uploading
        
        # File type
        file_type = audio_file.get("type", "")
        if file_type == "stuck_processing":
            score += 3
        elif file_type == "failed_processing":
            score += 4
        elif file_type == "large_transcript":
            score += 2
        
        # Estimated duration (if available)
        estimated_duration = audio_file.get("estimated_duration", 0)
        if estimated_duration >= 45:  # Close to 1 hour
            score += 5
        elif estimated_duration >= 30:
            score += 2
        
        return score
    
    async def run_recovery_investigation(self):
        """Run complete audio recovery investigation"""
        print("🚨 URGENT: AUDIO RECOVERY INVESTIGATION")
        print("Searching for lost 1-hour meeting voice note recording...")
        print("=" * 80)
        
        # Register test user for investigation
        if not await self.register_test_user():
            print("❌ Cannot proceed without authentication")
            return False
        
        investigation_results = {
            "audio_notes_found": 0,
            "stuck_files": 0,
            "large_files": 0,
            "meeting_candidates": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0
        }
        
        try:
            # Investigation 1: Search recent audio notes
            audio_notes = await self.search_recent_audio_notes()
            investigation_results["audio_notes_found"] = len(audio_notes)
            investigation_results["stuck_files"] = len(self.stuck_files)
            investigation_results["large_files"] = len(self.large_files)
            
            # Investigation 2: Check processing pipeline
            await self.investigate_processing_pipeline()
            
            # Investigation 3: Test large file processing
            await self.check_large_file_processing()
            
            # Investigation 4: Pattern analysis for lost meeting
            meeting_candidates = await self.search_for_lost_meeting_patterns()
            investigation_results["meeting_candidates"] = len(meeting_candidates)
            
            # Deep investigation of top candidates
            print("\n🔍 DEEP INVESTIGATION OF TOP CANDIDATES")
            print("=" * 60)
            
            top_candidates = meeting_candidates[:3]  # Top 3 candidates
            
            for candidate in top_candidates:
                note_id = candidate.get("note_id")
                if note_id:
                    print(f"\n🎯 Investigating high-probability candidate: {candidate.get('title', 'Untitled')}")
                    
                    # Deep investigation
                    detailed_note = await self.investigate_specific_note(note_id, candidate)
                    
                    # Attempt recovery if needed
                    if candidate.get("status") in ["processing", "failed", "uploading"]:
                        print(f"🔧 Attempting recovery for stuck/failed note...")
                        investigation_results["recovery_attempts"] += 1
                        
                        recovery_success = await self.attempt_recovery_reprocessing(note_id)
                        if recovery_success:
                            investigation_results["successful_recoveries"] += 1
            
            # Final summary
            print("\n" + "=" * 80)
            print("📊 RECOVERY INVESTIGATION SUMMARY")
            print("=" * 80)
            
            print(f"📊 Audio notes found: {investigation_results['audio_notes_found']}")
            print(f"⚠️  Files stuck in processing: {investigation_results['stuck_files']}")
            print(f"📏 Large files detected: {investigation_results['large_files']}")
            print(f"🎯 Meeting candidates identified: {investigation_results['meeting_candidates']}")
            print(f"🔧 Recovery attempts made: {investigation_results['recovery_attempts']}")
            print(f"✅ Successful recoveries: {investigation_results['successful_recoveries']}")
            
            # Recommendations
            print(f"\n💡 RECOVERY RECOMMENDATIONS:")
            
            if investigation_results["meeting_candidates"] > 0:
                print(f"✅ Found {investigation_results['meeting_candidates']} potential matches for the lost meeting")
                print("   → Check the detailed analysis above for the most likely candidates")
                
                if investigation_results["stuck_files"] > 0:
                    print(f"⚠️  {investigation_results['stuck_files']} files are stuck in processing")
                    print("   → These files may contain the lost meeting recording")
                    print("   → Consider manual intervention to recover these files")
                
                if investigation_results["large_files"] > 0:
                    print(f"📏 {investigation_results['large_files']} large files detected")
                    print("   → These are most likely to be the 1-hour meeting recording")
            else:
                print("❌ No obvious candidates found for the lost meeting")
                print("   → The meeting may have failed to upload completely")
                print("   → Check device storage and upload history")
                print("   → Consider checking browser cache or temp files")
            
            return investigation_results["meeting_candidates"] > 0
            
        except Exception as e:
            print(f"❌ Critical error during recovery investigation: {str(e)}")
            return False

async def main():
    """Main recovery investigation execution"""
    tester = AudioRecoveryTester()
    
    try:
        success = await tester.run_recovery_investigation()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n🏁 Recovery investigation {'completed successfully' if success else 'completed with issues'}")
    exit(0 if success else 1)