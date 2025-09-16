#!/usr/bin/env python3
"""
Line Walrus Discord Bot
A Discord bot for managing hockey lines and sharing updates with teams.
"""

import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
LINE_WALRUS_URL = os.getenv('LINE_WALRUS_URL', 'http://localhost:5001')
BOT_PREFIX = '!'

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Create bot instance
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

class LineWalrusBot:
    def __init__(self):
        self.session = None
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def api_request(self, endpoint, method='GET', data=None):
        """Make API request to Line Walrus"""
        session = await self.get_session()
        url = f"{LINE_WALRUS_URL}{endpoint}"
        
        try:
            if method == 'GET':
                async with session.get(url) as response:
                    return await response.json()
            elif method == 'POST':
                async with session.post(url, json=data) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def format_lines_embed(self, lines_data, team_name="Current Team"):
        """Format lines data into a Discord embed"""
        embed = discord.Embed(
            title=f"🏒 {team_name} - Game Lines",
            color=0x1e3a8a,  # Blue color matching Line Walrus
            timestamp=datetime.now()
        )
        
        embed.set_footer(text="Line Walrus • Because Even a Walrus Can Manage Lines Better")
        
        for line_num, line in lines_data.items():
            if not line:
                continue
                
            line_title = f"Line {line_num}"
            line_text = ""
            
            # Forward positions
            forwards = []
            for pos in ['LW', 'C', 'RW']:
                player = line.get(pos)
                if player:
                    forwards.append(f"**{pos}:** {player['name']} #{player.get('jersey_number', '')}")
                else:
                    forwards.append(f"**{pos}:** *Empty*")
            
            # Defense positions
            defense = []
            for pos in ['LD', 'RD']:
                player = line.get(pos)
                if player:
                    defense.append(f"**{pos}:** {player['name']} #{player.get('jersey_number', '')}")
                else:
                    defense.append(f"**{pos}:** *Empty*")
            
            # Goalie
            goalie = line.get('G')
            if goalie:
                goalie_text = f"**G:** {goalie['name']} #{goalie.get('jersey_number', '')}"
            else:
                goalie_text = "**G:** *Empty*"
            
            line_text = "\n".join(forwards) + "\n" + "\n".join(defense) + "\n" + goalie_text
            
            embed.add_field(
                name=line_title,
                value=line_text,
                inline=False
            )
        
        return embed
    
    def format_players_embed(self, players_data, team_name="Current Team"):
        """Format players data into a Discord embed"""
        embed = discord.Embed(
            title=f"👥 {team_name} - Roster",
            color=0x3b82f6,  # Light blue
            timestamp=datetime.now()
        )
        
        # Separate players by position
        forwards = []
        defense = []
        goalies = []
        spares = []
        
        for player in players_data:
            name = player['name']
            jersey = player.get('jersey_number', '')
            position = player.get('roster_position', player.get('position', 'FORWARD'))
            affiliate = player.get('affiliate', False)
            
            player_text = f"#{jersey} {name}"
            if affiliate:
                player_text += " 🔄"
            
            if position == 'GOALIE':
                goalies.append(player_text)
            elif position == 'DEFENSE':
                defense.append(player_text)
            elif position == 'FORWARD':
                forwards.append(player_text)
            else:
                spares.append(player_text)
        
        if forwards:
            embed.add_field(
                name="🦵 Forwards",
                value="\n".join(forwards[:10]) + ("\n..." if len(forwards) > 10 else ""),
                inline=True
            )
        
        if defense:
            embed.add_field(
                name="🛡️ Defense",
                value="\n".join(defense[:10]) + ("\n..." if len(defense) > 10 else ""),
                inline=True
            )
        
        if goalies:
            embed.add_field(
                name="🥅 Goalies",
                value="\n".join(goalies),
                inline=True
            )
        
        if spares:
            embed.add_field(
                name="🔄 Spares",
                value="\n".join(spares[:5]) + ("\n..." if len(spares) > 5 else ""),
                inline=False
            )
        
        embed.set_footer(text="Line Walrus • Use !lines to see current line combinations")
        
        return embed

# Create bot instance
line_bot = LineWalrusBot()

