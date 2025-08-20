#!/usr/bin/env python3
"""
World Bank API Abstract Scraper

This script uses the World Bank's official API to extract project abstracts
directly from their JSON API, avoiding all the JavaScript/HTML parsing issues.
"""

import pandas as pd
import requests
import json
import time
import sys
import os
import logging
import argparse
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WorldBankAPIScraper:
    def __init__(self, delay=1):
        """
        Initialize the API scraper
        
        Args:
            delay (int): Delay between API requests in seconds
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
    def extract_project_id(self, url):
        """Extract project ID from World Bank URL"""
        # Pattern: https://projects.worldbank.org/en/projects-operations/project-detail/P123456
        match = re.search(r'/project-detail/(P\d+)', url)
        if match:
            return match.group(1)
        return None
        
    def get_project_data(self, project_id):
        """
        Get project data from World Bank API
        
        Args:
            project_id (str): Project ID (e.g., 'P123456')
            
        Returns:
            dict: Project data including abstract
        """
        try:
            # World Bank API endpoint
            api_url = f"https://search.worldbank.org/api/v3/projects?format=json&fl=*&qterm={project_id}"
            
            logger.info(f"Fetching data for project: {project_id}")
            
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'projects' in data and project_id in data['projects']:
                project = data['projects'][project_id]
                return project
            else:
                logger.warning(f"No project data found for {project_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching data for {project_id}: {e}")
            return None
    
    def extract_abstract(self, url):
        """
        Extract abstract from World Bank project URL using API
        
        Args:
            url (str): World Bank project URL
            
        Returns:
            str: Abstract text or empty string
        """
        try:
            # Extract project ID from URL
            project_id = self.extract_project_id(url)
            if not project_id:
                logger.warning(f"Could not extract project ID from URL: {url}")
                return ""
            
            # Get project data from API
            project_data = self.get_project_data(project_id)
            if not project_data:
                return ""
            
            # Extract abstract from different possible fields
            abstract = ""
            
            # Try different field names that might contain the abstract
            abstract_fields = [
                'project_abstract',  # Full project abstract (most complete)
                'abstract',
                'description',
                'summary',
                'project_description',
                'project_summary'
            ]
            
            for field in abstract_fields:
                if field in project_data and project_data[field]:
                    abstract = str(project_data[field]).strip()
                    if len(abstract) > 50:  # Only consider substantial text
                        logger.info(f"Found abstract in field '{field}' ({len(abstract)} characters)")
                        break
            
            if abstract:
                # Clean up the text
                abstract = self._clean_text(abstract)
                logger.info(f"Successfully extracted abstract for {project_id}")
                return abstract
            else:
                logger.warning(f"No abstract found for project {project_id}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting abstract from {url}: {e}")
            return ""
        finally:
            # Add delay between requests
            time.sleep(self.delay)
    
    def _clean_text(self, text):
        """Clean and normalize the extracted text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common prefixes
        prefixes_to_remove = [
            'Abstract*', 'Abstract:', 'Abstract', 
            'Project Abstract:', 'Project Abstract',
            'Project Development Objective:', 'Project Development Objective',
            'Description:', 'Description'
        ]
        
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        return text
    
    def process_csv(self, input_file, url_column='Project URL', output_column='Abstract'):
        """
        Process CSV file to extract abstracts using API
        
        Args:
            input_file (str): Path to input CSV file
            url_column (str): Name of column containing URLs
            output_column (str): Name of column to add abstracts to
            
        Returns:
            str: Path to output CSV file
        """
        try:
            # Read CSV file
            logger.info(f"Reading CSV file: {input_file}")
            df = pd.read_csv(input_file)
            
            if url_column not in df.columns:
                available_columns = ', '.join(df.columns.tolist())
                raise ValueError(f"Column '{url_column}' not found in CSV. Available columns: {available_columns}")
            
            # Initialize abstract column
            df[output_column] = ""
            
            # Process each URL
            total_urls = len(df)
            logger.info(f"Processing {total_urls} URLs using World Bank API...")
            
            for index, row in df.iterrows():
                url = row[url_column]
                if pd.isna(url) or not url.strip():
                    logger.warning(f"Row {index + 1}: Empty or invalid URL")
                    continue
                
                logger.info(f"Processing row {index + 1}/{total_urls}: {url}")
                
                try:
                    abstract = self.extract_abstract(url)
                    df.at[index, output_column] = abstract
                    
                    if abstract:
                        logger.info(f"Row {index + 1}: Abstract extracted successfully")
                    else:
                        logger.warning(f"Row {index + 1}: No abstract found")
                        
                except Exception as e:
                    logger.error(f"Row {index + 1}: Error processing URL - {e}")
                    df.at[index, output_column] = ""
            
            # Generate output filename
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_with_abstracts.csv"
            
            # Save updated CSV
            df.to_csv(output_file, index=False)
            logger.info(f"Results saved to: {output_file}")
            
            # Print summary
            successful_extractions = (df[output_column] != "").sum()
            logger.info(f"Summary: {successful_extractions}/{total_urls} abstracts extracted successfully")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Extract World Bank project abstracts using official API')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('--url-column', default='Project URL', help='Name of column containing URLs (default: "Project URL")')
    parser.add_argument('--output-column', default='Abstract', help='Name of column to add abstracts to (default: "Abstract")')
    parser.add_argument('--delay', type=int, default=1, help='Delay between API requests in seconds (default: 1)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    try:
        # Initialize scraper
        scraper = WorldBankAPIScraper(delay=args.delay)
        
        # Process CSV file
        output_file = scraper.process_csv(
            args.input_file, 
            url_column=args.url_column,
            output_column=args.output_column
        )
        
        print(f"\n🎉 Processing complete!")
        print(f"📁 Output file: {output_file}")
        print(f"⚡ This method uses the World Bank's official API - much faster and more reliable!")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
