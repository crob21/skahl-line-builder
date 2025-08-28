"""
Configuration settings for Line Walrus
Centralized configuration for the hockey line builder application.
"""

import os
from datetime import datetime

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5001
FLASK_DEBUG = False

# File Paths
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEAMS_DIR = os.path.join(DATA_DIR, 'teams')
SESSIONS_DIR = os.path.join(DATA_DIR, 'sessions')
SHARED_LINES_DIR = os.path.join(DATA_DIR, 'shared_lines')
CSV_DIR = os.path.join(DATA_DIR, 'csv')
BACKUPS_DIR = os.path.join(DATA_DIR, 'backups')

# Static Files
STATIC_DIR = os.path.join(BASE_DIR, 'static')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
CSS_DIR = os.path.join(STATIC_DIR, 'css')
JS_DIR = os.path.join(STATIC_DIR, 'js')

# Logo Configuration
LOGO_FILE = 'line-walrus-logo.png'
FAVICON_FILE = 'favicon.png'
LOGO_PATH = os.path.join(IMAGES_DIR, LOGO_FILE)
FAVICON_PATH = os.path.join(IMAGES_DIR, FAVICON_FILE)

# App Branding
APP_NAME = "Line Walrus"
APP_TAGLINE = "Because Even a Walrus Can Manage Lines Better"
APP_VERSION = "1.0.0"

# Hockey Configuration
POSITIONS = {
    'FORWARD': ['LW', 'C', 'RW'],
    'DEFENSE': ['LD', 'RD'],
    'GOALIE': ['G']
}

LINES = ['1', '2', '3']
DEFAULT_LINE_POSITIONS = {
    '1': ['LW', 'C', 'RW', 'LD', 'RD', 'G'],
    '2': ['LW', 'C', 'RW', 'LD', 'RD'],
    '3': ['LW', 'C', 'RW', 'LD', 'RD']
}

# Colors (SKAHL Theme)
COLORS = {
    'primary_blue': '#1e3a8a',
    'secondary_blue': '#3b82f6',
    'accent_purple': '#8B57F3',
    'gold': '#fbbf24',
    'white': '#FFFFFF'
}

# Mobile Configuration
MOBILE_BREAKPOINTS = {
    'tablet': 768,
    'mobile': 480
}

# Session Configuration
SESSION_TIMEOUT = 3600  # 1 hour
MAX_SESSIONS = 1000

# File Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.csv', '.json'}

# Create directories if they don't exist
def ensure_directories():
    """Create all necessary directories"""
    directories = [
        DATA_DIR, TEAMS_DIR, SESSIONS_DIR, SHARED_LINES_DIR,
        CSV_DIR, BACKUPS_DIR, IMAGES_DIR, CSS_DIR, JS_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Initialize directories
ensure_directories()
