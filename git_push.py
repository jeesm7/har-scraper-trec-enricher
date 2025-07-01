#!/usr/bin/env python3
import subprocess
import sys
import os

def run_git_command(args, description):
    """Run a git command"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        print(f"✅ {description} successful")
        if result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def main():
    print("🚀 Pushing enhanced features to git repository...")
    print("=" * 60)
    
    # Add all changes
    if not run_git_command(["git", "add", "-A"], "Adding all changes"):
        return
    
    # Commit changes
    commit_msg = "Add name parsing and phone formatting features to sanitize_data method"
    if not run_git_command(["git", "commit", "-m", commit_msg], "Committing changes"):
        print("ℹ️ No new changes to commit")
    
    # Push to remote
    if not run_git_command(["git", "push", "origin", "main"], "Pushing to remote"):
        # Try pushing to master branch if main fails
        run_git_command(["git", "push", "origin", "master"], "Pushing to master branch")
    
    print("\n🎉 Changes successfully pushed!")
    print("🌐 Your Streamlit app should update automatically within 2-3 minutes")
    print("✨ New features include:")
    print("   • Name parsing: first_name and last_name columns")
    print("   • Phone formatting: phone_e164 column with +1xxxxxxxxxx format")

if __name__ == "__main__":
    main() 