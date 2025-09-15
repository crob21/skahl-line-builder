import sqlite3
import json 
import os
from datetime import datetime
from typing import List, Dict, Optional

# Try to import PostgreSQL adapter
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

class Database:
    def __init__(self, db_path: str = "data/line_walrus.db"):
        """Initialize database connection"""
        self.use_postgres = False
        self.connection_string = None
        
        # Check if we should use PostgreSQL (production)
        database_url = os.getenv('DATABASE_URL')
        print(f"🔍 DATABASE_URL present: {database_url is not None}")
        if database_url:
            print(f"🔍 DATABASE_URL value: {database_url[:50]}...")  # Show first 50 chars
        print(f"🔍 PSYCOPG2_AVAILABLE: {PSYCOPG2_AVAILABLE}")
        print(f"🔍 All environment variables with 'DATABASE': {[k for k in os.environ.keys() if 'DATABASE' in k.upper()]}")
        
        if database_url and PSYCOPG2_AVAILABLE:
            self.use_postgres = True
            self.connection_string = database_url
            print("🐘 Using PostgreSQL database")
        else:
            # Use SQLite for local development
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.db_path = db_path
            print("📁 Using SQLite database")
        
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        if self.use_postgres:
            self._init_postgres()
        else:
            self._init_sqlite()
        
        # Auto-restore teams if database is empty
        self._auto_restore_teams()
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
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
    
    def _init_postgres(self):
        """Initialize PostgreSQL database"""
        with psycopg2.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            
            # Teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    filename VARCHAR(255) UNIQUE NOT NULL,
                    players TEXT NOT NULL,  -- JSON string
                    lines TEXT,             -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(255) PRIMARY KEY,
                    players TEXT,           -- JSON string
                    lines TEXT,             -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Shared lines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shared_lines (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    players TEXT NOT NULL,  -- JSON string
                    lines TEXT NOT NULL,    -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def _get_connection(self):
        """Get database connection (SQLite or PostgreSQL)"""
        if self.use_postgres:
            return psycopg2.connect(self.connection_string)
        else:
            return sqlite3.connect(self.db_path)
    
    def _auto_restore_teams(self):
        """Auto-restore teams from backup if database is empty"""
        try:
            # Check if we have any teams
            teams = self.list_teams()
            if len(teams) > 0:
                return  # Database already has teams
            
            # Check if backup file exists
            backup_file = 'data/teams_backup.json'
            if not os.path.exists(backup_file):
                return  # No backup to restore
            
            # Restore from backup
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            restored_count = 0
            for team in backup_data:
                if self.save_team(team['name'], team['filename'], team['players'], team['lines']):
                    restored_count += 1
            
            if restored_count > 0:
                print(f"🔄 Auto-restored {restored_count} teams from backup")
                
        except Exception as e:
            print(f"⚠️ Auto-restore failed: {e}")
    
    def save_team(self, name: str, filename: str, players: List[Dict], lines: Dict) -> bool:
        """Save or update a team"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if team exists
                if self.use_postgres:
                    cursor.execute('SELECT id FROM teams WHERE filename = %s', (filename,))
                else:
                    cursor.execute('SELECT id FROM teams WHERE filename = ?', (filename,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing team
                    if self.use_postgres:
                        cursor.execute('''
                            UPDATE teams 
                            SET name = %s, players = %s, lines = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE filename = %s
                        ''', (name, json.dumps(players), json.dumps(lines), filename))
                    else:
                        cursor.execute('''
                            UPDATE teams 
                            SET name = ?, players = ?, lines = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE filename = ?
                        ''', (name, json.dumps(players), json.dumps(lines), filename))
                else:
                    # Insert new team
                    if self.use_postgres:
                        cursor.execute('''
                            INSERT INTO teams (name, filename, players, lines)
                            VALUES (%s, %s, %s, %s)
                        ''', (name, filename, json.dumps(players), json.dumps(lines)))
                    else:
                        cursor.execute('''
                            INSERT INTO teams (name, filename, players, lines)
                            VALUES (?, ?, ?, ?)
                        ''', (name, filename, json.dumps(players), json.dumps(lines)))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving team: {e}")
            return False
    
    def load_team(self, team_name: str) -> Optional[Dict]:
        """Load a team by name"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('SELECT name, filename, players, lines FROM teams WHERE name = %s', (team_name,))
                else:
                    cursor.execute('SELECT name, filename, players, lines FROM teams WHERE name = ?', (team_name,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'name': row[0],
                        'filename': row[1],
                        'players': json.loads(row[2]),
                        'lines': json.loads(row[3]) if row[3] else {}
                    }
                return None
        except Exception as e:
            print(f"Error loading team: {e}")
            return None
    
    def list_teams(self) -> List[Dict]:
        """List all teams"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('SELECT name, filename, players, updated_at FROM teams ORDER BY updated_at DESC')
                else:
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
    
    def delete_team(self, team_name: str) -> bool:
        """Delete a team by name"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('DELETE FROM teams WHERE name = %s', (team_name,))
                else:
                    cursor.execute('DELETE FROM teams WHERE name = ?', (team_name,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting team: {e}")
            return False
    
    def save_session(self, session_id: str, players: List[Dict], lines: Dict) -> bool:
        """Save session data"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if session exists
                if self.use_postgres:
                    cursor.execute('SELECT id FROM sessions WHERE id = %s', (session_id,))
                else:
                    cursor.execute('SELECT id FROM sessions WHERE id = ?', (session_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing session
                    if self.use_postgres:
                        cursor.execute('''
                            UPDATE sessions 
                            SET players = %s, lines = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        ''', (json.dumps(players), json.dumps(lines), session_id))
                    else:
                        cursor.execute('''
                            UPDATE sessions 
                            SET players = ?, lines = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (json.dumps(players), json.dumps(lines), session_id))
                else:
                    # Insert new session
                    if self.use_postgres:
                        cursor.execute('''
                            INSERT INTO sessions (id, players, lines)
                            VALUES (%s, %s, %s)
                        ''', (session_id, json.dumps(players), json.dumps(lines)))
                    else:
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('SELECT players, lines FROM sessions WHERE id = %s', (session_id,))
                else:
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('''
                        INSERT INTO shared_lines (id, name, players, lines)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        players = EXCLUDED.players,
                        lines = EXCLUDED.lines
                    ''', (line_id, name, json.dumps(players), json.dumps(lines)))
                else:
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.use_postgres:
                    cursor.execute('SELECT name, players, lines FROM shared_lines WHERE id = %s', (line_id,))
                else:
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
