from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)

class HockeyTeamManager:
    def __init__(self, data_file="hockey_team.json"):
        self.data_file = data_file
        self.players = []
        self.lines = {
            "1": {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None},
            "2": {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None},
            "3": {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None}
        }
        self.load_data()
    
    def save_data(self):
        data = {
            "players": self.players,
            "lines": self.lines,
            "last_updated": datetime.now().isoformat()
        }
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
    
    def add_player(self, name, position):
        if any(p["name"].lower() == name.lower() for p in self.players):
            return {"success": False, "message": f"{name} already exists"}
        
        valid_positions = ["C", "LW", "RW", "LD", "RD", "G"]
        if position.upper() not in valid_positions:
            return {"success": False, "message": "Invalid position"}
        
        player = {
            "name": name.strip(),
            "position": position.upper(),
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

# Create the manager instance
manager = HockeyTeamManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players', methods=['GET'])
def get_players():
    return jsonify(manager.players)

@app.route('/api/players', methods=['POST'])
def add_player():
    data = request.json
    result = manager.add_player(data['name'], data['position'])
    return jsonify(result)

@app.route('/api/players/<int:player_id>', methods=['DELETE'])
def remove_player(player_id):
    result = manager.remove_player(player_id)
    return jsonify(result)

@app.route('/api/lines', methods=['GET'])
def get_lines():
    return jsonify(manager.lines)

@app.route('/api/lines/set-player', methods=['POST'])
def set_player_in_line():
    data = request.json
    result = manager.set_player_in_line(
        data['player_id'], 
        data['line_num'], 
        data['position']
    )
    return jsonify(result)

@app.route('/api/lines/remove-player/<int:player_id>', methods=['DELETE'])
def remove_from_line(player_id):
    result = manager.remove_from_line(player_id)
    return jsonify(result)

@app.route('/api/lines/clear/<line_num>', methods=['DELETE'])
def clear_line(line_num):
    if line_num in manager.lines:
        manager.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                                  "LD": None, "RD": None, "G": None}
        manager.save_data()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/teams/upload', methods=['POST'])
def upload_team():
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
        
        # Clear current team
        manager.players = []
        for line_num in manager.lines:
            manager.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                                      "LD": None, "RD": None, "G": None}
        
        # Add players from CSV
        for row in csv_reader:
            name = row.get('name', '').strip()
            position = row.get('position', '').strip().upper()
            
            if name and position:
                valid_positions = ["C", "LW", "RW", "LD", "RD", "G"]
                if position in valid_positions:
                    player = {
                        "name": name,
                        "position": position,
                        "id": len(manager.players) + 1
                    }
                    manager.players.append(player)
        
        manager.save_data()
        return jsonify({"success": True, "message": f"Team uploaded successfully! Added {len(manager.players)} players."})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error processing file: {str(e)}"})

