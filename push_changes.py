#!/usr/bin/env python3
"""
Simple script to push changes to git repository
"""

import subprocess
import sys

def run_git_command(command, description):
    """Run a git command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} successful")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    print("🚀 Pushing changes to git repository...")
    print("=" * 50)
    
    # Check git status
    if not run_git_command("git status --porcelain", "Checking git status"):
        return
    
    # Add all changes
    if not run_git_command("git add -A", "Adding changes to staging"):
        return
    
    # Commit changes
    commit_message = "Enhanced data processing with name parsing and phone formatting features"
    if not run_git_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("ℹ️ No changes to commit or commit failed")
    
    # Push to remote
    if not run_git_command("git push origin main", "Pushing to remote repository"):
        return
    
    print("\n🎉 Changes successfully pushed to git!")
    print("🌐 Your Streamlit app should update automatically within a few minutes")

if __name__ == "__main__":
    main() 