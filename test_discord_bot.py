#!/usr/bin/env python3
"""
Test script for Line Walrus Discord Bot
Tests API connectivity and bot functionality
"""

import asyncio
import aiohttp
import os
from discord_bot import LineWalrusBot

async def test_api_connection():
    """Test connection to Line Walrus API"""
    print("🔍 Testing Line Walrus API connection...")
    
    line_walrus_url = os.getenv('LINE_WALRUS_URL', 'http://localhost:5001')
    print(f"📡 API URL: {line_walrus_url}")
    
    bot = LineWalrusBot()
    
    # Test players endpoint
    print("\n👥 Testing /api/players endpoint...")
    players = await bot.api_request('/api/players')
    if players:
        print(f"✅ Players endpoint working - {len(players)} players found")
        if players:
            print(f"   Sample player: {players[0]['name']}")
    else:
        print("❌ Players endpoint failed")
    
    # Test lines endpoint
    print("\n🏒 Testing /api/lines endpoint...")
    lines = await bot.api_request('/api/lines')
    if lines:
        print("✅ Lines endpoint working")
        for line_num, line in lines.items():
            if line and any(line.values()):
                print(f"   Line {line_num}: {len([p for p in line.values() if p])} players")
    else:
        print("❌ Lines endpoint failed")
    
    # Test teams endpoint
    print("\n📂 Testing /api/teams/list endpoint...")
    teams = await bot.api_request('/api/teams/list')
    if teams:
        print(f"✅ Teams endpoint working - {len(teams)} teams found")
        for team in teams:
            print(f"   Team: {team['name']} ({team['player_count']} players)")
    else:
        print("❌ Teams endpoint failed")
    
    # Test embed formatting
    print("\n🎨 Testing embed formatting...")
    if lines and players:
        try:
            lines_embed = bot.format_lines_embed(lines, "Test Team")
            print("✅ Lines embed formatting working")
            
            players_embed = bot.format_players_embed(players, "Test Team")
            print("✅ Players embed formatting working")
        except Exception as e:
            print(f"❌ Embed formatting failed: {e}")
    
    # Close session
    if bot.session and not bot.session.closed:
        await bot.session.close()
    
    print("\n🎯 API connection test complete!")

async def test_discord_bot():
    """Test Discord bot functionality"""
    print("\n🤖 Testing Discord bot setup...")
    
    # Check environment variables
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    if not discord_token:
        print("❌ DISCORD_BOT_TOKEN not set")
        return False
    
    if discord_token == 'your_discord_bot_token_here':
        print("❌ Please set a real Discord bot token")
        return False
    
    print("✅ Discord bot token found")
    
    # Check if discord.py is available
    try:
        import discord
        print(f"✅ discord.py version: {discord.__version__}")
    except ImportError:
        print("❌ discord.py not installed. Run: pip install -r discord_requirements.txt")
        return False
    
    print("✅ Discord bot setup looks good!")
    return True

def main():
    """Main test function"""
    print("🦭 Line Walrus Discord Bot Test")
    print("=" * 40)
    
    # Test Discord bot setup
    discord_ok = asyncio.run(test_discord_bot())
    
    # Test API connection
    asyncio.run(test_api_connection())
    
    print("\n" + "=" * 40)
    if discord_ok:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("💡 Run 'python discord_bot.py' to start the bot")
    else:
        print("⚠️  Some tests failed. Check the setup instructions.")
    
    print("\n📚 For setup help, see discord_bot_setup.md")

if __name__ == "__main__":
    main()