@app.route('/api/teams/download', methods=['GET'])
def download_team():
    try:
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['name', 'position'])
        
        for player in manager.players:
            writer.writerow([player['name'], player['position']])
        
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
    data = request.json
    team_name = data.get('team_name', 'hockey_team').strip()
    
    if not team_name:
        team_name = 'hockey_team'
    
    # Create a copy of current data
    team_data = {
        "players": manager.players,
        "lines": manager.lines,
        "last_updated": datetime.now().isoformat(),
        "team_name": team_name
    }
    
    # Save to a new file
    filename = f"{team_name.replace(' ', '_').lower()}.json"
    filepath = os.path.join(os.path.dirname(manager.data_file), filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(team_data, f, indent=2)
        return jsonify({"success": True, "message": f"Team saved as {filename}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving team: {str(e)}"})

@app.route('/api/teams/load', methods=['POST'])
def load_team():
    data = request.json
    filename = data.get('filename', 'hockey_team.json')
    
    filepath = os.path.join(os.path.dirname(manager.data_file), filename)
    
    if not os.path.exists(filepath):
        return jsonify({"success": False, "message": "Team file not found"})
    
    try:
        with open(filepath, 'r') as f:
            team_data = json.load(f)
        
        manager.players = team_data.get("players", [])
        manager.lines = team_data.get("lines", manager.lines)
        manager.save_data()
        
        return jsonify({"success": True, "message": f"Team loaded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error loading team: {str(e)}"})

@app.route('/api/teams/list', methods=['GET'])
def list_teams():
    try:
        teams = []
        directory = os.path.dirname(manager.data_file)
        
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
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

@app.route('/api/print-lines', methods=['GET'])
def print_lines():
    try:
        # Get current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Create print-friendly HTML
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>SKAHL Line Builder - Lines</title>
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
                    border-bottom: 3px solid #1e3c72;
                    padding-bottom: 20px;
                }}
                .header h1 {{
                    color: #1e3c72;
                    font-size: 28px;
                    margin-bottom: 5px;
                }}
                .header h2 {{
                    color: #2a5298;
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
                    color: #1e3c72;
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
                    border: 2px solid #1e3c72; 
                    padding: 12px 8px; 
                    min-width: 100px; 
                    text-align: center; 
                    background: white;
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .position-label {{ 
                    font-weight: bold; 
                    color: #1e3c72; 
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
                    border: 2px solid #ff6b35;
                    background: #fff5f2;
                    min-width: 100px;
                }}
                .goalie-position .position-label {{
                    color: #ff6b35;
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
                <h1>🏒 SKAHL Line Builder</h1>
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
        for line_num in ["1", "2", "3"]:
            if manager.lines[line_num]['G']:
                goalie_player = manager.lines[line_num]['G']
                break
        
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SKAHL Line Builder</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
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
            color: #ff6b35;
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
            color: #ff6b35;
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
        }

        .team-section h4 {
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
            background: #2a5298;
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
            background: #17a2b8;
        }

        .btn-upload:hover {
            background: #138496;
            transform: translateY(-1px);
        }

        .btn-download {
            background: #6f42c1;
        }

        .btn-download:hover {
            background: #5a32a3;
            transform: translateY(-1px);
        }

        .btn-save {
            background: #fd7e14;
        }

        .btn-save:hover {
            background: #e8690b;
            transform: translateY(-1px);
        }

        .btn-load {
            background: #20c997;
        }

        .btn-load:hover {
            background: #1ba085;
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
            background: #ff6b35;
            color: white;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }

        button:hover {
            background: #e55a2b;
        }

        .main-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }

        .bench {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }

        .bench h2 {
            margin-bottom: 15px;
            text-align: center;
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
        }

        .position-slot.drag-over {
            border-color: #ff6b35;
            background: rgba(255,107,53,0.2);
            transform: scale(1.05);
        }

        .position-label {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.7);
            margin-bottom: 5px;
            font-weight: bold;
        }

        .player-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
            cursor: grab;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            user-select: none;
            text-align: center;
            position: relative;
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
            padding: 4px 8px;
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

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .positions {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .goalie-position {
                grid-column: span 2;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏒 SKAHL Line Builder</h1>
        
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
                    <input type="text" id="playerName" placeholder="Player Name" maxlength="20">
                    <select id="playerPosition">
                        <option value="C">Center</option>
                        <option value="LW">Left Wing</option>
                        <option value="RW">Right Wing</option>
                        <option value="LD">Left Defense</option>
                        <option value="RD">Right Defense</option>
                        <option value="G">Goalie</option>
                    </select>
                    <button onclick="addPlayer()">Add Player</button>
                    <button onclick="addSamplePlayers()" style="background: #28a745;">Add Sample Players</button>
                    <button onclick="printLines()" style="background: #dc3545;">🖨️ Print Lines</button>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="bench">
                <h2>🪑 Bench</h2>
                <div id="benchPlayers"></div>
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
                    <div class="goalie-row">
                        <div class="position-slot goalie-position" data-position="G" data-line="2">
                            <div class="position-label">G</div>
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
                    <div class="goalie-row">
                        <div class="position-slot goalie-position" data-position="G" data-line="3">
                            <div class="position-label">G</div>
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
            
            if (!name) {
                alert('Please enter a player name');
                return;
            }
            
            const response = await fetch('/api/players', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, position })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('playerName').value = '';
                loadPlayers();
            } else {
                alert(result.message);
            }
        }

        async function addSamplePlayers() {
            const samplePlayers = [
                { name: 'Connor McDavid', position: 'C' },
                { name: 'Alex Ovechkin', position: 'LW' },
                { name: 'David Pastrnak', position: 'RW' },
                { name: 'Erik Karlsson', position: 'LD' },
                { name: 'Cale Makar', position: 'RD' },
                { name: 'Igor Shesterkin', position: 'G' },
                { name: 'Sidney Crosby', position: 'C' },
                { name: 'Brad Marchand', position: 'LW' },
                { name: 'Mitch Marner', position: 'RW' },
                { name: 'Victor Hedman', position: 'LD' },
                { name: 'Aaron Ekblad', position: 'RD' },
                { name: 'Frederik Andersen', position: 'G' }
            ];
            
            for (const player of samplePlayers) {
                await fetch('/api/players', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(player)
                });
            }
            
            loadPlayers();
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
            const response = await fetch('/api/players');
            const players = await response.json();
            
            const benchDiv = document.getElementById('benchPlayers');
            benchDiv.innerHTML = '';
            
            // Get players currently in lines
            const linesResponse = await fetch('/api/lines');
            const lines = await linesResponse.json();
            const playersInLines = new Set();
            
            Object.values(lines).forEach(line => {
                Object.values(line).forEach(player => {
                    if (player) playersInLines.add(player.id);
                });
            });
            
            // Show only bench players
            const benchPlayers = players.filter(p => !playersInLines.has(p.id));
            
            benchPlayers.forEach(player => {
                const playerCard = createPlayerCard(player);
                benchDiv.appendChild(playerCard);
            });
        }

        function createPlayerCard(player) {
            const card = document.createElement('div');
            card.className = 'player-card';
            card.draggable = true;
            card.dataset.playerId = player.id;
            card.innerHTML = `
                <div class="player-name">${player.name}</div>
                <div class="player-position">${player.position}</div>
                <button onclick="removePlayer(${player.id})" class="remove-btn">×</button>
            `;
            
            card.addEventListener('dragstart', (e) => {
                draggedPlayer = player;
                e.dataTransfer.setData('text/plain', player.id);
            });
            
            return card;
        }

        async function loadLines() {
            const response = await fetch('/api/lines');
            const lines = await response.json();
            
            // Clear all position slots
            document.querySelectorAll('.position-slot').forEach(slot => {
                slot.innerHTML = slot.querySelector('.position-label').outerHTML;
            });
            
            // Populate with players
            Object.entries(lines).forEach(([lineNum, line]) => {
                Object.entries(line).forEach(([position, player]) => {
                    if (player) {
                        const slot = document.querySelector(`[data-line="${lineNum}"][data-position="${position}"]`);
                        if (slot) {
                            slot.innerHTML = `
                                ${slot.querySelector('.position-label').outerHTML}
                                <div class="player-card" data-player-id="${player.id}">
                                    <div class="player-name">${player.name}</div>
                                    <div class="player-position">${player.position}</div>
                                    <button onclick="removeFromLine(${player.id})" class="remove-btn">×</button>
                                </div>
                            `;
                        }
                    }
                });
            });
        }

        function setupDropZones() {
            document.querySelectorAll('.position-slot').forEach(slot => {
                slot.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    slot.style.borderColor = '#ff6b35';
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
                        
                        const response = await fetch('/api/lines/set-player', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                player_id: draggedPlayer.id,
                                line_num: lineNum,
                                position: position
                            })
                        });
                        
                        if (response.ok) {
                            loadPlayers();
                            loadLines();
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
            const response = await fetch(`/api/lines/clear/${lineNum}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadPlayers();
                loadLines();
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
    </script>
</body>
</html>'''

    # Write the template to a file
    with open('templates/index.html', 'w') as f:
        f.write(html_template)
    
    # Get port from environment variable (for production) or use 5001 for local
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)