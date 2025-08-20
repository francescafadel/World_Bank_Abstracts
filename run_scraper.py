#!/usr/bin/env python3
"""
Launcher script for the World Bank Abstracts Extractor

This script provides an easy way to run the main API scraper from the root directory.
"""

import sys
import os
import argparse

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(
        description='World Bank Abstracts Extractor - Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py data/your_file.csv
  python run_scraper.py data/your_file.csv --delay 2
  python run_scraper.py data/your_file.csv --test 5
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the input CSV file (relative to data/ directory)'
    )
    
    parser.add_argument(
        '--delay',
        type=int,
        default=1,
        help='Delay between requests in seconds (default: 1)'
    )
    
    parser.add_argument(
        '--test',
        type=int,
        help='Test mode: process only the first N projects'
    )
    
    parser.add_argument(
        '--url-column',
        default='Project URL',
        help='Name of the column containing URLs (default: "Project URL")'
    )
    
    parser.add_argument(
        '--output-column',
        default='Abstract',
        help='Name of the new column for abstracts (default: "Abstract")'
    )
    
    args = parser.parse_args()
    
    # Import the scraper
    try:
        from api_scraper import WorldBankAPIScraper
    except ImportError as e:
        print(f"Error: Could not import api_scraper. Make sure you're in the project root directory.")
        print(f"Import error: {e}")
        sys.exit(1)
    
    # Check if input file exists
    input_path = args.input_file
    if not os.path.exists(input_path):
        # Try with data/ prefix
        data_path = os.path.join('data', args.input_file)
        if os.path.exists(data_path):
            input_path = data_path
        else:
            print(f"Error: Input file not found: {args.input_file}")
            print(f"Tried: {input_path} and {data_path}")
            sys.exit(1)
    
    print("🚀 World Bank Abstracts Extractor")
    print("=" * 50)
    print(f"Input file: {input_path}")
    print(f"Delay: {args.delay} seconds")
    if args.test:
        print(f"Test mode: processing first {args.test} projects")
    print("=" * 50)
    
    # Initialize and run the scraper
    scraper = WorldBankAPIScraper(delay=args.delay)
    
    try:
        if args.test:
            # Test mode - create a temporary file with only the first N rows
            import pandas as pd
            df = pd.read_csv(input_path)
            test_df = df.head(args.test)
            test_file = f"test_{os.path.basename(input_path)}"
            test_df.to_csv(test_file, index=False)
            print(f"📋 Test mode: Processing first {args.test} projects from {len(df)} total")
            
            try:
                scraper.process_csv(
                    test_file,
                    url_column=args.url_column,
                    output_column=args.output_column
                )
            finally:
                # Clean up test file
                if os.path.exists(test_file):
                    os.remove(test_file)
        else:
            # Full processing
            scraper.process_csv(
                input_path,
                url_column=args.url_column,
                output_column=args.output_column
            )
            
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        sys.exit(1)
    
    print("\n✅ Processing complete!")

if __name__ == "__main__":
    main()
