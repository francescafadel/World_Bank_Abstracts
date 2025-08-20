#!/usr/bin/env python3
"""
Example usage of the World Bank Abstract Scraper

This script demonstrates how to use the WorldBankScraper class
for extracting abstracts from World Bank project URLs.
"""

import pandas as pd
from world_bank_scraper import WorldBankScraper
import os

def create_sample_csv():
    """Create a sample CSV file for testing"""
    sample_data = {
        'Project ID': ['P123456', 'P178545', 'P167890'],
        'Project URL': [
            'https://projects.worldbank.org/en/projects-operations/project-detail/P178545',
            'https://projects.worldbank.org/en/projects-operations/project-detail/P167890',
            'https://projects.worldbank.org/en/projects-operations/project-detail/P123456'
        ],
        'Project Title': [
            'Sample Project 1',
            'Sample Project 2', 
            'Sample Project 3'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv('sample_projects.csv', index=False)
    print("Created sample_projects.csv with test data")
    return 'sample_projects.csv'

def example_basic_usage():
    """Demonstrate basic usage of the scraper"""
    print("=== Basic Usage Example ===")
    
    # Create sample CSV (you would skip this step with your real file)
    csv_file = create_sample_csv()
    
    # Initialize the scraper
    scraper = WorldBankScraper(headless=True, delay=2)
    
    try:
        # Process the CSV file
        output_file = scraper.process_csv(csv_file)
        print(f"Processing complete! Results saved to: {output_file}")
        
        # Show the results
        df = pd.read_csv(output_file)
        print("\nResults preview:")
        print(df[['Project ID', 'Abstract']].head())
        
    finally:
        scraper.close()

def example_custom_columns():
    """Demonstrate usage with custom column names"""
    print("\n=== Custom Columns Example ===")
    
    # Create CSV with different column names
    sample_data = {
        'ID': ['P123456'],
        'URL': ['https://projects.worldbank.org/en/projects-operations/project-detail/P178545'],
        'Name': ['Test Project']
    }
    
    df = pd.DataFrame(sample_data)
    custom_csv = 'custom_columns.csv'
    df.to_csv(custom_csv, index=False)
    
    scraper = WorldBankScraper(headless=True, delay=2)
    
    try:
        # Process with custom column names
        output_file = scraper.process_csv(
            custom_csv,
            url_column='URL',           # Column containing URLs
            output_column='Full_Abstract'  # Name for new abstract column
        )
        print(f"Custom processing complete! Results saved to: {output_file}")
        
    finally:
        scraper.close()
        # Clean up example files
        if os.path.exists(custom_csv):
            os.remove(custom_csv)

if __name__ == "__main__":
    print("World Bank Abstract Scraper - Example Usage")
    print("=" * 50)
    
    try:
        # Run basic example
        example_basic_usage()
        
        # Run custom columns example
        example_custom_columns()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        print("\nTo use with your own CSV file:")
        print("python world_bank_scraper.py your_file.csv")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have installed the requirements:")
        print("pip install -r requirements.txt")
