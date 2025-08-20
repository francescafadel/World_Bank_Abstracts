#!/usr/bin/env python3
"""
Test script to verify the fixed API scraper works correctly
"""

import sys
import os
sys.path.append('../src')

from api_scraper import WorldBankAPIScraper

def test_fixed_scraper():
    """Test the fixed scraper on a few projects"""
    
    # Initialize scraper
    scraper = WorldBankAPIScraper(delay=0)
    
    # Test URLs
    test_urls = [
        "https://projects.worldbank.org/en/projects-operations/project-detail/P168606",
        "https://projects.worldbank.org/en/projects-operations/project-detail/P163004",
        "https://projects.worldbank.org/en/projects-operations/project-detail/P171465"
    ]
    
    print("🧪 Testing Fixed API Scraper")
    print("=" * 50)
    
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
                
            # Check for pdo
            if 'pdo' in project_data:
                pdo = project_data['pdo']
                print(f"   📝 PDO field: {len(pdo)} characters")
                print(f"   Preview: {pdo[:100]}...")
        else:
            print(f"   ❌ No project data found")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_fixed_scraper()
