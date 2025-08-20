#!/usr/bin/env python3
"""
Simple World Bank Abstract Scraper (Backup Version)

This is a simpler version that uses requests and BeautifulSoup only,
without Selenium. This won't handle JavaScript "Show More" buttons,
but will work for basic abstract extraction.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import sys
import os
import logging
from urllib.parse import urlparse
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleWorldBankScraper:
    def __init__(self, delay=2):
        """
        Initialize the simple scraper
        
        Args:
            delay (int): Delay between requests in seconds
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.7258.128 Safari/537.36'
        })
        
    def extract_abstract(self, url):
        """
        Extract the abstract from a World Bank project URL using requests/BeautifulSoup
        
        Args:
            url (str): The World Bank project URL
            
        Returns:
            str: The abstract text, or empty string if not found
        """
        try:
            logger.info(f"Processing URL: {url}")
            
            # Make request
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            abstract_text = ""
            
            # Try multiple strategies to find the abstract
            strategies = [
                # Strategy 1: Look for elements containing "Abstract"
                lambda: self._find_by_text_content(soup, "Abstract"),
                # Strategy 2: Look for Project Development Objective
                lambda: self._find_by_text_content(soup, "Project Development Objective"),
                # Strategy 3: Look for description sections
                lambda: self._find_by_text_content(soup, "Description"),
                # Strategy 4: Look for common CSS classes
                lambda: self._find_by_classes(soup),
                # Strategy 5: Look for summary content
                lambda: self._find_by_text_content(soup, "Summary"),
            ]
            
            for i, strategy in enumerate(strategies, 1):
                try:
                    result = strategy()
                    if result and len(result.strip()) > 50:  # Only consider substantial text
                        abstract_text = result
                        logger.info(f"Abstract found using strategy {i}")
                        break
                except Exception as e:
                    logger.debug(f"Strategy {i} failed: {e}")
                    continue
            
            if abstract_text:
                # Clean up the text
                abstract_text = self._clean_text(abstract_text)
                logger.info(f"Successfully extracted abstract ({len(abstract_text)} characters)")
                return abstract_text
            else:
                logger.warning(f"No abstract found for URL: {url}")
                return ""
                
        except requests.RequestException as e:
            logger.error(f"Network error for URL {url}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return ""
        finally:
            # Add delay between requests
            time.sleep(self.delay)
    
    def _find_by_text_content(self, soup, search_text):
        """Find abstract by looking for specific text content"""
        # Look for headings containing the search text
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=lambda text: text and search_text.lower() in text.lower())
        
        for heading in headings:
            # Get the next sibling elements that might contain the abstract
            next_elements = []
            current = heading.find_next_sibling()
            
            # Collect following elements until we hit another heading or section
            while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                if current.name in ['p', 'div', 'span'] and current.get_text().strip():
                    next_elements.append(current.get_text().strip())
                current = current.find_next_sibling()
                if len(next_elements) > 5:  # Don't go too far
                    break
            
            if next_elements:
                return ' '.join(next_elements)
        
        # Also look for divs/spans that contain the search text directly
        containers = soup.find_all(['div', 'section', 'article'], string=lambda text: text and search_text.lower() in text.lower())
        for container in containers:
            text = container.get_text().strip()
            if len(text) > 50:
                return text
        
        return ""
    
    def _find_by_classes(self, soup):
        """Find abstract by looking for common CSS classes"""
        class_patterns = [
            'abstract', 'project-abstract', 'summary', 'description', 
            'project-description', 'project-summary', 'overview',
            'project-details', 'content', 'main-content'
        ]
        
        for pattern in class_patterns:
            # Look for exact class matches
            elements = soup.find_all(['div', 'section', 'article'], class_=lambda x: x and pattern in x)
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 50:
                    return text
            
            # Look for class names containing the pattern
            elements = soup.find_all(['div', 'section', 'article'], class_=lambda x: x and any(pattern in cls.lower() for cls in x))
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 50:
                    return text
        
        return ""
    
    def _clean_text(self, text):
        """Clean and normalize the extracted text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common prefixes
        prefixes_to_remove = [
            'Abstract*', 'Abstract:', 'Abstract', 'Project Abstract:', 
            'Project Abstract', 'Project Development Objective:', 
            'Project Development Objective', 'Description:', 'Description'
        ]
        
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        return text
    
    def process_csv(self, input_file, url_column='Project URL', output_column='Abstract'):
        """
        Process a CSV file to extract abstracts for all URLs
        
        Args:
            input_file (str): Path to input CSV file
            url_column (str): Name of column containing URLs
            output_column (str): Name of column to add abstracts to
            
        Returns:
            str: Path to output CSV file
        """
        try:
            # Read the CSV file
            logger.info(f"Reading CSV file: {input_file}")
            df = pd.read_csv(input_file)
            
            if url_column not in df.columns:
                available_columns = ', '.join(df.columns.tolist())
                raise ValueError(f"Column '{url_column}' not found in CSV. Available columns: {available_columns}")
            
            # Initialize the abstract column
            df[output_column] = ""
            
            # Process each URL
            total_urls = len(df)
            logger.info(f"Processing {total_urls} URLs...")
            
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
            
            # Save the updated CSV
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
    parser = argparse.ArgumentParser(description='Extract World Bank project abstracts from URLs in a CSV file (Simple version)')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('--url-column', default='Project URL', help='Name of column containing URLs (default: "Project URL")')
    parser.add_argument('--output-column', default='Abstract', help='Name of column to add abstracts to (default: "Abstract")')
    parser.add_argument('--delay', type=int, default=2, help='Delay between requests in seconds (default: 2)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    try:
        # Initialize scraper
        scraper = SimpleWorldBankScraper(delay=args.delay)
        
        # Process the CSV file
        output_file = scraper.process_csv(
            args.input_file, 
            url_column=args.url_column,
            output_column=args.output_column
        )
        
        print(f"\nProcessing complete!")
        print(f"Output file: {output_file}")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
