#!/usr/bin/env python3
"""
Direct Chunking Function Tests
Tests the chunking functions directly to verify they work as expected
"""

import sys
import os
import tempfile
import subprocess
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')

from providers import get_audio_duration, split_audio_file, OPENAI_MAX_FILE_SIZE, CHUNK_DURATION_SECONDS

async def test_chunking_functions():
    """Test the chunking functions directly"""
    print("🧪 Testing chunking functions directly...")
    
    temp_files = []
    
    try:
        # Create a test audio file (10 minutes = should create 2 chunks)
        print("📁 Creating test audio file...")
        fd, test_audio = tempfile.mkstemp(suffix='_direct_test.wav')
        os.close(fd)
        temp_files.append(test_audio)
        
        # Generate 10 minutes of audio
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=600',
            '-ar', '16000', '-ac', '1', '-y', test_audio
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Failed to create test audio: {result.stderr}")
            return False
        
        file_size = os.path.getsize(test_audio)
        print(f"✅ Created test audio: {file_size / (1024*1024):.1f} MB")
        
        # Test 1: get_audio_duration
        print("\n🕐 Testing get_audio_duration...")
        duration = await get_audio_duration(test_audio)
        print(f"   Detected duration: {duration:.1f} seconds")
        
        if 590 <= duration <= 610:  # Should be around 600 seconds
            print("✅ Duration detection working correctly")
        else:
            print(f"❌ Duration detection failed - expected ~600s, got {duration:.1f}s")
            return False
        
        # Test 2: split_audio_file
        print("\n✂️  Testing split_audio_file...")
        chunks = await split_audio_file(test_audio, CHUNK_DURATION_SECONDS)
        
        print(f"   Created {len(chunks)} chunks")
        
        expected_chunks = 2  # 600 seconds / 300 seconds per chunk = 2 chunks
        if len(chunks) == expected_chunks:
            print(f"✅ Correct number of chunks created ({len(chunks)})")
        else:
            print(f"⚠️  Expected {expected_chunks} chunks, got {len(chunks)}")
        
        # Verify each chunk exists and has reasonable size
        for i, chunk_path in enumerate(chunks):
            if os.path.exists(chunk_path):
                chunk_size = os.path.getsize(chunk_path)
                chunk_duration = await get_audio_duration(chunk_path)
                print(f"   Chunk {i+1}: {chunk_size / (1024*1024):.1f} MB, {chunk_duration:.1f}s")
                temp_files.append(chunk_path)
            else:
                print(f"❌ Chunk {i+1} file not found: {chunk_path}")
                return False
        
        # Test 3: File size detection logic
        print("\n📏 Testing file size detection logic...")
        
        if file_size > OPENAI_MAX_FILE_SIZE:
            print(f"✅ Large file detected correctly ({file_size / (1024*1024):.1f} MB > {OPENAI_MAX_FILE_SIZE / (1024*1024):.1f} MB)")
        else:
            print(f"ℹ️  File size {file_size / (1024*1024):.1f} MB is under limit {OPENAI_MAX_FILE_SIZE / (1024*1024):.1f} MB")
        
        # Test 4: Constants verification
        print("\n🔧 Testing constants...")
        print(f"   OPENAI_MAX_FILE_SIZE: {OPENAI_MAX_FILE_SIZE / (1024*1024):.1f} MB")
        print(f"   CHUNK_DURATION_SECONDS: {CHUNK_DURATION_SECONDS} seconds ({CHUNK_DURATION_SECONDS/60:.1f} minutes)")
        
        if OPENAI_MAX_FILE_SIZE == 24 * 1024 * 1024:
            print("✅ File size limit set correctly (24MB)")
        else:
            print("❌ File size limit incorrect")
            return False
        
        if CHUNK_DURATION_SECONDS == 300:
            print("✅ Chunk duration set correctly (5 minutes)")
        else:
            print("❌ Chunk duration incorrect")
            return False
        
        print("\n🎉 All direct chunking function tests passed!")
        return True
        
    except Exception as e:
        print(f"💥 Error during direct testing: {e}")
        return False
    
    finally:
        # Clean up
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    print(f"🧹 Cleaned up: {temp_file}")
            except Exception as e:
                print(f"⚠️  Failed to clean up {temp_file}: {e}")

async def main():
    """Main test execution"""
    print("🚀 Starting Direct Chunking Function Tests")
    
    success = await test_chunking_functions()
    
    if success:
        print("\n✅ All direct function tests passed!")
        return 0
    else:
        print("\n❌ Some direct function tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))