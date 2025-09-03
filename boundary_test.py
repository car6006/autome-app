#!/usr/bin/env python3
"""
Boundary Condition Test for 25MB Limit
Tests files right at the 24MB/25MB boundary
"""

import requests
import sys
import tempfile
import os
import subprocess
import time
from datetime import datetime

class BoundaryTester:
    def __init__(self, base_url="https://autome-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.temp_files = []
        self.created_notes = []

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    self.log(f"Cleaned up: {temp_file}")
            except Exception as e:
                self.log(f"Failed to clean up {temp_file}: {e}")

    def create_audio_file_target_size(self, target_mb: float, suffix: str = "") -> str:
        """Create an audio file targeting a specific size in MB"""
        try:
            # Estimate duration needed (roughly 2MB per minute for our settings)
            estimated_duration = int(target_mb * 30)  # Rough estimate
            
            fd, temp_path = tempfile.mkstemp(suffix=f'_boundary_{suffix}.wav')
            os.close(fd)
            self.temp_files.append(temp_path)
            
            # Generate audio
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', f'sine=frequency=440:duration={estimated_duration}',
                '-ar', '16000', '-ac', '1', '-y', temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                file_size = os.path.getsize(temp_path)
                actual_mb = file_size / (1024 * 1024)
                self.log(f"Created {suffix} audio: {actual_mb:.1f} MB (target: {target_mb:.1f} MB)")
                return temp_path
            else:
                self.log(f"Failed to create {suffix} audio: {result.stderr}")
                return None
                
        except Exception as e:
            self.log(f"Error creating {suffix} audio file: {e}")
            return None

    def test_boundary_conditions(self):
        """Test files at various sizes around the 24MB boundary"""
        self.log("🎯 Testing boundary conditions around 24MB limit...")
        
        # Test cases: just under, at, and just over the limit
        test_cases = [
            (23.5, "just_under_24mb"),
            (24.5, "just_over_24mb"),
            (26.0, "well_over_24mb")
        ]
        
        results = {}
        
        for target_mb, case_name in test_cases:
            self.log(f"\n📊 Testing {case_name} (target: {target_mb} MB)...")
            
            # Create test file
            audio_file = self.create_audio_file_target_size(target_mb, case_name)
            if not audio_file:
                results[case_name] = "failed_to_create"
                continue
            
            actual_size = os.path.getsize(audio_file) / (1024 * 1024)
            
            # Upload via /upload-file endpoint
            try:
                with open(audio_file, 'rb') as f:
                    files = {'file': (f'{case_name}.wav', f, 'audio/wav')}
                    data = {'title': f'Boundary Test {case_name}'}
                    
                    response = requests.post(
                        f"{self.api_url}/upload-file",
                        data=data,
                        files=files,
                        timeout=300
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        note_id = response_data.get('id')
                        if note_id:
                            self.created_notes.append(note_id)
                        
                        self.log(f"✅ Upload successful for {case_name} ({actual_size:.1f} MB)")
                        
                        # Wait and check processing
                        time.sleep(15)  # Give it time to start processing
                        
                        status_response = requests.get(f"{self.api_url}/notes/{note_id}", timeout=30)
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('status', 'unknown')
                            artifacts = status_data.get('artifacts', {})
                            transcript = artifacts.get('transcript', '')
                            
                            # Check if chunking was used
                            has_parts = '[Part ' in transcript if transcript else False
                            
                            self.log(f"   Status: {status}")
                            self.log(f"   Has transcript: {bool(transcript)}")
                            self.log(f"   Chunking used: {has_parts}")
                            
                            if actual_size > 24.0 and has_parts:
                                self.log(f"✅ Large file ({actual_size:.1f} MB) correctly used chunking")
                                results[case_name] = "chunked_correctly"
                            elif actual_size <= 24.0 and not has_parts:
                                self.log(f"✅ Small file ({actual_size:.1f} MB) correctly processed without chunking")
                                results[case_name] = "processed_normally"
                            elif actual_size <= 24.0 and has_parts:
                                self.log(f"ℹ️  Small file ({actual_size:.1f} MB) was chunked (acceptable)")
                                results[case_name] = "small_file_chunked"
                            else:
                                self.log(f"⚠️  Large file ({actual_size:.1f} MB) not chunked (unexpected)")
                                results[case_name] = "large_file_not_chunked"
                        else:
                            self.log(f"❌ Failed to check status for {case_name}")
                            results[case_name] = "status_check_failed"
                    else:
                        self.log(f"❌ Upload failed for {case_name}: {response.status_code}")
                        results[case_name] = "upload_failed"
                        
            except Exception as e:
                self.log(f"❌ Error testing {case_name}: {e}")
                results[case_name] = "error"
        
        return results

    def print_boundary_summary(self, results):
        """Print summary of boundary tests"""
        self.log("\n" + "="*50)
        self.log("📊 BOUNDARY TEST SUMMARY")
        self.log("="*50)
        
        for case_name, result in results.items():
            status_emoji = "✅" if result in ["chunked_correctly", "processed_normally", "small_file_chunked"] else "❌"
            self.log(f"{status_emoji} {case_name}: {result}")
        
        successful_cases = sum(1 for r in results.values() if r in ["chunked_correctly", "processed_normally", "small_file_chunked"])
        total_cases = len(results)
        
        self.log(f"\nSuccessful cases: {successful_cases}/{total_cases}")
        self.log("="*50)
        
        return successful_cases == total_cases

def main():
    """Main test execution"""
    tester = BoundaryTester()
    
    try:
        results = tester.test_boundary_conditions()
        success = tester.print_boundary_summary(results)
        
        if success:
            print("\n🎉 All boundary tests passed!")
            return 0
        else:
            print("\n⚠️  Some boundary tests had issues.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())