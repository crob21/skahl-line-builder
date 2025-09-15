"""
Utility functions for Line Walrus
Common helper functions used throughout the application.
"""

import os
import json
import csv
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import TEAMS_DIR, SESSIONS_DIR, SHARED_LINES_DIR, CSV_DIR

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return secrets.token_hex(16)

def generate_line_id() -> str:
    """Generate a unique line ID for sharing"""
    return secrets.token_hex(8)

def get_session_data_file(session_id: str) -> str:
    """Get the file path for a session's data"""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

def get_team_file(team_name: str) -> str:
    """Get the file path for a team's data"""
    # Map team names to filenames
    team_mapping = {
        "Jackalopes": "jackalopes.json",
        "Seattle Kraken": "seattle_kraken.json"
    }
    
    filename = team_mapping.get(team_name, f"{team_name.lower().replace(' ', '_')}.json")
    return os.path.join(TEAMS_DIR, filename)

def get_shared_line_file(line_id: str) -> str:
    """Get the file path for shared line data"""
    return os.path.join(SHARED_LINES_DIR, f"{line_id}.json")

def load_json_file(filepath: str) -> Optional[Dict]:
    """Load data from a JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return None

def save_json_file(filepath: str, data: Dict) -> bool:
    """Save data to a JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

def list_team_files() -> List[Dict]:
    """List all available team files"""
    teams = []
    try:
        for filename in os.listdir(TEAMS_DIR):
            if filename.endswith('.json') and filename != 'current_session.json':
                filepath = os.path.join(TEAMS_DIR, filename)
                data = load_json_file(filepath)
                if data:
                    teams.append({
                        'filename': filename,
                        'name': data.get('name', filename.replace('.json', '')),
                        'player_count': len(data.get('players', [])),
                        'last_updated': data.get('last_updated', '')
                    })
    except Exception as e:
        print(f"Error listing teams: {e}")
    return teams

def parse_csv_data(csv_content: str) -> List[Dict]:
    """Parse CSV content into player data"""
    players = []
    try:
        csv_reader = csv.DictReader(csv_content.splitlines())
        for row in csv_reader:
            # Handle different column names for affiliate status
            affiliate_value = row.get('Affiliate', '') or row.get('Affiliate Status', '')
            
            # Handle SportNinja position format (Skater, Goalie, Defense, Forward)
            position = row.get('Position', '').upper()
            if position == 'SKATER':
                # For skaters, we'll assign a generic position that can be changed later
                roster_position = 'SKATER'
            elif position == 'GOALIE':
                roster_position = 'GOALIE'
            elif position == 'DEFENSE':
                roster_position = 'DEFENSE'
            elif position == 'FORWARD':
                roster_position = 'FORWARD'
            else:
                # Fallback for other formats (LW, C, RW, D, G)
                roster_position = position
            
            player = {
                'id': f"player_{len(players) + 1}",
                'name': f"{row.get('Last Name', '')} {row.get('First Name', '')}".strip(),
                'jersey': row.get('Jersey Number', ''),
                'roster_position': roster_position,
                'affiliate': affiliate_value.upper() == 'YES',
                'location': 'spares' if affiliate_value.upper() == 'YES' else 'bench'
            }
            players.append(player)
    except Exception as e:
        print(f"Error parsing CSV: {e}")
    return players

def format_player_name(player: Dict) -> str:
    """Format player name for display"""
    name = player.get('name', '')
    jersey = player.get('jersey', '')
    if jersey:
        return f"{name} #{jersey}"
    return name

def get_position_display_name(position: str) -> str:
    """Get display name for position"""
    position_names = {
        'LW': 'Left Wing',
        'C': 'Center',
        'RW': 'Right Wing',
        'LD': 'Left Defense',
        'RD': 'Right Defense',
        'G': 'Goalie'
    }
    return position_names.get(position, position)

def is_mobile_device(user_agent: str) -> bool:
    """Check if user agent indicates mobile device"""
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'blackberry', 'windows phone']
    user_agent_lower = user_agent.lower()
    return any(keyword in user_agent_lower for keyword in mobile_keywords)

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return timestamp

def validate_file_upload(filename: str, content: str) -> tuple[bool, str]:
    """Validate uploaded file"""
    if not filename:
        return False, "No file provided"
    
    if not filename.lower().endswith('.csv'):
        return False, "Only CSV files are allowed"
    
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        return False, "File too large (max 10MB)"
    
    if not content.strip():
        return False, "File is empty"
    
    return True, "File is valid"

def create_backup(data: Dict, backup_type: str) -> str:
    """Create a backup of data"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{backup_type}_{timestamp}.json"
    filepath = os.path.join('data/backups', filename)
    
    if save_json_file(filepath, data):
        return filename
    return ""

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace unsafe characters
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return safe_filename[:100]  # Limit length
