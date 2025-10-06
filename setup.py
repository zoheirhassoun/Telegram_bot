#!/usr/bin/env python3
"""
Setup script for Telegram Bot with Google Sheets Integration
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_env_file():
    """Check if .env file exists"""
    if os.path.exists('.env'):
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("Please copy env_example.txt to .env and fill in your values:")
        print("  - TELEGRAM_BOT_TOKEN (from BotFather)")
        print("  - GOOGLE_SHEET_ID (from your Google Sheet URL)")
        return False

def check_credentials():
    """Check if credentials.json exists"""
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found")
        return True
    else:
        print("⚠️  credentials.json not found")
        print("Please download it from Google Cloud Console:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Enable Google Sheets API")
        print("  3. Create OAuth 2.0 credentials")
        print("  4. Download as credentials.json")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Telegram Bot with Google Sheets Integration")
    print("=" * 60)
    
    # Install packages
    if not install_requirements():
        return
    
    print("\n📋 Checking configuration files...")
    
    # Check configuration files
    env_ok = check_env_file()
    creds_ok = check_credentials()
    
    print("\n" + "=" * 60)
    
    if env_ok and creds_ok:
        print("🎉 Setup complete! You can now run: python telegram_bot.py")
    else:
        print("⚠️  Please complete the missing configuration steps above")
        print("Then run: python telegram_bot.py")

if __name__ == "__main__":
    main()
