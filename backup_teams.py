#!/usr/bin/env python3
"""
Backup teams to a JSON file that can be restored after deployment
"""
import json
import os
from database import db

def backup_teams():
    """Backup all teams to a JSON file"""
    teams = db.list_teams()
    backup_data = []
    
    for team in teams:
        # Load full team data
        team_data = db.load_team(team['filename'])
        if team_data:
            backup_data.append({
                'name': team['name'],
                'filename': team['filename'],
                'players': team_data['players'],
                'lines': team_data['lines']
            })
    
    # Save backup
    with open('data/teams_backup.json', 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backed up {len(backup_data)} teams to data/teams_backup.json")
    return backup_data

def restore_teams():
    """Restore teams from backup file"""
    if not os.path.exists('data/teams_backup.json'):
        print("❌ No backup file found")
        return
    
    with open('data/teams_backup.json', 'r') as f:
        backup_data = json.load(f)
    
    restored_count = 0
    for team in backup_data:
        if db.save_team(team['name'], team['filename'], team['players'], team['lines']):
            restored_count += 1
            print(f"✅ Restored: {team['name']}")
        else:
            print(f"❌ Failed to restore: {team['name']}")
    
    print(f"📊 Restored {restored_count} teams")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_teams()
    else:
        backup_teams()
