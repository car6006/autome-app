#!/usr/bin/env python3
"""
Transcription Jobs Database Investigation
Tests the specific user and job mentioned in the review request
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import os

class TranscriptionJobsInvestigator:
    def __init__(self, base_url="https://autome-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.target_user_id = "a8ad15d9-4409-4168-85c2-9488f7d9b989"
        self.target_job_id = "0757fea2-7dd3-4f8b-aef3-9d03a24a9786"

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authentication header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"message": "Success but no JSON response"}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}")
                except:
                    self.log(f"   Response text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        if success:
            self.log(f"   API Status: {response.get('status', 'N/A')}")
            self.log(f"   Services: {response.get('services', {})}")
        return success

    def authenticate_as_admin(self):
        """Try to authenticate as admin to access job data"""
        # Try to register/login as admin user for testing
        admin_user_data = {
            "email": f"admin_test_{int(time.time())}@admin.com",
            "username": f"adminuser{int(time.time())}",
            "password": "AdminPassword123!",
            "first_name": "Admin",
            "last_name": "User"
        }
        
        success, response = self.run_test(
            "Admin User Registration",
            "POST",
            "auth/register",
            200,
            data=admin_user_data
        )
        
        if success:
            self.auth_token = response.get('access_token')
            user_data = response.get('user', {})
            self.log(f"   Admin user ID: {user_data.get('id')}")
            self.log(f"   Token received: {'Yes' if self.auth_token else 'No'}")
            return True
        return False

    def test_transcriptions_endpoint_general(self):
        """Test the general /api/transcriptions/ endpoint"""
        success, response = self.run_test(
            "List All Transcription Jobs",
            "GET",
            "transcriptions/",
            401  # Should require authentication
        )
        
        if not success and response == {}:
            # Try with authentication
            if self.auth_token:
                success, response = self.run_test(
                    "List Transcription Jobs (Authenticated)",
                    "GET",
                    "transcriptions/",
                    200,
                    auth_required=True
                )
                
                if success:
                    jobs = response.get('jobs', [])
                    total = response.get('total', 0)
                    self.log(f"   Total jobs found: {total}")
                    
                    # Analyze job statuses
                    status_counts = {}
                    user_jobs = {}
                    
                    for job in jobs:
                        status = job.get('status')
                        user_id = job.get('user_id', 'unknown')
                        
                        # Count by status
                        status_counts[status] = status_counts.get(status, 0) + 1
                        
                        # Count by user
                        if user_id not in user_jobs:
                            user_jobs[user_id] = []
                        user_jobs[user_id].append(job)
                    
                    self.log(f"   Job status breakdown: {status_counts}")
                    self.log(f"   Users with jobs: {len(user_jobs)}")
                    
                    # Check for target user
                    if self.target_user_id in user_jobs:
                        target_user_jobs = user_jobs[self.target_user_id]
                        self.log(f"   🎯 Target user {self.target_user_id} has {len(target_user_jobs)} jobs")
                        
                        # Analyze target user's jobs
                        processing_jobs = [j for j in target_user_jobs if j.get('status') == 'processing']
                        self.log(f"   🔄 Active/processing jobs for target user: {len(processing_jobs)}")
                        
                        for job in processing_jobs:
                            self.log(f"      Job ID: {job.get('job_id')}")
                            self.log(f"      Status: {job.get('status')}")
                            self.log(f"      Stage: {job.get('current_stage')}")
                            self.log(f"      Progress: {job.get('progress', 0)}%")
                            self.log(f"      Created: {job.get('created_at')}")
                    else:
                        self.log(f"   ❌ Target user {self.target_user_id} not found in job list")
                    
                    return True, jobs
        
        return False, []

    def test_specific_job_status(self):
        """Test the specific job mentioned in the review request"""
        self.log(f"\n🎯 INVESTIGATING SPECIFIC JOB: {self.target_job_id}")
        
        success, response = self.run_test(
            f"Get Job Status: {self.target_job_id}",
            "GET",
            f"transcriptions/{self.target_job_id}",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Job found!")
            self.log(f"   Job ID: {response.get('job_id')}")
            self.log(f"   Status: {response.get('status')}")
            self.log(f"   Current Stage: {response.get('current_stage')}")
            self.log(f"   Progress: {response.get('progress', 0)}%")
            self.log(f"   Error Code: {response.get('error_code', 'None')}")
            self.log(f"   Error Message: {response.get('error_message', 'None')}")
            
            # Check stage progress
            stage_progress = response.get('stage_progress', {})
            if stage_progress:
                self.log(f"   Stage Progress:")
                for stage, progress in stage_progress.items():
                    self.log(f"      {stage}: {progress}%")
            
            # Check durations
            durations = response.get('durations', {})
            if durations:
                self.log(f"   Stage Durations:")
                for stage, duration in durations.items():
                    self.log(f"      {stage}: {duration}s")
            
            # Check if job is stuck
            status = response.get('status')
            current_stage = response.get('current_stage')
            progress = response.get('progress', 0)
            
            if status == 'processing' and progress == 0:
                self.log(f"   ⚠️  POTENTIAL ISSUE: Job stuck in processing with 0% progress")
            elif status == 'processing' and current_stage == 'created':
                self.log(f"   ⚠️  POTENTIAL ISSUE: Job processing but still in 'created' stage")
            elif status == 'failed':
                self.log(f"   ❌ Job has failed - this could be blocking concurrent limit")
            
            return True, response
        else:
            self.log(f"   ❌ Job not found or access denied")
            return False, {}

    def test_concurrent_job_limits(self):
        """Check for jobs that might be blocking concurrent limits"""
        self.log(f"\n🔍 CHECKING FOR STUCK JOBS BLOCKING CONCURRENT LIMITS")
        
        # Get all jobs
        success, response = self.run_test(
            "List All Jobs for Concurrent Analysis",
            "GET",
            "transcriptions/",
            200,
            auth_required=True
        )
        
        if not success:
            return False
        
        jobs = response.get('jobs', [])
        
        # Analyze jobs by status
        processing_jobs = [j for j in jobs if j.get('status') == 'processing']
        created_jobs = [j for j in jobs if j.get('status') == 'created']
        failed_jobs = [j for j in jobs if j.get('status') == 'failed']
        
        self.log(f"   📊 Job Status Summary:")
        self.log(f"      Processing: {len(processing_jobs)}")
        self.log(f"      Created: {len(created_jobs)}")
        self.log(f"      Failed: {len(failed_jobs)}")
        
        # Check for stuck processing jobs
        stuck_jobs = []
        current_time = datetime.now(timezone.utc)
        
        for job in processing_jobs:
            created_at_str = job.get('created_at')
            if created_at_str:
                try:
                    # Parse the datetime string
                    if isinstance(created_at_str, str):
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    else:
                        created_at = created_at_str
                    
                    # Check if job has been processing for more than 1 hour
                    time_diff = current_time - created_at
                    if time_diff.total_seconds() > 3600:  # 1 hour
                        stuck_jobs.append({
                            'job': job,
                            'stuck_duration': time_diff.total_seconds() / 3600  # hours
                        })
                except Exception as e:
                    self.log(f"      ⚠️  Could not parse created_at for job {job.get('job_id')}: {e}")
        
        if stuck_jobs:
            self.log(f"   🚨 FOUND {len(stuck_jobs)} POTENTIALLY STUCK JOBS:")
            for stuck in stuck_jobs:
                job = stuck['job']
                duration = stuck['stuck_duration']
                self.log(f"      Job ID: {job.get('job_id')}")
                self.log(f"      User ID: {job.get('user_id', 'unknown')}")
                self.log(f"      Status: {job.get('status')}")
                self.log(f"      Stage: {job.get('current_stage')}")
                self.log(f"      Progress: {job.get('progress', 0)}%")
                self.log(f"      Stuck for: {duration:.1f} hours")
                self.log(f"      ---")
        else:
            self.log(f"   ✅ No stuck jobs found")
        
        # Check for target user specifically
        target_user_jobs = [j for j in jobs if j.get('user_id') == self.target_user_id]
        if target_user_jobs:
            self.log(f"\n   🎯 TARGET USER {self.target_user_id} ANALYSIS:")
            
            target_processing = [j for j in target_user_jobs if j.get('status') == 'processing']
            target_created = [j for j in target_user_jobs if j.get('status') == 'created']
            
            self.log(f"      Total jobs: {len(target_user_jobs)}")
            self.log(f"      Processing: {len(target_processing)}")
            self.log(f"      Created: {len(target_created)}")
            
            if len(target_processing) > 1:
                self.log(f"      ⚠️  Multiple processing jobs detected - potential concurrent limit issue")
            
            for job in target_processing:
                self.log(f"         Processing Job: {job.get('job_id')} - Stage: {job.get('current_stage')} - Progress: {job.get('progress', 0)}%")
        
        return True

    def test_cleanup_stuck_jobs(self):
        """Test the cleanup endpoint for stuck jobs"""
        self.log(f"\n🧹 TESTING STUCK JOBS CLEANUP")
        
        success, response = self.run_test(
            "Cleanup Stuck Jobs",
            "POST",
            "transcriptions/cleanup",
            200,
            auth_required=True
        )
        
        if success:
            fixed_count = response.get('fixed_count', 0)
            message = response.get('message', '')
            self.log(f"   ✅ Cleanup completed: {message}")
            self.log(f"   Fixed jobs: {fixed_count}")
            
            if fixed_count > 0:
                self.log(f"   🔧 {fixed_count} stuck jobs were fixed")
            else:
                self.log(f"   ✅ No stuck jobs found to fix")
            
            return True
        else:
            self.log(f"   ❌ Cleanup failed")
            return False

    def test_database_direct_query(self):
        """Test direct database queries if possible"""
        self.log(f"\n💾 ATTEMPTING DIRECT DATABASE ANALYSIS")
        
        try:
            # Try to connect to MongoDB directly
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            import os
            
            # Get MongoDB URL from environment
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'auto_me_db')
            
            async def query_database():
                client = AsyncIOMotorClient(mongo_url)
                db = client[db_name]
                
                # Query transcription jobs collection
                jobs_collection = db["transcription_jobs"]
                
                # Count total jobs
                total_jobs = await jobs_collection.count_documents({})
                self.log(f"   📊 Total transcription jobs in database: {total_jobs}")
                
                # Count by status
                statuses = ['created', 'processing', 'complete', 'failed', 'cancelled']
                for status in statuses:
                    count = await jobs_collection.count_documents({"status": status})
                    if count > 0:
                        self.log(f"      {status}: {count}")
                
                # Check target user specifically
                user_jobs = await jobs_collection.count_documents({"user_id": self.target_user_id})
                self.log(f"   🎯 Target user {self.target_user_id} jobs: {user_jobs}")
                
                if user_jobs > 0:
                    # Get details of target user's jobs
                    cursor = jobs_collection.find({"user_id": self.target_user_id})
                    user_job_list = await cursor.to_list(length=None)
                    
                    processing_count = 0
                    for job in user_job_list:
                        if job.get('status') == 'processing':
                            processing_count += 1
                            self.log(f"      Processing job: {job.get('id')} - Stage: {job.get('current_stage')} - Progress: {job.get('progress', 0)}%")
                    
                    self.log(f"   🔄 Active/processing jobs for target user: {processing_count}")
                
                # Check specific job
                target_job = await jobs_collection.find_one({"id": self.target_job_id})
                if target_job:
                    self.log(f"   🎯 Target job {self.target_job_id} found:")
                    self.log(f"      Status: {target_job.get('status')}")
                    self.log(f"      Stage: {target_job.get('current_stage')}")
                    self.log(f"      Progress: {target_job.get('progress', 0)}%")
                    self.log(f"      User ID: {target_job.get('user_id')}")
                    self.log(f"      Created: {target_job.get('created_at')}")
                    self.log(f"      Updated: {target_job.get('updated_at')}")
                    
                    if target_job.get('error_message'):
                        self.log(f"      Error: {target_job.get('error_message')}")
                else:
                    self.log(f"   ❌ Target job {self.target_job_id} not found in database")
                
                client.close()
                return True
            
            # Run the async query
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(query_database())
            loop.close()
            
            return result
            
        except Exception as e:
            self.log(f"   ❌ Direct database query failed: {str(e)}")
            return False

    def run_investigation(self):
        """Run the complete investigation"""
        self.log("🔍 TRANSCRIPTION JOBS DATABASE INVESTIGATION")
        self.log("=" * 60)
        
        # Test 1: Health Check
        if not self.test_health_check():
            self.log("❌ System health check failed - aborting investigation")
            return False
        
        # Test 2: Authentication
        if not self.authenticate_as_admin():
            self.log("❌ Could not authenticate - some tests may be limited")
        
        # Test 3: General transcriptions endpoint
        self.test_transcriptions_endpoint_general()
        
        # Test 4: Specific job status
        self.test_specific_job_status()
        
        # Test 5: Concurrent job limits analysis
        self.test_concurrent_job_limits()
        
        # Test 6: Cleanup stuck jobs
        self.test_cleanup_stuck_jobs()
        
        # Test 7: Direct database query (if possible)
        self.test_database_direct_query()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📋 INVESTIGATION SUMMARY")
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return True

if __name__ == "__main__":
    investigator = TranscriptionJobsInvestigator()
    success = investigator.run_investigation()
    
    if success:
        print("\n✅ Investigation completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Investigation failed")
        sys.exit(1)