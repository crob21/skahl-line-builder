import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "data/line_walrus.db"):
        """Initialize database connection"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    filename TEXT UNIQUE NOT NULL,
                    players TEXT NOT NULL,  -- JSON string
                    lines TEXT,             -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    players TEXT,           -- JSON string
                    lines TEXT,             -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Shared lines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shared_lines (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    players TEXT NOT NULL,  -- JSON string
                    lines TEXT NOT NULL,    -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_team(self, name: str, filename: str, players: List[Dict], lines: Dict) -> bool:
        """Save or update a team"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                cursor.execute('SELECT id FROM teams WHERE filename = ?', (filename,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing team
                    cursor.execute('''
                        UPDATE teams 
                        SET name = ?, players = ?, lines = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE filename = ?
                    ''', (name, json.dumps(players), json.dumps(lines), filename))
                else:
                    # Insert new team
                    cursor.execute('''
                        INSERT INTO teams (name, filename, players, lines)
                        VALUES (?, ?, ?, ?)
                    ''', (name, filename, json.dumps(players), json.dumps(lines)))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving team: {e}")
            return False
    
    def load_team(self, filename: str) -> Optional[Dict]:
        """Load a team by filename"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name, players, lines FROM teams WHERE filename = ?', (filename,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'name': row[0],
                        'players': json.loads(row[1]),
                        'lines': json.loads(row[2]) if row[2] else {}
                    }
                return None
        except Exception as e:
            print(f"Error loading team: {e}")
            return None
    
    def list_teams(self) -> List[Dict]:
        """List all teams"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name, filename, players, updated_at FROM teams ORDER BY updated_at DESC')
                rows = cursor.fetchall()
                
                teams = []
                for row in rows:
                    players = json.loads(row[2])
                    teams.append({
                        'name': row[0],
                        'filename': row[1],
                        'player_count': len(players),
                        'last_updated': row[3]
                    })
                return teams
        except Exception as e:
            print(f"Error listing teams: {e}")
            return []
    
    def delete_team(self, filename: str) -> bool:
        """Delete a team"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM teams WHERE filename = ?', (filename,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting team: {e}")
            return False
    
    def save_session(self, session_id: str, players: List[Dict], lines: Dict) -> bool:
        """Save session data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if session exists
                cursor.execute('SELECT id FROM sessions WHERE id = ?', (session_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing session
                    cursor.execute('''
                        UPDATE sessions 
                        SET players = ?, lines = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (json.dumps(players), json.dumps(lines), session_id))
                else:
                    # Insert new session
                    cursor.execute('''
                        INSERT INTO sessions (id, players, lines)
                        VALUES (?, ?, ?)
                    ''', (session_id, json.dumps(players), json.dumps(lines)))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load session data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT players, lines FROM sessions WHERE id = ?', (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'players': json.loads(row[0]) if row[0] else [],
                        'lines': json.loads(row[1]) if row[1] else {}
                    }
                return None
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def save_shared_lines(self, line_id: str, name: str, players: List[Dict], lines: Dict) -> bool:
        """Save shared lines"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO shared_lines (id, name, players, lines)
                    VALUES (?, ?, ?, ?)
                ''', (line_id, name, json.dumps(players), json.dumps(lines)))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving shared lines: {e}")
            return False
    
    def load_shared_lines(self, line_id: str) -> Optional[Dict]:
        """Load shared lines"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name, players, lines FROM shared_lines WHERE id = ?', (line_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'name': row[0],
                        'players': json.loads(row[1]),
                        'lines': json.loads(row[2])
                    }
                return None
        except Exception as e:
            print(f"Error loading shared lines: {e}")
            return None

# Global database instance
db = Database()
