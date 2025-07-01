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

def push_git_changes():
    """Push changes to git repository"""
    print("🚀 Pushing enhanced features to git repository...")
    print("=" * 60)
    
    try:
        # Add all changes
        print("🔄 Adding changes...")
        subprocess.run(["git", "add", "-A"], check=True)
        print("✅ Changes added to staging")
        
        # Commit changes
        print("🔄 Committing changes...")
        commit_msg = "Add name parsing and phone formatting features"
        result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Changes committed successfully")
        else:
            print("ℹ️ No new changes to commit")
        
        # Push to remote
        print("🔄 Pushing to remote repository...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Successfully pushed to main branch")
        
        print("\n🎉 Changes successfully deployed!")
        print("🌐 Your Streamlit app should update automatically within 2-3 minutes")
        print("✨ New features include:")
        print("   • Name parsing: first_name and last_name columns")
        print("   • Phone formatting: phone_e164 column with +1xxxxxxxxxx format")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        print("Please check your git configuration and try again")

def run_streamlit_app():
    """Run the Streamlit application"""
    print("🚀 Starting HAR Scraper + TREC Enricher...")
    try:
        subprocess.run(["python3", "-m", "streamlit", "run", "har_trec_enricher.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

def run_command(cmd, description):
    print(f"🔄 {description}...")
    result = os.system(cmd)
    if result == 0:
        print(f"✅ {description} completed")
        return True
    else:
        print(f"❌ {description} failed")
        return False

def main():
    print("🏠 HAR Scraper + TREC Enricher Launcher")
    print("=" * 50)
    
    # Check for push flag
    if len(sys.argv) > 1 and sys.argv[1] == "--push":
        push_git_changes()
        return
    
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

    # Git add, commit, and push
    commands = [
        ("git add .", "Adding changes to staging"),
        ('git commit -m "Add name parsing and phone formatting features"', "Committing changes"),
        ("git push origin main", "Pushing to remote repository")
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            # Try alternative for push

if __name__ == "__main__":
    main() 