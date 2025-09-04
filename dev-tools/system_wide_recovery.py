#!/usr/bin/env python3
"""
URGENT: System-Wide Audio Recovery Investigation
Check for lost meeting recording across all system components.
"""

import asyncio
import httpx
import json
import os
import time
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def system_wide_investigation():
    """System-wide investigation for lost meeting recording"""
    print("🚨 URGENT: SYSTEM-WIDE AUDIO RECOVERY INVESTIGATION")
    print("Checking all system components for lost 1-hour meeting recording...")
    print("=" * 80)
    
    client = httpx.AsyncClient(timeout=60.0)
    
    try:
        # Step 1: Check system health and pipeline status
        print("\n🔍 STEP 1: System Health Check")
        print("-" * 40)
        
        response = await client.get(f"{API_BASE}/health")
        
        if response.status_code == 200:
            health_data = response.json()
            services = health_data.get("services", {})
            pipeline = health_data.get("pipeline", {})
            
            print(f"📊 API Health: {services.get('api', 'unknown')}")
            print(f"📊 Database Health: {services.get('database', 'unknown')}")
            print(f"📊 Pipeline Health: {services.get('pipeline', 'unknown')}")
            print(f"📊 Cache Health: {services.get('cache', 'unknown')}")
            print(f"📊 Storage Health: {services.get('storage', 'unknown')}")
            
            if services.get('pipeline') != 'healthy':
                print(f"⚠️  PIPELINE ISSUE: {services.get('pipeline')}")
                print("   This could explain processing failures!")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        
        # Step 2: Check for processing jobs or stuck transcriptions
        print("\n🔍 STEP 2: Processing Pipeline Investigation")
        print("-" * 40)
        
        # Try to access transcription endpoints to see if there are stuck jobs
        try:
            # Check if there are any transcription jobs
            response = await client.get(f"{API_BASE}/transcriptions")
            if response.status_code == 200:
                jobs = response.json()
                print(f"📊 Found {len(jobs)} transcription jobs")
                
                for job in jobs:
                    job_id = job.get("id", "unknown")
                    status = job.get("status", "unknown")
                    created_at = job.get("created_at", "unknown")
                    print(f"   Job {job_id}: {status} (Created: {created_at})")
                    
                    if status in ["processing", "failed", "stuck"]:
                        print(f"   🎯 POTENTIAL MATCH: Job {job_id} is {status}")
            else:
                print(f"📊 Transcription endpoint: {response.status_code}")
        except Exception as e:
            print(f"📊 Transcription check: {str(e)}")
        
        # Step 3: Check local file system for temp files or uploads
        print("\n🔍 STEP 3: File System Investigation")
        print("-" * 40)
        
        # Check for audio files in common locations
        search_paths = [
            "/app",
            "/tmp",
            "/app/backend",
            "/app/uploads" if os.path.exists("/app/uploads") else None
        ]
        
        audio_extensions = ['.mp3', '.wav', '.m4a', '.webm', '.ogg']
        found_audio_files = []
        
        for search_path in search_paths:
            if search_path and os.path.exists(search_path):
                print(f"📂 Searching {search_path}...")
                
                try:
                    for root, dirs, files in os.walk(search_path):
                        for file in files:
                            if any(file.lower().endswith(ext) for ext in audio_extensions):
                                file_path = os.path.join(root, file)
                                file_size = os.path.getsize(file_path)
                                
                                # Check if it's a large file (potentially 1-hour meeting)
                                if file_size > 10 * 1024 * 1024:  # > 10MB
                                    found_audio_files.append({
                                        "path": file_path,
                                        "size_mb": file_size / (1024 * 1024),
                                        "name": file
                                    })
                                    print(f"   🎯 LARGE AUDIO FILE: {file} ({file_size / (1024*1024):.1f} MB)")
                                    
                                    # Check if filename suggests it's a meeting
                                    meeting_keywords = ["meeting", "conference", "call", "discussion"]
                                    if any(keyword in file.lower() for keyword in meeting_keywords):
                                        print(f"      🚨 MEETING FILE DETECTED!")
                except Exception as e:
                    print(f"   ⚠️  Error searching {search_path}: {e}")
        
        # Step 4: Check upload sessions or incomplete uploads
        print("\n🔍 STEP 4: Upload Session Investigation")
        print("-" * 40)
        
        try:
            # Register a test user to check upload sessions
            test_email = f"syscheck{int(time.time())}@expeditors.com"
            
            response = await client.post(f"{API_BASE}/auth/register", json={
                "email": test_email,
                "password": "SystemCheck123!",
                "username": f"syscheck{int(time.time())}",
                "name": "System Check User"
            })
            
            if response.status_code in [200, 201]:
                auth_data = response.json()
                auth_token = auth_data.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Check for upload sessions
                response = await client.get(f"{API_BASE}/uploads/sessions", headers=headers)
                if response.status_code == 200:
                    sessions = response.json()
                    print(f"📊 Found {len(sessions)} upload sessions")
                    
                    for session in sessions:
                        session_id = session.get("upload_id", "unknown")
                        status = session.get("status", "unknown")
                        filename = session.get("filename", "unknown")
                        total_size = session.get("total_size", 0)
                        
                        print(f"   Session {session_id}: {filename} ({total_size / (1024*1024):.1f} MB) - {status}")
                        
                        if total_size > 50 * 1024 * 1024:  # > 50MB (potential 1-hour file)
                            print(f"   🎯 LARGE UPLOAD SESSION: Could be the lost meeting!")
                else:
                    print(f"📊 Upload sessions check: {response.status_code}")
            else:
                print(f"📊 Could not authenticate for upload session check")
                
        except Exception as e:
            print(f"📊 Upload session check error: {str(e)}")
        
        # Step 5: Summary and recommendations
        print(f"\n" + "=" * 80)
        print(f"📊 SYSTEM-WIDE RECOVERY RESULTS")
        print(f"=" * 80)
        
        print(f"📂 Audio files found on filesystem: {len(found_audio_files)}")
        
        if found_audio_files:
            print(f"\n🎯 POTENTIAL RECOVERY CANDIDATES:")
            for i, audio_file in enumerate(found_audio_files, 1):
                print(f"{i}. {audio_file['name']}")
                print(f"   Path: {audio_file['path']}")
                print(f"   Size: {audio_file['size_mb']:.1f} MB")
                
                # Estimate duration based on file size (rough approximation)
                estimated_minutes = audio_file['size_mb'] * 0.5  # Very rough estimate
                print(f"   Estimated duration: ~{estimated_minutes:.0f} minutes")
                
                if estimated_minutes >= 45:
                    print(f"   🚨 HIGH PROBABILITY: Duration suggests this could be the 1-hour meeting!")
        
        print(f"\n💡 RECOVERY RECOMMENDATIONS:")
        
        if found_audio_files:
            print(f"✅ Found {len(found_audio_files)} audio files on the system")
            print(f"   → Check the files listed above")
            print(f"   → Large files (>45 minutes) are most likely candidates")
            print(f"   → Files can potentially be manually processed through the system")
        else:
            print(f"❌ No audio files found on the system")
            print(f"   → The meeting recording may not have been successfully uploaded")
            print(f"   → Check the user's device for the original recording")
            print(f"   → Check browser cache or temporary files on user's device")
            print(f"   → The recording might be in the user's device storage")
        
        # Additional technical recommendations
        print(f"\n🔧 TECHNICAL RECOVERY OPTIONS:")
        print(f"   1. Check user's browser localStorage/sessionStorage")
        print(f"   2. Check user's device Downloads folder")
        print(f"   3. Check browser's temporary files")
        print(f"   4. If file exists locally, re-upload through /api/upload-file")
        print(f"   5. Check if recording is still in the recording app/browser")
        
        return len(found_audio_files) > 0
        
    except Exception as e:
        print(f"❌ Critical system investigation error: {str(e)}")
        return False
    finally:
        await client.aclose()

async def main():
    success = await system_wide_investigation()
    print(f"\n🏁 System-wide investigation {'found potential files' if success else 'completed - no files found'}")
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)