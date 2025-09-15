from flask import Flask, render_template, request, jsonify, send_file, session
import json
import os
import csv
import io
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a random secret key

def get_session_data_file():
    """Get the data file path for the current session"""
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(8)  # Generate unique session ID
    return f"data/sessions/{session['session_id']}.json"

class HockeyTeamManager:
    def __init__(self, data_file=None):
        if data_file is None:
            data_file = get_session_data_file()
        self.data_file = data_file
        self.players = []
        self.lines = {
            "1": {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None},
            "2": {"LW": None, "C": None, "RW": None, "LD": None, "RD": None},
            "3": {"LW": None, "C": None, "RW": None, "LD": None, "RD": None}
        }
        self.load_data()
    
    def save_data(self):
        data = {
            "players": self.players,
            "lines": self.lines,
            "last_updated": datetime.now().isoformat()
        }
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.players = data.get("players", [])
                    self.lines = data.get("lines", self.lines)
            except (json.JSONDecodeError, KeyError):
                pass
    
    def add_player(self, name, position, jersey_number="", affiliate=False):
        if any(p["name"].lower() == name.lower() for p in self.players):
            return {"success": False, "message": f"{name} already exists"}
        
        valid_positions = ["FORWARD", "DEFENSE", "GOALIE"]
        if position.upper() not in valid_positions:
            return {"success": False, "message": "Invalid position"}
        
        player = {
            "name": name.strip(),
            "roster_position": position.upper(),
            "jersey_number": jersey_number.strip(),
            "affiliate": affiliate,
            "id": len(self.players) + 1
        }
        
        self.players.append(player)
        self.save_data()
        return {"success": True, "player": player}
    
    def remove_player(self, player_id):
        # Remove from roster
        self.players = [p for p in self.players if p["id"] != player_id]
        
        # Remove from lines
        for line_num in self.lines:
            for position in self.lines[line_num]:
                if (self.lines[line_num][position] and 
                    self.lines[line_num][position]["id"] == player_id):
                    self.lines[line_num][position] = None
        
        self.save_data()
        return {"success": True}
    
    def set_player_in_line(self, player_id, line_num, position):
        # Find the player
        player = next((p for p in self.players if p["id"] == player_id), None)
        if not player:
            return {"success": False, "message": "Player not found"}
        
        # Check if line and position exist
        if line_num not in self.lines:
            return {"success": False, "message": "Invalid line number"}
        
        if position not in self.lines[line_num]:
            return {"success": False, "message": "Invalid position for this line"}
        
        # Remove player from any other position
        for ln in self.lines:
            for pos in self.lines[ln]:
                if (self.lines[ln][pos] and 
                    self.lines[ln][pos]["id"] == player_id):
                    self.lines[ln][pos] = None
        
        # Set player in new position
        self.lines[line_num][position] = player
        self.save_data()
        return {"success": True}
    
    def remove_from_line(self, player_id):
        # Remove player from all line positions
        for line_num in self.lines:
            for position in self.lines[line_num]:
                if (self.lines[line_num][position] and 
                    self.lines[line_num][position]["id"] == player_id):
                    self.lines[line_num][position] = None
        
        self.save_data()
        return {"success": True}

def get_manager():
    """Get the team manager for the current session"""
    return HockeyTeamManager()

def get_shared_team_manager():
    """Get a team manager for shared team operations (save/load)"""
    # Use a temporary file for shared operations
    return HockeyTeamManager("data/teams/temp_shared.json")

def generate_line_id():
    """Generate a unique ID for shared lines"""
    return secrets.token_hex(8)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players', methods=['GET'])
def get_players():
    manager = get_manager()
    return jsonify(manager.players)

@app.route('/api/players', methods=['POST'])
def add_player():
    manager = get_manager()
    data = request.json
    jersey_number = data.get('jersey_number', '')
    affiliate = data.get('affiliate', False)
    result = manager.add_player(data['name'], data['position'], jersey_number, affiliate)
    return jsonify(result)

@app.route('/api/players/<int:player_id>', methods=['DELETE'])
def remove_player(player_id):
    manager = get_manager()
    result = manager.remove_player(player_id)
    return jsonify(result)

@app.route('/api/lines', methods=['GET'])
def get_lines():
    manager = get_manager()
    return jsonify(manager.lines)

@app.route('/api/lines/set-player', methods=['POST'])
def set_player_in_line():
    manager = get_manager()
    data = request.json
    result = manager.set_player_in_line(
        data['player_id'], 
        data['line_num'], 
        data['position']
    )
    return jsonify(result)

@app.route('/api/lines/remove-player/<int:player_id>', methods=['DELETE'])
def remove_from_line(player_id):
    manager = get_manager()
    result = manager.remove_from_line(player_id)
    return jsonify(result)

@app.route('/api/lines/clear/<line_num>', methods=['DELETE'])
def clear_line(line_num):
    manager = get_manager()
    if line_num in manager.lines:
        # Clear the line by setting all positions to None
        if line_num == 1:
            manager.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                                      "LD": None, "RD": None, "G": None}
        else:
            manager.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                                      "LD": None, "RD": None}
        manager.save_data()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/teams/upload', methods=['POST'])
def upload_team():
    # Get current session manager to load CSV into
    session_manager = get_manager()
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"})
    
    if not file.filename.endswith('.csv'):
        return jsonify({"success": False, "message": "Please upload a CSV file"})
    
    try:
        # Read CSV content
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        # Clear current session team
        session_manager.players = []
        session_manager.lines[1] = {"LW": None, "C": None, "RW": None, 
                                   "LD": None, "RD": None, "G": None}
        session_manager.lines[2] = {"LW": None, "C": None, "RW": None, 
                                   "LD": None, "RD": None}
        session_manager.lines[3] = {"LW": None, "C": None, "RW": None, 
                                   "LD": None, "RD": None}
        
        # Add players from CSV
        for row in csv_reader:
            last_name = row.get('last_name', '').strip()
            first_name = row.get('first_name', '').strip()
            jersey_number = row.get('jersey_number', '').strip()
            position = row.get('position', '').strip().upper()
            affiliate = row.get('affiliate', '').strip().upper()
            
            if last_name and first_name and position:
                # Map roster positions to our system
                valid_roster_positions = ["FORWARD", "DEFENSE", "GOALIE"]
                if position in valid_roster_positions:
                    # Create full name
                    full_name = f"{first_name} {last_name}"
                    
                    player = {
                        "name": full_name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "jersey_number": jersey_number,
                        "roster_position": position,  # FORWARD, DEFENSE, GOALIE
                        "affiliate": affiliate == "YES",
                        "id": len(session_manager.players) + 1
                    }
                    session_manager.players.append(player)
        
        session_manager.save_data()
        return jsonify({"success": True, "message": f"Team uploaded successfully! Added {len(session_manager.players)} players."})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error processing file: {str(e)}"})

