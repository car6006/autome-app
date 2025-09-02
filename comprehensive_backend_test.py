#!/usr/bin/env python3
"""
Comprehensive OPEN AUTO-ME v1 Backend Test
Testing all key endpoints mentioned in the review request
"""

import requests
import json
import time
from datetime import datetime
import tempfile
import os

class ComprehensiveBackendTester:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.expeditors_token = None
        self.regular_token = None
        self.created_notes = []
        self.test_results = []

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def add_result(self, test_name, success, details=""):
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def setup_users(self):
        """Setup test users"""
        self.log("🔐 Setting up test users...")
        
        # Register Expeditors user
        expeditors_data = {
            "email": f"test_expeditors_{int(time.time())}@expeditors.com",
            "username": f"expeditors_user_{int(time.time())}",
            "password": "ExpeditorsPass123!",
            "first_name": "Expeditors",
            "last_name": "User"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=expeditors_data)
        if response.status_code == 200:
            self.expeditors_token = response.json().get('access_token')
            self.log(f"✅ Expeditors user registered: {expeditors_data['email']}")
        
        # Register regular user
        regular_data = {
            "email": f"test_user_{int(time.time())}@example.com",
            "username": f"testuser_{int(time.time())}",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=regular_data)
        if response.status_code == 200:
            self.regular_token = response.json().get('access_token')
            self.log(f"✅ Regular user registered: {regular_data['email']}")
        
        success = self.expeditors_token and self.regular_token
        self.add_result("User Setup", success, f"Expeditors: {bool(self.expeditors_token)}, Regular: {bool(self.regular_token)}")
        return success

    def test_basic_api_health(self):
        """Test 1: Basic API Health"""
        self.log("\n🏥 Testing Basic API Health...")
        
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = data.get('message', '')
                self.log(f"✅ API Health Check - Status: {response.status_code}")
                self.log(f"   Message: {message}")
                
                # Check if it mentions AUTO-ME
                if 'AUTO-ME' in message:
                    self.log(f"   ✅ API identifies as AUTO-ME system")
                    details = f"API Message: {message}"
                else:
                    details = f"API Message: {message} (no AUTO-ME reference)"
            else:
                details = f"Status: {response.status_code}"
                self.log(f"❌ API Health Check failed - Status: {response.status_code}")
            
            self.add_result("Basic API Health", success, details)
            return success
            
        except Exception as e:
            self.log(f"❌ API Health Check error: {str(e)}")
            self.add_result("Basic API Health", False, f"Error: {str(e)}")
            return False

    def test_user_authentication(self):
        """Test 2: User Authentication"""
        self.log("\n🔐 Testing User Authentication...")
        
        results = []
        
        # Test login endpoints
        for user_type, token, email in [
            ("Regular", self.regular_token, "test_user"),
            ("Expeditors", self.expeditors_token, "test_expeditors")
        ]:
            # Test profile retrieval
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f"{self.api_url}/auth/me", headers=headers)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                user_email = data.get('email', '')
                self.log(f"✅ {user_type} user profile retrieved: {user_email}")
                
                # Verify Expeditors domain
                if user_type == "Expeditors" and user_email.endswith('@expeditors.com'):
                    self.log(f"   ✅ Expeditors domain verified")
                
                results.append(True)
            else:
                self.log(f"❌ {user_type} user profile retrieval failed")
                results.append(False)
        
        overall_success = all(results)
        self.add_result("User Authentication", overall_success, f"Regular: {results[0]}, Expeditors: {results[1]}")
        return overall_success

    def test_file_upload_functionality(self):
        """Test 3: File Upload Functionality"""
        self.log("\n📁 Testing File Upload Functionality...")
        
        results = []
        
        # Test audio file upload
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            # Write minimal MP3 header
            mp3_header = b'\xff\xfb\x90\x00' + b'\x00' * 100
            tmp_file.write(mp3_header)
            tmp_file.flush()
            
            headers = {'Authorization': f'Bearer {self.regular_token}'}
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_audio.mp3', f, 'audio/mp3')}
                data = {'title': 'Audio Upload Test'}
                response = requests.post(f"{self.api_url}/upload-file", 
                                       data=data, files=files, headers=headers)
            
            os.unlink(tmp_file.name)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                note_id = data.get('id')
                file_kind = data.get('kind')
                self.created_notes.append(note_id)
                self.log(f"✅ Audio upload successful - Note ID: {note_id}, Kind: {file_kind}")
                results.append(True)
            else:
                self.log(f"❌ Audio upload failed - Status: {response.status_code}")
                results.append(False)
        
        # Test image file upload
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01IEND\xaeB`\x82'
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(png_data)
            tmp_file.flush()
            
            headers = {'Authorization': f'Bearer {self.regular_token}'}
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_image.png', f, 'image/png')}
                data = {'title': 'Image Upload Test'}
                response = requests.post(f"{self.api_url}/upload-file", 
                                       data=data, files=files, headers=headers)
            
            os.unlink(tmp_file.name)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                note_id = data.get('id')
                file_kind = data.get('kind')
                self.created_notes.append(note_id)
                self.log(f"✅ Image upload successful - Note ID: {note_id}, Kind: {file_kind}")
                results.append(True)
            else:
                self.log(f"❌ Image upload failed - Status: {response.status_code}")
                results.append(False)
        
        # Test unsupported file type
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b'This is a text file')
            tmp_file.flush()
            
            headers = {'Authorization': f'Bearer {self.regular_token}'}
            with open(tmp_file.name, 'rb') as f:
                files = {'file': ('test_file.txt', f, 'text/plain')}
                data = {'title': 'Unsupported File Test'}
                response = requests.post(f"{self.api_url}/upload-file", 
                                       data=data, files=files, headers=headers)
            
            os.unlink(tmp_file.name)
            
            success = response.status_code == 400  # Should fail
            if success:
                self.log(f"✅ Unsupported file correctly rejected - Status: {response.status_code}")
                results.append(True)
            else:
                self.log(f"❌ Unsupported file handling failed - Status: {response.status_code}")
                results.append(False)
        
        overall_success = all(results)
        self.add_result("File Upload Functionality", overall_success, f"Audio: {results[0]}, Image: {results[1]}, Validation: {results[2]}")
        return overall_success

    def add_content_to_note(self, note_id, token):
        """Helper to add content to a note for report testing"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
            import os
            
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'auto_me_db')
            
            async def update_note():
                client = AsyncIOMotorClient(mongo_url)
                db = client[db_name]
                
                mock_content = """
                This is a comprehensive business strategy meeting discussing Q4 operations and supply chain optimization. 
                Key topics include vendor management, logistics efficiency, cost reduction initiatives, and market expansion plans. 
                The team reviewed performance metrics, identified improvement opportunities, and established action items for implementation. 
                Budget allocations and resource planning were discussed for the upcoming quarter with focus on operational excellence.
                """
                
                result = await db.notes.update_one(
                    {"id": note_id},
                    {
                        "$set": {
                            "status": "ready",
                            "artifacts.transcript": mock_content.strip(),
                            "ready_at": datetime.utcnow()
                        }
                    }
                )
                
                client.close()
                return result.modified_count > 0
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(update_note())
            loop.close()
            
            return success
                
        except Exception as e:
            self.log(f"   Error adding content: {str(e)}")
            return False

    def test_professional_report_generation(self):
        """Test 4: Professional Report Generation with Expeditors Branding"""
        self.log("\n📊 Testing Professional Report Generation...")
        
        results = []
        
        # Test single note report for Expeditors user
        headers = {'Authorization': f'Bearer {self.expeditors_token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}/notes", 
                               json={"title": "Expeditors Supply Chain Meeting", "kind": "audio"}, 
                               headers=headers)
        
        if response.status_code == 200:
            note_id = response.json().get('id')
            self.created_notes.append(note_id)
            
            # Add content to the note
            if self.add_content_to_note(note_id, self.expeditors_token):
                time.sleep(2)
                
                # Generate report
                response = requests.post(f"{self.api_url}/notes/{note_id}/generate-report", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    report = data.get('report', '')
                    is_expeditors = data.get('is_expeditors', False)
                    
                    # Check for Expeditors branding
                    has_branding = 'EXPEDITORS INTERNATIONAL' in report
                    has_header = 'Professional Business Report' in report
                    
                    self.log(f"✅ Expeditors single report generated ({len(report)} chars)")
                    self.log(f"   Is Expeditors user: {is_expeditors}")
                    self.log(f"   Has branding: {has_branding}")
                    self.log(f"   Has header: {has_header}")
                    
                    results.append(has_branding and has_header and is_expeditors)
                else:
                    self.log(f"❌ Expeditors report generation failed - Status: {response.status_code}")
                    results.append(False)
            else:
                self.log(f"❌ Failed to add content to Expeditors note")
                results.append(False)
        else:
            self.log(f"❌ Failed to create Expeditors note")
            results.append(False)
        
        # Test single note report for regular user (should not have branding)
        headers = {'Authorization': f'Bearer {self.regular_token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}/notes", 
                               json={"title": "Business Strategy Meeting", "kind": "audio"}, 
                               headers=headers)
        
        if response.status_code == 200:
            note_id = response.json().get('id')
            self.created_notes.append(note_id)
            
            # Add content to the note
            if self.add_content_to_note(note_id, self.regular_token):
                time.sleep(2)
                
                # Generate report
                response = requests.post(f"{self.api_url}/notes/{note_id}/generate-report", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    report = data.get('report', '')
                    is_expeditors = data.get('is_expeditors', False)
                    
                    # Check that regular user does NOT get Expeditors branding
                    has_no_branding = 'EXPEDITORS INTERNATIONAL' not in report
                    
                    self.log(f"✅ Regular user report generated ({len(report)} chars)")
                    self.log(f"   Is Expeditors user: {is_expeditors}")
                    self.log(f"   No branding (correct): {has_no_branding}")
                    
                    results.append(has_no_branding and not is_expeditors)
                else:
                    self.log(f"❌ Regular user report generation failed - Status: {response.status_code}")
                    results.append(False)
            else:
                self.log(f"❌ Failed to add content to regular user note")
                results.append(False)
        else:
            self.log(f"❌ Failed to create regular user note")
            results.append(False)
        
        overall_success = all(results)
        self.add_result("Professional Report Generation", overall_success, f"Expeditors branding: {results[0]}, Regular no branding: {results[1]}")
        return overall_success

    def test_batch_report_generation(self):
        """Test 5: Batch Report Generation with Expeditors Branding"""
        self.log("\n📊 Testing Batch Report Generation...")
        
        # Create multiple notes for Expeditors user
        note_ids = []
        headers = {'Authorization': f'Bearer {self.expeditors_token}', 'Content-Type': 'application/json'}
        
        for title in ["Q4 Supply Chain Review", "Client Logistics Analysis", "Operational Efficiency Meeting"]:
            response = requests.post(f"{self.api_url}/notes", 
                                   json={"title": title, "kind": "audio"}, 
                                   headers=headers)
            
            if response.status_code == 200:
                note_id = response.json().get('id')
                note_ids.append(note_id)
                self.created_notes.append(note_id)
                
                # Add content to each note
                self.add_content_to_note(note_id, self.expeditors_token)
        
        if len(note_ids) >= 2:
            time.sleep(3)
            
            # Generate batch report
            response = requests.post(f"{self.api_url}/notes/batch-report", 
                                   json=note_ids, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                report = data.get('report', '')
                is_expeditors = data.get('is_expeditors', False)
                note_count = data.get('note_count', 0)
                
                # Check for Expeditors branding in batch report
                has_branding = 'EXPEDITORS INTERNATIONAL' in report
                has_header = 'Comprehensive Business Analysis Report' in report
                
                self.log(f"✅ Batch report generated ({len(report)} chars)")
                self.log(f"   Notes processed: {note_count}")
                self.log(f"   Is Expeditors user: {is_expeditors}")
                self.log(f"   Has branding: {has_branding}")
                self.log(f"   Has comprehensive header: {has_header}")
                
                success = has_branding and has_header and is_expeditors
                self.add_result("Batch Report Generation", success, f"Notes: {note_count}, Branding: {has_branding}, Header: {has_header}")
                return success
            else:
                self.log(f"❌ Batch report generation failed - Status: {response.status_code}")
                self.add_result("Batch Report Generation", False, f"Status: {response.status_code}")
                return False
        else:
            self.log(f"❌ Failed to create sufficient notes for batch report")
            self.add_result("Batch Report Generation", False, "Insufficient notes created")
            return False

    def test_notes_crud_operations(self):
        """Test 6: Notes CRUD Operations"""
        self.log("\n📝 Testing Notes CRUD Operations...")
        
        results = []
        headers = {'Authorization': f'Bearer {self.regular_token}', 'Content-Type': 'application/json'}
        
        # Create note
        response = requests.post(f"{self.api_url}/notes", 
                               json={"title": "CRUD Test Note", "kind": "photo"}, 
                               headers=headers)
        
        if response.status_code == 200:
            note_id = response.json().get('id')
            self.log(f"✅ Note created: {note_id}")
            results.append(True)
            
            # Read note
            response = requests.get(f"{self.api_url}/notes/{note_id}", headers=headers)
            if response.status_code == 200:
                note_data = response.json()
                self.log(f"✅ Note retrieved: {note_data.get('title')}")
                results.append(True)
            else:
                self.log(f"❌ Note retrieval failed")
                results.append(False)
            
            # List notes
            response = requests.get(f"{self.api_url}/notes", headers=headers)
            if response.status_code == 200:
                notes = response.json()
                self.log(f"✅ Notes listed: {len(notes)} notes found")
                results.append(True)
            else:
                self.log(f"❌ Notes listing failed")
                results.append(False)
            
            # Delete note
            response = requests.delete(f"{self.api_url}/notes/{note_id}", headers=headers)
            if response.status_code == 200:
                self.log(f"✅ Note deleted successfully")
                results.append(True)
            else:
                self.log(f"❌ Note deletion failed")
                results.append(False)
        else:
            self.log(f"❌ Note creation failed")
            results.extend([False, False, False, False])
        
        overall_success = all(results)
        self.add_result("Notes CRUD Operations", overall_success, f"Create: {results[0]}, Read: {results[1]}, List: {results[2]}, Delete: {results[3]}")
        return overall_success

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        self.log("🚀 Starting OPEN AUTO-ME v1 Comprehensive Backend Testing")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        
        # Setup
        if not self.setup_users():
            self.log("❌ User setup failed - stopping tests")
            return False
        
        # Run all tests
        test_functions = [
            self.test_basic_api_health,
            self.test_user_authentication,
            self.test_file_upload_functionality,
            self.test_professional_report_generation,
            self.test_batch_report_generation,
            self.test_notes_crud_operations
        ]
        
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                self.log(f"❌ Test {test_func.__name__} failed with error: {str(e)}")
                self.add_result(test_func.__name__, False, f"Error: {str(e)}")
        
        return True

    def print_summary(self):
        """Print comprehensive test summary"""
        self.log("\n" + "="*70)
        self.log("📊 OPEN AUTO-ME v1 COMPREHENSIVE TEST SUMMARY")
        self.log("="*70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        self.log(f"Overall Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
        self.log("")
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            self.log(f"{status} - {result['test']}")
            if result['details']:
                self.log(f"      {result['details']}")
        
        self.log("")
        if self.created_notes:
            self.log(f"Created test notes: {len(self.created_notes)}")
        
        self.log("="*70)
        
        # Key findings summary
        self.log("\n🔍 KEY FINDINGS:")
        
        # Check specific requirements from review request
        expeditors_branding = any("Professional Report Generation" in r['test'] and r['success'] for r in self.test_results)
        file_upload = any("File Upload Functionality" in r['test'] and r['success'] for r in self.test_results)
        auth_working = any("User Authentication" in r['test'] and r['success'] for r in self.test_results)
        api_health = any("Basic API Health" in r['test'] and r['success'] for r in self.test_results)
        
        self.log(f"✅ Basic API Health: {'WORKING' if api_health else 'FAILED'}")
        self.log(f"✅ User Authentication: {'WORKING' if auth_working else 'FAILED'}")
        self.log(f"✅ File Upload (Audio & Image): {'WORKING' if file_upload else 'FAILED'}")
        self.log(f"✅ Expeditors Branding in Reports: {'WORKING' if expeditors_branding else 'FAILED'}")
        
        return passed == total

def main():
    """Main test execution"""
    tester = ComprehensiveBackendTester()
    
    try:
        tester.run_comprehensive_test()
        success = tester.print_summary()
        
        if success:
            print("\n🎉 All comprehensive tests passed! OPEN AUTO-ME v1 backend is working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some tests failed. Check the detailed results above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.print_summary()
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.print_summary()
        return 1

if __name__ == "__main__":
    exit(main())