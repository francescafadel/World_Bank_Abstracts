#!/usr/bin/env python3
"""
World Bank Abstract Scraper

This script reads a CSV file containing World Bank project URLs,
visits each URL to extract the full abstract, and adds the abstracts
to a new column in the CSV file.

Usage:
    python world_bank_scraper.py <input_csv_file>

The script will create a new CSV file with "_with_abstracts" added to the filename.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
        logging.FileHandler('world_bank_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WorldBankScraper:
    def __init__(self, headless=True, delay=2):
        """
        Initialize the scraper with Chrome WebDriver
        
        Args:
            headless (bool): Run browser in headless mode
            delay (int): Delay between requests in seconds
        """
        self.delay = delay
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.7258.128 Safari/537.36")
        
        # Additional stability options
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        
        # Suppress ChromeDriver version warnings
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
            
            # Set up service with logging disabled to reduce noise
            service = Service()
            service.log_path = "/dev/null"  # Suppress logs on macOS/Linux
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
            
    def extract_abstract(self, url):
        """
        Extract the full abstract from a World Bank project URL
        
        Args:
            url (str): The World Bank project URL
            
        Returns:
            str: The full abstract text, or empty string if not found
        """
        try:
            logger.info(f"Processing URL: {url}")
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for the abstract section
            abstract_text = ""
            
            # Try different selectors for the abstract
            abstract_selectors = [
                # Look for abstract heading and following content
                "//h2[contains(text(), 'Abstract')]/following-sibling::*",
                "//h3[contains(text(), 'Abstract')]/following-sibling::*",
                "//div[contains(@class, 'abstract')]",
                "//section[contains(@class, 'abstract')]",
                # Look for Project Development Objective (PDO) which is often the abstract
                "//h2[contains(text(), 'Project Development Objective')]/following-sibling::*",
                "//h3[contains(text(), 'Project Development Objective')]/following-sibling::*",
                "//div[contains(text(), 'Project Development Objective')]/../following-sibling::*",
                # Look for Description sections
                "//h2[contains(text(), 'Description')]/following-sibling::*",
                "//h3[contains(text(), 'Description')]/following-sibling::*",
                # Look for specific World Bank page structure
                "//div[contains(@class, 'project-details')]//div[contains(text(), 'Abstract')]/../following-sibling::div",
                "//div[contains(@class, 'project-summary')]",
                "//div[contains(@class, 'project-description')]",
                # More generic selectors
                "//*[contains(text(), 'Abstract')]/following-sibling::*",
                "//*[contains(text(), 'Abstract')]/../following-sibling::*",
                # Look for summary or overview sections
                "//div[contains(@class, 'summary')]",
                "//div[contains(@class, 'overview')]",
                # CSS selectors converted to XPath
                "//div[@class='summary-section']",
                "//div[@class='project-abstract']",
                "//div[@id='abstract']",
                "//div[@id='summary']"
            ]
            
            for selector in abstract_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        # Check if there's a "Show More" or "Show Less" button
                        try:
                            show_more_button = self.driver.find_element(
                                By.XPATH, "//button[contains(text(), 'Show More')] | //a[contains(text(), 'Show More')] | //span[contains(text(), 'Show More')]"
                            )
                            if show_more_button.is_displayed():
                                logger.info("Found 'Show More' button, clicking to expand abstract")
                                self.driver.execute_script("arguments[0].click();", show_more_button)
                                time.sleep(2)  # Wait for content to expand
                        except NoSuchElementException:
                            # No "Show More" button found, that's okay
                            pass
                        
                        # Extract text from all matching elements
                        for element in elements:
                            text = element.get_attribute('textContent').strip()
                            if text and len(text) > 50:  # Only consider substantial text
                                abstract_text += text + " "
                        
                        if abstract_text.strip():
                            logger.info(f"Abstract found using selector: {selector}")
                            break
                            
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # If no abstract found with selectors, try to find it in the page source
            if not abstract_text.strip():
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Look for common patterns in World Bank pages
                patterns = [
                    soup.find('div', {'class': lambda x: x and 'abstract' in x.lower()}),
                    soup.find('div', {'id': lambda x: x and 'abstract' in x.lower()}),
                    soup.find('section', {'class': lambda x: x and 'abstract' in x.lower()}),
                    # Look for Project Development Objective
                    soup.find('div', string=lambda text: text and 'Project Development Objective' in text),
                    soup.find('h2', string=lambda text: text and 'Project Development Objective' in text),
                    soup.find('h3', string=lambda text: text and 'Project Development Objective' in text),
                    # Look for Description sections
                    soup.find('div', {'class': lambda x: x and 'description' in x.lower()}),
                    soup.find('div', {'class': lambda x: x and 'summary' in x.lower()}),
                    soup.find('div', {'class': lambda x: x and 'overview' in x.lower()}),
                    # Look for common World Bank specific classes
                    soup.find('div', {'class': lambda x: x and 'project' in x.lower() and 'details' in x.lower()}),
                    soup.find('div', {'class': lambda x: x and 'project' in x.lower() and 'summary' in x.lower()}),
                ]
                
                for pattern in patterns:
                    if pattern:
                        abstract_text = pattern.get_text().strip()
                        if abstract_text:
                            logger.info("Abstract found using BeautifulSoup pattern matching")
                            break
            
            # Clean up the abstract text
            if abstract_text:
                # Remove extra whitespace and normalize
                abstract_text = ' '.join(abstract_text.split())
                # Remove common prefixes
                prefixes_to_remove = ['Abstract*', 'Abstract:', 'Abstract', 'Project Abstract:', 'Project Abstract']
                for prefix in prefixes_to_remove:
                    if abstract_text.startswith(prefix):
                        abstract_text = abstract_text[len(prefix):].strip()
                
                logger.info(f"Successfully extracted abstract ({len(abstract_text)} characters)")
                return abstract_text
            else:
                logger.warning(f"No abstract found for URL: {url}")
                return ""
                
        except TimeoutException:
            logger.error(f"Timeout while loading URL: {url}")
            return ""
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return ""
        finally:
            # Add delay between requests
            time.sleep(self.delay)
    
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
    
    def close(self):
        """Close the WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    parser = argparse.ArgumentParser(description='Extract World Bank project abstracts from URLs in a CSV file')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('--url-column', default='Project URL', help='Name of column containing URLs (default: "Project URL")')
    parser.add_argument('--output-column', default='Abstract', help='Name of column to add abstracts to (default: "Abstract")')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode (default: True)')
    parser.add_argument('--delay', type=int, default=2, help='Delay between requests in seconds (default: 2)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    scraper = None
    try:
        # Initialize scraper
        scraper = WorldBankScraper(headless=args.headless, delay=args.delay)
        
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
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
