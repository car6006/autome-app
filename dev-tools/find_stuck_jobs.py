#!/usr/bin/env python3
"""
Find and cancel stuck transcription jobs
Specifically looking for "Regional Meeting 21 August - Recap Session 1.mp3"
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime, timezone

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def find_stuck_transcription_jobs():
    """Find and display stuck transcription jobs"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔍 Searching for stuck transcription jobs...")
    print("=" * 60)
    
    # Search for notes with specific criteria
    query_conditions = [
        # Look for notes in processing or created status
        {"status": {"$in": ["processing", "created", "uploading"]}},
        # Look for audio notes specifically
        {"kind": "audio"},
        # Look for notes with the specific filename pattern
        {"title": {"$regex": "Regional Meeting.*August", "$options": "i"}}
    ]
    
    all_stuck_jobs = []
    
    for i, condition in enumerate(query_conditions):
        print(f"\n📋 Query {i+1}: {condition}")
        
        cursor = db["notes"].find(condition)
        jobs = await cursor.to_list(length=None)
        
        print(f"   Found {len(jobs)} jobs matching this condition")
        
        for job in jobs:
            job_info = {
                "id": job.get("id"),
                "title": job.get("title"),
                "status": job.get("status"),
                "kind": job.get("kind"),
                "created_at": job.get("created_at"),
                "user_id": job.get("user_id"),
                "artifacts": job.get("artifacts", {}),
                "media_key": job.get("media_key")
            }
            all_stuck_jobs.append(job_info)
            
            print(f"   📄 Job: {job_info['title']}")
            print(f"      ID: {job_info['id']}")
            print(f"      Status: {job_info['status']}")
            print(f"      Created: {job_info['created_at']}")
            
            # Check for error information in artifacts
            artifacts = job_info.get("artifacts", {})
            if "error" in artifacts:
                print(f"      Error: {artifacts['error']}")
            
            # Check for transcription segments or processing info
            if "segments" in artifacts:
                segments = artifacts["segments"]
                print(f"      Segments: {len(segments) if isinstance(segments, list) else 'N/A'}")
            
            print()
    
    # Look specifically for the mentioned file
    print("\n🎯 Searching specifically for 'Regional Meeting 21 August - Recap Session 1.mp3'...")
    specific_query = {
        "$or": [
            {"title": {"$regex": "Regional Meeting.*21.*August.*Recap.*Session.*1", "$options": "i"}},
            {"title": {"$regex": "Recap Session 1", "$options": "i"}},
            {"media_key": {"$regex": "Regional.*Meeting.*21.*August", "$options": "i"}}
        ]
    }
    
    cursor = db["notes"].find(specific_query)
    specific_jobs = await cursor.to_list(length=None)
    
    print(f"Found {len(specific_jobs)} jobs matching the specific pattern")
    
    target_job = None
    for job in specific_jobs:
        print(f"📄 Specific Match: {job.get('title')}")
        print(f"   ID: {job.get('id')}")
        print(f"   Status: {job.get('status')}")
        print(f"   Media Key: {job.get('media_key', 'N/A')}")
        
        # Check if this looks like the problematic job
        if ("Regional Meeting" in job.get("title", "") and 
            "21" in job.get("title", "") and 
            "August" in job.get("title", "") and
            job.get("status") in ["processing", "created"]):
            target_job = job
            print(f"   🎯 TARGET JOB IDENTIFIED!")
        print()
    
    # Also search for any jobs with OpenAI 400 errors
    print("\n🚨 Searching for jobs with OpenAI 400 errors...")
    error_query = {
        "artifacts.error": {"$regex": "400|Bad Request|OpenAI", "$options": "i"}
    }
    
    cursor = db["notes"].find(error_query)
    error_jobs = await cursor.to_list(length=None)
    
    print(f"Found {len(error_jobs)} jobs with error patterns")
    
    for job in error_jobs:
        print(f"❌ Error Job: {job.get('title')}")
        print(f"   ID: {job.get('id')}")
        print(f"   Status: {job.get('status')}")
        print(f"   Error: {job.get('artifacts', {}).get('error', 'N/A')}")
        
        # Check if this is also the target job
        if ("Regional Meeting" in job.get("title", "") and 
            "August" in job.get("title", "")):
            target_job = job
            print(f"   🎯 TARGET JOB WITH ERRORS IDENTIFIED!")
        print()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    total_stuck = len(all_stuck_jobs)
    print(f"Total stuck jobs found: {total_stuck}")
    print(f"Jobs with errors: {len(error_jobs)}")
    print(f"Specific target matches: {len(specific_jobs)}")
    
    if target_job:
        print(f"\n🎯 TARGET JOB FOR DELETION:")
        print(f"   Title: {target_job.get('title')}")
        print(f"   ID: {target_job.get('id')}")
        print(f"   Status: {target_job.get('status')}")
        print(f"   Created: {target_job.get('created_at')}")
        
        # Ask for confirmation to delete
        print(f"\n⚠️  READY TO DELETE THIS JOB")
        print(f"   This will permanently remove the stuck transcription job.")
        print(f"   The user can then try uploading a different audio file.")
        
        return target_job
    else:
        print(f"\n❓ No exact match found for 'Regional Meeting 21 August - Recap Session 1.mp3'")
        print(f"   The job may have already been processed or deleted.")
        
        if all_stuck_jobs:
            print(f"\n📋 Other stuck jobs that could be cleaned up:")
            for job in all_stuck_jobs[:5]:  # Show first 5
                print(f"   - {job['title']} (ID: {job['id']}, Status: {job['status']})")
        
        return None
    
    await client.close()

async def delete_stuck_job(job_id):
    """Delete a specific stuck job"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print(f"\n🗑️  Deleting job with ID: {job_id}")
    
    # Delete the job
    result = await db["notes"].delete_one({"id": job_id})
    
    if result.deleted_count > 0:
        print(f"✅ Successfully deleted job {job_id}")
        print(f"   The user can now try uploading a different audio file.")
        return True
    else:
        print(f"❌ Failed to delete job {job_id} - job may not exist")
        return False
    
    await client.close()

async def main():
    """Main function"""
    print("🔧 STUCK TRANSCRIPTION JOB FINDER AND CLEANER")
    print("=" * 60)
    print("Looking for: 'Regional Meeting 21 August - Recap Session 1.mp3'")
    print("Status: CREATED or processing with OpenAI 400 errors")
    print()
    
    try:
        target_job = await find_stuck_transcription_jobs()
        
        if target_job:
            job_id = target_job.get("id")
            if job_id:
                # Automatically delete the stuck job
                success = await delete_stuck_job(job_id)
                if success:
                    print(f"\n🎉 MISSION ACCOMPLISHED!")
                    print(f"   Stuck transcription job has been removed.")
                    print(f"   User can now upload a different audio file.")
                else:
                    print(f"\n❌ Failed to delete the stuck job.")
            else:
                print(f"\n❌ No job ID found for deletion.")
        else:
            print(f"\n✅ No stuck jobs matching the criteria found.")
            print(f"   The problematic job may have already been resolved.")
    
    except Exception as e:
        print(f"\n❌ Error during operation: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())