"""
Line Walrus - Hockey Line Builder
Main application file for the hockey line builder web application.
"""

from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import secrets
import os

# Import our organized modules
from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG, APP_NAME, APP_TAGLINE,
    LOGO_PATH, FAVICON_PATH, COLORS
)
from routes import init_routes
from hockey_manager import HockeyTeamManager
from utils import (
    generate_session_id, get_session_data_file, load_json_file,
    get_shared_line_file, format_timestamp
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize routes
init_routes(app)

def get_manager():
    """Get the current session's hockey team manager"""
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
    
    session_file = get_session_data_file(session['session_id'])
    return HockeyTeamManager(session_file)

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/lines/<line_id>')
def view_shared_lines(line_id):
    """View shared lines via URL"""
    try:
        line_file = get_shared_line_file(line_id)
        line_data = load_json_file(line_file)
        
        if not line_data:
            return "Lines not found or have been removed.", 404
        
        # Generate HTML for shared view
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{APP_NAME} - {line_data['name']}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="icon" type="image/png" href="/static/images/favicon.png">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: linear-gradient(135deg, {COLORS['primary_blue']}, {COLORS['secondary_blue']});
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
                    border-bottom: 3px solid {COLORS['gold']};
                    padding-bottom: 20px;
                }}
                .header h1 {{
                    color: {COLORS['gold']};
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
                    color: {COLORS['gold']};
                    font-style: italic;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                .header h2 {{
                    color: {COLORS['secondary_blue']};
                    font-size: 20px;
                    margin: 0;
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
                    color: {COLORS['gold']};
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
                    border: 2px solid {COLORS['gold']}; 
                    padding: 12px 8px; 
                    min-width: 100px; 
                    text-align: center; 
                    background: rgba(255,255,255,0.1);
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                .position-label {{ 
                    font-weight: bold; 
                    color: {COLORS['gold']}; 
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
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid rgba(255,255,255,0.2);
                    color: #ccc;
                }}
                .load-button {{
                    background: {COLORS['gold']};
                    color: {COLORS['primary_blue']};
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
                            <img src="/static/images/line-walrus-logo.png" alt="{APP_NAME} Logo">
                        </div>
                        {APP_NAME}
                    </h1>
                    <p class="tagline">{APP_TAGLINE}</p>
                    <h2>{line_data['name']}</h2>
                    <p style="color: {COLORS['gold']}; font-size: 18px; font-weight: bold; margin: 10px 0; text-transform: uppercase; letter-spacing: 1px;">{line_data.get('team_name', 'Current Team')}</p>
                    <p>Shared on {format_timestamp(line_data['created'])}</p>
                </div>
        '''
        
        # Add each line
        for line_num, line in line_data['lines'].items():
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
        
        html_content += f'''
                <div class="footer">
                    <a href="/" class="load-button">Open {APP_NAME}</a>
                    <button onclick="window.print()" class="print-button">🖨️ Print Lines</button>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html_content
        
    except Exception as e:
        return f"Error loading shared lines: {str(e)}", 500

if __name__ == '__main__':
    print(f"🦭 Starting {APP_NAME}...")
    print(f"📍 Running on http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"🎯 {APP_TAGLINE}")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )
