import json
import os
from datetime import datetime

class HockeyTeamManager:
    def __init__(self, data_file="data/teams/hockey_team.json"):
        self.data_file = data_file
        self.players = []
        self.lines = {
            1: {"LW": None, "C": None, "RW": None, "LD": None, "RD": None, "G": None},
            2: {"LW": None, "C": None, "RW": None, "LD": None, "RD": None},
            3: {"LW": None, "C": None, "RW": None, "LD": None, "RD": None}
        }
        self.load_data()
    
    def save_data(self):
        """Save players and lines to JSON file"""
        data = {
            "players": self.players,
            "lines": self.lines,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Data saved to {self.data_file}")
    
    def load_data(self):
        """Load players and lines from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.players = data.get("players", [])
                    
                    # Load lines and ensure line numbers are integers
                    loaded_lines = data.get("lines", self.lines)
                    self.lines = {}
                    for line_key, line_data in loaded_lines.items():
                        line_num = int(line_key) if isinstance(line_key, str) else line_key
                        self.lines[line_num] = line_data
                    
                print(f"✅ Data loaded from {self.data_file}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Error loading data: {e}")
                print("Starting with Kraken roster")
                self.load_kraken_roster()
        else:
            print("📝 No saved data found, loading Kraken roster")
            self.load_kraken_roster()
    
    def add_player(self, player_data):
        """Add a new player to the roster (new API)"""
        # Check if player already exists
        if any(p["name"].lower() == player_data["name"].lower() for p in self.players):
            print(f"❌ {player_data['name']} is already on the roster!")
            return False
        
        self.players.append(player_data)
        self.save_data()
        print(f"✅ Added {player_data['name']} to the roster!")
        return True
    
    def add_player_legacy(self, name, position):
        """Add a new player to the roster (legacy method)"""
        # Check if player already exists
        if any(p["name"].lower() == name.lower() for p in self.players):
            print(f"❌ {name} is already on the roster!")
            return False
        
        # Validate position
        valid_positions = ["C", "LW", "RW", "LD", "RD", "G"]
        if position.upper() not in valid_positions:
            print(f"❌ Invalid position. Use: {', '.join(valid_positions)}")
            return False
        
        player = {
            "name": name.strip(),
            "position": position.upper(),
            "id": len(self.players) + 1
        }
        
        self.players.append(player)
        self.save_data()
        print(f"✅ Added {name} ({position.upper()}) to the roster!")
        return True
    
    def remove_player(self, player_id):
        """Remove a player from roster and all lines (new API)"""
        player_found = False
        
        # Remove from roster
        for i, player in enumerate(self.players):
            if player.get("id") == player_id:
                self.players.pop(i)
                player_found = True
                break
        
        if not player_found:
            print(f"❌ Player with ID {player_id} not found on roster")
            return False
        
        # Remove from all lines
        for line_num in self.lines:
            for position in self.lines[line_num]:
                if (self.lines[line_num][position] and 
                    self.lines[line_num][position].get("id") == player_id):
                    self.lines[line_num][position] = None
        
        self.save_data()
        print(f"✅ Removed player {player_id} from roster and all lines!")
        return True
    
    def remove_player_legacy(self, name):
        """Remove a player from roster and all lines (legacy method)"""
        player_found = False
        
        # Remove from roster
        for i, player in enumerate(self.players):
            if player["name"].lower() == name.lower():
                self.players.pop(i)
                player_found = True
                break
        
        if not player_found:
            print(f"❌ {name} not found on roster")
            return False
        
        # Remove from all lines
        for line_num in self.lines:
            for position in self.lines[line_num]:
                if (self.lines[line_num][position] and 
                    self.lines[line_num][position].lower() == name.lower()):
                    self.lines[line_num][position] = None
        
        self.save_data()
        print(f"✅ Removed {name} from roster and all lines!")
        return True
    
    def show_roster(self):
        """Display the current roster organized by position"""
        if not self.players:
            print("📝 No players on the roster yet!")
            return
        
        print("\n🏒 TEAM ROSTER 🏒")
        print("=" * 30)
        
        # Group by position
        positions = ["G", "LD", "RD", "C", "LW", "RW"]
        for pos in positions:
            pos_players = [p["name"] for p in self.players if p["position"] == pos]
            if pos_players:
                print(f"{pos:2}: {', '.join(pos_players)}")
        
        print(f"\nTotal Players: {len(self.players)}")
        print()
    
    def set_line(self, line_num, position, player_name):
        """Set a player in a specific line position"""
        if line_num not in [1, 2, 3]:
            print("❌ Line number must be 1, 2, or 3")
            return False
        
        # Only Line 1 can have a goalie
        if position == "G" and line_num != 1:
            print("❌ Goalie position only available on Line 1")
            return False
        
        if position not in ["LW", "C", "RW", "LD", "RD", "G"]:
            print("❌ Invalid position. Use: LW, C, RW, LD, RD, G")
            return False
        
        # Check if player exists
        player = next((p for p in self.players if p["name"].lower() == player_name.lower()), None)
        if not player:
            print(f"❌ {player_name} not found on roster")
            return False
        
        # Remove player from any other position first
        for ln in self.lines:
            for pos in self.lines[ln]:
                if (self.lines[ln][pos] and 
                    self.lines[ln][pos].lower() == player_name.lower()):
                    self.lines[ln][pos] = None
        
        # Set player in new position
        self.lines[line_num][position] = player["name"]
        self.save_data()
        print(f"✅ Set {player['name']} as {position} on Line {line_num}")
        return True
    
    def show_lines(self):
        """Display all current lines"""
        print("\n🏒 CURRENT LINES 🏒")
        print("=" * 40)
        
        for line_num in [1, 2, 3]:
            line = self.lines[line_num]
            print(f"\nLine {line_num}:")
            print(f"  {line['LW'] or '___':10} - {line['C'] or '___':10} - {line['RW'] or '___'}")
            print(f"  {line['LD'] or '___':10} - {line['RD'] or '___'}")
            if line_num == 1:
                print(f"  G: {line['G'] or '___'}")
        
        # Show bench players
        self.show_bench()
        print()
    
    def show_bench(self):
        """Show players not currently in any line"""
        assigned_players = set()
        for line in self.lines.values():
            for player in line.values():
                if player:
                    assigned_players.add(player.lower())
        
        bench_players = [p["name"] for p in self.players 
                        if p["name"].lower() not in assigned_players]
        
        if bench_players:
            print(f"\nBench: {', '.join(bench_players)}")
        else:
            print("\nBench: Empty")
    
    def clear_line(self, line_num):
        """Clear all positions in a specific line"""
        if line_num not in [1, 2, 3]:
            print("❌ Line number must be 1, 2, or 3")
            return False
        
        if line_num == 1:
            self.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                                   "LD": None, "RD": None, "G": None}
        else:
            self.lines[line_num] = {"LW": None, "C": None, "RW": None, 
                                   "LD": None, "RD": None}
        self.save_data()
        print(f"✅ Cleared Line {line_num}")
        return True
    
    def clear_all_lines(self):
        """Clear all lines"""
        self.lines[1] = {"LW": None, "C": None, "RW": None, 
                         "LD": None, "RD": None, "G": None}
        self.lines[2] = {"LW": None, "C": None, "RW": None, 
                         "LD": None, "RD": None}
        self.lines[3] = {"LW": None, "C": None, "RW": None, 
                         "LD": None, "RD": None}
        self.save_data()
        print("✅ Cleared all lines!")
    
    def load_kraken_roster(self):
        """Load default Seattle Kraken roster"""
        kraken_file = "data/teams/seattle_kraken.json"
        if os.path.exists(kraken_file):
            try:
                with open(kraken_file, 'r') as f:
                    data = json.load(f)
                    players = data.get("players", [])
                    
                    # Load all players from the JSON file
                    self.players = players
                
                self.save_data()
                print(f"✅ Loaded Seattle Kraken roster with {len(players)} players!")
            except Exception as e:
                print(f"⚠️  Error loading Kraken roster: {e}")
        else:
            print("⚠️  Kraken roster file not found")
    
    # New API methods for web interface
    def load_players(self, players_list):
        """Load players from a list (new API)"""
        self.players = players_list
        self.save_data()
        print(f"✅ Loaded {len(players_list)} players")
    
    def set_player_in_line(self, player_id, line, position):
        """Set a player in a specific line position (new API)"""
        # Find the player
        player = None
        for p in self.players:
            if p.get("id") == player_id:
                player = p
                break
        
        if not player:
            print(f"❌ Player with ID '{player_id}' not found on roster")
            return False
        
        # Validate line and position
        line_num = int(line)
        if line_num not in [1, 2, 3]:
            print("❌ Invalid line number. Use 1, 2, or 3")
            return False
        
        valid_positions = ["LW", "C", "RW", "LD", "RD", "G"]
        if position.upper() not in valid_positions:
            print(f"❌ Invalid position. Use: {', '.join(valid_positions)}")
            return False
        
        # Check if goalie position is only on line 1
        if position.upper() == "G" and line_num != 1:
            print("❌ Goalie position is only available on Line 1")
            return False
        
        # Remove player from any other position first
        for ln in self.lines:
            for pos in self.lines[ln]:
                if (self.lines[ln][pos] and 
                    isinstance(self.lines[ln][pos], dict) and
                    self.lines[ln][pos].get("id") == player_id):
                    self.lines[ln][pos] = None
        
        # Set the player in the position
        self.lines[line_num][position.upper()] = player
        self.save_data()
        print(f"✅ Set {player['name']} in Line {line_num} {position.upper()}")
        return True
    
    def remove_from_line(self, line, position):
        """Remove a player from a line position (new API)"""
        print(f"🔍 HockeyManager.remove_from_line called with: line={line} (type: {type(line)}), position={position} (type: {type(position)})")
        
        try:
            line_num = int(line)
            print(f"🔍 Converted line to int: {line_num}")
        except (ValueError, TypeError) as e:
            print(f"❌ Error converting line to int: {e}")
            return False
            
        if line_num not in [1, 2, 3]:
            print(f"❌ Invalid line number {line_num}. Use 1, 2, or 3")
            return False
        
        if position.upper() not in ["LW", "C", "RW", "LD", "RD", "G"]:
            print(f"❌ Invalid position {position.upper()}")
            return False
        
        print(f"🔍 Checking if player exists at line {line_num}, position {position.upper()}")
        print(f"🔍 Current lines: {self.lines}")
        
        if self.lines[line_num].get(position.upper()):
            self.lines[line_num][position.upper()] = None
            self.save_data()
            print(f"✅ Removed player from Line {line_num} {position.upper()}")
            return True
        else:
            print(f"❌ No player found at Line {line_num} {position.upper()}")
            return False

def main():
    """Main interactive menu"""
    manager = HockeyTeamManager()
    
    while True:
        print("\n" + "="*50)
        print("🏒 HOCKEY TEAM MANAGER 🏒")
        print("="*50)
        print("1. Show Roster")
        print("2. Add Player")
        print("3. Remove Player")
        print("4. Show Lines")
        print("5. Set Player in Line")
        print("6. Clear Line")
        print("7. Clear All Lines")
        print("8. Quick Setup (add sample players)")
        print("9. Exit")
        print("="*50)
        
        choice = input("\nChoose an option (1-9): ").strip()
        
        if choice == "1":
            manager.show_roster()
        
        elif choice == "2":
            name = input("Player name: ").strip()
            if not name:
                print("❌ Name cannot be empty")
                continue
            
            print("Positions: C, LW, RW, LD, RD, G")
            position = input("Position: ").strip().upper()
            manager.add_player(name, position)
        
        elif choice == "3":
            if not manager.players:
                print("📝 No players to remove")
                continue
            
            manager.show_roster()
            name = input("\nPlayer name to remove: ").strip()
            if name:
                manager.remove_player(name)
        
        elif choice == "4":
            manager.show_lines()
        
        elif choice == "5":
            if not manager.players:
                print("📝 Add some players first!")
                continue
            
            manager.show_roster()
            print("\nPositions: LW, C, RW, LD, RD, G")
            
            try:
                line_num = int(input("Line number (1, 2, 3): "))
                position = input("Position: ").strip().upper()
                player_name = input("Player name: ").strip()
                
                if line_num and position and player_name:
                    manager.set_line(line_num, position, player_name)
            except ValueError:
                print("❌ Please enter a valid line number")
        
        elif choice == "6":
            try:
                line_num = int(input("Line number to clear (1, 2, 3): "))
                manager.clear_line(line_num)
            except ValueError:
                print("❌ Please enter a valid line number")
        
        elif choice == "7":
            confirm = input("Clear all lines? (yes/no): ").lower()
            if confirm in ["yes", "y"]:
                manager.clear_all_lines()
        
        elif choice == "8":
            # Quick setup with sample players
            sample_players = [
                ("Connor McDavid", "C"),
                ("Alex Ovechkin", "LW"), 
                ("David Pastrnak", "RW"),
                ("Erik Karlsson", "LD"),
                ("Cale Makar", "RD"),
                ("Igor Shesterkin", "G"),
                ("Sidney Crosby", "C"),
                ("Brad Marchand", "LW"),
                ("Mitch Marner", "RW"),
                ("Victor Hedman", "LD"),
                ("Aaron Ekblad", "RD"),
                ("Frederik Andersen", "G")
            ]
            
            print("Adding sample players...")
            for name, pos in sample_players:
                manager.add_player(name, pos)
            
            print("✅ Sample players added!")
        
        elif choice == "9":
            print("Thanks for using Hockey Team Manager! 🏒")
            break
        
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    main()