"""
API Routes for Line Walrus
Flask routes and API endpoints for the hockey line builder application.
"""

from flask import request, jsonify, session
from datetime import datetime
import os
import json
from hockey_manager import HockeyTeamManager
from utils import (
    generate_session_id, generate_line_id, get_session_data_file,
    get_team_file, get_shared_line_file, load_json_file, save_json_file,
    list_team_files, parse_csv_data, validate_file_upload, format_timestamp
)
from database import db
from config import APP_NAME, APP_TAGLINE

def get_manager():
    """Get the current session's hockey team manager"""
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
        print(f"Created new session: {session['session_id']}")
    else:
        print(f"Using existing session: {session['session_id']}")
    
    session_file = get_session_data_file(session['session_id'])
    return HockeyTeamManager(session_file)

def init_routes(app):
    """Initialize all routes for the Flask app"""
    
    @app.route('/api/players')
    def get_players():
        """Get all players for the current session"""
        manager = get_manager()
        print(f"API returning {len(manager.players)} players")
        return jsonify(manager.players)
    
    @app.route('/api/players/add', methods=['POST'])
    def add_player():
        """Add a new player and automatically save to database"""
        manager = get_manager()
        data = request.json
        
        player = {
            'id': f"player_{len(manager.players) + 1}",
            'name': data.get('name', '').strip(),
            'jersey': data.get('jersey_number', data.get('jersey', '')).strip(),
            'roster_position': data.get('position', data.get('roster_position', 'FORWARD')),
            'affiliate': data.get('affiliate', False),
            'location': 'spares' if data.get('affiliate', False) else 'bench'
        }
        
        manager.add_player(player)
        
        # Automatically save to database if a team is selected
        team_name = data.get('team_name')
        if team_name:
            filename = f"{team_name.lower().replace(' ', '_')}.json"
            if db.save_team(team_name, filename, manager.players, manager.lines):
                return jsonify({"success": True, "message": f"Player added and team '{team_name}' updated successfully"})
            else:
                return jsonify({"success": True, "message": "Player added to session (team update failed)"})
        else:
            return jsonify({"success": True, "message": "Player added to session"})
    
    @app.route('/api/players/remove', methods=['POST'])
    def remove_player():
        """Remove a player"""
        manager = get_manager()
        data = request.json
        player_id = data.get('player_id')
        
        if manager.remove_player(player_id):
            return jsonify({"success": True, "message": "Player removed successfully"})
        return jsonify({"success": False, "message": "Player not found"})
    
    @app.route('/api/lines')
    def get_lines():
        """Get current lines"""
        manager = get_manager()
        return jsonify(manager.lines)
    
    @app.route('/api/lines/set-player', methods=['POST'])
    def set_player_in_line():
        """Set a player in a specific line position"""
        manager = get_manager()
        data = request.json
        
        player_id = data.get('player_id')
        line = data.get('line') or data.get('line_num')  # Support both 'line' and 'line_num'
        position = data.get('position')
        
        if not line:
            return jsonify({"success": False, "message": "Line parameter missing"})
        
        if manager.set_player_in_line(player_id, line, position):
            return jsonify({"success": True, "message": "Player placed successfully"})
        return jsonify({"success": False, "message": "Failed to place player"})
    
    @app.route('/api/lines/remove-player', methods=['POST'])
    def remove_from_line():
        """Remove a player from a line position"""
        manager = get_manager()
        data = request.json
        
        line = data.get('line')
        position = data.get('position')
        
        print(f"🔍 Remove from line - Received: line={line} (type: {type(line)}), position={position} (type: {type(position)})")
        print(f"🔍 Current lines state: {manager.lines}")
        
        if manager.remove_from_line(line, position):
            print(f"✅ Successfully removed player from line {line}, position {position}")
            return jsonify({"success": True, "message": "Player removed from line"})
        else:
            print(f"❌ Failed to remove player from line {line}, position {position}")
            return jsonify({"success": False, "message": "Failed to remove player"})
    
    @app.route('/api/lines/clear', methods=['POST'])
    def clear_line():
        """Clear all players from a line"""
        manager = get_manager()
        data = request.json
        line = data.get('line')
        
        if manager.clear_line(line):
            return jsonify({"success": True, "message": f"Line {line} cleared"})
        return jsonify({"success": False, "message": "Failed to clear line"})
    
    @app.route('/api/teams/upload', methods=['POST'])
    def upload_team():
        """Upload team from CSV"""
        manager = get_manager()
        
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file uploaded"})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"})
        
        # Get team name from form data
        team_name = request.form.get('team_name', '').strip()
        if not team_name:
            return jsonify({"success": False, "message": "Team name is required"})
        
        # Validate file
        content = file.read().decode('utf-8')
        is_valid, message = validate_file_upload(file.filename, content)
        if not is_valid:
            return jsonify({"success": False, "message": message})
        
        # Parse CSV and load players
        players = parse_csv_data(content)
        manager.load_players(players)
        
        # Save the team with the provided name
        filename = f"{team_name.lower().replace(' ', '_')}.json"
        if db.save_team(team_name, filename, manager.players, manager.lines):
            actual_count = len(manager.players)
            return jsonify({
                "success": True, 
                "message": f"Team '{team_name}' uploaded and saved successfully! {actual_count} players loaded."
            })
        else:
            return jsonify({
                "success": False, 
                "message": f"Failed to save team '{team_name}'. Team may already exist."
            })
    
    @app.route('/api/teams/download')
    def download_team():
        """Download current team as CSV"""
        manager = get_manager()
        
        if not manager.players:
            return jsonify({"success": False, "message": "No players to download"})
        
        # Create CSV content
        csv_content = "Last Name,First Name,Jersey Number,Position,Affiliate\n"
        for player in manager.players:
            name_parts = player['name'].split(' ', 1)
            last_name = name_parts[0] if len(name_parts) > 0 else ''
            first_name = name_parts[1] if len(name_parts) > 1 else ''
            
            csv_content += f"{last_name},{first_name},{player.get('jersey', '')},{player.get('roster_position', '')},{'YES' if player.get('affiliate', False) else 'NO'}\n"
        
        return jsonify({
            "success": True,
            "csv_content": csv_content,
            "filename": f"line_walrus_team_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        })
    
    @app.route('/api/teams/save', methods=['POST'])
    def save_team():
        """Save current team"""
        manager = get_manager()
        data = request.json
        team_name = data.get('team_name', data.get('name', 'My Team')).strip()
        
        if not team_name:
            return jsonify({"success": False, "message": "Please provide a team name"})
        
        # Generate filename from team name
        filename = f"{team_name.lower().replace(' ', '_')}.json"
        
        if db.save_team(team_name, filename, manager.players, manager.lines):
            return jsonify({"success": True, "message": f"Team '{team_name}' saved successfully"})
        return jsonify({"success": False, "message": "Failed to save team"})
    
    @app.route('/api/teams/load', methods=['POST'])
    def load_team():
        """Load a saved team"""
        manager = get_manager()
        data = request.json
        team_name = data.get('team_name')
        
        print(f"🔍 Load team request: team_name='{team_name}'")
        print(f"🔍 Database type: {'PostgreSQL' if db.use_postgres else 'SQLite'}")
        
        if not team_name:
            return jsonify({"success": False, "message": "No team name provided"})
        
        team_data = db.load_team(team_name)
        print(f"🔍 Team data from database: {team_data is not None}")
        
        if team_data:
            players = team_data.get('players', [])
            print(f"✅ Loading {len(players)} players for team {team_name}")
            manager.load_players(players)
            manager.lines = team_data.get('lines', manager.lines)
            print(f"✅ Manager now has {len(manager.players)} players")
            return jsonify({"success": True, "message": f"Team '{team_name}' loaded successfully"})
        else:
            print(f"❌ Team '{team_name}' not found in database")
            return jsonify({"success": False, "message": "Team not found"})
    
    @app.route('/api/teams/list')
    def list_teams():
        """List all available teams"""
        teams = db.list_teams()
        return jsonify(teams)
    
    @app.route('/api/teams/delete', methods=['POST'])
    def delete_team():
        """Delete a saved team"""
        data = request.json
        team_name = data.get('team_name')
        
        if not team_name:
            return jsonify({"success": False, "message": "Team name required"})
        
        if db.delete_team(team_name):
            print(f"🗑️ Deleted team: {team_name}")
            return jsonify({"success": True, "message": f"Team '{team_name}' deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Team not found"})
    
    @app.route('/api/teams/update', methods=['POST'])
    def update_team():
        """Update a saved team with current roster and lines"""
        data = request.json
        team_name = data.get('team_name')
        
        if not team_name:
            return jsonify({"success": False, "message": "Team name required"})
        
        manager = get_manager()
        
        # Generate filename from team name
        filename = f"{team_name.lower().replace(' ', '_')}.json"
        
        if db.save_team(team_name, filename, manager.players, manager.lines):
            print(f"🔄 Updated team: {team_name} with {len(manager.players)} players")
            return jsonify({"success": True, "message": f"Team '{team_name}' updated successfully"})
        else:
            return jsonify({"success": False, "message": f"Error updating team"})
    
    @app.route('/api/lines/save', methods=['POST'])
    def save_lines():
        """Save and share current lines"""
        manager = get_manager()
        data = request.json
        line_name = data.get('name', 'My Lines').strip()
        team_name = data.get('team_name', '').strip()
        
        if not line_name:
            return jsonify({"success": False, "message": "Please provide a name for your lines"})
        
        # Try to determine the current team name if not provided
        if not team_name:
            if manager.players:
                # Check if this looks like the default Seattle Kraken roster
                kraken_players = [p for p in manager.players if 'kraken' in p.get('name', '').lower() or 
                                any(kraken_name in p.get('name', '').lower() for kraken_name in 
                                    ['matty', 'beniers', 'eberle', 'schwartz', 'dunn', 'larsson'])]
                if kraken_players:
                    team_name = "Seattle Kraken"
                else:
                    team_name = "Current Team"
            else:
                team_name = "Current Team"
        
        line_id = generate_line_id()
        line_data = {
            "name": line_name,
            "team_name": team_name,
            "lines": manager.lines,
            "players": manager.players,
            "created": datetime.now().isoformat(),
            "line_id": line_id
        }
        
        line_file = get_shared_line_file(line_id)
        if save_json_file(line_file, line_data):
            share_url = f"{request.host_url}lines/{line_id}"
            return jsonify({
                "success": True, 
                "message": f"Lines saved as '{line_name}'", 
                "share_url": share_url, 
                "line_id": line_id
            })
        return jsonify({"success": False, "message": "Error saving lines"})
    
    @app.route('/api/lines/load-shared/<line_id>', methods=['POST'])
    def load_shared_lines(line_id):
        """Load shared lines into current session"""
        manager = get_manager()
        line_file = get_shared_line_file(line_id)
        line_data = load_json_file(line_file)
        
        if line_data:
            manager.load_players(line_data.get('players', []))
            manager.lines = line_data.get('lines', manager.lines)
            return jsonify({"success": True, "message": "Shared lines loaded successfully"})
        return jsonify({"success": False, "message": "Shared lines not found"})
    
    @app.route('/api/print-lines', methods=['GET'])
    def print_lines():
        """Generate print-friendly view of current lines"""
        manager = get_manager()
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Try to determine the current team name
        team_name = "Current Team"  # Default fallback
        
        # Check if we have players (like default Seattle Kraken)
        if manager.players:
            # Check if this looks like the default Seattle Kraken roster
            kraken_players = [p for p in manager.players if 'kraken' in p.get('name', '').lower() or 
                            any(kraken_name in p.get('name', '').lower() for kraken_name in 
                                ['matty', 'beniers', 'eberle', 'schwartz', 'dunn', 'larsson'])]
            if kraken_players:
                team_name = "Seattle Kraken"
            else:
                # Try to get team name from session data or use a generic name
                team_name = "Current Team"
        
        # Generate print HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{APP_NAME} - {team_name} Lines</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="icon" type="image/png" href="/static/images/favicon.png">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: white;
                    color: black;
                }}
                .header {{ 
                    text-align: center; 
                    margin-bottom: 40px; 
                    border-bottom: 3px solid #1e3a8a;
                    padding-bottom: 20px;
                }}
                .header h1 {{
                    color: #1e3a8a;
                    font-size: 28px;
                    margin-bottom: 5px;
                }}
                .header p {{
                    color: #fbbf24;
                    font-style: italic;
                    margin-bottom: 10px;
                }}
                .header h2 {{
                    color: #3b82f6;
                    font-size: 20px;
                    margin: 0;
                }}
                .team-name {{
                    color: #1e40af;
                    font-size: 18px;
                    font-weight: bold;
                    margin: 10px 0;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .line-section {{ 
                    margin-bottom: 35px; 
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 10px;
                    padding: 20px;
                }}
                .line-title {{ 
                    font-size: 20px; 
                    font-weight: bold; 
                    margin-bottom: 15px; 
                    color: #1e3a8a;
                    text-align: center;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .positions {{ 
                    display: flex; 
                    gap: 12px; 
                    margin-bottom: 12px; 
                    justify-content: center;
                    flex-wrap: wrap;
                }}
                .position {{ 
                    border: 2px solid #1e3a8a; 
                    padding: 12px 8px; 
                    min-width: 100px; 
                    text-align: center; 
                    background: white;
                    border-radius: 6px;
                }}
                .position-label {{ 
                    font-weight: bold; 
                    color: #495057; 
                    margin-bottom: 8px; 
                    font-size: 12px;
                    text-transform: uppercase;
                }}
                .player-name {{ 
                    font-weight: bold; 
                    color: black;
                    font-size: 14px;
                }}
                .empty-position {{
                    color: #6c757d;
                    font-style: italic;
                }}
                @media print {{ 
                    body {{ margin: 15px; }}
                    .header {{ border-bottom: 2px solid #1e3a8a; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{APP_NAME}</h1>
                <p>{APP_TAGLINE}</p>
                <div class="team-name">{team_name}</div>
                <h2>Game Lines - {current_date}</h2>
            </div>
        """
        
        # Add each line (ensure we only process each line once)
        processed_lines = set()
        for line_num, line in manager.lines.items():
            # Convert to int to avoid duplicates (e.g., "1" and 1)
            line_key = int(line_num) if isinstance(line_num, str) else line_num
            if line_key in processed_lines:
                continue
            processed_lines.add(line_key)
            html_content += f'''
                <div class="line-section">
                    <div class="line-title">Line {line_num}</div>
            '''
            
            # Add forwards row
            forwards = []
            if line.get('LW'): forwards.append(('LW', line['LW']['name']))
            if line.get('C'): forwards.append(('C', line['C']['name']))
            if line.get('RW'): forwards.append(('RW', line['RW']['name']))
            
            if forwards:
                html_content += '<div class="positions">'
                for pos, name in forwards:
                    html_content += f'''
                    <div class="position">
                        <div class="position-label">{pos}</div>
                        <div class="player-name">{name}</div>
                    </div>
                    '''
                html_content += '</div>'
            
            # Add defense row
            defense = []
            if line.get('LD'): defense.append(('LD', line['LD']['name']))
            if line.get('RD'): defense.append(('RD', line['RD']['name']))
            
            if defense:
                html_content += '<div class="positions">'
                for pos, name in defense:
                    html_content += f'''
                    <div class="position">
                        <div class="position-label">{pos}</div>
                        <div class="player-name">{name}</div>
                    </div>
                    '''
                html_content += '</div>'
            
            # Add goalie (only for Line 1)
            if line_num == "1" and line.get('G'):
                html_content += f'''
                <div class="positions">
                    <div class="position">
                        <div class="position-label">G</div>
                        <div class="player-name">{line['G']['name']}</div>
                    </div>
                </div>
                '''
            
            html_content += '</div>'
        
        html_content += "</body></html>"
        
        return html_content
