#!/usr/bin/env python3
"""
Delete the specific stuck transcription job
"Regional Meeting 21 August - Recap Session 1.mp3"
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def delete_stuck_job():
    """Delete the specific stuck job"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # The specific job ID found in the search
    target_job_id = "8ab8b1e8-b74e-45eb-a1e1-278d62281709"
    
    print("🎯 DELETING STUCK TRANSCRIPTION JOB")
    print("=" * 50)
    print(f"Job ID: {target_job_id}")
    print(f"Title: Regional Meeting 21 August - Recap Session 1.mp3")
    print(f"Status: uploading (stuck)")
    print()
    
    # First, verify the job exists and get its details
    job = await db["notes"].find_one({"id": target_job_id})
    
    if not job:
        print("❌ Job not found - may have already been deleted")
        return False
    
    print("📋 Job Details Before Deletion:")
    print(f"   Title: {job.get('title', 'N/A')}")
    print(f"   Status: {job.get('status', 'N/A')}")
    print(f"   Kind: {job.get('kind', 'N/A')}")
    print(f"   Created: {job.get('created_at', 'N/A')}")
    print(f"   User ID: {job.get('user_id', 'N/A')}")
    print(f"   Media Key: {job.get('media_key', 'N/A')}")
    print()
    
    # Check if this is indeed the problematic job
    title = job.get('title', '')
    if not ("Regional Meeting" in title and "21 August" in title and "Recap Session 1" in title):
        print("⚠️  WARNING: This doesn't appear to be the exact job mentioned in the review request")
        print(f"   Expected: 'Regional Meeting 21 August - Recap Session 1.mp3'")
        print(f"   Found: '{title}'")
        print()
    
    # Delete the job
    print("🗑️  Deleting the stuck job...")
    result = await db["notes"].delete_one({"id": target_job_id})
    
    if result.deleted_count > 0:
        print("✅ SUCCESS: Stuck transcription job deleted!")
        print()
        print("📝 SUMMARY:")
        print("   - The problematic transcription job has been removed from the database")
        print("   - The job was stuck in 'uploading' status and failing with OpenAI 400 errors")
        print("   - User can now try uploading a different audio file")
        print("   - The system is ready to accept new transcription jobs")
        print()
        print("💡 RECOMMENDATION FOR USER:")
        print("   - Try uploading a different audio file with better quality")
        print("   - Ensure the audio file is in a supported format (MP3, WAV, M4A, WebM, OGG)")
        print("   - Check that the audio file is not corrupted")
        print("   - Consider using a shorter audio file for testing")
        
        return True
    else:
        print("❌ FAILED: Could not delete the job")
        print("   The job may have been deleted by another process")
        return False
    
    await client.close()

async def verify_deletion():
    """Verify the job has been deleted"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    target_job_id = "8ab8b1e8-b74e-45eb-a1e1-278d62281709"
    
    print("\n🔍 VERIFICATION: Checking if job was deleted...")
    
    job = await db["notes"].find_one({"id": target_job_id})
    
    if job is None:
        print("✅ VERIFIED: Job has been successfully deleted")
        return True
    else:
        print("❌ VERIFICATION FAILED: Job still exists in database")
        print(f"   Current status: {job.get('status', 'N/A')}")
        return False
    
    await client.close()

async def main():
    """Main function"""
    print("🚨 STUCK TRANSCRIPTION JOB CLEANUP UTILITY")
    print("=" * 60)
    print("Target: 'Regional Meeting 21 August - Recap Session 1.mp3'")
    print("Issue: Job stuck with OpenAI 400 errors during transcription")
    print("Action: Delete the stuck job to allow user to try again")
    print()
    
    try:
        # Delete the stuck job
        success = await delete_stuck_job()
        
        if success:
            # Verify deletion
            verified = await verify_deletion()
            
            if verified:
                print("\n🎉 MISSION ACCOMPLISHED!")
                print("   The stuck transcription job has been successfully removed.")
                print("   The user can now upload a different audio file.")
                return True
            else:
                print("\n⚠️  Deletion may not have completed properly.")
                return False
        else:
            print("\n❌ Failed to delete the stuck job.")
            return False
    
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(main())