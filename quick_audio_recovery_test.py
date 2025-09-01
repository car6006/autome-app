#!/usr/bin/env python3
"""
QUICK AUDIO RECOVERY TEST - September 1, 2025
Focused search for today's audio files with immediate results
"""

import os
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
import stat

# Today's date
TODAY = datetime.now(timezone.utc).date()
print(f"🚨 URGENT AUDIO RECOVERY - September 1, 2025")
print(f"🔍 Searching for files created/modified TODAY: {TODAY}")
print("=" * 60)

def check_file_timestamps():
    """Quick check of file system for today's audio files"""
    print("📁 STEP 1: Scanning file system for audio files from TODAY...")
    
    # Storage locations to check
    locations = [
        "/tmp/autome_storage",
        "/app/uploads", 
        "/tmp",
        "/var/tmp",
        "/app/backend",
        "/app"
    ]
    
    audio_extensions = [".mp3", ".wav", ".m4a", ".webm", ".ogg", ".mpeg", ".aac"]
    found_files = []
    
    for location in locations:
        if os.path.exists(location):
            print(f"   Checking: {location}")
            
            try:
                # Check all files in directory
                for root, dirs, files in os.walk(location):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Check if it's an audio file
                        if any(file.lower().endswith(ext) for ext in audio_extensions):
                            try:
                                stat_info = os.stat(file_path)
                                created = datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc)
                                modified = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
                                
                                # Check if from today
                                if created.date() == TODAY or modified.date() == TODAY:
                                    size = stat_info.st_size
                                    
                                    print(f"   🎵 FOUND AUDIO FILE FROM TODAY:")
                                    print(f"      Path: {file_path}")
                                    print(f"      Size: {size} bytes")
                                    print(f"      Created: {created}")
                                    print(f"      Modified: {modified}")
                                    
                                    found_files.append({
                                        "path": file_path,
                                        "size": size,
                                        "created": created.isoformat(),
                                        "modified": modified.isoformat(),
                                        "filename": file
                                    })
                                    
                            except Exception as e:
                                print(f"      Error checking {file_path}: {e}")
                                
            except Exception as e:
                print(f"   Error scanning {location}: {e}")
        else:
            print(f"   Directory not found: {location}")
    
    return found_files

def check_database_files():
    """Check for database-related files from today"""
    print("\n📊 STEP 2: Checking for database/log files from TODAY...")
    
    db_locations = [
        "/var/log/supervisor/*.log",
        "/app/*.log",
        "/tmp/*.log"
    ]
    
    today_entries = []
    
    for pattern in db_locations:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                stat_info = os.stat(file_path)
                modified = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
                
                if modified.date() == TODAY:
                    print(f"   📋 Log file from today: {file_path}")
                    
                    # Check for audio-related content
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        audio_keywords = ["audio", "upload", "transcription", "wav", "mp3"]
                        if any(keyword in content.lower() for keyword in audio_keywords):
                            print(f"      ✅ Contains audio-related entries!")
                            today_entries.append(file_path)
                        
                    except Exception as e:
                        print(f"      Error reading file: {e}")
                        
            except Exception as e:
                print(f"   Error checking {file_path}: {e}")
    
    return today_entries

def check_recent_processes():
    """Check for any recent audio processing"""
    print("\n🔄 STEP 3: Checking for recent audio processing activity...")
    
    try:
        # Check supervisor logs for backend activity
        supervisor_logs = glob.glob("/var/log/supervisor/backend*.log")
        
        for log_file in supervisor_logs:
            print(f"   Checking supervisor log: {log_file}")
            
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Get recent lines (last 100)
                recent_lines = lines[-100:] if len(lines) > 100 else lines
                
                for line in recent_lines:
                    if any(keyword in line.lower() for keyword in ["audio", "upload", "transcription", "processing"]):
                        print(f"      📋 Recent activity: {line.strip()}")
                        
            except Exception as e:
                print(f"      Error reading log: {e}")
                
    except Exception as e:
        print(f"   Error checking processes: {e}")

def main():
    """Main recovery function"""
    print("🚀 Starting quick audio recovery scan...")
    
    # Step 1: Check file system
    audio_files = check_file_timestamps()
    
    # Step 2: Check database/log files  
    log_files = check_database_files()
    
    # Step 3: Check recent processes
    check_recent_processes()
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 RECOVERY SUMMARY")
    print("=" * 60)
    
    print(f"📅 Search Date: {TODAY} (September 1, 2025)")
    print(f"🕐 Search Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
    print(f"🎵 Audio Files Found: {len(audio_files)}")
    print(f"📋 Relevant Log Files: {len(log_files)}")
    
    if audio_files:
        print(f"\n🎉 SUCCESS: Found {len(audio_files)} audio files from TODAY!")
        print("📋 DETAILED FINDINGS:")
        
        for i, file_info in enumerate(audio_files, 1):
            print(f"   {i}. {file_info['filename']}")
            print(f"      Path: {file_info['path']}")
            print(f"      Size: {file_info['size']} bytes")
            print(f"      Created: {file_info['created']}")
            print(f"      Modified: {file_info['modified']}")
        
        # Save results
        report = {
            "search_date": TODAY.isoformat(),
            "search_timestamp": datetime.now(timezone.utc).isoformat(),
            "audio_files_found": audio_files,
            "log_files_found": log_files
        }
        
        try:
            with open(f"/tmp/quick_recovery_report_{TODAY.strftime('%Y%m%d')}.json", 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n💾 Report saved to: /tmp/quick_recovery_report_{TODAY.strftime('%Y%m%d')}.json")
        except Exception as e:
            print(f"\n❌ Failed to save report: {e}")
        
        return True
    else:
        print(f"\n❌ NO AUDIO FILES FOUND from TODAY ({TODAY})")
        print("   Possible reasons:")
        print("   - No recordings were made today")
        print("   - Files were already processed and moved")
        print("   - Files are in a different storage location")
        print("   - Files were deleted after processing")
        
        return False

if __name__ == "__main__":
    success = main()
    
    print(f"\n🏁 Recovery scan completed: {'SUCCESS' if success else 'NO FILES FOUND'}")
    exit(0 if success else 1)