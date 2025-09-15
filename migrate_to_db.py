#!/usr/bin/env python3
"""
Migration script to move existing team files to database
"""
import os
import json
from database import db
from utils import TEAMS_DIR

def migrate_teams():
    """Migrate existing team files to database"""
    print("🔄 Starting team migration to database...")
    
    if not os.path.exists(TEAMS_DIR):
        print("❌ Teams directory not found")
        return
    
    migrated_count = 0
    error_count = 0
    
    for filename in os.listdir(TEAMS_DIR):
        if filename.endswith('.json') and filename != 'current_session.json':
            filepath = os.path.join(TEAMS_DIR, filename)
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Extract team data
                name = data.get('team_name', data.get('name', filename.replace('.json', '')))
                players = data.get('players', [])
                lines = data.get('lines', {})
                
                # Save to database
                if db.save_team(name, filename, players, lines):
                    print(f"✅ Migrated: {name} ({filename})")
                    migrated_count += 1
                else:
                    print(f"❌ Failed to migrate: {filename}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Error migrating {filename}: {e}")
                error_count += 1
    
    print(f"\n📊 Migration complete:")
    print(f"   ✅ Migrated: {migrated_count} teams")
    print(f"   ❌ Errors: {error_count} teams")
    
    # List teams in database
    teams = db.list_teams()
    print(f"\n📋 Teams in database:")
    for team in teams:
        print(f"   - {team['name']} ({team['filename']}) - {team['player_count']} players")

if __name__ == "__main__":
    migrate_teams()
