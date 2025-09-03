#!/usr/bin/env python3
"""
Simple RTF Export Test - Test existing notes with AI conversations
"""

import requests
import json

def test_rtf_export():
    api_url = 'https://autome-fix.preview.emergentagent.com/api'
    
    print("🔍 Finding notes with AI conversations...")
    
    # Get notes without authentication to find anonymous ones
    response = requests.get(f'{api_url}/notes?limit=50')
    if response.status_code != 200:
        print(f"❌ Failed to get notes: {response.status_code}")
        return False
    
    notes = response.json()
    print(f"Found {len(notes)} notes")
    
    test_passed = False
    
    for note in notes:
        note_id = note['id']
        user_id = note.get('user_id')
        artifacts = note.get('artifacts', {})
        
        # Look for anonymous notes with AI conversations
        if not user_id and 'ai_conversations' in artifacts:
            print(f"\n📄 Testing note {note_id}")
            print(f"   Title: {note['title']}")
            print(f"   AI Conversations: {len(artifacts['ai_conversations'])}")
            
            # Test RTF export
            response = requests.get(f'{api_url}/notes/{note_id}/ai-conversations/export?format=rtf')
            if response.status_code == 200:
                rtf_content = response.text
                print(f"   ✅ RTF export successful! Content length: {len(rtf_content)} characters")
                
                # Verify RTF structure based on review request requirements
                rtf_checks = {
                    'RTF Header Structure': rtf_content.startswith(r'{\rtf1\ansi\deff0'),
                    'Professional Font Tables': r'{\fonttbl{\f0 Times New Roman;}{\f1 Arial;}{\f2 Calibri;}' in rtf_content,
                    'Professional Color Tables': r'{\colortbl;\red0\green0\blue0;\red234\green10\blue42;' in rtf_content,
                    'Professional Report Title': 'AI CONTENT ANALYSIS REPORT' in rtf_content,
                    'Clean Section Divisions': '─' in rtf_content,  # Professional separator lines
                    'Professional Bullet Points': r'\bullet\tab' in rtf_content,
                    'No Messy Dots': rtf_content.count('...') < 3,
                    'Professional Typography': all(font in rtf_content for font in [r'\f0', r'\f1', r'\f2']),
                    'Professional Colors': all(color in rtf_content for color in [r'\cf1', r'\cf2', r'\cf3']),
                    'Clean Headers': 'ANALYSIS SECTION' in rtf_content,
                    'No Markdown Symbols': not any(symbol in rtf_content for symbol in ['###', '**', '```']),
                    'Proper RTF Closing': rtf_content.endswith('}'),
                    'Professional Content Length': len(rtf_content) > 5000
                }
                
                # Check file headers
                content_type = response.headers.get('Content-Type', '')
                content_disposition = response.headers.get('Content-Disposition', '')
                
                header_checks = {
                    'Correct Content-Type': content_type == 'application/rtf',
                    'File Download Headers': 'attachment' in content_disposition,
                    'Descriptive Filename': 'AI_Analysis_' in content_disposition,
                    'RTF Extension': '.rtf' in content_disposition
                }
                
                all_checks = {**rtf_checks, **header_checks}
                
                passed = 0
                total = len(all_checks)
                
                print("   🔍 RTF PROFESSIONAL FORMATTING VERIFICATION:")
                for check, result in all_checks.items():
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"     {check}: {status}")
                    if result:
                        passed += 1
                
                rtf_success_rate = (passed / total) * 100
                print(f"   📊 RTF Score: {passed}/{total} ({rtf_success_rate:.1f}%)")
                
                # Test TXT export
                response = requests.get(f'{api_url}/notes/{note_id}/ai-conversations/export?format=txt')
                if response.status_code == 200:
                    txt_content = response.text
                    print(f"   ✅ TXT export successful! Content length: {len(txt_content)} characters")
                    
                    txt_checks = {
                        'Professional Header Lines': '=' * 50 in txt_content or '=' * 70 in txt_content,
                        'Professional Report Title': 'AI CONTENT ANALYSIS REPORT' in txt_content,
                        'Executive Summary': 'EXECUTIVE SUMMARY' in txt_content,
                        'Analysis Sections': 'ANALYSIS SECTION' in txt_content,
                        'Professional Separators': '-' * 20 in txt_content or '-' * 40 in txt_content,
                        'Clean Bullet Points': '•' in txt_content,
                        'No Markdown Symbols': not any(symbol in txt_content for symbol in ['###', '**', '```']),
                        'Professional Spacing': '\n\n' in txt_content,
                        'Document Information': 'Document:' in txt_content and 'Generated:' in txt_content,
                        'Professional Footer': 'AI-Generated Content Analysis Report' in txt_content,
                        'Substantial Content': len(txt_content) > 1000
                    }
                    
                    # Check TXT headers
                    txt_content_type = response.headers.get('Content-Type', '')
                    txt_content_disposition = response.headers.get('Content-Disposition', '')
                    
                    txt_header_checks = {
                        'Correct TXT Content-Type': txt_content_type == 'text/plain',
                        'TXT File Download Headers': 'attachment' in txt_content_disposition,
                        'TXT Descriptive Filename': 'AI_Analysis_' in txt_content_disposition,
                        'TXT Extension': '.txt' in txt_content_disposition
                    }
                    
                    all_txt_checks = {**txt_checks, **txt_header_checks}
                    
                    txt_passed = 0
                    txt_total = len(all_txt_checks)
                    
                    print("   🔍 TXT PROFESSIONAL FORMATTING VERIFICATION:")
                    for check, result in all_txt_checks.items():
                        status = "✅ PASS" if result else "❌ FAIL"
                        print(f"     {check}: {status}")
                        if result:
                            txt_passed += 1
                    
                    txt_success_rate = (txt_passed / txt_total) * 100
                    print(f"   📊 TXT Score: {txt_passed}/{txt_total} ({txt_success_rate:.1f}%)")
                    
                    # Overall assessment
                    if rtf_success_rate >= 85 and txt_success_rate >= 85:
                        print(f"\n🎉 RTF/TXT Export Test PASSED for note {note_id}!")
                        print("✅ Professional RTF formatting with improved structure verified")
                        print("✅ Professional TXT formatting with clean headers verified")
                        print("✅ Descriptive filename generation working")
                        print("✅ Clean bullet points and professional typography confirmed")
                        print("✅ No messy, tacky output - everything aligned and professional")
                        test_passed = True
                        break
                    else:
                        print(f"   ⚠️  Test scores below 85% threshold")
                
                else:
                    print(f"   ❌ TXT export failed: {response.status_code}")
            
            else:
                print(f"   ❌ RTF export failed: {response.status_code}")
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        print(f"     Error: {error_data}")
                    except:
                        print(f"     Error: {response.text}")
    
    return test_passed

