#!/usr/bin/env python3
"""
Filter High Priority Projects

This script filters the World Bank projects to focus on those most likely
to have abstracts available, making manual extraction more efficient.
"""

import pandas as pd
import sys
from datetime import datetime

def filter_projects(input_file):
    """Filter projects to focus on high-priority ones likely to have abstracts"""
    
    print("Loading project data...")
    df = pd.read_csv(input_file)
    
    print(f"Total projects: {len(df)}")
    
    # Create filtered datasets
    filters = {
        "recent_active": "Recent & Active Projects (2020+, Active Status)",
        "high_value": "High Value Projects ($10M+)",
        "recent_approved": "Recently Approved Projects (2022+)",
        "sample_mix": "Sample Mix (Every 5th Project)"
    }
    
    filtered_data = {}
    
    # Filter 1: Recent and Active Projects
    recent_active = df[
        (df['Last Stage Reached'].str.contains('APPROVED|APPRAISAL', na=False)) &
        (pd.to_datetime(df['Board Approval Date'], errors='coerce') >= '2020-01-01')
    ].copy()
    filtered_data["recent_active"] = recent_active
    
    # Filter 2: High Value Projects (IDA + IBRD > 10M)
    df['Total_IBRD_IDA_clean'] = pd.to_numeric(df['Total IBRD, IDA and GRANT Commitment $US'], errors='coerce')
    high_value = df[df['Total_IBRD_IDA_clean'] >= 10000000].copy()
    filtered_data["high_value"] = high_value
    
    # Filter 3: Recently Approved (2022+)
    recent_approved = df[
        pd.to_datetime(df['Board Approval Date'], errors='coerce') >= '2022-01-01'
    ].copy()
    filtered_data["recent_approved"] = recent_approved
    
    # Filter 4: Sample Mix - every 5th project
    sample_mix = df.iloc[::5].copy()
    filtered_data["sample_mix"] = sample_mix
    
    # Create output files
    for filter_name, description in filters.items():
        if filter_name in filtered_data and len(filtered_data[filter_name]) > 0:
            output_file = f"filtered_{filter_name}_projects.csv"
            filtered_data[filter_name].to_csv(output_file, index=False)
            
            print(f"\n{description}:")
            print(f"  File: {output_file}")
            print(f"  Count: {len(filtered_data[filter_name])} projects")
            print(f"  Estimated time: {len(filtered_data[filter_name]) * 30 / 3600:.1f} hours")
            
            # Show sample URLs
            sample_urls = filtered_data[filter_name]['Project URL'].head(3).tolist()
            print(f"  Sample URLs:")
            for i, url in enumerate(sample_urls, 1):
                print(f"    {i}. {url}")
    
    # Create a combined priority file (recent + high value, deduplicated)
    priority_projects = pd.concat([recent_active, high_value]).drop_duplicates(subset=['Project Id'])
    priority_file = "priority_projects.csv"
    priority_projects.to_csv(priority_file, index=False)
    
    print(f"\n{'='*60}")
    print(f"RECOMMENDED: {priority_file}")
    print(f"Combined recent & high-value projects: {len(priority_projects)} projects")
    print(f"Estimated time: {len(priority_projects) * 30 / 3600:.1f} hours")
    print(f"{'='*60}")
    
    # Summary statistics
    print(f"\nSUMMARY:")
    print(f"Original dataset: {len(df)} projects")
    print(f"Filtered options:")
    for filter_name, description in filters.items():
        if filter_name in filtered_data:
            count = len(filtered_data[filter_name])
            percentage = (count / len(df)) * 100
            print(f"  {description}: {count} ({percentage:.1f}%)")
    print(f"  Priority combination: {len(priority_projects)} ({(len(priority_projects) / len(df)) * 100:.1f}%)")

def main():
    if len(sys.argv) != 2:
        print("Usage: python filter_high_priority_projects.py <input_csv_file>")
        print("Example: python filter_high_priority_projects.py cleaned_world_bank_data.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    filter_projects(input_file)

if __name__ == "__main__":
    main()
