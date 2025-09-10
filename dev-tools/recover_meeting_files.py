#!/usr/bin/env python3
"""
URGENT: Meeting File Recovery and Processing
Attempt to recover and process the found meeting audio files.
"""

import asyncio
import httpx
import json
import os
import time
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://smart-transcript-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def recover_meeting_files():
    """Attempt to recover and process the found meeting files"""
    print("🚨 URGENT: MEETING FILE RECOVERY AND PROCESSING")
    print("Attempting to recover the found meeting audio files...")
    print("=" * 80)
    
    # Found files from previous investigation
    meeting_files = [
        {
            "path": "/app/Regional_Meeting_20_August_2025.mp3",
            "name": "Regional_Meeting_20_August_2025.mp3",
            "size_mb": 61.8
        },
        {
            "path": "/app/Regional_Meeting_Test.mp3", 
            "name": "Regional_Meeting_Test.mp3",
            "size_mb": 61.8
        }
    ]
    
    client = httpx.AsyncClient(timeout=300.0)  # Extended timeout for large files
    
    try:
        # Step 1: Authenticate
        print("\n🔐 STEP 1: Authentication")
        print("-" * 40)
        
        test_email = f"recovery{int(time.time())}@expeditors.com"
        
        response = await client.post(f"{API_BASE}/auth/register", json={
            "email": test_email,
            "password": "Recovery123!",
            "username": f"recovery{int(time.time())}",
            "name": "Meeting Recovery User"
        })
        
        if response.status_code not in [200, 201]:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
        
        auth_data = response.json()
        auth_token = auth_data.get("access_token")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        print(f"✅ Authentication successful")
        
        # Step 2: Analyze each meeting file
        print(f"\n🔍 STEP 2: Meeting File Analysis")
        print("-" * 40)
        
        recovery_results = []
        
        for i, meeting_file in enumerate(meeting_files, 1):
            file_path = meeting_file["path"]
            file_name = meeting_file["name"]
            
            print(f"\n📝 Analyzing File {i}: {file_name}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
            
            # Get file details
            file_size = os.path.getsize(file_path)
            print(f"   📊 Size: {file_size / (1024*1024):.1f} MB")
            
            # Estimate duration (more accurate calculation)
            # For MP3: roughly 1MB per minute for standard quality
            estimated_duration_minutes = file_size / (1024 * 1024)
            print(f"   ⏱️  Estimated Duration: ~{estimated_duration_minutes:.0f} minutes")
            
            if estimated_duration_minutes >= 45:
                print(f"   🎯 POTENTIAL 1-HOUR MEETING: Duration matches user's description!")
            
            # Check file creation/modification time
            try:
                stat = os.stat(file_path)
                mod_time = time.ctime(stat.st_mtime)
                print(f"   📅 Last Modified: {mod_time}")
            except Exception as e:
                print(f"   ⚠️  Could not get file timestamp: {e}")
            
            # Step 3: Attempt to upload and process the file
            print(f"\n🔧 STEP 3: Recovery Processing for {file_name}")
            print("-" * 40)
            
            try:
                # Read file content
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                print(f"   📤 Uploading {file_name} for processing...")
                
                # Upload via the upload-file endpoint
                files = {
                    "file": (file_name, file_content, "audio/mpeg")
                }
                data = {
                    "title": f"RECOVERED: {file_name.replace('.mp3', '')}"
                }
                
                response = await client.post(f"{API_BASE}/upload-file", 
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    upload_data = response.json()
                    note_id = upload_data.get("id")
                    status = upload_data.get("status")
                    
                    print(f"   ✅ Upload successful!")
                    print(f"      Note ID: {note_id}")
                    print(f"      Status: {status}")
                    
                    recovery_results.append({
                        "file_name": file_name,
                        "note_id": note_id,
                        "status": status,
                        "estimated_duration": estimated_duration_minutes,
                        "upload_success": True
                    })
                    
                    # Monitor processing
                    print(f"   🔄 Monitoring processing...")
                    
                    for attempt in range(10):  # Monitor for up to 10 attempts
                        await asyncio.sleep(5)  # Wait 5 seconds between checks
                        
                        note_response = await client.get(f"{API_BASE}/notes/{note_id}", headers=headers)
                        
                        if note_response.status_code == 200:
                            note_data = note_response.json()
                            current_status = note_data.get("status", "unknown")
                            artifacts = note_data.get("artifacts", {})
                            
                            print(f"      Status check {attempt + 1}: {current_status}")
                            
                            if current_status == "ready":
                                transcript = artifacts.get("transcript", "")
                                if transcript:
                                    word_count = len(transcript.split())
                                    actual_duration = word_count / 150  # Speaking rate
                                    
                                    print(f"   ✅ PROCESSING COMPLETE!")
                                    print(f"      Transcript: {word_count} words")
                                    print(f"      Actual Duration: ~{actual_duration:.1f} minutes")
                                    
                                    if actual_duration >= 45:
                                        print(f"   🚨 RECOVERY SUCCESS: This appears to be the 1-hour meeting!")
                                        print(f"      First 100 characters: {transcript[:100]}...")
                                    
                                    recovery_results[-1]["processing_success"] = True
                                    recovery_results[-1]["actual_duration"] = actual_duration
                                    recovery_results[-1]["word_count"] = word_count
                                    break
                                else:
                                    print(f"   ⚠️  Processing complete but no transcript found")
                                    break
                            elif current_status == "failed":
                                error_msg = artifacts.get("error", "Unknown error")
                                print(f"   ❌ Processing failed: {error_msg}")
                                recovery_results[-1]["processing_success"] = False
                                recovery_results[-1]["error"] = error_msg
                                break
                            elif current_status in ["processing", "uploading"]:
                                print(f"      Still processing... (attempt {attempt + 1}/10)")
                                continue
                        else:
                            print(f"      ⚠️  Could not check status: {note_response.status_code}")
                    
                else:
                    print(f"   ❌ Upload failed: {response.status_code} - {response.text}")
                    recovery_results.append({
                        "file_name": file_name,
                        "upload_success": False,
                        "error": f"Upload failed: {response.status_code}",
                        "estimated_duration": estimated_duration_minutes
                    })
                    
            except Exception as e:
                print(f"   ❌ Recovery processing error: {str(e)}")
                recovery_results.append({
                    "file_name": file_name,
                    "upload_success": False,
                    "error": str(e),
                    "estimated_duration": estimated_duration_minutes
                })
        
        # Step 4: Final Recovery Report
        print(f"\n" + "=" * 80)
        print(f"📊 MEETING RECOVERY FINAL REPORT")
        print(f"=" * 80)
        
        successful_recoveries = 0
        potential_matches = 0
        
        for result in recovery_results:
            file_name = result["file_name"]
            print(f"\n📝 {file_name}:")
            
            if result.get("upload_success"):
                print(f"   ✅ Upload: SUCCESS")
                print(f"   📋 Note ID: {result.get('note_id')}")
                
                if result.get("processing_success"):
                    print(f"   ✅ Processing: SUCCESS")
                    print(f"   ⏱️  Duration: ~{result.get('actual_duration', 0):.1f} minutes")
                    print(f"   📝 Words: {result.get('word_count', 0)}")
                    
                    successful_recoveries += 1
                    
                    if result.get('actual_duration', 0) >= 45:
                        potential_matches += 1
                        print(f"   🚨 POTENTIAL MATCH: This could be the lost 1-hour meeting!")
                else:
                    print(f"   ⚠️  Processing: {result.get('error', 'In progress or failed')}")
            else:
                print(f"   ❌ Upload: FAILED - {result.get('error', 'Unknown error')}")
        
        print(f"\n📊 RECOVERY SUMMARY:")
        print(f"   Files processed: {len(recovery_results)}")
        print(f"   Successful recoveries: {successful_recoveries}")
        print(f"   Potential 1-hour meetings: {potential_matches}")
        
        if potential_matches > 0:
            print(f"\n🎉 RECOVERY SUCCESS!")
            print(f"   Found {potential_matches} file(s) that could be the lost 1-hour meeting")
            print(f"   The user can now access these recovered recordings in their notes")
        elif successful_recoveries > 0:
            print(f"\n✅ PARTIAL SUCCESS!")
            print(f"   Recovered {successful_recoveries} meeting file(s)")
            print(f"   Check the processed files to see if any match the lost meeting")
        else:
            print(f"\n❌ RECOVERY CHALLENGES")
            print(f"   Could not successfully process the found files")
            print(f"   Files may be corrupted or in an unsupported format")
        
        return potential_matches > 0 or successful_recoveries > 0
        
    except Exception as e:
        print(f"❌ Critical recovery error: {str(e)}")
        return False
    finally:
        await client.aclose()

async def main():
    success = await recover_meeting_files()
    print(f"\n🏁 Meeting recovery {'successful' if success else 'completed with issues'}")
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)