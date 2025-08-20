#!/usr/bin/env python3
"""
Setup script for World Bank Abstract Scraper

This script helps you install dependencies and verify the setup.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.7+")
        return False

def install_requirements():
    """Install required packages"""
    if os.path.exists('requirements.txt'):
        return run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements")
    else:
        print("❌ requirements.txt not found")
        return False

def check_chrome():
    """Check if Chrome is installed"""
    try:
        result = subprocess.run(['which', 'google-chrome'], capture_output=True)
        if result.returncode == 0:
            print("✅ Google Chrome found")
            return True
        else:
            # Try alternative Chrome locations
            chrome_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/usr/bin/google-chrome',
                '/usr/local/bin/google-chrome'
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    print("✅ Google Chrome found")
                    return True
            print("❌ Google Chrome not found. Please install Chrome browser")
            return False
    except Exception as e:
        print(f"❌ Error checking for Chrome: {e}")
        return False

def test_imports():
    """Test if all required packages can be imported"""
    print("\nTesting package imports...")
    packages = ['pandas', 'requests', 'bs4', 'selenium']
    all_good = True
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {package}: {e}")
            all_good = False
    
    return all_good

def main():
    """Main setup function"""
    print("World Bank Abstract Scraper - Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Check Chrome browser
    if not check_chrome():
        success = False
    
    # Test imports
    if not test_imports():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nYou can now use the scraper:")
        print("python world_bank_scraper.py your_file.csv")
        print("\nOr run the example:")
        print("python example_usage.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("\nFor help, check the README.md file.")

if __name__ == "__main__":
    main()
