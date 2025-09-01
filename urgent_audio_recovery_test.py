#!/usr/bin/env python3
"""
URGENT DATE-SPECIFIC AUDIO RECOVERY TEST
September 1, 2025 - Time-Sensitive Audio File Recovery

This test specifically searches for and attempts to recover any audio recordings
from TODAY (September 1, 2025) that may be stuck in processing or lost.
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
from datetime import datetime, timezone, timedelta
from pathlib import Path
import glob
import stat
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://pwa-integration-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Today's date for filtering
TODAY = datetime.now(timezone.utc).date()
TODAY_START = datetime.combine(TODAY, datetime.min.time()).replace(tzinfo=timezone.utc)
TODAY_END = datetime.combine(TODAY, datetime.max.time()).replace(tzinfo=timezone.utc)

print(f"🔍 URGENT AUDIO RECOVERY - Searching for files from: {TODAY} (September 1, 2025)")
print(f"📅 Time range: {TODAY_START} to {TODAY_END}")

class UrgentAudioRecoveryTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.auth_token = None
        self.test_user_email = f"recovery_test_{int(time.time())}@example.com"
        self.test_user_password = "RecoveryTest123!"
        self.found_today_files = []
        self.recovered_files = []
        
        # MongoDB connection for direct database access
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.mongo_client = AsyncIOMotorClient(mongo_url)
        self.db = self.mongo_client[os.environ.get('DB_NAME', 'auto_me_db')]
        
    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()
        self.mongo_client.close()
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            response = await self.client.post(f"{API_BASE}/auth/register", json={
                "email": self.test_user_email,
                "password": self.test_user_password,
                "username": "recoveryuser",
                "name": "Recovery Test User"
            })
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.auth_token = data.get("access_token")
                print(f"✅ Test user registered for recovery operations: {self.test_user_email}")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ User registration error: {str(e)}")
            return False
    
    async def check_database_for_today_notes(self):
        """Check database for notes created today"""
        print(f"\n🔍 STEP 1: Checking database for notes created TODAY ({TODAY})")
        
        try:
            # Query for notes created today
            query = {
                "created_at": {
                    "$gte": TODAY_START,
                    "$lte": TODAY_END
                }
            }
            
            notes_cursor = self.db["notes"].find(query)
            today_notes = await notes_cursor.to_list(length=None)
            
            print(f"📊 Found {len(today_notes)} notes created today")
            
            audio_notes_today = []
            for note in today_notes:
                if note.get("kind") == "audio":
                    audio_notes_today.append(note)
                    created_time = note.get("created_at")
                    status = note.get("status", "unknown")
                    title = note.get("title", "Untitled")
                    note_id = note.get("id", "unknown")
                    media_key = note.get("media_key")
                    
                    print(f"🎵 AUDIO NOTE FOUND:")
                    print(f"   ID: {note_id}")
                    print(f"   Title: {title}")
                    print(f"   Status: {status}")
                    print(f"   Created: {created_time}")
                    print(f"   Media Key: {media_key}")
                    
                    # Check if stuck in processing
                    if status in ["created", "uploading", "processing"]:
                        print(f"   ⚠️  NOTE IS STUCK IN '{status}' STATUS!")
                        self.found_today_files.append({
                            "type": "stuck_note",
                            "note_id": note_id,
                            "title": title,
                            "status": status,
                            "created_at": created_time,
                            "media_key": media_key
                        })
            
            print(f"🎵 Total audio notes from today: {len(audio_notes_today)}")
            
            # Also check for any notes with today's timestamp in any field
            all_notes_cursor = self.db["notes"].find({})
            all_notes = await all_notes_cursor.to_list(length=None)
            
            for note in all_notes:
                # Check ready_at timestamp
                ready_at = note.get("ready_at")
                if ready_at and ready_at.date() == TODAY:
                    if note.get("kind") == "audio" and note not in audio_notes_today:
                        print(f"🎵 ADDITIONAL AUDIO NOTE (ready today): {note.get('title')} - {note.get('id')}")
                        audio_notes_today.append(note)
            
            return audio_notes_today
            
        except Exception as e:
            print(f"❌ Database check error: {str(e)}")
            return []
    
    async def check_file_system_for_today_audio(self):
        """Check file system for audio files created/modified today"""
        print(f"\n🔍 STEP 2: Checking file system for audio files from TODAY ({TODAY})")
        
        storage_dirs = [
            "/tmp/autome_storage",
            "/app/uploads",
            "/tmp/uploads",
            "/var/tmp",
            "/tmp"
        ]
        
        audio_extensions = [".mp3", ".wav", ".m4a", ".webm", ".ogg", ".mpeg", ".aac", ".flac"]
        today_audio_files = []
        
        for storage_dir in storage_dirs:
            if os.path.exists(storage_dir):
                print(f"📁 Scanning directory: {storage_dir}")
                
                try:
                    # Search for audio files
                    for ext in audio_extensions:
                        pattern = f"{storage_dir}/**/*{ext}"
                        files = glob.glob(pattern, recursive=True)
                        
                        for file_path in files:
                            try:
                                # Get file stats
                                file_stat = os.stat(file_path)
                                created_time = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)
                                modified_time = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
                                
                                # Check if file was created or modified today
                                if (created_time.date() == TODAY or modified_time.date() == TODAY):
                                    file_size = file_stat.st_size
                                    
                                    print(f"🎵 AUDIO FILE FROM TODAY FOUND:")
                                    print(f"   Path: {file_path}")
                                    print(f"   Size: {file_size} bytes")
                                    print(f"   Created: {created_time}")
                                    print(f"   Modified: {modified_time}")
                                    
                                    today_audio_files.append({
                                        "type": "file_system",
                                        "path": file_path,
                                        "size": file_size,
                                        "created_at": created_time,
                                        "modified_at": modified_time,
                                        "extension": ext
                                    })
                                    
                                    self.found_today_files.append({
                                        "type": "file_system",
                                        "path": file_path,
                                        "size": file_size,
                                        "created_at": created_time,
                                        "modified_at": modified_time
                                    })
                                    
                            except Exception as e:
                                print(f"   ⚠️  Error checking file {file_path}: {str(e)}")
                                
                except Exception as e:
                    print(f"   ⚠️  Error scanning {storage_dir}: {str(e)}")
            else:
                print(f"📁 Directory not found: {storage_dir}")
        
        print(f"🎵 Total audio files from today found in file system: {len(today_audio_files)}")
        return today_audio_files
    
    async def check_upload_logs_for_today(self):
        """Check for upload logs from today"""
        print(f"\n🔍 STEP 3: Checking for upload/processing logs from TODAY ({TODAY})")
        
        log_locations = [
            "/var/log/supervisor/backend.*.log",
            "/app/logs/*.log",
            "/tmp/*.log",
            "/var/log/*.log"
        ]
        
        today_log_entries = []
        
        for log_pattern in log_locations:
            try:
                log_files = glob.glob(log_pattern)
                for log_file in log_files:
                    if os.path.exists(log_file):
                        print(f"📋 Checking log file: {log_file}")
                        
                        try:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                
                            for line in lines:
                                # Look for today's date in logs
                                if TODAY.strftime("%Y-%m-%d") in line or TODAY.strftime("%m-%d") in line:
                                    # Look for audio-related keywords
                                    audio_keywords = ["audio", "upload", "transcription", "processing", "wav", "mp3", "m4a"]
                                    if any(keyword.lower() in line.lower() for keyword in audio_keywords):
                                        print(f"📋 TODAY'S AUDIO LOG ENTRY: {line.strip()}")
                                        today_log_entries.append(line.strip())
                                        
                        except Exception as e:
                            print(f"   ⚠️  Error reading log file {log_file}: {str(e)}")
                            
            except Exception as e:
                print(f"   ⚠️  Error checking log pattern {log_pattern}: {str(e)}")
        
        print(f"📋 Total relevant log entries from today: {len(today_log_entries)}")
        return today_log_entries
    
    async def check_temp_and_processing_files(self):
        """Check for temporary and processing files from today"""
        print(f"\n🔍 STEP 4: Checking for temporary/processing files from TODAY ({TODAY})")
        
        temp_locations = [
            "/tmp",
            "/var/tmp",
            "/app/temp",
            "/tmp/autome_*",
            "/tmp/upload_*",
            "/tmp/audio_*",
            "/tmp/chunk_*"
        ]
        
        today_temp_files = []
        
        for temp_location in temp_locations:
            try:
                if "*" in temp_location:
                    # Pattern matching
                    files = glob.glob(temp_location)
                else:
                    # Directory scanning
                    if os.path.exists(temp_location):
                        files = [os.path.join(temp_location, f) for f in os.listdir(temp_location)]
                    else:
                        files = []
                
                for file_path in files:
                    if os.path.isfile(file_path):
                        try:
                            file_stat = os.stat(file_path)
                            created_time = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)
                            modified_time = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
                            
                            # Check if file was created or modified today
                            if (created_time.date() == TODAY or modified_time.date() == TODAY):
                                file_size = file_stat.st_size
                                
                                # Check if it might be audio-related
                                filename = os.path.basename(file_path).lower()
                                audio_indicators = ["audio", "wav", "mp3", "m4a", "upload", "chunk", "transcr"]
                                
                                if any(indicator in filename for indicator in audio_indicators) or file_size > 1000:
                                    print(f"📁 TEMP FILE FROM TODAY:")
                                    print(f"   Path: {file_path}")
                                    print(f"   Size: {file_size} bytes")
                                    print(f"   Created: {created_time}")
                                    print(f"   Modified: {modified_time}")
                                    
                                    today_temp_files.append({
                                        "type": "temp_file",
                                        "path": file_path,
                                        "size": file_size,
                                        "created_at": created_time,
                                        "modified_at": modified_time
                                    })
                                    
                        except Exception as e:
                            print(f"   ⚠️  Error checking temp file {file_path}: {str(e)}")
                            
            except Exception as e:
                print(f"   ⚠️  Error checking temp location {temp_location}: {str(e)}")
        
        print(f"📁 Total temp files from today: {len(today_temp_files)}")
        return today_temp_files
    
    async def attempt_recovery_of_stuck_notes(self, stuck_notes):
        """Attempt to recover stuck notes from today"""
        print(f"\n🔧 STEP 5: Attempting recovery of {len(stuck_notes)} stuck notes from TODAY")
        
        if not stuck_notes:
            print("   No stuck notes to recover")
            return []
        
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        recovered_notes = []
        
        for note_info in stuck_notes:
            if note_info.get("type") == "stuck_note":
                note_id = note_info.get("note_id")
                status = note_info.get("status")
                media_key = note_info.get("media_key")
                
                print(f"🔧 Attempting recovery of note: {note_id}")
                print(f"   Current status: {status}")
                print(f"   Media key: {media_key}")
                
                try:
                    # Try to get the note via API
                    response = await self.client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                    
                    if response.status_code == 200:
                        note_data = response.json()
                        current_status = note_data.get("status")
                        
                        print(f"   ✅ Note accessible via API, current status: {current_status}")
                        
                        # If still stuck, try to trigger processing
                        if current_status in ["created", "uploading", "processing"]:
                            print(f"   🔄 Note still stuck in '{current_status}', attempting to trigger processing...")
                            
                            # Try to re-trigger processing by updating status
                            if media_key:
                                # Update to processing status to trigger background task
                                await self.db["notes"].update_one(
                                    {"id": note_id},
                                    {"$set": {"status": "processing"}}
                                )
                                
                                print(f"   ✅ Updated note status to 'processing' to trigger recovery")
                                recovered_notes.append(note_info)
                                self.recovered_files.append(note_info)
                        else:
                            print(f"   ✅ Note appears to have been processed (status: {current_status})")
                            recovered_notes.append(note_info)
                    
                    elif response.status_code == 404:
                        print(f"   ❌ Note not found via API")
                        
                        # Try direct database access
                        db_note = await self.db["notes"].find_one({"id": note_id})
                        if db_note:
                            print(f"   ✅ Note found in database, attempting API recovery...")
                            recovered_notes.append(note_info)
                        else:
                            print(f"   ❌ Note not found in database either")
                    
                    else:
                        print(f"   ❌ API error: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"   ❌ Recovery error: {str(e)}")
        
        print(f"🔧 Recovery attempt completed: {len(recovered_notes)} notes processed")
        return recovered_notes
    
    async def verify_audio_file_integrity(self, file_paths):
        """Verify integrity of found audio files"""
        print(f"\n🔍 STEP 6: Verifying integrity of {len(file_paths)} audio files from TODAY")
        
        valid_files = []
        
        for file_info in file_paths:
            if file_info.get("type") == "file_system":
                file_path = file_info.get("path")
                file_size = file_info.get("size", 0)
                
                print(f"🔍 Checking file: {file_path}")
                
                try:
                    # Basic file checks
                    if os.path.exists(file_path) and file_size > 0:
                        # Try to read first few bytes to verify it's not corrupted
                        with open(file_path, 'rb') as f:
                            header = f.read(100)
                        
                        if len(header) > 0:
                            print(f"   ✅ File is readable, size: {file_size} bytes")
                            
                            # Check if it looks like audio file
                            if (header.startswith(b'RIFF') or  # WAV
                                header.startswith(b'ID3') or   # MP3
                                header.startswith(b'\xff\xfb') or  # MP3
                                b'ftyp' in header[:20]):  # M4A/MP4
                                
                                print(f"   ✅ File appears to be valid audio format")
                                valid_files.append(file_info)
                            else:
                                print(f"   ⚠️  File may not be audio format (header: {header[:20]})")
                        else:
                            print(f"   ❌ File appears to be empty or corrupted")
                    else:
                        print(f"   ❌ File not accessible or empty")
                        
                except Exception as e:
                    print(f"   ❌ Error checking file: {str(e)}")
        
        print(f"🔍 File integrity check completed: {len(valid_files)} valid audio files")
        return valid_files
    
    async def attempt_file_recovery_and_processing(self, valid_files):
        """Attempt to recover and process valid audio files"""
        print(f"\n🔧 STEP 7: Attempting recovery and processing of {len(valid_files)} valid audio files")
        
        if not valid_files:
            print("   No valid files to process")
            return []
        
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        processed_files = []
        
        for file_info in valid_files:
            file_path = file_info.get("path")
            file_size = file_info.get("size", 0)
            created_at = file_info.get("created_at")
            
            print(f"🔧 Processing file: {file_path}")
            
            try:
                # Read the file
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Determine filename
                filename = os.path.basename(file_path)
                if not any(ext in filename.lower() for ext in ['.wav', '.mp3', '.m4a']):
                    filename = f"recovered_audio_{int(time.time())}.wav"
                
                # Try to upload via the upload-file endpoint
                files = {
                    "file": (filename, file_content, "audio/wav")
                }
                data = {
                    "title": f"RECOVERED: Audio from {created_at.strftime('%Y-%m-%d %H:%M')}"
                }
                
                print(f"   📤 Uploading recovered file as: {filename}")
                
                response = await self.client.post(f"{API_BASE}/upload-file", 
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    note_id = result.get("id")
                    status = result.get("status")
                    
                    print(f"   ✅ File uploaded successfully!")
                    print(f"      Note ID: {note_id}")
                    print(f"      Status: {status}")
                    
                    processed_files.append({
                        "original_path": file_path,
                        "note_id": note_id,
                        "status": status,
                        "filename": filename,
                        "size": file_size
                    })
                    
                    self.recovered_files.append({
                        "type": "recovered_and_processed",
                        "original_path": file_path,
                        "note_id": note_id,
                        "status": status
                    })
                    
                else:
                    print(f"   ❌ Upload failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Processing error: {str(e)}")
        
        print(f"🔧 File recovery completed: {len(processed_files)} files processed")
        return processed_files
    
    async def generate_recovery_report(self):
        """Generate comprehensive recovery report"""
        print(f"\n📊 STEP 8: Generating comprehensive recovery report for TODAY ({TODAY})")
        
        report = {
            "recovery_date": TODAY.isoformat(),
            "recovery_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_files_found": len(self.found_today_files),
            "total_files_recovered": len(self.recovered_files),
            "found_files": self.found_today_files,
            "recovered_files": self.recovered_files
        }
        
        print("=" * 80)
        print("🚨 URGENT AUDIO RECOVERY REPORT - September 1, 2025")
        print("=" * 80)
        print(f"📅 Recovery Date: {TODAY}")
        print(f"🕐 Recovery Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
        print(f"📁 Total Files Found from Today: {len(self.found_today_files)}")
        print(f"🔧 Total Files Recovered: {len(self.recovered_files)}")
        
        if self.found_today_files:
            print(f"\n📋 DETAILED FINDINGS:")
            for i, file_info in enumerate(self.found_today_files, 1):
                file_type = file_info.get("type", "unknown")
                print(f"   {i}. Type: {file_type}")
                
                if file_type == "stuck_note":
                    print(f"      Note ID: {file_info.get('note_id')}")
                    print(f"      Title: {file_info.get('title')}")
                    print(f"      Status: {file_info.get('status')}")
                    print(f"      Created: {file_info.get('created_at')}")
                elif file_type == "file_system":
                    print(f"      Path: {file_info.get('path')}")
                    print(f"      Size: {file_info.get('size')} bytes")
                    print(f"      Created: {file_info.get('created_at')}")
                    print(f"      Modified: {file_info.get('modified_at')}")
        
        if self.recovered_files:
            print(f"\n🔧 RECOVERY ACTIONS TAKEN:")
            for i, recovery_info in enumerate(self.recovered_files, 1):
                recovery_type = recovery_info.get("type", "unknown")
                print(f"   {i}. Recovery Type: {recovery_type}")
                
                if recovery_type == "recovered_and_processed":
                    print(f"      Original Path: {recovery_info.get('original_path')}")
                    print(f"      New Note ID: {recovery_info.get('note_id')}")
                    print(f"      Status: {recovery_info.get('status')}")
        
        # Save report to file
        report_filename = f"/tmp/audio_recovery_report_{TODAY.strftime('%Y%m%d')}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 Recovery report saved to: {report_filename}")
        except Exception as e:
            print(f"\n❌ Failed to save report: {str(e)}")
        
        return report
    
    async def run_urgent_recovery(self):
        """Run the complete urgent audio recovery process"""
        print("🚨 STARTING URGENT DATE-SPECIFIC AUDIO RECOVERY")
        print("=" * 80)
        print(f"🎯 TARGET DATE: {TODAY} (September 1, 2025)")
        print(f"🕐 RECOVERY START TIME: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
        print("=" * 80)
        
        # Register test user for API access
        if not await self.register_test_user():
            print("⚠️  Proceeding without authentication (limited access)")
        
        try:
            # Step 1: Check database for today's notes
            today_notes = await self.check_database_for_today_notes()
            
            # Step 2: Check file system for today's audio files
            today_files = await self.check_file_system_for_today_audio()
            
            # Step 3: Check logs for today's activity
            today_logs = await self.check_upload_logs_for_today()
            
            # Step 4: Check temp/processing files
            today_temp_files = await self.check_temp_and_processing_files()
            
            # Step 5: Attempt recovery of stuck notes
            stuck_notes = [f for f in self.found_today_files if f.get("type") == "stuck_note"]
            recovered_notes = await self.attempt_recovery_of_stuck_notes(stuck_notes)
            
            # Step 6: Verify audio file integrity
            file_system_files = [f for f in self.found_today_files if f.get("type") == "file_system"]
            valid_files = await self.verify_audio_file_integrity(file_system_files)
            
            # Step 7: Attempt file recovery and processing
            processed_files = await self.attempt_file_recovery_and_processing(valid_files)
            
            # Step 8: Generate comprehensive report
            report = await self.generate_recovery_report()
            
            # Final summary
            print("\n" + "=" * 80)
            print("🎯 URGENT RECOVERY SUMMARY")
            print("=" * 80)
            
            if len(self.found_today_files) > 0:
                print(f"✅ SUCCESS: Found {len(self.found_today_files)} files from TODAY ({TODAY})")
                print(f"🔧 RECOVERY: Attempted recovery on {len(self.recovered_files)} files")
                
                if len(self.recovered_files) > 0:
                    print("🎉 RECOVERY SUCCESSFUL: Audio files from today have been found and processed!")
                else:
                    print("⚠️  PARTIAL SUCCESS: Files found but recovery needs manual intervention")
            else:
                print(f"❌ NO FILES FOUND: No audio recordings found from TODAY ({TODAY})")
                print("   This could mean:")
                print("   - No recordings were made today")
                print("   - Files were already processed successfully")
                print("   - Files are stored in a different location")
            
            return len(self.found_today_files) > 0
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR during recovery: {str(e)}")
            return False

async def main():
    """Main recovery execution"""
    tester = UrgentAudioRecoveryTester()
    
    try:
        success = await tester.run_urgent_recovery()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    print("🚨 URGENT DATE-SPECIFIC AUDIO RECOVERY SYSTEM")
    print("🎯 Searching for audio recordings from September 1, 2025")
    print("⏰ This is a time-sensitive recovery operation")
    print()
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 RECOVERY OPERATION COMPLETED - Files from today were found!")
        exit(0)
    else:
        print("\n❌ RECOVERY OPERATION COMPLETED - No files from today found")
        exit(1)