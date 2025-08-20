#!/usr/bin/env python3
"""
Test script to verify the updated API scraper leaves abstract blank when no project_abstract is available
"""

import sys
import os
sys.path.append('.')

from api_scraper import WorldBankAPIScraper

def test_updated_scraper():
    """Test the updated scraper on projects with and without project_abstract"""
    
    # Initialize scraper
    scraper = WorldBankAPIScraper(delay=0)
    
    # Test URLs - some with project_abstract, some without
    test_urls = [
        "https://projects.worldbank.org/en/projects-operations/project-detail/P168606",  # Has project_abstract
        "https://projects.worldbank.org/en/projects-operations/project-detail/P163004",  # No project_abstract
        "https://projects.worldbank.org/en/projects-operations/project-detail/P171465"   # Has project_abstract
    ]
    
    print("🧪 Testing Updated API Scraper (No PDO Fallback)")
    print("=" * 60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📋 Test {i}: {url}")
        
        # Extract project ID
        project_id = scraper.extract_project_id(url)
        print(f"   Project ID: {project_id}")
        
        # Get project data
        project_data = scraper.get_project_data(project_id)
        
        if project_data:
            # Check what fields are available
            print(f"   Available fields: {list(project_data.keys())}")
            
            # Check for project_abstract
            if 'project_abstract' in project_data:
                abstract = project_data['project_abstract']
                print(f"   ✅ Found project_abstract: {len(abstract)} characters")
                print(f"   Preview: {abstract[:100]}...")
            else:
                print(f"   ❌ No project_abstract field found")
                
            # Check for pdo (should not be used)
            if 'pdo' in project_data:
                pdo = project_data['pdo']
                print(f"   📝 PDO field exists: {len(pdo)} characters (will be ignored)")
                print(f"   Preview: {pdo[:100]}...")
            
            # Test the extract_abstract method
            extracted_abstract = scraper.extract_abstract(url)
            if extracted_abstract:
                print(f"   🎯 Extracted abstract: {len(extracted_abstract)} characters")
                print(f"   Preview: {extracted_abstract[:100]}...")
            else:
                print(f"   🎯 Extracted abstract: BLANK (correct!)")
        else:
            print(f"   ❌ No project data found")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_updated_scraper()
