#!/usr/bin/env python3
"""
Script to identify remaining projects that haven't been processed yet
"""

import pandas as pd
import os

def identify_remaining_projects():
    """Identify projects from main dataset that haven't been processed yet"""
    
    print("🔍 Identifying remaining projects to process...")
    
    # Read the main dataset
    print("📖 Reading main dataset...")
    main_df = pd.read_csv('cleaned_world_bank_data.csv')
    print(f"   Main dataset: {len(main_df)} projects")
    
    # Read the already processed dataset
    print("📖 Reading processed dataset...")
    processed_df = pd.read_csv('priority_projects_with_abstracts.csv')
    print(f"   Already processed: {len(processed_df)} projects")
    
    # Get project IDs from both datasets
    main_project_ids = set(main_df['Project Id'].tolist())
    processed_project_ids = set(processed_df['Project Id'].tolist())
    
    # Find remaining projects
    remaining_project_ids = main_project_ids - processed_project_ids
    print(f"   Remaining to process: {len(remaining_project_ids)} projects")
    
    # Create dataframe with remaining projects
    remaining_df = main_df[main_df['Project Id'].isin(remaining_project_ids)].copy()
    
    # Save remaining projects
    output_file = 'remaining_projects_to_process.csv'
    remaining_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Remaining projects saved to: {output_file}")
    print(f"📊 Summary:")
    print(f"   - Total projects in main dataset: {len(main_df)}")
    print(f"   - Already processed: {len(processed_df)}")
    print(f"   - Remaining to process: {len(remaining_df)}")
    
    # Show some sample remaining projects
    print(f"\n📋 Sample remaining projects:")
    for i, (_, row) in enumerate(remaining_df.head(5).iterrows()):
        print(f"   {i+1}. {row['Project Id']} - {row['Project Name'][:50]}...")
    
    return output_file

if __name__ == "__main__":
    identify_remaining_projects()
