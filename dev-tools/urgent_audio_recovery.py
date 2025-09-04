#!/usr/bin/env python3
"""
URGENT: Lightweight Audio Recovery Investigation
Critical data recovery for lost 1-hour meeting voice note recording.
"""

import asyncio
import httpx
import json
import os
import time
from datetime import datetime, timezone

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://autome-ai.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def investigate_lost_meeting():
    """Lightweight investigation for lost meeting recording"""
    print("🚨 URGENT: AUDIO RECOVERY INVESTIGATION")
    print("Searching for lost 1-hour meeting voice note recording...")
    print("=" * 80)
    
    client = httpx.AsyncClient(timeout=60.0)
    
    try:
        # Step 1: Register test user for investigation
        test_email = f"urgent{int(time.time())}@expeditors.com"
        
        response = await client.post(f"{API_BASE}/auth/register", json={
            "email": test_email,
            "password": "UrgentRecovery123!",
            "username": f"urgent{int(time.time())}",
            "name": "Urgent Recovery User"
        })
        
        if response.status_code not in [200, 201]:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
        
        auth_data = response.json()
        auth_token = auth_data.get("access_token")
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        print(f"✅ Authentication successful")
        
        # Step 2: Search for recent audio notes
        print("\n🔍 Searching for recent audio notes...")
        
        response = await client.get(f"{API_BASE}/notes?limit=50", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to retrieve notes: {response.status_code}")
            return False
        
        notes = response.json()
        audio_notes = [note for note in notes if note.get("kind") == "audio"]
        
        print(f"📊 Found {len(audio_notes)} audio notes out of {len(notes)} total notes")
        
        # Step 3: Analyze audio notes for meeting patterns
        meeting_candidates = []
        stuck_files = []
        large_files = []
        
        current_time = datetime.now(timezone.utc)
        
        for note in audio_notes:
            note_id = note.get("id")
            title = note.get("title", "Untitled")
            status = note.get("status", "unknown")
            created_at = note.get("created_at", "")
            artifacts = note.get("artifacts", {})
            
            print(f"\n📝 Audio Note: {title}")
            print(f"   ID: {note_id}")
            print(f"   Status: {status}")
            print(f"   Created: {created_at}")
            
            # Calculate age
            try:
                if created_at:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    hours_ago = (current_time - created_time).total_seconds() / 3600
                    print(f"   Age: {hours_ago:.1f} hours ago")
                else:
                    hours_ago = 999
            except:
                hours_ago = 999
            
            # Check for meeting keywords
            meeting_keywords = ["meeting", "conference", "call", "discussion", "session"]
            is_meeting = any(keyword in title.lower() for keyword in meeting_keywords)
            
            # Check transcript for duration estimation
            transcript = artifacts.get("transcript", "")
            estimated_duration = 0
            if transcript:
                word_count = len(transcript.split())
                estimated_duration = word_count / 150  # Average speaking rate
                print(f"   Transcript: {word_count} words (~{estimated_duration:.1f} minutes)")
            
            # Scoring system for meeting likelihood
            score = 0
            
            # Recent creation (within 24 hours)
            if hours_ago <= 1:
                score += 5
            elif hours_ago <= 6:
                score += 3
            elif hours_ago <= 24:
                score += 1
            
            # Meeting keywords
            if is_meeting:
                score += 3
                print(f"   🎯 MEETING KEYWORD DETECTED")
            
            # Status issues (stuck/failed)
            if status == "processing":
                score += 4
                stuck_files.append(note)
                print(f"   ⚠️  STUCK IN PROCESSING")
            elif status == "failed":
                score += 5
                print(f"   ❌ FAILED PROCESSING")
            elif status == "uploading":
                score += 3
                stuck_files.append(note)
                print(f"   ⚠️  STUCK UPLOADING")
            
            # Large file (close to 1 hour)
            if estimated_duration >= 45:
                score += 5
                large_files.append(note)
                print(f"   🎯 LARGE FILE: ~{estimated_duration:.1f} minutes - POTENTIAL MATCH!")
            elif estimated_duration >= 30:
                score += 2
            
            if score >= 5:
                meeting_candidates.append({
                    "note": note,
                    "score": score,
                    "hours_ago": hours_ago,
                    "estimated_duration": estimated_duration,
                    "is_meeting": is_meeting
                })
                print(f"   🚨 HIGH PROBABILITY CANDIDATE (Score: {score})")
        
        # Step 4: Report findings
        print(f"\n" + "=" * 80)
        print(f"📊 RECOVERY INVESTIGATION RESULTS")
        print(f"=" * 80)
        
        print(f"📊 Total audio notes: {len(audio_notes)}")
        print(f"⚠️  Files stuck in processing: {len(stuck_files)}")
        print(f"📏 Large files (>45 min): {len(large_files)}")
        print(f"🎯 Meeting candidates: {len(meeting_candidates)}")
        
        # Sort candidates by score
        meeting_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        if meeting_candidates:
            print(f"\n🎯 TOP CANDIDATES FOR LOST MEETING:")
            for i, candidate in enumerate(meeting_candidates[:3], 1):
                note = candidate["note"]
                print(f"\n{i}. {note.get('title', 'Untitled')} (Score: {candidate['score']})")
                print(f"   Status: {note.get('status')}")
                print(f"   Duration: ~{candidate['estimated_duration']:.1f} minutes")
                print(f"   Age: {candidate['hours_ago']:.1f} hours ago")
                print(f"   ID: {note.get('id')}")
                
                if candidate["score"] >= 8:
                    print(f"   🚨 VERY HIGH PROBABILITY - This is likely the lost meeting!")
        
        if stuck_files:
            print(f"\n⚠️  STUCK FILES REQUIRING ATTENTION:")
            for stuck in stuck_files:
                print(f"   - {stuck.get('title', 'Untitled')} (Status: {stuck.get('status')})")
                print(f"     ID: {stuck.get('id')}")
        
        # Step 5: Recommendations
        print(f"\n💡 RECOVERY RECOMMENDATIONS:")
        
        if meeting_candidates:
            print(f"✅ Found {len(meeting_candidates)} potential matches")
            print(f"   → Check the top candidates listed above")
            
            if large_files:
                print(f"📏 {len(large_files)} large files detected - most likely candidates")
                
            if stuck_files:
                print(f"⚠️  {len(stuck_files)} files stuck in processing")
                print(f"   → These may contain the lost meeting - manual recovery needed")
        else:
            print(f"❌ No obvious candidates found")
            print(f"   → Meeting may have failed to upload completely")
            print(f"   → Check device storage and browser cache")
        
        return len(meeting_candidates) > 0
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        return False
    finally:
        await client.aclose()

async def main():
    success = await investigate_lost_meeting()
    print(f"\n🏁 Investigation {'found potential matches' if success else 'completed - no matches found'}")
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)