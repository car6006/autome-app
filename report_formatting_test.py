#!/usr/bin/env python3
"""
Professional Report Formatting Test
Tests the new clean, rich-text professional report generation
"""

import requests
import sys
import json
import time
import re
from datetime import datetime

class ReportFormattingTester:
    def __init__(self, base_url="https://auto-me-debugger.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log(self, message):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, test_func):
        """Run a single test and track results"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            success, details = test_func()
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - PASSED")
                self.test_results.append({"name": name, "status": "PASSED", "details": details})
            else:
                self.log(f"❌ {name} - FAILED")
                self.test_results.append({"name": name, "status": "FAILED", "details": details})
            return success
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}")
            self.test_results.append({"name": name, "status": "ERROR", "details": str(e)})
            return False

    def find_suitable_note(self):
        """Find a note with substantial content for report generation"""
        try:
            response = requests.get(f"{self.api_url}/notes", timeout=10)
            if response.status_code != 200:
                return None, f"Failed to get notes: {response.status_code}"
            
            notes = response.json()
            
            # Look for JNB Management Meeting notes (they have substantial content)
            for note in notes:
                if "JNB Management Meeting" in note.get('title', ''):
                    artifacts = note.get('artifacts', {})
                    transcript = artifacts.get('transcript', '')
                    if len(transcript) > 10000:  # Substantial content
                        return note['id'], f"Found note: {note['title']} with {len(transcript)} characters"
            
            # Fallback to any note with substantial content
            for note in notes:
                artifacts = note.get('artifacts', {})
                content_length = len(artifacts.get('transcript', '')) + len(artifacts.get('text', ''))
                if content_length > 1000:
                    return note['id'], f"Found note: {note['title']} with {content_length} characters"
            
            return None, "No notes with substantial content found"
            
        except Exception as e:
            return None, f"Error finding suitable note: {str(e)}"

    def test_individual_report_generation(self):
        """Test individual note report generation"""
        note_id, message = self.find_suitable_note()
        if not note_id:
            return False, message
        
        try:
            # Generate report
            response = requests.post(
                f"{self.api_url}/notes/{note_id}/generate-report",
                timeout=60
            )
            
            if response.status_code != 200:
                return False, f"Report generation failed: {response.status_code} - {response.text}"
            
            report_data = response.json()
            report_content = report_data.get('report', '')
            
            if not report_content:
                return False, "No report content returned"
            
            # Test report structure and formatting
            issues = []
            
            # Check for markdown symbols (should NOT be present)
            if '###' in report_content:
                issues.append("Found markdown header symbols (###)")
            if '**' in report_content:
                issues.append("Found markdown bold symbols (**)")
            if '##' in report_content:
                issues.append("Found markdown header symbols (##)")
            
            # Check for required sections (should be in ALL CAPS)
            required_sections = [
                'EXECUTIVE SUMMARY',
                'KEY INSIGHTS',
                'STRATEGIC RECOMMENDATIONS', 
                'ACTION ITEMS',
                'PRIORITIES',
                'FOLLOW-UP & MONITORING'
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in report_content:
                    missing_sections.append(section)
            
            # Check for bullet points (should use •)
            bullet_count = report_content.count('•')
            if bullet_count < 5:
                issues.append(f"Insufficient bullet points (•) found: {bullet_count}")
            
            # Check for proper structure
            if not any(section in report_content for section in required_sections):
                issues.append("No required sections found in report")
            
            details = {
                "note_id": note_id,
                "report_length": len(report_content),
                "bullet_points": bullet_count,
                "missing_sections": missing_sections,
                "formatting_issues": issues,
                "has_clean_formatting": len(issues) == 0 and len(missing_sections) == 0,
                "sample_content": report_content[:500] + "..." if len(report_content) > 500 else report_content
            }
            
            success = len(issues) == 0 and len(missing_sections) == 0
            return success, details
            
        except Exception as e:
            return False, f"Exception during report generation: {str(e)}"

    def test_batch_report_generation(self):
        """Test batch report generation with multiple notes"""
        try:
            # Find multiple notes with content
            response = requests.get(f"{self.api_url}/notes", timeout=10)
            if response.status_code != 200:
                return False, f"Failed to get notes: {response.status_code}"
            
            notes = response.json()
            suitable_notes = []
            
            for note in notes:
                artifacts = note.get('artifacts', {})
                content_length = len(artifacts.get('transcript', '')) + len(artifacts.get('text', ''))
                if content_length > 500:
                    suitable_notes.append(note['id'])
                    if len(suitable_notes) >= 3:  # Get 3 notes for batch test
                        break
            
            if len(suitable_notes) < 2:
                return False, f"Need at least 2 notes with content, found {len(suitable_notes)}"
            
            # Generate batch report
            response = requests.post(
                f"{self.api_url}/notes/batch-report",
                json=suitable_notes[:3],  # Use up to 3 notes
                timeout=90
            )
            
            if response.status_code != 200:
                return False, f"Batch report generation failed: {response.status_code} - {response.text}"
            
            report_data = response.json()
            report_content = report_data.get('report', '')
            
            if not report_content:
                return False, "No batch report content returned"
            
            # Test batch report structure
            issues = []
            
            # Check for markdown symbols (should NOT be present)
            if '###' in report_content:
                issues.append("Found markdown header symbols (###)")
            if '**' in report_content:
                issues.append("Found markdown bold symbols (**)")
            
            # Check for batch-specific sections
            batch_sections = [
                'EXECUTIVE SUMMARY',
                'COMPREHENSIVE ANALYSIS',
                'STRATEGIC RECOMMENDATIONS',
                'IMPLEMENTATION ROADMAP',
                'SUCCESS METRICS',
                'RISK ASSESSMENT',
                'STAKEHOLDER INVOLVEMENT'
            ]
            
            missing_sections = []
            for section in batch_sections:
                if section not in report_content:
                    missing_sections.append(section)
            
            # Check for bullet points
            bullet_count = report_content.count('•')
            if bullet_count < 10:  # Batch reports should have more bullet points
                issues.append(f"Insufficient bullet points (•) for batch report: {bullet_count}")
            
            details = {
                "note_count": len(suitable_notes[:3]),
                "report_length": len(report_content),
                "bullet_points": bullet_count,
                "missing_sections": missing_sections,
                "formatting_issues": issues,
                "has_clean_formatting": len(issues) == 0 and len(missing_sections) <= 2,  # Allow some flexibility for batch reports
                "sample_content": report_content[:500] + "..." if len(report_content) > 500 else report_content
            }
            
            success = len(issues) == 0 and len(missing_sections) <= 2
            return success, details
            
        except Exception as e:
            return False, f"Exception during batch report generation: {str(e)}"

    def test_report_content_quality(self):
        """Test the quality and professionalism of report content"""
        note_id, message = self.find_suitable_note()
        if not note_id:
            return False, message
        
        try:
            response = requests.post(
                f"{self.api_url}/notes/{note_id}/generate-report",
                timeout=60
            )
            
            if response.status_code != 200:
                return False, f"Report generation failed: {response.status_code}"
            
            report_data = response.json()
            report_content = report_data.get('report', '')
            
            # Quality checks
            quality_issues = []
            
            # Check for professional language indicators
            professional_indicators = [
                'recommend', 'strategic', 'implement', 'priority', 'action',
                'analysis', 'assessment', 'monitoring', 'stakeholder'
            ]
            
            found_indicators = sum(1 for indicator in professional_indicators 
                                 if indicator.lower() in report_content.lower())
            
            if found_indicators < 3:
                quality_issues.append(f"Limited professional language: {found_indicators}/8 indicators")
            
            # Check for actionable content
            actionable_words = ['should', 'must', 'will', 'need to', 'require', 'ensure']
            actionable_count = sum(1 for word in actionable_words 
                                 if word.lower() in report_content.lower())
            
            if actionable_count < 3:
                quality_issues.append(f"Limited actionable content: {actionable_count} actionable phrases")
            
            # Check report length (should be substantial)
            if len(report_content) < 1000:
                quality_issues.append(f"Report too short: {len(report_content)} characters")
            
            # Check for proper sentence structure
            sentences = report_content.split('.')
            if len(sentences) < 10:
                quality_issues.append(f"Too few sentences: {len(sentences)}")
            
            details = {
                "report_length": len(report_content),
                "professional_indicators": found_indicators,
                "actionable_phrases": actionable_count,
                "sentence_count": len(sentences),
                "quality_issues": quality_issues,
                "is_professional": len(quality_issues) <= 1
            }
            
            success = len(quality_issues) <= 1
            return success, details
            
        except Exception as e:
            return False, f"Exception during content quality test: {str(e)}"

    def test_report_storage_and_retrieval(self):
        """Test that reports are properly stored in note artifacts"""
        note_id, message = self.find_suitable_note()
        if not note_id:
            return False, message
        
        try:
            # Generate report
            response = requests.post(
                f"{self.api_url}/notes/{note_id}/generate-report",
                timeout=60
            )
            
            if response.status_code != 200:
                return False, f"Report generation failed: {response.status_code}"
            
            # Wait a moment for storage
            time.sleep(1)
            
            # Retrieve note to check if report is stored
            response = requests.get(f"{self.api_url}/notes/{note_id}", timeout=10)
            
            if response.status_code != 200:
                return False, f"Failed to retrieve note: {response.status_code}"
            
            note_data = response.json()
            artifacts = note_data.get('artifacts', {})
            
            if 'professional_report' not in artifacts:
                return False, "Professional report not stored in artifacts"
            
            stored_report = artifacts['professional_report']
            
            if not stored_report or len(stored_report) < 500:
                return False, f"Stored report is too short: {len(stored_report)} characters"
            
            details = {
                "note_id": note_id,
                "report_stored": True,
                "stored_report_length": len(stored_report),
                "artifacts_keys": list(artifacts.keys())
            }
            
            return True, details
            
        except Exception as e:
            return False, f"Exception during storage test: {str(e)}"

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test with non-existent note
            response = requests.post(
                f"{self.api_url}/notes/invalid-note-id/generate-report",
                timeout=10
            )
            
            if response.status_code != 404:
                return False, f"Expected 404 for invalid note, got {response.status_code}"
            
            # Test with empty note list for batch report
            response = requests.post(
                f"{self.api_url}/notes/batch-report",
                json=[],
                timeout=10
            )
            
            if response.status_code != 400:
                return False, f"Expected 400 for empty batch list, got {response.status_code}"
            
            details = {
                "invalid_note_handling": "Correct 404 response",
                "empty_batch_handling": "Correct 400 response"
            }
            
            return True, details
            
        except Exception as e:
            return False, f"Exception during error handling test: {str(e)}"

    def run_all_tests(self):
        """Run all report formatting tests"""
        self.log("🚀 Starting Professional Report Formatting Tests")
        self.log(f"   API URL: {self.api_url}")
        
        # Run all tests
        tests = [
            ("Individual Report Generation", self.test_individual_report_generation),
            ("Batch Report Generation", self.test_batch_report_generation),
            ("Report Content Quality", self.test_report_content_quality),
            ("Report Storage and Retrieval", self.test_report_storage_and_retrieval),
            ("Error Handling", self.test_error_handling)
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        return self.tests_passed == self.tests_run

    def print_summary(self):
        """Print detailed test summary"""
        self.log("\n" + "="*60)
        self.log("📊 PROFESSIONAL REPORT FORMATTING TEST SUMMARY")
        self.log("="*60)
        self.log(f"Tests run: {self.tests_run}")
        self.log(f"Tests passed: {self.tests_passed}")
        self.log(f"Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        self.log("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            self.log(f"{status_icon} {result['name']}: {result['status']}")
            
            if isinstance(result["details"], dict):
                for key, value in result["details"].items():
                    if key == "sample_content":
                        continue  # Skip sample content in summary
                    self.log(f"   {key}: {value}")
            else:
                self.log(f"   Details: {result['details']}")
        
        self.log("="*60)
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = ReportFormattingTester()
    
    try:
        success = tester.run_all_tests()
        all_passed = tester.print_summary()
        
        if all_passed:
            print("\n🎉 All report formatting tests passed! Professional reports are working correctly.")
            return 0
        else:
            print(f"\n⚠️  Some tests failed. Check the logs above for details.")
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
    sys.exit(main())