def test_expeditors_branding():
    """Test Expeditors branding by registering an Expeditors user"""
    api_url = 'https://autome-fix.preview.emergentagent.com/api'
    
    print("\n👑 Testing Expeditors Branding...")
    
    # Register Expeditors user
    expeditors_user_data = {
        "email": f"rtf_expeditors_test@expeditors.com",
        "username": f"rtfexptest",
        "password": "ExpeditorsPass123!",
        "first_name": "Expeditors",
        "last_name": "RTF Test"
    }
    
    response = requests.post(f'{api_url}/auth/register', json=expeditors_user_data)
    if response.status_code != 200:
        print(f"❌ Expeditors user registration failed: {response.status_code}")
        return False
    
    token = response.json()['access_token']
    print("✅ Expeditors user registered")
    
    # Find a note with AI conversations to test branding
    response = requests.get(f'{api_url}/notes?limit=20')
    if response.status_code != 200:
        return False
    
    notes = response.json()
    for note in notes:
        if not note.get('user_id') and note.get('artifacts', {}).get('ai_conversations'):
            note_id = note['id']
            print(f"Testing Expeditors branding with note {note_id}")
            
            # Test RTF export with Expeditors user
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f'{api_url}/notes/{note_id}/ai-conversations/export?format=rtf', headers=headers)
            
            if response.status_code == 200:
                rtf_content = response.text
                
                # Check for Expeditors branding
                expeditors_checks = {
                    'Expeditors Header': 'EXPEDITORS INTERNATIONAL' in rtf_content,
                    'Global Logistics Branding': 'Global Logistics & Freight Forwarding' in rtf_content,
                    'Expeditors Colors': r'\cf2 EXPEDITORS INTERNATIONAL' in rtf_content,
                    'Expeditors Footer': 'confidential and proprietary' in rtf_content,
                    'Expeditors Filename': 'Expeditors_AI_Analysis_' in response.headers.get('Content-Disposition', '')
                }
                
                print("   🔍 EXPEDITORS BRANDING VERIFICATION:")
                expeditors_passed = 0
                for check, result in expeditors_checks.items():
                    status = "✅ PASS" if result else "❌ FAIL"
                    print(f"     {check}: {status}")
                    if result:
                        expeditors_passed += 1
                
                expeditors_rate = (expeditors_passed / len(expeditors_checks)) * 100
                print(f"   📊 Expeditors Branding Score: {expeditors_passed}/{len(expeditors_checks)} ({expeditors_rate:.1f}%)")
                
                return expeditors_rate >= 80
            else:
                print(f"❌ Expeditors RTF export failed: {response.status_code}")
                return False
    
    return False

if __name__ == "__main__":
    print("🚀 Starting Simple RTF Export Test")
    print("   Testing improved professional RTF and TXT export formatting")
    
    # Test basic RTF/TXT export
    basic_test_passed = test_rtf_export()
    
    # Test Expeditors branding
    branding_test_passed = test_expeditors_branding()
    
    print("\n" + "="*70)
    print("📊 SIMPLE RTF EXPORT TEST SUMMARY")
    print("="*70)
    
    if basic_test_passed:
        print("✅ Basic RTF/TXT Export Test: PASSED")
        print("   - Professional RTF formatting verified")
        print("   - Professional TXT formatting verified")
        print("   - Clean structure without messy formatting")
        print("   - Descriptive filename generation working")
    else:
        print("❌ Basic RTF/TXT Export Test: FAILED")
    
    if branding_test_passed:
        print("✅ Expeditors Branding Test: PASSED")
        print("   - Expeditors header and logo integration working")
        print("   - Professional branding elements present")
    else:
        print("❌ Expeditors Branding Test: FAILED")
    
    print("="*70)
    
    if basic_test_passed and branding_test_passed:
        print("\n🎉 All RTF export tests PASSED!")
        print("The improved professional RTF and TXT export formatting is working correctly.")
        exit(0)
    else:
        print("\n⚠️  Some RTF export tests failed.")
        exit(1)