@bot.event
async def on_ready():
    """Bot ready event"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status
    activity = discord.Activity(type=discord.ActivityType.watching, name="hockey lines 🏒")
    await bot.change_presence(activity=activity)

@bot.command(name='lines', help='Show current line combinations')
async def show_lines(ctx):
    """Show current lines"""
    await ctx.trigger_typing()
    
    # Get lines data
    lines_data = await line_bot.api_request('/api/lines')
    if not lines_data:
        await ctx.send("❌ Could not fetch lines data. Make sure Line Walrus is running!")
        return
    
    # Get team name
    team_data = await line_bot.api_request('/api/teams/list')
    team_name = "Current Team"
    if team_data and len(team_data) > 0:
        team_name = team_data[0].get('name', 'Current Team')
    
    # Format and send embed
    embed = line_bot.format_lines_embed(lines_data, team_name)
    await ctx.send(embed=embed)

@bot.command(name='roster', help='Show team roster')
async def show_roster(ctx):
    """Show team roster"""
    await ctx.trigger_typing()
    
    # Get players data
    players_data = await line_bot.api_request('/api/players')
    if not players_data:
        await ctx.send("❌ Could not fetch roster data. Make sure Line Walrus is running!")
        return
    
    # Get team name
    team_data = await line_bot.api_request('/api/teams/list')
    team_name = "Current Team"
    if team_data and len(team_data) > 0:
        team_name = team_data[0].get('name', 'Current Team')
    
    # Format and send embed
    embed = line_bot.format_players_embed(players_data, team_name)
    await ctx.send(embed=embed)

@bot.command(name='teams', help='List available teams')
async def list_teams(ctx):
    """List available teams"""
    await ctx.trigger_typing()
    
    teams_data = await line_bot.api_request('/api/teams/list')
    if not teams_data:
        await ctx.send("❌ Could not fetch teams data. Make sure Line Walrus is running!")
        return
    
    if not teams_data:
        await ctx.send("📝 No teams found. Upload a CSV or create a team first!")
        return
    
    embed = discord.Embed(
        title="🏒 Available Teams",
        color=0x28a745,  # Green
        timestamp=datetime.now()
    )
    
    for team in teams_data:
        embed.add_field(
            name=f"📂 {team['name']}",
            value=f"{team['player_count']} players",
            inline=True
        )
    
    embed.set_footer(text="Line Walrus • Use !lines to see current lines")
    await ctx.send(embed=embed)

@bot.command(name='help_walrus', help='Show Line Walrus bot help')
async def help_walrus(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="🦭 Line Walrus Bot Help",
        description="Manage your hockey lines directly from Discord!",
        color=0x1e3a8a
    )
    
    embed.add_field(
        name="📋 Commands",
        value="""`!lines` - Show current line combinations
`!roster` - Show team roster
`!teams` - List available teams
`!help_walrus` - Show this help message""",
        inline=False
    )
    
    embed.add_field(
        name="🌐 Web App",
        value="Visit the full Line Walrus web app for advanced features like drag & drop, CSV upload, and line management.",
        inline=False
    )
    
    embed.add_field(
        name="🔗 Features",
        value="• Mobile-friendly line management\n• CSV import from SportNinja\n• Print and share lines\n• Real-time updates",
        inline=False
    )
    
    embed.set_footer(text="Line Walrus • Because Even a Walrus Can Manage Lines Better")
    await ctx.send(embed=embed)

@bot.command(name='status', help='Check bot and Line Walrus status')
async def check_status(ctx):
    """Check bot and Line Walrus status"""
    await ctx.trigger_typing()
    
    # Check Line Walrus API
    try:
        session = await line_bot.get_session()
        async with session.get(f"{LINE_WALRUS_URL}/api/players") as response:
            if response.status == 200:
                walrus_status = "✅ Online"
            else:
                walrus_status = "⚠️ API Error"
    except:
        walrus_status = "❌ Offline"
    
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=0x28a745 if "Online" in walrus_status else 0xdc3545,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Discord Bot", value="✅ Online", inline=True)
    embed.add_field(name="Line Walrus API", value=walrus_status, inline=True)
    embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
    
    if "Online" in walrus_status:
        embed.add_field(
            name="🎯 Ready to use!",
            value="Try `!lines` to see current lines or `!help_walrus` for more commands.",
            inline=False
        )
    else:
        embed.add_field(
            name="⚠️ Setup Required",
            value="Make sure Line Walrus is running and accessible.",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    logger.error(f"Command error: {error}")
    
    embed = discord.Embed(
        title="❌ Error",
        description=f"An error occurred: {str(error)}",
        color=0xdc3545
    )
    
    await ctx.send(embed=embed)

# Cleanup on shutdown
@bot.event
async def on_disconnect():
    """Cleanup on disconnect"""
    if line_bot.session and not line_bot.session.closed:
        await line_bot.session.close()

def main():
    """Main function to run the bot"""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_BOT_TOKEN environment variable not set!")
        return
    
    logger.info("Starting Line Walrus Discord Bot...")
    logger.info(f"Line Walrus URL: {LINE_WALRUS_URL}")
    
    try:
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token!")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    main()
