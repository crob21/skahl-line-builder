# Line Walrus Discord Bot Setup

## Overview
The Line Walrus Discord Bot allows teams to view and manage hockey lines directly from Discord. It provides real-time updates and easy access to line combinations.

## Features
- **View Lines**: Show current line combinations with `!lines`
- **View Roster**: Display team roster with `!roster`
- **List Teams**: See available teams with `!teams`
- **Status Check**: Verify bot and API status with `!status`
- **Help**: Get command help with `!help_walrus`

## Setup Instructions

### 1. Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it "Line Walrus Bot"
4. Go to "Bot" section
5. Click "Add Bot"
6. Copy the bot token (keep it secret!)

### 2. Set Bot Permissions
1. Go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`, `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
   - Add Reactions
4. Copy the generated URL and use it to invite the bot to your server

### 3. Environment Setup
Create a `.env` file in your project directory:
```bash
DISCORD_BOT_TOKEN=your_bot_token_here
LINE_WALRUS_URL=https://your-line-walrus-app.onrender.com
```

### 4. Install Dependencies
```bash
pip install -r discord_requirements.txt
```

### 5. Run the Bot
```bash
python discord_bot.py
```

## Commands

### Basic Commands
- `!lines` - Show current line combinations
- `!roster` - Show team roster
- `!teams` - List available teams
- `!status` - Check bot and API status
- `!help_walrus` - Show help information

### Example Usage
```
!lines
```
Shows current line combinations in a formatted embed.

```
!roster
```
Displays the team roster organized by position.

## Integration with Line Walrus Web App

The bot connects to your Line Walrus web application via API calls. Make sure:
1. Line Walrus is running and accessible
2. The `LINE_WALRUS_URL` environment variable points to your app
3. The web app's API endpoints are working

## Deployment Options

### Option 1: Run Locally
- Install dependencies
- Set environment variables
- Run `python discord_bot.py`

### Option 2: Deploy to Cloud
- Use services like Railway, Heroku, or DigitalOcean
- Set environment variables in your deployment platform
- The bot will run continuously

### Option 3: Run on VPS
- Set up a VPS with Python
- Install dependencies
- Use systemd or PM2 to keep the bot running

## Troubleshooting

### Bot Not Responding
1. Check if the bot is online in Discord
2. Verify the bot has proper permissions
3. Check the console for error messages

### API Connection Issues
1. Verify `LINE_WALRUS_URL` is correct
2. Make sure Line Walrus web app is running
3. Check if the API endpoints are accessible

### Permission Errors
1. Make sure the bot has "Send Messages" permission
2. Check if the bot can see the channel
3. Verify the bot role is above other roles if needed

## Advanced Features (Future)

### Webhook Integration
- Set up Discord webhooks to notify channels when lines change
- Real-time updates when coaches modify lines

### Slash Commands
- Modern Discord slash commands for better UX
- Auto-complete for team names and player names

### Team Management
- Link Discord servers to specific teams
- Role-based access control for line management

## Support

For issues or questions:
1. Check the console logs for error messages
2. Verify all environment variables are set correctly
3. Test the Line Walrus web app API endpoints directly
4. Check Discord bot permissions and role hierarchy
