#!/usr/bin/env python3
"""
Launcher script for HAR Scraper + TREC Enricher
This script will automatically install dependencies and run the application.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("🔧 Installing required packages...")
    try:
        subprocess.check_call(["python3", "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies. Please run manually:")
        print("pip install -r requirements.txt")
        sys.exit(1)

def run_streamlit_app():
    """Run the Streamlit application"""
    print("🚀 Starting HAR Scraper + TREC Enricher...")
    try:
        subprocess.run(["python3", "-m", "streamlit", "run", "har_trec_enricher.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

def main():
    print("🏠 HAR Scraper + TREC Enricher Launcher")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Check if main application file exists
    if not os.path.exists("har_trec_enricher.py"):
        print("❌ har_trec_enricher.py not found!")
        sys.exit(1)
    
    # Install dependencies
    install_requirements()
    
    # Run the application
    run_streamlit_app()

if __name__ == "__main__":
    main() 