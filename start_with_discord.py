#!/usr/bin/env python3
"""
Start Line Walrus with Discord Bot
Runs both the web application and Discord bot together
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

def run_web_app():
    """Run the Line Walrus web application"""
    print("🌐 Starting Line Walrus web application...")
    try:
        subprocess.run([sys.executable, "app_simple.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Web app stopped by user")
    except Exception as e:
        print(f"❌ Web app error: {e}")

def run_discord_bot():
    """Run the Discord bot"""
    print("🤖 Starting Discord bot...")
    try:
        subprocess.run([sys.executable, "discord_bot.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Discord bot stopped by user")
    except Exception as e:
        print(f"❌ Discord bot error: {e}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import discord
        print("✅ discord.py installed")
    except ImportError:
        print("❌ discord.py not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "discord.py>=2.3.0", "aiohttp>=3.8.0", "python-dotenv>=1.0.0"])
    
    try:
        import aiohttp
        print("✅ aiohttp installed")
    except ImportError:
        print("❌ aiohttp not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "aiohttp>=3.8.0"])
    
    try:
        import dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv>=1.0.0"])

def check_environment():
    """Check environment variables"""
    print("🔧 Checking environment variables...")
    
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    if not discord_token:
        print("⚠️  DISCORD_BOT_TOKEN not set")
        print("   Set it in your environment or create a .env file")
        return False
    
    if discord_token == 'your_discord_bot_token_here':
        print("⚠️  Please set a real Discord bot token")
        return False
    
    print("✅ Discord bot token found")
    
    line_walrus_url = os.getenv('LINE_WALRUS_URL', 'http://localhost:5001')
    print(f"✅ Line Walrus URL: {line_walrus_url}")
    
    return True

def main():
    """Main function"""
    print("🦭 Line Walrus with Discord Bot")
    print("=" * 40)
    
    # Check dependencies
    check_dependencies()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment setup incomplete. Please check your configuration.")
        print("📚 See discord_bot_setup.md for setup instructions")
        return
    
    print("\n🚀 Starting both services...")
    print("   Web app will run on http://localhost:5001")
    print("   Discord bot will connect to your server")
    print("   Press Ctrl+C to stop both services")
    print("-" * 40)
    
    # Start web app in a separate thread
    web_thread = threading.Thread(target=run_web_app, daemon=True)
    web_thread.start()
    
    # Wait a moment for web app to start
    time.sleep(3)
    
    # Start Discord bot in main thread
    try:
        run_discord_bot()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        print("✅ Both services stopped")

if __name__ == "__main__":
    main()