@app.route('/api/teams/download', methods=['GET'])
def download_team():
    manager = get_manager()
    try:
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['last_name', 'first_name', 'jersey_number', 'position', 'affiliate'])
        
        for player in manager.players:
            affiliate_status = "YES" if player.get('affiliate', False) else "NO"
            writer.writerow([
                player.get('last_name', ''),
                player.get('first_name', ''),
                player.get('jersey_number', ''),
                player.get('roster_position', 'FORWARD'),  # Use roster position
                affiliate_status
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'hockey_team_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error creating CSV: {str(e)}"})

@app.route('/api/teams/save', methods=['POST'])
def save_team():
    # Get current session data
    session_manager = get_manager()
    data = request.json
    team_name = data.get('team_name', 'hockey_team').strip()
    
    if not team_name:
        team_name = 'hockey_team'
    
    # Create a copy of current session data to save as shared team
    team_data = {
        "players": session_manager.players,
        "lines": session_manager.lines,
        "last_updated": datetime.now().isoformat(),
        "team_name": team_name
    }
    
    # Save to a new file
    filename = f"{team_name.replace(' ', '_').lower()}.json"
    filepath = os.path.join(os.getcwd(), 'data', 'teams', filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(team_data, f, indent=2)
        return jsonify({"success": True, "message": f"Team saved as {filename}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving team: {str(e)}"})

@app.route('/api/teams/load', methods=['POST'])
def load_team():
    # Get current session manager to load data into
    session_manager = get_manager()
    data = request.json
    filename = data.get('filename', 'hockey_team.json')
    
    filepath = os.path.join(os.getcwd(), 'data', 'teams', filename)
    
    if not os.path.exists(filepath):
        return jsonify({"success": False, "message": "Team file not found"})
    
    try:
        with open(filepath, 'r') as f:
            team_data = json.load(f)
        
        # Load shared team data into current session
        session_manager.players = team_data.get("players", [])
        session_manager.lines = team_data.get("lines", session_manager.lines)
        session_manager.save_data()
        
        return jsonify({"success": True, "message": f"Team loaded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error loading team: {str(e)}"})

@app.route('/api/teams/list', methods=['GET'])
def list_teams():
    try:
        teams = []
        directory = os.path.join(os.getcwd(), 'data', 'teams')  # Use data/teams directory
        
        if not os.path.exists(directory):
            return jsonify([])
            
        for filename in os.listdir(directory):
            if filename.endswith('.json') and filename not in ['current_session.json']:
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r') as f:
                        team_data = json.load(f)
                    team_name = team_data.get('team_name', filename.replace('.json', ''))
                    teams.append({
                        'filename': filename,
                        'name': team_name,
                        'player_count': len(team_data.get('players', [])),
                        'last_updated': team_data.get('last_updated', '')
                    })
                except:
                    continue
        
        return jsonify(teams)
    except Exception as e:
        return jsonify([])



@app.route('/api/lines/save', methods=['POST'])
def save_lines():
    """Save current lines with a name and generate a shareable URL"""
    manager = get_manager()
    data = request.json
    line_name = data.get('name', 'My Lines').strip()
    
    if not line_name:
        return jsonify({"success": False, "message": "Please provide a name for your lines"})
    
    # Generate unique ID for the lines
    line_id = generate_line_id()
    
    # Create line data
    line_data = {
        "name": line_name,
        "lines": manager.lines,
        "players": manager.players,  # Include players so others can see who's in each position
        "created": datetime.now().isoformat(),
        "line_id": line_id
    }
    
    # Save to shared lines directory
    filename = f"{line_id}.json"
    filepath = os.path.join(os.getcwd(), 'data', 'shared_lines', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(line_data, f, indent=2)
        
        # Generate shareable URL
        share_url = f"{request.host_url}lines/{line_id}"
        
        return jsonify({
            "success": True, 
            "message": f"Lines saved as '{line_name}'",
            "share_url": share_url,
            "line_id": line_id
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving lines: {str(e)}"})

@app.route('/lines/<line_id>')
def view_shared_lines(line_id):
    """View shared lines via URL"""
    try:
        filepath = os.path.join(os.getcwd(), 'data', 'shared_lines', f"{line_id}.json")
        
        if not os.path.exists(filepath):
            return "Lines not found or have been removed.", 404
        
        with open(filepath, 'r') as f:
            line_data = json.load(f)
        
        # Create a view-only HTML page
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Line Walrus - {line_data['name']}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
                    color: white;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .header {{ 
                    text-align: center; 
                    margin-bottom: 40px; 
                    border-bottom: 3px solid #fbbf24;
                    padding-bottom: 20px;
                }}
                .header h1 {{
                    color: #fbbf24;
                    font-size: 28px;
                    margin-bottom: 5px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 15px;
                }}
                .logo {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .logo img {{
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                }}
                .header h2 {{
                    color: #3b82f6;
                    font-size: 20px;
                    margin: 0;
                }}
                .tagline {{
                    text-align: center;
                    margin-top: -10px;
                    margin-bottom: 20px;
                    font-size: 1rem;
                    color: #fbbf24;
                    font-style: italic;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                .line-section {{ 
                    margin-bottom: 35px; 
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    border: 2px solid rgba(255,255,255,0.2);
                }}
                .line-title {{ 
                    font-size: 20px; 
                    font-weight: bold; 
                    margin-bottom: 15px; 
                    color: #fbbf24;
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
                    border: 2px solid #fbbf24; 
                    padding: 12px 8px; 
                    min-width: 100px; 
                    text-align: center; 
                    background: rgba(255,255,255,0.1);
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                .position-label {{ 
                    font-weight: bold; 
                    color: #fbbf24; 
                    margin-bottom: 8px; 
                    font-size: 12px;
                    text-transform: uppercase;
                }}
                .player-name {{ 
                    font-weight: bold; 
                    color: white;
                    font-size: 14px;
                }}
                .empty-position {{
                    color: #ccc;
                    font-style: italic;
                }}
                .goalie-position {{
                    border: 2px solid #fbbf24;
                    background: rgba(251, 191, 36, 0.2);
                }}
                .goalie-position .position-label {{
                    color: #fbbf24;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid rgba(255,255,255,0.2);
                    color: #ccc;
                }}
                .load-button {{
                    background: #fbbf24;
                    color: #1e3a8a;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    margin-top: 20px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .load-button:hover {{
                    background: #f59e0b;
                    transform: translateY(-2px);
                }}
                .print-button {{
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    margin-top: 10px;
                    margin-left: 10px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .print-button:hover {{
                    background: #c82333;
                    transform: translateY(-2px);
                }}
                @media print {{
                    .load-button, .print-button {{
                        display: none;
                    }}
                    body {{
                        background: white !important;
                        color: black !important;
                    }}
                    .container {{
                        background: white !important;
                        box-shadow: none !important;
                    }}
                    .line-section {{
                        background: #f8f9fa !important;
                        border: 1px solid #dee2e6 !important;
                        color: black !important;
                    }}
                    .position {{
                        background: white !important;
                        border: 1px solid #dee2e6 !important;
                        color: black !important;
                    }}
                    .position-label {{
                        color: #495057 !important;
                    }}
                    .player-name {{
                        color: black !important;
                    }}
                    .header h1, .header h2 {{
                        color: #495057 !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>
                        <div class="logo">
                            <img src="/static/images/line-walrus-logo.png" alt="Line Walrus Logo">
                        </div>
                        Line Walrus
                    </h1>
                    <p class="tagline">Because Even a Walrus Can Manage Lines Better</p>
                    <h2>{line_data['name']}</h2>
                    <p>Shared on {datetime.fromisoformat(line_data['created']).strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
        '''
        
        # Add each line
        for line_num, line in line_data['lines'].items():
            html_content += f'''
                <div class="line-section">
                    <div class="line-title">Line {line_num}</div>
            '''
            
            # Add forwards row (only if there are forwards)
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
            
            # Add defense row (only if there are defensemen)
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
            
            # Add goalie (only for line 1)
            if line_num == "1" and line.get('G'):
                html_content += f'''
                <div class="positions">
                    <div class="position goalie-position">
                        <div class="position-label">G</div>
                        <div class="player-name">{line['G']['name']}</div>
                    </div>
                </div>
                '''
            
            html_content += '</div>'
        
        html_content += f'''
                <div class="footer">
                    <p>Want to use these lines in your own session?</p>
                    <a href="{request.host_url}" class="load-button">Open LINE WALRUS</a>
                    <button onclick="window.print()" class="print-button">🖨️ Print Lines</button>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"Error loading shared lines: {str(e)}", 500

@app.route('/api/lines/load-shared/<line_id>', methods=['POST'])
def load_shared_lines(line_id):
    """Load shared lines into current session"""
    try:
        filepath = os.path.join(os.getcwd(), 'data', 'shared_lines', f"{line_id}.json")
        
        if not os.path.exists(filepath):
            return jsonify({"success": False, "message": "Shared lines not found"})
        
        with open(filepath, 'r') as f:
            line_data = json.load(f)
        
        # Load into current session
        manager = get_manager()
        manager.lines = line_data['lines']
        manager.save_data()
        
        return jsonify({
            "success": True, 
            "message": f"Loaded '{line_data['name']}' into your session"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error loading shared lines: {str(e)}"})

@app.route('/api/print-lines', methods=['GET'])
def print_lines():
    manager = get_manager()
    try:
        # Get current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Create print-friendly HTML
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Line Walrus - Lines</title>
            <link rel="icon" type="image/png" href="/static/images/favicon.png">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: white;
                    color: #333;
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
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 15px;
                }}
                .logo {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .logo img {{
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                }}
                .tagline {{
                    text-align: center;
                    margin-top: -10px;
                    margin-bottom: 20px;
                    font-size: 1rem;
                    color: #fbbf24;
                    font-style: italic;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                .header h2 {{
                    color: #3b82f6;
                    font-size: 20px;
                    margin: 0;
                }}
                .line-section {{ 
                    margin-bottom: 35px; 
                    page-break-inside: avoid; 
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 20px;
                    border: 2px solid #e9ecef;
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
                }}
                .position {{ 
                    border: 2px solid #1e3a8a; 
                    padding: 12px 8px; 
                    min-width: 100px; 
                    text-align: center; 
                    background: white;
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .position-label {{ 
                    font-weight: bold; 
                    color: #1e3a8a; 
                    margin-bottom: 8px; 
                    font-size: 12px;
                    text-transform: uppercase;
                }}
                .player-name {{ 
                    font-weight: bold; 
                    color: #333;
                    font-size: 14px;
                }}
                .goalie-row {{ 
                    text-align: center; 
                    margin-top: 15px; 
                }}
                .goalie-position {{
                    border: 2px solid #fbbf24;
                    background: #fef3c7;
                    min-width: 100px;
                }}
                .goalie-position .position-label {{
                    color: #d97706;
                }}

                .empty-position {{
                    color: #999;
                    font-style: italic;
                }}
                @media print {{
                    body {{ margin: 15px; }}
                    .no-print {{ display: none; }}
                    .line-section {{ 
                        page-break-inside: avoid; 
                        margin-bottom: 25px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>
                    <div class="logo">
                        <img src="/static/images/line-walrus-logo.png" alt="Line Walrus Logo">
                    </div>
                    Line Walrus
                </h1>
                <p class="tagline">Because Even a Walrus Can Manage Lines Better</p>
                <h2>Game Lines - {current_date}</h2>
            </div>
        '''
        
        # Add each line (only if it has players)
        for line_num in ["1", "2", "3"]:
            line = manager.lines[line_num]
            
            # Check if line has any players
            has_players = any(player for player in line.values())
            if not has_players:
                continue
                
            html_content += f'''
            <div class="line-section">
                <div class="line-title">Line {line_num}</div>
            '''
            
            # Add forwards row (only if there are forwards)
            forwards = []
            if line['LW']: forwards.append(('LW', line['LW']['name']))
            if line['C']: forwards.append(('C', line['C']['name']))
            if line['RW']: forwards.append(('RW', line['RW']['name']))
            
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
            
            # Add defense row (only if there are defensemen)
            defense = []
            if line['LD']: defense.append(('LD', line['LD']['name']))
            if line['RD']: defense.append(('RD', line['RD']['name']))
            
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
            
            html_content += '</div>'
        
        # Add single goalie section (only if there's a goalie)
        goalie_player = None
        # Only check Line 1 for goalie since that's the only line with G position
        if 'G' in manager.lines["1"] and manager.lines["1"]['G']:
            goalie_player = manager.lines["1"]['G']
        
        if goalie_player:
            html_content += f'''
            <div class="line-section">
                <div class="line-title">Goalie</div>
                <div class="positions">
                    <div class="position goalie-position">
                        <div class="position-label">G</div>
                        <div class="player-name">{goalie_player['name']}</div>
                    </div>
                </div>
            </div>
            '''
        

        
        html_content += '''
        </body>
            </style>
        </head>
        <body>
            <div class="header">
                <h1>
                    <div class="logo">
                        <img src="/static/images/line-walrus-logo.png" alt="Line Walrus Logo">
                    </div>
                    Line Walrus
                </h1>
                <p class="tagline">Because Even a Walrus Can Manage Lines Better</p>
                <h2>Game Lines - {current_date}</h2>
            </div>
        '''
        
        # Add each line (only if it has players)
        for line_num in ["1", "2", "3"]:
            line = manager.lines[line_num]
            
            # Check if line has any players
            has_players = any(player for player in line.values())
            if not has_players:
                continue
                
            html_content += f'''
            <div class="line-section">
                <div class="line-title">Line {line_num}</div>
            '''
            
            # Add forwards row (only if there are forwards)
            forwards = []
            if line['LW']: forwards.append(('LW', line['LW']['name']))
            if line['C']: forwards.append(('C', line['C']['name']))
            if line['RW']: forwards.append(('RW', line['RW']['name']))
            
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
            
            # Add defense row (only if there are defensemen)
            defense = []
            if line['LD']: defense.append(('LD', line['LD']['name']))
            if line['RD']: defense.append(('RD', line['RD']['name']))
            
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
            
            html_content += '</div>'
        
        # Add single goalie section (only if there's a goalie)
        goalie_player = None
        # Only check Line 1 for goalie since that's the only line with G position
        if 'G' in manager.lines["1"] and manager.lines["1"]['G']:
            goalie_player = manager.lines["1"]['G']
        
        if goalie_player:
            html_content += f'''
            <div class="line-section">
                <div class="line-title">Goalie</div>
                <div class="positions">
                    <div class="position goalie-position">
                        <div class="position-label">G</div>
                        <div class="player-name">{goalie_player['name']}</div>
                    </div>
                </div>
            </div>
            '''
        

        
        html_content += '''
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"Error generating print view: {str(e)}"

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create the HTML template
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>Line Walrus</title>
    <link rel="icon" type="image/png" href="/static/images/favicon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="format-detection" content="telephone=no">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        
        .logo {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .logo img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
        }
        
        .tagline {
            text-align: center;
            margin-top: -10px;
            margin-bottom: 30px;
            font-size: 1.1rem;
            color: #fbbf24;
            font-style: italic;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }

        .controls {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }

        .player-management {
            border-top: 2px solid rgba(255,255,255,0.2);
            padding-top: 25px;
            margin-top: 20px;
        }

        .player-management h3 {
            margin-bottom: 20px;
            text-align: center;
            color: #ffffff;
            font-size: 1.4rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }

        .add-player-form {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            justify-content: center;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .team-management {
            border-top: 2px solid rgba(255,255,255,0.2);
            padding-top: 25px;
            margin-top: 20px;
        }

        .team-management h3 {
            margin-bottom: 20px;
            text-align: center;
            color: #ffffff;
            font-size: 1.4rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }

        .team-controls {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }

        .team-section {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 120px;
        }        .team-section h4 {
            margin-bottom: 12px;
            text-align: center;
            color: #fff;
            font-size: 1rem;
            font-weight: bold;
        }

        .team-row {
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            flex: 1;
        }

        .team-controls input[type="text"], .team-controls select {
            min-width: 120px;
            width: 100%;
            padding: 8px 12px;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 5px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 0.9rem;
        }

        .team-controls input[type="text"]::placeholder {
            color: rgba(255,255,255,0.6);
        }

        .team-controls select option {
            background: #1e3a8a;
            color: white;
        }

        .btn-upload, .btn-download, .btn-save, .btn-load {
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.9rem;
        }

        .btn-upload {
            background: #3b82f6;
        }

        .btn-upload:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }

        .btn-download {
            background: #1e3a8a;
        }

        .btn-download:hover {
            background: #1e40af;
            transform: translateY(-1px);
        }

        .btn-save {
            background: #3b82f6;
        }

        .btn-save:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }

        .btn-load {
            background: #1e3a8a;
        }

        .btn-load:hover {
            background: #1e40af;
            transform: translateY(-1px);
        }

        /* Responsive design for smaller screens */
        @media (max-width: 768px) {
            .team-controls {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .team-section {
                min-height: auto;
            }
        }

        input, select, button {
            padding: 10px;
            border: none;
            border-radius: 5px;
        }

        input, select {
            background: rgba(255,255,255,0.9);
            color: #333;
        }

        button {
            background: #3b82f6;
            color: white;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }

        button:hover {
            background: #2563eb;
        }

        .main-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }

        .left-panel {
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-height: 100vh;
            overflow-y: auto;
        }
        
        .bench {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            max-height: 50vh;
            overflow-y: auto;
        }

        .bench h2, .spares h2 {
            margin-bottom: 15px;
            text-align: center;
        }

        .spares {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            margin-top: 20px;
            max-height: 40vh;
            overflow-y: auto;
        }

        .ice-rink {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            min-height: 600px;
        }

        .line-section {
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            text-align: center;
        }

        .line-title {
            text-align: center;
            margin-bottom: 15px;
            font-size: 1.2rem;
            font-weight: bold;
        }

        .positions {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 15px;
            justify-items: center;
            align-items: center;
        }

        .defense-positions {
            grid-template-columns: repeat(2, 1fr);
        }

        .goalie-row {
            display: flex;
            justify-content: center;
            margin-bottom: 15px;
        }

        .goalie-position {
            width: 120px;
            height: 80px;
        }

        .position-slot {
            width: 120px;
            height: 80px;
            border: 2px dashed rgba(255,255,255,0.5);
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.05);
            transition: all 0.3s;
            position: relative;
            margin: 0 auto;
            overflow: hidden;
            min-height: 44px;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
            cursor: pointer;
        }

        .position-slot.drag-over {
            border-color: #3b82f6;
            background: rgba(59,130,246,0.2);
            transform: scale(1.05);
        }
        
        /* Custom scrollbar styling */
        .left-panel::-webkit-scrollbar,
        .bench::-webkit-scrollbar,
        .spares::-webkit-scrollbar {
            width: 8px;
        }
        
        .left-panel::-webkit-scrollbar-track,
        .bench::-webkit-scrollbar-track,
        .spares::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
        }
        
        .left-panel::-webkit-scrollbar-thumb,
        .bench::-webkit-scrollbar-thumb,
        .spares::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.3);
            border-radius: 4px;
        }
        
        .left-panel::-webkit-scrollbar-thumb:hover,
        .bench::-webkit-scrollbar-thumb:hover,
        .spares::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.5);
        }

        .position-label {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.7);
            margin-bottom: 5px;
            font-weight: bold;
        }

        .player-card {
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            cursor: grab;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            user-select: none;
            text-align: center;
            position: relative;
            min-height: 44px;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
        }

        .player-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .player-card.dragging {
            opacity: 0.5;
            cursor: grabbing;
            transform: rotate(5deg);
        }

        .player-card.in-position {
            margin: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            padding: 8px 4px;
            border: none;
            box-shadow: none;
            position: relative;
        }

        .spare-player {
            background: linear-gradient(135deg, #374151, #6b7280);
            border: 1px solid #4b5563;
        }

        .spare-player:hover {
            background: linear-gradient(135deg, #4b5563, #6b7280);
        }
        
        .player-card.goalie {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            color: #333;
            border: 1px solid #d97706;
        }
        
        .player-card.goalie:hover {
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }
        
        .spare-player.goalie {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            color: #333;
            border: 1px solid #d97706;
        }
        
        .spare-player.goalie:hover {
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }

        .player-card.goalie .position-indicator {
            background: #333;
            color: #fbbf24;
        }

        .position-indicator {
            position: absolute;
            top: 2px;
            right: 2px;
            background: rgba(255,255,255,0.9);
            color: #333;
            font-size: 0.6rem;
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 3px;
            min-width: 16px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            opacity: 0.8;
            transition: opacity 0.3s;
        }

        .player-card.in-position:hover .position-indicator {
            opacity: 1;
        }

        .player-card .roster-position {
            position: absolute;
            bottom: 2px;
            left: 2px;
            background: rgba(255,255,255,0.15);
            color: rgba(255,255,255,0.8);
            font-size: 0.5rem;
            font-weight: bold;
            padding: 1px 3px;
            border-radius: 2px;
            opacity: 0.6;
            transition: opacity 0.3s;
        }

        .player-card:hover .roster-position {
            opacity: 1;
        }

        .player-name {
            font-weight: bold;
            margin-bottom: 2px;
        }

        .player-position {
            font-size: 0.8rem;
            opacity: 0.8;
        }

        .remove-btn {
            position: absolute;
            top: -5px;
            right: -5px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #ff4444;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 12px;
            padding: 0;
            display: none;
        }

        .player-card:hover .remove-btn {
            display: block;
        }

        .clear-line {
            background: #666;
            padding: 5px 10px;
            font-size: 0.8rem;
            margin-top: 10px;
        }

        .clear-line:hover {
            background: #555;
        }

        /* Mobile Optimizations */
        @media (max-width: 768px) {
            .player-card {
                padding: 16px 20px;
                min-height: 50px;
                font-size: 1rem;
                margin-bottom: 10px;
                touch-action: manipulation;
                -webkit-tap-highlight-color: transparent;
            }
            
            .position-slot {
                width: 100px;
                height: 70px;
                min-height: 50px;
                touch-action: manipulation;
                -webkit-tap-highlight-color: transparent;
            }
            
            .position-label {
                font-size: 0.7rem;
            }
            
            button {
                padding: 12px 16px;
                font-size: 16px;
                min-height: 44px;
                touch-action: manipulation;
                -webkit-tap-highlight-color: transparent;
            }
            
            .logo {
                width: 60px;
                height: 60px;
            }
            
            .tagline {
                font-size: 0.9rem;
            }
            
            .positions {
                gap: 8px;
            }
            
            h1 {
                font-size: 1.8rem;
                gap: 10px;
            }
            
            body {
            body {
                padding: 10px;
                font-size: 14px;
            }
            
            .container {
                max-width: 100%;
                margin: 0;
            }
            
            h1 {
                font-size: 1.8rem;
                margin-bottom: 20px;
            }
            
            .controls {
                padding: 15px;
                margin-bottom: 15px;
            }
            
            .team-management h3, .player-management h3 {
                font-size: 1.2rem;
                margin-bottom: 15px;
            }
            
            .team-controls {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .team-section {
                min-height: auto;
                padding: 12px;
            }
            
            .team-section h4 {
                font-size: 0.9rem;
                margin-bottom: 8px;
            }
            
            .team-row {
                flex-direction: column;
                gap: 8px;
            }
            
            .team-controls input[type="text"], 
            .team-controls select,
            .add-player-form input,
            .add-player-form select {
                width: 100%;
                min-width: auto;
                padding: 10px;
                font-size: 16px; /* Prevents zoom on iOS */
            }
            
            .add-player-form {
                flex-direction: column;
                gap: 8px;
                padding: 15px;
            }
            
            .add-player-form label {
                justify-content: center;
                margin: 5px 0;
            }
            
            .btn-upload, .btn-download, .btn-save, .btn-load,
            .add-player-form button {
                width: 100%;
                padding: 12px;
                font-size: 14px;
                margin: 2px 0;
            }
            
            .main-content {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .left-panel {
                max-height: none;
                overflow-y: visible;
            }
            
            .bench, .spares {
                max-height: 200px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            .bench h2, .spares h2 {
                font-size: 1.1rem;
                margin-bottom: 10px;
            }
            
            .ice-rink {
                min-height: auto;
                padding: 15px;
            }
            
            .line-section {
                margin-bottom: 20px;
                padding: 15px;
            }
            
            .line-title {
                font-size: 1.1rem;
                margin-bottom: 10px;
            }
            
            .positions {
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin-bottom: 8px;
            }
            
            .defense-positions {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }
            
            .position-slot {
                width: 100%;
                height: 60px;
                min-width: auto;
            }
            
            .goalie-position {
                width: 100%;
                height: 60px;
                grid-column: span 3;
            }
            
            .player-card {
                padding: 6px 8px;
                margin-bottom: 6px;
                font-size: 12px;
            }
            
            .player-card.in-position {
                padding: 4px 2px;
                font-size: 11px;
            }
            
            .position-label {
                font-size: 0.7rem;
                margin-bottom: 3px;
            }
            
            .player-name {
                font-size: 11px;
                margin-bottom: 1px;
            }
            
            .clear-line {
                width: 100%;
                padding: 8px;
                font-size: 12px;
                margin-top: 8px;
            }
            
            /* Touch-friendly improvements */
            .player-card {
                min-height: 44px; /* iOS minimum touch target */
            }
            
            .position-slot {
                min-height: 44px;
            }
            
            button {
                min-height: 44px;
                touch-action: manipulation;
            }
            
            /* Prevent horizontal scroll */
            .container {
                overflow-x: hidden;
            }
            
            /* Better spacing for mobile */
            .team-management, .player-management {
                margin-top: 15px;
                padding-top: 15px;
            }
        }
        
        /* iPhone SE and smaller screens */
        @media (max-width: 375px) {
            body {
                padding: 5px;
            }
            
            .controls {
                padding: 10px;
            }
            
            .team-section, .line-section {
                padding: 10px;
            }
            
            .positions {
                grid-template-columns: repeat(2, 1fr);
                gap: 5px;
            }
            
            .defense-positions {
                grid-template-columns: repeat(2, 1fr);
                gap: 5px;
            }
            
            .goalie-position {
                grid-column: span 2;
            }
            
            .position-slot {
                height: 50px;
            }
            
            .goalie-position {
                height: 50px;
            }
        }
        
        /* Landscape orientation on mobile */
        @media (max-width: 768px) and (orientation: landscape) {
            .main-content {
                grid-template-columns: 200px 1fr;
                gap: 10px;
            }
            
            .bench, .spares {
                max-height: 150px;
            }
            
            .ice-rink {
                min-height: 400px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <div class="logo">
                <img src="/static/images/line-walrus-logo.png" alt="Line Walrus Logo">
            </div>
            Line Walrus
        </h1>
        <p class="tagline">Because Even a Walrus Can Manage Lines Better</p>
        
        <div class="controls">
            <div class="team-management">
                <h3>🏒 Team Management</h3>
                <div class="team-controls">
                    <div class="team-section">
                        <h4>📁 Import/Export</h4>
                        <div class="team-row">
                            <input type="file" id="csvFile" accept=".csv" style="display: none;">
                            <button onclick="document.getElementById('csvFile').click()" class="btn-upload">📁 Upload CSV</button>
                            <button onclick="downloadTeam()" class="btn-download">💾 Download CSV</button>
                        </div>
                        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7); margin-top: 5px; font-style: italic;">
                            💡 Compatible with SportNinja CSV exports
                        </div>
                    </div>
                    
                    <div class="team-section">
                        <h4>💾 Save Current Team</h4>
                        <div class="team-row">
                            <input type="text" id="teamName" placeholder="Enter team name..." maxlength="30">
                            <button onclick="saveTeam()" class="btn-save">💾 Save Team</button>
                        </div>
                    </div>
                    
                    <div class="team-section">
                        <h4>📂 Load Saved Team</h4>
                        <div class="team-row">
                            <select id="teamSelect">
                                <option value="">Choose a team...</option>
                            </select>
                            <button onclick="loadTeam()" class="btn-load">📂 Load Team</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="player-management">
                <h3>👥 Player Management</h3>
                <div class="add-player-form">
                    <input type="text" id="playerName" placeholder="Player Name" maxlength="30">
                    <input type="text" id="jerseyNumber" placeholder="Jersey #" maxlength="3" style="width: 80px;">
                    <select id="playerPosition">
                        <option value="FORWARD">Forward</option>
                        <option value="DEFENSE">Defense</option>
                        <option value="GOALIE">Goalie</option>
                    </select>
                    <label style="display: flex; align-items: center; gap: 5px; color: white;">
                        <input type="checkbox" id="isAffiliate" style="margin: 0;">
                        Affiliate Player
                    </label>
                    <button onclick="addPlayer()">Add Player</button>
                    <button onclick="printLines()" style="background: #dc3545;">🖨️ Print Lines</button>
                    <button onclick="saveAndShareLines()" style="background: #28a745;">🔗 Save & Share Lines</button>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="left-panel">
                <div class="bench">
                    <h2>🪑 Bench</h2>
                    <div id="benchPlayers"></div>
                </div>
                
                <div class="spares">
                    <h2>🔄 Spares</h2>
                    <div id="sparePlayers"></div>
                </div>
            </div>

            <div class="ice-rink">
                <div class="line-section">
                    <div class="line-title">Line 1</div>
                    <div class="positions">
                        <div class="position-slot" data-position="LW" data-line="1">
                            <div class="position-label">LW</div>
                        </div>
                        <div class="position-slot" data-position="C" data-line="1">
                            <div class="position-label">C</div>
                        </div>
                        <div class="position-slot" data-position="RW" data-line="1">
                            <div class="position-label">RW</div>
                        </div>
                    </div>
                    <div class="positions defense-positions">
                        <div class="position-slot" data-position="LD" data-line="1">
                            <div class="position-label">LD</div>
                        </div>
                        <div class="position-slot" data-position="RD" data-line="1">
                            <div class="position-label">RD</div>
                        </div>
                    </div>
                    <div class="goalie-row">
                        <div class="position-slot goalie-position" data-position="G" data-line="1">
                            <div class="position-label">G</div>
                        </div>
                    </div>
                    <button class="clear-line" onclick="clearLine(1)">Clear Line</button>
                </div>

                <div class="line-section">
                    <div class="line-title">Line 2</div>
                    <div class="positions">
                        <div class="position-slot" data-position="LW" data-line="2">
                            <div class="position-label">LW</div>
                        </div>
                        <div class="position-slot" data-position="C" data-line="2">
                            <div class="position-label">C</div>
                        </div>
                        <div class="position-slot" data-position="RW" data-line="2">
                            <div class="position-label">RW</div>
                        </div>
                    </div>
                    <div class="positions defense-positions">
                        <div class="position-slot" data-position="LD" data-line="2">
                            <div class="position-label">LD</div>
                        </div>
                        <div class="position-slot" data-position="RD" data-line="2">
                            <div class="position-label">RD</div>
                        </div>
                    </div>
                    <button class="clear-line" onclick="clearLine(2)">Clear Line</button>
                </div>

                <div class="line-section">
                    <div class="line-title">Line 3</div>
                    <div class="positions">
                        <div class="position-slot" data-position="LW" data-line="3">
                            <div class="position-label">LW</div>
                        </div>
                        <div class="position-slot" data-position="C" data-line="3">
                            <div class="position-label">C</div>
                        </div>
                        <div class="position-slot" data-position="RW" data-line="3">
                            <div class="position-label">RW</div>
                        </div>
                    </div>
                    <div class="positions defense-positions">
                        <div class="position-slot" data-position="LD" data-line="3">
                            <div class="position-label">LD</div>
                        </div>
                        <div class="position-slot" data-position="RD" data-line="3">
                            <div class="position-label">RD</div>
                        </div>
                    </div>
                    <button class="clear-line" onclick="clearLine(3)">Clear Line</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let draggedPlayer = null;

        // Load initial data
        window.onload = function() {
            loadPlayers();
            loadLines();
            setupDropZones();
            loadTeamList();
            setupFileUpload();
        };

        async function addPlayer() {
            const name = document.getElementById('playerName').value.trim();
            const position = document.getElementById('playerPosition').value;
            const jerseyNumber = document.getElementById('jerseyNumber').value.trim();
            const isAffiliate = document.getElementById('isAffiliate').checked;
            
            if (!name) {
                alert('Please enter a player name');
                return;
            }
            
            const response = await fetch('/api/players', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name, 
                    position, 
                    jersey_number: jerseyNumber,
                    affiliate: isAffiliate
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('playerName').value = '';
                document.getElementById('jerseyNumber').value = '';
                document.getElementById('isAffiliate').checked = false;
                loadPlayers();
            } else {
                alert(result.message);
            }
        }



        async function removePlayer(playerId) {
            const response = await fetch(`/api/players/${playerId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadPlayers();
                loadLines();
            }
        }

        async function loadPlayers() {
            try {
                const response = await fetch('/api/players');
                const players = await response.json();
                
                console.log('Loading players:', players);
                
                const benchDiv = document.getElementById('benchPlayers');
                const sparesDiv = document.getElementById('sparePlayers');
                benchDiv.innerHTML = '';
                sparesDiv.innerHTML = '';
                
                // Get players currently in lines
                const linesResponse = await fetch('/api/lines');
                const lines = await linesResponse.json();
                const playersInLines = new Set();
                
                Object.values(lines).forEach(line => {
                    Object.values(line).forEach(player => {
                        if (player) playersInLines.add(player.id);
                    });
                });
                
                // Separate regular players and spares
                const regularPlayers = players.filter(p => !playersInLines.has(p.id) && !p.affiliate);
                const sparePlayers = players.filter(p => !playersInLines.has(p.id) && p.affiliate);
                
                console.log('Regular players (bench):', regularPlayers);
                console.log('Spare players:', sparePlayers);
                
                // Show regular bench players
                regularPlayers.forEach(player => {
                    const playerCard = createPlayerCard(player);
                    benchDiv.appendChild(playerCard);
                });
                
                // Show spare players
                sparePlayers.forEach(player => {
                    const playerCard = createPlayerCard(player);
                    sparesDiv.appendChild(playerCard);
                });
            } catch (error) {
                console.error('Error loading players:', error);
            }
        }

        function createPlayerCard(player) {
            const card = document.createElement('div');
            card.className = 'player-card';
            if (player.affiliate) {
                card.classList.add('spare-player');
            }
            if (player.roster_position === 'GOALIE' || player.position === 'GOALIE') {
                card.classList.add('goalie');
            }
            card.draggable = true;
            card.dataset.playerId = player.id;
            card.dataset.rosterPosition = player.roster_position || player.position;
            
            const jerseyDisplay = player.jersey_number ? `#${player.jersey_number}` : '';
            card.innerHTML = `
                <div class="player-name">${player.name} ${jerseyDisplay}</div>
                <div class="roster-position">${player.roster_position || player.position}</div>
                <button onclick="removePlayer(${player.id})" class="remove-btn">×</button>
            `;
            
            card.addEventListener('dragstart', (e) => {
                draggedPlayer = player;
                e.dataTransfer.setData('text/plain', player.id);
            });
            
            return card;
        }

        async function loadLines() {
            try {
                const response = await fetch('/api/lines');
                const lines = await response.json();
                
                console.log('Loading lines:', lines);
                
                // Clear all position slots
                document.querySelectorAll('.position-slot').forEach(slot => {
                    const positionLabel = slot.querySelector('.position-label');
                    if (positionLabel) {
                        slot.innerHTML = positionLabel.outerHTML;
                    } else {
                        // If no position label exists, create one based on the slot's data attributes
                        const position = slot.dataset.position;
                        slot.innerHTML = `<div class="position-label">${position}</div>`;
                    }
                });
                
                // Populate with players
                Object.entries(lines).forEach(([lineNum, line]) => {
                    Object.entries(line).forEach(([position, player]) => {
                        if (player) {
                            const slot = document.querySelector(`[data-line="${lineNum}"][data-position="${position}"]`);
                            if (slot) {
                                const playerCardClass = (player.roster_position === 'GOALIE' || player.position === 'GOALIE') ? 'player-card goalie' : 'player-card';
                                slot.innerHTML = `
                                    <div class="${playerCardClass} in-position" data-player-id="${player.id}" draggable="true">
                                        <div class="position-indicator">${position}</div>
                                        <div class="player-name">${player.name}</div>
                                        <button onclick="removeFromLine(${player.id})" class="remove-btn">×</button>
                                    </div>
                                `;
                                
                                // Add drag event listeners to the player card
                                const playerCard = slot.querySelector('.player-card');
                                if (playerCard) {
                                    playerCard.addEventListener('dragstart', (e) => {
                                        draggedPlayer = player;
                                        e.dataTransfer.setData('text/plain', player.id);
                                        e.target.classList.add('dragging');
                                    });
                                    
                                    playerCard.addEventListener('dragend', (e) => {
                                        e.target.classList.remove('dragging');
                                    });
                                }
                            }
                        }
                    });
                });
            } catch (error) {
                console.error('Error loading lines:', error);
            }
        }

        function setupDropZones() {
            document.querySelectorAll('.position-slot').forEach(slot => {
                slot.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    if (draggedPlayer) {
                        const position = slot.dataset.position;
                        const playerPosition = draggedPlayer.roster_position || draggedPlayer.position;
                        
                        // Color coding based on position suitability
                        if (position === 'G' && playerPosition === 'GOALIE') {
                            slot.style.borderColor = '#28a745'; // Green for perfect match
                        } else if (position === 'G' && playerPosition !== 'GOALIE') {
                            slot.style.borderColor = '#dc3545'; // Red for goalie position
                        } else if ((position === 'LW' || position === 'C' || position === 'RW') && playerPosition === 'FORWARD') {
                            slot.style.borderColor = '#28a745'; // Green for forward positions
                        } else if ((position === 'LD' || position === 'RD') && playerPosition === 'DEFENSE') {
                            slot.style.borderColor = '#28a745'; // Green for defense positions
                        } else {
                            slot.style.borderColor = '#ffc107'; // Yellow for mixed positions
                        }
                    }
                });
                
                slot.addEventListener('dragleave', (e) => {
                    e.preventDefault();
                    slot.style.borderColor = 'rgba(255,255,255,0.5)';
                });
                
                slot.addEventListener('drop', async (e) => {
                    e.preventDefault();
                    slot.style.borderColor = 'rgba(255,255,255,0.5)';
                    
                    if (draggedPlayer) {
                        const lineNum = slot.dataset.line;
                        const position = slot.dataset.position;
                        
                        try {
                            // Check if the target slot already has a player
                            const existingPlayer = slot.querySelector('.player-card');
                            if (existingPlayer) {
                                // If there's already a player, we need to swap them
                                const existingPlayerId = existingPlayer.dataset.playerId;
                                
                                // First, remove the dragged player from their current position
                                await fetch(`/api/lines/remove-player/${draggedPlayer.id}`, {
                                    method: 'DELETE'
                                });
                                
                                // Then, remove the existing player from the target position
                                await fetch(`/api/lines/remove-player/${existingPlayerId}`, {
                                    method: 'DELETE'
                                });
                                
                                // Now place both players in their new positions
                                await fetch('/api/lines/set-player', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        player_id: draggedPlayer.id,
                                        line_num: lineNum,
                                        position: position
                                    })
                                });
                                
                                // Find where the dragged player was originally and put the existing player there
                                const originalSlot = document.querySelector(`[data-player-id="${draggedPlayer.id}"]`);
                                if (originalSlot) {
                                    const originalLine = originalSlot.closest('.position-slot').dataset.line;
                                    const originalPosition = originalSlot.closest('.position-slot').dataset.position;
                                    
                                    await fetch('/api/lines/set-player', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                            player_id: existingPlayerId,
                                            line_num: originalLine,
                                            position: originalPosition
                                        })
                                    });
                                }
                            } else {
                                // Simple case: just place the player in the empty slot
                                const response = await fetch('/api/lines/set-player', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        player_id: draggedPlayer.id,
                                        line_num: lineNum,
                                        position: position
                                    })
                                });
                            }
                            
                            // Clear the dragged player reference
                            draggedPlayer = null;
                            
                            // Refresh the display
                            console.log('Refreshing display...');
                            await loadPlayers();
                            await loadLines();
                            console.log('Display refresh complete');
                            
                        } catch (error) {
                            console.error('Error during drop operation:', error);
                            // Clear the dragged player reference on error
                            draggedPlayer = null;
                        }
                    }
                });
            });
        }

        async function removeFromLine(playerId) {
            const response = await fetch(`/api/lines/remove-player/${playerId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadPlayers();
                loadLines();
            }
        }

        async function clearLine(lineNum) {
            try {
                const response = await fetch(`/api/lines/clear/${lineNum}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    // Clear the visual display immediately
                    const lineSection = document.querySelector(`[data-line="${lineNum}"]`).closest('.line-section');
                    lineSection.querySelectorAll('.position-slot').forEach(slot => {
                        const positionLabel = slot.querySelector('.position-label');
                        if (positionLabel) {
                            slot.innerHTML = positionLabel.outerHTML;
                        }
                    });
                    
                    // Reload data
                    await loadPlayers();
                    await loadLines();
                    
                    // Show feedback
                    showFeedback(`Line ${lineNum} cleared`, 'success');
                } else {
                    showFeedback('Error clearing line', 'error');
                }
            } catch (error) {
                console.error('Error clearing line:', error);
                showFeedback('Error clearing line', 'error');
            }
        }

        function setupFileUpload() {
            document.getElementById('csvFile').addEventListener('change', async function(e) {
                const file = e.target.files[0];
                if (!file) return;
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/teams/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(result.message);
                        loadPlayers();
                        loadLines();
                        loadTeamList();
                    } else {
                        alert('Error: ' + result.message);
                    }
                } catch (error) {
                    alert('Error uploading file: ' + error.message);
                }
                
                // Reset file input
                e.target.value = '';
            });
        }

        async function downloadTeam() {
            try {
                const response = await fetch('/api/teams/download');
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `hockey_team_${new Date().toISOString().slice(0,10)}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    alert('Error downloading team');
                }
            } catch (error) {
                alert('Error downloading team: ' + error.message);
            }
        }

        async function saveTeam() {
            const teamName = document.getElementById('teamName').value.trim();
            
            if (!teamName) {
                alert('Please enter a team name');
                return;
            }
            
            try {
                const response = await fetch('/api/teams/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ team_name: teamName })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(result.message);
                    loadTeamList();
                    document.getElementById('teamName').value = '';
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                alert('Error saving team: ' + error.message);
            }
        }

        async function loadTeam() {
            const teamSelect = document.getElementById('teamSelect');
            const filename = teamSelect.value;
            
            if (!filename) {
                alert('Please select a team to load');
                return;
            }
            
            try {
                const response = await fetch('/api/teams/load', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: filename })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(result.message);
                    loadPlayers();
                    loadLines();
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                alert('Error loading team: ' + error.message);
            }
        }

        async function loadTeamList() {
            try {
                const response = await fetch('/api/teams/list');
                const teams = await response.json();
                
                const teamSelect = document.getElementById('teamSelect');
                teamSelect.innerHTML = '<option value="">Select a team...</option>';
                
                teams.forEach(team => {
                    const option = document.createElement('option');
                    option.value = team.filename;
                    option.textContent = `${team.name} (${team.player_count} players)`;
                    teamSelect.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading team list:', error);
            }
        }

        function printLines() {
            const printWindow = window.open('/api/print-lines', '_blank');
            if (printWindow) {
                printWindow.onload = function() {
                    printWindow.print();
                };
            } else {
                alert('Please allow popups to print lines');
            }
        }

        async function saveAndShareLines() {
            const lineName = prompt('Enter a name for your lines:');
            if (!lineName || lineName.trim() === '') {
                return;
            }
            
            try {
                const response = await fetch('/api/lines/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: lineName.trim() })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Create a modal to show the share URL
                    const modal = document.createElement('div');
                    modal.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0,0,0,0.8);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 1000;
                    `;
                    
                    modal.innerHTML = `
                        <div style="
                            background: white;
                            padding: 30px;
                            border-radius: 15px;
                            max-width: 500px;
                            text-align: center;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        ">
                            <h2 style="color: #1e3a8a; margin-bottom: 20px;">🎉 Lines Saved Successfully!</h2>
                            <p style="margin-bottom: 20px; color: #333;">Your lines "${lineName}" have been saved and can be shared with others.</p>
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 5px; color: #666; font-weight: bold;">Share this URL:</label>
                                <input type="text" value="${result.share_url}" readonly style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 2px solid #ddd;
                                    border-radius: 5px;
                                    font-family: monospace;
                                    background: #f8f9fa;
                                ">
                            </div>
                            <div style="display: flex; gap: 10px; justify-content: center;">
                                <button onclick="copyToClipboard('${result.share_url}')" style="
                                    background: #28a745;
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    font-weight: bold;
                                ">📋 Copy URL</button>
                                <button onclick="this.closest('div[style*=\\"position: fixed\\"]').remove()" style="
                                    background: #6c757d;
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 5px;
                                    cursor: pointer;
                                ">Close</button>
                            </div>
                        </div>
                    `;
                    
                    document.body.appendChild(modal);
                } else {
                    alert('Error saving lines: ' + result.message);
                }
            } catch (error) {
                console.error('Error saving lines:', error);
                alert('Error saving lines. Please try again.');
            }
        }

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(function() {
                alert('URL copied to clipboard!');
            }, function(err) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('URL copied to clipboard!');
            });
        }

        // Mobile-first player placement system
        let selectedPlayer = null;
        let selectedPlayerElement = null;
        let isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

        function setupMobilePlayerPlacement() {
            if (isMobile) {
                // Mobile: Use touch events only
                setupMobileTouchPlacement();
            } else {
                // Desktop: Use click events
                setupDesktopClickPlacement();
            }
        }

        function setupMobileTouchPlacement() {
            let touchStartTime = 0;
            let touchStartX = 0;
            let touchStartY = 0;
            let isDragging = false;

            // Touch start - detect what was touched
            document.addEventListener('touchstart', function(e) {
                const playerCard = e.target.closest('.player-card');
                const positionSlot = e.target.closest('.position-slot');
                
                touchStartTime = Date.now();
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                isDragging = false;

                console.log('Touch start:', { playerCard: !!playerCard, positionSlot: !!positionSlot, selectedPlayer: !!selectedPlayer });

                // Visual feedback for touch
                if (playerCard && !playerCard.classList.contains('in-position')) {
                    playerCard.style.transform = 'scale(0.95)';
                    playerCard.style.opacity = '0.8';
                }
                if (positionSlot && selectedPlayer) {
                    positionSlot.style.transform = 'scale(0.95)';
                    positionSlot.style.opacity = '0.8';
                }
            }, { passive: true });

            // Touch move - detect if user is dragging
            document.addEventListener('touchmove', function(e) {
                if (touchStartX !== undefined) {
                    const touchEndX = e.touches[0].clientX;
                    const touchEndY = e.touches[0].clientY;
                    const distance = Math.sqrt(
                        Math.pow(touchEndX - touchStartX, 2) + 
                        Math.pow(touchEndY - touchStartY, 2)
                    );
                    
                    if (distance > 5) { // Small threshold for mobile
                        isDragging = true;
                    }
                }
            }, { passive: true });

            // Touch end - handle the action
            document.addEventListener('touchend', function(e) {
                const touchEndTime = Date.now();
                const touchEndX = e.changedTouches[0].clientX;
                const touchEndY = e.changedTouches[0].clientY;
                
                // Calculate distance moved
                const distance = Math.sqrt(
                    Math.pow(touchEndX - touchStartX, 2) + 
                    Math.pow(touchEndY - touchStartY, 2)
                );
                
                // Reset visual feedback
                document.querySelectorAll('.player-card, .position-slot').forEach(el => {
                    el.style.transform = '';
                    el.style.opacity = '';
                });

                // Only handle if it's a tap (not a drag)
                if (!isDragging && touchEndTime - touchStartTime < 500 && distance < 10) {
                    e.preventDefault();
                    
                    const playerCard = e.target.closest('.player-card');
                    const positionSlot = e.target.closest('.position-slot');
                    
                    console.log('Touch end - tap detected:', { 
                        playerCard: !!playerCard, 
                        positionSlot: !!positionSlot, 
                        selectedPlayer: !!selectedPlayer,
                        isDragging: isDragging,
                        duration: touchEndTime - touchStartTime,
                        distance: distance
                    });
                    
                    if (playerCard && !playerCard.classList.contains('in-position')) {
                        // Select player
                        console.log('Selecting player');
                        selectPlayer(playerCard);
                        showFeedback('Player selected! Tap a position to place.', 'info');
                    } else if (positionSlot && selectedPlayer) {
                        // Place player
                        console.log('Placing player in position');
                        placePlayerInPosition(positionSlot);
                    } else if (!playerCard && !positionSlot) {
                        // Deselect
                        console.log('Deselecting player');
                        deselectPlayer();
                    }
                } else {
                    console.log('Touch end - not a tap:', { 
                        isDragging: isDragging, 
                        duration: touchEndTime - touchStartTime, 
                        distance: distance 
                    });
                }

                // Reset tracking variables
                touchStartX = undefined;
                touchStartY = undefined;
                touchStartTime = 0;
                isDragging = false;
            }, { passive: false });
        }

        function setupDesktopClickPlacement() {
            document.addEventListener('click', function(e) {
                const playerCard = e.target.closest('.player-card');
                const positionSlot = e.target.closest('.position-slot');
                
                if (playerCard && !playerCard.classList.contains('in-position')) {
                    selectPlayer(playerCard);
                } else if (positionSlot && selectedPlayer) {
                    placePlayerInPosition(positionSlot);
                } else if (!playerCard && !positionSlot) {
                    deselectPlayer();
                }
            });
        }

        function selectPlayer(playerCard) {
            // Deselect previous player
            deselectPlayer();
            
            // Select new player
            selectedPlayer = {
                id: parseInt(playerCard.dataset.playerId),
                name: playerCard.querySelector('.player-name').textContent,
                roster_position: playerCard.dataset.rosterPosition || 'FORWARD'
            };
            selectedPlayerElement = playerCard;
            
            // Visual feedback
            playerCard.style.transform = 'scale(1.05)';
            playerCard.style.boxShadow = '0 0 15px rgba(59, 130, 246, 0.8)';
            playerCard.style.border = '2px solid #3b82f6';
            
            // Show selection indicator
            showSelectionIndicator();
        }

        function deselectPlayer() {
            if (selectedPlayerElement) {
                selectedPlayerElement.style.transform = '';
                selectedPlayerElement.style.boxShadow = '';
                selectedPlayerElement.style.border = '';
                selectedPlayerElement = null;
            }
            selectedPlayer = null;
            hideSelectionIndicator();
        }

        function placePlayerInPosition(positionSlot) {
            if (!selectedPlayer) return;
            
            const lineNum = positionSlot.dataset.line;
            const position = positionSlot.dataset.position;
            
            // Check if position is suitable for player
            const playerPosition = selectedPlayer.roster_position;
            let isValidPosition = true;
            let feedbackMessage = '';
            
            if (position === 'G' && playerPosition !== 'GOALIE') {
                isValidPosition = false;
                feedbackMessage = 'Only goalies can be placed in goalie position';
            } else if ((position === 'LW' || position === 'C' || position === 'RW') && playerPosition !== 'FORWARD') {
                isValidPosition = false;
                feedbackMessage = 'Only forwards can be placed in forward positions';
            } else if ((position === 'LD' || position === 'RD') && playerPosition !== 'DEFENSE') {
                isValidPosition = false;
                feedbackMessage = 'Only defensemen can be placed in defense positions';
            }
            
            if (!isValidPosition) {
                showFeedback(feedbackMessage, 'error');
                return;
            }
            
            // Place the player
            setPlayerInLine(selectedPlayer.id, lineNum, position).then(() => {
                deselectPlayer();
                showFeedback(`Placed ${selectedPlayer.name} in ${position}`, 'success');
            }).catch(error => {
                showFeedback('Error placing player', 'error');
            });
        }

        function showSelectionIndicator() {
            // Create or update selection indicator
            let indicator = document.getElementById('selection-indicator');
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'selection-indicator';
                indicator.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #3b82f6;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    z-index: 1000;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    animation: slideIn 0.3s ease-out;
                `;
                document.body.appendChild(indicator);
            }
            indicator.textContent = `Selected: ${selectedPlayer.name}`;
            indicator.style.display = 'block';
            
            // Add CSS animation
            if (!document.getElementById('selection-animation')) {
                const style = document.createElement('style');
                style.id = 'selection-animation';
                style.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }
        }

        function hideSelectionIndicator() {
            const indicator = document.getElementById('selection-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }

        function showFeedback(message, type) {
            // Create feedback element
            const feedback = document.createElement('div');
            feedback.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: ${type === 'success' ? '#10b981' : '#ef4444'};
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                font-weight: bold;
                z-index: 1001;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                animation: fadeInOut 2s ease-in-out;
            `;
            feedback.textContent = message;
            document.body.appendChild(feedback);
            
            // Add CSS animation
            if (!document.getElementById('feedback-animation')) {
                const style = document.createElement('style');
                style.id = 'feedback-animation';
                style.textContent = `
                    @keyframes fadeInOut {
                        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                        20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                        80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Remove after animation
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.parentNode.removeChild(feedback);
                }
            }, 2000);
        }

        // Mobile touch improvements
        function setupMobileTouch() {
            // Prevent zoom on double tap
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function (event) {
                const now = (new Date()).getTime();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);

            // Improve touch scrolling
            document.addEventListener('touchmove', function(event) {
                if (event.scale !== 1) {
                    event.preventDefault();
                }
            }, { passive: false });

            // Add touch feedback for buttons
            document.querySelectorAll('button').forEach(button => {
                button.addEventListener('touchstart', function() {
                    this.style.transform = 'scale(0.95)';
                });
                
                button.addEventListener('touchend', function() {
                    this.style.transform = 'scale(1)';
                });
            });

            // Add touch feedback for player cards
            document.addEventListener('touchstart', function(e) {
                const playerCard = e.target.closest('.player-card');
                if (playerCard && !playerCard.classList.contains('in-position')) {
                    playerCard.style.transform = 'scale(0.98)';
                }
            }, { passive: true });

            document.addEventListener('touchend', function(e) {
                const playerCard = e.target.closest('.player-card');
                if (playerCard && !playerCard.classList.contains('in-position')) {
                    playerCard.style.transform = '';
                }
            }, { passive: true });

            // Add touch feedback for position slots
            document.addEventListener('touchstart', function(e) {
                const positionSlot = e.target.closest('.position-slot');
                if (positionSlot && selectedPlayer) {
                    positionSlot.style.transform = 'scale(0.95)';
                }
            }, { passive: true });

            document.addEventListener('touchend', function(e) {
                const positionSlot = e.target.closest('.position-slot');
                if (positionSlot) {
                    positionSlot.style.transform = '';
                }
            }, { passive: true });
        }

                    // Initialize all functionality when page loads
            document.addEventListener('DOMContentLoaded', function() {
                setupMobileTouch();
                setupMobilePlayerPlacement();
            });
    </script>
</body>
</html>'''

    # Write the template to a file
    with open('templates/index.html', 'w') as f:
        f.write(html_template)
    
    # Get port from environment variable (for production) or use 5001 for local
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)